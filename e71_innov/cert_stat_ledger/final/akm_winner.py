# -*- coding: utf-8 -*-
"""
akm_winner.py —— P7/P8：AKM 式赢家诅咒校正（插入式自助适配版，非正版 AKM；偏离清单内嵌）。

P7（E65 冠军）：
  场：E65_AXES.npz 的 A（15376 把）。A 轴口径 = -spearman(v26, S) 在 **58 条陡臂样本**上计算
  （e65_spurious_vs_true.py / e65.log「陡臂样本 58」；32 组是 B 轴配对口径，与 A 轴无关——PREREG §0b 核正）。
  Fisher-z 域 sigma = 1.03/sqrt(N_SAMP-3) = 1.03/sqrt(55)。
  插入式参数自助 B=4000：z*_i ~ N(z_hat_i, sigma^2)，重选赢家 w_b，
  gap_b = z*_{w_b} - z_hat_{w_b}（选择性高估的插入式分布）。
  校正点 = z_w - mean(gap)；校正 95% 区间 = [z_w - q97.5(gap) - 1.96*sigma, z_w - q2.5(gap) + 1.96*sigma]
  （选择偏移与抽样噪声两项都保留，保守合成；正版 AKM 为条件截断精确区间——见偏离清单）。
  overlap45（PREREG P7 双条件定义）：(champ_lb <= r45_ub) AND (r45_lb <= champ_ub)。
  第 45 名（A 降序 1-based；PREREG §0b：A>=0.99 共 45 把，第 45 名 0.990095）区间=无条件 Fisher-z 95%。

P8（E67B 45° 富集）：
  富集 = (140/204) / 底率 0.0295（落盘舍入值）。校正 = 胜率与底率双 Binomial 插入式自助（B=4000）取比值 2.5 分位。
  S_A 门在纬向选出、45° 评估，选择与评估分离 ⇒ 无赢家截断项（偏离清单注明）。
  口径冻结（PREREG P8）：上台引用观测富集 23.24（E67B 未舍入口径）；本脚本由舍入底率复算 ≈23.26 只作注脚。

输出 AKM_WINNER.json。
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(HERE, "PREREG_cert_stat_ledger.sha256")):
    raise SystemExit("拒跑：PREREG 未封存（缺 .sha256）——盘外产出无预注册效力")
OUT = os.path.join(HERE, "AKM_WINNER.json")
E65 = "/data/xinyuan/GOAI_ai4s_env/e65/E65_AXES.npz"
E67B = "/data/xinyuan/GOAI_ai4s_env/e67/E67B_RECIPE_TRANSFER.json"
B = 4_000
SEED = 20260917 + 6
N_SAMP = 58                       # e65 陡臂样本数（A 轴 Spearman 的 n；非 32 组配对口径）
SIGMA = 1.03 / np.sqrt(N_SAMP - 3)
Z = 1.959964

DEVIATIONS_FROM_AKM = [
    "①正版 AKM(Andrews-Kitagawa-McCloskey) 是条件截断正态精确推断；此处用插入式参数自助近似",
    "②Spearman 的 Fisher-z 正态近似，sigma=1.03/sqrt(n-3)，n=58 陡臂样本（Bonett-Wright）",
    "③赢家并列（max_A=0.998216 共 2 把）按首索引处理",
    "④候选间相关未建模，自助按独立场抽样；保守性未证明，如实标注",
    "⑤P8 无赢家截断项：S_A 门选于纬向、评估于 45°，选择与评估数据分离",
]


def fisher(a):
    a = np.clip(a, -0.999999, 0.999999)
    return np.arctanh(a)


def main():
    rng = np.random.default_rng(SEED)
    A = np.load(E65)["A"]
    # §0b 对表（改动=数据被换，直接崩）
    assert A.shape == (15376,) and not np.isnan(A).any(), "E65 A 轴形状/NaN 与 §0b 不符"
    assert int((A == A.max()).sum()) == 2 and int(np.argmax(A)) == 3922, "冠军并列/索引与 §0b 不符"
    assert int((A >= 0.99).sum()) == 45, "A>=0.99 数与 §0b 不符"
    z_hat = fisher(A)
    w0 = int(np.argmax(z_hat))                    # 首索引赢家
    z_w = float(z_hat[w0])
    gaps = np.empty(B)
    for b in range(B):                            # 15376 正态/轮，逐轮省内存
        z_star = z_hat + SIGMA * rng.standard_normal(z_hat.shape)
        wb = int(np.argmax(z_star))
        gaps[b] = z_star[wb] - z_hat[wb]
    bias = float(gaps.mean())
    lo = z_w - float(np.quantile(gaps, 0.975)) - Z * SIGMA
    hi = z_w - float(np.quantile(gaps, 0.025)) + Z * SIGMA
    champ = {
        "A_obs": float(np.tanh(z_w)),
        "corrected_point": float(np.tanh(z_w - bias)),
        "corrected_ci95": [float(np.tanh(lo)), float(np.tanh(hi))],
        "selection_bias_z": bias,
        "gap_q975_z": float(np.quantile(gaps, 0.975)),
        "naive_ci95": [float(np.tanh(z_w - Z * SIGMA)), float(np.tanh(z_w + Z * SIGMA))],
    }
    # 第 45 名（降序 1-based）无条件区间
    a_sorted = np.sort(A)[::-1]
    a45 = float(a_sorted[44])
    z45 = float(fisher(np.array([a45]))[0])
    r45 = {"A_obs": a45,
           "uncond_ci95": [float(np.tanh(z45 - Z * SIGMA)), float(np.tanh(z45 + Z * SIGMA))]}
    # overlap45：双条件区间相交（PREREG P7 精确定义）
    champ_lb, champ_ub = champ["corrected_ci95"]
    r45_lb, r45_ub = r45["uncond_ci95"]
    overlap = bool((champ_lb <= r45_ub) and (r45_lb <= champ_ub))
    # ---- P8 ----
    e67 = json.load(open(E67B))
    k, nS = int(e67["diag45"]["S_A"]["n"]), int(e67["size_S_A"])          # 140/204
    base = float(e67["diag45"]["base_rate"])                              # 0.0295（落盘舍入）
    n_all = int(e67["n_diag45"])                                          # 15376
    rate_bs = rng.binomial(nS, k / nS, size=B) / nS
    base_bs = rng.binomial(n_all, base, size=B) / n_all
    enr_bs = rate_bs / base_bs
    p8 = {
        "enrich_obs_from_rounded_base": (k / nS) / base,
        "enrich_obs_stage_caliber_e67b": float(e67["diag45"]["S_A"]["enrich"]),
        "caliber_note": "上台引用 23.24（E67B 未舍入口径）；本行 from_rounded_base≈23.26 只作复算注脚（PREREG P8 冻结）",
        "enrich_corr_lb95": float(np.quantile(enr_bs, 0.025)),
        "enrich_corr_ub95": float(np.quantile(enr_bs, 0.975)),
        "k": k, "n": nS, "base_rate": base,
    }
    res = {
        "module": "P7P8_akm_winner",
        "B": B, "seed": SEED, "sigma_fisher_z": float(SIGMA), "n_samples_A": N_SAMP,
        "n_samp_note": "A 轴 n=58 陡臂样本（e65 源码核）；32 组是 B 轴配对口径，与 A 轴无关",
        "champion_index_first_argmax": w0,
        "P7_champion": champ,
        "P7_rank45": r45,
        "P7_overlap_champ_vs_rank45": overlap,
        "P8_enrichment_diag45": p8,
        "akm_style_deviation_list": DEVIATIONS_FROM_AKM,
        "note": "置换 p 与本校正同图并陈但回答不同问题（PREREG R8）",
    }
    with open(OUT, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
