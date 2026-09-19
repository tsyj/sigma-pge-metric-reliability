# COLLECT（ppi_truth_budget 判分批）
- 启动：2026-09-17T15:53:54+08:00，setsid nohup bash run_all.sh > RUN_ALL.nohup 2>&1
- 封存：.sha256 时间戳 2026-09-17T15:53:47+08:00（PREREG sha256 80e93dc9…cc00a2）
- 收集：已完成 2026-09-17T15:55:06+08:00（RUN_ALL.log done）；结果见 RESULT_ppi_truth_budget.md
- 进程：pgrep -f "tb_(budget|rectifier|verdict).py" 按确切 pid 处置；禁 pkill -f
