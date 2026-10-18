# H1-fix：归属、门引用与归档文字复核

## 处置

| 项 | 处置与边界 |
|---|---|
| M3 | README 与 A10 改引生产实体/拓扑门；原开胞手算放算例栏。A28 标“无门（仅文档算例）”，rho 手算不冒充生产门。 |
| M4 | A14 主门改为 `test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits`；原两门保留并明确仅守包含/覆盖方向、参照边界仍由生产构造。 |
| m1 | README 13 行全部与归属表的具名门集合对齐：A01/A04、A12、A16、A20、A25、A27、A30、A31–A33 补齐。 |
| m2 | A36 改“已有标准结果”，明确二维特例 Shi 2015 §6.3–6.4 / 2021 §5.3；不再列作本仓库新结果。分类规则明确这一既有数学类别，不把它硬归到五种原文关系之一。 |
| m3 | canon_map §六标题与历史 AGENTS 指针订正；m3_global 更新原文已核状态、外归档指针；历史 plan 的确定性裁决措辞加本地勘误。 |
| m4 | EVIDENCE_ARCHIVE 写明 theory_audit 文首 +197 B 唯一例外、原样全文与当前有效归属链接、原件恢复命令；Git 原字节总数改 523,273,912 B，区分归档现场 523,274,109 B。外归档未写入。 |
| m5/m26 | A39 明确位移形式 d↔−d、对独立 oracle 逐点检查；参数格互异另标 test-of-test。测试增强与节点账由根执行者处理。 |
| m6 | AGENTS 恢复 F 的五组门指针、点名纯度门、阈值先测后钉；纪律 C 明确已证明只收有生产门守护命题；basetemp 改通用本单路径，`-m slow` 必须配 `--runslow`。 |
| m7 | C1 §6 明确 2728 / 44 来自未验收封存 WIP `5e3ba68`；独立校验只近似测到，不升级为连续时间结论；保留 26 标签改变 + 18 离开严格贯入的分列。 |
| m8–m10 文档 | AGENTS 同步扩展词法扫描、词表及窄白名单理由；实现和变异由纯度子任务承担。 |
| m21/m22 | 旧路径映射覆盖当前文档/工具，先 fixtures/frozen 后外归档，并注明不意味着所有旧 CLI 自动回退；43 目录表加“转入 fixture”列，表内 134 搬迁 + 表外两项 + 一项复制 = 137。可选新增死链测试未做。 |

## 验收原样最后一行

全部测试在本工作树 `H1_evidence/tmp/fix_docs/source` 的独立字节副本执行，均显式使用 `--runslow -p no:cacheprovider --basetemp ...`，TEMP/TMP 在本单 tmp。没有跑全档或全量回放，没有修改真实生产文件或外归档。

| 运行 | 原样最后一行 | 解释 |
|---|---|---|
| README 27 个不同具名测试 | `96 passed in 45.17s` | 13 行引用均存在且原版绿。 |
| M3 原版 + 两个算例 | `24 passed in 0.36s` | 22 个生产参数节点与 2 个纯算例。 |
| M4 原版 | `15 passed in 1.14s` | 主门 6 格 + 原包含门 9 格。 |
| M3 生产路径抛错变异 | `22 failed, 2 passed in 0.43s` | 22 个新引用节点均确实运行生产路径；2 手算仍绿，正是不能充当生产门的依据。 |
| M4 完全取消裁剪 | `6 failed, 9 passed in 0.87s` | 主门 6 格全部在 `cover clipping exposure mismatch` 断言红；旧覆盖门 9 格仍绿。 |

[验证 JSON](verification.json)；[原版日志](readme_cited_pristine.log)；[M3 变异日志](m3_production_poison.log)；[M4 变异日志](m4_no_clipping.log)。

最终文档核对：[documentation_audit.json](documentation_audit.json)。65 行 README；39 行归属；13/13 README 行门集合与归属一致；43/43 外归档清单 SHA 未变；theory_audit 正文与 `1ce9a91` 一致、仅文首 +197 B；137/137 fixture 完整性哈希一致。本轮没有再次遍历哈希 274,740 个外归档数据文件，不把清单核对冒充重新全量数据核对。

## 修改文件

仅 8 份现行文档；无新增或删除 pytest 节点，修改前后哈希与行数见 [documentation_edits.json](documentation_edits.json)。

- [README](file:///D:/eab-wt/cx-e2/README.md)
- [归属表](file:///D:/eab-wt/cx-e2/docs/shi_attribution.md)
- [AGENTS](file:///D:/eab-wt/cx-e2/AGENTS.md)
- [canon_map](file:///D:/eab-wt/cx-e2/docs/canon_map.md)
- [M3 设计](file:///D:/eab-wt/cx-e2/docs/m3_global_entrance_design.md)
- [历史计划本地勘误](file:///D:/eab-wt/cx-e2/docs/plan_20260921.md)
- [C1 理论文档](file:///D:/eab-wt/cx-e2/docs/m5d_c1_theory.md)
- [归档索引](file:///D:/eab-wt/cx-e2/reports/EVIDENCE_ARCHIVE.md)

回退锚为所有者提交 `476c5d6`；本子任务只读 Git，不暂存、不提交、不回退文件。
