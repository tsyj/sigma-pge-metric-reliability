#!/bin/bash
# 从源码重建 MITgcm 真值求解器 —— 回应 C 队攻击：二进制不能是拷来的。
#
# 只读引用用户科研目录的源码树（16 GB，不复制），所有产物落在本目录。
# 关键：PATH 必须钉死系统编译器 —— conda 的 mpif77 是坏的
#       （原 build_nr_13/genmake.log 里 13 处「未找到命令」即此故）。
set -e
export PATH=/usr/bin:/bin
unset LD_LIBRARY_PATH

ROOT=/data/xinyuan/zpg_roms_dev/MITgcm          # 只读
HERE=/data/xinyuan/GOAI_ai4s_env/build_mitgcm
CODE=$HERE/code
BUILD=$HERE/build

echo "=== 编译器 ==="
mpif77 --version 2>&1 | head -1
echo

rm -rf "$BUILD"; mkdir -p "$BUILD"
echo "=== genmake2 ==="
cd "$BUILD"
"$ROOT/tools/genmake2" \
    -rootdir="$ROOT" \
    -mods="$CODE" \
    -mpi \
    -optfile="$ROOT/tools/build_options/linux_amd64_gfortran" \
    > genmake_stdout.log 2>&1 || { tail -30 genmake_stdout.log; exit 1; }
echo "  ok"
grep -E "^(FC|LINK|FFLAGS)\s*=" Makefile | sed 's/^/  /'

echo
echo "=== make depend ==="
make depend > make_depend.log 2>&1 || { tail -30 make_depend.log; exit 1; }
echo "  ok"

echo
echo "=== make (16 核) ==="
make -j16 > make.log 2>&1 || { tail -40 make.log; exit 1; }
ls -l mitgcmuv
echo
echo "sha256: $(sha256sum mitgcmuv | cut -d' ' -f1)"
echo "md5   : $(md5sum   mitgcmuv | cut -d' ' -f1)"
echo "原拷贝 md5: 16ea8774286c6556eb2cab5b2f46e454"
