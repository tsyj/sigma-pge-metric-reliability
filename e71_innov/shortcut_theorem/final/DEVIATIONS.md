# DEVIATIONS · shortcut_theorem（E73）

封存文件 PREREG_shortcut_theorem.md（sha256 238377f14ca258aeeee5238a19b27e2e7f33e2ae63ba2f38c7a360270f7bc607，
2026-09-17T15:33:57+08:00 封存）一字未改。以下为封存后发现的问题与按 PREREG 承诺必须记录的事项。
所有条目**不改任何判定**；verdict.json 保持机械输出原样（counted_pass=6/7）。

## D1｜尾部附验 κ 出现 NaN：H2 封存版不可算，H1 含伪秩（发现：2026-09-17 15:34，e73t 运行输出）

- 现象：E73_TAIL.json 的 H2.med_kappa_dead/alive = NaN、mw_p_one_sided = null ⇒ direction_confirmed=false。
  另外 E73_TAIL.json 因此含非标准 JSON 字面量 `NaN`（Python json 可读，严格解析器会拒绝）。
- 根因（E73X_POSTHOC.json#/a_tail_nan_audit）：15376 个候选中有 32 个在 58 条纬向带标签陡臂上读数恒定
  （全部是 G=0 比值型，如 temp|all|max÷temp|s200|max、w|d200|max÷w|d400|max），scipy 峰度为 0/0=NaN。
  PREREG §6 没有写 NaN 的处理办法，封存版 e73t 也没有过滤 NaN。
- 对封存版数字的影响：H1 的 ρ=0.1615 里，np.argsort 把 32 个 NaN 排成 κ 秩最大；H2 的 Mann-Whitney 遇到 NaN
  返回 NaN，记为 null。
- 探索性敏感性分析（封存后做的，非预注册，不计数，不改判；e73x_posthoc_audit.py）：
  - 剔除 NaN 后 H1：n=15344，ρ=0.1687，置换 p=0.0002，方向与封存版相同。
  - 剔除 NaN 后 H2：κ 中位数 B 死组 0.094 vs B 活组 25.03，单侧 p=1.0。**方向与 H2 的预期相反**。
- 口径：H2 按封存判定记"未确认"。探索性结果显示方向相反，只能进附录并注明"封存后探索"，不能说成支持
  El-Mhamdi 尾部判据。H1 上台必须带这条 NaN 脚注，并且写明"非独立证据、不计数"。

## D2｜§3.7 承诺的"预先存在"注明（封存后第一次读 ledger/metric_search_diag45.json，2026-09-17 15:35）

- 这个文件 2026-09-02 17:28 就已落盘，含 top-30 行 [num, den, rho, B]，以及 n_pass_A=4646、n_pass_AB=454。
- 和本模块判分集合的重叠（E73X_POSTHOC.json#/b_top30_overlap）：
  - **P6 唯一过严格门的 u|d1500|p95÷w|d1500|rms 在 top-30 里，属预先存在**；
  - 三向幸存者 80 个里有 12 个在 top-30 里，属预先存在；
  - 残差榜 top-20 与 top-30 没有重叠。
- n_pass_AB=454 与 §4 门_45 锚（454）一致。这是预先存在的计数，本来就归在验证性断言里。

## D3｜锚与护栏实际走到的分支（记录，非偏差）

- 轴来源：E71M 的 final/E71_FINAL_AXES.npz，只读，sha256 4711080967c5…df898。
  e73c_axes45.py 按协作条款拒绝运行（e73c_axes45.log），没有产出 E73_AXES45.npz。
- 实际 n_45=22、n_common=15376、n_pairs_45=28，没有触发 low_n、k5_degenerate 或 null 退化分支。
- 六个锚全部通过，门_45 实测 454；script_integrity 五项全部为 true。

## D4｜封存后新增的脚本与产出（非预注册，描述性，均不改判）

| 文件 | 作用 | sha256 |
|---|---|---|
| e73x_posthoc_audit.py → E73X_POSTHOC.json | NaN 审计、top-30 重叠、P3b 描述性分解、P6 点名 | eb52eaa8…9062358 / 23988796…cb67181 |
| e73k_kendall_bound.py → E73K_KENDALL.json | §7.2 的 ε̂ 标定，外加逐候选机械核对不等式 | 6cd34968…c7687eb / ec5540c4…251bf6f |
| e73p_prop1_audit.py → E73P_PROP1_AUDIT.json | PROP1 的 G 分支描述审计（纬/经/45°） | 6a75be94…c84194 / 243649a7…d4a8a4 |
| e73f_figs.py → FIG1/2/3 | §7.7 三张图（第一版图例不可见，修正后重跑，sha 为终版） | faa9f782…d86f3 |

## D5｜封存前预演目录 final/_pretest/（已在 PREREG §10 R12/R13 申报，这里只登记位置）

build_pretest.py、pt_e73d/pt_e73e/pt_e73t.py 及其输出，preseal_checks.py → E73_PRESEAL_CHECKS.json，
时间在 15:31–15:33，都早于封存（15:33:57）。pt_e73t 在 3 个基本量的子集上跑，日志里有数值行，执行者没有查看；
这些数值与 §6 全体检验无关。

## D6 · 2026-09-17 · 四旋钮设计、重复配置、v0 时间证据

PREREG §8.8 的“VISC2 单旋钮”是事实错，封存原文不改。经向与 45° 为同一批 22 个 run 的四旋钮单变扫描（VISC2 7、VISC4 7、TNU2 7、AKV_BAK 1）。22 条真值对应 19 个独立配置；4 条为同一默认配置，skill 均为 −295.3628（`../recompute/RC2_RESULTS.json#/labeled45_composition`）。PROP1 适用范围与另名 FIG1–3 统一更正；原 444 作图脚本和 PNG 全部保留。

v0 时间证据改引 final/__pycache__/ 中 4 个创建于 10:17:51 的 .pyc，`../recompute/RC0_PYC_V0.json` 逐份证明与 draft_v0 字节码结构相等。draft_v0 文件实际创建于 15:31:16，10:17 是 cp -p 保留的 mtime，不是创建时间。103 scratchpad/e73/PREREG_shortcut_theorem.md 为非封存版（33453 vs 33713 字节），引用以 amax 封存件为准。

P4 穷举 26334 个 5 条真值子集，正号 99.72%、零 0.26%、负号 0.019%，改为“约 99.7% 子集给出正号”。Kendall 界零违例与取等为数学必然，只称代码自检。H1 p≤0.0002 是 1/5001 的分辨下限。与 multienv 共用 45°、非独立、多重比较敞口必须同页申报。P6 唯一存活者带“预先存在”脚注，P5 与扣 |D| 的 −0.6526 同框。本轮不重跑判分。
