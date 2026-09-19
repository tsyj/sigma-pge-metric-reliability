# RUN_LOG · audit_battery_meta

环境：amax；python /home/xinyuan/anaconda3/envs/numpy1/bin/python（numpy 2.0.2）；每步 `systemd-run --user --scope -p MemoryMax=16G nice -n 19`，OMP/MKL/OPENBLAS=4，串行。
起批前检查（2026-09-17T16:43 与 17:16）：free 可用 476G（memguard 8% 红线 ≈40G，余量 >100G）；monitor/state/active 为空；无 coawstM_yagi_FRESH 进程；未用 8890 端口；未触 e70。

| 时间（+08:00） | 步骤 | 结果 |
|---|---|---|
| 09:55 | 草稿 v1（另一代理）→ 存 ../_draft_history/ | — |
| 16:43–17:13 | 修订 PREREG v2、mr_audit.yaml、8 个脚本 | 只读已印出数字/源码/ledger 结构/nc 头信息 |
| 17:13–17:14 | abm_selftest.py 合成夹具（../_selftest/run1/） | passed=true，0 失败 |
| 17:14 | 真实模式 5 脚本无 .sha256 试跑 | 全部 rc=1 拒跑 |
| 17:15 | 回填 §2.1 sha 表；本机与 amax 逐文件 sha 一致 | — |
| **17:16:04** | **封存** sha256 7b641565…79d9，chmod 444 | — |
| 17:16:13 | abm_mr_checker.py | 22/22 求值，n_disagree=2，真实锚全 true |
| 17:16:14 | abm_goodhart_map.py | 13 死格一致；空列 causal、regression_D |
| 17:16:20–28 | abm_chain.py | V2 ΔB=ΔA=0；L0..L4 = 15344/5514/5035/4916/4624；S_A∩L3=56；无回退 |
| 17:16:38–44 | abm_mutants.py（40 版） | 杀 20 漏 17 排除 3；率 0.541；V5 true；实现锚 true |
| 17:16:58 | abm_verdict.py | 8 PASS / 3 FAIL；PIPELINE_SUSPECT=false；LOW_COVERAGE=true |
| 17:18:32–38 | abm_posthoc_ties.py（非预注册） | 平均秩重跑：1 体变化，率不变 |
| 17:19 | abm_derived.py、abm_fig_chain.py（非预注册） | ABM_DERIVED.json、abm_chain_curve_v2.png |

墙钟全部 <10 秒/步，无需 setsid nohup，无 COLLECT.md。
