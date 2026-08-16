#!/usr/bin/env python
"""为一次 run 生成隔离的运行目录 + 改写后的 .in（输出全部相对，输入指向本树）。

铁律（源自 zpg_roms_dev 那次覆写档案事故）：
  - 所有 OUTPUT 路径必须相对，写在本 run 目录内
  - 所有 INPUT 路径指向 GOAI 树内的只读副本，绝不指回原科研树
"""
import os, re, sys, shutil, argparse

ENV = "/data/xinyuan/GOAI_ai4s_env"
CASE = f"{ENV}/cases/seamount"

OUT_KEYS = ["RSTNAME", "HISNAME", "AVGNAME", "DIANAME", "QCKNAME",
            "TLMNAME", "TLFNAME", "ADJNAME", "STANAME", "FLTNAME"]


def make_run(run_id, grid="grid_rx0.2.nc", ntimes=8640, template="roms_real.in.template",
             overrides=None):
    rundir = f"{ENV}/runs/{run_id}"
    os.makedirs(rundir, exist_ok=True)
    src = f"{CASE}/{template}"
    dst = f"{rundir}/roms.in"

    ov = dict(overrides or {})
    ov.setdefault("NTIMES", str(ntimes))

    out_lines = []
    for line in open(src, errors="replace"):
        s = line.strip()
        # 输入：指向本树只读副本
        if re.match(r"^\s*VARNAME\s*=", line):
            line = f"     VARNAME = {CASE}/external/varinfo.dat\n"
        elif re.match(r"^\s*GRDNAME\s*==", line):
            line = f"     GRDNAME == {CASE}/grids/{grid}\n"
        elif re.match(r"^\s*ININAME\s*==", line):
            line = "     ININAME == roms_ini.nc\n"      # ANA_INITIAL，不会被读
        else:
            # 输出：一律相对，落在本 run 目录
            m = re.match(r"^\s*(" + "|".join(OUT_KEYS) + r")\s*==", line)
            if m:
                key = m.group(1)
                fn = {"RSTNAME": "roms_rst.nc", "HISNAME": "roms_his.nc",
                      "AVGNAME": "roms_avg.nc", "DIANAME": "roms_dia.nc"}.get(
                          key, f"roms_{key.lower()}.nc")
                line = f"     {key} == {fn}\n"
            else:
                # 运行期参数覆写
                for k, v in list(ov.items()):
                    if re.match(rf"^\s*{k}\s*==", line):
                        line = re.sub(r"==\s*\S+", f"== {v}", line, count=1)
                        ov.pop(k)
                        break
        out_lines.append(line)

    open(dst, "w").writelines(out_lines)
    if ov:
        print(f"  [warn] 这些参数在模板里没找到，未覆写: {list(ov)}", file=sys.stderr)
    return rundir


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run_id")
    p.add_argument("--grid", default="grid_rx0.2.nc")
    p.add_argument("--ntimes", type=int, default=8640)
    p.add_argument("--set", action="append", default=[], metavar="KEY=VAL")
    a = p.parse_args()
    ov = dict(kv.split("=", 1) for kv in a.set)
    d = make_run(a.run_id, a.grid, a.ntimes, overrides=ov)
    print(d)
