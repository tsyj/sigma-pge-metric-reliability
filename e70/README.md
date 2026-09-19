# E70 结果证据与读法

本目录按原字节收录 `results/claude.jsonl`、`SUMMARY_E70.md` 和 `E70_NAMESWAP_XVENDOR.json`。原汇总生成于 2026-09-18 12:57:26 +0800；来源哈希见根目录 `SOURCE_PROVENANCE.json`，状态统计与读取时刻见 `MODEL_USAGE_SNAPSHOT.json`。没有重发请求或改写结果。

Claude 账本共 872 行：ok 131、channel_error 437、tool_use 163、gave_up 139、parse_fail 2。按请求名，Opus 成功 90（30/30/30），Sonnet 成功 5（5/0/0），Haiku 成功 36（18/18/0）；后三个数字依次对应 C0、C1、C2。只有 Opus 请求组满足原汇总的每条件至少 23 行门槛。

**模型身份限制：** 原采集器 `run_claude.py:58–66` 将排序后的首个 `modelUsage` 键记入 `actual_model`。Opus/Sonnet 的全部成功行都有 Haiku 及对应请求模型两个用量键，却将 Haiku 写入 `actual_model`；Haiku 的成功行只有 Haiku 键。多键记录不足以唯一确认最终回答模型，也不能据此断言请求被替换。请结合 `requested_model` 与 `extra.model_usage_keys` 阅读；原汇总的模型标签按请求分组，不能称模型应答身份已独立验证。原结果保留，未据此重新判定科学结论。

CLI 版本号是实验渠道证据。usage 内的计量字段不是凭据。含工具使用的行和失败行供审计，不计入 ok 样本。费用字段不代表完整账单；本目录未交付其他渠道全部原账本及完整 E70 运行链，不能单凭三个文件完整重跑跨渠道分析。离线 CI 不调用模型。
