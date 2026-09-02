# 复赛增量说明（2026-09）

**一句话**：尺子的可靠性不是标量的性质，是审计协议的性质。见 `docs/semifinal/报告_v4_主文.md`。

## 目录
- `e44_tide/` — 第二环境（M2 内潮，84 km）：`mk_case.py`（白名单造例+md5 审计）、`analyze_e44.py`（TM/COH 口径逐字自 wake_20260829/phase_test.py）、`e47_mech.py`、`e48_search.py`（内潮穷举）、`e49_cross.py`（两环境交集）、`e50_audit_uv.py`（相位/盒宽/确定性审计）、`agent_tide.py`（陷阱局/判据局/中性局）、`e54_nameswap.py`（换名 ×5）、`scorecard.py`（kill board 一键重生成）、`PREREG_E44.md`+sha256+stamp、`analysis/`（全部 JSON，含 `E44_VERDICT_v2.json` 单一口径与 `RUNS_MANIFEST.json`）、`agent/`（全部轨迹 JSONL，含作废件）、`audit/`（每例输入件 md5）。
- `e52/` — 第三环境（经向风）：`ana_smflux_merid.h`（20 行补丁）、`env2_merid.py`、`knob_sweep_merid.py`、`metric_search_merid.py`、`e52_cross.py`（三重交集）、`PROVENANCE.md`（二进制 sha、真值镜像验证）、`E52_CROSS.json`。
- `scripts/smoke_test.sh` — 10 秒自检：预注册未改动、判读可重算、500 km 锚结构、E52 交集与 kill board 一致。

## 复现
```
bash scripts/smoke_test.sh
python e44_tide/scorecard.py      # 从 analysis/*.json 重画 kill board
```
完整重跑需 ROMS/MITgcm 数据（约 4 GB；his 文件与 MITgcm 输出未随包），构建与获取方式见 `build/`、`build_mitgcm/` 与 `e52/PROVENANCE.md`。
