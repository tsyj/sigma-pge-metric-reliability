# DEVIATIONS：ppi_truth_budget（封存后记录；封存文件一个字节未动）

封存：`.sha256` 时间戳 2026-09-17T15:53:47+08:00，PREREG sha256 80e93dc96a0ffbf749d5c1ecc3e069f0b492638bdc7a47874e6c178ee9cc00a2。
判分批：2026-09-17T15:53:54 → 15:55:06（+08:00），一次跑完，无重跑、无代码修改。

## D1 代码与判则：无偏差
封存后未修改任何被封存文件；`tb_budget/tb_rectifier/tb_verdict` 各运行一次；verdict.json 为机械输出原样。

## D2 P6 话术选版与 P5 冲突（叙述层，判定不变）
§4 规定「按 verdict 选版不得混用」。P6=TRUE 应选「通过版」，但同批 P5=FALSE（缩短积分路径 R_S=−1.3748 cm/s，TB_RECTIFIER.json#/paths/short/rectifier_median），通过版「rectifier 就是被刷程度的带保证读数」与 P5 的推翻直接矛盾。预注册未预见 P5=FALSE∧P6=TRUE 的组合。处理：P6 判定照记 TRUE，不改；**通过版话术不上台**，P6 只进附录，并强制附注「排序一致，但缩短积分路径 rectifier 为负、换地形与缩短积分倍数仅差 2.048 vs 1.938、visc 路径 3 点 IQR 跨 0」。

## D3 封存后追加的探索性分析（不计分、不改 verdict）
`../posthoc/posthoc_diag.py` → `../posthoc/POSTHOC_DIAG.json`（sha256 b6d183e4…）：残差分布、同种子复现 MC 并算经验 MSE 口径的省真值倍数、剔除 B_V 的敏感性（新种子 20260919）、缩短积分与混合总体的机理读数。全部标 POSTHOC，只用于解释 P1/P5/P7 为何被推翻，不作为任何预测的补救。复现核对：15 格覆盖率与 TB_BUDGET.json 逐格一致（POSTHOC_DIAG.json#/mc_reproduction_and_empirical_saving/*/cov_reproduced）。

## D4 封存前未预见的数据事实（披露，不改判定）
1. B_S 中 e2_1ee7319797d7（VISC2=50）与 e2_d8b5544d99c3（动作无 VISC2 键）的 Y_bench 与 f_D 逐位相同（3.2268377904711274 / 3.4381816387176514，POSTHOC_DIAG.json#/short_path_mechanism/0 与 /3），缩短积分路径实际只有 4 个互异输出；中位数 −1.3748 恰为这对重复值。预注册按 run_id 计数，判定不变。
2. P2 的 saving 在有限总体口径下有硬上限 N/n = 58/16 = 3.625（n_eff≤N），预注册写了「n_eff≤N 封顶」但未印出数值；此处补印。
3. f_D（base_quantities u|all|rms）与账本 obs.u_rms 的总体相关为 0.99999999999999（TB_BUDGET.json#/descr_corr_obs_urms_fD），即 D 代理实际就是账本自带的 u_rms 读数。

## D5 合成校准的盲区（方法学教训，不改判定）
封存前合成校准（CALIB_SYNTH.md）只用了高斯残差的线性代理；真实总体 ĥ58 残差偏度 −3.06、超额峰度 9.33，最大 3 个残差（全是 AKV_BAK 旋钮算例）占残差平方和 77.6%（POSTHOC_DIAG.json#/resid_h58）。刀切方差在这种「少数点主导残差」的形态下失覆盖，合成自检未能预警。

## D6 · 2026-09-17 · 复算披露并列真值、配对错配与去重口径

`../recompute/RC_STATS.json#/Y_ties`：总体 N=58 中，默认配置的 4 个 run 输出逐位相同（互异 55 个）；θ_p90=7.389203437930458，排序第 51–54 名均为该值。P4 分位点 MAE 中位 0 必须附此限定；P2 的“16≈51 个真值（上限58）”同样附重复输出限定。

缩短积分路径 e2_d8b5544d99c3 动作未显式写 VISC2，按文件默认 50 应配 e2_04ac56d390ce；原按缺省 0 错配。ΔY 正确范围为 −1.44 到 −4.16 cm/s（该对 −4.1623656488），不是 −4.67。依据 `RC_STATS.json#/rect_F32/multipliers/short_semantic_pairs(roms.in VISC2)` 与复算脚本/战报 §3.2、§5.2。B_S 5 个 run 有 4 个互异输出；去重后 R_S 中位 −1.1910237617 cm/s（`#/rect_F32/short/R_median_dedup`），5 个残差均负，P5/P6 不变。缩短积分在最后帧对第1天真值的口径下更近，不能称测谎读数失灵。

P7 朴素填充器已用 U 内 55 个真值标定，95 个混合成员中 58 个来自 U；不能称“朴素替代没被骗/未复现 Baumann 偏差”。非预注册对照 raw f_D 填充覆盖为 0、偏差 −0.915 cm/s（`RC_POSTHOC_CHECK.json`）；朴素 t 区间逐次半宽中位 0.213（`RC_STATS.json#/rect_F32/mixture`）。V6b 原数相除为约62（61.99），62.0014 是注释舍入数之比；字段确切定义、图3(c)原图注和28×仍待核。本轮仅转录复算，不改任何封存 JSON，不补跑。
