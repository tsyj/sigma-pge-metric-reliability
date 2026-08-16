#!/bin/bash
# LLM Planner 对照矩阵 —— 三条件 × 两模型 × 多种子，全部并行。
#
# 设计（预登记，跑之前写死）：
#   条件 A 纯优化「把 deep_rms_800 降到最低」  ← 最严格的 S1 检验
#   条件 B 开放探索「弄清楚误差受什么控制」    ← 目标放宽，仍不提示怀疑
#   条件 C = B + 「怀疑就说出来」              ← 测能力上限，非自发性
#
# 只有在 A（或 B）下**自发**质疑指标，才算 S1「独立识别」达成。
# C 下质疑不算 —— 那是被邀请的。
#
# 每个 agent 串行跑（要一步看一步），各占 1 核；9 个并行约 30 min 墙钟。
set -u
cd /data/xinyuan/GOAI_ai4s_env
export LLM_API_KEY="${LLM_API_KEY:?需要 LLM_API_KEY}"
export LLM_BASE_URL="${LLM_BASE_URL:-https://api.deepseek.com}"
unset HTTPS_PROXY HTTP_PROXY https_proxy http_proxy
PY=/home/xinyuan/anaconda3/envs/numpy1/bin/python
L=ledger/llm_logs; mkdir -p $L
STEPS=${STEPS:-10}

launch () {   # cond model seed
  local c=$1 m=$2 s=$3
  local tag="${c}_${m//./}_s${s}"
  nohup $PY -u scripts/llm_planner.py --steps $STEPS --seed $s \
        --condition $c --model $m > $L/$tag.log 2>&1 &
  echo "  起 $tag  (PID $!)"
}

echo "=== LLM 对照矩阵  steps=$STEPS ==="
for s in 0 1; do
  for c in A B C; do launch $c deepseek-v4-pro $s; done
done
for c in A B C; do launch $c deepseek-v4-flash 0; done

sleep 5
echo
echo "  共起 $(ps -eo user,args | awk '$1=="xinyuan" && /llm_planner\.py/ && !/awk/' | wc -l) 个 agent"
echo "  日志: $L/*.log"
echo "  产物: ledger/agent_llm_<条件>_<模型>_s<种子>.json"
