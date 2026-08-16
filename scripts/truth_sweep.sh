#!/bin/bash
# 通用 MITgcm 真值扫描：truth_sweep.sh <参数名> <值1> <值2> ...
#
# 每个值起一个独立 run 目录 truth/sw_<参数>_<值>/，跑完打印读数。
#
# 关键（E26 教训）：`data` 文件缩进是 **一个空格**，写死空格数的 sed 会
# 静默不匹配 —— 五个 run 全用同一套配置，结果干净得可疑。因此
#   (a) 用空白字符类匹配
#   (b) 参数行不存在时**插入**而不是静默跳过
#   (c) 跑之前回显实际写进去的那一行
set -e
E=/data/xinyuan/GOAI_ai4s_env
SEED=$E/truth/mit_r26steep          # 已验证可复现官方结果的基准 run
PARAM=$1; shift

echo "=== 扫描 $PARAM: $* ==="
for v in "$@"; do
    tag=$(echo "$v" | tr '.-' 'pm')
    d=$E/truth/sw_${PARAM}_${tag}
    rm -rf "$d"; mkdir -p "$d"
    for f in data data.pkg eedata topog.bin T_wind13.bin windx.bin mitgcmuv; do
        cp "$SEED/$f" "$d/" 2>/dev/null || true
    done
    cp $E/build_mitgcm/build/mitgcmuv "$d/"      # 源码重建的二进制

    if grep -qiE "^[[:space:]]*$PARAM[[:space:]]*=" "$d/data"; then
        sed -i -E "s/^([[:space:]]*)$PARAM[[:space:]]*=.*/\1$PARAM = $v,/" "$d/data"
    else
        # 参数原本不在 namelist 里（如 viscA4）→ 插到 PARM01 段首
        sed -i -E "0,/^[[:space:]]*&PARM01/s//\&PARM01\n $PARAM = $v,/" "$d/data"
    fi

    got=$(grep -iE "^[[:space:]]*$PARAM[[:space:]]*=" "$d/data" | head -1 | tr -s ' ')
    printf "  %-22s 写入: %s\n" "$(basename $d)" "$got"
    [ -n "$got" ] || { echo "  ✗ $PARAM 未写入，中止"; exit 1; }

    ( cd "$d" && ./mitgcmuv > run.log 2>&1 ) || echo "    ⚠ 退出码非零"
    grep -q "STOP NORMAL END" "$d/run.log" || echo "    ⚠ 未正常结束"
done
echo "=== $PARAM 扫描完成 ==="
