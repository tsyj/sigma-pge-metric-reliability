# DEVIATIONS · audit_battery_meta（封存后记录；PREREG 与封存脚本均未改动）

封存：PREREG_audit_battery_meta.md sha256 7b641565f778ba909f6cff4583d8b7a8be896e59561e15b07a54fc3ce79679d9，2026-09-17T17:16:04+08:00。
封存后复核（2026-09-17 17:2x）：PREREG 与 §2.1 表中 8 个文件 sha256 全部与封存记录一致。

| # | 发现时间 | 内容 | 影响面 |
|---|---|---|---|
| D1 | 2026-09-17T17:18 | 封存后新增非预注册脚本 abm_posthoc_ties.py（sha256 69c5accc…b527）：把秩算子换成平均秩重跑模块②，产出 ABM_POSTHOC_TIES.json 与 posthoc_avgrank/ | 探索性；不改 verdict.json、不进计数；动机是核查 P2f 被推翻是否为 argsort 并列破法伪迹（结论：否，仅 M7_b2 多一个杀手） |
| D2 | 2026-09-17T17:19 | 封存后新增 abm_derived.py（sha256 444fcc49…cfed）：从已落盘产出与 E57_AB/E66_AXES 计派生描述量 → ABM_DERIVED.json | 描述性；不改判 |
| D3 | 2026-09-17T17:2x | 封存后新增 abm_fig_chain.py（sha256 94cb8674…0e93）→ abm_chain_curve_v2.png；原 abm_chain_curve.png（封存脚本产出）为诊断图，symlog 轴含负区间，不宜上台 | 作图；不读新读数 |
| D4 | 2026-09-17T17:16 | 脚本 import 在 final/ 生成 `__pycache__/` | 无 |
| D5 | 2026-09-17T17:16 | MR_TAXONOMY.md（封存脚本生成）A2 行的"期望关系"含竖线，Markdown 表错列 | 外观；说明书手工给出正确写法；封存脚本不改 |
| D6 | — | PREREG §0 写"第 1 批 9/17 晚"，实际 17:16 起跑 | 无（未触发任何降档条件） |

无规则层偏差；无降档、无回退、无弃档。
