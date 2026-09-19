# 谁来给尺子打分

在海山数值试验中检验代理指标：既要与参照解排序一致，也要通过平底配对检验。AI 在实验中挑动作、挑指标或给出判断，数值由固定脚本计算。

准备 Python 3.9–3.12，以下三条命令依次执行（安装时固定 NumPy 2.0.2，与冻结数值实现一致）：

```bash
git clone https://github.com/tsyj/sigma-pge-metric-reliability.git && cd sigma-pge-metric-reliability
python3 -m venv .venv && .venv/bin/python -m pip install . && PYTHON=.venv/bin/python nice -n 19 bash scripts/demo_60s.sh
nice -n 19 .venv/bin/python -m sigma_audit submit 'u|s50|mean_abs / v|s50|rms'
```

当前为决赛工作区准备版，上述入口随本轮文件交付；公开远端是否包含本版须以发布后的验证为准。安装需要获取 Python 依赖，安装后的演示与送检使用随包缓存，无需模型服务或原始模式输出。线程统一限制为 8。

## 可以复算什么

送检台给出纬向、经向及 45° 风向上的排序、配对检验和扣除伪流成分后的读数。只覆盖随包环境族及缓存可表达的指标；参照解由另一套代码 MITgcm 计算，不能据此归因于垂向坐标这一项差别。

```bash
PYTHON=.venv/bin/python nice -n 19 bash scripts/reproduce_core.sh
PYTHON=.venv/bin/python nice -n 19 bash scripts/smoke_test.sh
nice -n 19 .venv/bin/python -m sigma_audit selftest
nice -n 19 .venv/bin/python -m sigma_audit replay
```

Demo 中的预测统计仅覆盖 E55–E61 五组实验。历史三环境交集计数保留供对账；交集为空不作为跨环境不可能性的证据。BH93 静止态幅度检验不能直接挪作风驱技巧评分。

## 数据与出处

- [RUNS_MANIFEST](RUNS_MANIFEST.md)：从五份扫描账本生成条数、完成状态与出处；不是全项目所有运行的总数。
- [送检台说明](docs/SIGMA_AUDIT.md)：缓存范围、校验方式及离线测试。
- [模型与数据披露](DISCLOSURE.md)：实验模型、渠道及未完成核验项。
- [预注册索引](PREREG_HASH_INDEX.json)：E65/E67b 校验封存段及全文前缀，不能称整文件封存。

重新生成清单：`nice -n 19 .venv/bin/python scripts/gen_runs_manifest.py`。预注册哈希是本地一致性证据；后续公开时间不能证明历史封存时间，同一执行链的自检也不构成外部复核。

自有代码采用 [MIT](LICENSE)，自产分析数据采用 [CC BY 4.0](LICENSE-DATA)。ROMS 的本地许可原文为 [MIT/X](docs/licenses/License_ROMS.txt)，其他组件各依原许可。引用格式见 [CITATION.cff](CITATION.cff)。
