# 预注册：negctrl_surrogate 验证批（E72）——平底孪生差分校正 · 互斥对修复免疫

状态：定稿待封存
条目：GOAI 2026 赛道三决赛 · 旗舰 4（negctrl_surrogate，候选与评分.json id 同名）
起草：2026-09-17（虎虎队）；执行目录 `/data/xinyuan/GOAI_ai4s_env/e71_innov/negctrl_surrogate/final/`
封存前动作：把第 3 行状态行改为「定稿待封存」，然后运行 `bash seal.sh`（脚本对状态行做行首锚定检查，本说明行不含可命中的行首模式）。

---

## 0. 封存流程与时序（协议）

1. 本文件冻结判据后：`sha256sum PREREG_negctrl_surrogate.md > PREREG_negctrl_surrogate.md.sha256 && sha256sum e72_valid.py e72_verdict.py SEEDS82.json E72_SELFTEST_ZONAL.json >> .sha256 && date -Is >> .sha256 && chmod 444`（由 `seal.sh` 一键执行，二次封存被脚本拒绝）。
2. **封存必须早于读取任何留出读数与判分输出。** `e72_valid.py --holdout` 与 `e72_verdict.py` 内置封存门：无 `.sha256`、**入档五件（PREREG、e72_valid.py、e72_verdict.py、SEEDS82.json、E72_SELFTEST_ZONAL.json）任一哈希不符**、或自检未全绿，一律拒跑。其中 PREREG 与 SEEDS82 哈希不符**永不放行**；两脚本或自检文件哈希不符仅当 `DEVIATIONS.md` 在场（§10 崩溃修复已申报）才放行。运行时两脚本的实际 sha256 印入 `E72_VALID.json` 与 `verdict.json` 供事后核对。
3. 封存后发现写错：只记 `DEVIATIONS.md`，不改封存文件（见 §10）。
4. 判分机械输出 `verdict.json`（`e72_verdict.py`，只读 `E72_VALID.json`，不重算任何统计）。
5. 真预测被推翻的，原样保留、原样上台。

---

## 1. 验证性断言与已知量（封存时已知答案，一律**不计分**）

### 1.1 管线锚（已执行，封存前完成）

- V1：正式版流水线（`e72_valid.py`，与留出域完全同一代码路径）在纬向自检中逐字复现试点 E71B/C/E 的 58 项关键数字，**58/58 全绿**（`E72_SELFTEST_ZONAL.json`，`all_match=true`；含 ρ(D,A) 三口径、置换 p、全部 gate 计数、OS 家族统计、演示位 5.71×/4.341）。
- V2：纬向 82 把复合门两全候选名单已于验证前存档：`SEEDS82.json`，n=82，sha256 `561dc4ea04f53137bb6aac16e048571a715c8387d2ece98a7d7eb5172488cbe0`；82 把在纬向按 P2 门（A*_diff≥0.5 ∧ |D*_diff|≤0.5）全部存活（闭环自检项）。
- V3：复算 A/B/D 与 `e65/E65_AXES.npz` 逐候选最大绝对差 = 0.0（试点锚，自检间接覆盖）。

### 1.2 已知量排除清单（这些数字在封存时已在盘上，**任何与之等价或可由之派生的量都不得当预测卖**）

| 已知量 | 值 | 落盘出处 |
|---|---|---|
| E65 两关同过 / ρ(A,B) / ρ(D,A) | 204 / −0.6742（并列平均秩口径 −0.7322）/ +0.9762 | e65/、metric_search.py 双口径 |
| 经向偏相关 | ρ(D,A⊥)=0.4814 | e66/E66_PARTIAL.json（2026-09-05 落盘，只能当样本内校准） |
| 经向**原始**轴与决策级 | ρ(A_z,A_m)=+0.874、ρ(D_z,D_m)=0.911、ρ(D_m,A_m)=0.9994、204 vs 407 交 88、κ=0.275、Jaccard=0.168、P(A_m<0\|A_z≥0.7)=2.49% | e71_innov/multienv_metrology/（2026-09-17 凌晨试点） |
| 初赛期两留出域的原始读数搜索件 | （未读，但在盘） | ledger/metric_search_merid.json、ledger/metric_search_diag45.json |
| E67B 配方迁移 | 88/140/80、经向存活 0 | e67/E67B_RECIPE_TRANSFER.json |
| 纬向试点全部数字 | ρ(D*,A*)=0.9144/0.8831/0.9204（p=0.0005）、耦合 0.9978、天花板 0.5927/0.5927/0.5832、互斥 −0.651→−0.2661/−0.2943、82 把、OS 家族 18.4%→21.6%、47.3%、演示位 5.21×/5.71×/13.3×/e^4.341≈76.8、τ(H,V)=0.994（n=37）、正对照 CI[−0.434,−0.000] | 本目录 E71A–E 五个 JSON 与 PILOT.md |
| 纬向 sweep 阶梯参考 | τ(H,V)=1.0（7 档），err 正对照在阶梯上自动「判死(与旋钮共线)」 | final/E72_SELFTEST_ZONAL.json（封存前查明，决定 P7 判据形态，见 §4-P7） |
| **sweep 账本自带 obs 读数** | `ledger/knob_sweep_*.json` 每行 obs 含 `deep_rms_800/u_max/u_rms/surf_max`（纬向核验：u_max 与 base_quantities 的 u\|all\|max 14/14 逐位同、deep_rms_800 与 u\|d800\|rms 3/14 逐位同其余相对差 ≤1e-2；steep/flat 两臂皆有）⇒ 两留出域的「u\|d800\|rms 原读数改善」与「lr(vmax)」可由在盘账本一步算术读出 | 封存前查明（2026-09-17），据此把原 P5 降级为验证性断言，见 §1.4 |

**推论（诚实口径）**：两留出域上一切**只涉原始（未校正）读数轴**的量，或为已落盘、或原则上可由在盘文件派生——一律不押。真预测只押封存时**任何落盘产物中都不存在**的量：平底孪生**校正**读数轴（A*/D*）、82 把种子的跨域存活、sweep 上的校正读数轨与 OS 家族分布、阶梯共线度 τ(H,V)。若封存后发现其中某量另有先前落盘出处，该条降级为验证性断言并记 DEVIATIONS.md。

### 1.3 行文更正（试点文档，随材料修正一并处理）

- PILOT.md「58 陡臂 + 52 平底臂」中 52 为**账本行数**（含重复 run_id 行）；去重后平底臂为 **44**（E71B_RUV.json `n_runs_flat=44` 为准，账本 52 行 → 44 个唯一 run_id，2026-09-17 复核）。
- 62× 不属本预注册（见 §8-5）；BH93 卡片数字出处更正另文（见 §8-6）。

### 1.4 原 P5 降级为验证性断言（V4，封存前处理，不计分）

原草稿 P5「演示位跨域复现」押 `u|d800|rms` 的原读数改善 ≥3× 与 lr(vmax)≥3.0。封存前查明（§1.2 末行）：sweep 账本 obs 自带 `deep_rms_800` 与 `u_max`，两子句的答案均可由**初赛期已在盘**的账本一步算术读出——按 §1.2 推论「只押盘上不存在的量」，此条不合格为真预测，**降级为验证性断言 V4**：

- V4（描述性判定，照算照印、不入计分）：对两域 VISC2 阶梯上的 u|d800|rms，`原读数改善 r(v_min)/r(v_max) ≥ 3.0 ∧ log(r_steep/r_flat)(v_max) ≥ 3.0`。纬向已知 5.71× / 4.341（e^4.341≈76.8，台词「约 77 倍」）。判定结果印入 verdict.json 的 `descriptive_P5_demo` 块，**不计入 n_true/n_false/n_ambiguous**。
- 演示位台词照常使用这些数字（它们本来就是演示位、不是赌注）；真预测缩为 **P1–P4、P6、P7 共 6 条**。

---

## 2. 留出集精确语义

**语义声明**：留出 = **本条目（negctrl_surrogate）流水线在封存前未输出、未使用任何留出域数值**；不主张全队历史零接触——历史接触产生的全部已知量已在 §1.2 逐出预测集。文件 IO 层面的一处例外如实申报：`ledger/regraded_v2.jsonl` 同时含纬向与经向/45° 行（后两者即两留出域的 H 真值 skill_vs_zero），试点脚本（e71b）与 2026-09-17 09:29 的 `--selftest` 曾**整文件载入**该账本、仅按纬向 run_id 索引使用——留出行的数值未被打印、未落盘、未参与任何决策；不主张「文件 IO 层面零读取」。加固（封存前已改）：`e72_valid.py` 的 domain_block 现先载本域账本 run_id 集、再**按域过滤**载入 regraded_v2，自检重跑复核数值不变。multienv_metrology 条目的封存预注册同样押 45°：两条目独立封存、独立判分，互不引用对方封存后的留出产出；时序上均为先封存后读。

**封存后 `--holdout` 模式允许读取的文件（白名单，读此外任何留出文件即违规）**：

- `ledger/env2_merid_runs.jsonl`、`runs_merid/`（预期 28 对 + sweep 臂）
- `ledger/env2_diag45_runs.jsonl`、`runs_diag45/`（预期 28 对 + sweep 臂）
- `ledger/knob_sweep_merid.json`、`ledger/knob_sweep_diag45.json`（VISC2 阶梯，预期各 7 档×2 bathy）
- `ledger/regraded_v2.jsonl`（历史接触见上方语义声明；本批按域账本 run_id 过滤载入，允许查经向/45° run_id 的 skill_vs_zero）
- `e60/runs/`（陡度轴，**仅 §6 描述性**，无任何计分量）

**明确不读**：`e70/`（在跑，禁触）、`e44/`（内潮）、`e56/` 读数（BH93 出处核查另文、不做统计）、`e66/E66_AXES.npz`、`e67/` 结果数组、`e63/`（隔离红线）、其他队伍/赛题任何数据。不调用任何大模型 API。

---

## 3. 冻结的操作定义（`e72_valid.py` 文件本身即定义，封存时 sha 固定；此处为摘要）

1. **配对**：域账本内 `obs.valid ∧ ntimes==8640` 的行，按 (VISC2,VISC4,AKV_BAK,TNU2) 各 round 6 位分组（缺键计 −1）；重复 run_id 行后行覆盖前行（dict 语义，与试点一致）。陡臂标签：有 `r26steep` 用之，否则取唯一的非 flat/mit 标签。孪生对 = 同四元组下 steep+flat 双全。
2. **真值标签 H（域级统一，不逐 run 混用）**：该域配对陡臂全部有 regraded_v2 skill_vs_zero → H=skill_vs_zero；否则全部用 H=−hidden.err_rms_vs_truth。每域实际用哪个印入 E72_VALID.json（`h_source`）。
3. **轴定义**（读数 r；d=r_steep−r_flat；lr=log r_steep−log r_flat）：A\*(x)=−spearman_ms(x,H)、D\*(x)=spearman_ms(x, 该域配对陡臂 u|all|rms 原始值)、B(x)=mean(flat 读数≥steep 读数)（E65 定义，该域配对上）。候选构造与 e71b 逐行同构（124 基元＋比值，过滤规则相同；自检 58/58 为证）。
4. **spearman 双口径**：判分一律用 `metric_search.spearman`（不做并列平均秩，与全项目管线一致）；scipy 并列平均秩版一并落盘只报告不判分。
5. **B\* 仅黏性路径**（E71A 实测：缩短积分路径仅 1 个四元组配得齐，判不可行）；sweep = 该域 knob_sweep 中 knob==VISC2 且 steep/flat 双全的档位升序。OS_raw=log(r(v_min)/r(v_max))/log(err(v_min)/err(v_max))，OS_lr 分子换 lr 差；要求 dlerr>0，否则 P6 记 AMBIGUOUS。
6. **A_surr 机器**：τ_b=scipy kendalltau；偏 τ、bootstrap 2000、判死/存疑规则逐字沿用 e71d。
7. **AMBIGUOUS 判则（冻结）**：域配对数 <20 或候选数 0 → 该域 **P1–P4、P6** 记 AMBIGUOUS（P6 的 OS 家族定义在配对候选族上，判分器 p6 同样先查配对门）；sweep 档位 <5 → 该域 **P6–P7** 记 AMBIGUOUS（原 P5 已降级为 V4 描述性，判定同门槛照印不计分）；sweep 缺 hidden err 或 dlerr≤0 → P6 AMBIGUOUS；H 不可得或档位 <3 → P7 AMBIGUOUS。P4 的 |D*_logr|≤0.3 集合为空 → 该域记空真 PASS（计数印出）。**域级流水线异常崩溃**（数据结构偏离预期导致某留出域整域算不出）→ 该域块以 {error, status:AMBIGUOUS} 落盘、另一域照算，该域全部预测记 AMBIGUOUS，不中断整批。
8. **合并规则**：每条预测按 merid、diag45 两域求值；任一域 FAIL → 预测 FALSE；否则任一域 AMBIGUOUS → AMBIGUOUS；两域皆 PASS → TRUE。AMBIGUOUS 不计入押中、不计入被推翻，如实报告。
9. **种子存活（P2）**：分母恒为 82；候选在该域不可算（被过滤）= 死亡。富集 = 存活率 ÷ max(全库同门通过率, 1/n_cand)。

---

## 4. 真预测（P1–P4、P6、P7 共 **6 条**，每条单一布尔式；只有本节计数；推翻原样保留。原 P5 已降级为 §1.4 V4，编号保留不复用）

**P1（主判决·结构复现）**
布尔式：`ρ_ms(D*_logr, A*_logr)_merid ≥ 0.50 ∧ ρ_ms(D*_logr, A*_logr)_diag45 ≥ 0.50`
点预测（不判分）：两域均落 0.80–0.95。纬向已知 0.9204（p=0.0005）。
被推翻的含义：免拟合校正在留出域打破了 D–A 耦合——那将是「两全族可能存在」的旁证，如实报，且与 P2 联判。

**P2（两全族存活）**
布尔式：对 merid 与 diag45 都有 `surv82 ≥ 0.30 ∧ enrich ≥ 5.0`，其中 surv82 = |{82 把中 A*_diff≥0.5 ∧ |D*_diff|≤0.5}| / 82，enrich = surv82 ÷ max(全候选同门通过率, 1/n_cand)。
被推翻的含义：82 把是纬向自适应复用的产物（Blum & Hardt），死亡加固 P1 的结构线（§7 未通过版话术）。

**P3（互斥缓解复现）**
布尔式：`ρ_ms(A*_diff, B)_merid ≥ −0.45 ∧ ρ_ms(A*_diff, B)_diag45 ≥ −0.45`
对照（不判分）：各域原始口径 ρ_ms(A*_raw, B) 同表印出（纬向 −0.651 → 校正 −0.2661）。

**P4（天花板不动）**
布尔式：`max{A*_logr : |D*_logr| ≤ 0.3}_merid ≤ 0.70 ∧ 同_diag45 ≤ 0.70`（空集=空真，计数印出）。
纬向已知 0.5832。此条与 P2 是**一对张力**：P2 押校正族有真金、P4 押真金不在「近零伪流区」——两条可同时成立（82 把门在 |D*|≤0.5 不在 ≤0.3），也可能一起打脸，判分互不挂钩。

**P5（已降级，不计分）**
原布尔式（u|d800|rms 改善 ≥3× ∧ lr(vmax)≥3.0）的答案可由在盘 sweep 账本 obs（`deep_rms_800`）一步读出，违反 §1.2「只押盘上不存在的量」——封存前降级为验证性断言 **V4（§1.4）**，照算照印于 verdict.json `descriptive_P5_demo`，不入真预测计数。演示位数字（5.71×/77×）不受影响。

**P6（家族级负结果复现：校正不是普遍抗刷药）**
布尔式：对两域都有 `frac(||OS_lr|−1| < ||OS_raw|−1|) ≤ 0.55`。
纬向已知 0.473。此条押的是**负结果的稳定性**：若某域该值显著 >0.55，说明校正在那个域反而是家族级止刷药——预测被推翻，但那是校正的好消息，照实报。

**P7（A_surr 适用域：阶梯近共线复现）**
布尔式：`|τ_b(H, VISC2)|_merid ≥ 0.85 ∧ |τ_b(H, VISC2)|_diag45 ≥ 0.85`（各域 VISC2 阶梯陡臂上）。
草稿版原有第二子句「err 正对照不被判死」，封存前自检查明其在 7 档阶梯上**结构性不可能**（纬向参考 τ(H,V)=1.0 → 正对照自动「判死(与旋钮共线)」，E72_SELFTEST_ZONAL.json）——把注定失败的子句冻进判据是假赌注，故删除；正对照照算、只作描述性报告（§6）。P7 成立 ⇒ A_surr 定稿口径 = 三要素表 + 共线敞口标记（τ(Z,V)≥0.98 判「旋钮复读机」），CI 数字不进主页面；P7 被推翻 ⇒ 留出域存在可检剩余变差，A_surr 反而升格，按 e71d 规则补跑并如实报。

---

## 5. 判分

`e72_verdict.py` 只读 `E72_VALID.json`，按下表冻结阈值机械输出 `verdict.json`（三值：TRUE/FALSE/AMBIGUOUS；合并规则见 §3-8）：

| 常量 | 值 | | 常量 | 值 |
|---|---|---|---|---|
| P1_rho_min | 0.50 | | P5_impr_min | 3.0 |
| P2_surv_min | 0.30 | | P5_lr_min | 3.0 |
| P2_enrich_min | 5.0 | | P6_frac_max | 0.55 |
| P3_rho_min | −0.45 | | P7_abstau_min | 0.85 |
| P4_maxA_max | 0.70 | | MIN_PAIRS / MIN_SWEEP | 20 / 5 |

注：P5_impr_min / P5_lr_min 保留在 TH 表中仅供 **V4 描述性判定**（§1.4）复用，不参与 n_true/n_false/n_ambiguous；判分器对 6 条真预测（P1–P4、P6、P7）计数，`n_predictions=6`。

---

## 6. 次级条目（不设通过线，只落盘）

- e60 陡度轴：校正读数（lr）随陡度的轨迹与配对表，纯描述（无真值）。
- 各域 sweep 的 err 正对照 A_surr 判定（描述性，见 §4-P7 说明）、demo 双轨（u|all|max、u|d800|rms 的 steep/flat/logratio 全轨，供一秒重算演示页接数）、V4 描述性判定（原 P5 门槛照印，§1.4）。
- 置换 p（2000 次、种子 0）与 scipy 并列平均秩副口径。
- ρ(D*_c, A*)（校正读数对校正后伪流幅度的耦合；纬向已知 0.9978）。

---

## 7. 82 把苗子——两版话术（预写，封存后按 verdict 选版，不得混用）

**通过版（P2=TRUE）**：「我们把纬向筛出的 82 把两全候选名单连同判据一起 sha256 封存，然后才去读两个从未读过的环境。它们活下来了：经向存活 X/82、45° 存活 Y/82，富集 Z 倍（判据封存在先，verdict.json 机械判定）。据我们检索未见（本地 417 篇全文＋arXiv export API，2026-09-17；外网杀检索见 §8-7）负对照差分校正在受控真值考场产出可跨环境复核的两全候选族的先例；近邻同框：Mandoline 需带标签源数据、CARE 拟合潜因子，我们免拟合。申报：复合门 B*≠B，这 82 把没有、也不宣称通过原 B 关；32 对属先选后检（Blum & Hardt），所以才把验证押在封存后的留出域上。」

**未通过版（P2=FALSE）**：「82 把苗子死在了留出环境（存活 X/82，判据封存在先，死亡名单照印）。这把另一件事钉得更死：免拟合负对照校正救不出跨环境的两全尺子——与主判决同向（校正后 ρ(D*,A*) 纬向 0.88–0.92、留出域 [实测值]，p=0.0005），『刻度准与抗刷分不可兼得』是结构，不是读数没洗干净。名单、判据、sha256、死亡名单全部公开。」

**AMBIGUOUS 版**：按 §3-7 条款报「不可判＋原因」，不得改口成半个通过。

---

## 8. 申报事项（与结果同页印出）

1. 校正尺子量的是**地形特异响应**，不是全部保真度；不说「更准」；机时翻倍（每模式配平底孪生）写入协议成本条款。
2. 复合门 B*≠B，当众申报；「B* 合格」永远不得表述为「通过原 B 关」。
3. 纬向 32 对/37 臂属先选后检的自适应复用（Blum & Hardt，444 配方查询史）；试点一切数字只算探索。
4. A_surr 是条件独立近似，n 小功效低，只判死/存疑不认证；在旋钮完全决定真值的家族里无剩余变差可检（P7 正是把这句变成可判赌注）；CI 数字不上台。
5. **62×**：不属本预注册。试点在 7 档 VISC2 路径实测最大 13.3×，未出现 62×；62× 出自初赛图 3(c)（黏性 3×10⁴ m²/s、同参数配对中位，`github_repo/scripts/fig_llm.py`，README L16），与本路径不是同一口径——上台引用前须按 fig_llm.py 复算并注明「初赛口径」，只可与 5.71×/77× **并列**，不得互替。演示位默认 5.71×（u|d800|rms 原读数）＋「深层流仍是平底孪生的约 77 倍（e^4.341）」。
6. **BH93 卡片出处更正**：候选文案挂在 BH93 名下的 81%/ρ=±1/skill −8.48→−1.46 实为**纬向 VISC2 sweep** 数字（E56_BH93.json 无 skill 字段）；决赛材料一律改挂「纬向黏性路径（E71D 悖论表）」；更正说明另文，e56 在本批仅做出处核查、不做统计。
7. 「平底伪流按离散化理论必然为零（流行病学负对照只能假设为零）」一律挂「据我们检索未见」口径并注明检索范围与日期；两条外网杀检索（negative control correction × evaluation metric；surrogate paradox × benchmark validity）待有配额会话执行——**用户拍板项**，未跑完前口径注明「本地库已查、外网待补」。
8. 近邻主动同框：Shi/Miao/Tchetgen Tchetgen 2020（“mainly been used to detect bias rather than to remove bias”）、Gagnon-Bartsch & Speed 2012、Schuemie 2018 PNAS、Prentice 1989、VanderWeele 2013、Athey et al. surrogate index；anomaly experiment 是海洋界家常便饭、BH93 本质即负对照。全文不写「首次/首个/第一」。
9. 负结果按大赛「负结果不当然扣分」口径原样呈现；P1/P2/P6 任何一头的话术都已在 §7 与 §4 预写。
10. 判分双口径披露：`metric_search.spearman` 不做并列平均秩（E65 口径 −0.6742 vs 并列平均秩 −0.7322），本批判分用前者、副口径同表印出。

---

## 9. 执行清单（封存后）

```
1) 人工把 §状态 行改为「定稿待封存」→ bash seal.sh          # 封存
2) bash run_valid.sh                                        # 自检(若缺)→留出验证→机械判分，串行
   资源：systemd-run --user --scope -p MemoryMax=16G nice -n 19，OMP=4，起批前查
   free / monitor-active / coawstM（脚本内置三查）
3) 产出：E72_VALID.json（内置 prereg_sha、elapsed_s）、verdict.json、
   E72_AXES_{merid,diag45}.npz、E72_BASEQ_{merid,diag45}.json、e60 描述块
4) 预计耗时：底量 ~140 run × ~0.3s + 候选枚举 2×~15s + 置换 2×~30s ≈ 3–6 分钟
```

---

## 10. 偏差政策

- 封存后发现本文件笔误/脚本崩溃级 bug：修复不得改动 §4 布尔式与 §5 阈值的语义；每处改动记 `DEVIATIONS.md`（改了什么、为什么、改前后 sha256），封存文件本身不动。
- 留出数据结构与预期不符（对数≠28、档位≠7 等）：按 §3-7 AMBIGUOUS 判则机械处理，不得临场改门槛。
- 本文件与 `e72_valid.py`/`e72_verdict.py` 语义冲突时：以**脚本**为准（文件即定义），冲突本身记 DEVIATIONS.md。
