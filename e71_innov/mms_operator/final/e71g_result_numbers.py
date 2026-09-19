#!/home/xinyuan/anaconda3/envs/numpy1/bin/python
# -*- coding: utf-8 -*-
"""E71G · RESULT 用派生数字（纯读 verdict.json / MMS_OPERATOR.json / POSTHOC_A2B.json，四则运算，无场计算）→ RESULT_NUMBERS.json"""
import json, hashlib
F = "/data/xinyuan/GOAI_ai4s_env/e71_innov/mms_operator/final"
V = json.load(open(f"{F}/verdict.json")); R = json.load(open(f"{F}/MMS_OPERATOR.json")); H = json.load(open(f"{F}/POSTHOC_A2B.json"))
A = {a["id"]: a for a in V["anchors"]}; P = {p["id"]: p for p in V["predictions"]}
S1 = R["S1_tiers"]; S2 = R["S2_refine"]; K = R["S3_knobs"]
N = dict(
  A2c_M_over_X=A["A2c"]["values"]["umax3d_row3"] / A["A2c"]["values"]["X_dt_signedmax_dev_u"],
  P1_harsh_over_rx069_EL2u=S1["harsh"]["EL2_u"] / S1["rx069"]["EL2_u"],
  P6_harsh_over_rx069_ELinfv=S1["harsh"]["ELinf_v"] / S1["rx069"]["ELinf_v"],
  S1_harsh_over_rx069_ELinfu=S1["harsh"]["ELinf_u"] / S1["rx069"]["ELinf_u"],
  S1_harsh_over_smooth_EL2u=S1["harsh"]["EL2_u"] / S1["smooth"]["EL2_u"],
  P3_p12_gap_smooth_minus_steep=S2["smooth"]["p12"] - S2["steep"]["p12"],
  S3_refsub_over_flat_EL2u=K["E_refsub"]["EL2_u"] / K["E_flat"]["EL2_u"],
  S3_orig_EL2u_over_true_amax=K["E_orig"]["EL2_u"] / K["E_flat"]["amax_u"],
  posthoc_rec1_DT_max_u_prsgrd=10.0 * H["records"][1]["max_abs_u_prsgrd_interior"],
  posthoc_rec1_DT_max_u_prsgrd_rel_to_row3=(10.0 * H["records"][1]["max_abs_u_prsgrd_interior"]) / A["A2"]["values"]["diag_row3"][3] - 1.0,
  n_pass=V["n_pass"], n_total=V["n_total"], n_refuted=V["n_total"] - V["n_pass"],
  src_sha256={f: hashlib.sha256(open(f"{F}/{f}", "rb").read()).hexdigest() for f in ["verdict.json", "MMS_OPERATOR.json", "POSTHOC_A2B.json"]})
json.dump(N, open(f"{F}/RESULT_NUMBERS.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(N, indent=1, ensure_ascii=False))
