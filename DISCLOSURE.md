# 依赖、授权与商业服务披露

按《赛道三参赛手册》08 节、官网 FAQ Q20 六项、复赛规则页通用披露要求逐项填写。

## 一、FAQ Q20 六项

**1. 开源/开放范围**　本仓库全部内容开源：两个探索环境（风驱 `scripts/env2.py`、内潮 `e44_tide/`）、第三/四强迫变体（`e52/` 经向风、`e55/` 45°）、BH93 静止态检验（`e56/`）、八项审计算子脚本、穷举器、Agent harness 与全部轨迹、判读与绘图脚本、参照系交付件（`baselines/`）、全部分析结果 JSON。
**不开放**：ROMS/MITgcm 的原始 `.nc` 输出（约 4 GB，见第五节）；已投出但未见刊的论文正文（本仓库只引用其数字并给出所在文件）。

**2. 开源协议**　本仓库自有代码采用 **MIT License**（见 `LICENSE`）。第三方组件各依其原协议，见第 3 项。

**3. 第三方依赖**

| 组件 | 用途 | 版本 | 协议/获取 |
|---|---|---|---|
| ROMS / COAWST | σ 坐标求解器（被审对象） | ROMS 3.9，本地编译，二进制 sha256 见 `e44_tide/audit/` 与各 `INPUTS_MD5.txt` | ROMS 为学术许可，需在 myroms.org 注册后获取源码；**本仓库不含其源码与二进制** |
| MITgcm | z 坐标独立真值 | checkpoint 见 `build_mitgcm/`，`mitgcmuv` 由源码重建 | MIT 许可，公开获取 |
| Python | 分析与绘图 | 3.9；numpy、netCDF4、matplotlib、scipy、python-docx、python-pptx、openai(SDK)、faster-whisper | 各自 BSD/MIT/Apache 类协议 |
| gfortran / OpenMPI / netCDF | 构建工具链 | gfortran 11.4.0、netCDF 4.8.1/4.9.2 | GPL/BSD |

**4. 商业 API 调用情况**　见第二节（手册 08 节五项）。
**5. 闭源模型使用情况**　仅 DeepSeek `deepseek-v4-pro`（reasoning 模型），用于三个 Agent 实验：陷阱局（目标导向）、中性措辞局、判据局/换名局。**不用于生成本报告正文、不用于生成任何被审计的数值结果**——所有数值由固定代码算出，语言模型只负责"挑下一步试什么"与"当评审给判断"。
**6. 数据来源与授权边界**　全部数据由本项目自产（ROMS/MITgcm 数值试验），无第三方数据集，无个人信息，无授权限制。地形、初值、强迫的生成脚本随包。

## 二、商业 API / 闭源模型五项（手册 08 节）

| 项 | 内容 |
|---|---|
| **调用环节** | 仅三处：① 陷阱局 6 轮 × 2 局（目标导向 + 中性措辞）；② 判据局 1 次；③ 换名局 3 条件 × 5 次 = 15 次。轨迹全文见 `e44_tide/agent/*.jsonl` 与 `RESULT_*.json`。总调用约 33 次（含重试）。 |
| **费用假设** | DeepSeek 按量计费；本项目全部 LLM 支出以账户余额变化计，量级为人民币十元级（换名局约 ¥5）。**费用不构成复现门槛**：全部结果均可在不调用 LLM 的情况下由 `scripts/reproduce_core.sh` 从已交付 JSON 重算。 |
| **权限范围** | 仅 chat completions，无文件上传、无工具调用授权、无数据留存要求；API Key 通过环境变量注入，不入库（`scripts/smoke_test.sh` 含 secret 扫描）。 |
| **可替代方案与迁移成本** | harness 走 OpenAI 兼容接口（`e44_tide/agent_tide.py::_client`），改 `LLM_BASE_URL` + `LLM_MODEL` 两个环境变量即可切换到任意兼容服务或本地开源 reasoning 模型（如 Qwen/DeepSeek-R1 系列自部署）。迁移成本 = 一次环境变量修改；**不需要改动任何判据、审计或分析代码**。 |
| **对可复现性的影响** | reasoning 模型输出**不可逐位复现**（无 seed 可控、供应商侧版本可变）。因此：(a) 全部轨迹原样存档，报告中每个 Agent 数字都指向具体 JSONL；(b) 所有**结论性数值**（判据、审计、kill board、交集）均不依赖 LLM，可零 LLM 重算；(c) 换名局报 5 次独立调用的计数而非单次结果。 |

## 三、采样参数与随机性

- LLM：`response_format={"type":"json_object"}`，`max_tokens=8000`，`timeout=300s`，最多 4 次重试；**temperature/top_p 未显式设置，使用服务端默认**（此为已知复现性缺口，如实声明）。
- 数值试验：ROMS 无随机数参与；风驱环境动作空间含 `seed` 旋钮（用于回归测试），本轮全部算例 `seed=0`。
- 随机基线：Python `random.Random(seed)`，种子 0/1/2 写死在 `e44_tide/analysis/E45_RANDOM_BASELINE.json`。
- 统计检验：置换检验为**精确枚举**（n≤8 全排列），无抽样随机性。

## 四、已有项目的使用与本次贡献范围（复赛规则页要求）

- **原项目来源**：ROMS/COAWST 与 MITgcm 均为社区开源模式；本作品的 σ-PGE 研究背景来自作者本人在投论文（未见刊，本仓库只引其数字）。
- **本次贡献范围**：不修改 ROMS/MITgcm 的数值算法；新增的是**环境层与审计层**——(K,V,H,A) 四元组接口、九档参照系、A1–A9 审计算子、穷举器、Agent harness、判读与一键复现管线。
- **新增创新点**：把评测方法学的扰动审计搬进有独立数值真值的物理环境，并给出跨强迫方向的不可迁移反例。
- **协议兼容性**：本仓库自有代码 MIT，与 ROMS 学术许可、MITgcm MIT 许可均不冲突；**本仓库不再分发 ROMS 源码或二进制**，使用者需自行按 README 获取并编译。

## 五、数据获取与体积

原始 `.nc` 输出约 4 GB，未随包。仓库内交付的是**分析级产物**（全部 JSON、审计 md5 清单、Agent 轨迹、图），`scripts/reproduce_core.sh` 可仅凭这些重算全部主结论与主图。完整重跑需按 `README_semifinal.md` 重建 ROMS/MITgcm 并按 `e44_tide/mk_case.py`、`e52/`、`e55/`、`e56/run_bh93.py` 复跑，机时估计见报告第三问。
