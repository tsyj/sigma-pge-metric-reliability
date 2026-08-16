#!/bin/bash
# 并发标度测试：找有效吞吐拐点（不是核越多越好）
# 每个 run 1200 步；测 batch wall time → 有效吞吐 runs/min
set -u
ENV=/data/xinyuan/GOAI_ai4s_env
PY=/home/xinyuan/anaconda3/envs/numpy1/bin/python
export PATH=/usr/bin:$PATH
NSTEP=1200
OUT=$ENV/ledger/scaling.csv
echo "concurrency,batch_wall_s,per_run_s,throughput_runs_per_min,disk_MB" > $OUT

for NC in 1 4 8 16 32 64 96 128; do
  rm -rf $ENV/runs/scal_*
  for i in $(seq 1 $NC); do
    $PY $ENV/scripts/mkrun.py scal_${NC}_${i} --ntimes $NSTEP >/dev/null 2>&1
  done
  t0=$(date +%s.%N)
  for i in $(seq 1 $NC); do
    ( cd $ENV/runs/scal_${NC}_${i} && $ENV/bin/coawstM_goai roms.in > run.log 2>&1 ) &
  done
  wait
  t1=$(date +%s.%N)
  wall=$(echo "$t1 - $t0" | bc)
  per=$(echo "scale=2; $wall / 1" | bc)
  thr=$(echo "scale=2; $NC * 60 / $wall" | bc)
  mb=$(du -sm $ENV/runs 2>/dev/null | cut -f1)
  ok=$(grep -l "ROMS/TOMS: DONE" $ENV/runs/scal_${NC}_*/run.log 2>/dev/null | wc -l)
  printf "%3d 并发 | batch %7.1fs | 吞吐 %8.2f runs/min | 完成 %d/%d | 盘 %s MB\n" \
         "$NC" "$wall" "$thr" "$ok" "$NC" "$mb"
  echo "$NC,$wall,$per,$thr,$mb" >> $OUT
done
rm -rf $ENV/runs/scal_*
echo "结果: $OUT"
