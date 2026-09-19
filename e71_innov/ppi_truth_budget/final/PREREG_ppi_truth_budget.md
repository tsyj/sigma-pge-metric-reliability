# 预注册：ppi_truth_budget——真值预算表与 rectifier 测谎（PPI 审计）

状态：定稿待封存
条目：GOAI 2026 赛道三决赛 · T3（ppi_truth_budget，候选与评分.json id 同名，merged_from #2+#4）
起草：2026-09-17（虎虎队）；执行目录 `/data/xinyuan/GOAI_ai4s_env/e71_innov/ppi_truth_budget/final/`
范围（按创新升级方案 §T3 冻结）：只交 (a) 真值预算表 ＋ (b) rectifier 测谎；(c) 主动推断与共形保单排队尾（见 §7），不设任何计分预测。
封存前人工动作（2026-09-17 已完成）：① PPSR（arXiv:2608.26638 v2，Gao/Sicilia/Shi）摘要已读，并经 WebFetch 摘要工具读取 arXiv HTML 正文要点（非本人逐字通读全文，引句为工具返回），按 §8-1 收窄措辞；② 独立检查意见六条全部落实（§11 修订记录）；③ `tb_selftest.py` 在修订后代码上重跑（纯合成）；④ 状态改为「定稿待封存」；⑤ `bash seal.sh`。

---

## 0. 封存流程与时序（协议）

1. `seal.sh` 一键执行：对 16 个文件（PREREG、`tb_common/tb_budget/tb_rectifier/tb_verdict/tb_selftest.py`、`TB_SELFTEST.json`、`preseal_sets.py`、`PRESEAL_SETS.json`、`calib.py calib2.py calib3.py calib4.py`、`CALIB_SYNTH.md`、`seal.sh`、`run_all.sh`）逐个 `sha256sum` 写临时文件→`date -Is` 追加→改名 `.sha256`→`chmod 444`（`.sha256` 与全部被封存文件）。任一文件缺失、行数≠16、判分输出（TB_BUDGET/TB_RECTIFIER/verdict.json）已存在、自检未全绿、二次封存——一律拒绝封存（不再有 `|| true` 静默跳过）。
2. **封存必须早于读取任何留出读数与判分输出。** `tb_budget.py / tb_rectifier.py / tb_verdict.py` 内置封存门（`tb_common.require_seal`）：无 `.sha256`、`.sha256` 所列文件任一已不存在、`SEALED_FILES` 任一未被列入、哈希不符、时间戳行数≠1、行格式异常——一律拒跑。
3. 唯一允许封存前运行的部件：`tb_selftest.py` 与合成校准 `calib*.py`（纯合成），以及 `preseal_sets.py`（**只读账本元数据**：run_id/bathy/ntimes/action 键/obs.valid、regraded_v2 的 run_id 键、out_his.nc 是否存在；不取 err_rms/skill 数值、不调用 base_quantities/grade、不读代理读数，产出 `PRESEAL_SETS.json` 为 V7 依据）。合成部件为纯合成随机数总体，不打开任何账本、任何 nc/MDS、任何在盘 JSON；只验证/选定估计量代码本身（管线正确性锚，不是数据预览）。**估计量形式经封存前合成校准选定并在此冻结**（过程与数字见 `CALIB_SYNTH.md`，与 calib 脚本一并入封存哈希）：①解析设计方差在 n≤16 失覆盖 0.85–0.87 → 均值方差改删一刀切；②rectified-CDF 分位**区间**在诚实松弛下恒宽于精确经典区间 → 判死，分位区间改精确次序统计量式，PPI 只保留分位**点估计**。这两处是合成数据上的方法学修正，发生在读取任何真实读数之前。
4. 判分机械输出 `verdict.json`（`tb_verdict.py` 只读 `TB_BUDGET.json`/`TB_RECTIFIER.json`，不重算任何统计）。
5. 封存后发现写错：只记 `DEVIATIONS.md`，不改封存文件（§10）。真预测被推翻的，原样保留、原样上台。

## 1. 验证性断言与已知量（封存时已知答案或已在盘，一律**不计分**）

### 1.1 验证性断言（判分时印出核对，不进 P 条目）

- V1：总体规模 |U| = 58（出处：`e65/E65_SPURIOUS_VS_TRUE.json` `n_runs_steep=58`；本管线按 §3-1 同款过滤重建）。
- V2：SPUR_KEY = `u|all|rms`（同上 JSON `spurious_key`；回退链同 e65）。
- V3：判分侧 `grade_bench(rid, 8640, akv)` 在 U 的 run_id 字典序前 5 例上复现 `regraded_v2.jsonl` 的 `err_rms`，逐例 |Δ| ≤ 1e-3 cm/s（**数据完整性门**：不过则 §4 P5–P7 记 AMBIGUOUS）。
- V4：E59 行掩码复刻行数 = len(score_te) = 15376（数据盘点 §2；不等则 §4 中涉 e59 代理的条目记 AMBIGUOUS）。
- V5：合成自检 `TB_SELFTEST.json all_pass=true`（N=58, n=16, 2000 重复：均值刀切覆盖∈[0.88,0.94]、精确 p90 区间覆盖≥0.90、PPI 分位点 MAE/经典≤1.05、λ̂ 中位∈[0.7,1.3]×总体斜率）。封存条件，非预测。
- V6：三条刷分路径倍数按**本口径**复算（SPUR_KEY 配对读数比中位，§3-8）并与初赛口径并排印出——初赛 224×/62×/28× 出自 `github_repo/scripts/fig_llm.py` L59-62（换地形 32 对中位 / VISC2 50→30000 单比 8.674/0.1399 / 缩短积分 5 对中位 27.8），README L16。**两口径不同，只可并列，不可互替，不设容差门。**
- V6b：初赛 62× 的算术复算 = fig_llm.py 注释 `8.674/0.1399`（= 62.0，印出）；判分侧在 VISC2=50 参考臂与 VISC2=30000 臂的 obs 字段与 base_quantities 键中搜索这对数值（相对差 <5e-4），报命中键或「未命中」——只为注明 62× 的口径出处，不计分、不设门。
- V7（路径集合尺寸，封存前由 `PRESEAL_SETS.json` 元数据核对得出，非留出读数）：|U|=58；孪生对 32、|B_T|=32（steep 臂全在 U、flat 臂 out_his.nc 齐全）；|B_V|=3（VISC2=5000/10000/30000：e2_ee394c011892、e2_b82a21ff15fd、e2_9e957e1b688e），**且 3 个全在 U 内**；|B_S| 账本 6 个，其中 e2_03aef1df4e2d 缺 out_his.nc → 可用 5 个，其中与 U 内简单动作臂按 (VISC2,seed) 可配 4 个（≥3 → 缩短积分倍数走 matched 口径）；U 内 VISC2=50 简单动作参考臂**只有 1 个**（M_V 的 ref 是单臂读数）；账本重复行 69 条、重复行元数据全部一致。**已知脆弱性**：|B_V|=3 恰好踩在 MIN_BRUSHED=3 上，任一成员 base_quantities 或 grade 失手即 visc 路径 AMBIGUOUS_SMALL → P5、P6 双双 AMBIGUOUS；这是封存前已知、不临场补救。
- V8（原 P3 降级，判分时机械印出布尔值但不计分）：`saving(D,16) ≥ saving(u_max,16)`，并印出在盘查表值 `E59_ARRAYS.npz Atr[(u|all|rms,'')]` 与 `Atr[(u|all|max,'')]`（Atr=纬向 A 标签 =−spearman(读数, skill_vs_zero) 于本总体；行名由逐行复刻 e59 纬向 build+clean 恢复，复刻 A 须与 Atr 逐元一致）及 f_D、obs.u_max 对 skill 与对 Y 的 spearman（描述性）。降级理由见 §4 与 §8-12。

### 1.2 已知量排除清单（在盘即不押；任何可由单次查表或既有数组直接派生的量都不得当预测卖）

| 已知量 | 落盘出处 |
|---|---|
| U 内每例真值 err_rms / skill_vs_zero 的**数值本身**（历史多次读取，E65 已用作标签） | `ledger/regraded_v2.jsonl` |
| ρ(D,A)=0.9762、ρ(D,B)=−0.661、n_pairs=32、58/15376 | `e65/E65_SPURIOUS_VS_TRUE.json` |
| E59 全部特征、A 标签、score_te 数组与分箱命中率 | `e59/E59_ARRAYS.npz`、`E59_TRUTHFREE.json` |
| 两候选 u\|all\|rms、u\|all\|max 对本总体 skill 的秩相关（Atr 按行名单次查表可得；skill_vs_zero 在 day1.0 下与 err_rms 近单调）→ 原 P3 的秩序层面 | `e59/E59_ARRAYS.npz` Atr |
| 路径集合尺寸 |B_T|/|B_V|/|B_S|、B_V⊆U、配对数（V7） | `final/PRESEAL_SETS.json`（元数据） |
| PPSR 节省比 ≈ Pearson r²、PPI 评估覆盖率验证（WMT，1000 次） | arXiv:2608.26638 §5.1/§6.2 |
| 初赛三条路径倍数 224/62/28 | `github_repo/scripts/fig_llm.py`（硬编码）＋README L16 |
| E44/E56/E60/E66/E67 全部在盘统计 | 各自目录 |

**推论（诚实口径）**：本条目**没有未读的原始数据文件**——58 个真值早已在盘、被全队反复使用。因此这里的「留出」不是数据，而是**程序输出**：覆盖率、n_eff/n 曲线、rectifier 幅度与排序、朴素替代对照的覆盖率，这些量在封存时**不存在于任何落盘产物**（据 2026-09-17 对 `/data/xinyuan/GOAI_ai4s_env` 与 repo 的检索）。真预测（§4）只押这些量。若封存后发现其中某量另有先前落盘出处，该条降级为验证性断言并记 DEVIATIONS.md。

## 2. 留出集精确语义与文件白名单

**语义声明**：留出 = 本条目判分管线（tb_budget / tb_rectifier / tb_verdict）在封存前**零执行、其输出零存在**。不主张对真值数值的历史零接触——历史接触产生的已知量全部列入 §1.2 排除清单。覆盖率的「真值」= 有限总体参数（§3-2），由同一次判分在揭盲侧机械算出，不依赖任何主观读数。

**封存后判分管线允许读取的文件（白名单，读此外任何数据文件即违规）**：

- `ledger/env2_runs.jsonl`（action/obs/ntimes/bathy；obs.u_max 为代理 2）
- `ledger/regraded_v2.jsonl`（err_rms = Y；判分时首次由**本管线**读取其数值）
- `runs/e2_*/out_his.nc`（base_quantities 读数与 grade_bench 提交态；仅纬向）
- `truth/` MITgcm MDS（仅经 `scripts/env2._truth`，r26steep 第 1.0 天口径）
- `e59/E59_ARRAYS.npz`（`score_te`；以及 `Atr`，仅供 V8 查表印出）
- `ledger/regraded_v2.jsonl` 的 `skill_vs_zero`（仅用于 V8 复刻 e59 纬向 clean 掩码与描述性 spearman；U 内数值为 §1.2 已知量）
- `ledger/env2_merid_runs.jsonl` ＋ `runs_merid/`（**仅**为复刻 E59 行掩码与行序，§3-6；其 hidden.skill_vs_zero 只用于掩码的有限性判断，数值已被在盘 E59 消费过，不进入任何计分量）
- `scripts/{metric_search,regrade_all,env2,sigma2z}.py`（代码复用）

**明确不读**：`e70/`（在跑，禁触）、`e44/`、`e56/` 读数、`e60/runs/`、`e63/`（隔离红线）、`e66/`E66_AXES、`e67/` 结果数组、其他队伍/赛题任何数据。不调用任何大模型 API。不向 `runs/` 等既有目录写任何文件；新产出只落本 final/ 目录。

## 3. 冻结的操作定义（脚本文件本身即定义，封存时 sha 固定；此处为摘要）

1. **总体 U**（复刻 e65 过滤）：`env2_runs.jsonl` 去重（dict 语义，后行覆盖前行）后，`obs.valid ∧ ntimes==8640 ∧ bathy==r26steep ∧ run_id∈regraded_v2 ∧ base_quantities 成功`，按 run_id 字典序冻结。预期 N=58（V1）。
2. **估计目标（有限总体参数）**：Y_i = regraded_v2 `err_rms`（cm/s，truth_day=1.0、AKV 匹配口径，`scripts/regrade_all.py` 定义）。θ_mean = (1/N)ΣY_i；θ_p90 = 升序第 ⌈0.9N⌉ 个次序统计量（N=58 → 第 53 个）。
3. **三条代理（揭盲前钉死，就是这三条，判分不加不减不换）**：
   - **D 口径读数**：f_D(i) = base_quantities(i)[SPUR_KEY]，SPUR_KEY 回退链同 e65（`u|all|rms`→`v|all|rms`→`u|all|max`→首个 `u|*|rms`）；
   - **u_max**：f_U(i) = 账本 `obs.u_max`；
   - **E59 机选尺子**：c* = argmax(score_te)（并列取最小下标），(分子,分母) 名字按 §3-6 复刻恢复；f_E(i) = 该候选在算例 i 上的读数。**申报**：score_te 的训练标签用过纬向真值（E59 纬向训练→经向测试），c* 的选择对本总体**不是免真值的**——其 n_eff 只当「见过真值的机选尺」上界参考，不与 f_D/f_U 同框卖（§8-4）。
4. **抽样与主估计量（设计基）**：SRSWOR（`rng.choice(N,n,replace=False)`），种子 20260917，循环序 `for proxy in (D,umax,e59): for n in (8,12,16,24,32): for b in range(1000)` 冻结。均值：有限总体差分/回归估计量 θ̂ = λ̂·mean_U(f) + mean_L(Y−λ̂f)，λ̂ = 标注集 OLS 斜率（Var 退化→0）；**方差 = 删一刀切**（逐次重拟合 λ̂，v = (1−n/N)·(n−1)/n·Σ(θ̂₍ᵢ₎−θ̂₍·₎)²），CI = θ̂ ± t_{n−1,0.95}·√v（解析设计方差经合成校准判失覆盖，见 §0-3 与 CALIB_SYNTH.md）。**近邻主动同框**：此式在有限总体口径下就是 Cochran 抽样调查的回归估计量（含 FPC）＋刀切方差；PPI/PPI++（arXiv:2301.09633 / 2311.01453）给出的是其现代代理版与调幅 λ——我们不声称估计量新。经典对照：Ȳ_L ± t_{n−1,0.95}·√((1/n−1/N)S²_{Y,L})。
5. **90 分位**：区间 = **有限总体精确次序统计量区间**（K₀=⌈0.9N⌉，标注命中数按超几何 HG(N,K₀,n) 反演取次序统计量，允许无界侧；SRSWOR 下保证式，不依赖代理）。PPI 只出**点估计**：标注集 OLS 校准 ĥ 后 rectified CDF 的 min{t:F̂(t)≥0.9}；与经典点估计（标注第 ⌈0.9n⌉ 次序统计量）做 MAE 对照（P4）。rectified-CDF 分位**区间**已在封存前被合成校准判死（诚实松弛下恒宽于精确经典区间，calib3），不出区间主张——这本身作为「分位维度代理省不动」的方法学负结果印入预算表页脚。
6. **E59 行掩码复刻**：逐行复刻 `e59_truthfree.py` 的 build(经向,'hidden')+clean()（枚举顺序、EPS 过滤、7 特征有限性掩码），仅取行名与掩码；行数≠15376 → 涉 e59 条目 AMBIGUOUS（V4）。
7. **n_eff 与省真值倍数**：由 (1/n_eff−1/N)·S²_Y = V_med 解出 n_eff = 1/(V_med/S²_Y+1/N)，V_med = 该格 1000 次 V̂ 的中位，S²_Y = 总体真方差（揭盲侧报表量）；saving = n_eff/n。预算表 = 3 代理 × 5 档 n 的 {覆盖率(均值/分位, PPI/经典), 区间宽中位, n_eff/n}；Dorner 因子-2 画参考线（§8-5 申报假设域差异）。
8. **(b) 三条刷分路径（冻结集合）**：
   - Y_bench 口径（基准问题固定）：提交态 = 该 run `out_his.nc` **最后一帧**，对 r26steep **第 1.0 天** MITgcm 真值（AKV 按 action，缺省 1e-5）的 err_rms（cm/s）——即 `grade_run(rid, ntimes=8640, akv)`；对 U 内成员它逐字等于 regraded_v2 口径（V3 为门）。
   - 换地形 B_T：e65 同款孪生对的**平底臂**；荒谬黏性 B_V：steep ∧ valid ∧ 8640 ∧ 动作键⊆{bathy,VISC2,ntimes,seed} ∧ VISC2>3000（高于诚实 sweep 上限 2747 的黏性档）；缩短积分 B_S：steep ∧ valid ∧ ntimes<8640 ∧ 同款动作键 ∧ VISC2≤2747。均要求 base_quantities 与 grade 成功；|B_p|<3 → 该路径 AMBIGUOUS。判据函数 `tb_common.is_BV/is_BS/twin_pairs`，(a)(b) 共用。
   - **已知事实 B_V⊆U（V7）**：3 个荒谬黏性 run 同时满足 U 过滤，都在 (a) 的 N=58 总体内；B_T（平底）与 B_S（ntimes<8640）与 U 不相交。
   - **rectifier 读数（计分口径，封存前按检查意见改为「拟合集外残差」）**：ĥ_cal = **U∖B_V（诚实标定集，预期 n=55）** 上 Y 对 f_D 的 OLS；R_p = median_{i∈B_p}(Y_bench,i − ĥ_cal(f_D,i))，单位 cm/s，附 IQR。三条路径的全部成员都在 ĥ_cal 拟合集之外，口径统一。ĥ_cal 用 55 个配对真值标定，申报为描述性测谎读数，非省真值机器的一部分。
   - **ĥ58 对照（描述性，不判分）**：U 全体（含 B_V）上的 OLS；各路径 `descr_rectifier_median_h58` 同表印出，并标注「visc 路径在 ĥ58 下为样本内残差、向 0 偏」。
   - **倍数复算口径（V6）**：M_T = 孪生对 f_D(steep)/f_D(flat) 中位；M_V = median(ref)/f_D(b)，ref = U 内 VISC2==50 的简单动作臂读数中位（V7：ref 只有 1 臂）；M_S = 同 (VISC2,seed) 的 8640 臂/短臂 读数比中位（配齐 <3 对时退 ref 口径并标注；V7 预期 matched 4 对）。
   - **混合总体对照（P7）**：U_mix = U ∪ B_T ∪ B_V ∪ B_S（run_id 去重）。**因 B_V⊆U，去重后 B_V 不贡献新成员，混合总体新增成员实际只来自换地形（预期 32）与缩短积分（预期 5）两路径**，预期 N_mix≈95；逐路径新增数 `n_new_members_by_path` 印出。θ_mix = mean(Y_bench)；n=16，1000 次 SRSWOR（种子 20260918）。朴素替代（Baumann 式）：无标注处填 **ĥ_cal(f_D)**，把 N_mix 个数当真数据算 t 区间；PPI：与 §3-4 同一机器。
   - **(a) 总体构成申报**：(a) 的真值预算总体 U 就是账本里「陡地形 ∧ valid ∧ 8640 ∧ 已重判」的旋钮总体**原样**，其中含 3 个高于诚实 sweep 上限的荒谬黏性 run（B_V）；因此 (a) 的结论口径是「本账本陡地形旋钮总体（含 3 个刷分黏性点）」，不是「诚实 sweep 总体」。2747 上限只用于 (b) 的路径划界，不用于 (a) 的总体划界；`TB_BUDGET.json B_V_members_in_U` 印出名单。
9. **AMBIGUOUS 判则（冻结）**：N<40 → P1、P2、P4 AMBIGUOUS；e59 掩码复刻失败或读数非有限 → P1 AMBIGUOUS（P2、P4 只涉 D，不受影响）；P4 另加：`p90_mae_classical ≤ 0`（经典 MAE 非正，比值无定义）→ AMBIGUOUS；V3 不过 → P5–P7 AMBIGUOUS；|B_p|<3 → P5、P6 AMBIGUOUS（V7：visc 路径 |B_V|=3 踩线，单点失手即触发）；倍数任一为 None → P6 AMBIGUOUS。**P6 并列规则**：R 或 M 出现相等值时按 (terrain, visc, short) 固定下标序定秩（稳定排序），不另判 AMBIGUOUS。AMBIGUOUS 不计押中、不计推翻，如实报告。原 P3 已降级为 V8，不在本判则内。
10. **方案对 spec 的两处收窄（封存前定死，非临场改动）**：n 网格从 8 起（spec 原文 4 起；n=4 时自由度只剩 2、λ̂ 近两点拟合，可预见假失覆盖，创新升级方案 §T3 已改 8 起）；代理三条 D/u_max/E59 score_te（spec 曾提「跨向代理」，方案已删）。

## 4. 真预测（P1、P2、P4、P5、P6、P7 共 6 条，每条单一布尔式；只有本节计数；推翻原样保留）

编号沿用草稿以保可追溯；原 P3 封存前降级为验证性断言 V8（见下）。

**P1（主判决·覆盖率）**：`min over {3 代理 × n∈{8,12,16,24,32}} 的均值 90% PPI 区间经验覆盖率 ≥ 0.86`。
点预测（不判分）：各格 0.88–0.93。被推翻的含义：λ̂ 噪声或非正态尾在小 n 打穿设计基口径——如实报哪一格、差多少；「覆盖率现场可复算」话术降级为「大 n 档成立」。

**P2（省真值·D 代理）**：`saving(D, n=16) = n_eff/n ≥ 2.0`。
点预测（不判分）：2–8 之间。被推翻的含义：案例级 corr(f_D,Y) 不足以省一半真值——真值预算表照发，结论改为「本总体上代理省真值有限，真值必须买」。
**邻接钉死**：f_D=u|all|rms 对本总体 skill 的**秩**相关在盘已知（Atr 查表，V8 印出），且 PPSR 已给出「节省比≈Pearson r²」的渐近关系（§8-1）。本条真赌注**只在**：秩相关→线性（Pearson）相关的落差、N=58 有限总体 FPC 对 n_eff 的封顶（n_eff≤N）、以及 n=16 删一刀切方差相对渐近方差的膨胀这三层；秩序本身视为在盘已知，不当预测卖。`descr_ppsr_like`（总体 r² 与无 FPC 渐近倍数 1/(1−r²)）与 saving 同表印出。

**（原 P3，已降级为 V8，不计分）**：`saving(D, n=16) ≥ saving(u_max, n=16)`。降级理由：E59_ARRAYS.npz 的 Atr 按行名单次查表即得 u|all|rms 与 u|all|max 对本总体 skill 的秩相关，而 obs.u_max 与 u|all|max 同为流速极值类读数（两者同源程度封存前未核，判分时由 V8 的描述性 spearman 印出，不预设）——「D 与 u_max 谁更贴真值」在秩序层面可由两次查表派生，与创新升级方案放弃清单第 11 条判死 E66 经向赌注同一把刀。封存前**未**打开 Atr 查看两值（降级不依赖查表结果），判分时机械印出布尔值与两查表值。若判分值与查表秩序相反，只作为「秩→线性落差」的描述性发现记录。

**P4（分位点估计效率）**：`p90_mae_ppi(D, n=16) ≤ 1.0 × p90_mae_classical(D, n=16)`（1000 次抽样中 |点估计−θ_p90| 的中位数之比）。
点预测（不判分）：0.7–0.95（合成校准 n=16 各 corr 档为 0.65–0.94，CALIB_SYNTH.md）。申报：N=58 的分位粒度粗（自报弱点，方案 §放弃-10 同源）；分位**区间**不押（保证式的精确经典区间覆盖率作为 §6 报表量印出）。被推翻的含义：代理连分位点估计都帮不上——预算表分位列如实标「代理无增益」。

**P5（rectifier 测谎·方向）**：`R_T > 0 ∧ R_V > 0 ∧ R_S > 0`（R_p 为 ĥ_cal=U∖B_V 拟合下的**拟合集外残差**中位，§3-8；三条路径都为正：刷分把读数做小，真差距被校正项接住）。

**P6（rectifier 测谎·排序，最大胆的一条）**：`(R_T,R_V,R_S) 的排序 = (M_T,M_V,M_S) 的排序`（R 同 P5 口径；本口径复算倍数，§3-8；并列按 (terrain,visc,short) 固定序定秩，§3-9）。注：visc 路径只有 3 点、M_V 的 ref 只有 1 臂（V7），排序中 visc 一格的抽样不确定性大，自报。
被推翻的预写话术（两版，封存后按 verdict 选版不得混用）：
- 通过版：「尺子每被刷狠一档，校正项涨一格——rectifier 就是被刷程度的带保证读数。」
- 未通过版：「rectifier 量的是『提交态离真值多远』，不是『读数被吹大多少倍』——两者在换地形路径上解耦（平底臂对平底问题本来就诚实，它骗的是考题不是读数）。测谎读数仍然三条路径全正（P5）〔此半句仅当 P5=TRUE 时保留，否则删去〕，但『按刷分强度排序』这半句我们赌输了，判据封存在先，照实报。」

**P7（朴素被骗、PPI 仍覆盖）**：`混合总体上 朴素替代覆盖率 ≤ 0.50 ∧ PPI 覆盖率 ≥ 0.85`（n=16，1000 次）。混合总体的新增成员实际来自**换地形与缩短积分两路径**（B_V 已在 U 内，去重后零新增，§3-8）；朴素填充用 ĥ_cal。
点预测（不判分）：朴素 <0.2，PPI 0.87–0.93。这是 Baumann（arXiv:2509.08825）「LLM hacking／朴素替代出偏」现象在物理基准上的对照实验版。

## 5. 判分

`tb_verdict.py` 只读两个 JSON（外加 TB_SELFTEST.json 供 V5），按 `tb_common.py` 冻结常量机械输出 `verdict.json`（TRUE/FALSE/AMBIGUOUS）；计数只含 P1、P2、P4、P5、P6、P7；V1–V8 验证性断言在 `verification_assertions_not_counted` 下印出、不计数：

| 常量 | 值 | | 常量 | 值 |
|---|---|---|---|---|
| COV_MEAN_MIN | 0.86 | | NAIVE_COV_MAX | 0.50 |
| P90_MAE_RATIO_MAX (n=16, D) | 1.0 | | PPI_MIX_COV_MIN | 0.85 |
| NEFF_D_MIN (n=16) | 2.0 | | MIN_POP / MIN_BRUSHED | 40 / 3 |
| DRAWS / SEED_A / SEED_B | 1000 / 20260917 / 20260918 | | VISC_BRUSH_MIN / GRADE_TOL | 3000 / 1e-3 cm/s |

## 6. 次级条目（不设通过线，只落盘）

- 预算表全表（含经典对照列、区间宽、精确 p90 区间覆盖率与无界比例）＋ Dorner 参考线标注；
- corr(f,Y) 三条代理的总体相关、corr(f_D, obs.u_rms)（描述性）；PPSR 同框列 `descr_ppsr_like`（总体 Pearson r² 与无 FPC 渐近倍数 1/(1−r²)）；
- ĥ58 下各路径 rectifier 中位（描述性，visc 路径样本内，§3-8）；V6b 初赛 62× 口径搜索结果；
- 三路径 Y_bench 均值、读数均值、R_p 的 IQR、逐 run 名单；
- 短算例的匹配时刻口径 err（descr，若补算则另存字段，不与 Y_bench 混表）。

## 7. 排队尾（明示不做进判分）

(c) 主动推断「下一个真值算例跑哪个」（Zrnic & Candès arXiv:2403.03208）与共形逐算例保单（#4，自报四条中最小、n≈30 分位粒度粗，方案 §放弃-10 判排队尾/降附录）：本预注册**零预测、零判分**；若封版前有富余时间，只作为附录描述性演示，且须另立预注册。

## 8. 申报事项（与结果同页印出；每条对应一项说过头风险）

1. **PPI 用于评估是密集前沿，先亮再说增量**：Angelopoulos et al. 2023（Science 382:669 / arXiv:2301.09633，本地 436）、PPI++（arXiv:2311.01453）、Boyeau et al.（arXiv:2403.07008）、Dorner et al.（arXiv:2410.13341，本地 224）、**Baumann（arXiv:2509.08825，本地 312）已量化朴素 LLM 替代的下游偏差**、**PPSR（Gao, Sicilia, Shi, arXiv:2608.26638 v2，2026-08-30）**。PPSR 要点（摘要已读；正文经 WebFetch 摘要工具读取 arXiv HTML，引句为工具返回、非本人逐字通读）：提出 prediction-powered evaluation（参数/非参数两套程序，配对/非配对设计效率权衡，λ̂ 由样本协方差估计，§4.1），在六个 WMT 数据集验证；**覆盖率已做闭环验证**——以全集人工均分差为总体真值，无放回抽 U+L、L 从 20 扫到 200、U=800、重复 1000 次，报「coverage close to the nominal 95% level」（§6.2）；**「哪个指标最省人工标注」已被做成元指标 PPSR**，定义为系统对上人工分差与指标分差的样本 Pearson r² 的平均，解释为「the fraction of human annotations saved」（§5.1–5.2）。据该工具对正文的检索，PPSR 未出现 finite population correction（方差式不含 1−n/N）、未涉及分位数、未出现 adversarial/gaming/hack/manipulat/Goodhart/shift/robust 等词。
   **因此收窄**：「省真值倍数」这一列是 PPSR 节省比的有限总体版本（本表 n_eff/n 与 PPSR 的关系：无 FPC 渐近下 n_eff/n≈1/(1−r²)，同表并列印出），**不主张新**；「PPI 区间覆盖率在已知真值上闭环验证」PPSR 已做，**不再列为增量**。据我们检索未见（范围：本地 417 篇全文库 grep ＋ arXiv 页面/HTML 核对 PPSR，2026-09-17；外网系统检索未做，口径注明「本地库已查、外网待补」）的只剩三点窄增量：①**刷分审计用法**：rectifier 作为对抗审计读数在三条实测刷分路径上的测谎（P5/P6），以及刷分污染混合总体上朴素替代 vs PPI 的覆盖对照（P7，Baumann 现象在「代理被刷」情形下的物理基准对照版）；②**小有限总体口径**：N=58、n/N 最高 0.55 时 FPC 对省真值倍数的封顶、删一刀切方差在 n≤16 的必要性、以及分位维度 PPI 区间被合成校准判死的负结果（均为已知统计工具在小 N 下的组合，不主张方法新）；③预注册-封存-机械判分协议本身作为交付物。此外一切表述从「首次」降为上述口径。
2. **不得说「不再需要真值」**：结论恰相反——真值可**定价**（n_eff 曲线=预算表）不可**归零**（FPC 项、rectifier 依赖配对真值、N 有限）。预算表页脚印这句话。
3. **rectifier 概念是 PPI 自带的，不据为己有**；我们只主张「对抗审计读数」这个用法；其地位不同于免真值的 A1–A9 审计（它要花真值），判定表里单列标注。
4. **E59 代理的选择污染**：c* 由用过纬向真值标签的模型选出，对本总体不是免真值代理；报表中 e59 列标「机选（选择时见过真值）」，不与 D/u_max 并列卖点。
5. **Dorner 因子-2 是别的假设域**（judge 型标注、超总体口径）；参考线只作对照，不声称「打破定理」——我们的代理带物理侧信息，本就不在其定理条件内。
6. **62×/224×/28× 属初赛口径**（fig_llm.py 硬编码，20260816 复核注释），与本口径并列印出、不互替（V6）；本预注册一切计分只用本口径复算值。
7. **揭盲子集必须随机**：SRSWOR＋冻结种子＋冻结循环序写死在脚本里；结论限「本纬向陡地形旋钮总体（N=58）」，不外推真实海洋、不外推其他风向。
8. **Y_bench 跨地形比较的语义**：flat 提交态对 steep 真值的 err 是「答错考题的距离」（审计语义），不是物理相似度声明；正文注明。
9. **负结果预注册如实报**：P4/P6 是自报高风险条；两版话术已在 §4 预写，AMBIGUOUS 按 §3-9 条款报「不可判＋原因」，不得改口成半个通过。
10. **数字纪律**：一切上台数字出自 TB_BUDGET.json / TB_RECTIFIER.json / verdict.json 并附 JSON 指针；不写「首次/第一」。
11. **总体含刷分点**：(a) 的 N=58 总体含 3 个荒谬黏性 run（B_V⊆U，V7）；预算表结论限「本账本陡地形旋钮总体（含 3 个刷分黏性点）」，不说成「诚实 sweep 总体」；(b) 的 rectifier 计分口径已改为 U∖B_V 拟合、全部路径为拟合集外残差，ĥ58 样本内口径只作描述。
12. **原 P3 降级**：D 与 u_max 的秩序层面在盘可查（Atr），降为 V8 不计分；上台时「买哪条代理」的推荐行须同页注明「秩序在盘已知、本条只报线性/小样本层面读数」。
13. **visc 路径脆弱**：|B_V|=3=MIN_BRUSHED、M_V 的 ref 只 1 臂（V7）；P5/P6 的 visc 一格即使判出也只可说「3 点中位」，不外推。

## 9. 执行清单（封存后）

```
0) （封存前，已完成）preseal_sets.py（元数据）→ tb_selftest.py（合成）→ 状态行 → bash seal.sh
1) bash run_all.sh     # 三查(free>140G / monitor-active 空 / coawstM 无) → systemd-run --scope MemoryMax=16G nice19
                        # OMP=4；串行：tb_budget → tb_rectifier → tb_verdict；日志 RUN_ALL.log
2) 产出：TB_BUDGET.json、TB_RECTIFIER.json、verdict.json（各含 prereg_seal 指针；前两者含 elapsed_s）
3) 预计耗时：U 底量 58 ＋ E59 经向掩码复刻 ＋ 纬向掩码复刻(V8) ＋ 刷分路径 grade ~45 run ＋ MC
   ≈ 总 10–20 min；超 20 min 则改 setsid nohup 挂起并写 COLLECT.md
```

## 10. 偏差政策

- 封存后发现笔误/崩溃级 bug：修复不得改动 §4 布尔式与 §5 阈值的语义；每处改动记 `DEVIATIONS.md`（改了什么、为什么、改前后 sha256），封存文件本身不动。
- 数据结构与预期不符（N≠58、路径集合过小、E59 行数不符等）：按 §3-9 AMBIGUOUS 判则机械处理，不得临场改门槛。
- 本文件与 `tb_*.py` 语义冲突时：以**脚本**为准（文件即定义），冲突本身记 DEVIATIONS.md。

## 11. 封存前修订记录（2026-09-17，草稿 sha256 32785757…1f71448 → 本定稿；均发生在任何留出读数与判分输出之前）

独立检查意见六条，逐条落实：
1. [重要] B_V⊆U 未申报 → §3-8 明写事实；R_V 选口径（甲）：ĥ_cal 在 U∖B_V 上拟合，三路径统一为拟合集外残差；ĥ58 降为描述性对照；P7 叙述改为新增成员只来自换地形与缩短积分；(a) 总体构成申报（§3-8 末、§8-11）。代码：`tb_common.is_BV/is_BS/twin_pairs`、`tb_rectifier.py` h_cal/naive 填充/新增成员计数。
2. [重要] P3/P2 逼近已知答案换皮 → 原 P3 降级为 V8（不查表即降级，判分时印出 Atr 两查表值）；P2 加邻接钉死句，真赌注限定在秩→线性落差＋FPC 封顶＋n=16 刀切膨胀。代码：`tb_common.rebuild_e59_names_zonal`、`tb_budget.py V8_lookup/descr_ppsr_like`、`tb_verdict.py` 计数只含 6 条。
3. [一般] 路径集合尺寸未预注册 → 新增 `preseal_sets.py`（只读元数据）→ `PRESEAL_SETS.json` → V7（含 |B_V|=3 踩线脆弱性、ref 单臂）。
4. [一般] 封存门松动 → `require_seal` 对「列出但缺失」「清单缺列」「行格式异常」「时间戳行≠1」一律拒跑；`seal.sh` 去掉 `2>/dev/null || true`，改逐文件存在性检查＋临时文件原子改名＋判分输出已存在即拒封。
5. [一般] P4 守卫与 P6 并列规则未申报 → §3-9 补两句。
6. [一般] 检查员沙箱 `../inspect_20260917/` → 封存前删除（删除前 sha256：tb_common.py e9801bc8…、TB_SELFTEST.json 47ff1604…、tb_selftest.py 599b4d2f…，记入 RESULT）。

另：PPSR 摘要与正文要点已读，§8-1 按其内容进一步收窄（「覆盖率闭环验证」与「省标注倍数元指标」不再列为增量）。
