#!/bin/bash
# 与 GitHub Actions 共用的离线验证入口。
set -euo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export MPLBACKEND=Agg PYTHONDONTWRITEBYTECODE=1
PY=${PYTHON:-python3}
mkdir -p ci-logs
run() {
  local name="$1"; shift
  nice -n 19 "$@" 2>&1 | tee "ci-logs/$name.log"
}
run selftest "$PY" -m sigma_audit selftest --json ci-logs/SELFTEST.json
run smoke env PYTHON="$PY" bash scripts/smoke_test.sh
run fault_injection "$PY" tests/test_fault_injection.py
run submit_e2e "$PY" tests/test_submit_e2e.py
run release_snapshot "$PY" tests/test_release_snapshot.py
run replay "$PY" -m sigma_audit replay --limit 1
echo "CI: all requested checks passed"
