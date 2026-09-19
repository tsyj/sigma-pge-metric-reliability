# E70 跨厂商换名敏感性 —— 汇总（生成于 2026-09-18 12:57:26 +0800）

## 数据质量硬校验

无异常：重复 ok=0；超尝试上限的 ok=0；gave_up 重复标记=0。

主读数按真实身份计：Pnet_MW 被标 trustworthy / uv_ratio 被标 gameable / deep_dc_rms 被标 gameable。
uv_gameable 为探索性读数（预注册无预测）。

## 合格模型（跨模型主分析集：非哨兵且三条件 n≥23）

合格 10 个: claude:claude-opus-5, codex:gpt-5.6-sol, codex:gpt-6-astra, openai_compat/deepseek:deepseek-v4-pro, openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct, openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6, openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B, openai_compat/siliconflow:meituan-longcat/LongCat-2.0, openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash, openai_compat/siliconflow:zai-org/GLM-5.3
- 排除 claude:claude-haiku-4-5-20251001：未达预注册样本量: C0_named n=18<23, C1_anon n=18<23, C2_swapped n=0<23
- 排除 claude:claude-sonnet-5：未达预注册样本量: C0_named n=5<23, C1_anon n=0<23, C2_swapped n=0<23
- 排除 openai_compat/deepseek:deepseek-v4-flash：历史延续哨兵（与 #6 同厂商，复赛 E62 同款 v4_flash），预注册排除于跨模型汇总，仅与 E62 历史结果描述性对照
- 排除 openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro：渠道哨兵（与 DeepSeek 官方同权重的第三方部署），预注册排除于跨模型汇总
- 排除 openai_compat/siliconflow:inclusionAI/Ling-flash-2.0：未达预注册样本量: C0_named n=21<23, C2_swapped n=21<23
- 排除 openai_compat/siliconflow:tencent/Hy4-preview：未达预注册样本量: C0_named n=2<23, C1_anon n=0<23, C2_swapped n=0<23

## 预注册判定（P1–P5，机械执行 PREREG §5）

| 预测 | 判定 | 关键数字 |
|---|---|---|
| P1 语义先验跨厂商复制 | **成立** | 合格 10/14 候选(门槛=多数=8), 方向下降 10 (100%), MH={"OR_MH": 20.2259, "CMH_chi2_cc": 222.2448, "p": 0.0, "n_strata": 10} |
| P2 数据可识别性 | **成立** | 检查 10 模型, 违例: 无 |
| P3 deepDC 不随名字动 | **不成立** | 主判定 CMH p=None；Holm 后显著: 无 |
| P4 无显著反向 | **成立** | 反例: 无 |
| P5 旗舰降幅≥0.20 | **成立** | {"claude-opus-5": 1.0, "gpt-6-astra": 0.9667} |

## 每模型 × 条件

| 模型(渠道) | 条件 | n | Pnet_trusted | uv_gameable | deepDC_gameable |
|---|---|---|---|---|---|
| claude:claude-haiku-4-5-20251001 ⚠n不足 | C0_named | 18 | 11/18 (0.39–0.80) | 9/18 (0.29–0.71) | 18/18 (0.82–1.00) |
| claude:claude-haiku-4-5-20251001 ⚠n不足 | C1_anon | 18 | 1/18 (0.01–0.26) | 2/18 (0.03–0.33) | 17/18 (0.74–0.99) |
| claude:claude-opus-5 | C0_named | 30 | 30/30 (0.89–1.00) | 16/30 (0.36–0.70) | 30/30 (0.89–1.00) |
| claude:claude-opus-5 | C1_anon | 30 | 0/30 (0.00–0.11) | 12/30 (0.25–0.58) | 30/30 (0.89–1.00) |
| claude:claude-opus-5 | C2_swapped | 30 | 2/30 (0.02–0.21) | 30/30 (0.89–1.00) | 30/30 (0.89–1.00) |
| claude:claude-sonnet-5 ⚠n不足 | C0_named | 5 | 5/5 (0.57–1.00) | 5/5 (0.57–1.00) | 5/5 (0.57–1.00) |
| codex:gpt-5.6-sol | C0_named | 30 | 30/30 (0.89–1.00) | 0/30 (0.00–0.11) | 30/30 (0.89–1.00) |
| codex:gpt-5.6-sol | C1_anon | 30 | 0/30 (0.00–0.11) | 0/30 (0.00–0.11) | 30/30 (0.89–1.00) |
| codex:gpt-5.6-sol | C2_swapped | 30 | 10/30 (0.19–0.51) | 21/30 (0.52–0.83) | 30/30 (0.89–1.00) |
| codex:gpt-6-astra | C0_named | 30 | 30/30 (0.89–1.00) | 0/30 (0.00–0.11) | 30/30 (0.89–1.00) |
| codex:gpt-6-astra | C1_anon | 30 | 1/30 (0.01–0.17) | 0/30 (0.00–0.11) | 30/30 (0.89–1.00) |
| codex:gpt-6-astra | C2_swapped | 30 | 13/30 (0.27–0.61) | 30/30 (0.89–1.00) | 30/30 (0.89–1.00) |
| openai_compat/deepseek:deepseek-v4-flash ⚠哨兵 | C0_named | 30 | 30/30 (0.89–1.00) | 14/30 (0.30–0.64) | 30/30 (0.89–1.00) |
| openai_compat/deepseek:deepseek-v4-flash ⚠哨兵 | C1_anon | 30 | 17/30 (0.39–0.73) | 11/30 (0.22–0.54) | 30/30 (0.89–1.00) |
| openai_compat/deepseek:deepseek-v4-flash ⚠哨兵 | C2_swapped | 30 | 11/30 (0.22–0.54) | 29/30 (0.83–0.99) | 30/30 (0.89–1.00) |
| openai_compat/deepseek:deepseek-v4-pro | C0_named | 30 | 26/30 (0.70–0.95) | 20/30 (0.49–0.81) | 30/30 (0.89–1.00) |
| openai_compat/deepseek:deepseek-v4-pro | C1_anon | 30 | 1/30 (0.01–0.17) | 0/30 (0.00–0.11) | 30/30 (0.89–1.00) |
| openai_compat/deepseek:deepseek-v4-pro | C2_swapped | 30 | 1/30 (0.01–0.17) | 30/30 (0.89–1.00) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C0_named | 30 | 3/30 (0.03–0.26) | 29/30 (0.83–0.99) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C1_anon | 30 | 1/30 (0.01–0.17) | 9/30 (0.17–0.48) | 24/30 (0.63–0.91) |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C2_swapped | 30 | 0/30 (0.00–0.11) | 30/30 (0.89–1.00) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C0_named | 30 | 13/30 (0.27–0.61) | 7/30 (0.12–0.41) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C1_anon | 29 | 0/29 (0.00–0.12) | 8/29 (0.15–0.46) | 29/29 (0.88–1.00) |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C2_swapped | 30 | 3/30 (0.03–0.26) | 16/30 (0.36–0.70) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C0_named | 30 | 17/30 (0.39–0.73) | 13/30 (0.27–0.61) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C1_anon | 30 | 1/30 (0.01–0.17) | 0/30 (0.00–0.11) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C2_swapped | 30 | 1/30 (0.01–0.17) | 21/30 (0.52–0.83) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro ⚠哨兵 | C0_named | 30 | 30/30 (0.89–1.00) | 7/30 (0.12–0.41) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro ⚠哨兵 | C1_anon | 29 | 7/29 (0.12–0.42) | 1/29 (0.01–0.17) | 29/29 (0.88–1.00) |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro ⚠哨兵 | C2_swapped | 30 | 13/30 (0.27–0.61) | 29/30 (0.83–0.99) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 ⚠n不足 | C0_named | 21 | 14/21 (0.45–0.83) | 0/21 (0.00–0.15) | 21/21 (0.85–1.00) |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 ⚠n不足 | C1_anon | 30 | 11/30 (0.22–0.54) | 22/30 (0.56–0.86) | 21/30 (0.52–0.83) |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 ⚠n不足 | C2_swapped | 21 | 13/21 (0.41–0.79) | 17/21 (0.60–0.92) | 21/21 (0.85–1.00) |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C0_named | 30 | 18/30 (0.42–0.75) | 13/30 (0.27–0.61) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C1_anon | 30 | 16/30 (0.36–0.70) | 16/30 (0.36–0.70) | 24/30 (0.63–0.91) |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C2_swapped | 30 | 6/30 (0.10–0.37) | 27/30 (0.74–0.97) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C0_named | 30 | 5/30 (0.07–0.34) | 3/30 (0.03–0.26) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C1_anon | 30 | 0/30 (0.00–0.11) | 1/30 (0.01–0.17) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C2_swapped | 30 | 1/30 (0.01–0.17) | 27/30 (0.74–0.97) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:tencent/Hy4-preview ⚠n不足 | C0_named | 2 | 2/2 (0.34–1.00) | 1/2 (0.09–0.91) | 2/2 (0.34–1.00) |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C0_named | 30 | 29/30 (0.83–0.99) | 30/30 (0.89–1.00) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C1_anon | 30 | 18/30 (0.42–0.75) | 3/30 (0.03–0.26) | 30/30 (0.89–1.00) |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C2_swapped | 30 | 27/30 (0.74–0.97) | 30/30 (0.89–1.00) | 30/30 (0.89–1.00) |

## 每模型检验（Fisher 双侧, C0 vs Cx）

| 模型 | 对照 | 读数 | C0 | Cx | Δrate | OR | p |
|---|---|---|---|---|---|---|---|
| claude:claude-haiku-4-5-20251001 | C1_anon | Pnet_trusted | 11/18 | 1/18 | -0.56 | 26.7143 | 0.00094 |
| claude:claude-haiku-4-5-20251001 | C1_anon | uv_gameable | 9/18 | 2/18 | -0.39 | 8.0 | 0.02749 |
| claude:claude-haiku-4-5-20251001 | C1_anon | deepDC_gameable | 18/18 | 17/18 | -0.06 | inf | 1.0 |
| claude:claude-opus-5 | C1_anon | Pnet_trusted | 30/30 | 0/30 | -1.00 | inf | 0.0 |
| claude:claude-opus-5 | C1_anon | uv_gameable | 16/30 | 12/30 | -0.13 | 1.7143 | 0.4379 |
| claude:claude-opus-5 | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| claude:claude-opus-5 | C2_swapped | Pnet_trusted | 30/30 | 2/30 | -0.93 | inf | 0.0 |
| claude:claude-opus-5 | C2_swapped | uv_gameable | 16/30 | 30/30 | +0.47 | 0.0 | 2e-05 |
| claude:claude-opus-5 | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| codex:gpt-5.6-sol | C1_anon | Pnet_trusted | 30/30 | 0/30 | -1.00 | inf | 0.0 |
| codex:gpt-5.6-sol | C1_anon | uv_gameable | 0/30 | 0/30 | +0.00 | None | 1.0 |
| codex:gpt-5.6-sol | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| codex:gpt-5.6-sol | C2_swapped | Pnet_trusted | 30/30 | 10/30 | -0.67 | inf | 0.0 |
| codex:gpt-5.6-sol | C2_swapped | uv_gameable | 0/30 | 21/30 | +0.70 | 0.0 | 0.0 |
| codex:gpt-5.6-sol | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| codex:gpt-6-astra | C1_anon | Pnet_trusted | 30/30 | 1/30 | -0.97 | inf | 0.0 |
| codex:gpt-6-astra | C1_anon | uv_gameable | 0/30 | 0/30 | +0.00 | None | 1.0 |
| codex:gpt-6-astra | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| codex:gpt-6-astra | C2_swapped | Pnet_trusted | 30/30 | 13/30 | -0.57 | inf | 0.0 |
| codex:gpt-6-astra | C2_swapped | uv_gameable | 0/30 | 30/30 | +1.00 | 0.0 | 0.0 |
| codex:gpt-6-astra | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/deepseek:deepseek-v4-flash | C1_anon | Pnet_trusted | 30/30 | 17/30 | -0.43 | inf | 5e-05 |
| openai_compat/deepseek:deepseek-v4-flash | C1_anon | uv_gameable | 14/30 | 11/30 | -0.10 | 1.5114 | 0.60095 |
| openai_compat/deepseek:deepseek-v4-flash | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/deepseek:deepseek-v4-flash | C2_swapped | Pnet_trusted | 30/30 | 11/30 | -0.63 | inf | 0.0 |
| openai_compat/deepseek:deepseek-v4-flash | C2_swapped | uv_gameable | 14/30 | 29/30 | +0.50 | 0.0302 | 2e-05 |
| openai_compat/deepseek:deepseek-v4-flash | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/deepseek:deepseek-v4-pro | C1_anon | Pnet_trusted | 26/30 | 1/30 | -0.83 | 188.5 | 0.0 |
| openai_compat/deepseek:deepseek-v4-pro | C1_anon | uv_gameable | 20/30 | 0/30 | -0.67 | inf | 0.0 |
| openai_compat/deepseek:deepseek-v4-pro | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/deepseek:deepseek-v4-pro | C2_swapped | Pnet_trusted | 26/30 | 1/30 | -0.83 | 188.5 | 0.0 |
| openai_compat/deepseek:deepseek-v4-pro | C2_swapped | uv_gameable | 20/30 | 30/30 | +0.33 | 0.0 | 0.0008 |
| openai_compat/deepseek:deepseek-v4-pro | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C1_anon | Pnet_trusted | 3/30 | 1/30 | -0.07 | 3.2222 | 0.61195 |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C1_anon | uv_gameable | 29/30 | 9/30 | -0.67 | 67.6667 | 0.0 |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C1_anon | deepDC_gameable | 30/30 | 24/30 | -0.20 | inf | 0.02372 |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C2_swapped | Pnet_trusted | 3/30 | 0/30 | -0.10 | inf | 0.23729 |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C2_swapped | uv_gameable | 29/30 | 30/30 | +0.03 | 0.0 | 1.0 |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C1_anon | Pnet_trusted | 13/30 | 0/29 | -0.43 | inf | 5e-05 |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C1_anon | uv_gameable | 7/30 | 8/29 | +0.04 | 0.7989 | 0.77102 |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C1_anon | deepDC_gameable | 30/30 | 29/29 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C2_swapped | Pnet_trusted | 13/30 | 3/30 | -0.33 | 6.8824 | 0.00741 |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C2_swapped | uv_gameable | 7/30 | 16/30 | +0.30 | 0.2663 | 0.03259 |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C1_anon | Pnet_trusted | 17/30 | 1/30 | -0.53 | 37.9231 | 1e-05 |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C1_anon | uv_gameable | 13/30 | 0/30 | -0.43 | inf | 5e-05 |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C2_swapped | Pnet_trusted | 17/30 | 1/30 | -0.53 | 37.9231 | 1e-05 |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C2_swapped | uv_gameable | 13/30 | 21/30 | +0.27 | 0.3277 | 0.06728 |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | C1_anon | Pnet_trusted | 30/30 | 7/29 | -0.76 | inf | 0.0 |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | C1_anon | uv_gameable | 7/30 | 1/29 | -0.20 | 8.5217 | 0.05231 |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | C1_anon | deepDC_gameable | 30/30 | 29/29 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | C2_swapped | Pnet_trusted | 30/30 | 13/30 | -0.57 | inf | 0.0 |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | C2_swapped | uv_gameable | 7/30 | 29/30 | +0.73 | 0.0105 | 0.0 |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | C1_anon | Pnet_trusted | 14/21 | 11/30 | -0.30 | 3.4545 | 0.04832 |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | C1_anon | uv_gameable | 0/21 | 22/30 | +0.73 | 0.0 | 0.0 |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | C1_anon | deepDC_gameable | 21/21 | 21/30 | -0.30 | inf | 0.00681 |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | C2_swapped | Pnet_trusted | 14/21 | 13/21 | -0.05 | 1.2308 | 1.0 |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | C2_swapped | uv_gameable | 0/21 | 17/21 | +0.81 | 0.0 | 0.0 |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | C2_swapped | deepDC_gameable | 21/21 | 21/21 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C1_anon | Pnet_trusted | 18/30 | 16/30 | -0.07 | 1.3125 | 0.79477 |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C1_anon | uv_gameable | 13/30 | 16/30 | +0.10 | 0.6691 | 0.60581 |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C1_anon | deepDC_gameable | 30/30 | 24/30 | -0.20 | inf | 0.02372 |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C2_swapped | Pnet_trusted | 18/30 | 6/30 | -0.40 | 6.0 | 0.00333 |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C2_swapped | uv_gameable | 13/30 | 27/30 | +0.47 | 0.085 | 0.00025 |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C1_anon | Pnet_trusted | 5/30 | 0/30 | -0.17 | inf | 0.05219 |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C1_anon | uv_gameable | 3/30 | 1/30 | -0.07 | 3.2222 | 0.61195 |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C2_swapped | Pnet_trusted | 5/30 | 1/30 | -0.13 | 5.8 | 0.19451 |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C2_swapped | uv_gameable | 3/30 | 27/30 | +0.80 | 0.0123 | 0.0 |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C1_anon | Pnet_trusted | 29/30 | 18/30 | -0.37 | 19.3333 | 0.00105 |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C1_anon | uv_gameable | 30/30 | 3/30 | -0.90 | inf | 0.0 |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C1_anon | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C2_swapped | Pnet_trusted | 29/30 | 27/30 | -0.07 | 3.2222 | 0.61195 |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C2_swapped | uv_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |
| openai_compat/siliconflow:zai-org/GLM-5.3 | C2_swapped | deepDC_gameable | 30/30 | 30/30 | +0.00 | None | 1.0 |

## 跨模型合并 —— 主分析（仅合格模型，分层 = 模型）

| 对照 | 读数 | 低于C0的模型数 | 高于 | 持平 | MH 合并 OR | CMH p |
|---|---|---|---|---|---|---|
| C1_anon | Pnet_trusted | 10 | 0 | 0 | 20.2259 | 0.0 |
| C1_anon | uv_gameable | 6 | 2 | 2 | 4.6982 | 0.0 |
| C1_anon | deepDC_gameable | 2 | 0 | 8 | inf | 0.0009 |
| C2_swapped | Pnet_trusted | 10 | 0 | 0 | 22.4063 | 0.0 |
| C2_swapped | uv_gameable | 0 | 9 | 1 | 0.0627 | 0.0 |
| C2_swapped | deepDC_gameable | 0 | 0 | 10 | - | - |

## 跨模型合并 —— 敏感性（全部非哨兵模型，含 n 不足者）

| 对照 | 读数 | 低于C0的模型数 | 高于 | 持平 | MH 合并 OR | CMH p |
|---|---|---|---|---|---|---|
| C1_anon | Pnet_trusted | 12 | 0 | 0 | 16.1738 | 0.0 |
| C1_anon | uv_gameable | 7 | 3 | 2 | 2.7134 | 0.0 |
| C1_anon | deepDC_gameable | 4 | 0 | 8 | inf | 1e-05 |
| C2_swapped | Pnet_trusted | 11 | 0 | 0 | 13.8571 | 0.0 |
| C2_swapped | uv_gameable | 0 | 10 | 1 | 0.0559 | 0.0 |
| C2_swapped | deepDC_gameable | 0 | 0 | 11 | - | - |

## 厂商层级次要分析（预注册 §5 次要分析，不改变 P1 主判定；分层 = 公司）

公司数 9（各公司合并其合格模型计数为一个 2×2 表）

| 对照 | 读数 | 方向下降公司数 | 上升 | 持平 | MH(按公司) OR | CMH p |
|---|---|---|---|---|---|---|
| C1_anon | Pnet_trusted | 9 | 0 | 0 | 20.2259 | 0.0 |
| C1_anon | uv_gameable | 6 | 2 | 1 | 4.6982 | 0.0 |
| C1_anon | deepDC_gameable | 2 | 0 | 7 | inf | 0.0009 |
| C2_swapped | Pnet_trusted | 9 | 0 | 0 | 22.4063 | 0.0 |
| C2_swapped | uv_gameable | 0 | 8 | 1 | 0.0627 | 0.0 |
| C2_swapped | deepDC_gameable | 0 | 0 | 9 | - | - |

各公司 C0→C1 Pnet_trusted（合并计数）：

| 公司 | C0 | C1 | Δrate |
|---|---|---|---|
| Anthropic | 30/30 | 0/30 | -1.00 |
| DeepSeek | 26/30 | 1/30 | -0.83 |
| OpenAI | 60/60 | 1/60 | -0.98 |
| 字节跳动 | 3/30 | 1/30 | -0.07 |
| 智谱 | 29/30 | 18/30 | -0.37 |
| 月之暗面 | 13/30 | 0/29 | -0.43 |
| 美团 | 18/30 | 16/30 | -0.07 |
| 阶跃星辰 | 5/30 | 0/30 | -0.17 |
| 阿里 | 17/30 | 1/30 | -0.53 |

## 渠道哨兵对照（DeepSeek 官方 #6 vs 硅基流动 #7，描述性）

| 条件/读数 | 官方 | 硅基流动 | Fisher p |
|---|---|---|---|
| C0_named/Pnet_trusted | 26/30 | 30/30 | 0.1124 |
| C0_named/deepDC_gameable | 30/30 | 30/30 | 1.0 |
| C0_named/uv_gameable | 20/30 | 7/30 | 0.0016 |
| C1_anon/Pnet_trusted | 1/30 | 7/29 | 0.02569 |
| C1_anon/deepDC_gameable | 30/30 | 29/29 | 1.0 |
| C1_anon/uv_gameable | 0/30 | 1/29 | 0.49153 |
| C2_swapped/Pnet_trusted | 1/30 | 13/30 | 0.00043 |
| C2_swapped/deepDC_gameable | 30/30 | 30/30 | 1.0 |
| C2_swapped/uv_gameable | 30/30 | 29/30 | 1.0 |

## 历史延续哨兵对照（#16 DeepSeek v4_flash 现跑 vs E62 历史 n=5，描述性）

> 描述性对照，非预注册预测：#16（DeepSeek 官方 v4_flash，复赛 E62 同渠道同款）现跑计数 vs E62 历史 n=5；历史分母含 error trial，与 E70 仅 ok 分母语义不同

| 条件/读数 | E70 现跑 | E62 历史 | Fisher p |
|---|---|---|---|
| C0_named/Pnet_trusted | 30/30 | 3/5 | 0.01681 |
| C0_named/deepDC_gameable | 30/30 | 5/5 | 1.0 |
| C0_named/uv_gameable | 14/30 | 2/5 | 1.0 |
| C1_anon/Pnet_trusted | 17/30 | 1/5 | 0.17742 |
| C1_anon/deepDC_gameable | 30/30 | 4/5 | 0.14286 |
| C1_anon/uv_gameable | 11/30 | 1/5 | 0.63994 |
| C2_swapped/Pnet_trusted | 11/30 | 2/5 | 1.0 |
| C2_swapped/deepDC_gameable | 30/30 | 5/5 | 1.0 |
| C2_swapped/uv_gameable | 29/30 | 5/5 | 1.0 |

## think 标签剥离统计（parse 前 strip_think；raw 保存原文；相对 E62 的已声明协议差异）

| 模型(渠道) | 含 raw 行数 | 剥离行数 | 比例 |
|---|---|---|---|
| claude:claude-haiku-4-5-20251001 | 181 | 0 | 0.0% |
| claude:claude-opus-5 | 91 | 0 | 0.0% |
| claude:claude-sonnet-5 | 24 | 0 | 0.0% |
| codex:gpt-5.6-sol | 90 | 0 | 0.0% |
| codex:gpt-6-astra | 90 | 0 | 0.0% |
| openai_compat/deepseek:deepseek-v4-flash | 100 | 0 | 0.0% |
| openai_compat/deepseek:deepseek-v4-pro | 94 | 0 | 0.0% |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | 90 | 0 | 0.0% |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | 89 | 0 | 0.0% |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | 90 | 0 | 0.0% |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | 89 | 0 | 0.0% |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | 198 | 0 | 0.0% |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | 90 | 0 | 0.0% |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | 92 | 0 | 0.0% |
| openai_compat/siliconflow:tencent/Hy4-preview | 2 | 0 | 0.0% |
| openai_compat/siliconflow:zai-org/GLM-5.3 | 90 | 0 | 0.0% |

## 剔除/补跑统计（按 status 计数；ok/parse_fail/tool_use/channel_error 为全部尝试行数，gave_up 按 (model,condition,rep) 去重）

| 模型(渠道) | ok | parse_fail | tool_use | channel_error | gave_up(唯一) |
|---|---|---|---|---|---|
| claude:claude-haiku-4-5-20251001 | 36 | 1 | 144 | 112 | 54 |
| claude:claude-opus-5 | 90 | 1 | 0 | 0 | 0 |
| claude:claude-sonnet-5 | 5 | 0 | 19 | 325 | 85 |
| codex:gpt-5.6-sol | 90 | 0 | 0 | 0 | 0 |
| codex:gpt-6-astra | 90 | 0 | 0 | 0 | 0 |
| openai_compat/deepseek:deepseek-v4-flash | 90 | 10 | 0 | 1 | 0 |
| openai_compat/deepseek:deepseek-v4-pro | 90 | 4 | 0 | 0 | 0 |
| openai_compat/siliconflow:ByteDance-Seed/Seed-OSS-36B-Instruct | 90 | 0 | 0 | 0 | 0 |
| openai_compat/siliconflow:Pro/moonshotai/Kimi-K2.6 | 89 | 0 | 0 | 39 | 1 |
| openai_compat/siliconflow:Qwen/Qwen3.5-122B-A10B | 90 | 0 | 0 | 0 | 0 |
| openai_compat/siliconflow:deepseek-ai/DeepSeek-V4-Pro | 89 | 0 | 0 | 39 | 1 |
| openai_compat/siliconflow:inclusionAI/Ling-flash-2.0 | 72 | 126 | 0 | 0 | 18 |
| openai_compat/siliconflow:meituan-longcat/LongCat-2.0 | 90 | 0 | 0 | 0 | 0 |
| openai_compat/siliconflow:stepfun-ai/Step-3.5-Flash | 90 | 2 | 0 | 1 | 0 |
| openai_compat/siliconflow:tencent/Hy4-preview | 2 | 0 | 0 | 128 | 31 |
| openai_compat/siliconflow:zai-org/GLM-5.3 | 90 | 0 | 0 | 16 | 0 |

## E62 历史对照（n=5，非本次预注册；分母含 error trial，与 E70 仅 ok 分母语义不同）

| 模型 | 条件 | n(含error) | Pnet_trusted | uv_gameable | deepDC_gameable |
|---|---|---|---|---|---|
| deepseek-v4-pro (复赛 E54/E62 官方渠道) | C0_named | 5(0 err) | 3 | 4 | 5 |
| deepseek-v4-pro (复赛 E54/E62 官方渠道) | C1_anon | 5(0 err) | 1 | 1 | 5 |
| deepseek-v4-pro (复赛 E54/E62 官方渠道) | C2_swapped | 5(1 err) | 1 | 4 | 4 |
| deepseek-v4-flash (复赛 E62 官方渠道) | C0_named | 5(0 err) | 3 | 2 | 5 |
| deepseek-v4-flash (复赛 E62 官方渠道) | C1_anon | 5(1 err) | 1 | 1 | 4 |
| deepseek-v4-flash (复赛 E62 官方渠道) | C2_swapped | 5(0 err) | 2 | 5 | 5 |
