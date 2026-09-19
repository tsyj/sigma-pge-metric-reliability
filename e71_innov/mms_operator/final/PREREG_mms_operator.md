# 预注册 · 解析真值算子级考场（E71G 最小闭环 · mms_operator）

状态：**封存版**（封存时刻以同目录 `PREREG_mms_operator.sha256` 第 2 行 `date -Is` 为准）。
本文件为 2026-09-17 上午草稿经检查意见（1 阻断＋3 重要＋2 一般）逐条修正后的定稿；修正前草稿原样保存在
`final/drafts_pre_review/`（chmod 444，只作审计留痕，不参与任何计算）。封存后一字不改，笔误只记 DEVIATIONS.md。
封存 = 在本目录执行：
```
sha256sum PREREG_mms_operator.md > PREREG_mms_operator.sha256
date -Is >> PREREG_mms_operator.sha256
chmod 444 PREREG_mms_operator.md PREREG_mms_operator.sha256
```
**封存必须早于读取任何留出读数与判分输出**。e71g_scan.py 与 e71g_verdict.py 在文件头做封存门控
（.sha256 缺失、与本文件不匹配、或五个脚本 sha256 与 §7 表不符，即拒绝运行），此纪律由代码硬性保证。

**封存前本条目读取过的全部内容（如实申报）**：
- 源码与编译产物：prsgrd31.h、build/work_rest/Build_roms/{prsgrd.f90, rho_eos.f90, analytical.f90（ana_diag）,
  step3d_uv.f90（诊断耦合段）, set_diags.f90（时间平均因子）}；E56 v0 的 roms.in、run.log（CPP 列表）。
- 网格几何元数据：S1 四档、flat48_noN、r26steep 的维度/h 极值/mask/pm/pn/rx0；out_his.nc 的 h 与网格文件 h 逐位一致
  （内点与全场 max|Δh| 均 0.0）；E56 v0 的 out_dia/out_his/ini 文件变量清单、dtype、ocean_time 轴。
- E56 既有落盘（全部归 §5 验证性断言）：seamount_diag.dat 前 5 行、E56_BH93.json、run_bh93.py（u_max 定义）。
- 自家近邻既有落盘（全部入 §4 已知量清单）：pge_test/ 下 harden_results.json、rest_sweep_results.json、
  offline_N_sweep*.json/offline_N_to100.json/offline_floor_evolution.json（前若干行）、
  pgferr_20260830/{CRITERIA_PGFERR.md, FINDINGS_PGFERR.md, pgferr_core.py 头部}、
  pgferr_frames_20260904/PREREG 头部、analytictruth_20260902/PREREG 头部、dxconverge_20260902/PREREG 头部。
- 文献：本地库 155 Song 1998 L1640-1646；本地库 418 个全文 grep 'manufactured solution'。

**制造场误差、复刻算子在任何预注册输入上的输出：一个数字没有算过。** 审计面申报：起草阶段留下过
`final/__pycache__/e71g_replica.cpython-39.pyc`（2026-09-17 10:44:20，与脚本同一时刻落盘），说明起草时曾
import 冒烟检查该模块；该模块只含函数定义，import 零计算；全树当时无任何扫描产物（无 MMS_OPERATOR.json、无杂散拷贝，
检查人已核）。该 pyc 已于封存前删除（rm -rf final/__pycache__）。修正阶段脚本只做 `bash -n` 与 `ast.parse` 语法检查，以及 §7 表 sha 解析正则对本文件的自检（纯文本，不触任何数据）。

---

## 0. 定位（品牌降格条款，已触发）

按创新升级方案 T3：**9/17 午前未开整案 ⇒ 自动降为最小闭环 = 复刻＋三锚验证＋旋钮判决表**。本预注册即最小闭环。
- **不以 MMS 当头条**。标题词=「解析真值的算子级考场」；Roache 2002 (DOI 10.1115/1.1436090)、
  Salari & Knupp 2000 (SAND2000-1444)、Oberkampf & Trucano 2002（本地 440）只作方法学谱系引用。
- 唯一卖点钉在元层用途：①解析真值算子入审计集 A 线（BH93 真值恒为零的对偶面：这里真值非零且能写在纸上）；
  ②旋钮获得原则性二分（碰算子的 vs 不碰算子的）；③不依赖任何模拟器回应「如果 MITgcm 错了」。
- **主动同框自引（外部先例）**：Song 1998 MWR Fig.6（本地 155 L1642-1644：「The exact pressure gradient force can be
  calculated analytically」，陡地形解析非零 PGF 先例）；Kliem & Pietrzak 1999 (DOI 10.1029/1999JC900188，实验室对照先例)；
  McCalpin 1994 / SM03（本地 005）「规定密度剖面算 PGF 误差」是领域老手艺。
- **主动同框自引（自家先例，§4.5 详列）**：「离线逐字复刻 ROMS PGF 算子＋以 seamount_diag 首步读数标定」是自家
  2026-08-30 Z10（pgferr_20260830，SM03/prsgrd_dnn.h，84/500 km 盒）已有手艺；「离线规定密度场算 PGF 误差」自家 6 月
  offline_N_sweep 管线已有（对 MITgcm oracle 真解）。本条增量只在：prsgrd31 SDJ 分支＋**封存的非零闭式真值**＋
  预注册真预测＋旋钮碰/不碰算子二分的元层用途。
- 「首次」一律不写，改「据我们检索未见」：方案阶段 Crossref 检索（记载于 创新升级/候选与评分.json candidates/6/spec，
  2026-09）未见 σ 坐标 PGF 的 MMS 用例、更未见用于代理指标可靠性元层；2026-09-17 本地文献库 418 个全文
  grep 'manufactured solution' 仅命中 440 Oberkampf 2002，该文 0 处 pressure gradient / σ 坐标。检索词表与日期进报告。

## 1. 冻结的复刻对象（源码走读事实，2026-09-17 逐条核过）

复刻目标 = E56 静止态所用二进制 `coawstM_goai_rest`（run 目录内副本 sha256 前 16 位 `00751585e69ff3e7`，
与 e56/prereg_e56.md 记载一致）的压强梯度算子：

| 事实 | 出处（只读） |
|---|---|
| PGF 方案 = prsgrd31.h 标准密度 Jacobian（SDJ）分支；WJ_GRADP 未定义（编译产物 grep gamma = 0 处）；ATM_PRESS/TIDE_GENERATING_FORCES/WET_DRY/WEC_VF 均未定义 | build/src/ROMS/Nonlinear/prsgrd31.h；build/work_rest/Build_roms/prsgrd.f90 |
| **RHO_SURF 已定义**（run.log L235）；其项 (fac2+fac1·(ρ_i+ρ_{i−1}))·(z_w,N(i)−z_w,N(i−1)) ∝ 表层 z_w 差，ζ≡0 下 z_w,N≡0 逐点恒零，故复刻按 ζ=0 合法略去（复刻数值不受影响） | build/work_rest/Build_roms/prsgrd.f90 L219-222（XI）、L259-261（ETA） |
| EOS = LINEAR_EOS：rho = R0 − R0·Tcoef·(T−T0) − 1000（Scoef=0），单位 kg/m³−1000 | build/work_rest/Build_roms/rho_eos.f90 L217-219 |
| R0=1025, T0=14, Tcoef=1.7e-4, rho0=1025, g=9.81 | e56/runs/bh93_r26steep_v0/roms.in |
| 网格 pge_grid_r26steep.nc：48×48 rho 点，dx=dy=2000 m，h∈[80,3000]，rx0=0.7659，f=5.4e-5，全湿（mask_rho 无 0） | e56 run 目录网格文件 |
| LBC：东西 Per、南北 Clo（全变量）；内点（u/v 阵两水平方向各去最外一圈）只用真实 rho 列/行，不触鬼格交换 | roms.in L184-191 |
| 垂向：Vtransform=2, Vstretching=4, θs=7, θb=2, hc=Tcline=250, N=13；DT=10 s, NDTFAST=20 | roms.in |
| 风应力恒 0（rest 版 analytical.f90 val1=0.0；E56 预注册记载 undef SEAMOUNT_WIND 重编）；VISC2 本臂=0 | build/work_rest/Build_roms/analytical.f90；roms.in L305 |
| 初值 ini_rest_r26steep.nc：temp float64，T=f(z) 逐点生成（z 空间水平等密），u=v=ζ=0 | e56/prereg_e56.md；文件元数据 |
| **seamount_diag.dat 写出序 = tdays, ubarmax, vbarmax, umax, vmax**；各列为**带符号 MAX**（非绝对值）；ubarmax 扫 i=1..Lm+1、j=0..Mm+1 | build/work_rest/Build_roms/analytical.f90 ana_diag L379-408 |
| 第 2 行 = 步 1：ubarmax=1.869474e-3、vbarmax=1.869474e-3、umax=−0、vmax=0；第 3 行 umax=6.833781e-3。自家 Z10 FINDINGS §3 结论：三维列因 nnew 指标滞后一行，步 1 三维值写在第 3 行（本条未独立核实，只用于 A2c 报告项） | e56/runs/bh93_r26steep_v0/seamount_diag.dat；pgferr_20260830/FINDINGS_PGFERR.md §3 |
| 正压耦合：step3d_uv 在步末把三维 u 的柱平均替换为正压模态值；DiaU3wrk(M3pgrd) = DC(i,0)·DiaRU·oHz − Dwrk(M2pgrd)（后项逐柱与 k 无关），故诊断 u_prsgrd 的**柱平均被替换、柱偏差保留**；步 1 为前向 Euler（cff=0.25·dt）；set_diags 平均因子 fac=1/nDIA 为全场常数 | step3d_uv.f90 L281-300（步 1 cff 与诊断累加）、L403-426（耦合）；set_diags.f90 L273-279 |

**复刻公式（写死）**：
- s 层：s_rho(k)=(k−N−0.5)/N (k=1..N)，s_w(k)=(k−N)/N (k=0..N)。
- Vstretching=4（θs>0, θb>0）：Csur=(1−cosh(θs·s))/(cosh(θs)−1)；C=(exp(θb·Csur)−1)/(1−exp(−θb))。
- Vtransform=2，ζ=0：z = h·(hc·s + h·C)/(hc + h)；Hz = z_w(k)−z_w(k−1)。
- prsgrd31 SDJ 逐字翻译（fac1=g/(2ρ0), fac3=g/(4ρ0)）：
  顶层 phix = fac1·(ρ_i−ρ_{i−1})·(z_w,N(i)+z_w,N(i−1)−z_r,N(i)−z_r,N(i−1))（RHO_SURF 项在 ζ≡0 下为零，见上表）；
  向下逐层 phix += fac3·(cff1·cff3 − cff2·cff4)（cff1..4 按源码原式）；
  加速度 a_u(i,j,k) = −phix/Δx，a_v = −phie/Δy（等价于 ru/(0.5(Hz_i+Hz_{i−1})·om_u·on_u)，Δx=Δy=2000 m 均匀）。
- **柱平均口径**（A2/A2b/A2c 用）：Hz_u = 0.5(Hz_i+Hz_{i−1})，⟨a_u⟩ = Σ_k(Hz_u·a_u)/Σ_k Hz_u（Σ_k Hz_u = 0.5(h_i+h_{i−1})，
  即正压耦合的深度平均）；v 向同式。柱偏差 a_u − ⟨a_u⟩。
- **措辞红线**：只说「按 Song 1998 与 prsgrd31.h 源码复刻」，不说「即 ROMS 算子」。等价级 = 源码走读＋
  §5 锚一致性（＋可选 A2b 一步场级对拍）。制造场直接规定 ρ 绕开 EOS，但取值约定同单位（kg/m³−1000）。

## 2. 制造场与误差定义（全部常数现在写死）

**制造密度场**（ROMS rho 单位，kg/m³−1000；y 向均匀）：
```
ρ_m(x,z) = 25.0 − 1.5·tanh((z+250)/100) + 0.05·sin(kx·x)·exp(z/500)，kx = 2π/20000 m⁻¹
```
- tanh 项（跃层在 z0=−250 m、厚度 d=100 m，落在 hc=250 的拉伸区）水平均匀 ⇒ 解析 x 梯度为零，
  它是**纯误差发生器**（σ 面穿越跃层）；sin 项（波长 20 km = 10Δx）提供**非零解析真值**。
- **真值闭式**（无需求积，如实标注为闭式）：
  a_x_true(x,z) = −(g/ρ0)·0.05·kx·cos(kx·x)·500·(1−exp(z/500))；a_y_true ≡ 0。
  量级 max|a_x_true| ≈ 7.5e-5 m/s²（解析式直接给出）。
- ρ 在每列 z_r(i,j,k) 处取值；x 取网格文件 x_rho 第 0 行（S2 解析族取 (i+0.5)Δx）；
  真值在 u 点取 x_u=相邻 rho 点中点、z_u=0.5(z_r(i)+z_r(i−1))（二阶中点约定）。
- **误差**：err = a_num − a_true，只在内点（u/v 阵两水平方向各去掉最外一圈）。
  范数：E_L2 = sqrt(Σw·err²/Σw)，w=0.5(Hz_i+Hz_{i−1})·ΔxΔy（体积权）；E_L∞ = max|err|。
  u 向（真值非零）主用 E_L2；v 向（真值恒零，纯伪梯度）主用 E_L∞。全湿（封存前已核所有用到网格 mask 无 0）；
  若 mask 有陆点则排除并记 n_land。

## 3. 扫描设计与运行口径

- **S1 四档陡度**（42×42、dx=2000、hmax=3000 同族，/data/xinyuan/zpg_roms_dev/pge_test/ 只读）：
  smooth(rx0=0.1500) → steep(0.4442) → rx069(0.6940) → harsh(0.9360)。rx0 = max|Δh|/(2h̄)（双向），
  2026-09-17 实测，档序现在钉死。r26steep(48×48, 0.7659) 与 flat48_noN(0.0000，h≡3000 逐位均匀) 单列（锚与旋钮表用）。
- **S2 同步加密（解析高斯族，脚本内构造）**：域 96×96 km，H0=3000、hmin=80，
  h = 3000 − 2920·exp(−r²/L²)；光滑成员 L=20 km、陡成员 L=4 km；
  三档 (Δx, N)=(2000,13)→(1000,26)→(500,52)（横竖同步减半，θs/θb/hc 不变）。
  p̂_12 = log2(E_L2(48)/E_L2(96))，p̂_23 = log2(E_L2(96)/E_L2(192))，u 向。rx0 由脚本实测记录。
  **口径申明**：p̂ 是 (Δx,Δσ) 同步减半的观测阶，不宣称单轴收敛。
- **S3 旋钮判决表**（r26steep×制造场）：{黏性、缩短积分、平底替换、地形平滑、参考态扣除、加密网格}
  × {是否进算子（源码走读）、算子误差变化（本扫描）、可见读数变化（既有 E56 落盘，指针见 §5）}。
  <1e-12 记「不碰误差源」。参考态扣除 = 逐点减去 25.0−1.5·tanh((z_r+250)/100)（算子对 ρ 线性）。
  黏性与缩短积分不是算子输入：以解析论证记 0，另做管线自检（同输入两次调用逐位一致）入 JSON，不计入真预测。
- **运行**：全部 amax，经 `e71g_run.sh` 串行：安全三查（monitor/state/active 为空；`pgrep -f coawstM_yagi_FRESH` 为空；
  `LC_ALL=C free -g` 可用内存 > 总量×8% + 100G）→ 可选 A2b → scan → verdict；每个计算
  `systemd-run --user --scope -p MemoryMax=16G nice -n 19 env OMP_NUM_THREADS=4 …`；纯 numpy，预计墙钟 <5 min；
  不碰 e70/、runs*、e56（只读）；新文件只写本 final/。
- **可选 A2b 一步验证运行**（唯一新算例，允许项）：`e71g_1step_clone.sh` 以 `cp -rL` 克隆 e56/runs/bh93_r26steep_v0 的
  {coawstM_goai_rest, pge_grid_r26steep.nc, ini_rest_r26steep.nc, roms.in} 至 final/clone_1step/，改 NTIMES=2、NDIA=1、NHIS=1、
  Dout(M3*) 全关后只开 Dout(M3pgrd)，systemd-run 16G 内跑（秒级）。dia 文件无 t0 记录（E56 v0 的 out_dia 6 条 = 8640/1440），
  故 NDIA=1 时**第 0 条记录 = 步 1**。不跑或未 DONE 不扣分（verdict 记 not_run / error）；若克隆/运行超 20 分钟即放弃并如实申报。

## 4. 已知量排除清单（封存时已在盘上；只能当验证性断言或近邻同框，不得作真预测标的）

1. E56_BH93.json 全部 14 条读数（陡臂日 1 三维 |u|max（his 末记录、绝对值、cm/s）：99.7174→18.7918，VISC2 0→2747，
   比值 5.31×；平底全零）；E56_VERDICT.json（含 wind_skill 列）。
2. e56/runs/*/seamount_diag.dat 全部内容（陡臂**步 1 ubarmax**（第 2 行第 2 列，正压深度平均量）：
   v0=1.869474e-3 … v2747=1.802511e-3 m/s，七档极差 ≈3.7%；v0 第 3 行第 4 列 umax=6.833781e-3）。
3. 网格几何与 rx0 实测值（§3 已列）；出 his/dia 文件的 Cs_r、维度、时间轴、dtype。
4. 创新升级方案引用的一切既有数字。**62× 不用**：出自初赛图 3(c)（VISC2→3e4 同参数配对中位，
   scripts/fig_llm.py 口径），与本条目 E56 七档口径不同；如台上需要，须按 fig_llm.py 复算并单独注明口径，
   与本条目数字不同框混用。方案所写「日 1 量级 99.53」与 E56_BH93.json 实值 99.7174 不符，本条一律用 JSON 指针值。
5. **自家 pge_test 既有落盘（同网格族；口径与本条不同，但同方向，被翻出即须能答）**：
   - `harden_results.json` H1：**运行级**伪流 DJ 均方根（cm/s）随 rx 0.2/0.44/0.6/0.69 = 1.25/7.95/10.44/8.55
     （**高 rx 段非单调**）；WJ 同扫 5.04/9.08/14.84/19.55。H4：强涡（A=0.8, δ=25）隔离，海山 |DJ−MEO| 11.25 vs 平底 1.04，
     比 10.79（运行级、不同量）。H6：np1/np4 一致性。
   - `rest_sweep_results.json`：**运行级**，跃层厚度 δ=200/100/50/25 下 DJ vs MEO 伪流与 reduction 35.8%/78.9%/94.0%/…。
   - `offline_N_sweep*.json`、`offline_N_to100.json`、`offline_floor_evolution.json`：**离线** DJ（自写 dj_accel，非 prsgrd31
     逐字）力级误差对 **MITgcm oracle 真解**（truePGF=9.036e-6），仅**垂向** N=10→100 加密，DJpct 55.7%→29.4%→26.6%→…→25.9%
     （N≥30 饱和）；态为涡旋场，非解析真值。
   - `pgferr_20260830`（Z10，已盖章）：**离线逐字复刻 SM03（prsgrd_dnn.h）＋ seamount_diag 首步标定**（G1a 三维最大 −0.17%、
     三维恒等式 dt·max(a−⟨a⟩柱)+ubar₁ᵐᵃˣ 闭合 2.5 ppm、正压快调整因子 0.9331）；**参考态扣除算子误差比** R24 均方根 9.13/9.01、
     逐点最大 64.8/62.4、深度平均 3.64/3.59；静止态真值为零、参考态为 256 段拟合。`pgferr_frames_20260904`：其逐帧扩展（只读 PREREG 头）。
   - `analytictruth_20260902`：内潮线性转换率解析真值（Bell/LSY 闭式）对**运行**的对表；`dxconverge_20260902`：内潮远场功率
     z/σ 比随 dx 4→2→1 km（运行级）。二者对象均非 PGF 算子误差。
   以上与本条 P1–P6 的**具体数值**无重叠（对象/范数/场/真值均不同；E58/E65/E66/E67 四账本经检查人核无重叠），
   但方向上：H1 与 P1/P6 相关（且为反例证据）、Z10 与 P5 同方向、offline_N_sweep/dxconverge 与 P2/P3 相关、E56 平底全零与 P4 同方向。

## 5. 验证性断言（封存时已知答案或解析恒等；判定锚不过 = 复刻存疑，P 组照判但全体挂 anchor_failed 旗）

判定锚（gating，入 anchor_failed）：A0、A1、A2、A3。报告项（不入 anchor_failed）：A2c、A2b。

- **A0 纵坐标锚**：复刻 Cs_r（V4 公式）对 out_his.nc 的 Cs_r（r26steep v0），max|Δ| ≤ 1e-10。
- **A1 平底零锚**：flat48 网格＋水平等密 ρ(z)（制造场 ε=0 项）⇒ 复刻算子输出 max|a_u| 与 max|a_v| **恒等于 0.0**
  （逐位零；对照：E56 平底 7/7 条日 1 u_max=0.0，指针 E56_BH93.json）。
- **A2 陡臂首步锚（钦定锚，深度平均口径）**：输入 = ini_rest_r26steep.nc 的 temp 经线性 EOS→ρ，r26steep 网格，ζ=0。
  判定量 ratio = DT·max_内点|⟨a_u⟩| / ubarmax_step1，其中 ⟨a_u⟩ 为 §1 柱平均口径、内点为 u 阵 j,i 各去最外一圈、
  ubarmax_step1 = **1.869474e-3 m/s**（e56/runs/bh93_r26steep_v0/seamount_diag.dat 第 2 行第 2 列 = 步 1 ubarmax，
  analytical.f90 ana_diag 写出序：tdays, ubarmax, vbarmax, umax, vmax）。**判据：ratio ∈ [0.5, 2.0]**，只用 u 向。
  带宽因子 2 的理由：ubar(knew) 为 NDTFAST=20 个正压子步（含幂律滤波延伸）之末的瞬时值，含自由面快调整
  （Z10 在 SM03/dt=30 s 下实测调整因子 0.9331，本臂 DT=10 s 未知），锚检验的是量级等价，不是逐位等价。
  取绝对值最大（对朝向稳健）；ana_diag 为带符号 MAX，带符号值并列记录不判。
  **同步落盘备审（不判）**：带符号 DT·max⟨a_u⟩、v 向 DT·max|⟨a_v⟩| 与带符号值、逐点 DT·max_内点|a_u|、DT·max_内点|a_v|、
  全阵逐点 DT·max|a_u|、逐点口径比值 ratio_pointwise_record。
- **A2c（报告项，Z10 式三维括号）**：X = DT·max_内点(a_u − ⟨a_u⟩)（带符号），U = ubarmax_step1，M = 第 3 行第 4 列 umax
  （6.833781e-3，依 Z10 结论为步 1 三维值）。记录 M 是否 ∈ [0.95·X, 1.05·(X+U)] 及 (M−(X+U))/M。依据：步 1 逐点
  u₁ = DT·(a−⟨a⟩柱)·h/(h+ζ) + ubar_avg(柱)。括号假设 argmax 处 0 ≤ ubar_avg ≤ U，且 ubar_avg（DU_avg1 口径）≠ ubar(knew)，
  故只作报告、不判、不入 anchor_failed。
- **A3 黏性首步近不变（纯已知数据断言）**：七档陡臂**步 1 ubarmax**（第 2 行第 2 列）max/min − 1 ≤ 0.04
  （脚本从 7 个 diag 文件机械复算入 JSON），而日 1 三维 |u|max 比值 = 5.31×（同框、不判）——「首步正压量几乎不动、
  日 1 三维量大动」的经验楔子已在盘上。**两者口径不同（正压 vs 三维；带符号 MAX vs 绝对值最大；步 1 vs 日 1），不混称。**
  同步记录（不判）：七档第 3 行第 4 列三维 umax 列表及其极差。
- **A2b（可选报告项，仅当 §3 一步运行 DONE）**：Q = clone_1step/out_dia.nc 的 u_prsgrd 第 0 条（= 步 1），
  Q′ = Q − ⟨Q⟩（柱平均用复刻的 ζ=0 层厚 Hz_u），R′ = a_u − ⟨a_u⟩（A2 同一输入）。
  判据：内点归一化形状 L∞ ‖Q′/max|Q′| − R′/max|R′|‖∞ ≤ **1e-3**，u、v 两向均需。
  用柱偏差而非原场的理由：§1 表末条——诊断 u_prsgrd 的柱平均已被正压耦合替换（原场形状对拍不成立，原场 L∞ 仅记录）。
  阈值 1e-3 的理由：Hz_new/Hz_old = 1+ζ/h 逐柱近常数，步 1 ζ/h 量级 ~ ubar·DT/Δx ~ 1e-5，加 float 输出精度，留 ≥10× 余量。
  同时记录 Q′/(DT·R′) 的幅值比 scale_dev（不判）。A2b 不过单列 a2b_status=fail，不入 anchor_failed。

## 6. 真预测（6 条，每条单一布尔式；数值今日不存在于任何角落；e71g_verdict.py 机械判定，人不改判；
被推翻原样保留并上台）

- **P1 陡度单调（u 向）**：S1 四档 E_L2^u 严格递增：E(smooth) < E(steep) < E(rx069) < E(harsh)。
  反向条款：不中 ⇒ 「rx0 不是算子误差的单一控制变量」，判决表照登实测序。
  在盘证据（§4.5）：H1 **运行级** DJ 伪流在 rx 0.60→0.69 由 10.44 降到 8.55 cm/s，运行级并非单调——算子级单调是真赌注。
- **P2 光滑收敛阶**：S2 光滑成员 p̂_23 ∈ [1.5, 2.5]。
  反向条款：p̂_23 < 1.5 ⇒ 该方案在此拉伸下未达设计阶，如实登；> 2.5 ⇒ 超收敛旗，查后登。
  近邻（§4.5）：offline_N_sweep 仅垂向加密、对 MITgcm oracle，N≥30 误差饱和——与同步加密、解析真值不同口径。
- **P3 陡度阶退化（粗对，考场工作分辨率）**：p̂_12(陡成员) ≤ p̂_12(光滑成员) − 0.3。
- **P4 平底替换比**：E_L2^u(flat48) / E_L2^u(r26steep) ≤ 0.2（同一制造场）。
- **P5 参考态扣除（真修复解析可见）**：E_L2^u(r26steep, ρ_m−ρ_ref(z)) / E_L2^u(r26steep, ρ_m) ≤ 0.5。
  如实标注：方向已有自家 Z10 先例（SM03、拟合参考态、真值零，R24 均方根比 9.13×）；本条差异 = SDJ、非零闭式真值、
  解析精确参考态。故 P5 是弱赌注，不作亮点宣称。
- **P6 伪梯度陡度单调（v 向，真值恒零）**：S1 四档 E_L∞^v 严格递增（同 P1 档序）。
  反向条款同 P1；H1 高 rx 段运行级非单调同样适用为在盘证据。

## 7. 判分与产出（文件名现在钉死）

| 文件（final/） | sha256 | 说明 |
|---|---|---|
| e71g_replica.py | `76cbac75a120eaca9c55f96ffa976f13dc151f27b4baef36359da58d98442e44` | set_depth V2/S4＋线性 EOS＋prsgrd31 SDJ 逐字翻译＋柱平均（纯函数库） |
| e71g_scan.py | `f73c167bedebc5d33072616cbe3a369f826704dbc541ced4341e9e5cc2ded472` | 封存门控→S0 锚＋S1/S2/S3 扫描→MMS_OPERATOR.json＋fig_mms_operator.png |
| e71g_verdict.py | `6a1591b2f4c1b2367d9abeecc7a75b8389f496534a86bd024096895ad6ace34a` | 封存门控→机械判分→verdict.json＋knob_table.md |
| e71g_1step_clone.sh | `c4c63d4ebe0e3f58932f2bfae2883cdc4a75887f6690aff1665eabb4ce5194e1` | 可选 A2b 克隆一步运行（不跑不扣分） |
| e71g_run.sh | `1558ec376cfc8119417c7b3e203a9cd03b1372bb403a5019de854c451e626353` | 安全三查＋串行执行 clone→scan→verdict |

封存流程：脚本终版→sha256 填上表→再封存本文件。封存后脚本一并不改（scan/verdict 运行期核对上表，不符即拒跑；
各脚本 sha 落入结果 JSON 可核）。

**MMS_OPERATOR.json 顶层键**：meta{date, code_sha, prereg_sha256, numpy, netCDF4, notes}、anchors{A0, A1, A2, A2c, A3, A2b}、
S1_tiers{smooth, steep, rx069, harsh}、S2_refine{smooth, steep}、S3_knobs。

**verdict.json 顶层字段（与 e71g_verdict.py 逐字一致）**：
`date`、`prereg_sha256`、`code_sha`（五脚本 → 完整 sha256）、`code_sha_match_scan`（与 MMS_OPERATOR.json meta.code_sha 是否一致）、
`scan_meta`、`anchors[]`（每条 `id`/`statement`/`values`/`gating`/`anchor_pass`；未跑或出错为 null）、`anchor_failed`
（gating 锚任一 false）、`a2b_status`（not_run/error/pass/fail）、`predictions[]`（每条 `id`/`statement`/`values`/`prediction_pass`）、
`n_pass`、`n_total`、`open_problems`。另出 knob_table.md（机械渲染）。图表均描述性，不参与判分。

## 8. 报告纪律（说过头风险逐条落地）

1. **算子误差 ≠ 演化伪流**（隔着响应函数）：只说「解析已知的误差源动了/没动」，不说「证明运行层改善
   全是假象」。A3 的间距（步 1 ubarmax 七档极差 ≤4% vs 日 1 三维 |u|max 5.31×）是响应函数厚度的经验楔子，同框展示，
   **但须注明首步为正压深度平均量（diag 第 2 列）、日 1 为三维绝对值最大（his），两口径不同框混称**。
2. 复刻等价级 = 源码走读＋锚一致性（＋A2b 若过）；「按 Song 1998/prsgrd31.h 复刻」，永不写「即 ROMS 算子」。
3. 真值来源如实标注 = 闭式（本场型无求积；若改场型需求积，标注精度、不冒充闭式）。
4. S1 n=4 为描述性；P1/P6 是序判断，不做相关系数显著性宣称。
5. 「误差范数随陡度解析曲线 vs 运行伪流 n=4 对照」需 4 档静止态新算例——最小闭环不做，
   记 OPEN_PROBLEMS（已预注册未执行），不以 S1 冒充；H1 运行级读数只作在盘近邻引用，不与 S1 拼成对照。
6. 加密口径 = (Δx,Δσ) 同步减半（§3）；不宣称单轴收敛阶。
7. 62× 处置见 §4.4。黏性可见读数一律用 E56 口径（5.31×，JSON 指针）。
8. 旋钮判决表中「缩短积分/黏性 = 0 变化」是解析论证（输入不含该旋钮）＋管线自检，不算发现、不计预测。
9. 近邻主动同框：外部——Song 1998 Fig.6、KP99、McCalpin 1994/SM03；自家——Z10（离线复刻＋diag 首步标定＋参考态扣除
   算子误差比，§4.5）、offline_N_sweep（离线规定密度场算 PGF 误差对 oracle 真解）为 6–8 月已有手艺，报告近邻页须同框标注，
   增量只在「SDJ 分支＋封存非零闭式真值＋预注册协议＋旋钮二分元层用途」。跨域指标审计体裁先例（医学影像 Reinke/Maier-Hein、
   NLG Sai、RL Shihab）主报告已同框，本条沿用，不另立「独特性」宣称。

## 9. 明确不做也不承诺

全模型 MMS（动量方程加源项、重编译、时间推进收敛研究）——3 天不可行且触「换格式=换对象」红线；
三风向对照；4 档陡度静止态新算例（见 §8.5）；把 p̂ 曲线并入 15376 候选空间（独立展示）。

—— 封存版完。
