# DEVIATIONS · multienv_metrology final

## D1 · 2026-09-17T14:33+08:00 · e71f_axes45.py 封存后修一处 TypeError（新增元数据仪表的缺陷）
- 现象：封存（14:30:56+08:00）后首跑，第 70 行 labeled_varying_knobs 统计对字符串型 action 值调用 round() 抛
  TypeError（该仪表为落实检查意见今晨新增，试点从未跑过此路径）。崩溃发生在读取 env2_diag45_runs.jsonl 之后、
  任何轴/结果落盘之前；无任何判分量已产生。
- 修改内容：仅该统计的取值处理（数值 round(·,6)，非数值取 str），axes() 配方与全部判据零改动。
- sha256：PREREG §2 表冻结值 076f9a30ae81e8827f25f5e25291872ee7248b6bca79bf07f7a29dd4144bf4f2 →
  修后 97f83046928d8089e566c1eed7e179688d18267a9a4ce71746dbe885ea2b581b（E71_FINAL_RESULTS.json 的 code_sha.axes 将与 §2 表不一致，以本条为准）。
- 影响面：labeled_varying_knobs 为 §7.1 限定句的核验元数据，不进入任何 P 判据；封存的 PREREG 一字未改。

## D2 · 2026-09-17T14:36+08:00 · §7.1 限定句按落盘改述（预注册预案触发，非笔误）

> 【2026-09-17 复算更正】 此历史记录中的设计/时间原点表述已由本文件末尾新条目纠正；原记录保留存证，不作当前口径。
- 落盘（E71_FINAL_AXES_META.json → diag45.labeled_varying_knobs）：45° 带标签臂 n=22 中
  VISC2/VISC4/TNU2 各 8 个取值、AKV_BAK 2 个取值——**不是**"与经向同为 VISC2 单旋钮扫描族"。
- 处理：按封存 §7.1 预案改述限定句为——"经向带标签臂 n=22 为 VISC2 单旋钮扫描；45° 带标签臂 n=22 为
  多旋钮（VISC2/VISC4/TNU2×8 值、AKV_BAK×2 值）变化设计；相关级高收敛部分是受控扫描设计的产物；
  k 与 G 的一切结论限定在本强迫场景族（风向×黏性/扩散旋钮扫描）内。"图注与台词一律用改述版。
- 影响面：仅报告表述；不进任何 P 判据。45° 臂旋钮多样性高于经向，单旋钮人工设计带来的收敛高估风险
  在 45° 对上反而更小（此句为描述，不作为发现卖）。

## D3 · 2026-09-17 · 撤回 D2 的错误更正；四旋钮设计事实

上面 D2 中“经向为 VISC2 单旋钮、45° 多样性更高”的旧说法错误，自本记录起失效。经向与 45° 是同一批 **22 个 run 的四旋钮单变扫描**（VISC2 7、VISC4 7、TNU2 7、AKV_BAK 1），run_id 与 action 逐一相同；各旋钮取值数不等于臂数。依据 `../recompute/RC_LABELED_DESIGN.json` 的 same_run_ids/same_actions，以及 shortcut 的 `RC2_RESULTS.json#/labeled45_composition`。k/G 与跨向结果均限本受控强迫场景族，不再比较两域旋钮多样性。PREREG §7.1 不改；E71_FINAL_RESULTS.json 的 M2_gtheory3.caveat 为旧原文，不再引用。只改呈现脚本和另名 FIG1–3，不改数据。

## D4 · 2026-09-17 · P4b 排序依赖、S1 已知答案、时间线

原“敏感性翻转 0 条”不成立：`RC_from_final_npz.json#/flips` 为 ['P4b']，argsort 下 B 占比 0.8121 < A 0.9193；G 模块实用 mergesort。S1 mergesort=0.9236（倒序候选后 0.9422），argsort=0.7775、k*=2（`RC_S1_S2.json`）。S1 相关均值在 E60_VERDICT 9/03 已知，改为验证性断言。A 占比 0.9193 等于三对 Spearman 均值，G(k) 为 Spearman–Brown 形式；P4a 不构成独立证据，P1a/P2b/P2c/P4a 高度相关、P5c=80−P5b 的 1。

准确时间线为 axes 脚本 14:31:52、npz 14:32:15、DEVIATIONS 14:32:45，旧 D1 标题 14:33 为约记，不能倒置因果顺序。头条塌 0.573 限纬向–45°；经向–45° 扣 D 后仍 0.684、只塌 0.266；FIG2 第三层为已知派生。P3a 与设计/标签来源混杂，不归因于风向角度；P5d 的 79 把为 temp/temp 13 + 流速比值 66，无 temp/非 temp 混合比值。判分原样保留，不重跑。
