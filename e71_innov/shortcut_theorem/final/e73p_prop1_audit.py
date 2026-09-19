#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E73 · PROP1 二分支描述性审计（封存后，非预注册，不改判）：排得准（A≥0.7）者中，按 G（1 绝对量/0 比值型）分组的 B≥0.9 比例；纬/经/45°。输出 E73P_PROP1_AUDIT.json。"""
import hashlib, json, os
import numpy as np
ENV = "/data/xinyuan/GOAI_ai4s_env"; FIN = f"{ENV}/e71_innov/shortcut_theorem/final"
z = np.load(f"{ENV}/e71_innov/multienv_metrology/final/E71_FINAL_AXES.npz", allow_pickle=True)
G = z["G"]
out = dict(script="e73p_prop1_audit.py", script_sha=hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(),
           status="封存后描述性，非预注册，不改判", n=int(G.size), n_G1=int((G == 1).sum()), n_G0=int((G == 0).sum()))
for e in ("z", "m", "45"):
    A, B, D = z["A_" + e], z["B_" + e], z["D_" + e]
    acc = A >= 0.7
    row = {}
    for g in (1, 0):
        sel = acc & (G == g)
        row["G%d" % g] = dict(n_A_ge_0p7=int(sel.sum()), n_B_ge_0p9=int((sel & (B >= 0.9)).sum()),
                              frac_B_ge_0p9=round(float((B[sel] >= 0.9).mean()), 4) if sel.sum() else None,
                              median_D=round(float(np.median(D[sel])), 4) if sel.sum() else None)
    row["n_strict_A0p9_B0p9_by_G"] = {"G1": int(((A >= 0.9) & (B >= 0.9) & (G == 1)).sum()), "G0": int(((A >= 0.9) & (B >= 0.9) & (G == 0)).sum())}
    out["env_" + e] = row
json.dump(out, open(f"{FIN}/E73P_PROP1_AUDIT.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, ensure_ascii=False))
