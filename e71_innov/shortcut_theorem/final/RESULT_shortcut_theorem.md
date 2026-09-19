# RESULT · shortcut_theorem（E73，T2 介质命题）

> 【2026-09-17 复算更正】 本文件已按战报§5.1–5.3和既有复算收紧口径；所有原判分JSON与封存件保留。文末列逐项改动清单，历史数不得脱离更正引用。

**结论**：本条先封存，再首次读取45°逐候选读数；项目级结果早已存在，与multienv共用留出、非独立。 【2026-09-17 复算更正】7 个布尔式真预测中了 6 个（counted_pass=6/7）。
**P3b 被推翻**，原样保留。6 个验证性锚全部通过，脚本完整性比对 5/5 通过，PIPELINE_SUSPECT=false。
尾部附验不计数：H1 方向确认；H2 封存版不可算，记"未确认"（NaN，见 DEVIATIONS D1）。
目录：amax `/data/xinyuan/GOAI_ai4s_env/e71_innov/shortcut_theorem/final/`（下文路径都相对于这个目录）。

## 1. 封存与时间线

| 事项 | 值 |
|---|---|
| PREREG | PREREG_shortcut_theorem.md，sha256 **238377f14ca258aeeee5238a19b27e2e7f33e2ae63ba2f38c7a360270f7bc607**，封存 **2026-09-17T15:33:57+08:00**，文件 444 |
| 草稿 v0 | v0脚本时间证据为10:17:51创建的4个.pyc（../recompute/RC0_PYC_V0.json证明字节码结构相同）；draft_v0实际创建15:31:16，mtime10:17为cp -p保留值 【2026-09-17 复算更正】 |
| 封存前预演 | _pretest/（15:31–15:33，只用经向样本内数据，不碰 45°）；pt_e73d 与 E73_INSAMPLE 彩排逐位一致 |
| 首读 45° | e73d 于 15:34:33 落盘 E73_SHORTCUT_MAP.json |
| 判分 | e73e 于 15:34:38 落盘 verdict.json |
| 执行者声明 | 封存前只读了 E71M 的代码 e71f_axes45.py，没有打开 E71M 的任何结果、数值或偏差文件（PREREG §3.10）。这一点无法机械证明，按声明申报 |

冻结脚本（sha 在 PREREG §2 表内，e73e 已机械比对，全部一致，verdict.json#/script_integrity）：
e73b d8323820…、e73t f68596ed…、e73c d60bfc0d…、e73d 4e1cde06…、e73e e45dc714…

执行顺序：
1. e73t_tail.py → E73_TAIL.json（e060a628…），耗时 9 s。
2. e73c_axes45.py **拒绝运行**：E71M 轴已落盘，按协作条款只读（e73c_axes45.log）。
3. e73d_predict45.py → E73_SHORTCUT_MAP.json（15ec5395…），耗时 2 s。所读轴文件为
   multienv_metrology/final/E71_FINAL_AXES.npz，sha 4711080967c5…df898。
4. e73e_verdict.py → verdict.json（b88dac8e…）。

以上全部在 amax 上用 systemd-run MemoryMax=16G、nice 19、OMP≤8 串行执行。
起批前检查：available 473G；monitor/state/active 为空；coawstM_yagi_FRESH 无进程。没有碰 e70/。

## 2. 验证性锚（封存时已知答案，不计数）

在 45° 对齐子集上计算，n_common=15376：
- ρ(A_z,B_z)=−0.6742（argsort）
- ρ(D_z,A_z)=+0.9762
- ρ(D_z,B_z)=−0.661
- |S_A|=204
- 逃逸者 12 把，全部 G=0
- 门_45=454（可检，n_pairs_45=28）

六项全部通过：verdict.json#/anchors、E73_SHORTCUT_MAP.json#/anchors。

## 3. 真预测（7 个布尔式；verdict.json#/predictions）

| 式 | 统计量 | 门槛 | 判定 | 经向彩排（校准，不是证据） |
|---|---|---|---|---|
| P1 ρs_argsort(c_45·D_z, A_45) | **0.9579**（平均秩 0.9579，无翻转） | ≥0.80 | 中 | 0.9102 |
| P2 \|D_z\|≥0.3 带内符号命中（n=13913，A_45=0 计 miss，实际为 0 个） | **0.9747** | ≥0.90 | 中 | 0.9449 |
| P3a S_A 内 45° 存活(140) vs 阵亡(64) 的 \|r\|，单侧 MW | **p=1.18e-4**（中位 0.081 vs 0.120） | p<0.05 | 中 | 1.65e-5 |
| P3b 三向幸存(80) vs 其余(15296) 的 \|r\|，单侧 MW | **p=0.174**（中位 0.103 vs 0.077） | p<0.05 | **不中** | 1.4e-8（二向口径） |
| P4 k=5 抽 200 次，带符号均值比 | **1.0**（同号率 1.0，ĉ=0 的 0 次；ĉ 均值 0.9265，CV 0.119） | P1>0 ∧ ≥0.9 | 中 | 1.0 |
| P5 \|偏ρ_avg(A_45,B_45\|D_45)\| / \|ρ_avg(A_45,B_45)\| | **0.0754**（−0.0492 / −0.6526；argsort raw −0.6279） | ≤0.5 | 中 | 0.2753 |
| P6 12 把逃逸者过 45° 严格门的数量 | **1**（标准门 4） | ≤4 | 中 | 0 |

- c_45 = **0.9729**（argsort）/ 0.9773（平均秩），n_45=22（19个独立配置，4条同默认配置重复），没有触发 low_n / k5_degenerate：
  E73_SHORTCUT_MAP.json#/c_45、#/n_45。
- P4 的判定在秩上等价于"k=5 子样本同号率约 ≥95%"。它押的是**符号**，不是 c 的幅度（PREREG §5 脚注）。
- P5 同框：扣 |D_45| 后偏 ρ = −0.6526，与原值相同（#/P5/partial_given_absD45_avgrank）。
  这是"一致性检查"，D_45 与 A_45 本身 ρ=0.9893，共线。

## 4. 被推翻：P3b

- 原样保留，进"预注册与被推翻"专页，并列入 OPEN_PROBLEMS。
- 事后描述，**非检验、不改判**（E73X_POSTHOC.json#/c_P3b_decomposition）：
  - 三向幸存者的平均带符号残差为 +0.079，即 A_45 系统性高于 c_45·D_z 的预测。
  - "其余"里 |A_45|≥0.7 的 9141 个候选中位 |r| 只有 0.034，其中 A_45≥0.7 的 4566 个为 0.033，对照组因此被拉低。
  - 45° 全体中位 |r|=0.0777，低于经向彩排的 0.1183（_pretest/E73_SHORTCUT_MAP.json#/P3/med_absr_all）。
- 口径：S_A 内部的富集（P3a）成立；"三向幸存者 = D 直通车解释得最好"不成立。PREREG 预先申报过门选混杂，
  +0.079 的正残差也可能来自 c_45<1 的机械缩放，不作解读。

## 5. 附验（不计数，与命题共用差值序列，非独立证据；verdict.json#/aux_tail）

- H1：ρs(κ,|g|)=0.1615，置换 p≤0.0002（1/5001下限） 【2026-09-17 复算更正】 ⇒ 方向确认。n_used=15376，n_excluded_lt16=0。
- H2：封存版 p=null ⇒ 未确认。
- NaN 偏差（DEVIATIONS D1）：32 个候选读数恒定（G=0），κ 为 NaN。
  - 探索性剔除 NaN 后，H1 为 ρ=0.1687、p≤0.0002（1/5001下限） 【2026-09-17 复算更正】。
  - 剔除 NaN 后 H2 **方向相反**（κ 中位：死组 0.094 vs 活组 25.03，p=1.0）。
  - 只能进附录，不能说成支持尾部判据。

## 6. 描述件（封存后，非预注册）

- 反号象限（map#/descriptive/quadrants_at_0p7）：A_z≥0.7 中 A_45<0 的有 18 个，变节率 0.0037，与 E71M P6 判定同值；
  按 PREREG 只引用，不重复设赌。
- E59 同框（目标定义不同，只同框）：
  - Â_45 预测 45° 标准门成员的 AUC=0.671（Â 不含 B 信息）；
  - |A_45|≥0.7 内按符号预测方向的 AUC≈1.000；
  - 对照 E59B_POSTHOC 的 0.8706 / 0.8128 / 0.9193（e59/E59B_POSTHOC.json#/*/auc_test）。
- 残差榜 top-20 全部是 G=0 比值型，且成对出现（u/v 分子分母互换），多为 u 与 v 相比的读数，
  A_z 与 A_45 反号（map#/descriptive/top20_residual）。只作观察，不作机制断言。
- Kendall 型界（E73K_KENDALL.json）：
  - ε̂：纬向 0.0526、45° 0.0433。
  - 15376个候选违例0、最大差=2ε̂是数学必然，只称代码自检。 【2026-09-17 复算更正】
  - τ_H(m,skill′)≥0.7 的候选，其 τ_H(m,spur) 实测最小：纬向 0.608（4038 个），45° 0.619（3633 个）。
- G 分支（E73P_PROP1_AUDIT.json）：A≥0.7 的绝对量候选中 B≥0.9 的数量为纬 0/81、经 0/84、45° 0/84。
  严格门候选全部是 G=0（纬 12、经 17、45° 26）。
- 预先存在的重叠（DEVIATIONS D2）：
  - P6 唯一严格存活者 u|d1500|p95÷w|d1500|rms 在 2026-09-02 的 metric_search_diag45.json top-30 里；
  - 80 个三向幸存者中有 12 个在 top-30 里；
  - 残差 top-20 与 top-30 无重叠。
- 与 E71M 非独立：E71M 的 P2b ρ(D_45,A_45)=0.9893、P2c ρ(D_z,D_45)=0.9521（其 verdict.json，封存后读取），
  与本模块 P1 高度相关；两份预注册对同一 45° 留出下注，多重比较敞口要同页申明。

## 7. 上台口径

**可上 PPT/Demo（带脚注）**
- "量一个数（纬向 D）＋一个标量的真值预算（c_45，22条真值、19个独立配置，4条为同一默认配置重复 【2026-09-17 复算更正】）⇒ 预测 45° 全部 15376 个候选的 A"：
  P1 0.9579、P2 0.9747、P4（穷举26334个5条真值子集，约99.7%给出正号） 【2026-09-17 复算更正】。
  脚注：秩相关等价于 ρ(D_z,A_45)；D 主导；与 E71M P2b/P2c 非独立。
- 逃逸者跨向不保：P6 严格门 1/12（B 关失守 7/12）。脚注：唯一存活者在预先存在的 top-30 里。
- 中介一致性在 45° 复现：P5 0.0754，同框扣 |D| 的 −0.6526，只称一致性检查。
- 预注册计分 6/7，P3b 被推翻页原样上台。
- FIG1_partial_AB_zonal_corrected_20260917.png、FIG2_sign_quadrant_45_corrected_20260917.png、FIG3_residual_board_45_corrected_20260917.png，图内已印 JSON 指针。

**只进附录**
- 尾部附验 H1（带 NaN 脚注、非独立、不计数），H2 未确认及其探索性反向结果。
- P3b 描述性分解。
- Kendall ε̂ 与 G 分支审计（封存后描述）。
- E59 AUC 同框、c_k5 的 CV。
- PROP1_命题卡.md 的论证页。

**不能用**
- "不可能定理""无真值预测""理解全部机制""首次/第一"。
- 把 −0.73→−0.20 单独展示（必须与 −0.7321 同框）。
- 把 H2 或 P3b 说成支持。
- 把 P1 当作独立于 E71M 的第二份证据。
- 把 45° 的 G 分支审计或 Kendall 界说成预注册预测。
- 不带"预先存在"脚注地展示 P6 存活者。

## 8. 未做 / 降级（如实）

- §7.1 M3 逐行代码审计：**未做**，命题卡只给了指针。M2 的"据我们检索未见"检索：**本轮未重做**，沿用 2026-09-16/17 口径。
- §7.8 文献：Durmus、VanderWeele（两篇）、Salaudeen 已核；Skalse、Zhuang、Kwa、El-Mhamdi、Geirhos、DeGrave、Miller、
  Baek、Achille、Veitch **本轮未重核**，沿用候选规格状态。Karwowski（#39）**未核**。
- OPEN_PROBLEMS 条目（P3b 三向口径失败）：**未写入仓库**（仓库不许 commit，由整合者放入）。
- 所有 P 都已执行，没有"已预注册未执行"的项。

## 9. 文件清单（final/）

- **预注册与冻结脚本**：PREREG_shortcut_theorem.md(+.sha256)、e73b/e73t/e73c/e73d/e73e_*.py、draft_v0/。
- **判定输出**：E73_INSAMPLE.json、E73_TAIL.json、E73_SHORTCUT_MAP.json、verdict.json、各 *.log。
- **封存后描述**：e73x_posthoc_audit.py→E73X_POSTHOC.json、e73k_kendall_bound.py→E73K_KENDALL.json、
  e73p_prop1_audit.py→E73P_PROP1_AUDIT.json、e73f_figs.py→FIG1/2/3。
- **文档**：PROP1_命题卡.md、DEVIATIONS.md、RESULT_shortcut_theorem.md（本文件）。
- **封存前预演**：_pretest/（build_pretest.py、pt_*.py、preseal_checks.py→E73_PRESEAL_CHECKS.json）。

## 2026-09-17 复算更正清单（当前引用口径）

本节旧说法仅为更正定位；以替代口径为准，不覆盖封存判分、不新增计算。

### 战报 §5.2 小错

| 条目 | 旧记录（已更正） | 当前替代口径 | 复算依据 |
|---|---|---|---|
| shortcut_theorem | 22 条真值 | 19 个独立配置（4 条为同一默认配置，skill 同为 −295.3628） | `recompute/RC2_RESULTS.json` |
| shortcut_theorem H1 | p=0.0002 | p≤0.0002（1/5001 下限） | 同上 |
| shortcut_theorem 103 副本 | scratchpad/e73/PREREG_shortcut_theorem.md | 非封存版（33453 字节 vs 封存版 33713 字节），引用以 amax 封存件为准 | 复算核对 |

### 战报 §5.3 说过头

| 战报序号 | 旧说法（撤回/收紧） | 当前替代口径 | 条目 |
|---|---|---|---|
| 26 | 45°（与经向）为 VISC2 单旋钮扫描 | 同一批 22 个 run 的四旋钮单变扫描 | multienv、shortcut |
| 27 | Kendall 界违例 0、界是紧的 | 数学必然，只称代码自检 | shortcut |
| 28 | 5 条真值足以钉死符号 | 约 99.7% 的 5 条真值子集给出正号 | shortcut |

详细偏差、敏感性指针与不重跑说明见同目录 `DEVIATIONS.md`。
