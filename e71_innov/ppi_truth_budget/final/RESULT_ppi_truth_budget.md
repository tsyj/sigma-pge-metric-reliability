# RESULT：ppi_truth_budget（T3 真值预算表＋rectifier 测谎）

> 【2026-09-17 复算更正】 本文件已按战报§5.1–5.3和既有复算收紧口径；所有原判分JSON与封存件保留。文末列逐项改动清单，历史数不得脱离更正引用。

执行目录：amax `/data/xinyuan/GOAI_ai4s_env/e71_innov/ppi_truth_budget/final/`
日期：2026-09-17（北京时间）。E70 未触碰；无 git 操作；未向官网提交；未使用赛题一/他队/e63 任何数据。

## 0. 封存

- 预注册：`final/PREREG_ppi_truth_budget.md`，sha256 `80e93dc96a0ffbf749d5c1ecc3e069f0b492638bdc7a47874e6c178ee9cc00a2`
- `final/.sha256`：16 个文件哈希＋时间戳 `2026-09-17T15:53:47+08:00`（chmod 444）
- 判分批启动 `2026-09-17T15:53:54+08:00`（晚于封存 7 秒；封存前 TB_BUDGET/TB_RECTIFIER/verdict.json 均不存在，seal.sh 内置检查）
- 封存前唯一运行过的部件：合成自检 `tb_selftest.py`（修订后重跑，输出与草稿版逐字节相同，sha256 9ce2144c…）、合成校准 `calib*.py`（草稿期）、`preseal_sets.py`（只读账本元数据，不读 err_rms/skill/代理读数）
- 判分批一次跑完，墙钟 72 秒（15:53:54→15:55:06，RUN_ALL.log）；无重跑。产出 sha256：TB_BUDGET.json 00f8187e…、TB_RECTIFIER.json 7ab44196…、verdict.json 3c513c1b…

路径前缀：`F=/data/xinyuan/GOAI_ai4s_env/e71_innov/ppi_truth_budget/final`，`PH=/data/xinyuan/GOAI_ai4s_env/e71_innov/ppi_truth_budget/posthoc`。

## 1. 检查意见落实（封存前，全部落实）

| 意见 | 处理 | 落点 |
|---|---|---|
| [重要] B_V⊆U 未申报 | 事实写明；R_V 选口径（甲）：ĥ_cal 在 U∖B_V（n=55）拟合，三路径统一为拟合集外残差；ĥ58 降为描述性；P7 改写为新增成员只来自换地形与缩短积分；(a) 总体含 3 个刷分黏性点写入申报 | PREREG §3-8、§8-11；tb_rectifier.py |
| [重要] P3/P2 逼近已知答案 | 原 P3 **未查表即**降级为 V8（不计分）；P2 加邻接钉死句（真赌注限于秩→线性落差、FPC 封顶、n=16 刀切膨胀） | PREREG §4、§1.1 V8；tb_verdict.py 只计 6 条 |
| [一般] 路径集合尺寸未预注册 | 新增只读元数据脚本 preseal_sets.py → PRESEAL_SETS.json → V7（含 \|B_V\|=3 踩线、ref 单臂） | PREREG §1.1 V7 |
| [一般] 封存门松动 | require_seal 对缺失/缺列/格式异常/时间戳≠1 一律拒跑；seal.sh 去掉 `\|\| true`，逐文件检查＋原子改名＋判分输出已存在即拒封。沙箱实测 5 种情形（无封存/全好/缺文件/哈希错/缺列）行为正确，沙箱已删 | tb_common.py、seal.sh |
| [一般] P4 守卫、P6 并列规则未申报 | §3-9 补两句 | PREREG §3-9 |
| [一般] inspect_20260917/ 沙箱 | 删除（删除前 sha256：tb_common.py e9801bc8…、TB_SELFTEST.json 47ff1604…、tb_selftest.py 599b4d2f…） | 已删 |
| 人工动作：读 PPSR | 摘要已读；正文要点经 WebFetch 摘要工具读 arXiv HTML v2（非本人逐字通读）；§8-1 进一步收窄（见 §5） | PREREG §8-1 |

## 2. 判决（verdict.json，机械输出，计数 6 条）

| 条目 | 布尔式 | 判定 | 关键读数（JSON 指针） |
|---|---|---|---|
| P1 覆盖率 | 15 格均值 PPI 覆盖最小值 ≥0.86 | **FALSE（推翻）** | 最小格 D、n=12：0.706（`F/TB_BUDGET.json#/budget_table/D_12/cov_mean`）；D 五档 0.715/0.706/0.764/0.809/0.886；u_max 0.881–0.896；E59 0.867–0.912 |
| P2 省真值 | saving(D,16) ≥2.0 | TRUE | 3.1856（`#/budget_table/D_16/saving`）；硬上限 N/n=3.625 |
| P4 分位点 | MAE_PPI(D,16) ≤ MAE_经典 | TRUE | 0.0 vs 0.0709 cm/s（θ_p90有4个并列真值，第51–54名；【2026-09-17 复算更正】；`#/budget_table/D_16/p90_mae_ppi`、`/p90_mae_classical`） |
| P5 测谎方向 | R_T>0∧R_V>0∧R_S>0 | **FALSE（推翻）** | R_T=0.1243、R_V=0.1406、R_S=−1.3748 cm/s（`F/TB_RECTIFIER.json#/paths/{terrain,visc,short}/rectifier_median`） |
| P6 测谎排序 | rank(R)=rank(M) | TRUE | R：short<terrain<visc；M：1.938<2.048<4.407（`#/multipliers`） |
| P7 朴素被骗 | 朴素覆盖≤0.50 ∧ PPI≥0.85 | **FALSE（推翻，两半都没过）** | 朴素 1.000、PPI 0.827（`#/mixture/cov_naive`、`/cov_ppi`） |

**合计：6 条真预测，3 条成立、3 条被推翻（P1、P5、P7），0 条 AMBIGUOUS**（`F/verdict.json#/n_true`、`/n_false`、`/n_ambiguous`）。被推翻的原样保留。

## 3. 验证性断言（不计分，全部核对通过）

- V1 |U|=58 ✓；V2 SPUR_KEY=u|all|rms ✓；V3 前 5 例复算 |Δ|=0.0 ✓（`F/TB_RECTIFIER.json#/v3_spotcheck`）；V4 E59 复刻行数 15376 ✓；V5 自检全绿 ✓。
- V6 倍数并列（口径不同，不互替）：本口径 换地形 2.048× / 黏性 4.407× / 缩短积分 1.938×（matched 4 对） vs 初赛 224×/62×/28×（`F/verdict.json#/verification_assertions_not_counted/V6_multipliers`）。
- **V6b账本单对比值已复现；图3(c)原图注、字段确切定义及28×仍待核** 【2026-09-17 复算更正】：账本 `obs.deep_rms_800`，VISC2=50 臂 e2_04ac56d390ce = 8.6737，VISC2=30000 臂 e2_9e957e1b688e = 0.13992，比值约62（61.99） 【2026-09-17 复算更正】（`F/TB_RECTIFIER.json#/V6b_init62_recompute/matches/0`）。即 62× 是账本 obs 字段 deep_rms_800（字段名指向深层 800 m 口径的 RMS，定义本条未另核）的单对比值，不是 u|all|rms 口径。
- V7 集合尺寸 7 项全部符合预期（`#/V7_path_sets/ok`=true）。
- V8（原 P3）：saving D 3.186 ≥ u_max 2.631，值为 true；在盘查表 Atr[u|all|rms]=0.95078、Atr[u|all|max]=0.94789，复刻 A 与 Atr 逐元一致（`#/V8_old_P3`）。两查表值只差 0.003，秩序层面其实近乎并列——降级是按「可查表派生」原则做的，未依赖查表结果。

## 4. 真值预算表要点（TB_BUDGET.json；N=58，θ_mean=5.468 cm/s，θ_p90=7.389 cm/s）

| 代理 | 总体 r²（PPSR 同框） | saving n=8/12/16/24/32 | PPI 均值覆盖 n=8…32 | 经典覆盖 |
|---|---|---|---|---|
| D=u\|all\|rms | 0.9546（无 FPC 渐近 22.0×） | 6.56/4.17/3.19/2.27/1.74 | 0.715/0.706/0.764/0.809/0.886 | 0.885–0.906 |
| u_max | 0.8723（7.83×） | 4.09/3.17/2.63/2.02/1.63 | 0.881/0.896/0.892/0.886/0.889 | 0.889–0.904 |
| E59 c*（机选，见过真值） | 0.5487（2.22×） | 1.71/1.67/1.62/1.45/1.30 | 0.867/0.888/0.886/0.912/0.898 | 0.904–0.917 |

指针：`F/TB_BUDGET.json#/descr_ppsr_like/<proxy>`、`#/budget_table/<proxy>_<n>/{saving,cov_mean,cov_mean_classical}`。E59 c* = v|d1500|max ÷ v|d800|rms，与 Y 相关 −0.741（`#/e59_diag`、`#/descr_corr/e59`）。
90 分位精确区间：n≤24 时 100% 抽样上侧无界（无信息），n=32 有界、宽中位 0.512 cm/s（`#/budget_table/D_32/width_p90_exact_med`）——分位维度连经典法也要 n≥32。

## 5. 被推翻条目的机理（POSTHOC，封存后探索性，不计分，见 DEVIATIONS D3）

- **P1**：最强代理 D 反而失覆盖。ĥ58 残差偏度 −3.06、超额峰度 9.33，最大 3 个残差（e2_16efdad9880d、e2_24d71298a83d、e2_5512d55442a2，全部是 AKV_BAK=1.0/0.1/0.3 的垂向黏性旋钮算例，D 高估其误差）占残差平方和 77.6%（`PH/POSTHOC_DIAG.json#/resid_h58`）。小样本多数抽不到这 3 点，刀切 se 在 n=8 只有经验 sd 的 0.52（`#/mc_reproduction_and_empirical_saving/D_8/jk_se_over_emp_sd`）；n=16 时 se 中位与经验 sd 持平（1.02），但 se 与估计值相依，覆盖仍只有 0.764。剔除 3 个 B_V 刷点后覆盖 0.688–0.892，**不是刷点造成的**（`#/sensitivity_U_minus_BV`）。
- **P2 的可信度**：按经验 MSE 算的 saving(D,16)=3.197，与名义 3.186 一致（`#/mc_reproduction_and_empirical_saving/D_16/saving_emp_mse`）；n=8 名义 6.56 被高估（经验 5.21）。结论：**点估计精度上 16 个真值≈51 个真值（总体58中4个默认配置输出逐位相同，互异55个；有限总体上限58） 【2026-09-17 复算更正】，但 90% 区间只兑现 76%**；D 代理要到 n=32 覆盖才 0.886。
- **P5**：缩短积分臂在 Y_bench 口径（最后一帧对第 1.0 天真值）下比同 (VISC2,seed) 的 8640 步臂更接近真值，ΔY = −1.44 至 −4.16 cm/s（e2_d8b5544d99c3按VISC2默认50应配e2_04ac56d390ce） 【2026-09-17 复算更正】（`#/short_path_mechanism/*/dY_short_minus_full`），误差降得比读数预测的还多，所以 rectifier 为负、测谎在这条路径上不报警。该路径5个run仅4个互异输出，去重R_S中位−1.191，5个残差全负（DEVIATIONS D4-1/D6）。 【2026-09-17 复算更正】
- **P7**：朴素臂填充器已用U内55个真值标定，混合95成员中58个是U内算例，不能当免真值朴素替代检验。平均偏差+0.109 cm/s、逐次t区间半宽中位0.213、覆盖1.000；PPI覆盖0.827。非预注册对照改用未标定f_D，朴素覆盖0、偏差−0.915（`../recompute/RC_POSTHOC_CHECK.json`）。 【2026-09-17 复算更正】

## 6. 近邻先例与收窄口径（PREREG §8-1 定稿）

- PPSR（Gao, Sicilia, Shi，arXiv:2608.26638 v2）已做：PPI 评估框架、λ̂ 由样本协方差估计、在 WMT 上以全集人工均分为真值做 1000 次覆盖率闭环验证（L 20–200、U=800、无放回），以及把「指标省多少标注」做成元指标 PPSR≈Pearson r²。据工具对正文的检索，未见 FPC、分位数、adversarial/gaming 等内容。→ 「省真值倍数」与「覆盖率闭环验证」**不再列为增量**，本表 saving 标为 PPSR 的有限总体版本（r² 与渐近 1/(1−r²) 同表印出）。
- Baumann（arXiv:2509.08825，本地 312）：朴素 LLM 替代的偏差已量化；本条P7填充器已用55个真值标定，不能据此判断该偏差现象是否复现。 【2026-09-17 复算更正】
- 剩余窄增量（据我们检索未见；范围：本地 417 篇全文库＋PPSR arXiv 页面/HTML，2026-09-17；外网系统检索**未做**）：①rectifier 作为刷分审计读数在三条实测刷分路径上的测谎（结果：两条为正、缩短积分为负，被推翻）；②小有限总体（N=58）下 FPC 封顶与高相关代理失覆盖的负结果；③预注册-封存-机械判分协议本身。

## 7. 未做 / 降级

- (c) 主动推断与共形保单：**未做**（排队尾，预注册零预测）。
- 外网系统检索（PPSR 引用者、FPC 版 PPI 先例）：**未做**，口径注明「本地库已查、外网待补」。
- PPSR 全文本人逐字通读：**未做**，引句来自 WebFetch 摘要工具。
- 按经验 MSE 重定义 saving、或换稳健方差修复 P1：**未做**（属新预注册范围，本条不临场改估计量）。

## 8. 上台口径

- **上台状态更正（2026-09-17）**：①62× 仍为候补：账本单对比值61.99已复现，但图3(c)原图注、字段确切定义与28×未核，转正条件未满足；不得以本节旧的“可上PPT”放行。与本口径D读数倍数2.05/4.41/1.94不互替。②「预注册 6 条，3 条被推翻」原样上台，头条用 P1：「最强免真值代理（r²=0.955）16 个真值的点估计精度约等于 51 个真值，但 90% 区间只兑现 76%；n=32 才 0.886——真值可定价，不可归零」（数字指针见 §2/§5，机理句须标 POSTHOC）；③P5/P7 负结果：「该真值口径不把缩短积分当变差，负R_S不能用于报警」「朴素填充器已用55个真值标定，覆盖1.000不支持免真值替代；PPI为0.827」 【2026-09-17 复算更正】。
- **只进附录**：P2（须与同格覆盖 0.764、上限 3.625 同页）、P4（MAE中位0 vs0.071；θ_p90上4个逐位相同真值占第51–54名，均7.389203，N=58互异55） 【2026-09-17 复算更正】、P6（排序一致但与 P5 冲突、2.048 vs 1.938 贴得近、visc 3 点 IQR 跨 0；通过版话术不用）、V8、E59 列（机选见过真值）、POSTHOC 全部机理。
- **不能用**：「rectifier 是被刷程度的带保证读数」；「PPI 区间在本基准有保证覆盖」；「不再需要真值」；「朴素替代被骗」；「覆盖率闭环验证/省标注倍数是我们首创」；任何「首次/第一」。

## 9. 运行合规记录

- 全部计算在 amax，systemd-run --user --scope MemoryMax=16G（封存门沙箱测试用 2G）＋nice 19＋线程 4；每批前查可用内存 469–472G、monitor/state/active 为空、coawstM_yagi_FRESH 无进程。
- 封存前合成自检比对时在 amax /tmp 写过一个临时副本并立即删除（未写其他目录）；封存门测试沙箱 `ppi_truth_budget/gatetest_tmp_20260917/` 已删除。
- 新增文件：F/preseal_sets.py、PRESEAL_SETS.json、.sha256、COLLECT.md、RUN_ALL.log、RUN_ALL.nohup、TB_BUDGET.json、TB_RECTIFIER.json、verdict.json、DEVIATIONS.md、本文件；PH/posthoc_diag.py、POSTHOC_DIAG.json。

## 2026-09-17 复算更正清单（当前引用口径）

本节旧说法仅为更正定位；以替代口径为准，不覆盖封存判分、不新增计算。

### 战报 §5.2 小错

| 条目 | 旧记录（已更正） | 当前替代口径 | 复算依据 |
|---|---|---|---|
| ppi_truth_budget V6b | 62.00 | 约 62（61.99）；62.0014 是 fig_llm 注释舍入值 8.674/0.1399 之比 | `recompute/RC_STATS.json` |
| ppi_truth_budget POSTHOC | ΔY 为 −1.44 到 −4.67 cm/s | −1.44 到 −4.16（错配改正后） | `recompute/RC_POSTHOC_CHECK.json` |
| ppi_truth_budget | 朴素区间半宽约 0.209 | 逐次抽样中位 0.213 | 同上 |

### 战报 §5.3 说过头

| 战报序号 | 旧说法（撤回/收紧） | 当前替代口径 | 条目 |
|---|---|---|---|
| 29 | 朴素替代没被骗 / Baumann 式偏差在本基准没复现 | 【不可用】写"朴素臂填充器已用 55 个真值标定" | ppi |
| 30 | 测谎读数在缩短积分路径上失灵 | 该口径不把缩短积分当作变差，这条路径不能靠测谎读数报警 | ppi |
| 31 | PPI 分位点 MAE 为 0（附录） | 注明 θ_p90 上有 4 个逐位相同的并列真值 | ppi |
| 32 | 16 个真值约等于 51 个（上限 58） | 注明 58 中 4 个是同一输出 | ppi |

详细偏差、敏感性指针与不重跑说明见同目录 `DEVIATIONS.md`。
