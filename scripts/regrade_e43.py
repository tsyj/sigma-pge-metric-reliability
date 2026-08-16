#!/usr/bin/env python
"""E43 离线重评：宽容 region 解析（修复 spec_key 静默改写），对已存盘 spec 重新打分。

起因：pro/s0 R4 写 "region": "deeper_than 800"（字符串），原 spec_key 不认识 →
归一到 all、丢分母，把 deep/shallow 比值静默评成了 u|all|rms。
Agent 的提议是合法意图，错的是我们的解析接口 —— 与 E36（ntimes 被滤掉）同款缺陷。
修复后对全部 5 个结果文件的原始 spec 重评（grader 确定性，无需重调 LLM），
新旧对照全部落盘。
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent_metric_v2 as m

_orig_region_key = m.region_key


def lenient_region_key(region):
    """在原解析基础上，识别字符串形式 'deeper_than 800' / 'shallower_than 200'。"""
    if isinstance(region, str):
        s = region.strip().lower()
        mm = re.match(r"(deeper|shallower)[_ ]?than[_ =:]*([0-9.]+)", s)
        if mm:
            kind, val = mm.group(1), float(mm.group(2))
            return _orig_region_key({("deeper_than" if kind == "deeper"
                                      else "shallower_than"): val})
    return _orig_region_key(region)


m.region_key = lenient_region_key
# spec_key 内部调用的是模块级 region_key，猴补后自动生效
G = m.Grader()
print("pool:", G.summary)

changed, out = 0, {}
for fn in sorted(glob.glob(f"{m.ENV}/ledger/agent_metric_v2_*_s*.json")):
    d = json.load(open(fn))
    tag = f"{d['condition']}/{d['model']}/s{d['seed']}"
    rows = []
    for r in d.get("results", []):
        if "parse_error" in r or not r.get("spec"):
            continue
        spec = r["spec"]
        old = r.get("grade", {})
        new = G.grade(spec.get("num"), spec.get("den"))
        diff = (old.get("key_num"), old.get("key_den")) != (new.get("key_num"), new.get("key_den"))
        rows.append(dict(round=r.get("round"), name=spec.get("name"),
                         old_key=[old.get("key_num"), old.get("key_den")],
                         new_key=[new.get("key_num"), new.get("key_den")],
                         old_valid=old.get("valid"), new=new, changed=diff))
        if diff:
            changed += 1
            print(f"CHANGED {tag} R{r.get('round')}: "
                  f"[{old.get('key_num')}/{old.get('key_den')}] -> "
                  f"[{new.get('key_num')}/{new.get('key_den')}]  "
                  f"new: valid={new.get('valid')} "
                  + (f"ρ={new['rho']:+.3f} paired={new['paired']:.3f} passed={new['passed']}"
                     if new.get("valid") else f"({new.get('reason')})"))
    out[tag] = rows

n_pass = sum(1 for rows in out.values() for x in rows
             if x["new"].get("valid") and x["new"].get("passed"))
n_valid = sum(1 for rows in out.values() for x in rows if x["new"].get("valid"))
print(f"\n重评完成：{changed} 轮 key 有变化；重评后 valid={n_valid}，通过 A+B′ = {n_pass}")
json.dump(dict(note="E43 宽容解析重评（修复字符串 region 静默改写）",
               changed_rounds=changed, n_valid=n_valid, n_passed=n_pass, detail=out),
          open(f"{m.ENV}/ledger/agent_metric_v2_regrade.json", "w"),
          ensure_ascii=False, indent=1)
print("→ ledger/agent_metric_v2_regrade.json")
