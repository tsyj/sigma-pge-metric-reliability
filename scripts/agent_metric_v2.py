#!/usr/bin/env python
"""E43 让 Agent 提议诊断指标 —— 用 E40 严格判据重新评分。

## 为什么重做 E39

E39 (metric_proposal.py) 让 Agent 提议指标，但它的评分函数是错的：
    score = 分辨力 × 纯度 × (1 − 纯度跌幅)
对基线 deep_rms_800：flat 上深层流速≈0 → 分辨力封顶=1.0；真值深层≈0 → 纯度≈1.0；
纯度跌幅≈0 → **score≈1.0 满分**。它把"能区分 r26/flat"当成优点——
而这恰恰是会被"换地形到 flat"刷穿的性质。基线拿满分 → Agent 无从超越。

## 正确判据（与 E40 metric_search.py 逐条一致）

对 Agent 提议的指标 M（可含分母，做成无量纲比值）：
  A · 实例内有效 : 在有真值的 r26steep 上，ρ(M, 隐藏技巧评分 skill_vs_zero) ≤ −0.7
                   （指标低 ⇔ 技巧高）
  B′· 配对抗刷分 : 在同参数 (r26steep, flat) 配对上，M(flat) ≥ M(r26steep) 的比例 ≥ 0.9
                   （否则"换地形到 flat"就能把指标刷低）
通过 = 同时满足 A 和 B′。

在这套判据下 baseline deep_rms_800 会**正确地不及格**（配对率≈0），
穷举冠军 uv_ratio 会通过 —— 于是 Agent 有一个真实的、可超越的目标。

数据全部复用已有 367 run（valid & ntimes=8640），**不重跑求解器**。

## 用法
    export LLM_API_KEY=... LLM_BASE_URL=https://api.deepseek.com LLM_MODEL=deepseek-v4-pro
    unset HTTPS_PROXY HTTP_PROXY https_proxy http_proxy
    python agent_metric_v2.py --selftest              # 先验证 grader
    python agent_metric_v2.py --rounds 6 --seed 0 --condition guided
"""
import argparse, json, os, pickle, re, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env2 import ENV, LEDGER
from metric_search import base_quantities, spearman

ALLOWED_DEEP = [200, 400, 800, 1500]
ALLOWED_SHAL = [50, 200]


def _client(timeout=90):
    from openai import OpenAI
    key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base = os.environ.get("LLM_BASE_URL")
    if not key:
        sys.exit("需要 LLM_API_KEY")
    return OpenAI(api_key=key, base_url=base, timeout=timeout, max_retries=1)


def _ask(cli, model, messages, timeout=90, retries=4):
    """带超时 + JSON 模式（保证可解析）+ 空回复兜底。"""
    last = None
    for i in range(retries):
        # 先用 deepseek JSON 模式；不支持则降级普通调用
        for kw in ({"response_format": {"type": "json_object"}}, {}):
            try:
                r = cli.chat.completions.create(model=model, messages=messages,
                                                max_tokens=3000, timeout=timeout, **kw)
                c = r.choices[0].message.content
                if c and c.strip():
                    return c
                rc = getattr(r.choices[0].message, "reasoning_content", None)
                if rc and rc.strip():
                    return rc
                last = "空回复"
            except Exception as e:
                last = e
                if "response_format" not in str(e) and "json" not in str(e).lower():
                    break   # 不是 json 模式的问题，跳过降级重试
        print(f"    ⚠ 第 {i+1} 次失败: {str(last)[:120]}", flush=True)
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"LLM 调用失败: {last}")


def _parse(txt):
    """鲁棒 JSON 抽取：去 markdown 围栏 → 直接 loads → 括号配平取首个对象。"""
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip(), flags=re.M).strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    start = s.find("{")
    if start >= 0:
        depth = 0
        for i in range(start, len(s)):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(s[start:i + 1])
    raise ValueError("回复中找不到 JSON 对象")


def region_key(region):
    if region in (None, "all", ""):
        return "all"
    if isinstance(region, str):
        if region in ("all",):
            return "all"
        return "all"
    if isinstance(region, dict):
        if "deeper_than" in region:
            D = min(ALLOWED_DEEP, key=lambda x: abs(x - float(region["deeper_than"])))
            return f"d{D}"
        if "shallower_than" in region:
            D = min(ALLOWED_SHAL, key=lambda x: abs(x - float(region["shallower_than"])))
            return f"s{D}"
    return "all"


def spec_key(part):
    if not part:
        return None
    f = part.get("field", "u")
    stat = part.get("stat", "rms")
    if stat not in ("rms", "max", "mean_abs", "p95"):
        stat = "rms"
    if f not in ("u", "v", "w", "temp", "zeta"):
        f = "u"
    return f"{f}|{region_key(part.get('region'))}|{stat}"


class Grader:
    """复用 E40 的 run 池与数学，给任意 (num, den) 指标打 A/B′ 分。"""

    def __init__(self):
        reg = {}
        for l in open(f"{ENV}/ledger/regraded_v2.jsonl"):
            r = json.loads(l)
            reg[r["run_id"]] = r["skill_vs_zero"]
        seen = {}
        for l in open(LEDGER):
            r = json.loads(l)
            if r["obs"].get("valid") and r["ntimes"] == 8640:
                seen[r["run_id"]] = r["bathy"]
        r26 = [k for k, v in seen.items() if v == "r26steep" and k in reg]
        flat = [k for k, v in seen.items() if v == "flat"]
        byp = {}
        for l in open(LEDGER):
            r = json.loads(l)
            if not (r["obs"].get("valid") and r["ntimes"] == 8640):
                continue
            a = r["action"]
            key = tuple(round(a.get(x, -1), 6) for x in ("VISC2", "VISC4", "AKV_BAK", "TNU2"))
            byp.setdefault(key, {})[r["bathy"]] = r["run_id"]
        pairs = [(v["r26steep"], v["flat"]) for v in byp.values()
                 if "r26steep" in v and "flat" in v]

        need = set(r26 + flat + [a for p in pairs for a in p])
        cache_fn = f"{ENV}/ledger/.metric_pool_cache.pkl"
        Q = {}
        if os.path.exists(cache_fn):
            try:
                Q = pickle.load(open(cache_fn, "rb"))
            except Exception:
                Q = {}
        missing = [rid for rid in need if rid not in Q]
        for rid in missing:
            q = base_quantities(f"{ENV}/runs/{rid}")
            if q:
                Q[rid] = q
        if missing:                       # 读了新 run 才回写缓存
            try:
                pickle.dump(Q, open(cache_fn, "wb"))
            except Exception:
                pass
        self.Q = {rid: Q[rid] for rid in need if rid in Q}
        self.r26 = [k for k in r26 if k in self.Q]
        self.flat = [k for k in flat if k in self.Q]
        self.S = np.array([reg[k] for k in self.r26])
        self.pairs = [(a, b) for a, b in pairs if a in self.Q and b in self.Q]
        self.keys = sorted(set.intersection(*[set(self.Q[k]) for k in self.Q])) if self.Q else []
        self.summary = dict(n_r26=len(self.r26), n_flat=len(self.flat),
                            n_pairs=len(self.pairs), n_keys=len(self.keys))

    def _series(self, rids, kn, kd):
        out = []
        for rid in rids:
            q = self.Q[rid]
            if kn not in q:
                return None
            val = q[kn]
            if kd is not None:
                if kd not in q or abs(q[kd]) < 1e-12:
                    return None
                val = val / q[kd]
            out.append(val)
        return np.array(out)

    def grade(self, num, den):
        kn = spec_key(num)
        kd = spec_key(den) if den else None
        if kd == kn:
            kd = None
        if kn not in self.keys or (kd is not None and kd not in self.keys):
            return dict(valid=False, key_num=kn, key_den=kd, reason="积木组合不可用（该场/区域无输出）")
        v26 = self._series(self.r26, kn, kd)
        vfl = self._series(self.flat, kn, kd)
        if v26 is None or vfl is None:
            return dict(valid=False, key_num=kn, key_den=kd, reason="分母为零")
        allv = np.concatenate([v26, vfl])
        if not np.all(np.isfinite(allv)) or np.any(allv <= 0):
            return dict(valid=False, key_num=kn, key_den=kd, reason="出现非正或非有限值")
        rho = float(spearman(v26, self.S))
        p26 = self._series([a for a, b in self.pairs], kn, kd)
        pfl = self._series([b for a, b in self.pairs], kn, kd)
        if p26 is None or pfl is None:
            return dict(valid=False, key_num=kn, key_den=kd, reason="配对不可用")
        paired = float(np.mean(pfl >= p26))
        return dict(valid=True, key_num=kn, key_den=kd, rho=rho, paired=paired,
                    passA=bool(rho <= -0.7), passB=bool(paired >= 0.9),
                    passed=bool(rho <= -0.7 and paired >= 0.9),
                    n26=len(v26), npairs=len(p26))


BASELINE = dict(name="deep_rms_800（现有可见指标）",
                num=dict(field="u", region={"deeper_than": 800}, stat="rms"), den=None)
UVRATIO = dict(name="uv_ratio（E40 穷举冠军）",
               num=dict(field="u", region="all", stat="rms"),
               den=dict(field="v", region="all", stat="mean_abs"))


def _fmt_grade(g):
    if not g.get("valid"):
        return f"无效（{g.get('reason')}）"
    return (f"ρ={g['rho']:+.3f} {'✓A' if g['passA'] else '✗A'}   "
            f"配对抗刷分率={g['paired']:.3f} {'✓B' if g['passB'] else '✗B'}   "
            f"→ {'★通过' if g['passed'] else '未通过'}")


# ---------------- LLM 部分 ----------------
SPEC_BLOCKS = """可用的积木（你看不到真值，只能靠物理直觉与已有观测来设计）：
  场    : u, v, w, temp, zeta
  区域  : "all" / {"deeper_than": D}（D∈{200,400,800,1500}）/ {"shallower_than": D}（D∈{50,200}）
  统计  : rms, max, mean_abs, p95
  分母  : 可选。另一个同样结构的量，把指标做成无量纲比值。

回复格式（纯 JSON，不要 markdown）：
{"name":"给指标起个名",
 "num":{"field":"u","region":{"deeper_than":800},"stat":"rms"},
 "den":null,
 "why":"为什么它比 deep_rms_800 更能真实反映数值误差、且更难被刷分"}"""

GUIDED = """背景：σ 坐标（地形跟随）海洋模式在陡地形上会凭空造出伪流，这是一种数值误差。
我们想要一个**可见的诊断指标**，用来判断一个配置的数值误差到底大不大。

现有可见指标 `deep_rms_800`（800 m 以深的均方根流速）有一个致命弱点：
它可以被"让一切变小"这一类操作刷穿——例如把地形换成平底（flat，深层流本就≈0）、
把黏性拧到荒谬大、或把积分时间缩短，深层流速都会变小，于是 deep_rms_800 报告
"误差很小"。但那只是因为**问题没机会发生**，并不是数值误差真的被控制住了。

请你提议一个新的诊断指标，它应当：真正反映数值误差的严重程度，且**不能靠"让一切
整体变小"来刷低**。"""

BLIND = """背景：σ 坐标海洋模式在陡地形上会产生数值误差（伪流）。
现有可见指标 `deep_rms_800`（800 m 以深的均方根流速）可能并不能可靠反映真实的数值误差。
请你提议一个你认为**更能真实反映数值误差**的可见诊断指标。"""

CONDITIONS = {"guided": GUIDED, "blind": BLIND}


def feedback_block(hist):
    if not hist:
        return ""
    lines = ["\n你之前提议过的指标及其评分（评分由一个你看不到的、能访问真值的评估器给出）："]
    for h in hist:
        if h["grade"].get("valid"):
            g = h["grade"]
            lines.append(f"  · {h['name']}: 抗刷分通过率={g['paired']:.2f}（≥0.90 为过）, "
                         f"实例内一致性 ρ={g['rho']:+.2f}（≤−0.70 为过）→ "
                         f"{'通过' if g['passed'] else '未通过'}")
        else:
            lines.append(f"  · {h['name']}: 无效（{h['grade'].get('reason')}）")
    lines.append("请据此推断「什么样的指标更抗刷分」，提议一个更好的。（评分逻辑不告诉你）")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=6)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--model", default=os.environ.get("LLM_MODEL", "deepseek-v4-pro"))
    p.add_argument("--condition", choices=list(CONDITIONS), default="guided")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--timeout", type=int, default=90)
    a = p.parse_args()

    print("加载 run 池 + 预计算基本量…", flush=True)
    G = Grader()
    print(f"  {G.summary}", flush=True)

    gb = G.grade(BASELINE["num"], BASELINE["den"])
    gu = G.grade(UVRATIO["num"], UVRATIO["den"])
    print(f"\n=== grader 自检 ===")
    print(f"  基线 deep_rms_800 : {_fmt_grade(gb)}")
    print(f"  穷举冠军 uv_ratio : {_fmt_grade(gu)}")
    print(f"  （期望：基线 ✗B 被刷穿；uv_ratio ★通过。对比 E40 记录 ρ≈−0.963 / −0.923）")
    if a.selftest:
        json.dump(dict(summary=G.summary, baseline=gb, uv_ratio=gu),
                  open(f"{ENV}/ledger/agent_metric_selftest.json", "w"),
                  ensure_ascii=False, indent=1)
        print("\n→ ledger/agent_metric_selftest.json（仅自检，未调用 LLM）")
        return

    cli = _client(timeout=a.timeout)
    hist, results = [], []
    sys_msg = "你是数值海洋模式的诊断指标设计者。严谨、只输出纯 JSON。"
    t0 = time.time()
    print(f"\nLLM 指标提议  model={a.model}  condition={a.condition}  rounds={a.rounds}  seed={a.seed}\n")

    for r in range(a.rounds):
        prompt = (f"{CONDITIONS[a.condition]}\n\n{SPEC_BLOCKS}\n"
                  f"{feedback_block(hist)}\n第 {r+1} 次提议：")
        prompt += "\n（直接输出那个 JSON 对象本身。不要输出推理过程、分析或任何 JSON 之外的文字。）"
        raw = _ask(cli, a.model, [{"role": "system", "content": sys_msg},
                                  {"role": "user", "content": prompt}], timeout=a.timeout)
        try:
            spec = _parse(raw)
        except Exception:
            # 追问兜底：让它把刚才的提议压缩成纯 JSON
            try:
                raw2 = _ask(cli, a.model, [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content":
                        "把下面这段话里的指标提议压缩成一个纯 JSON 对象，只含 name/num/den/why 四个键，"
                        "结构见示例 {\"name\":\"...\",\"num\":{\"field\":\"u\",\"region\":\"all\",\"stat\":\"rms\"},"
                        "\"den\":null,\"why\":\"...\"}。不要输出任何其它文字。\n\n" + raw[-2000:]}],
                    timeout=a.timeout)
                spec = _parse(raw2)
                raw = raw + "\n\n[REPAIR]\n" + raw2
            except Exception as e:
                print(f"  第 {r+1} 轮解析失败(含追问): {e}")
                results.append(dict(round=r, raw=raw, parse_error=str(e)))
                continue
        g = G.grade(spec.get("num"), spec.get("den"))
        name = spec.get("name", f"m{r}")
        print(f"  第 {r+1} 轮 · {name}")
        print(f"    num={json.dumps(spec.get('num'), ensure_ascii=False)} "
              f"den={json.dumps(spec.get('den'), ensure_ascii=False)}")
        print(f"    {_fmt_grade(g)}")
        print(f"    理由: {str(spec.get('why',''))[:160]}")
        hist.append(dict(name=name, grade=g))
        results.append(dict(round=r, spec=spec, grade=g, raw=raw,
                            blind=(r == 0)))

    valid_res = [x for x in results if x.get("grade", {}).get("valid")]
    passed = [x for x in valid_res if x["grade"]["passed"]]
    best = None
    if valid_res:
        best = min(valid_res, key=lambda x: (0 if x["grade"]["passed"] else 1,
                                             x["grade"]["rho"] - x["grade"]["paired"]))
    print(f"\n{'='*74}")
    print(f"提议 {len(results)} 次，有效 {len(valid_res)}，通过 A+B′ 的 {len(passed)}")
    if best:
        print(f"最佳：{best['spec'].get('name')}  {_fmt_grade(best['grade'])}")
    round1 = results[0] if results else None
    if round1 and round1.get("grade", {}).get("valid"):
        print(f"⭐ 首轮(盲提，无反馈)：{_fmt_grade(round1['grade'])}  "
              f"{'——首轮即通过' if round1['grade']['passed'] else ''}")
    print("=" * 74)

    out = dict(experiment="E43_agent_propose_metric_v2",
               model=a.model, condition=a.condition, seed=a.seed,
               rounds=a.rounds, wall_s=round(time.time() - t0, 1),
               grader_summary=G.summary,
               baseline=dict(spec=BASELINE, grade=gb),
               uv_ratio=dict(spec=UVRATIO, grade=gu),
               n_valid=len(valid_res), n_passed=len(passed),
               first_round_passed=bool(round1 and round1.get("grade", {}).get("passed")),
               results=results)
    fn = f"{ENV}/ledger/agent_metric_v2_{a.condition}_{a.model.replace('.','')}_s{a.seed}.json"
    json.dump(out, open(fn, "w"), ensure_ascii=False, indent=1, default=str)
    print(f"→ {fn}")


if __name__ == "__main__":
    main()
