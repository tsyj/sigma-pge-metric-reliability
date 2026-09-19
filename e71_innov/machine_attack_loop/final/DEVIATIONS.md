# DEVIATIONS · machine_attack_loop

## D1 · 2026-09-17 · 复算发现 loader 真值字段错误（严重）

冻结 `audit_replay_final.py` L151 读取 `e.get("hidden_grade")`；真值实际位于轨迹文件顶层 `hidden_grades[i].hidden`，run_id 位于 `trace[i]`。因此冻结 AUDIT_VS_MACHINE.json 的 159 条留出记录 hidden_score/run_id 全空。独立复算 V3 故意忽略 hidden_grades 可复现错误数字，V0 按顶层字段读取给出以下更正。

| 项目 | 冻结输出（保留存证） | 复算更正 |
|---|---|---|
| LB=136 的 T1 构成 | 90 FAKE_OFFTASK + 46 UNGRADABLE | 90 FAKE_OFFTASK + 46 REAL |
| 全集 T1 | REAL 0 / FAKE_OFFTASK 95 / FAKE_SHORT 12 / FAKE_TRUTH 0 / UNGRADABLE 52 | REAL 51 / FAKE_OFFTASK 95 / FAKE_SHORT 12 / FAKE_TRUTH 1 / UNGRADABLE 0 |
| P6 | 0/0=NA，REFUTED | 0/46=0.000，Wilson95 [0,0.077]，低于 [0.10,0.45]，仍 REFUTED |

46 条 REAL 是阻尼类动作（45 条 @25920、1 条 @8640），R3 全部 NOT_AUDITABLE（no_flat_pair 36、no_flat_ref 10）。没误伤是因为没判；REAL 只由 err 族真值判得。T2 全集/LB 的 NA 52/46 碰巧未变，因为这批 run_id 在 regraded_v2 中无匹配。P1/P2/P3/P4/P5b 不受影响，P7 的短积分计数也不变；删除以 P7 为依据的“loader 不掉链子”解读。P1 是标签与 R1 同式的构造性检查（90 条仅 64 种配置、16 段轨迹，Wilson 区间偏窄），P2 空洞成立，P5a/P5b 是样本内校准。

依据：`../recompute/RECOMPUTE.json` → `V0_primary_spec(zero-default,tiers_all_nt,T1=file hidden_grades)` 的 predictions/summary，以及 V3 对照。冻结 verdict.json `/predictions/P6/numbers`、AUDIT_VS_MACHINE.json 的 overall/by_condition/by_model/by_stratum 同类 T1 数字不再作材料依据；逐层更正以复算记录为准，不覆盖判分产物。

## D2 · 2026-09-17 · 缺省旋钮与封存证据限定

文件基础配置 VISC2=50、TNU2=50；不能把冻结 loader 的缺省 0 写成文件默认值。复算 `V4_file-default_knob_convention` 六个判定不变，P5a p=0.0179（样本内校准）。`.pyc` 创建早于封存 31 秒，import 不读数据；`.sha256` 本身不是 444，应与正文/脚本区分。以上为既有复算转录，本轮不改 loader、不重跑任何封存判分。
