# 附录 B · 实验编号 E40–E58 全表与数字出处

冲突处以 v6 主文为准；v3 合成稿仅作历史版本存于仓库 docs/semifinal/。

| 编号 | 目的 | 环境 / 算例数 | 关键数字 | 出处（仓库路径） |
|---|---|---|---|---|
| E40 | 风驱穷举判据 A（ρ≤−0.7 对 skill_vs_zero）+ B（配对抗刷≥0.9） | 风驱 58 r26 + 44 flat（32 对）；15376 候选 | 通过 204；基线 deep_rms_800（即 u|d800|rms）纬向 ρ=−0.963、经向 ρ=−0.990，两者 B 均=0.000 | ledger/metric_search.json（纬向）、ledger/metric_search_merid.json（经向） |
| E43 | LLM 提议判据 | 30 轮（20 轮格式有效） | 0 通过；随机基率 1.33% → 20 抽 0 中 p≈0.77 | ledger/agent_metric_v2_*.json |
| E44 | 内潮三轴扫描（预注册 13 + 加密 7） | 内潮 84 km 20 条 + 在档 3 臂 | u/v ρ=1.0/0.976/0.893（n=5/8/7；预注册口径 1.0/0.943/1.0，n=4/6/4） | e44_tide/analysis/E44_VERDICT_v2.json；PREREG_E44.md（sha 6ec975c0…） |
| E45 | 陷阱局 / 判据局 / 中性局 | Agent 下单 7 条 | 终选 ag_s3：残余流 3.25、功率 4.15 MW、u/v 3.46 | e44_tide/agent/RESULT_A_*.json、RESULT_An_*.json、RESULT_B_*.json |
| E47 | u/v 机制（分母贡献） | 22 臂 | 分母贡献（相对基准臂的比值区间；按 E47_MECH.json 重算：以 pf_dj 为基 116–157%，以 pf_v4 为基 129–231%。此前正文的 146–170% 取自 e47_mech.py 的 stdout，未落盘，已改为可复算口径） | e44_tide/analysis/E47_MECH.json |
| E48 | 内潮穷举三轴判据 | 19600 候选 | 报警型 2574（13.1%）/ 可刷型 2580 | e44_tide/analysis/E48_SEARCH.json |
| E49 | 风驱∩内潮交集 | — | 13（期望 26.8） | e44_tide/analysis/E49_CROSS.json |
| E50 | u/v 审计：帧敏感 / 窗均 / 盒宽 | 7 臂 + 500 km 5 臂 | 末帧全幅 39–66%；500 km 绝对值 16–18 | e44_tide/analysis/E50_UV_AUDIT.json |
| E52 | 经向风第三环境 | 56 条（22 带真值） | u/v A +0.17；v/u A −0.92 B 0.11；三重交集 0（期望 0.71） | e52/E52_CROSS.json、PROVENANCE.md |
| E53 | 配对规则与置换 | 7 锚臂 | 门 ×1.1/1.2/1.5 → 冻结修正 / m2 / m6 | e44_tide/analysis/E53_PAIRED_AND_STATS.json、RT2_FIXES.json:M19 |
| E54 | 换名 ×5 | 15 次调用 | 真名 3/5·4/5 → 匿名 1/5·1/5 | e44_tide/agent/E54_NAMESWAP.json |
| E55 | 45° 风（预注册 P1–P4） | 56 条（22 带真值） | P1 中、P2 反驳、P3 反驳、P4 中；u/v A −0.97 B 0.25；v/u A +0.10 B 0.82；纬向∩45°∩内潮 = 1（期望 0.79） | e55/PREREG_E55.md（sha ec1b1ecf…）、e55/E55_CROSS.json:prereg_check |
| 500 km 锚 | 逐模态远场功率 | 在档 5 臂 + 补跑 2 | m2/m4/m6 第二模 0.94/0.68/0.47；γ16 0.25；VISC4 3e8 0.52 | e44_tide/analysis/ANSWER_KEY_500KM.json、upstream/BANDTOLL_VERDICT.json |
| E56 | BH93 静止态检验（预注册 A9） | 14 条（7 档 VISC2 × 2 地形） | 平底全档 u_max=0.0000；陡海山 99.72→18.79（ρ=−1.000, p=0.0004）；A1 抗刷 0.000；代理夸大 1.69 倍；技巧全程为负 −8.48→−1.46（P3 被反驳） | e56/prereg_e56.md（sha 7792b30e…）、e56/E56_BH93.json、E56_VERDICT.json |
| E57 | 双目标 (A,B) 全候选分析 | 15376 候选 | ρ(A,B)=−0.674；两关同过 204 vs 独立期望 2159（贫化 10.6×）；Pareto 前沿 5 点；乌托邦角为空；阈值 (0.5,0.7)→(0.9,1.0) 通过数 739→9 | e44_tide/analysis/E57_PARETO.json、E57_AB.npz、fig_pareto.png |
| E58 | 判定三值化 + 信噪比门 | 零机时 | 抗刷率按 Wilson CI 三值化：u/v 纬向 32/32 CI[0.893,1.000] → **待定**；经向 25/28 CI[0.728,0.963] → 待定；45° 7/28、v/u 纬向 7/32、v/u 经向 3/28 → 确定死。SNR 门（IQR/中位数，32 臂）：深水温度 0.3% vs u/v 24% / 残余流 28% / 环带功率 445% | e44_tide/analysis/E58_TRIVALENT.json |
| E59 | 无真值特征预测排序力（预注册） | 15376 训练(纬向) + 15376 测试(经向) | 跨环境 AUC=0.8706；单特征 f1 抗刷率 AUC=0.2005（负向）、f7 旋钮秩相关 0.6752；P3 未命中：precision@204=0.0882 < 基率 0.2797216441207076；命中率非单调，峰值 0.8306 后回落至 0.6906（最极端 0.5% 为 0.052）；两条事后解释（方向不可测、外推失败）均被数据推翻并留档 | e59/PREREG_E59.md（sha 533c3062…）、e59/E59_TRUTHFREE.json、E59B_POSTHOC.json |
| E60 | 抗刷率在陡度轴上的稳定性（预注册） | 56 条（4 档 rx0 × 2 地形 × 7 档 VISC2），全部完赛 | B≥0.9 集合的 Jaccard 0.817–0.968、秩相关 0.734–0.953（**P1 赌 <0.5 被推翻**）；四档通过比例 44.4–44.6%；u|d800|rms 全陡度 B=0.000（P2 命中）；P4 未命中（风驱下平底有真实风生流约 14 cm/s，预注册前提写错） | e60/PREREG_E60.md（sha af8fe044…）、e60/E60_RX0.json、E60_VERDICT.json |
| E61 | Agent 在同等信息条件下挑尺子（预注册） | 8 局 × 40 候选，deepseek-v4-pro | 命中率 逻辑回归 0.675 > 低B启发式 0.500 > Agent 0.412 > 随机 0.283；**P2 命中**（8 局无一胜出，符号检验 p=1.00）；**P1 未命中**（Agent>随机 p=0.1445，不显著）；P3 部分推翻（抗刷率仅 5/8 被引用，方向 4 局用对 1 局用反）；事后分组：说对方向 3 局 0.60、说反/没说清 5 局 0.30 | e61/PREREG_E61.md（sha 67d3ede0…）、e61/E61_AGENT_PICKS.json、E61B_POSTHOC.json、trajectory_e61.jsonl |
| E62 | A7 换名局跨模型复核 | 3 条件 × 5 次，deepseek-v4-flash（同题面、同 n） | 核心效应逐位复现：环带功率真名被信 3/5 → 匿名 1/5（与 pro 完全一致）；换名局穿外衣的 u/v 被疑 5/5（pro 4/5）；阴性对照两模型均稳定；**模型依赖部分**：真名下 u/v 被疑 pro 4/5 vs flash 2/5 | e44_tide/agent/E62_NAMESWAP_XMODEL.json、analysis/E62_XMODEL_COMPARE.json、e44_tide/e62_nameswap_xmodel.py |
| 时间台账 | 算例时刻记录 | 43 条 | e44/e52/e55 用 DONE 文件 mtime（当时未写 T_START）；e56 为运行时写入的真起止时刻。差异如实记录，不追溯补造 | e44_tide/analysis/TIME_LEDGER.json |
| 审计原件 | 盒宽 / 时钟 | 在档 | 摆 7.24×；4.58→7.89 | e44_tide/analysis/upstream/DOMWIDTH_RESULT.json、PHASEFIX_TABLE.md |

经向∩内潮的 2 把：见 e52/E52_CROSS.json（family_merid 字段；三重列表为空即无一在纬向通过）；45°∩内潮的 3 把：w|all|max / w|d400|max、w|all|max / w|d200|max、u|s50|mean_abs / v|s50|rms（e55/E55_CROSS.json:merid_tide_list）。


---

# 参考文献（正文引用，按首次出现顺序）

数值海洋学侧：
1. Strathern M. (1997) "Improving ratings": audit in the British University system. *European Review* 5(3):305–321.（古德哈特定律的经典表述）
2. Haney R.L. (1991) On the pressure gradient force over steep topography in sigma coordinate ocean models. *JPO* 21:610–619. DOI 10.1175/1520-0485(1991)021<0610:OTPGFO>2.0.CO;2
3. **Beckmann A. & Haidvogel D.B. (1993)** Numerical simulation of flow around a tall isolated seamount. Part I. *JPO* 23:1736–1753. DOI 10.1175/1520-0485(1993)023<1736:NSOFAA>2.0.CO;2（本作品 A9 的社区标准来源）
4. Mellor G.L., Oey L.-Y. & Ezer T. (1998) Sigma coordinate pressure gradient errors and the seamount problem. *JTECH* 15:1122–1131. DOI 10.1175/1520-0426(1998)015<1122:SCPGEA>2.0.CO;2
5. Shchepetkin A.F. & McWilliams J.C. (2003) A method for computing horizontal pressure-gradient force in an oceanic model with a nonaligned vertical coordinate. *JGR* 108(C3):3090. DOI 10.1029/2001JC001047
6. Berntsen J. (2002) Internal pressure errors in sigma-coordinate ocean models. *JTECH* 19:1403–1414. DOI 10.1175/1520-0426(2002)019<1403:IPEISC>2.0.CO;2
7. Schifano V. et al. (2025) 陡地形区数值混合与参数化混合的不一致. *JAMES*. DOI 10.1029/2024MS004768
8. Stow C.A. et al. (2009) Skill assessment for coupled biological/physical models of marine systems. *J. Marine Systems* 76:4–15. DOI 10.1016/j.jmarsys.2008.03.011（RMSD 奖励方差低估）
9. Gleckler P.J., Taylor K.E. & Doutriaux C. (2008) Performance metrics for climate models. *JGR* 113:D06104. DOI 10.1029/2007JD008972（换一个变量排名就翻）

评测方法学侧：
10. **Skalse J. et al. (2022)** Defining and Characterizing Reward Hacking. *NeurIPS 2022*. arXiv:2209.13085（定理 1 预言"没有一行全绿"；Def 1 = 我们的 A1）
11. **Karwowski J. et al. (2023)** Goodhart's Law in Reinforcement Learning. arXiv:2310.09144（命题 2 给 A8 理论名字；推论 1 说明"门"是定理性质）
12. Manheim D. & Garrabrant S. (2018) Categorizing Variants of Goodhart's Law. arXiv:1803.04585（四分类；正文使用其术语处已核对定义）
13. Blum A. & Hardt M. (2015) The Ladder: A Reliable Leaderboard for Machine Learning Competitions. arXiv:1502.04585（藏起来的 holdout 在自适应查询下必被过拟合）
14. Sai A.B. et al. (2021) Perturbation CheckLists for Evaluating NLG Evaluation Metrics. *EMNLP 2021*. arXiv:2109.05771（多指标 × 多扰动 × 没有一把全过的同构体裁）
15. Ye J. et al. (2024) Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge (CALM). arXiv:2410.02736（Compassion-Fade = A7 的先行）
16. Starace G. et al. (2025) PaperBench. arXiv:2504.01848（JudgeEval：唯一正面"给评分器打分"，但依赖与人类金标一致）
17. Chan J.S. et al. (2024) MLE-bench. arXiv:2410.07095（抹掉赛事出处的**阴性**对照 8.5%→8.4%）
18. Workflow Closure Is Not Scientific Closure in Autonomous Research. arXiv:2605.26200（closure through the world；H 的 Weak/Mitigated 分级）
19. CVEvolve: Autonomous Algorithm Discovery. arXiv:2605.11359（开发集/holdout 分离曲线）
20. AEvo: Harnessing Agentic Evolution. arXiv:2605.13821（隐藏评测器的现行做法；去 harness 后 2/3 进入 reward hacking）
21. CMIP-Forge. arXiv:2606.17076（相位论证换度量并改变排序 = A4 的先行；同模型评审 = 零认知独立性）
22. ScientistOne: Chain of Evidence. arXiv:2605.26340（Case 1 型失效）
23. Kosmos. arXiv:2511.02824（"不存在可靠评估 claim 准确性的自动方法"）
24. FIRE-Bench. arXiv:2602.02905（Agent 不会构造控制组）
25. Moran & Morato (2025) Exploration–Exploitation in Active Learning with Surrogate Reliability. arXiv:2508.18170（单标量压双目标失真 = 4.1 的标准表述）
26. Do We Need the Entire Pareto Front? arXiv:2604.09417（多目标下全支配点近乎先验为空）
27. Foucart C. et al. (2023) Deep RL for Adaptive Mesh Refinement. arXiv:2103.01342（TrueError 不是性能上界 = 好排序器不等于好尺子）

> 引用核验：数值海洋学侧 DOI 经 Crossref 核实；方法学侧 arXiv 编号取自本团队文献库 `资料/文献/`（manifest 含标题与抓取记录）。**2026 年新条目在提交前逐条打开 abs 页确认。**
