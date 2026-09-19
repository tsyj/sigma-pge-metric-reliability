# OPEN_PROBLEMS（machine_attack_loop，2026-09-17 立卷；不补跑）

1. **25920 层平底默认参照整层缺失**：纬向账本中 flat+默认旋钮参照只存在于 ntimes=8640
   （指针：`../PILOT_AUDIT_VS_MACHINE.json` → `summary.flat_pair_grid_sizes.flat_default_ref_ntimes`）。
   ⇒ R3 平底配对门对留出集主力时长 25920 按构造不可判。这是协议数据覆盖缺口的真实代价，
   如实记录并带上台；**不以补跑消除**——补跑会破坏"存档回审"（协议建成前的轨迹、建成后的账本，
   均封闭不动）的证据性质。
2. **R3 flat 侧中位数比较未做三档敏感性**：flat 配对样本构成异质（n 不一），本轮只对
   (r26steep, nt) 基线做 {min, median, max} 三档；flat 侧作为已知局限记录。
3. **T2 @25920 基线可能缺失**：regraded_v2 覆盖 65 行；缺失时 T2 记 NA_not_regraded，
   不回退硬判、不用 T1 顶替 T2 口径。
4. **manifest 189→188**：28 段轨迹约 189 个带真实读数唯一动作中，1 个 run 目录缺失
   （09-17 盘点），如实标注，不补跑、不插值。
