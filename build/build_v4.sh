#!/bin/bash
# GOAI 赛道三 · 开放探索赛题 —— 环境求解器构建脚本
#
# 用法:  bash build.sh [-j N]        默认 -j 12
# 产出:  <build>/coawstM_goai        （即 env2.py 使用的求解器）
#
# 依赖（本机已验证的版本）:
#   gfortran 11.4.0 (Ubuntu 11.4.0-1ubuntu1~22.04.3)
#   OpenMPI mpif90  —— 必须用 /usr/bin/mpif90
#   netCDF 4.9.2    —— nc-config 在 /usr/local/bin
#
# ⚠ 两条构建铁律（踩过坑，见 HANDOFF_CONTEXT_MAP §7）:
#   1. PATH 必须把 /usr/bin 放最前 —— conda 环境里的 mpif90/mpicc 会导致链接失败
#   2. LD_LIBRARY_PATH 必须指向 /usr/lib/x86_64-linux-gnu —— 否则 gcc 7.2.0 ABI
#      不匹配会在运行期 SIGSEGV
set -euo pipefail

JOBS=12
while getopts "j:" o; do case $o in j) JOBS=$OPTARG;; esac; done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/src"
WORK="$HERE/work_v4"

# ---- 铁律 1 & 2 ----
export PATH=/usr/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}

echo "== 工具链 =="
echo "  mpif90 : $(command -v mpif90)"
mpif90 --version | head -1 | sed 's/^/           /'
echo "  netCDF : $(nc-config --version)"

# ---- 准备工作目录：header 与 analytical 必须在同一目录 ----
mkdir -p "$WORK"
cp "$HERE/v4/goai_seamount_v4.h" "$WORK/seamount.h"

# ---- ROMS 构建参数 ----
export ROMS_APPLICATION=SEAMOUNT      # → 头文件名 seamount.h
export MY_ROOT_DIR="$SRC"
export MY_ROMS_SRC="$SRC"
export MY_PROJECT_DIR="$WORK"
export MY_HEADER_DIR="$WORK"          # 我们的 goai_seamount.h 拷成 seamount.h 放这里
export MY_ANALYTICAL_DIR="$SRC/ROMS/Functionals"   # 含 SEAMOUNT_WIND 补丁
export SCRATCH_DIR="$WORK/Build_roms"
export BINDIR="$WORK"

export FORT=gfortran
export USE_MPI=on
export USE_MPIF90=on
export USE_NETCDF4=on

echo
echo "== 开始构建 (-j $JOBS) =="
cd "$WORK"
bash "$SRC/build_roms.sh" -j "$JOBS" 2>&1 | tail -25

if [ -f "$WORK/coawstM" ]; then
  mv "$WORK/coawstM" "$HERE/coawstM_goai"
  chmod +x "$HERE/coawstM_goai"
  echo
  echo "✓ 构建成功: $HERE/coawstM_goai"
  echo "  sha256: $(sha256sum "$HERE/coawstM_goai" | cut -d' ' -f1)"
else
  echo "✗ 构建失败：未找到 $WORK/coawstM"
  exit 1
fi
