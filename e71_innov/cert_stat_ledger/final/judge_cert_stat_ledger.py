# -*- coding: utf-8 -*-
"""
judge_cert_stat_ledger.py —— 机械判分：读输出 JSON，按 PREREG_cert_stat_ledger.md
写死的 P1–P8 布尔式输出 verdict.json。无命令行参数；阈值一律硬编码；人不改判。

前置校验（PREREG §4，任一失败即拒绝判分）：
  ① PREREG 已封存：.sha256 存在、sha 相符、文件权限 444；
  ② SEALED_SCRIPTS.sha256 存在，逐行重算每个脚本（含本脚本与 run_all.sh）的 sha256 比对；
  ③ INPUTS_SHA256.txt 存在，逐行重算每个输入数据文件的 sha256 比对（date 行跳过）。
缺输出文件 ⇒ 该条记 "未跑"。任何字段缺失/歧义 ⇒ 记 "不中" 并注明原因（PREREG §4）。
verdict.json 含：P1–P8（各带 tier）、headline 块（真赌注 4 项，P6 子句 2 单判）、S_status 块（S1–S4）。
"""
import hashlib
import json
import os
import stat as statmod
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HEXD = set("0123456789abcdef")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def verify_checklist(path, label):
    """逐行重算 sha256 比对；非校验行（如 date -Is 行）跳过；不符即拒绝判分。"""
    n_ok = 0
    for raw in open(path).read().splitlines():
        line = raw.strip()
        if len(line) < 66 or set(line[:64]) - HEXD:
            continue  # date 行等非校验行
        rec_sha = line[:64]
        fp = line[64:].lstrip(" *")
        full = fp if os.path.isabs(fp) else os.path.join(HERE, fp)
        if not os.path.exists(full):
            sys.exit(f"拒绝判分：{label} 所列文件不存在：{fp}")
        if sha256_of(full) != rec_sha:
            sys.exit(f"拒绝判分：{label} 校验不符（文件被改动）：{fp}")
        n_ok += 1
    if n_ok == 0:
        sys.exit(f"拒绝判分：{label} 无任何可校验行")
    return n_ok


def load(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def main():
    prereg = os.path.join(HERE, "PREREG_cert_stat_ledger.md")
    seal = prereg.replace(".md", ".sha256")
    if not os.path.exists(seal):
        sys.exit("拒绝判分：PREREG 未封存（缺 .sha256）")
    sealed_sha = open(seal).read().split()[0]
    if sha256_of(prereg) != sealed_sha:
        sys.exit("拒绝判分：PREREG 内容与封存 sha 不符")
    perm = oct(os.stat(prereg).st_mode & 0o777)[-3:]
    if perm != "444":
        sys.exit(f"拒绝判分：PREREG 权限 {perm} != 444")
    sseal = os.path.join(HERE, "SEALED_SCRIPTS.sha256")
    if not os.path.exists(sseal):
        sys.exit("拒绝判分：缺 SEALED_SCRIPTS.sha256（脚本未封存）")
    n_scripts = verify_checklist(sseal, "SEALED_SCRIPTS.sha256")
    inputs = os.path.join(HERE, "INPUTS_SHA256.txt")
    if not os.path.exists(inputs):
        sys.exit("拒绝判分：缺 INPUTS_SHA256.txt")
    n_inputs = verify_checklist(inputs, "INPUTS_SHA256.txt")

    sim = load("SIM_FALSE_CERT.json")
    price = load("PRICE_TABLE.json")
    kill = load("KILL_WOULDHAVE.json")
    perm_j = load("PERM_LEDGER.json")
    power = load("POWER_LEDGER.json")
    akm = load("AKM_WINNER.json")

    TIER = {"P1": "真赌注", "P2": "近确定", "P3": "确定性核验", "P4": "真赌注",
            "P5": "近确定", "P6": "子句1=确定性核验/子句2=真赌注",
            "P7": "真赌注", "P8": "近确定"}
    V = {}

    def judge(pid, predicted, fn, src):
        if src is None:
            V[pid] = {"predicted": predicted, "observed": None,
                      "verdict": "未跑", "tier": TIER[pid]}
            return
        try:
            obs, ok = fn()
            V[pid] = {"predicted": predicted, "observed": obs,
                      "verdict": "中" if ok else "不中", "tier": TIER[pid]}
        except Exception as e:  # 字段缺失/歧义 ⇒ 不中（PREREG §4）
            V[pid] = {"predicted": predicted, "observed": f"字段异常: {e}",
                      "verdict": "不中", "tier": TIER[pid]}

    judge("P1", "r_optstop >= 0.0375 AND r_oneshot204 <= 0.035",
          lambda: ({"r_optstop": sim["r_optstop"], "r_oneshot204": sim["r_oneshot204"]},
                   sim["r_optstop"] >= 0.0375 and sim["r_oneshot204"] <= 0.035), sim)

    judge("P2", "r_eproc <= 0.027",
          lambda: ({"r_eproc": sim["r_eproc"]}, sim["r_eproc"] <= 0.027), sim)

    judge("P3", "n*_mix in [45,60] AND n*_point in [60,80] AND AV_LB_32of32 in [0.80,0.88]",
          lambda: ({"n_star_mix": price["n_star_mix_U(0.9,1]"],
                    "n_star_point": price["n_star_point_0.95"],
                    "AV_LB_32of32": price["AV_LB_32of32"]},
                   45 <= price["n_star_mix_U(0.9,1]"] <= 60
                   and 60 <= price["n_star_point_0.95"] <= 80
                   and 0.80 <= price["AV_LB_32of32"] <= 0.88), price)

    def _p4():
        cells = kill["cells"]
        ms = [cells[c]["mean_stop_pairs"] for c in
              ("uv_diag45_paired", "vu_zonal_paired", "vu_merid_paired")]
        return ({"mean_stop_pairs": dict(zip(("uv_diag45", "vu_zonal", "vu_merid"), ms)),
                 "sum": sum(ms)}, all(m <= 6.0 for m in ms) and sum(ms) <= 18.0)
    judge("P4", "三判死格平均爆仓对数均<=6 AND 三格之和<=18", _p4, kill)

    def _p5():
        ps = {c: perm_j["cells"][c]["p_perm_plus1"] for c in perm_j["cells"]}
        return ({"p_perm_plus1": ps}, all(v <= 0.02 for v in ps.values()))
    judge("P5", "三判死格加一修正置换 p 均 <= 0.02", _p5, perm_j)

    judge("P6", "power_e@32 <= 0.05 AND power_e@204 in [0.20,0.75]",
          lambda: ({"power_e_32": power["P6_power_e_at_32"],
                    "power_e_204": power["P6_power_e_at_204"]},
                   power["P6_power_e_at_32"] <= 0.05
                   and 0.20 <= power["P6_power_e_at_204"] <= 0.75), power)

    def _p7():
        lb = akm["P7_champion"]["corrected_ci95"][0]
        ov = akm["P7_overlap_champ_vs_rank45"]
        return ({"LB_champ_corr": lb, "overlap45": ov},
                0.90 <= lb <= 0.995 and bool(ov))
    judge("P7", "0.90 <= 冠军校正后95%下界 <= 0.995 AND overlap45（双条件区间相交）", _p7, akm)

    judge("P8", "E67B 45° 富集校正后95%下界 >= 5",
          lambda: ({"enrich_corr_lb95": akm["P8_enrichment_diag45"]["enrich_corr_lb95"]},
                   akm["P8_enrichment_diag45"]["enrich_corr_lb95"] >= 5.0), akm)

    # ---- headline：真赌注 4 项（PREREG §1 计数纪律），P6 用子句 2 单判 ----
    if power is None:
        p6c2 = {"predicted": "0.20 <= power_e@204 <= 0.75", "observed": None, "verdict": "未跑"}
    else:
        try:
            v204 = power["P6_power_e_at_204"]
            p6c2 = {"predicted": "0.20 <= power_e@204 <= 0.75", "observed": v204,
                    "verdict": "中" if 0.20 <= v204 <= 0.75 else "不中"}
        except Exception as e:
            p6c2 = {"predicted": "0.20 <= power_e@204 <= 0.75",
                    "observed": f"字段异常: {e}", "verdict": "不中"}
    head_members = {"P1": V["P1"]["verdict"], "P4": V["P4"]["verdict"],
                    "P6_clause2": p6c2["verdict"], "P7": V["P7"]["verdict"]}
    headline = {
        "members": ["P1", "P4", "P6_clause2", "P7"],
        "P6_clause2": p6c2,
        "verdicts": head_members,
        "n_hit": sum(1 for x in head_members.values() if x == "中"),
        "n_of": 4,
        "note": "头条战绩只数真赌注 4 项（PREREG §1 冻结）；『8 中 X』总数只可进附录并同框分层表",
    }

    # ---- S_status（PREREG §2/§4）----
    def s_stat(fname):
        if os.path.exists(os.path.join(HERE, fname)):
            return {"status": "已跑", "output": fname}
        return {"status": "未跑", "reason": f"输出 {fname} 不存在"}
    S_status = {
        "S1": s_stat("S1_FLIP_TABLE.json"),
        "S2": {"status": "未跑", "reason": "无冻结脚本（PREREG 附录 B：无脚本即未跑）"},
        "S3": s_stat("S3_CROSSCHECK.json"),
        "S4": {"status": "未跑", "reason": "无冻结脚本；R9 random-walk 原文待核"},
    }

    n_hit = sum(1 for v in V.values() if v["verdict"] == "中")
    n_miss = sum(1 for v in V.values() if v["verdict"] == "不中")
    out = {
        "module": "verdict_cert_stat_ledger",
        "prereg_sha256": sealed_sha,
        "preflight": {"scripts_reverified": n_scripts, "inputs_reverified": n_inputs},
        "n_true_predictions": 8, "n_hit": n_hit, "n_miss": n_miss,
        "n_notrun": 8 - n_hit - n_miss,
        "headline_true_bets": headline,
        "per_prediction": V,
        "S_status": S_status,
        "note": "验证性断言（PREREG §0b）不计入战绩；被推翻的预测原样保留（PREREG §1）",
    }
    with open(os.path.join(HERE, "verdict.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
