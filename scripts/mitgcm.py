#!/usr/bin/env python
"""极简 MITgcm meta/data 读取器（真值接入）。

MITgcm 把每个场写成一对 <name>.<iter>.<tile>.meta / .data：
  .meta 给 nDims / dimList / dataprec，.data 是 big-endian Fortran 裸二进制。
"""
import os, re, glob
import numpy as np


def read_meta(path):
    txt = open(path).read()
    nd = int(re.search(r"nDims\s*=\s*\[\s*(\d+)", txt).group(1))
    nums = [int(x) for x in re.findall(r"-?\d+",
            re.search(r"dimList\s*=\s*\[(.*?)\]", txt, re.S).group(1))]
    # dimList 每维三个数：global, start, end
    dims = [nums[3 * i] for i in range(nd)]
    prec = re.search(r"dataprec\s*=\s*\[\s*'(\w+)'", txt).group(1)
    nrec = int(re.search(r"nrecords\s*=\s*\[\s*(\d+)", txt).group(1))
    return dims, prec, nrec


def read_field(prefix, iter_=None, rundir="."):
    """返回 (nz, ny, nx) 数组（Fortran 序 → C 序转置）。"""
    pat = f"{rundir}/{prefix}." + (f"{iter_:010d}." if iter_ is not None else "") + "*.meta"
    metas = sorted(glob.glob(pat))
    if not metas:
        pat = f"{rundir}/{prefix}*.meta"
        metas = sorted(glob.glob(pat))
    if not metas:
        raise FileNotFoundError(pat)
    m = metas[0]
    dims, prec, nrec = read_meta(m)
    dt = {">f8": ">f8", "float64": ">f8", "float32": ">f4"}[prec]
    data = np.fromfile(m.replace(".meta", ".data"), dtype=dt)
    # dimList 顺序为 (x, y, z)；Fortran 序 → reshape 成 (z,y,x)
    shape = tuple(dims[::-1])
    return data.reshape(shape)


def iters(prefix, rundir="."):
    out = []
    for f in glob.glob(f"{rundir}/{prefix}.*.meta"):
        m = re.search(rf"{prefix}\.(\d{{10}})\.", os.path.basename(f))
        if m:
            out.append(int(m.group(1)))
    return sorted(set(out))


if __name__ == "__main__":
    import sys
    rd = sys.argv[1] if len(sys.argv) > 1 else "."
    print("时间步:", iters("U", rd))
    for name in ("XC", "YC", "Depth", "RC", "DRF"):
        try:
            a = read_field(name, None, rd)
            print(f"{name:8s} shape={a.shape}  范围=[{np.nanmin(a):.4g}, {np.nanmax(a):.4g}]")
        except Exception as e:
            print(f"{name:8s} 读取失败: {e}")
