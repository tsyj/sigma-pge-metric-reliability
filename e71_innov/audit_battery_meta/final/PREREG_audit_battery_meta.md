# 预注册 · 审计电池说明书（E71T2 正式版 · audit_battery_meta）

状态：**v2（2026-09-17 封存前修订版；封存记录见同目录 PREREG_audit_battery_meta.sha256）**。
封存后一字不改，笔误与实现层修复只记 DEVIATIONS.md。封存 = 在本目录执行：
```
sha256sum PREREG_audit_battery_meta.md > PREREG_audit_battery_meta.sha256
date -Is >> PREREG_audit_battery_meta.sha256
chmod 444 PREREG_audit_battery_meta.md PREREG_audit_battery_meta.sha256
```
**封存必须早于本条任何真实数据新计算的第一个字节**（§1）。abm_*.py 全部脚本在真实模式下做封存门控
（.sha256 缺失或与本文件不匹配即拒跑）；`--selftest` 模式只读合成夹具、不读任何真实 run/npz。
abm_verdict.py 机械判分，人不改判。

---

## 0. 目的、四模块与执行序

对审计电池（A1–A9 九算子＋判定表）自身做形式化与体检，合成《审计电池说明书》。

| 模块 | 内容 | 执行序 |
|---|---|---|
| ① MR 库 | A1–A9 写成蜕变关系四元组（mr_audit.yaml 声明化）；checker 按 RULES 从源 JSON 复导出判定、与 KILLBOARD 逐格对照 | 第 1 批（9/17 晚，封存后立即） |
| ③ Goodhart 覆盖矩阵 | 13 个死格分两科；A1–A9×失效类型覆盖矩阵，**只保「有实证检出/不覆盖」两档** | 第 1 批 |
| ④ 滤链曲线 | 不可刷配置集逐级扩张 L0⊃L1⊃L2⊃L3(⊃L4)，15376 候选逐级计数 | 第 2 批（先跑 V2 管线锚） |
| ② 变异 kill 矩阵 | 8 类×5 基=40 个显式名册变异体过电池可执行子集，差分检出率（Wilson CI）与漏网点名 | 第 3 批 |

产出只落 `/data/xinyuan/GOAI_ai4s_env/e71_innov/audit_battery_meta/final/`；既有实验目录一律只读；e70 不碰。

## 0.5 封存前修订记录（相对 09:55 草稿 v1，草稿原件存 `../_draft_history/`）

| # | 修订 | 触发 |
|---|---|---|
| R1 | 第二真实阳性锚改为 **E56_VERDICT.json:A1_paired_correct=0.0**（BH93 静止线 7 对平底≥海山比例，纯静止线、按 RULES A1 阈值机械判死）；`exaggeration=1.6895` 降为描述性文字并标明其**纬向风 sweep 出处**（proxy_drop=1−1.5072/8.7752 取 wind_deep800，true_err_drop=1−4.028/7.902 取 wind_err） | 评审［重要］1 |
| R2 | Pnet_MW 的 A3/A4 死复导出所需辅助事实（DOMWIDTH 判为域共振控制＝含义变；M2_phase 无 Pnet 稳健窗均键＝无稳健版）在 mr_audit.yaml 显式声明并挂指针 | 评审［重要］1 |
| R3 | wrong_region / wrong_layer 查表补全到 {all,d200,d400,d800,d1500,s50,s200} 全部源项；§2.5 列出 **40 个变异体显式名册**；公式重复体记 DUPLICATE、逐 run 读数恒等体记 EQUIVALENT，二者排出主分母 | 评审［重要］2 |
| R4 | 7 档参考 run 逐个钉死 run_id；**真值源改为 ledger/regraded_v2.jsonl 的 err_rms / skill_vs_zero**（原因：env2_runs.jsonl 同一 run_id 存在重复行且 hidden 真值口径不一——298 个 run_id 中 42 个有重复行、其中 23 个重复行 hidden 不同，例如 e2_266404276ec5 有 7 行、3 个不同 err_rms_vs_truth；regraded_v2 每 run 一行、口径 truth_day=1.0/truth_akv=1e-5，与 E57 的 A 同源）。全文不再使用 ledger hidden 字段 | 评审［一般］3 |
| R5 | 原 P2a（unit_scale 漏网≥1）按构造必真 → 移入 §4.3 构造性预期（不计数）；原 P1（checker 不一致=0）作者撰写 yaml 时已读全部格值 → 移入 §4.2 已知答案检查（不计数）；说明书写"7 把中 A2 对全比值基不出判定，有效 6 把" | 评审［一般］4 ＋封存前自查 |
| R6 | abm_verdict.py：全类不可判记 UNJUDGEABLE；输入 JSON 缺关键字段记 NOT_RUN 并置 PIPELINE_SUSPECT | 评审［一般］5 |
| R7 | **检出语义改为变异测试标准的差分杀死**（变异体在某算子判死而基指标在该算子不死）为主口径；草稿的"≥1 个死即检出"降为敏感性口径同报。理由：5 把基指标若自身在某算子已死，其全部变异体会被"继承性检出"，检出率不再度量对注入缺陷的敏感性 | 封存前构造审查 |
| R8 | A9′ 草稿定标（夸大倍数 >2 死）在静止线上**不可达**：静止线真伪流 u_max 降幅 0.8116（E56_VERDICT.bh93_umax 端点），任何保持非负的读数降幅 ≤1，夸大倍数上界 1/0.8116=1.232<1.25，按构造恒"过"。改为 RULES['A9'] 原文"判据同 A1/A8"在静止线 7 对/7 档上执行 | 封存前构造审查 |
| R9 | 滤链 L3 草稿规则"err(r)>err(v) 且读数更好"为空规则：regraded_v2 实查荒谬黏性 err_rms（10000: 3.4162；30000: 2.8349）低于全部 7 档参考（最低 4.0280），该式恒不触发。改为 E34（scripts/absurd_visc.py 文档串）原始定义的极值型判据：读数奖励越过物理量程的旋钮（见 §2.7） | 封存前规则输入核查 |
| R10 | 草稿 P2d（盒宽依赖漏网=0，理由"A3′ 按构造抓"）理由不成立：A3′ 判死条件是序变，而同一陡海山网格上盒宽因子对全部陡臂为同一常数、不改序；另 b1 分子区域 all 使因子恒为 1（等价体）。改押漏网≥1。草稿 P2f（截断作弊漏网=0）经构造审查：截断制造并列，A1 把并列计为"平底≥海山"反而抬高 B，秩算子对并列宽容，改押漏网≥1。P2i 区间按差分口径重定为 [0.20,0.60] | 封存前构造审查 |
| R11 | P4c 草稿写 "A≤−0.7∧B≥0.9"，与 E57_AB.npz 的 A=−ρ 约定反号；更正为 E57 约定 A≥0.7∧B≥0.9（=204 把） | 封存前自查 |

以上修订均在读取任何候选读数之前完成（§1 第 3 段如实列出封存前读过什么）。

## 1. 留出语义

本条不跑新模式算例；**留出读数 = 封存后才允许产生的一切新计算输出**：
1. checker 复导出判定与 KILLBOARD 的逐格一致性（ABM_MR_CONSISTENCY.json）；
2. 任何候选/基指标/变异体在任何 run 上的读数（out_his.nc 派生），及其一切汇总：滤链计数、电池判定、检出率；
3. 由 E57_AB.npz / E66_AXES.npz 派生的新计数（例如纬向 B=1.0 的候选数）——封存后算出标"派生非预测"；
4. abm_verdict.py 的判分输出。

**封存前实际读过的（如实）**：KILLBOARD.json 全部格（判定、文本、value、source）；RULES 源码（e44/scorecard.py）；
scripts/metric_search.py、e57_pareto.py、e66/e66_partial.py、e67/e67b_recipe_transfer.py、scripts/absurd_visc.py 源码；
E57_PARETO.json、E56_VERDICT.json、E56_BH93.json、RT2_FIXES.json、DOMWIDTH_RESULT.json（repo upstream）、E58_TRIVALENT.json、
E49_CROSS.json:tempd400_wind、E50_UV_AUDIT.json:boxwidth_500km、E52_CROSS.json、E55_CROSS.json 及其键名勘误、E54_NAMESWAP.json:conditions 计数、
ledger/metric_search.json:baseline、KB_EXTRA_CELLS.json、E44_METRICS.json（d_flatdj 与 pf_* 的 uv_ratio）中已印出的数字；
三本 ledger 的 run_id/action/valid/ntimes/bathy 结构与重复行统计；regraded_v2.jsonl 中 10 个钉死 run（§2.2）的 err_rms/skill_vs_zero（规则输入）；
out_his.nc 头信息（维度/形状/类型，无数值）。**未读取任何 run 的场数值，未对任何 npz 做汇总。**

## 2. 冻结口径

### 2.1 文件与 sha（封存前回填；封存后脚本不改，确需实现层修复时记 DEVIATIONS.md：原因＋前后 sha＋规则层不变声明）

| 文件（final/） | sha256 | 说明 |
|---|---|---|
| mr_audit.yaml | `d3b9b309fe4730bd7456e2f27d0cb972c190525dd51fe245f74718c2d25e5b1d` | ① MR 四元组、逐格声明（机器可判/辅助事实/指针）、③ 死格分科 |
| abm_common.py | `0ac0b416d53c593eae7f076cebe149da326d46f9b1f7f1bd9320525575ac98a6` | 共用：封存门控、秩相关、精确置换 p、Wilson、run 集合装载、扩展基元（阈缩放/帧/格点数） |
| abm_mr_checker.py | `50ca2f3fa05e8f64216a45b1a58d5347beb366645d9c1753dc5cb0226102e936` | ① → ABM_MR_CONSISTENCY.json、MR_TAXONOMY.md |
| abm_goodhart_map.py | `2464864d5f6d137fbe519f08c2af1502f355929f02e0f57f012d0d30054c4217` | ③ → ABM_GOODHART_MAP.json |
| abm_chain.py | `a618fe8e5695f6dec4347e5cdccc26b2016bd5cf923748d52d51f7528c1249d8` | ④ → ABM_FILTER_CHAIN.json、abm_chain_curve.png |
| abm_mutants.py | `d7e3d7a53fdea0986d1bac9e2028d9ca74b4a40d4d8438251e1be74cfb6df3a5` | ② → ABM_MUTANT_LEDGER.json、ABM_KILL_MATRIX.json |
| abm_verdict.py | `443dcecf7ce96c6ef2ccdcdc6851db53ec6589ae4e1e36df91cf9a9dd853e46a` | 机械判分 → verdict.json（§4/§5 的逐字翻译） |
| abm_selftest.py | `b2611e8efe7695aad53ccf912a2eb5fbd906d6f461e615e707d1993988ed32f2` | 合成夹具自测（不读真实数据） |

- **封存前自测**：abm_selftest.py 在合成夹具（`../_selftest/run1/`，假 ledger＋真实维度随机场 out_his.nc＋合成源 JSON，零真实数值）上
  全部断言通过（SELFTEST_RESULT.json：统计函数、E57 复现锚、滤链单调与淘汰分解守恒、名册与本文件 §2.5 表逐项一致、DUPLICATE/EQUIVALENT 识别、
  V5、checker 22 格求值与故意不一致逐格抓出、verdict 故障注入 4 类）。真实模式封存门控另行实测（无 .sha256 拒跑）。
- 相关系数主口径 = metric_search.py 的 argsort-秩 spearman（并列按下标序破）；平均秩版同报为敏感性列，不参与判定。
- 候选方向约定：字面"越小越好"，不做方向自适应。
- 运行：amax，`systemd-run --user --scope -p MemoryMax=16G nice -n 19`，OMP/MKL/OPENBLAS 线程=4，本条内串行；
  起批前查 free -g（比 memguard 8% 红线多留 >100G）、monitor/state/active 为空、无 coawstM_yagi_FRESH。

### 2.2 run 集合（全部钉死；E=/data/xinyuan/GOAI_ai4s_env）

- **真值源**：`E/ledger/regraded_v2.jsonl`（err_rms、skill_vs_zero；每 run 一行）。经向 A 的技巧分沿用 e67b 同口径（经向 ledger `hidden.skill_vs_zero` 非空者；经向 ledger 无重复行）。
- **Z58 纬向陡臂**：env2_runs.jsonl 中 valid ∧ ntimes=8640 ∧ bathy=r26steep ∧ run_id∈regraded_v2，按 run_id 去重、账本首次出现序（E57 同式）。
- **Zflat**：同条件 bathy=flat（去重，首次出现序；仅用于 E57 候选正值过滤复现）。
- **Z32 纬向配对**：键=(VISC2,VISC4,AKV_BAK,TNU2) 各 round 6 位（缺省 −1），同键同地形 last-wins，键首次出现序，steep/flat 双全（E57 同式）。
- **M28 / D28**：env2_merid_runs.jsonl＋runs_merid/、env2_diag45_runs.jsonl＋runs_diag45/，同式建配对。**M_truth**：经向陡臂中 hidden.skill_vs_zero 非空者（e67b 同式）。
- **V7 纬向黏性参考**（runs/，ntimes=8640，seed=0，仅 VISC2 旋钮）：0→e2_266404276ec5，50→e2_04ac56d390ce，150→e2_8ece45ca0d8d，
  400→e2_3b79f788a4f1，800→e2_37506f16ae83，1500→e2_ce64784901eb，2747→e2_e6d68386cec3；真值 = regraded_v2.err_rms。
- **荒谬黏性**（runs/）：steep 10000→e2_b82a21ff15fd，steep 30000→e2_9e957e1b688e，flat 30000→e2_710f227af49f。
- **静止线 ST7**：E/e56/runs/bh93_{flat,r26steep}_v{0,50,150,400,800,1500,2747}；静止线误差量 = E56_BH93.json 对应 steep tag 的 `u_max`
  （真值解析为零，伪流幅度即误差；须与 E56_VERDICT.bh93_umax 逐档相等，否则 PIPELINE_SUSPECT）。
- **E60 陡度轴**（仅 L4）：E/e60/runs/rx0{20,44,60,69}_{flat,steep}_v{0,50,150,400,800,1500,2747}，同 (rx0,VISC2) 配对 28 对。

### 2.3 候选与读数

- 候选索引 = E57 复现：keys = Z58∪Zflat 基元键交集排序（metric_search.base_quantities，末帧）；对每个分子 i 先 (i,None)，再 j≠i 且分母在
  Z58/Zflat/Z32 两侧均 |·|≥1e-12；再滤掉 Z58 或 Zflat 上任一读数非有限或 ≤0 者。长度须 = 15376。
- 读数 m(run) = q[num]/q[den]（den=None 时 q[num]）；键缺失、除零、非有限 → NaN（"不可判"），**不插补**。
- **扩展基元**（abm_common.ext_base_quantities）：与 metric_search.base_quantities 同运算序，额外参数 frame（默认 −1）、阈缩放 s（深/浅阈值同乘 s，all 不变）、
  并返回每键有限格点数 N。实现锚：s=1、frame=−1 时与原函数逐键逐位相等（所有被读 run），否则 PIPELINE_SUSPECT。

### 2.4 模块① MR 库：分类标签与 checker 规则

- 分类（写死）：A1/A2/A9 = 按构造零真值的 sound 证伪（依赖平底/静止态伪流为零的**物理构造**，非形式证明）；A3/A4/A7 = 启发式不变性；
  A6 = 等变性；A8 = 单调性；**A5 = 程序性控制，非 MR**（deck p7 同步）。分类是描述性组织，非本体断言。
- 对照对象：E/e44/analysis/KILLBOARD.json（sha256 6687…d92；repo 副本仅 uv·A6 文本串正负号勘误不同，判定字段相同）5 行×10 列=50 格。
- checker 规则（名称与 mr_audit.yaml 一致，全部取自 RULES 原文，数值化方式写死）：
  - `A1_trivalent`：k/n（n 缺省取对应风向配对数；内潮单对 n=1）；Wilson 95% CI（z=1.959964）下界 ≥0.9 → 过；CI 跨 0.9 → 待定；
    上界 <0.9 时点估计 <0.5 → 死、否则 边（RULES['三值化']∘RULES['A1']，对全部 A1 类格统一适用）。
  - `A2_zero_channel`：|平底读数|/|海山典型值| <0.01 → 过；非有限 → 死；否则 边（只执行数值分句；"平底本身无该误差成分"定性分句的格一律 manual）。
  - `A3_boxwidth`：幅变 amp（比值型输入取 max/min−1）；辅助事实"含义变"或 序检验（给出两组同臂读数时 spearman<1）→ 死；否则 amp≥0.20 → 边；否则 过。
  - `A4_phase`：amp = max|相对变化%|；<10 → 过；否则 若存在稳健版且 |稳健版变化%|<10 → 边；否则（辅助事实"无稳健版"）→ 死。
  - `A6_rotate`：A=ρ(读数,技巧)；aok=A≤−0.7，bok=B≥0.9；同过 → 过；A>0（方向反）或 同败 → 死；否则 边。
  - `A7_nameswap`：真名计数 ≥3 且匿名 ≤1 → 死；两版计数相等 → 过；否则 边。
  - `A8_anchor`：带符号 ρ≥0.8 且 p<0.05 → 过；ρ<0.6 → 死；否则 边。
  - `A9_static`：RULES['A9']"判据同 A1/A8"——A1 部分用 `A1_trivalent`（静止线 7 对），A8 部分用 `A8_anchor`（静止线 7 档读数 vs u_max，精确 p）；取最坏（死>待定>边>过）。
- **机器可判格（写死 22 格）**：Pnet_MW{A1,A2,A3,A4,A7,A8}、deep_dc_rms{A1,A4,A6,A7,A8,A9}、temp_d400{A1,A4,A6,A8}、uv_ratio{A1,A3,A4,A6,A7,A8}。
  其余 28 格（A5 全列、R 全列、truth 全行、deep/temp/uv 的 A2 定性分句格、8 个"未"格）为 manual，逐格点名、不入分母。
  **验收门（非预测）**：机器可判格 ≥24；22<24 → verdict 挂 LOW_COVERAGE（封存时已知将挂旗，照挂）。
- 不一致处理：只列 discrepancy 表（行、列、KB 判定、checker 判定、规则、输入指针与值），**不静默修、不改判**。
- MT 不对称（违反即证伪、通过不认证）给"能判死不能认证"盖章；E58 的 32/32 判待定（CI[0.8928,1]）为其定量实例（已知量）。

### 2.5 模块② 变异 kill 矩阵

**基指标**（E57_PARETO.json `front_sample` 顺序）：b1=`u|all|rms / v|s200|p95`；b2=`u|s200|rms / v|s50|p95`；b3=`v|s50|rms / v|s50|p95`；
b4=`u|s50|rms / v|s50|p95`；b5=`u|d1500|p95 / w|d1500|rms`（knee）。**降档 24 = 8 类 × b1–b3**。

**8 类变换**（作用在汇报侧读数或候选定义上，物理零改动）：
1. `unit_scale`：m′=3.7817·m。 2. `mono_norm`：m′=m²。 3. `sign_flip`：m′=−m。
4. `wrong_region`（深浅错置，分子分母同换）：all→s50，d200→s200，d400→s200，d800→s50，d1500→s50，s50→d800，s200→d1500。
5. `wrong_layer`（相邻深度档错位，分子分母同换）：all→d200，d200→d400，d400→d200，d800→d400，d1500→d800，s50→s200，s200→s50。
6. `irrelevant_num`：分子换 `temp|all|mean_abs`，分母保留。
7. `clip_cheat`：m′=min(m, c)，c = 该基指标在 Z58（末帧、标称阈）读数的 np.median（运行期算，全部上下文共用同一 c）。
8. `boxwidth_dep`（求和代替平均的盒宽依赖）：m′=m·N_num/N_ref；N_num=该 run、该阈缩放下分子键的有限格点数，N_ref=Z58 首 run 标称阈的 N_num
   （Z58 全部 run 的标称 N_num 须相同，否则 PIPELINE_SUSPECT）。

**40 个变异体显式名册**（id=M<类号>_b<k>；T=`temp|all|mean_abs`）：

| 类 | b1 | b2 | b3 | b4 | b5 |
|---|---|---|---|---|---|
| M1 unit_scale | 3.7817·b1 | 3.7817·b2 | 3.7817·b3 | 3.7817·b4 | 3.7817·b5 |
| M2 mono_norm | b1² | b2² | b3² | b4² | b5² |
| M3 sign_flip | −b1 | −b2 | −b3 | −b4 | −b5 |
| M4 wrong_region | u\|s50\|rms / v\|d1500\|p95 | u\|d1500\|rms / v\|d800\|p95 | v\|d800\|rms / v\|d800\|p95 | u\|d800\|rms / v\|d800\|p95 | u\|s50\|p95 / w\|s50\|rms |
| M5 wrong_layer | u\|d200\|rms / v\|s50\|p95 | u\|s50\|rms / v\|s200\|p95 | v\|s200\|rms / v\|s200\|p95 | u\|s200\|rms / v\|s200\|p95 | u\|d800\|p95 / w\|d800\|rms |
| M6 irrelevant_num | T / v\|s200\|p95 | T / v\|s50\|p95 | T / v\|s50\|p95 **(DUPLICATE_OF M6_b2)** | T / v\|s50\|p95 **(DUPLICATE_OF M6_b2)** | T / w\|d1500\|rms |
| M7 clip_cheat | min(b1,c1) | min(b2,c2) | min(b3,c3) | min(b4,c4) | min(b5,c5) |
| M8 boxwidth_dep | b1·N/N_ref | b2·N/N_ref | b3·N/N_ref | b4·N/N_ref | b5·N/N_ref |

- **排除规则（机械）**：公式与同类先出现者相同 → DUPLICATE；在全部算子输入上下文（标称、两档阈缩放、倒数第二帧、Z32、M_truth、M28、V7、ST7）
  读数与基指标逐位相同（NaN 位置相同视为相同）→ EQUIVALENT。二者排出主分母，原始分母（40 或 24）版本同报。
- **电池可执行子集** = {A1, A2(仅绝对型), A3′, A4′, A6, A8, A9′}；A5（程序性）、A7（需 LLM）排除。5 把基指标全为比值型、A2 对其全部记"未"——
  **说明书写"7 把中 A2 对全比值基不出判定，有效 6 把"**。操作化（输入含 NaN 即该算子记 未）：
  - **A1**：B = mean_{Z32}[m_flat ≥ m_steep]；≥0.9 过 / <0.5 死 / 其间 边（变异电池用普通阈值；三值化在 n=32 时上界最多判"待定"、永不判过，只作敏感性列）。
  - **A2**（仅 den=None）：|median_{Z32} m_flat| / |median_{Z32} m_steep| <0.01 过；比值非有限 死；否则 边。
  - **A3′ 区域边界扰动**（A3 盒宽的场量代理，与 KILLBOARD A3 的 DOMWIDTH 口径不同，逐处标注）：s∈{0.75,1.25}，
    amp_s = median_{Z58}|m_s/m−1|，ord_s = ρ(m, m_s)；amp=max_s amp_s，ord=min_s ord_s。ord<0.95 → 死；否则 amp≥0.20 → 边；否则 过。
  - **A4′ 帧扰动**：rel = median_{Z58}|m_{−2}/m_{−1}−1|，ord=ρ(m_{−1},m_{−2})。rel<0.10 → 过；rel≥0.10 且 ord≥0.95 → 边；否则 死。
  - **A6 转风向（经向）**：A_m = ρ(m, skill_vs_zero) over M_truth；B_m = mean_{M28}[m_flat ≥ m_steep]；同过（A_m≤−0.7 且 B_m≥0.9）→ 过；
    A_m>0 或 同败 → 死；否则 边。
  - **A8 真值锚**：ρ = ρ(m(V7), err_rms(V7))（带符号，n=7），p = 7! 全置换精确双侧（|ρ_π|≥|ρ|−1e−12 的比例）；ρ≥0.8 且 p<0.05 → 过；ρ<0.6 → 死；否则 边。
  - **A9′ 静止线（RULES['A9'] 原文"判据同 A1/A8"）**：A1 部分 B_s = mean_{ST7}[m(flat_v) ≥ m(steep_v)]（阈值同 A1 普通版）；
    A8 部分 ρ_s = ρ(m(steep_v), u_max(v))（阈值与精确 p 同 A8）；取两部分中已定义者的最坏（死>边>过）；两部分均未定义 → 未。
    注：静止平底场全零，比值型的 A1 部分为 0/0 → 未，故比值型的 A9′ 实际只剩 A8 部分；KILLBOARD 对 uv_ratio·A9 记"未（静止态无真信号可锚）"，
    A9′ 对比值型仍执行 A8 部分（静止线误差量取伪流幅度 u_max）——此为新定标，与 KB 原格口径不同，逐处标注。
- **判定语义（写死）**：给出判定 = 该算子结果 ∈{过,边,死}。
  - **主口径·差分杀死**：killed ⇔ ∃算子 o：v_mut(o)=死 ∧ v_base(o)≠死。**漏网** ⇔ 未被杀 ∧ 给出判定的算子数 ≥3；**UNJUDGEABLE** ⇔ 未被杀 ∧ 给出判定 <3（单列）。
    检出率 = killed / (killed+漏网)（Wilson 95%）；原始分母版 = killed/40（或 24）同报。
  - **敏感性口径·绝对检出**（草稿原义）：detected_abs ⇔ ∃o：v_mut(o)=死；漏网_abs ⇔ 零死 ∧ 判定≥3。同表同报，不参与判分。
  - 5 把基指标自身的电池判定同表公示（它们决定差分口径的"继承"部分）。
- **真实阳性锚 n=2**（§4.1 V3，从源 JSON 按 RULES 复导出，不新跑）：
  (a) `Pnet_MW`：A3 死 ← DOMWIDTH_RESULT.json ratio_vs_84km（max/min=7.24，amp≥0.20）＋辅助事实 judgement.main_branch 以 RESONANCE_CONTROLLED 开头（含义变）；
      A4 死 ← RT2_FIXES.json M2_phase.Pnet_lastframe.rel_change_pct（max|·|=14.1≥10）＋辅助事实 M2_phase 下不存在 Pnet 窗均稳健版键。
  (b) `deep_dc_rms`（**BH93 静止线锚**）：A9 死 ← E56_VERDICT.json:A1_paired_correct=0.0（n=7，Wilson 上界 0.354<0.9 且 <0.5 → 死）。
      `exaggeration=1.6895` 仅作描述，出处为纬向风 sweep（wind_deep800 / wind_err），**不作判死依据、不挂 BH93 名下**。
  另设**电池内锚 V5**：可执行电池代码对绝对型 `u|d800|rms`（metric_search baseline 即 deep_rms_800 口径）必须给出 A1=死 且 A9′=死（已知：baseline paired=0.0；静止平底读数恒 0）。

### 2.6 模块③ Goodhart 覆盖矩阵（描述性，无预测）

- 对象 = KILLBOARD 4 尺×A1–A9 的 13 个死格：Pnet{A1,A3,A4,A7}、deep{A1,A4,A6,A8,A9}、temp{A6}、uv{A2,A6,A7}。
- 失效类型列（写死 6 列）：优化诱发科 = {极值（荒谬黏性/过耗散）, 因果（缩短积分）, 对抗（换平底）, 回归·搜索冠军迁移失效, 回归·排得准跟踪伪流幅度 D}；
  构念缺陷科 = {构念（无优化者也错：BH93/环带功率/分母发散/相位敏感/名义效度）}。逐格分类与理由、证据指针写死在 mr_audit.yaml `goodhart:` 节；
  指针解析失败的格降 manual 并点名。
- 覆盖矩阵 A1–A9 × 6 类型，**只两档**：有实证检出（存在该算子×该类型的死格）/ 不覆盖。
- 已知结构陈述（不下注）："回归·跟踪 D"九项都不覆盖（E66 A⊥ 补过、E67b 证明治法场景依赖）；"因果（缩短积分）"九项死格中无标本。成品如显其他空格照实写。

### 2.7 模块④ 滤链曲线

- 读数：15376 候选（§2.3）在各 run 上的标称读数（metric_search.base_quantities 原函数）。非有限读数 = "未定义"，该步直接淘汰并单独计数。
- **步骤（hack 容限 H；H 主值 0，敏感档 0.01、0.05）**：
  - L0（非退化基线）：Z58 上读数全有限且 std>0。
  - S_zonal：Z32 每对 hack ⇔ m_flat < m_steep·(1−H)。
  - S_rotate：M28 ∪ D28 每对同式。
  - S_absurd：(i) 同键对 (flat30000, steep30000) 同式；(ii) 极值型：对 r∈{steep10000, steep30000}，hack ⇔ m(r) < min_{v∈V7} m(v)·(1−H)
    ——配置有效性公理：VISC2=1e4/3e4 为典型海洋值（1–100 m²/s）的 100–300 倍，属 E34 定义的"物理荒谬量级"，
    奖励该旋钮越过物理量程即为刷分（真值 err_rms 在此处并不变差，见 R9；这正是"真值轴也看不见"的极值型 Goodhart）。
  - S_e60（L4，可选）：E60 28 对同式。
  - 幸存 = 该步无 hack 且无未定义。L1=L0∩S_zonal，L2=L1∩S_rotate，L3=L2∩S_absurd，L4=L3∩S_e60。
- **排法稳健性**：几何序（S_zonal→S_rotate→S_absurd）、单独杀伤力降序、升序（杀伤力 = 该步单独作用于 L0 的淘汰数）三版曲线；
  末级集合与排法无关是集合交的构造性质（§4.3 C2，不作预测）。
- **图上参考线**（已知量）：204（E57 两关门）、444（E66 A⊥ 门）、12（E57 0.90/0.90）；并报三集合在各级的留存数（派生非预测）。
- **定理定位（口径写死）**：Skalse arXiv:2209.13085（本地 038）"全体随机策略上非平凡不可刷对不存在、受限策略集上存在"与本滤链
  "有限配置集有非平凡幸存者、配置集扩张幸存者单调不增"是**结构同型**（对象从奖励函数×策略换成候选尺×配置对，无形式归约）；
  **禁句：「不是我们不够，是数学」及一切把本滤链说成 Skalse 定理推论的表述**。Karwowski arXiv:2310.09144 Corollary 1 只作展望类比。
  滤链单调性数学平凡，只当组织原则；贡献 = 实例化＋测量。
- **管线锚（先于一切滤链读数）**：复算纬向 A、B 与 E57_AB.npz 逐候选最大绝对差（B 须 =0 否则 PIPELINE_SUSPECT；A 同报）。
- **回退（写死）**：读数再生墙钟 >45 分钟、或 M28/D28/荒谬/V7 任一集合读取失败、或经向/45° 配对数 ≠28 → 回退两级（L0＋L1），P4a–P4c 记 NOT_RUN，入 OPEN_PROBLEMS。
  L4 读取失败只记"L4 未跑"，不触发回退。

## 3. 已知量排除清单（一律不得作为真预测标的）

1. E57_PARETO.json：n_both=**204**；threshold_grid["0.90/0.90"]=**12**；frac_A_ge_0p7=0.3155；frac_B_ge_0p9=0.4451；knee=(0.948,1.000)；n_pairs=32；front_sample 5 把的 A/B。
2. E66_PARTIAL.json：n_both_Aperp=**444**。 3. E67B：S_A→经向 88 / →45° 140 / 三向 80。 4. E65：n_runs_steep=58、n_pairs=32、ρ(D,A)=0.9762。
5. KILLBOARD.json：判定分布与 13 死格坐标；以及由 §2.4 规则对其源值的复导出结果（作者撰写 yaml 时已读全部格值——故原 P1 降为 §4.2 已知检查）。
6. E58_TRIVALENT.json：uv 纬向 32/32、CI[0.8928,1] → 待定。
7. E56_VERDICT.json：A1_paired_correct=0.0、bh93_umax/bh93_deep800 序列、rho_bh93=−1.0、exaggeration=1.6895（纬向风 sweep 出处，描述用）。
8. regraded_v2 中 V7 与荒谬黏性 run 的 err_rms/skill_vs_zero（规则输入）。
9. 一切可由 E57_AB.npz/E66_AXES.npz 派生的量：封存后算出标"派生非预测"。

## 4. 不计入命中率的判定项

### 4.1 验证性断言（锚；不过 = PIPELINE_SUSPECT，判分照跑、全体挂旗）
- **V1**：KILLBOARD 4 尺×A1–A9 的死格集合恰为 §2.6 列的 13 格。
- **V2**：复算纬向 B 与 E57_AB.npz 逐候选最大绝对差 = 0（A 差同报）；ext_base_quantities 实现锚逐位相等；E56_BH93 steep u_max 与 E56_VERDICT.bh93_umax 逐档相等。
- **V3**：真实阳性锚 n=2 按 §2.5 从源 JSON 复导出：Pnet_MW A3=死 ∧ A4=死；deep_dc_rms A9=死（静止线 A1 部分）。
- **V4**：204/444/12 由 E57_AB.npz / E66_AXES.npz 重数与源 JSON 精确一致。
- **V5**：电池代码对 `u|d800|rms` 给出 A1=死 ∧ A9′=死。

### 4.2 已知答案检查（作者封存前已读输入；照判照报，不计数）
- **K1**（原 P1）：机器可判 22 格上 checker 与 KILLBOARD 不一致数 = 0。**作者封存时预期不成立（=2）**：temp_d400·A1（32/32 按三值化应为待定，KB 记过）、
  deep_dc_rms·A6（经向 A=−0.99 过、45° B=0.00 败，按"一过一败 边"，KB 记死）。不一致原样上台为"手写判定表与宣示规则的实测缝隙"，不改表。

### 4.3 构造性预期（按构造近乎必真；照判照报，不计数、不进命中率宣传口径）
- **C1**（原 P2a）：`unit_scale` 类全部可判体均漏网（全部可执行算子对正常数缩放不变——秩审计对单调重标度构造性失明，说明书第一页）。
- **C2**：H=0 时三种排法末级幸存集合相同。

## 5. 真预测（11 条，每条单一布尔式；abm_verdict.py 机械判定；被推翻原样保留并上台）

主口径 = §2.5 差分杀死；H=0；降档 24 时按 3 基/类照判并挂 downgraded 旗。"可判体" = 被杀或漏网者（排除 DUPLICATE/EQUIVALENT/UNJUDGEABLE）。

**P2 变异 kill 矩阵（模块②）**
- **P2b**：`mono_norm` 类可判体数 ≥1 且漏网数 = 可判体数（零差分杀死）。
  不确定性来源：平方保序，唯一可致差分杀死的路径是 A4′（基指标 rel∈[≈0.049,0.10) 且 ord<0.95 时平方把 rel 推过 10%）；押陡臂相邻帧序稳定、此路径不触发。
- **P2c**：`sign_flip` 类漏网数 = 0（基指标 A8 过 → 变异 ρ 反号判死；或 A6 A_m 反号判死；或 A1 反转）。
- **P2d**：`boxwidth_dep` 类漏网数 ≥1（同网格陡臂上因子为常数，A3′/A4′/A8 不改序；只有平底侧格点数差异经 A1/A6 的 B 可致杀，押 d1500 类分子不致杀）。
- **P2e**：`irrelevant_num` 类漏网数 = 0（分子近常数 → 读数≈1/分母 → 与伪流/误差反向 → A8 判死）。
- **P2f**：`clip_cheat` 类漏网数 ≥1（截断造并列：A1 并列计"≥"抬高 B，秩算子对并列宽容）。
- **P2g**：`wrong_region` 类漏网数 ≥1（"选错但诚实"的量不在电池设计目标内——盲区显形）。
- **P2h**：`wrong_layer` 类漏网数 ≥1（相邻档错位与基指标近似，同上）。
- **P2i**：主口径总检出率（killed / 可判体）∈ [0.20, 0.60]（Wilson 95% CI 照报；>0.90 反而可疑条款见 §7）。

**P4 滤链曲线（模块④；回退两级则记 NOT_RUN）**
- **P4a**：|L3| ∈ [1, 1537]（≥1 = 有限配置集有非平凡幸存者的定量下注；≤10% = 滤链非平凡地在筛）。
- **P4b**：几何序下 |L1|−|L2| ≥ |L2|−|L3|（转风向一步淘汰 ≥ 荒谬黏性一步淘汰）。
- **P4c**：|S_A ∩ L3| ≤ 122，S_A = E57_AB.npz 上 A≥0.7 ∧ B≥0.9（A=−ρ 约定；须 =204）。

## 6. 降档与放弃条件（写死，触发即自动执行）

1. 模块② **40→24**：9/18 12:00 尚未起跑、或 40 版预计墙钟 >40 分钟 → 降 24（8 类 × b1–b3）。
2. 模块② 弃档：9/18 24:00 仍未起跑 → "已预注册未执行"入 OPEN_PROBLEMS，P2b–P2i 记 NOT_RUN。
3. 模块④ 回退两级：见 §2.7；L4 任何情况下可弃，弃记"未跑"。
4. 模块①③ 无降档；9/18 12:00 未完成即执行失败，如实入 OPEN_PROBLEMS。
5. 降档一经触发不回头改判据、不改子集。

## 7. 报告纪律

1. **不称首次**：一律"据我们检索未见（检索范围：arXiv API＋本地 417 篇全文库，2026-09-17）"；"第一份野外测量"降格"据检索未见的域外实例化"。
2. **近邻主动同框**：Li & Hai arXiv:2607.16646（本地 313，全文已读，2026 同体裁：证伪电池＋变异分析＋盲区点名）**第一顺位亮出**；MetaQuantus（本地 067）、
   Sai 2021（本地 066）、神经元覆盖 MT（Research Square，仅存在性）、Cavallazzi arXiv:2606.06227（本地 048）、Fluri（本地 137）、气候界 ECT（Baker 2015、
   Price-Broncucia 2024，Crossref 存在性）。
3. **MT 文献归属（Kanewala 条款）**：Chen 2018、Liu 2014、Segura 2016、Kanewala & Bieman 2014、Jia & Harman 2011 仅 Crossref 题录核实、本地库无全文——
   **8 类缺陷分类学按"自建分类、借用 MT/变异测试术语（等价变异体、差分杀死）"申报，不冠"Kanewala 分类学"之名**；Segura 式标签同此口径。
4. **Skalse 口径**：只说"结构同型"；禁句"不是我们不够，是数学"；不称证明认证不可能（有限集恰可认证——E69 带适用域合格证）。
5. **A5 非 MR**：deck p7 同步（9/18 材料任务）。
6. **变异体循环性**三重缓解：分类学与名册固定（§2.5）＋预注册（本文件）＋真实缺陷锚 n=2（Pnet_MW；deep_dc_rms/BH93 静止线 A1_paired_correct=0.0）。
7. **漏网 ≠ 电池失败**：单调重标度盲区是秩审计的构造性质；说明书第一页写盲区点名清单。检出率 >90% 反而可疑（变异体太弱），照实讨论。
8. **检出率不外推**：只覆盖 8 类合成缺陷＋2 个真实锚。
9. **新定标申明**：A3′（区域阈缩放代理）、A4′（相邻帧）、A6（仅经向）、A8（纬向 V7 对 regraded err_rms）、A9′（静止线 7 对/7 档）均与 KILLBOARD 原格口径不同，逐处标注，不与原格数字混算。
10. **两档覆盖矩阵**；"对判据自身的 Goodhart"维持降格口径（描述性）。
11. 数字一律脚本算出、挂 JSON 指针；名义 N=15376 与候选相依性同页申明（计数只作描述）。
12. BH93 卡片不得再挂 81%/−8.48→−1.46/1.69× 为静止线读数（均为纬向 sweep）；静止线只引 A1_paired_correct=0.0、bh93_umax 端点降幅。

## 8. 判分、产出与偏差纪律

- 执行顺序：封存 → abm_mr_checker → abm_goodhart_map → abm_chain（V2 管线锚先行）→ abm_mutants → abm_verdict → RESULT_audit_battery_meta.md、AUDIT_BATTERY_MANUAL.md。
- 产出（final/，文件名钉死）：mr_audit.yaml、MR_TAXONOMY.md、ABM_MR_CONSISTENCY.json、ABM_GOODHART_MAP.json、ABM_FILTER_CHAIN.json（＋逐级成员 ABM_FILTER_CHAIN_MASKS.npz）、abm_chain_curve.png、
  ABM_MUTANT_LEDGER.json、ABM_KILL_MATRIX.json、verdict.json、RUN_LOG.md、RESULT_audit_battery_meta.md、AUDIT_BATTERY_MANUAL.md（＋需要时 DEVIATIONS.md、OPEN_PROBLEMS.md）。
- verdict.json：predictions（11 条，{statement,status∈{PASS,FAIL,NOT_RUN,UNJUDGEABLE},value,source}）、tally（只计 11 条）、known_checks（K1）、
  constructive（C1,C2）、anchors（V1–V5）、flags{PIPELINE_SUSPECT,LOW_COVERAGE,downgraded,fallback_two_level}、derived_consistency_checks、input_sha、code_sha、prereg_sha。
- 输入 JSON 缺判定所需字段 → 该条 NOT_RUN 且置 PIPELINE_SUSPECT（管线故障不记为科学负结果）。
- 封存后发现本文件笔误或脚本实现错：不改本文件，记 DEVIATIONS.md（发现时间、影响面、前后 sha）。
