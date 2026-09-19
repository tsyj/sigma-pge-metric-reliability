#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""
community_metric_trial 机械判分（预注册冻结件之一）
====================================================
只读 final/VALIDATION_{merid,diag45,bh93,zonal}.json（绝不读原始数据），
按 PREREG §4/§5 冻结的布尔式逐条判 P1–P10，输出 final/verdict.json。
运行前提：PREREG 已封存（.sha256 存在），四个 VALIDATION 文件已产出。
封存后本脚本一字不改；发现错误只记 DEVIATIONS.md。
"""
import hashlib, json, math, os, sys, time

OUT = "/data/xinyuan/GOAI_ai4s_env/e71_innov/community_metric_trial/final"
SEAL = f"{OUT}/PREREG_community_metric_trial.sha256"
PREREG = f"{OUT}/PREREG_community_metric_trial.md"

# ---- PREREG §4/§5 冻结常数 ----
FLOOR = math.log(1.001)
ETA_ZONAL = 0.025500820115274825
THR_ZONAL = max(2 * ETA_ZONAL, FLOOR)
P1_LO, P1_HI = 0.319, 0.519
P2_OR_MIN = 3.0
P3_RHO_MAX = 0.2
P4_MIN = 0.25
P5_MIN_HITS = 8
P5A_B_MAX, P5A_IMPR_MIN = 0.1, 20.0
P5B_AABS_MAX = 0.3
P8_MIN = 0.8
P910_FRAC = 0.8
P5A_Q = ["spec_hi", "hi_lo_ratio", "enstrophy_surf", "div_surf", "ke_total"]

def die(msg):
    print("拒绝：" + msg); sys.exit(2)

def require_seal():
    """与 validate_envs.py 同款封存门：.sha256 存在、封存件不可写、逐文件哈希相符。"""
    if not os.path.exists(SEAL):
        die("未封存（无 .sha256），判分不得先于封存")
    for p in (PREREG, f"{OUT}/validate_envs.py", f"{OUT}/score_prereg.py", SEAL):
        if not os.path.exists(p):
            die(f"封存件缺失 {p}")
        if os.stat(p).st_mode & 0o222:
            die(f"{p} 仍可写（未 chmod 444）")
    listed = {}
    for line in open(SEAL):
        parts = line.strip().split()
        if len(parts) == 2 and len(parts[0]) == 64:
            listed[os.path.basename(parts[1].lstrip("*"))] = parts[0]
    if not listed:
        die(".sha256 无哈希行")
    for base, h in listed.items():
        hh = hashlib.sha256(open(f"{OUT}/{base}", "rb").read()).hexdigest()
        if hh != h:
            die(f"{base} 哈希与封存记录不符")

def main():
    require_seal()
    J = {}
    for e in ("zonal", "merid", "diag45", "bh93"):
        p = f"{OUT}/VALIDATION_{e}.json"
        if not os.path.exists(p):
            die(f"缺 {p}（先跑 validate_envs.py）")
        J[e] = json.load(open(p))
    V = {"V1": J["merid"], "V2": J["diag45"]}
    verdict = dict(stamp=time.strftime("%F %T"),
                   prereg_sha=open(SEAL).read().strip().splitlines(),
                   inputs={e: f"{OUT}/VALIDATION_{e}.json" for e in J})

    def rec(pid, stmt, values, ok):
        verdict[pid] = dict(statement=stmt, values=values,
                            result=("PASS" if ok else "FAIL") if isinstance(ok, bool) else ok)

    # ---- P1 ----
    f2 = {k: v["blur_gameable"]["sigma2"]["frac_of_valid"] for k, v in V.items()}
    rec("P1", f"σ2 可刷比例(frac_of_valid) ∈ [{P1_LO},{P1_HI}] 于 V1 与 V2",
        f2, all(P1_LO <= x <= P1_HI for x in f2.values()))

    # ---- P2 ----
    orh = {k: v["isomorphism"]["table_sigma2"]["odds_ratio_haldane"] for k, v in V.items()}
    orr = {k: v["isomorphism"]["table_sigma2"]["odds_ratio_raw"] for k, v in V.items()}
    rec("P2", f"Haldane OR(σ2) ≥ {P2_OR_MIN} 于 V1 与 V2",
        dict(haldane=orh, raw=orr), all(x is not None and x >= P2_OR_MIN for x in orh.values()))

    # ---- P3 ----
    rho = {k: v["isomorphism"]["rho_blur2_D_sym"] for k, v in V.items()}
    rec("P3", f"|ρ(σ2美颜改善, D_sym)| ≤ {P3_RHO_MAX} 于 V1 与 V2",
        dict(rho_D_sym=rho, rho_D_u={k: v["isomorphism"].get("rho_blur2_D_u") for k, v in V.items()}),
        all(x is not None and abs(x) <= P3_RHO_MAX for x in rho.values()))

    # ---- P4 ----
    p4 = J["merid"].get("p4_zonalSA_cross_survivors", {})
    n_set, fh = p4.get("n_set", 0), p4.get("frac_hit")
    p4dev = (n_set != 88)
    rec("P4", f"纬向S_A∧经向两关集合（期望88）σ2 美颜中招比例 ≥ {P4_MIN}",
        dict(**p4, deviation_n_set_ne_88=p4dev),
        (fh is not None and fh >= P4_MIN) if n_set > 0 else False)

    # ---- P5 ----
    cells = {}
    hits = 0
    for envk, v in V.items():
        ex = v.get("exemplars", {})
        for q in P5A_Q:
            row = ex.get(q, {})
            ok = (isinstance(row.get("B_oriented"), (int, float))
                  and isinstance(row.get("blur2_oriented_impr_pct"), (int, float))
                  and row["B_oriented"] <= P5A_B_MAX
                  and row["blur2_oriented_impr_pct"] >= P5A_IMPR_MIN)
            cells[f"{envk}:{q}"] = dict(B_oriented=row.get("B_oriented"),
                                        impr=row.get("blur2_oriented_impr_pct"), hit=bool(ok))
            hits += bool(ok)
        row = ex.get("temp_drift", {})
        ok = (row.get("blur2_max_absrel") == 0.0
              and isinstance(row.get("A"), (int, float)) and abs(row["A"]) < P5B_AABS_MAX)
        cells[f"{envk}:temp_drift"] = dict(A=row.get("A"),
                                           blur2_max_absrel=row.get("blur2_max_absrel"), hit=bool(ok))
        hits += bool(ok)
        for q in ("budget_res_u", "budget_res_v"):     # (c) 观察项不计分
            r2 = ex.get(q, {})
            cells[f"{envk}:{q}(obs)"] = dict(A=r2.get("A"), counted=False)
    rec("P5", f"12 单元格命中 ≥ {P5_MIN_HITS}（(a)5基元×2环境, (b)temp_drift×2；(c)观察不计）",
        dict(hits=hits, cells=cells), hits >= P5_MIN_HITS)

    # ---- P6 ----
    mono = {}
    for envk, v in V.items():
        b = v["blur_gameable"]
        mono[envk] = [b["sigma1"]["frac_of_valid"], b["sigma2"]["frac_of_valid"],
                      b["sigma4"]["frac_of_valid"]]
    rec("P6", "frac(σ1) ≤ frac(σ2) ≤ frac(σ4) 于 V1 与 V2", mono,
        all(m[0] <= m[1] <= m[2] for m in mono.values()))

    # ---- P7 ----
    bh = J["bh93"]
    med = bh["sigma2"]["median_absdlog_uv"]
    p7 = med < FLOOR
    rec("P7", f"BH93 flat 静止：u/v 基元 σ2 |Δlog| 中位数 < ln1.001={FLOOR:.6f}（失败→全案降级）",
        dict(median_absdlog_uv=med, max_absdlog_uv=bh["sigma2"]["max_absdlog_uv"],
             n_uv_cells=bh["sigma2"]["n_uv_cells"],
             n_uv_cells_gt_floor=bh["sigma2"]["n_uv_cells_gt_floor"],
             median_all124_obs=bh["sigma2"]["median_absdlog_all124"],
             n_flat=bh["n_flat"]), p7)

    # ---- P8 ----
    di = {k: v["dual_immune"] for k, v in V.items()}
    rec("P8", f"双攻免疫幸存者非空且形状比占比 ≥ {P8_MIN} 于 V1 与 V2",
        di, all(d["n"] > 0 and d["shape_frac"] is not None and d["shape_frac"] >= P8_MIN
                for d in di.values()))

    # ---- P9/P10（条件：#20 落地） ----
    m20p = f"{OUT}/METRICS20_ZONAL.json"
    if os.path.exists(m20p):
        m20 = json.load(open(m20p))
        r = m20.get("rmse_uv", {}); s = m20.get("specdiv_uv", {})
        # 严格分数：frac_neg = frac(Δlog<0)、frac_pos = frac(Δlog>0)，Δlog==0 不计入
        # 任一侧（对 P9 与 P10 都不利，PREREG §5 锁死）
        need = ("dlog_sigma2_median", "frac_dlog_sigma2_neg", "frac_dlog_sigma2_pos", "n_runs")
        if all(k in r for k in need) and all(k in s for k in need):
            rec("P9", f"σ2 使 rmse_uv 变好：−median(Δlog) > {THR_ZONAL:.6f} ∧ frac(Δlog<0) ≥ {P910_FRAC}",
                r, (-r["dlog_sigma2_median"] > THR_ZONAL and r["frac_dlog_sigma2_neg"] >= P910_FRAC))
            rec("P10", f"σ2 使 specdiv_uv 变差：median(Δlog) > {THR_ZONAL:.6f} ∧ frac(Δlog>0) ≥ {P910_FRAC}",
                s, (s["dlog_sigma2_median"] > THR_ZONAL and s["frac_dlog_sigma2_pos"] >= P910_FRAC))
        else:
            rec("P9", "schema 不符", dict(file=m20p), "已预注册未执行")
            rec("P10", "schema 不符", dict(file=m20p), "已预注册未执行")
    else:
        rec("P9", "#20 未落地（9/18 12:00 门）", dict(file=m20p), "已预注册未执行")
        rec("P10", "#20 未落地（9/18 12:00 门）", dict(file=m20p), "已预注册未执行")

    # ---- 自检块（验证性断言，不计数） ----
    verdict["self_checks"] = dict(
        zonal_S_A_204=(J["zonal"]["S_A_env"] == 204),
        zonal_S_A_distinct_num_41=(J["zonal"].get("n_distinct_numerators_S_A_env") == 41),
        zonal_keys_124=(J["zonal"]["keys"] == 124),
        merid_p4_set_88=(n_set == 88),
        bh93_n_flat=bh["n_flat"],
        key_deviation={e: J[e].get("key_deviation") for e in ("merid", "diag45")})

    # ---- 汇总 ----
    executed = [p for p in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10")
                if verdict.get(p, {}).get("result") in ("PASS", "FAIL")]
    passed = [p for p in executed if verdict[p]["result"] == "PASS"]
    verdict["summary"] = dict(
        executed=len(executed), passed=len(passed),
        not_executed=[p for p in ("P9", "P10") if verdict.get(p, {}).get("result") == "已预注册未执行"],
        case_status=("OK" if verdict["P7"]["result"] == "PASS" else "DEGRADED_PENDING"),
        note="P7 失败=美颜关噪声门失效，全案降级为待定（PREREG §4.P7）；负结果原样发布")
    # 家族聚簇双口径回显（PREREG §9.3）：含 S_A_env 全集的独立分子数（机械指针）
    def dual_row(v):
        return dict(S_A_env=v["S_A_env"],
                    S_A_env_distinct_num=v.get("n_distinct_numerators_S_A_env"),
                    blur2_hits_in_S_A_env=v["blur_gameable"]["sigma2"]["n_in_S_A_env"],
                    blur2_hits_distinct_num=v["blur_gameable"]["sigma2"]["n_distinct_numerators_in_S_A_env"],
                    dual_immune_n=v["dual_immune"]["n"],
                    dual_immune_distinct_num=v["dual_immune"]["n_distinct_numerators"])
    verdict["distinct_numerator_duals"] = {k: dual_row(v) for k, v in V.items()}
    verdict["distinct_numerator_duals"]["zonal"] = dual_row(J["zonal"])

    json.dump(verdict, open(f"{OUT}/verdict.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({p: verdict[p]["result"] for p in
                      ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10")},
                     ensure_ascii=False, indent=1))
    print("case_status =", verdict["summary"]["case_status"])
    print(f"-> {OUT}/verdict.json")

if __name__ == "__main__":
    main()
