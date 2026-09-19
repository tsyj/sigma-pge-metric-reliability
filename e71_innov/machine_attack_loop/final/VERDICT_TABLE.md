> 【2026-09-17 复算更正】 本表为冻结输出的历史呈现；P6应引用复算0/46=0、Wilson95[0,0.077]，仍REFUTED。LB=90 FAKE_OFFTASK+46 REAL，R3对46条全部不可判；loader真值字段错误详见DEVIATIONS D1。

# 机器攻击存档回审 —— 一页判定表（冻结输出的文字更正，2026-09-17）

PREREG sha256: `09c5438ab3d4c138…`  脚本 sha256: `88568d47fd68b6b1…`
封存时间戳: 2026-09-17T14:49:08+08:00

| # | 布尔式 | 关键数字 | 判定 |
|---|---|---|---|
| P1 | `Wilson95下界(caught \| LB∧FAKE_T1主档) >= 0.75` | 90/90 Wilson95=[0.959,1.000] | **CONFIRMED** |
| P2 | `#{LB ∧ R3==PASS ∧ (FAKE_TRUTH@T1 ∨ FAKE_TRUTH@T2)} == 0` | escapes=0 | **CONFIRMED** |
| P3 | `caught/\|LB\| ∈ [0.55, 0.85]（口径乙）` | 90/136=0.662 | **CONFIRMED** |
| P4 | `#{R3==NOT_AUDITABLE}/#{LB∧过R1R2} >= 0.60` | 46/46=1.000 原因={'no_flat_pair_at_same_knobs': 36, 'no_flat_default_ref_at_same_ntimes': 10} | **CONFIRMED** |
| P5a | `校准：Fisher单侧p(变好看率: A∪A2 > B∪C) < 0.05` | p=0.024 表=[[84, 0], [52, 4]] | **CALIBRATION_CONSISTENT** |
| P5b | `校准：FAKE占比(LB∩A∪A2) >= 1.5 × FAKE占比(LB∩B∪C)（边界规则见 §3.5）` | AA2=0.810 vs BC=0.423 | **CALIBRATION_CONSISTENT** |
| P6 | `误伤率(caught\|LB∧REAL_T1主档) ∈ [0.10, 0.45]` | 0/46=0（2026-09-17更正） | **REFUTED** |
| P7 | `#{caught_by_R2 \| ntimes<8640} == n（盘点预期 19/19；实数≠19 记 DEVIATIONS 不改布尔式）` | 19/19 (盘点 19) | **CONFIRMED** |
| P8 | `探索性：uv_ratio 子集方向 vs E40 (1.151/1.012/2.729)，只描述` | n_uv=40 | **EXPLORATORY** |

两个抓取率分母口径：甲=变好看∧FAKE（试点 17/17）；乙=全部变好看含 REAL（试点 24/44）。
真预测共 6 条（P1–P4、P6、P7）。P5a/P5b 为样本内校准不计数：同批留出的按条件聚合数
初赛已发表（llm_matrix.json / README 90%→18% / fig_loop 89.8%→7.5%，PREREG §3.5/§4）。P8 探索性。
P4/P7 接近构造性（PREREG §3 诚实限定），不当强预测卖。
本表只测判死侧；无论结果如何不得写“协议经受住攻击/协议被认证”。
【2026-09-17 复算更正】 原封存判分脚本不再重跑；更正数直接引用 `recompute/RECOMPUTE.json` 与 `DEVIATIONS.md`，不覆盖冻结 verdict.json。
