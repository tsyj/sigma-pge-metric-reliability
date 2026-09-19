# RESULT · mms_operator（E71G 最小闭环：复刻＋三锚＋旋钮判决表＋6 条真预测）

> 【2026-09-17 复算更正】 本文件已按战报§5.1–5.3和既有复算收紧口径；所有原判分JSON与封存件保留。文末列逐项改动清单，历史数不得脱离更正引用。

日期 2026-09-17（北京时间）。全部数字由脚本算出，附 JSON 指针（RFC 6901；V=verdict.json，M=MMS_OPERATOR.json，
H=POSTHOC_A2B.json，N=RESULT_NUMBERS.json，均在 amax `/data/xinyuan/GOAI_ai4s_env/e71_innov/mms_operator/final/`）。

## 0. 封存与执行

- 封存：`PREREG_mms_operator.md` sha256 `60865d479350418d88eca135f350f20a9196d5d98464725a03b1a15937eec3f4`，
  `date -Is` = 2026-09-17T16:03:36+08:00，文件与 .sha256 均 chmod 444。封存前无 MMS_OPERATOR.json / verdict.json / clone_1step（封存命令同一行 ls 核过）。
- 执行：`e71g_run.sh` 16:03:41→16:03:44，墙钟 3.2 s；每步前安全三查通过（active 空、无 coawstM_yagi_FRESH、可用 469G > 140G）；
  clone 一步运行、scan、verdict 各跑一次，均在 `systemd-run --user --scope -p MemoryMax=16G nice -n 19` 内，线程 ≤4。未碰 e70/ 与任何既有实验目录（E56 只读）。
- 脚本 sha 门控生效：V `/code_sha_match_scan` = true；五脚本 sha 见 V `/code_sha`，与 PREREG §7 表一致（否则 scan/verdict 拒跑）。

## 1. 检查意见落实（均在封存前完成；修正前草稿留 `drafts_pre_review/`）

| 意见 | 落实 |
|---|---|
| [阻断] A2 锚源口径判错 | A2 改为深度平均口径：DT·max_内点\|Σ(Hz_u·a_u)/ΣHz_u\| 对步 1 ubarmax=1.869474e-3，带宽 [0.5,2] 不变；全文「步 1 u_max」改「步 1 ubarmax」并写明 ana_diag 写出序与带符号 MAX；§8.1 注明首步正压量 vs 日 1 三维绝对值不混称；逐点值与深度平均值同落盘 |
| [重要] scan 用 u、v 合并最大 | ratio 只用 u 向深度平均；v 向与逐点值并列记录不判 |
| [重要] RHO_SURF 陈述错误 | §1 表与 replica 头注/docstring 改为「RHO_SURF 已定义；其项在 ζ≡0 下逐点恒零，按 ζ=0 合法略去（prsgrd.f90 L219-222 / L259-261）」；另核 run.log CPP 列表确认 WEC_VF/ATM_PRESS/TIDE/WET_DRY/WJ_GRADP 无 |
| [重要] 自家近邻未入清单 | §4.5 增列 harden_results(H1/H4/H6)、rest_sweep_results、offline_N_sweep 系列、**pgferr_20260830(Z10) 离线复刻＋diag 标定＋参考态扣除 9.13×**、pgferr_frames、analytictruth、dxconverge；P1/P6 反向条款自引 H1 高 rx 非单调；P5 标「弱赌注，Z10 同方向先例」；§0/§8.9 近邻同框 |
| [一般] pycache | 封存前 rm -rf final/__pycache__；PREREG 头部申报「起草时曾 import 冒烟、零计算」；此后一律 python -B |
| [一般] verdict schema 不一致 | 代码改为 anchor_pass / prediction_pass、顶层 code_sha；§7 逐字列出字段，二者一致 |
| 自查新增 | clone 脚本 `pgrep -x`（进程名截断 15 字符永不匹配）改 `pgrep -f`；`free -g` 在中文 locale 下匹配不到 Mem: 改 `LC_ALL=C`；A2b 原「原场归一化对拍」与 step3d_uv 正压耦合（诊断柱平均被替换）矛盾，改为柱偏差对拍、阈值 1e-3；新增 A2c 报告项（Z10 式三维括号） |

## 2. 验证性断言（锚）

源码逐式翻译加A2量级锚1.134；场级一致性为封存后探索性。A0只核Cs_r，A1平底零几乎检不出翻译错误，A3不经过复刻，不能以四锚全过证明保真。冻结V `/anchor_failed`=false。 【2026-09-17 复算更正】

| 锚 | 判据 | 读数 | 结果 |
|---|---|---|---|
| A0 | Cs_r max\|Δ\| ≤ 1e-10 | 4.44e-16（V `/anchors/0/values/max_dcs`） | 过 |
| A1 | 平底 max\|a_u\|=max\|a_v\|=0.0 | 0.0 / 0.0（V `/anchors/1/values`） | 过 |
| A2 | DT·max\|⟨a_u⟩\| / ubarmax_step1 ∈ [0.5,2] | **1.134**（V `/anchors/2/values/ratio`）；DT·max\|⟨a_u⟩\|=2.120e-3（`/anchors/2/values/dt_absmax_ubar_repl`） | 过 |
| A3 | 七档步 1 ubarmax 极差 ≤ 4% | 3.71%（V `/anchors/3/values/spread`）；日 1 三维 \|u\|max 比 5.306（`/anchors/3/values/day1_ratio`，不判） | 过 |
| A2c（报告项） | row3 umax ∈ [0.95X, 1.05(X+U)] | 在括号内（V `/anchors/4/values/in_bracket`）；M/X = 1.0132（N `/A2c_M_over_X`），(M−(X+U))/M = −0.261 | 报告 |
| A2b（可选报告项） | 柱偏差形状 L∞ ≤ 1e-3 | **机械判 fail**：读到第 0 条记录为零场，统计量为 NaN（V `/a2b_status`，`/anchors/5/values`） | fail（管线索引错，见 §5 D1） |

- 备审记录：旧草稿的逐点口径比 DT·max\|a_u\|/ubarmax = 3.789（V `/anchors/2/values/ratio_pointwise_record`）——若按原草稿逐点口径封存，钦定锚会越出 [0.5,2] 自爆，检查意见的阻断判断成立。
- A3 同框口径：步 1 为**正压深度平均量**（diag 第 2 列，带符号 MAX），日 1 为**三维绝对值最大**（his），不混称。报告项：七档 row3 三维 umax 极差 0.99%（V `/anchors/3/values/report_row3_spread`）。

## 3. 冻结计数6条5中1负；有风险的P1/P3/P6为2中1负（2026-09-17更正）

V `/n_pass` = 5，`/n_total` = 6。

| 预测 | 判据 | 读数 | 结果 |
|---|---|---|---|
| P1 陡度单调（u, E_L2） | smooth<steep<rx069<harsh | 2.334e-6 < 3.119e-6 < 1.210e-5 < 1.386e-5（V `/predictions/0/values/EL2_u`）；末档只 +14.5%（N `/P1_harsh_over_rx069_EL2u`=1.145） | 中 |
| P2 光滑收敛阶 | p̂_23 ∈ [1.5,2.5] | 2.024（V `/predictions/1/values/p23_smooth`）；p̂_12=2.084 | 中 |
| P3 陡度阶退化 | p̂_12(陡) ≤ p̂_12(光滑) − 0.3 | 1.754 vs 2.084，差 0.330（N `/P3_p12_gap_smooth_minus_steep`）——**余量仅 0.03，险过** | 中 |
| P4 平底替换比（近构造必然、弱赌注） 【2026-09-17 复算更正】 | ≤ 0.2 | 0.0396（V `/predictions/3/values/ratio_flat`） | 中 |
| P5 参考态扣除比 | ≤ 0.5 | 0.0404（V `/predictions/4/values/ratio_refsub`）——弱赌注、近构造必然（Z10同方向先例） 【2026-09-17 复算更正】 | 中 |
| **P6 伪梯度陡度单调（v, E_L∞）** | 四档严格递增 | 2.849e-5 < 1.993e-4 < **1.241e-3 > 1.101e-3**（V `/predictions/5/values/ELinf_v`）；harsh/rx069 = 0.887（N `/P6_harsh_over_rx069_ELinfv`） | **被推翻** |

- P6 原样保留上台。按封存反向条款：「rx0 不是算子最大伪梯度的单一控制变量」。镜像同一量（不作独立旁证）：u 向 【2026-09-17 复算更正】 E_L∞ 在同一处同样回落（N `/S1_harsh_over_rx069_ELinfu`=0.888），而体积加权 E_L2 仍单调（P1）——最坏点误差与体积平均误差对 rx0 的响应不同。与 §4.5 在盘的 H1 运行级高 rx 非单调同向，但口径不同，不拼成对照。
- S2 陡成员 p̂_23 = 1.310（M `/S2_refine/steep/p23`）：不在任何预测内，描述性登记，不解释。

## 4. 旋钮判决表（knob_table.md 机械渲染）

| 旋钮 | 进算子？ | 算子误差变化（制造场，解析真值） | 可见读数（既有落盘） |
|---|---|---|---|
| 黏性 VISC2 | 否 | 0（解析论证：黏性不是算子输入） 【2026-09-17 复算更正】 | 日 1 三维 \|u\|max 99.72→18.79 cm/s，5.31×（M `/S3_knobs/visc_visible`） |
| 缩短积分 | 否 | 0（解析论证） | 无落盘读数，未填 |
| 平底替换 | 是 | E_L2^u 6.472e-6→2.561e-7，比 0.040（P4） | E56 平底 7/7 日 1 u_max=0.0 |
| 地形平滑 | 是 | S1 四档 E_L2^u 2.334e-6…1.386e-5，harsh/smooth=5.94（N `/S1_harsh_over_smooth_EL2u`） | 无落盘读数，未填 |
| 参考态扣除 | 是 | E_L2^u 6.472e-6→2.617e-7，比 0.040（P5）；扣除后与平底臂同量级（refsub/flat=1.022，N `/S3_refsub_over_flat_EL2u`） | 无落盘读数，未填 |
| 加密网格 | 是 | p̂12/p̂23：光滑 2.08/2.02，陡 1.75/1.31（P2/P3） | 无落盘读数，未填 |

口径：「黏性/缩短积分=0」仅据解析论证（管线自检一致只证明程序确定性） 【2026-09-17 复算更正】，不是发现、不计预测；算子误差 ≠ 演化伪流，只说「解析已知的误差源动了/没动」。

## 5. 偏离与封存后补充（DEVIATIONS.md）

- **D1（A2b 记录索引前提写错）**：PREREG §3 断言「NDIA=1 时第 0 条 dia 记录=步 1」，由 E56（NDIA=1440）外推而来；
  源码 output.f90 L342-344 与 set_diags.f90 L256-264 对 nDIA=1 有特例，t0 也写一条零场。故 A2b 机械判 fail（NaN）。
  **verdict.json 不改判、不重跑**；A2b 为非判定项，anchor_failed 不受影响。D1 条目写于查看任何探索性数字之前（2026-09-17T16:04:55+08:00）。
- **封存后探索性补充（非预注册、不改判）**：`e71g_posthoc_a2b.py`（sha256 baea7598…21c5，H `/code_sha256`）按 D1 事先写定的口径，取相对模型起始时刻+10 s的记录（DSTART=0.0d0；原偏移来自ROMS原点与ini时间） 【2026-09-17 复算更正】（H `/primary_rec`=1）：
  u/v为对称镜像同一量、只计一条；柱偏差归一化形状 L∞ u/v = 【2026-09-17 复算更正】 1.105e-6 / 1.105e-6（H `/records/1/pat_dev_linf_u`、`/pat_dev_linf_v`），≤1e-3（H `/exploratory_le_1e3`=true）；
  幅值比 scale_dev = 1.0000006（H `/records/1/scale_dev_u`），相关 0.9999999999990（H `/records/1/corr_dev_u`）；
  原场形状 L∞ = 0.0606（H `/records/1/pat_raw_linf_u`，符合「柱平均被正压耦合替换」的预期，原场对拍不成立）。
  旁证：DT·max\|u_prsgrd\|（记录 1）= 6.833779e-3，与 diag 第 3 行第 4 列 6.833781e-3 相对差 −2.9e-7（N `/posthoc_rec1_DT_max_u_prsgrd_rel_to_row3`），与 Z10「第 3 行=步 1 三维值」结论一致。
  **引用口径**：只能写「封存后探索性、记录索引修正后，一步场柱偏差对拍 L∞≈1e-6」，不得写「A2b 预注册通过」。
- 记录：M/V 的 A2b 字段含 NaN 字面量（非严格 JSON）。

## 6. 未做 / 降级

- 「误差范数随陡度解析曲线 vs 运行伪流 n=4 对照」：**已预注册未执行**（PREREG §8.5，V `/open_problems/0`；需 4 档静止态新算例，最小闭环不做）。
- 全模型 MMS、三风向对照、p̂ 并入 15376 空间：**未做**（PREREG §9 明确不做）。
- 「据我们检索未见」的 Crossref 检索：沿用方案阶段记载（候选与评分.json candidates/6/spec），本条**未重跑外部检索**；仅补了本地库 418 篇 grep（只命中 440，无 PGF/σ 内容）。
- 62×：本条不用、未按 fig_llm.py 复算。
- 仓库未改、未 commit、未提交官网。

## 7. 产出清单（final/）

PREREG_mms_operator.md(.sha256)、DEVIATIONS.md、e71g_{replica,scan,verdict}.py、e71g_1step_clone.sh、e71g_run.sh、
MMS_OPERATOR.json、verdict.json、knob_table.md、fig_mms_operator.png（描述性）、clone_1step/（一步运行克隆与输出）、
e71g_posthoc_a2b.py + POSTHOC_A2B.json（探索性）、e71g_result_numbers.py + RESULT_NUMBERS.json（派生数字）、
scan.log / verdict.log / a2b_clone.log、drafts_pre_review/（修正前草稿，444）。

## 2026-09-17 复算更正清单（当前引用口径）

本节旧说法仅为更正定位；以替代口径为准，不覆盖封存判分、不新增计算。

### 战报 §5.2 小错

| 条目 | 旧记录（已更正） | 当前替代口径 | 复算依据 |
|---|---|---|---|
| mms_operator PREREG §5 | scale_dev = Q′/(DT·R′) | 代码为 Q′/R′（量纲正确，封存文本多写 DT；未记 DEVIATIONS） | 复算 |
| mms_operator D1 | DSTART·86400=63082281600 | roms.in 中 DSTART=0.0d0，偏移来自 ROMS 时间原点与 ini 时间；−5/+10/+20 s 相对时间无误 | 复算 |

### 战报 §5.3 说过头

| 战报序号 | 旧说法（撤回/收紧） | 当前替代口径 | 条目 |
|---|---|---|---|
| 33 | 四个判定锚全过（证明复刻保真） | 源码逐式翻译加 A2 量级锚；场级一致性为封存后探索性 | mms |
| 34 | u 向 E_L∞ 同处回落 0.888 是旁证 / A2b u、v 两向均过 | 镜像同一量，只算一条 | mms |
| 35 | 5/6 命中 | 有风险的 P1/P3/P6 为 2 中 1 负；P4 也标弱赌注 | mms |
| 36 | 黏性：管线自检逐位一致 | 只写"解析论证：不是算子输入" | mms |

详细偏差、敏感性指针与不重跑说明见同目录 `DEVIATIONS.md`。
