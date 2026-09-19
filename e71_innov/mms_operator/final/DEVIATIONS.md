# DEVIATIONS · mms_operator（封存后发现，封存文件一字未改）

封存：PREREG_mms_operator.md sha256 60865d479350418d88eca135f350f20a9196d5d98464725a03b1a15937eec3f4，2026-09-17T16:03:36+08:00。
执行：e71g_run.sh 2026-09-17T16:03:41→16:03:44（clone 一步运行 DONE；scan、verdict 各一次，未重跑）。

## D1（A2b 记录索引前提写错；本条写于查看任何探索性对拍数字之前，2026-09-17T16:04:55+08:00）

> 【2026-09-17 复算更正】 此历史记录中的设计/时间原点表述已由本文件末尾新条目纠正；原记录保留存证，不作当前口径。

- **现象**：verdict.json 机械判 a2b_status=fail；A2b 四个形状 L∞ 全为 NaN，scale_dev_u/v=0.0，scan.log 报 "invalid value encountered in divide"。
  clone_1step/out_dia.nc 有 3 条记录（ocean_time 相对 DSTART·86400=63082281600 s 为 −5 / +10 / +20 s），不是 PREREG §3 预设的 2 条。
- **根因（源码核实）**：PREREG §3 写「dia 文件无 t0 记录（E56 v0 的 out_dia 6 条 = 8640/1440），故 NDIA=1 时第 0 条记录 = 步 1」。
  该推断把 NDIA=1440 的情形外推到 NDIA=1，是错的：build/work_rest/Build_roms/output.f90 L342-344 的写出条件含特例
  `((iic.ge.ntsDIA).and.(nDIA.eq.1))`，set_diags.f90 L256-264 同样特例（nDIA=1 时 DIAtime=time）。NDIA=1 时 iic=ntstart 也写一条，
  第 0 条是尚未累加的零场（内点 max|u_prsgrd|=0 ⇒ 归一化除零 ⇒ NaN ⇒ 判 fail）。
- **定性**：这是封存前 A2b 管线的记录索引错误，**不是**复刻与 ROMS 场不一致的证据；但按协议，verdict.json 的 a2b_status=fail 原样保留，不改判、不重跑 verdict。
  A2b 本为可选报告项（gating=false），anchor_failed 不受影响（A0/A1/A2/A3 全过）。
- **封存后探索性补充（非预注册、不改判、单独落盘）**：写本条时先把口径定死再算——
  脚本 e71g_posthoc_a2b.py 读取 clone_1step/out_dia.nc 全部 3 条记录，逐条算与 A2b 完全相同的统计量
  （柱偏差归一化形状内点 L∞，u、v；原场 L∞ 与 scale_dev 记录），**主读数 = ocean_time 相对 DSTART 为 +DT=+10 s 的那一条**，
  沿用同一阈值 1e-3 给出「探索性是否 ≤1e-3」，结果写 POSTHOC_A2B.json。任何台面引用必须写「封存后探索性、记录索引修正后」，
  不得写成「A2b 预注册通过」。

## 说明（非偏离，记录）

- MMS_OPERATOR.json 与 verdict.json 的 A2b 字段含 NaN 字面量（Python json 默认 allow_nan）；严格 JSON 解析器需开 allow_nan 或按字符串处理。

## D2 · 2026-09-17 · 封存公式与 D1 时间原点的文字更正

PREREG §5 写 scale_dev=Q′/(DT·R′)，实装为 Q′/R′，后者量纲正确；封存文本多写一个 DT，不改代码/判分。旧 D1 的“DSTART·86400=63082281600”错误：roms.in 的 DSTART=0.0d0，偏移来自 ROMS 时间原点与 ini 时间；相对 −5/+10/+20 s 无误（`../recompute/RC_MMS.json#/posthoc_A2b`）。

复刻保真表述采用“源码逐式翻译加 A2 量级锚 1.134；场级一致性为封存后探索性”。A0/A1/A3 检验力有限；u/v 是对称地形镜像同一量，不算独立旁证。P4/P5 近构造必然（平底和精确参考态都消去指定 tanh 误差源），均标弱赌注；有风险的 P1/P3/P6 为 2 中 1 负，P2 为二阶格式教科书期望。黏性不进算子只用解析论证，自检一致仅证明程序确定性。
