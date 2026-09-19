# 扫描账本机算清单

由 `scripts/gen_runs_manifest.py` 生成；数值真源为 `e44_tide/analysis/RUNS_MANIFEST_FULL.json`。

扫描行数：**207**；其中完成状态为真的行数：**204**；按环境及标识去重：**207**。另列内潮 Agent 行：**4**。

这不是全项目运行总数，不代表全部原始输出已经交付，也不证明没有重跑。

| 环境 | 扫描行数 |
|---|---:|
| tide | 25 |
| wind_zonal | 56 |
| wind_merid | 56 |
| wind_diag45 | 56 |
| bh93_rest | 14 |

源文件完整 SHA-256 见 JSON 的 `source_sha256`；逐行出处见 `rows[].source`。
