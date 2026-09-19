# DEVIATIONS · negctrl_surrogate

## D1 · 2026-09-17 · H 标签跨域撞名借用（阻断级）

冻结规则按 run_id 从 regraded_v2.jsonl 查 H，但该文件 65 行都是纬向 r26steep；run_id 按 action 哈希生成，在风向之间撞名。经向/45° 的所谓 28/28 skill_vs_zero 实为纬向标签，两域冻结 sweep 的 skill_trace 完全相同。留出账本自带 hidden 只有 22/28 对，缺少真值的 6 个 AKV_BAK 陡臂不能当留出真值。PREREG §2 的标签来源叙述事实有误，封存件原样保留。

| 预测 | 冻结纬向标签口径 | 仅 22 对本域真值（经向 / 45°） |
|---|---|---|
| P1 | ρ=0.8012 / 0.8711，TRUE | 0.999513 / 0.990946，TRUE；超出点预测区间 0.80–0.95 |
| P2 | 74/82 / 36/82，TRUE | 0/82 / 0/82，FALSE |
| P3 | −0.3533 / −0.3697，TRUE | −0.303496 / −0.357635，TRUE |
| P4 | 0.7247 / 0.6612，FALSE | 0.357425 / 0.422925，TRUE |
| P6 | 0.5643 / 0.4530，FALSE | 不用 H，不变 |
| P7 | τ=1.0 / 1.0，TRUE | τ 仍 1.0；降为验证性断言 |

4T/2F 的总数不变，P2/P4 互换；冻结 TRUE/FALSE 均不覆盖。主敏感性指针是 `../recompute/RC_PREDICT.json#/variants/own_skill|ms`（own_err|ms 同值）。`RC_EXTRA.json` 的 `frozen_labels_on_22_own_pairs` 仍用纬向标签，仅删掉 6 对，不能误引为本域真值版；其 P4=0.359684/0.433089，与本域真值版不同。该对照同样令 P2/P4 互换，支持原结论由 6 对 AKV_BAK 驱动（另见复算 `rc_akv_check.py` 的已有日志）。

## D2 · 2026-09-17 · 已知量与报告纪律

P7 使用的 H7 就是封存于 E72_SELFTEST_ZONAL.json 的纬向参考轨，τ=1.0 为已知答案，改归验证性断言；V4（原 P5）仍为描述性。multienv 在 14:32:15 已落盘 45° 轴，早于本条 14:55:35 封存；“留出”仅指本条封存前未读取逐候选读数，不是全项目未见。

**从本更正起，不再运行 e72_valid.py、e72_verdict.py 或 run_valid.sh，不再重跑封存判分。** require_seal 在 DEVIATIONS.md 存在时会允许脚本哈希不符，不能把登记偏差当成重跑授权。本次只转录已有复算。P1 置换口径写 p<0.001（2000 次零次超过）；X/Y 受排序影响，stable 为 73/82、34/82；P6 仅边际越线且两域方向相反，不作止刷药证据。
