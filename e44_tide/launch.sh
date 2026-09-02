#!/bin/bash
set -u
E=/data/xinyuan/GOAI_ai4s_env/e44
echo $$ > /data/xinyuan/zpg_roms_dev/run_locks/e44_chain.pid
for d in $E/cases/*/; do
  tag=$(basename $d)
  [ -f $d/DONE ] && continue
  ( cd $d && rm -f DONE && /usr/bin/time -v ./coawstM_dnn_tide ocean_run.in > run.log 2> time.log && \
    grep -q "ROMS/TOMS: DONE" run.log && touch DONE || echo "FAIL $tag" >> $E/logs/failures.txt ) &
  echo "launched $tag pid=$!"
done
wait
echo "ALL_RUNS_FINISHED $(date +%F_%T)" | tee $E/logs/launch_done.txt
