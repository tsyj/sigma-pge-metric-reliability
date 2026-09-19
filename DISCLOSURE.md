# 依赖、授权与实验模型披露

## 交付范围与数据边界

本版交付本项目的数值试验分析账本、判定 JSON、预注册校验件、离线送检代码与缓存。原始模式输出、求解器源码和二进制不随本版交付。代码用 MIT（`LICENSE`），自产分析数据用 CC BY 4.0（`LICENSE-DATA`）；第三方组件继续适用其自身许可。

外部报告与论文的审查结果可在决赛展示；展示结果不授予原始数据及文稿的再分发权。这些原始材料不进入公开仓库，也不归入本项目的数据许可。自产数据的授权仅覆盖本项目持有的权利。

## 第三方组件与许可核对

| 组件 | 实验用途 | 本地证据与交付边界 |
|---|---|---|
| ROMS / COAWST 中的 ROMS 组件 | σ 坐标求解器 | 核对本地 `build/src/ROMS/License_ROMS.txt`，原文副本见 `docs/licenses/License_ROMS.txt`；其版本行是 revision 1054（2021-03-06）。ROMS/TOMS Group 2002–2021 版权，许可为 MIT/X。不能由此推断整个耦合系统的所有组件采用同一许可。 |
| MITgcm | z 坐标参照解 | 构建入口 `build_mitgcm/build.sh`；求解器不在本版中再分发，使用时应核对所取版本的许可。参照解来自另一套代码，不是只改变一个坐标参数的对照。 |
| Python 数值依赖 | 缓存查表、分析、绘图 | 安装依赖见 `pyproject.toml`，原始实验还使用 netCDF4 等库；依赖各依其自身许可。 |

ROMS 原文写明：`This Software is open-source and licensed under the following conditions as stated by MIT/X License`。其授权包含使用、复制、修改、合并、发布、分发、再许可及销售，要求保留版权和许可声明，并按原样提供。原文另将用户论坛参与和可用技术支持限于注册用户；不能把注册条件写成学术用途限定。上述文字仅描述本地许可原文，不作版本范围之外的许可推定。

## 实验角色表

本表仅列实验调用。运行与数值判分由脚本执行；模型的回答属于被测数据，模型给出的判断不替代固定数值判据。

| 角色 | 实际模型与渠道 | 用途与证据 |
|---|---|---|
| 实验执行者（提出下一动作或指标）／被试 | DeepSeek 官方 API：`deepseek-v4-pro`、`deepseek-v4-flash` | 初赛与复赛动作选择、指标提议和挑指标；随包 `ledger/agent_*.json`、`e44_tide/agent/*.jsonl`、`e61/trajectory_e61.jsonl`。 |
| 审查者／被试 | DeepSeek 官方 API：`deepseek-v4-pro`、`deepseek-v4-flash` | 换名题面的可信性与可刷分性判断；`e44_tide/agent/E54_NAMESWAP.json`、`E62_NAMESWAP_XMODEL.json`。 |
| 审查者／被试（E70） | DeepSeek 官方 API：请求 `deepseek-v4-pro`、`deepseek-v4-flash`；后者成功应答身份为 `deepseek-flash` | 本机日志只读快照中有成功应答，身份原样保留，见 `MODEL_USAGE_SNAPSHOT.json`。 |
| 审查者／被试（E70） | OpenAI 订阅渠道、实验 CLI：请求 `gpt-5.6-sol`、`gpt-6-astra` | 本机日志有成功记录；`actual_model` 为空，故只披露请求名，不称应答身份已经核实。 |
| 审查者／被试（E70） | 硅基流动 API：`deepseek-ai/DeepSeek-V4-Pro`、`Qwen/Qwen3.5-122B-A10B`、`zai-org/GLM-5.3`、`Pro/moonshotai/Kimi-K2.6` | 各模型均在只读快照中有成功记录。 |
| 审查者／被试（E70） | 硅基流动 API：`meituan-longcat/LongCat-2.0`、`stepfun-ai/Step-3.5-Flash`、`inclusionAI/Ling-flash-2.0`、`ByteDance-Seed/Seed-OSS-36B-Instruct` | 各模型均在只读快照中有成功记录；格式解析失败另记，不能算入有效样本。 |
| 审查者／被试（E70，样本不足） | 硅基流动 API：`tencent/Hy4-preview` | 结束快照中 C0 有 2 条成功记录，C1/C2 为 0，未进入合格主分析集。 |

**Claude 渠道已有结果**：Anthropic 实验 CLI 请求 `claude-opus-5`、`claude-sonnet-5`、`claude-haiku-4-5-20251001`，原账本与两份汇总见 [E70 证据说明](e70/README.md)。按请求名分别有 90、5、36 条 ok；Sonnet/Haiku 样本量不足。`actual_model` 来自排序后的首个用量模型键，Opus/Sonnet 的成功行同时有对应请求名与 Haiku 键，因此应答身份仍存在字段歧义，不能把请求名直接当作已核实的最终回答模型。源文件按原字节保留，本轮未重新调用模型。

## 调用统计、费用与复现限制

`MODEL_USAGE_SNAPSHOT.json` 从 E70 已结束日志只读提取请求名、身份字段、状态行数及原文件哈希；该元数据文件不含题面、应答原文或凭据。Claude 原账本另随本版交付，并与原汇总逐条件对齐；其他渠道原账本仍只在本地。状态行数含重试与停止标记，不等于有效样本数或计费调用次数。现有材料不足以机算完整 E70 费用，本版不报费用总数。

DeepSeek 历史实验的详细轨迹以随包账本为准，不继续沿用约数作为完整调用总量。所有模型凭据均不交付。模型输出受服务端版本与采样影响，不能保证逐字复现；离线入口只回读已交付结果，不再调用模型。缓存数值复算也不等于重新运行物理求解器。

## 预注册与复核边界

本地哈希证明所列字节与登记一致，不能单独证明历史先后顺序。E65/E67b 在运行后向预注册文件追加过内容，校验范围为封存段及全文前缀，见各自核验说明。后续提交日期不能追认历史封存时间。本轮不添加独立外部审查者身份，也不把同一执行链的检查称作外部复核。
