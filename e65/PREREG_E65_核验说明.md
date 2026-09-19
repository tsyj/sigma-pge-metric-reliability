# PREREG_E65.md 的哈希核验说明（2026-09-17 补记，repo_fixes 第二轮）

## 发生了什么
与 E67b 同一类流程错误（见 `e67/PREREG_E67b_核验说明.md`），此前未单独记录，本次入仓校验时由脚本发现：

- 预注册登记：`PREREG_E65.sha256` 记录 `7b6a2331…`，`PREREG_E65.stamp` 记录 `2026-09-04_23:42:32 CST`（/data 原件 mtime 2026-09-04T23:42:32+08:00）。
- 实验输出 `E65_SPURIOUS_VS_TRUE.json` 的 mtime 为 2026-09-04T23:43:33+08:00，其 `prereg_sha` 字段在运行时读入登记哈希，值与登记值逐位相等。
- 之后"结果与如实记录"被**追加到了同一个文件末尾**（以 `---` 分隔）；/data 原件最后一次写入时间 2026-09-04T23:53:46+08:00。
  追加段标题自述「2026-09-05 凌晨」，与文件系统时间不一致，此处以 stat 为准照录，不作推断。
- 追加之后全文哈希变为 `0afa7165…`，与登记值不再相等。

## 如何证明预测原文未被改动
登记的是**文件前 2501 字节**（全文 4435 字节，追加 1934 字节）。
该长度由脚本对全文逐前缀计算哈希、取与登记值相等的唯一前缀得到，不是手填；封存段之后紧接 1 个换行符，然后就是追加段的 `---` 分隔行。

    head -c 2501 e65/PREREG_E65.md | sha256sum      # 从仓库根目录运行
    sha256sum -c e65/PREREG_E65.sha256                    # 校验逐字节封存段 PREREG_E65.sealed_prefix.md
    cmp -n 2501 e65/PREREG_E65.sealed_prefix.md e65/PREREG_E65.md   # 封存段 = 全文前缀

三条都通过 ⇒ P1–P4 四条预测与判读规则在运行前后逐字节一致；追加段不属于预注册内容，不受哈希保护。
`scripts/smoke_test.sh` 第 1 步对 E65 与 E67b 自动执行后两条。

## 处置
原文件保持原样不动（保留证据）；结果以追加段与 `E65_SPURIOUS_VS_TRUE.json`（prereg_check: P1/P2/P4 推翻、P3 命中）为准。
生成脚本：`e71_innov/repo_fixes/scripts/fix_09_prereg_hash_paths.py`；逐份登记原始行见仓库根 `PREREG_HASH_INDEX.json`。
