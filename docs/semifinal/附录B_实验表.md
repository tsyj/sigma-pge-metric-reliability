# 附录 B · 实验编号 E40–E55 全表与数字出处

冲突处以 v5 主文为准；v3 合成稿仅作历史版本存于仓库 docs/semifinal/。

| 编号 | 目的 | 环境 / 算例数 | 关键数字 | 出处（仓库路径） |
|---|---|---|---|---|
| E40 | 风驱穷举判据 A（ρ≤−0.7 对 skill_vs_zero）+ B（配对抗刷≥0.9） | 风驱 58 r26 + 44 flat（32 对）；15376 候选 | 通过 204；基线 deep_rms_800 ρ=−0.99、B=0.000 | ledger/metric_search.json |
| E43 | LLM 提议判据 | 30 轮（20 轮格式有效） | 0 通过；随机基率 1.33% → 20 抽 0 中 p≈0.77 | ledger/agent_metric_v2_*.json |
| E44 | 内潮三轴扫描（预注册 13 + 加密 7） | 内潮 84 km 20 条 + 在档 3 臂 | u/v ρ=1.0/0.976/0.893（n=5/8/7；预注册口径 1.0/0.943/1.0，n=4/6/4） | e44_tide/analysis/E44_VERDICT_v2.json；PREREG_E44.md（sha 6ec975c0…） |
| E45 | 陷阱局 / 判据局 / 中性局 | Agent 下单 7 条 | 终选 ag_s3：残余流 3.25、功率 4.15 MW、u/v 3.46 | e44_tide/agent/RESULT_A_*.json、RESULT_An_*.json、RESULT_B_*.json |
| E47 | u/v 机制（分母贡献） | 22 臂 | 分母贡献 146–170% | e44_tide/analysis/E47_MECH.json |
| E48 | 内潮穷举三轴判据 | 19600 候选 | 报警型 2574（13.1%）/ 可刷型 2580 | e44_tide/analysis/E48_SEARCH.json |
| E49 | 风驱∩内潮交集 | — | 13（期望 26.8） | e44_tide/analysis/E49_CROSS.json |
| E50 | u/v 审计：帧敏感 / 窗均 / 盒宽 | 7 臂 + 500 km 5 臂 | 末帧全幅 39–66%；500 km 绝对值 16–18 | e44_tide/analysis/E50_UV_AUDIT.json |
| E52 | 经向风第三环境 | 56 条（22 带真值） | u/v A +0.17；v/u A −0.92 B 0.11；三重交集 0（期望 0.71） | e52/E52_CROSS.json、PROVENANCE.md |
| E53 | 配对规则与置换 | 7 锚臂 | 门 ×1.1/1.2/1.5 → 冻结修正 / m2 / m6 | e44_tide/analysis/E53_PAIRED_AND_STATS.json、RT2_FIXES.json:M19 |
| E54 | 换名 ×5 | 15 次调用 | 真名 3/5·4/5 → 匿名 1/5·1/5 | e44_tide/agent/E54_NAMESWAP.json |
| E55 | 45° 风（预注册 P1–P4） | 56 条（22 带真值） | P1 中、P2 反驳、P3 反驳、P4 中；u/v A −0.97 B 0.25；v/u A +0.10 B 0.82；纬向∩45°∩内潮 = 1（期望 0.79） | e55/PREREG_E55.md（sha ec1b1ecf…）、e55/E55_CROSS.json:prereg_check |
| 500 km 锚 | 逐模态远场功率 | 在档 5 臂 + 补跑 2 | m2/m4/m6 第二模 0.94/0.68/0.47；γ16 0.25；VISC4 3e8 0.52 | e44_tide/analysis/ANSWER_KEY_500KM.json、upstream/BANDTOLL_VERDICT.json |
| 审计原件 | 盒宽 / 时钟 | 在档 | 摆 7.24×；4.58→7.89 | e44_tide/analysis/upstream/DOMWIDTH_RESULT.json、PHASEFIX_TABLE.md |

经向∩内潮的 2 把：见 e52/E52_CROSS.json（family_merid 字段；三重列表为空即无一在纬向通过）；45°∩内潮的 3 把：w|all|max / w|d400|max、w|all|max / w|d200|max、u|s50|mean_abs / v|s50|rms（e55/E55_CROSS.json:merid_tide_list）。
