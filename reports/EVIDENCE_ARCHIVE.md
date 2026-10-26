# 证据外部归档（WO-H1，2026-10-19）

历史报告正文不逐个改链接；同一映射规则也适用于当前 docs/README/AGENTS 与工具中残留的历史路径。对旧 `reports/<相对路径>`，**先查**仓库内 `fixtures/frozen/<去掉 reports/ 的原路径>`，存在则作为冻结输入使用；**否则再查** `D:/eab-evidence/<完整旧路径>`。例如 `reports/codex/M5b_evidence/endpoint_inputs/…` 优先解析到 `fixtures/frozen/codex/M5b_evidence/endpoint_inputs/…`，而 `reports/codex/M3_evidence/theory_audit.md` 解析到外归档。H1 当前运行目录不归档；仍在仓库的当前文件不走历史映射。
该规则是路径迁移说明，不声称所有旧 CLI 都自动回退到外归档；测试固定输入由 `tools/frozen_evidence.py` 解析，旧全量命令如需历史输出应由所有者按映射准备，不在本单重跑。冻结输入原字节保留，嵌入的历史路径/哈希不重写。
保留仓库内的报告正文、当前 `reports/codex/inputs/`、本单 H1 证据及其他小型索引；不重写 Git 历史。

- 首批测试输入：136 文件，11,662,520 字节已搬入 fixtures；[初批专属清单](codex/H1_evidence/frozen_inputs_initial_136.json)（从当前总清单减去明确追加项复原，逐文件行未改）。
- 外归档：32 目录，实际 274,244 文件、20,061,143,706 字节（含旧 ignored 临时/沙箱产物）；其中已归档的 Git 跟踪文件 5,551 个，归档现场字节 521,250,702；`1ce9a91` 原 blob 字节 521,250,505（相差下述勘误行 197 B）。
- 每目录清单含原相对路径、字节数、SHA256、是否原 Git 跟踪；巨大清单只存仓库外。
- 验证：搬迁前逐文件 SHA256；同卷目录 rename 保留归档时字节（相对 `1ce9a91` 的唯一例外见下节）；搬迁后逐文件存在性/长度核对。输入迁移另外重算目标 SHA256；无覆写与无删除操作。
- 归档脚本：[tools/h1_archive_evidence.py](../tools/h1_archive_evidence.py)；[机器结果](codex/H1_evidence/archive_result.json)。

| 原目录 | 实际文件数 | 实际字节 | 已归档跟踪文件数 | 归档现场跟踪字节 | 转入 fixture | SHA256 逐文件清单 |
|---|---:|---:|---:|---:|---:|---|
| `reports/codex/E2_evidence` | 250 | 1,373,863 | 97 | 1,018,251 | 0 | [reports__codex__E2_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E2_evidence.sha256.jsonl) |
| `reports/codex/E3E4_evidence` | 257 | 5,125,829 | 137 | 4,209,859 | 0 | [reports__codex__E3E4_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E3E4_evidence.sha256.jsonl) |
| `reports/codex/E5a2_evidence` | 758 | 19,524,060 | 229 | 14,755,975 | 0 | [reports__codex__E5a2_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E5a2_evidence.sha256.jsonl) |
| `reports/codex/E5a_evidence` | 990 | 13,908,187 | 193 | 5,531,982 | 0 | [reports__codex__E5a_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E5a_evidence.sha256.jsonl) |
| `reports/codex/E5b_evidence` | 560 | 9,655,072 | 305 | 9,022,482 | 0 | [reports__codex__E5b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E5b_evidence.sha256.jsonl) |
| `reports/codex/INT1_evidence` | 151 | 718,037 | 151 | 718,037 | 0 | [reports__codex__INT1_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__INT1_evidence.sha256.jsonl) |
| `reports/codex/M3_evidence` | 22,897 | 2,250,334,257 | 89 | 1,343,958 | 0 | [reports__codex__M3_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M3_evidence.sha256.jsonl) |
| `reports/codex/M3b_evidence` | 179 | 1,684,890 | 179 | 1,684,890 | 0 | [reports__codex__M3b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M3b_evidence.sha256.jsonl) |
| `reports/codex/M3c_evidence` | 105 | 258,424 | 105 | 258,424 | 0 | [reports__codex__M3c_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M3c_evidence.sha256.jsonl) |
| `reports/codex/M4a_evidence` | 84 | 2,694,906 | 84 | 2,694,906 | 1 | [reports__codex__M4a_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M4a_evidence.sha256.jsonl) |
| `reports/codex/M4b_evidence` | 30 | 343,538 | 30 | 343,538 | 0 | [reports__codex__M4b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M4b_evidence.sha256.jsonl) |
| `reports/codex/M4c_evidence` | 36,792 | 3,585,974,700 | 388 | 3,989,846 | 32 | [reports__codex__M4c_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M4c_evidence.sha256.jsonl) |
| `reports/codex/M5a2_evidence` | 34,708 | 3,290,853,547 | 377 | 1,274,766 | 0 | [reports__codex__M5a2_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5a2_evidence.sha256.jsonl) |
| `reports/codex/M5a_evidence` | 15,536 | 1,452,456,181 | 121 | 703,929 | 0 | [reports__codex__M5a_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5a_evidence.sha256.jsonl) |
| `reports/codex/M5b_evidence` | 17,014 | 1,587,625,943 | 92 | 682,890 | 95 | [reports__codex__M5b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5b_evidence.sha256.jsonl) |
| `reports/codex/M5c_evidence` | 22,575 | 1,549,886,215 | 98 | 2,906,500 | 3 搬迁 + 1 复制 | [reports__codex__M5c_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5c_evidence.sha256.jsonl) |
| `reports/codex/M5d_evidence` | 19,509 | 1,505,727,055 | 102 | 4,515,024 | 3 | [reports__codex__M5d_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5d_evidence.sha256.jsonl) |
| `reports/codex/M5e_evidence` | 40,086 | 2,382,095,499 | 0 | 0 | 0 | [reports__codex__M5e_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5e_evidence.sha256.jsonl) |
| `reports/codex/M5f_evidence` | 40,285 | 1,403,719,378 | 0 | 0 | 0 | [reports__codex__M5f_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5f_evidence.sha256.jsonl) |
| `reports/codex/PERF_evidence` | 520 | 11,271,956 | 258 | 10,637,992 | 0 | [reports__codex__PERF_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__PERF_evidence.sha256.jsonl) |
| `reports/codex/R10FIX_evidence` | 411 | 5,020,313 | 273 | 4,514,973 | 0 | [reports__codex__R10FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R10FIX_evidence.sha256.jsonl) |
| `reports/codex/R11FIX_evidence` | 746 | 5,639,361 | 373 | 4,603,848 | 0 | [reports__codex__R11FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R11FIX_evidence.sha256.jsonl) |
| `reports/codex/R12FIX_evidence` | 779 | 101,644,612 | 124 | 55,480,495 | 0 | [reports__codex__R12FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R12FIX_evidence.sha256.jsonl) |
| `reports/codex/R12FIXb_evidence` | 2,524 | 105,028,673 | 518 | 75,962,260 | 0 | [reports__codex__R12FIXb_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R12FIXb_evidence.sha256.jsonl) |
| `reports/codex/R13FIX_evidence` | 3,109 | 200,078,361 | 123 | 25,526,019 | 0 | [reports__codex__R13FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R13FIX_evidence.sha256.jsonl) |
| `reports/codex/R13FIXb_evidence` | 3,551 | 110,528,236 | 173 | 28,711,823 | 0 | [reports__codex__R13FIXb_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R13FIXb_evidence.sha256.jsonl) |
| `reports/codex/R14FIX_evidence` | 4,382 | 133,382,384 | 185 | 38,210,567 | 0 | [reports__codex__R14FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R14FIX_evidence.sha256.jsonl) |
| `reports/codex/R15FIX_evidence` | 3,747 | 128,365,388 | 129 | 32,467,477 | 0 | [reports__codex__R15FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R15FIX_evidence.sha256.jsonl) |
| `reports/codex/R6FIX_evidence` | 491 | 12,678,140 | 175 | 11,945,094 | 0 | [reports__codex__R6FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R6FIX_evidence.sha256.jsonl) |
| `reports/codex/R7FIX_evidence` | 298 | 26,447,626 | 107 | 25,819,120 | 0 | [reports__codex__R7FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R7FIX_evidence.sha256.jsonl) |
| `reports/codex/R8FIX_evidence` | 311 | 48,515,676 | 170 | 48,158,630 | 0 | [reports__codex__R8FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R8FIX_evidence.sha256.jsonl) |
| `reports/codex/R9FIX_evidence` | 609 | 108,583,399 | 166 | 103,557,147 | 0 | [reports__codex__R9FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R9FIX_evidence.sha256.jsonl) |

## theory_audit.md 唯一字节例外与勘误全文

6047 个已归档跟踪文件中，6046 个与 `1ce9a91` 原 blob 逐字节一致；唯一例外是 [theory_audit.md](file:///D:/eab-evidence/reports/codex/M3_evidence/theory_audit.md)，依 WO-H1 P0.3 在正文前加了 197 B 的勘误行，正文未改。原件可只读 `git show 1ce9a91:reports/codex/M3_evidence/theory_audit.md` 恢复；本轮不改外归档文件或清单。两种总字节口径不可混用。

归档中该行的**原样全文**如下；其历史相对链接会错指外归档根下不存在的 docs，因此在此保留可提交、可审阅的全文并给出当前有效的 [归属总表](../docs/shi_attribution.md)，不偷偷修外部字节：

```markdown
> 勘误（2026-10-19）：石根华两篇原文已核；本报告正文保留历史状态，现行理论归属与 cutting/转动范围订正见 [归属总表](../../../docs/shi_attribution.md)。
```

“转入 fixture”列中的搬迁项不包含在“已归档跟踪文件数”中：表内 134 项为搬迁，表外根级 `reports/bb52_g0_first_look.json` 与 `reports/g2_bdda3d.json` 另搬迁 2 项；另 1 项 `M5c_evidence/research_diagnostics.json` 为复制，仍计入外归档原件。合计 136 搬迁 + 1 复制，总数以 [137 项清单](codex/H1_evidence/frozen_inputs_manifest.json) 为准。

## 验证与回退

`archive_result.json` 另记录每份清单自身的 SHA256。如需回退，先确认原路径不存在，再依据清单将目标目录移回原位置，并把 fixtures/frozen 输入移回其 source；不得覆盖所有者后续生成的数据。归档是本地原字节保存，不是远端备份。

## 追加：历史对抗复现与展示产物

运行输入依赖扫描未发现 G6F–G6O 复现目录的生产/测试/工具引用；这些目录及 showcase 作为历史证据原字节外移，不执行旧复现。旧 `reports/<相对路径>` 映射为 `D:/eab-evidence/reports/<相对路径>`。

追加 11 目录、496 文件、2,023,407 字节；两批合计 43 目录、274,740 文件、20,063,167,113 字节，其中已归档的原 Git 跟踪文件 6,047 个；**Git 真值（`1ce9a91` 原 blob）为 523,273,912 B**，归档现场为 523,274,109 B（+197 B 勘误行）。

[依赖审计](codex/H1_evidence/g6_repro_dependency_audit.json)；[追加归档结果](codex/H1_evidence/archive_additional_result.json)。

| 原目录 | 实际文件数 | 实际字节 | 已归档跟踪文件数 | 归档现场跟踪字节 | 转入 fixture | SHA256 逐文件清单 |
|---|---:|---:|---:|---:|---:|---|
| `reports/codex/inputs/G6F_repro` | 50 | 146,381 | 50 | 146,381 | 0 | [reports__codex__inputs__G6F_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6F_repro.sha256.jsonl) |
| `reports/codex/inputs/G6G_repro` | 73 | 166,238 | 73 | 166,238 | 0 | [reports__codex__inputs__G6G_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6G_repro.sha256.jsonl) |
| `reports/codex/inputs/G6H_repro` | 70 | 177,442 | 70 | 177,442 | 0 | [reports__codex__inputs__G6H_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6H_repro.sha256.jsonl) |
| `reports/codex/inputs/G6I_repro` | 58 | 163,297 | 58 | 163,297 | 0 | [reports__codex__inputs__G6I_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6I_repro.sha256.jsonl) |
| `reports/codex/inputs/G6J_repro` | 43 | 113,774 | 43 | 113,774 | 0 | [reports__codex__inputs__G6J_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6J_repro.sha256.jsonl) |
| `reports/codex/inputs/G6K_repro` | 42 | 86,370 | 42 | 86,370 | 0 | [reports__codex__inputs__G6K_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6K_repro.sha256.jsonl) |
| `reports/codex/inputs/G6L_repro` | 20 | 67,042 | 20 | 67,042 | 0 | [reports__codex__inputs__G6L_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6L_repro.sha256.jsonl) |
| `reports/codex/inputs/G6M_repro` | 36 | 122,865 | 36 | 122,865 | 0 | [reports__codex__inputs__G6M_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6M_repro.sha256.jsonl) |
| `reports/codex/inputs/G6N_repro` | 45 | 172,597 | 45 | 172,597 | 0 | [reports__codex__inputs__G6N_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6N_repro.sha256.jsonl) |
| `reports/codex/inputs/G6O_repro` | 51 | 206,856 | 51 | 206,856 | 0 | [reports__codex__inputs__G6O_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6O_repro.sha256.jsonl) |
| `reports/showcase` | 8 | 600,545 | 8 | 600,545 | 0 | [reports__showcase.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__showcase.sha256.jsonl) |

### 留在 reports 的文件类别

- 历史 `*_report.md` 正文与小型文字/JSON 汇总：保留为证据导航，不重新计算或更新历史结论。
- `reports/codex/inputs/` 的 Shi 双读者/对照材料、历史 findings JSON 与审查报告：文档性输入保留；十个 `_repro` 子目录已外移。
- `reports/codex/H1_evidence/`：本工单的计划、审计清单、迁移映射与当前验证；ignored 临时目录不属于可交付文件。
- 根 `reports/` 的小型报告/指标记录及本归档索引：未把它们冒作当前运行证据；实际测试输入已按清单移到 fixtures。

## WO-T1a 验收返修追加（2026-10-19）

Claude 本轮明确批准写入 `D:/eab-evidence/reports/codex/T1a_evidence/`。原 272 个大证据文件共 **95,543,532 B** 已按“复制 → 两端逐文件 SHA256 → 再核源文件 → 删除本树原文件”的顺序外归档；没有覆盖不等字节的目标，没有递归删除目录。每条记录含旧相对路径、新绝对路径、长度与 SHA，外归档另存同一清单。

- [逐文件清单](codex/T1a_evidence/accept_fix/archive_original.json)；[外归档清单](file:///D:/eab-evidence/reports/codex/T1a_evidence/_manifests/archive_original.json)。
- 包括旧正式批（保留本树小型 readback.json）、旧 smoke、48 例诊断、36 格扫描、幅值再试和两个手装探针。旧 binary64 批不留在当前 fixtures 或报告目录里；原始历史字节仅在外归档。
- [归档工具](../tools/tia2d_archive_evidence.py) 限定本树 T1a_evidence 源及本次批准的外目标。图工具通过 `frozen_evidence.data_path` 读取：fixtures 优先，仍存在的当前文件保持原位置，否则按历史路径查外归档。
- 新正式输入移入 `fixtures/eab2_cases/tia2d-2/`，gzip−9、mtime=0；内容 SHA 与压缩 SHA 分开，来源见 [PROVENANCE](../fixtures/PROVENANCE.json)。包装与后续归档的实测数见 [T1a 报告](codex/T1a_report.md)。
- 二级历史证据另移 81 文件、962,073 B：[本树清单](codex/T1a_evidence/accept_fix/archive_secondary.json)、[外清单](file:///D:/eab-evidence/reports/codex/T1a_evidence/_manifests/archive_secondary.json)。包括历史 resume 数据、两次中间变异运行、完整真圆探针；保留文献核读笔记和本轮最终摘要。
- 新正式批原始 JSON、Python-only、计时进度另移 176 文件、81,175,040 B：[本树清单](codex/T1a_evidence/accept_fix/archive_formal_v2.json)、[外清单](file:///D:/eab-evidence/reports/codex/T1a_evidence/_manifests/archive_formal_v2.json)。三批合计 529 文件、177,680,645 B；不包括留在 fixtures 的 165 个 gzip 分片（4,581,793 B）及其索引。新批内容 SHA 按解压字节核验，gz SHA 另列；完整加强回读摘要留在本树。
- 历史门摘要再移61文件、163,738 B：[本树清单](codex/T1a_evidence/accept_fix/archive_historical_summaries.json)、[外清单](file:///D:/eab-evidence/reports/codex/T1a_evidence/_manifests/archive_historical_summaries.json)。本轮四批总计 **590文件、177,844,383 B**；当前快档/全档/无Git摘要仍保留本树，历史原文不混称当前验证。
- **没有改写 Git 历史**。`b0c1cbf` 仍含旧大 blob；Claude 将从 `fc9675c` 重建干净提交。本轮工作树布局正确不等于历史体积已被清除。

回退仅可按清单在旧路径不存在时复制对应外归档字节，并重新核 SHA；不得覆盖所有者后续文件。外归档为本地原字节副本，不称远端备份。

## 晚发现的测试输入与最终核对

快档实跑发现 `M5c_evidence/research_diagnostics.json` 也是固定门输入：从外归档原字节**复制**到 `fixtures/frozen/codex/M5c_evidence/research_diagnostics.json`，782,733 字节，外归档原件及其 SHA256 清单均未修改。最终输入为 **136 搬迁 + 1 复制 = 137 文件，12,445,253 字节**；不重算冻结数据。

[追加映射](codex/H1_evidence/frozen_inputs_addendum.json)；[当前完整输入清单](codex/H1_evidence/frozen_inputs_manifest.json)；[最终校验](codex/H1_evidence/archive_validation.json)。`archive_result.json` 的 `input_manifest` 是当时读取的路径（当时为 136 项），不是现已追加为 137 项的内容快照；初批专属清单明确记录复原方法，不伪称有未保存的原清单文件哈希。回退时，追加复制项的原件已在外归档，不应再次覆盖它。

单文件上限为 1,000,000 字节；唯一例外是本单冻结、只准机械重键的 `tools/exact_construction_policy.json`。具名门见 [test_repository_size.py](../tests/test_repository_size.py)，包含无 Git 副本中实际写入 1,000,001 字节文件后报红的牙。

## WO-T1b 原轮追加（2026-10-22；历史状态，续单见下节）

获准外目录为 `D:/eab-evidence/reports/codex/T1b_evidence/`，未触碰其他工作树。新大证据直接写外部；H1日志与执行清单采用gzip（mtime=0），压缩后逐字节解压核对，不删除原始临时文件。不改历史T1a数据或来源哈希。

- [外部逐文件SHA256清单](file:///D:/eab-evidence/reports/codex/T1b_evidence/_manifests/t1b_files.sha256.jsonl)；[文件数/总量/清单自身SHA](codex/T1b_evidence/external_archive_summary.json)。清单不包括自身与runtime tmp。
- [P0最终数据](file:///D:/eab-evidence/reports/codex/T1b_evidence/p0_final.json)：36燕尾政策组合、4凸耳、72逐内块条目、8标准例；完整有理输入/路径/界。探索 `p0_tolerance.json` 不混作最终数据。
- [P1最终36例](file:///D:/eab-evidence/reports/codex/T1b_evidence/p1_final_20261022/)：gzip逐例精确LP与一阶证书、来源前后清单、进度与完成标记。`p1_scan_20261022`仅为早期探索。
- [门日志映射及双SHA](codex/T1b_evidence/gate_archive.json)：开工全档GREEN、收尾快档GREEN、收尾全档**RED**原日志均保留，不拼接成新绿。
- [源码字节快照](codex/T1b_evidence/source_snapshots.json)：全档RED的完整字节导出，以及只修复两份测试helper后的 `postfix_NOT_FULL_VERIFIED_source.zip`；均1154文件、逐成员清单另存。后者没有完整全档复验，不能因其ZIP完整性正确而称验证通过。
- [无Git字节副本](file:///D:/eab-evidence/reports/codex/T1b_evidence/no_git_postfix/)；[修复后摘要](codex/T1b_evidence/no_git_postfix_summary.json)。无`.git`、PATH中无git；不是新鲜Git worktree/克隆。
- [回滚锚点](codex/T1b_evidence/rollback.json)：原设计、静态准入、适配器、纯度门与本台账原字节，均与开工HEAD比对。只能在确认没有所有者后续改动后人工恢复，不自动覆盖。

当前只交付Python诊断格式，没有新建正式tia2d-2 C++批次或自行改schema。完整结果、订正与未完成验收项见 [T1b报告](codex/T1b_report.md)；修复后完整快档已GREEN，四分片及Claude独立核查仍待安排，不能将快档或局部复核冒作最终全绿。外目录是本地保存，不是远端备份。

## WO-T1b 第一轮验收续单归档（e757883 后字节；历史快照）

本轮仅在获准的 `T1b_evidence/acceptance_fix/` 新建证据，不覆盖原P0/P1冻结数据或原RED日志；未执行Git写操作。Claude所报原提交新鲜树14848通过及独立A/B核验，按[入口记录](codex/T1b_evidence/acceptance_fix/intake.json)保留来源，不伪称本代理重跑。

- [本轮外部逐文件SHA256](file:///D:/eab-evidence/reports/codex/T1b_evidence/acceptance_fix/_manifests/files.sha256.jsonl)：109文件、44,877,378字节；清单自身SHA `de0f69682b0a13846cbcb5c9310e426b70ca409e1fc07ee09df9d400dd98afdf`，清单目录自身不列入。包含只读e757883回滚archive、验收原脚本、三点升级证书、39厚度样本/18厚块对照、开发期输出及最终完整门日志。
- [外归档摘要](codex/T1b_evidence/acceptance_fix/external_archive_summary.json)、[门日志映射及双SHA](codex/T1b_evidence/acceptance_fix/gate_archive.json)。日志gzip采用mtime=0，逐个解压与原日志相等；原日志未删，不拼接。
- [本次全档受测源码ZIP](file:///D:/eab-evidence/reports/codex/T1b_evidence/acceptance_fix/acceptance_full_source.zip)及[逐成员SHA](file:///D:/eab-evidence/reports/codex/T1b_evidence/acceptance_fix/acceptance_full_source_manifest.json)：完整工作字节导出，不是新建Git树；最终报告/本索引的收尾更新不改变受测代码。
- [当前快档](codex/T1b_evidence/acceptance_fast/summary.json)与[当前四片全档](codex/T1b_evidence/acceptance_full/summary.json)均GREEN：分别8851、14935项，0失败/跳过、模块实际执行66/66、静态0违例。
- [本轮全部文件链接](codex/T1b_evidence/acceptance_fix/artifacts.md)、[当前字节清单](codex/T1b_evidence/acceptance_fix/artifact_manifest.json)、[净增及卫生](codex/T1b_evidence/acceptance_fix/hygiene.json)。旧轮清单/状态仅描述原快照；本轮最终结论以[T1b报告](codex/T1b_report.md)为准。

本地外归档不等于远端备份；回滚不得覆盖所有者后续变化。未增加正式C++批次、未改tia2d-2 schema、未擅自冻结新增助手接口。可选C未做，不构成本单PARTIAL。

## WO-T1b 第二轮m4b返修归档（773b760 后未提交字节）

本轮只补同一凹障碍内部跨凸片的端点式变异测试与两处措辞；原生产核验器正确，未改生产代码/B数据/schema/静态准入，未执行Git写操作。上一节8851/14935为第一轮历史快照，当前新增测试另以完整门核验。

- [入口及三份原字节回滚备份清单](codex/T1b_evidence/acceptance_recheck_m4b/intake.json)：初始HEAD773b760且干净；对手脚本只读复制，不在用户Temp目录运行或写入。
- [独立源码变异核验](codex/T1b_evidence/acceptance_recheck_m4b/m4b_process_audit.json)：原版绿，原版对手脚本注入m4b后同一语义门红，正确命中假困住断言。
- [当前快档](codex/T1b_evidence/m4b_fast/summary.json)、[当前全档四片](codex/T1b_evidence/m4b_full/summary.json)：8853/14937项均GREEN，0失败/跳过、实际执行66/66、静态0违例。
- [外部逐文件SHA256](file:///D:/eab-evidence/reports/codex/T1b_evidence/acceptance_recheck_m4b/_manifests/files.sha256.jsonl)：171文件、24,589,094字节，清单SHA `3725f6e3587a8f78446a7938621cf35435b9843435dab6302769149b48b5e1e0`；排除清单目录自身。包含原字节回滚备份、验收脚本及隔离变异副本、日志和受测源码；均在获准外目录。
- [外归档摘要](codex/T1b_evidence/acceptance_recheck_m4b/external_archive_summary.json)、[门日志映射及双SHA](codex/T1b_evidence/acceptance_recheck_m4b/gate_archive.json)：gzip mtime=0，解压逐字节等于原日志；不删除原日志，不拼接。
- [当前全档受测源码ZIP](file:///D:/eab-evidence/reports/codex/T1b_evidence/acceptance_recheck_m4b/m4b_full_source.zip)、[逐成员SHA](file:///D:/eab-evidence/reports/codex/T1b_evidence/acceptance_recheck_m4b/m4b_full_source_manifest.json)：当前工作树字节导出，不是新建Git树；最终报告/本索引回填不改变受测代码。
- [全部本轮文件链接](codex/T1b_evidence/acceptance_recheck_m4b/artifacts.md)、[当前文件SHA](codex/T1b_evidence/acceptance_recheck_m4b/artifact_manifest.json)、[受测字节审计](codex/T1b_evidence/acceptance_recheck_m4b/final_tested_source_audit.json)、[净增/卫生](codex/T1b_evidence/acceptance_recheck_m4b/hygiene.json)。最终结论见[T1b报告§6.4](codex/T1b_report.md#64-第二轮复验同一凹障碍内跨片的端点式变异)。

外归档仅为本地保存，不等于远端备份；回滚不得覆盖所有者后续修改。C仍为可选项，不记PARTIAL；旧轮RED及所有来源哈希保留。

## WO-C3L1 验收返修归档（84d514e 后未提交字节）

Claude 本次仅授权外写 `D:/eab-evidence/reports/codex/C3L1_evidence/`。按 LP/ABI 验收第(4)节三清单迁移：旧轮219文件中81个小型摘要/必要日志留仓，136个原文件（11,949,974 B）外移，2个正式重放文件改为gzip−9、mtime=0；10个待更新报告/索引另存原字节副本，不混入“外移”数量。旧三个repair差分选用获准的外归档方案，当前返修差分只保留新的权威gzip。

- [逐文件旧路径/新路径/长度/SHA256及双SHA压缩记录](codex/C3L1_evidence/acceptance_fix/archive_manifest.json)；[外部相同清单](file:///D:/eab-evidence/reports/codex/C3L1_evidence/_manifests/archive_original.json)。
- [原始验收全文](file:///D:/eab-evidence/reports/codex/C3L1_evidence/acceptance_review/C3L1_acceptance.md)；[入口与回退锚](codex/C3L1_evidence/acceptance_fix/intake.json)。Claude所报84d514e新鲜树全绿及两路0 critical/0 major，以该输入记录来源，不冒称本代理亲自重跑。
- 每个外移文件执行“复制 → 目标逐字节/SHA核对 → 再核源 → 单文件unlink”，未覆盖不等字节目标，未递归删除。gzip逐个解压等于原字节；旧SHA原样保留。过期 `test_eab2_c3l1_before_static_repair.py` 已外归档，不再作为本树可收集测试。
- 历史H1原始执行记录及脚本在外归档同相对路径，原哈希见 [raw_log_archive.json](codex/C3L1_evidence/raw_log_archive.json)。原脚本是历史快照，不在外部位置直接执行其旧相对路径假设。
- [返修定向红/绿及对手脚本原字节清单](codex/C3L1_evidence/acceptance_fix/preflight_archive.json)；最终门与新的原始记录映射将在 [C3L1报告](codex/C3L1_report.md) 和 [交付索引](codex/C3L1_evidence/deliverables.md) 收口。

不改Git历史；工作字节瘦身不等于84d514e旧大blob已从历史清除。外目录是本地归档，不称远端备份。回退仅在原路径不存在时依清单复制并核SHA，禁止覆盖所有者后续修改。

### C3L1 本次最终门与归档索引

完整重建及12阶段固定字节收尾全部GREEN，快/全H1使用本树字节导出，不冒称新的Git树。新的逐分片日志/执行多重集/来源清单在C3L1外归档 `acceptance_runs/`；每个gzip均level9、mtime=0、解压原SHA相等，原ignored临时日志不混作入库材料。

- [本轮最终归档映射与双SHA](codex/C3L1_evidence/acceptance_fix/final_archive.json)；[外部相同清单](file:///D:/eab-evidence/reports/codex/C3L1_evidence/_manifests/acceptance_final_archive.json)。
- [完整最终流水账](codex/C3L1_evidence/acceptance_fix/acceptance_final_run.json)；[当前权威交付索引](codex/C3L1_evidence/deliverables.md)；[当前文件SHA](codex/C3L1_evidence/artifact_manifest.json)；[链接/哈希/执行集合审计](codex/C3L1_evidence/delivery_integrity.json)。
- [工作字节净增/单文件卫生](codex/C3L1_evidence/acceptance_fix/hygiene.json)：相对7540cde按当前拟交付字节计，不是Git pack/history体积。

## WO-C3L3（1b6b4f3 后未提交字节，2026-10-23）

本节保留原交付时的历史状态与路径；`c8718bb` 后验收事实及当前差分权威见下一节，旧差分路径按下一节精确映射读取归档。

P0/P1 实现及本单验证、P2 实测交付；所有者新鲜 Git 树与 Claude 一路独立对抗核查尚未执行，不签里程碑 DONE。

- [中文报告](codex/C3L3_report.md)、[交付索引](codex/C3L3_evidence/deliverables.md)、[当前文件 SHA](codex/C3L3_evidence/artifact_manifest.json)、[卫生账](codex/C3L3_evidence/hygiene.json)。
- [开工全档](codex/C3L3_evidence/baseline/summary.json)、[收尾快档](codex/C3L3_evidence/final_fast/summary.json)、[收尾全档四片](codex/C3L3_evidence/final_full/summary.json)：15035 / 8972 / 15056 项 GREEN，0 failed/skip，逐模块实际执行完备，两个全档静态 0 违例。使用工作树字节导出，非新建 Git 树。
- [唯一权威差分](codex/C3L3_evidence/differential.json)：217 limit、171 critical（含1个不支持参数调用错误），0失配；[规模报告](codex/C3L3_evidence/scale.json)：60行/1441列，非性能门。
- [原始日志/执行节点/回退字节/隔离变体归档映射及双 SHA](codex/C3L3_evidence/archive_manifest.json)：102 文件、原始 45,501,105 B；gzip level9、mtime=0，逐文件解压原 SHA 相等，保留 ignored 原临时日志，不拼接运行。旧轮差分仅归档，不冒充最后源码绿。
- [受测完整源码 ZIP](file:///D:/eab-evidence/reports/codex/C3L3_evidence/run_20261023/final_full_tested_source.zip)：1845成员，逐成员 SHA 核验；[外部相同映射](file:///D:/eab-evidence/reports/codex/C3L3_evidence/run_20261023/archive_manifest.json)。
- [受测字节与交付完整性](codex/C3L3_evidence/delivery_integrity.json)：全档后只回填报告/本索引及证据，不改受测源码。

只向本单新路径追加，不删除原证据、不写 Git。外目录为本地保存，不等于远端备份；回滚须核对所有者后续修改。

## WO-C3L3 验收返修（c8718bb 后未提交字节）

Claude 提供 c8718bb 新鲜树构建/五层差分/全档15056绿及两路验收全文：静力路0缺陷，临界路1 major门缺口、2 minor；来源与SHA见[返修入口](codex/C3L3_repair_evidence/intake.json)。这是所有者提供的基线，不冒称本代理重跑其新鲜树。

- [原 c8718bb 证据逐文件原SHA/压缩SHA与归档路径](codex/C3L3_repair_evidence/previous_archive.json)。旧 differential.json/log/progress 三文件复制、解压核字节及源SHA后逐文件移出工作树；其余旧摘要保留为历史。旧清单中的SHA不重写。
- 对上述三个旧路径，按逐文件清单定位 `D:/eab-evidence/reports/codex/C3L3_evidence/acceptance_repair_20261023/history_c8718bb/` 下原相对路径加 `.gz`；这条本单精确映射优先于默认旧目录回退规则。
- 本轮[唯一权威差分 gzip](codex/C3L3_repair_evidence/differential.json.gz)：292 limit、2528 critical，0 失配；原 JSON 为 2,544,040 B，压缩后 106,221 B，[解压与双 SHA](codex/C3L3_repair_evidence/differential_archive.json)已核。包括原五层、2332 宽括号查询及 7+18 厚度条目；73 项合法证明增强中，验收指出的[20 个实例全部逐例处置](codex/C3L3_repair_evidence/acceptance_enrichment_disposition.md)。
- [完整构建与运行记录](codex/C3L3_repair_evidence/verification_runs.json)：CTest 12/12；[快档](codex/C3L3_repair_evidence/final_fast/summary.json)8996、[全档四片](codex/C3L3_repair_evidence/final_full/summary.json)15080，GREEN，0 failed/skip，模块实际执行覆盖完整，静态构造 0 违例。
- [本轮归档映射](codex/C3L3_repair_evidence/archive_manifest.json)：107 份原始记录逐件 gzip/解压核 SHA，[受测源码 ZIP](file:///D:/eab-evidence/reports/codex/C3L3_evidence/acceptance_repair_20261023/final_runs/final_full_tested_source.zip)1909 成员逐件核 SHA；[外部相同映射](file:///D:/eab-evidence/reports/codex/C3L3_evidence/acceptance_repair_20261023/final_runs/archive_manifest.json)。不拼接运行、不移改冻结历史 SHA。
- [日志编码补充映射](codex/C3L3_repair_evidence/encoding_corrections.json)：报告回填发现两份定向日志为 PowerShell 的 UTF-16LE 输出，原字节追加保存在 [encoding_originals](file:///D:/eab-evidence/reports/codex/C3L3_evidence/acceptance_repair_20261023/final_runs/encoding_originals/)，仓内转为 UTF-8 无 BOM/LF，逐行内容完全不变，未重跑或改写测试结果。
- 修复内容及原样末行见[主报告](codex/C3L3_report.md)；[最终交付索引](codex/C3L3_repair_evidence/deliverables.md)、[字节与链接审计](codex/C3L3_repair_evidence/delivery_integrity.json)、[卫生账](codex/C3L3_repair_evidence/hygiene.json)给出当前候选。`c8718bb` 新鲜树与静力验收已据所有者来函记录；本轮临界参数路返修仍待 Claude 复验，不以作者自查签署独立验收。

无Git写操作；外归档为本地保存，不是远端备份。

## WO-C3L4（2026-10-23）追加映射

本单 H1 原始日志、收集/执行节点记录和受测源文件清单按原字节追加到
`D:/eab-evidence/reports/codex/C3L4_evidence/20261023_run1/<run>/`，不覆盖不同内容，不删除源文件；逐件复制前后 SHA256 相同。
每个运行完成后才产生对应清单：[开工全档](codex/C3L4_evidence/baseline_full/archive_manifest.json)、收尾快档 / 收尾全档（已被修复轮结果取代、从树中移除，逐字节映射见 [superseded_prior_outputs.json](codex/C3L4_fix_evidence/superseded_prior_outputs.json)）。
[归档脚本](codex/C3L4_evidence/archive_h1.py.txt) 支持上述三个历史运行名及本次明确授权的 `clarified_fast` / `clarified_full`；完整源字节导出仍在 ignored tmp，不称所有者新鲜 Git 树。

[收尾受测源码 ZIP 记录](codex/C3L4_evidence/tested_source_archive.json) 另保存 1981 个成员，逐成员 SHA 与受测 source_manifest 一致；快档与全档使用相同源清单。它保留的是静态测试装配修复前的受测版本，原全档 RED 不被替换；最终两个测试文件的等价修复与定向验证另列本单报告。

六层差分每层的唯一拟交付完整数据保存在 [C3L4 differential](codex/C3L4_evidence/differential/) 的 gzip 中；[压缩前后清单](codex/C3L4_evidence/pack_manifest.json.gz) 记录原 SHA、压缩 SHA 和字节数，已解压回验。旧 L4 的 32 项 tied_labels 红项原始字节已存入下述续办回退 ZIP，不因归档改状态/哈希来过门；当前权威目录只由新完成的运行替换。中间接线/探针输出只留 ignored tmp，不并入权威结果。
[主报告](codex/C3L4_report.md) 和 [交付清单](codex/C3L4_evidence/deliverables.md) 记录实际完成边界及最终净增。外部归档只是本地保存，不是远端备份。

### WO-C3L4 Claude 裁定续办（同一 b34c966 工作树）

- [续办入口与回退 SHA](codex/C3L4_evidence/clarification/intake.json)：修改前的 120 项交付文件逐字节核验后追加到 [prior_delivery.zip](file:///D:/eab-evidence/reports/codex/C3L4_evidence/clarification_20261023/prior_handoff/prior_delivery.zip)，包括旧报告、旧严格 32 失配数据、原逐文件清单与比较器。历史文件按 ZIP 中原仓库相对路径定位，不改写旧结果。
- 新运行名为 `clarified_fast` / `clarified_full`；仅完成后将原始日志、节点及源清单追加到 `D:/eab-evidence/reports/codex/C3L4_evidence/clarification_20261023/<run>/`，对应本树各运行的 `archive_manifest.json`。最终受测源码另存完整 ZIP，每成员核 SHA。
- [串行构建/六层/H1 执行器](codex/C3L4_evidence/clarification/run_verification.py.txt) 与 [进度目录](codex/C3L4_evidence/clarification/) 保留实际命令、进度、退出码和原样末行；未完成记录不能被当作通过。
- 本次阈值基依赖 tied_labels 逐侧独立核证后登记合法表示差异，旧 RED 与新比较口径区分；32 个非 binary64 输入按设计逐条列为 ABI 域外，不伪造成运行通过数。

### WO-C3L4 裁定轮最终收尾归档

- [最终快档原始清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarified_fast/archive_manifest.json)：9109项GREEN，5份原始文件、10,510,087 B；[最终全档原始清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarified_full/archive_manifest.json)：15193项、四片全部GREEN，15份原始文件、17,516,029 B，静态构造0违例。执行节点多重集合与收集一致、0 failed/skip，逐模块实际执行完整，源前后不变。
- [最终受测源码ZIP记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/tested_source_archive.json)：1983成员、23,055,873 B，逐成员SHA核验；[完整ZIP](file:///D:/eab-evidence/reports/codex/C3L4_evidence/clarification_20261023/clarified_full/tested_source.zip) SHA-256 `8bd4defa21383cc38685add3a267265e166f1ac403a63fb6de38fad82b80411d`。快/全档源清单相同，保留全档后仅文档/证据回填的边界，不称新鲜Git树。
- [被授权复用的完整r2五层](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/completed_layers_reuse.json) 与 [L4从头复跑/最终H1执行](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/closeout_execution.json) 分别保存，不拼接中断L4；最终L4 402查询/0失配、32项合法跨基标签台账及32项ABI域外清单见 [L4汇总](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/l4_summary.md)。
- [25份被替换/退役历史文件的精确ZIP映射](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/history_mapping.json.gz) 保留旧字节及SHA；当前权威每层只留一份完整gzip，历史RED不改写。未commit，所有者新鲜Git树及非作者对抗核查由Claude负责，待所有者验收，不计为Codex执行PARTIAL。

## WO-C3L4-fix 定理审查停止实施（2026-10-23，cb14522）

- [修复轮报告](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_report.md)记录双无穷小定理在mu*=mu_max时的实际profile1反例；依Claude工单停下等待边界合同裁定，未改生产实现。
- [开工全档归档清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/baseline_full/archive_manifest.json)：15193项、4分片GREEN、0failed/skip、静态0违例；15份原始日志/节点/源清单逐件复制核SHA，原临时源未删。它不是修后验收。
- [外部相同清单](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/20261023_domain_block/baseline_full/manifest.json)及 [受测源码ZIP](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/20261023_domain_block/baseline_full/tested_source.zip)只在本单新目录追加，2119成员逐项核SHA，不称新鲜Git树。
- [独立K证明发布映射](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/proof_publish.json)、[真实几何脚本身份/编码记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/boundary_geometry_probe_manifest.json)、本轮逐文件清单（已压缩归档，映射见 [historical_compaction.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/historical_compaction.json)）保留取证范围。旧轮结果及旧归档不覆盖，旧UTF16日志minor尚未处理。

外部路径是本地归档，不是远端备份；没有Git写操作，回退不得覆盖所有者后续修改。

## WO-C3L4-fix 续裁定与集成历史（2026-10-23）

以上“停止实施”为续裁定前历史，不能作为当前实现状态。原 BLOCKED 报告及被压缩取证文件见 [历史精确映射](codex/C3L4_fix_evidence/ruling_resume.json) 与 [本树压缩清单](codex/C3L4_fix_evidence/historical_compaction.json)；旧 `deliverables.md`、两个反例 JSON 等按清单在外部 ZIP 中读取，不再保留重复本地副本。

- [旧 RED / UTF-16 归档映射](codex/C3L4_fix_evidence/abi_minor_history.json)：19 个原始成员已逐件核验，外部 ZIP SHA-256 `01cdba67d17b5af5c6c5819b2a78d7c71c3f22b37580ce7b48fb62d48adc5f68`。当前取证日志为 UTF-8 无 BOM、LF；最终哈希采用映射的 `utf8_log_final_sha256`，原字节未覆盖。
- [本轮集成历史映射](codex/C3L4_fix_evidence/integration_history.json)：两份真实字节快照及 RED/INVALID 日志、节点、执行与自有 PID 终止记录共 4292 成员，逐成员 SHA 核验；[追加 ZIP](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/integration_history_20261023_r3/history.zip) SHA-256 `44cc544adb9f8e1f2dc591eba031457fceac561ceb514080b0c6fa70ae75bcf0`。原样末行 `24 failed, 9203 passed in 800.83s (0:13:20)` 是历史 RED，第一次未完成快档及中断构建/差分同属无效证据，未拼接为通过。
- 两个被取代快档目录只留历史 README；7 个 JSON 在核验归档后移除。可复跑脚本见 [archive_integration_history.py.txt](codex/C3L4_fix_evidence/archive_integration_history.py.txt)。忽略目录的原始临时文件未删，未将编译产物收入此归档。

最终修后验收应读取修复轮报告与新运行清单，而不是上述历史 RED。新鲜 Git 树及非作者对抗核查仍待所有者验收。

### WO-C3L4-fix 四项旧 JSON 精确迁移（2026-10-23）

- [逐文件路径、字节与 SHA 映射](codex/C3L4_fix_evidence/superseded_prior_outputs.json)覆盖且仅覆盖旧 `checks/static_repair_verification.json`、`hygiene.json`、`tied_labels_forensics.json`、`checks/build_audit.json`；总计 **211,565 B**。574 个 authored 运行/测试/构建文本文件重检，无这四项文件名依赖；同名 `.log`、consumer 与冻结测试输入不移动。
- 四份 JSON 先追加复制到[本单专属外部目录](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/superseded_prior_outputs_20261023/)，全部逐字节及 SHA-256 读回相等，再逐项复核工作树绝对路径与源 SHA，仅移除这四份本地副本。[外部 manifest](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/superseded_prior_outputs_20261023/manifest.json) SHA-256 为 `11f7d445fdc55cd5d30d2a70ba41ce5bb81f9489e8c9adbbd7b1ff1113e9f01d`；已存在不同字节拒绝覆盖。
- [固定四目标的可复跑脚本](codex/C3L4_fix_evidence/archive_superseded_prior_outputs.py.txt)保留精确尺寸/SHA、依赖重检、复制/删除前验证与不存在路径恢复边界。旧结果/结论/SHA 不改写，旧报告链接改指相同外部 JSON；源清单中的历史相对路径通过本映射解释。此迁移不升级历史结果为本轮通过，不把旧净增当修复轮最终净增。

无 Git 写、无递归删除、无编译产物归档；外部路径仅为本地保存，不是远端备份。回退只可恢复映射指定且当前不存在的原路径，核 SHA，绝不覆盖所有者后续修改。

### WO-C3L4-fix-close 64b499f 历史 JSON 无损压缩（2026-10-24）

真实净增超限后，仅将旧 C3L4_evidence 的三份 module_coverage、abi_static_repair、checks/mutations、pack_manifest、clarification/history_mapping 与 checks/harness_static_equivalence 共八份 JSON 压为同目录 `.json.gz`，逐字节解压回验后移除原副本。原始 100,295 B → gzip 19,896 B，节省 80,399 B；数据、历史结论与原 SHA 不改写，不升级为本轮通过。

[逐文件路径/字节/SHA 映射](codex/C3L4_fix_evidence/historical_compaction.json) 的 `close_64b499f_gzip` 保存原路径与压缩路径；目录清单和旧 harness 文档链接同步，两份主报告不改。回退只向不存在的原路径解压并核原 SHA，不能覆盖后续修改。未写外部目录，冻结语料/准入不动。

## WO-T2a（2026-10-25）：原BLOCKED交付历史（续裁定前）

本节保留续裁定前的交付叙述；下文“当前166项”“policy不改”均指当时状态，不代表续裁定后的最终状态。原报告、清单和审计字节见[原BLOCKED交付ZIP](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/blocked_delivery_anchor.zip)及[入口SHA](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/intake.json)；当前状态见本节后的续裁定收尾记录。

本单只新增Python路径原语、测试和T2工具；既有数学API、C++/eab2、静态策略及分析器未改。完整记录见[中文报告](file:///D:/eab-wt/cx-e2/reports/codex/T2a_report.md)及[全部交付链接](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/artifacts.md)。**10例数值证书通过不等于工单验收：当前166项冻结静态诊断、旧纯度固定模块计数52与新增后53不一致，收尾全仓快/全档没有执行。**

- [开工源ZIP](file:///D:/eab-evidence/reports/codex/T2a_evidence/baseline_anchor/source.zip)由干净 `239ec30863db52d531531f77003da46fc3441908` 的2398份被跟踪文件逐字节生成；[成员SHA与入口记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/baseline_anchor/manifest.json)。它是字节快照，不是新鲜Git树。
- [开工H1全档四片](file:///D:/eab-evidence/reports/codex/T2a_evidence/baseline_full/)保存原始日志、收集/执行节点、逐模块监测与源清单；结果以完成的summary为准，不与收尾混称。
- [完整13条交付证书](file:///D:/eab-evidence/reports/codex/T2a_evidence/certificates/)：10个指定样本全接受；门洞等号/上侧接受、下侧伪造路径拒收。JSON有理数为字符串，保存生产基线提交和实际未提交源SHA；[原生产及独立oracle记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/verification_01/)不覆写，交付版仅规范门洞尾段整数坐标为有理字符串，值/结果相同及双SHA见[序列化映射](file:///D:/eab-evidence/reports/codex/T2a_evidence/certificates/serialization_manifest.json)。仓内仅留[两条固定小子集](file:///D:/eab-wt/cx-e2/tests/data/t2a_escape_replay.json)，测试实际重跑，不钉当前源码哈希。
- [166项诊断](file:///D:/eab-evidence/reports/codex/T2a_evidence/static_01.json)、[最小复现](file:///D:/eab-evidence/reports/codex/T2a_evidence/static_minimal_repro.json)、[定向验证](file:///D:/eab-evidence/reports/codex/T2a_evidence/targeted_checks/)、[作者QA](file:///D:/eab-evidence/reports/codex/T2a_evidence/author_qa.json)均保留原状态；静态policy字节和总准入数不改。
- [外部逐文件SHA/路径清单](file:///D:/eab-evidence/reports/codex/T2a_evidence/artifact_manifest.json)覆盖持久证据（不递归列tmp运行副本）；每条`relative_path`相对本单外部根。源快照成员由独立manifest覆盖，tmp中的运行源另按H1 source_manifest定位。
- [工作树交付审计](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/delivery_audit.json)记录新增/修改清单、净增、UTF-8及原受保护文件字节未变。原证据不删除、不篡改哈希；外部只是本地归档，不是远端备份。

回滚只逐文件对照开工ZIP，不能覆盖后续所有者修改；Codex无commit/push/reset/checkout/stash/worktree/branch写操作。

### WO-T2a 续裁定收尾（2026-10-25，同一239ec30工作树）

- 所有者批准证明缺口逐站审查后，按AST节点和最小外围源码SHA追加 **137项**（生产44、测试辅助93）；rounded/浮点构造汇点准入 **0**。旧3522条、其他策略字段及三静态分析器字节不变。[逐站账本与逐规则计数](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/static_admissions.json)、[报告§10](file:///D:/eab-wt/cx-e2/reports/codex/T2a_report.md#t2a-static-admission-review)、[写入审查记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/admission_authoring.json)。纯度仅52→53；历史策略视图总数仅3522→3659配套维护，投影逻辑和历史指纹不变。
- [收尾快档](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_fast_r2/summary.json)：9415项；[收尾全档四片](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/summary.json)：15521项。均GREEN、0 failed/skip，收集/分派/实际call节点多重集合相同，69个模块实际执行覆盖完整，现场与导出源前后不变；全档静态原样末行 `exact construction AST gate: 0 violation(s)`。所有原日志、执行记录与源清单在各run目录逐项保存，不拼接运行。
- 首轮 [resume_final_fast](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_fast/state.json)因900s上限作废，保留其失败进度和原日志；11项历史计数失败及其机械修正见[修前](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/history_counter_before.json)、[修后](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/history_counter_after.json)。它不计作通过证据。
- 快档与全档源清单一致；全档[受测字节ZIP](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/tested_source.zip)及[逐成员核验记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/tested_source_archive.json)保留运行时版本。运行后只回填报告、归档、交付清单/审计；`src/`、`tests/`、`tools/`及准入账本仍为受测原字节。此为字节导出，**不是所有者新鲜Git树**。
- 原13条证书JSON及序列化映射共14文件的SHA仍与续工前快照相等；10个指定T1b平移困住样本的286段、858次生产及888次独立oracle核验结论未改。不为文档重算全量冻结数值，也不把它们升级为刚体临界公差或SE(2)困住结论。
- 当前[逐文件SHA/路径清单](file:///D:/eab-evidence/reports/codex/T2a_evidence/artifact_manifest.json)覆盖本次持久外部证据（排除tmp及清单自身）和仓内交付；源ZIP成员另由对应source_manifest覆盖。[交付审计](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/delivery_audit.json)重新核对完整日志、节点、模块覆盖、受测代码、冻结证书、UTF-8无BOM与净增≤5MB；4项原有文件修改严格限于归档登记、准入policy、纯度计数及历史计数视图。

本单执行完成；所有者新鲜Git树、一路独立对抗验收及T1b正式追加勘误仍由Claude负责。未commit、未改C++或既有数学API，未干预非本代理启动的进程。外部归档是本地保存而非远程备份；回滚必须先对照SHA并保护所有者后续修改。

### WO-T2a 验收返修（2026-10-25，t2a @ d60b79b）

本节为当前状态，以上续裁定收尾属于所有者提交d60b79b之前的历史。所有者来函确认新鲜Git树复现和三路非作者核查通过：13份证书、7320次对拍0分歧；健全性10000随机例与25手推退化例0缺陷。该结果按[所有者裁定](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/owner_ruling.json)登记，不冒称本代理重跑或持有其全部原日志；所有者另跑的新鲜树全仓全档完成结果尚未由本代理记录。

- 返修前实查分支`t2a`、HEAD `d60b79b0b0c7f671e34971a3596648727846b8af`、干净工作树；[2425文件回退ZIP](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/before_repair.zip)及[成员SHA/入口](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/intake.json)另保留原外部artifact_manifest，ZIP SHA `459435616e1f45f832a355ac32432b27c10bc955f781c387f69269dd1d8e8f49`。
- **证书内嵌的生产块来自早一版源码，终版源码复核结果逐项相同。** 原内嵌 `se2_paths.py` SHA `9b791d2885edb2e62e8c9c1a00f17c393391f5d4a030d525ce24d7bfcfa5e39e` 保留不改；按裁定重跑10例和门洞3例的新完整结果在[final_reverify_20261025](file:///D:/eab-evidence/reports/codex/T2a_evidence/final_reverify_20261025/)，绑定终版SHA `14bfd823dda1c438ffd136128f73545236d5e2bbbb428a3b1eb5e09efc79bbdf` 和d60b79b。[运行记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/reverify.json)、[逐项比较](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/comparison.json)：13例生产/oracle整块对原两套记录完全相同，12例VERIFIED_ESCAPE、原door_below拒收；生产903对、oracle948对。原证书和verification_01共41文件不改，原SHA不重写；新27个JSON只作CRLF→LF规范，前后解析值及SHA完整记录。
- 回放小输入[tests/data/t2a_escape_replay.json](file:///D:/eab-wt/cx-e2/tests/data/t2a_escape_replay.json)仅替换1436个CRLF，JSON值不变；[转换映射](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/replay_lf_conversion.json)给出旧SHA `bf9ffbf76792abd344906448478686725322b2ba806a843b6c52bdd0d22a7168`、新SHA `f3d0c9d523cfab8275b3949744a2d576eb63503dee43495e18d02291ee15338a`。当前交付审计及artifact_manifest的repository_delivery同步为新SHA；不改原冻结输入的几何或出处字段。
- [本轮完整指定门checks_02](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/checks_02/summary.json)：全T2a含slow108项、纯度38项，另独立复跑准入15项、回放2项，全0 failed/skip/deselected，静态 `exact construction AST gate: 0 violation(s)`。两个many补门、新开线段变异及门洞全端点自由/段内贯入门见[报告§10.5](file:///D:/eab-wt/cx-e2/reports/codex/T2a_report.md)；本轮无新增准入，仍137=44+93。首轮checks_01的临时父目录漏建导致36个setup errors，原脚本/日志保留；只修外部执行器，新目录完整重跑，不拼接绿片段。
- 本轮只改三份测试、回放数据、报告和证据，`src/`、工具、policy、三分析器、C++及T1b报告与d60b79b逐字节相同；所有者对H1计数和两类证明缺口的追认仅写报告。按裁定不重跑全仓快/全档；旧9415/15521记录仍属于原交付，不能冒充本轮新增测试运行。
- [当前交付审计](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/delivery_audit.json)与[外部逐件SHA清单](file:///D:/eab-evidence/reports/codex/T2a_evidence/artifact_manifest.json)重新核验旧178份持久证据未变、授权写域、UTF-8无BOM/LF、当前仓内交付及累计净增≤5MB；[外部可复跑审计脚本](file:///D:/eab-evidence/reports/codex/T2a_evidence/acceptance_repair_20261025/audit_repair_delivery.py)区分原工单累计基线239ec30、本轮d60基线与历史全仓运行。全部成员以manifest相对路径定位，tmp及manifest自身不递归收录。

本代理未commit/push/reset/checkout/stash/worktree/branch；返修完成待所有者合入，不改T1b历史报告。外部仅为本地保存；回退须先核SHA并保护所有者后续修改。

## WO-T2b（2026-10-25）：SE(2) 笼证书与双侧括号

- [中文报告](file:///D:/eab-wt/cx-e2/reports/codex/T2b_report.md)与[交付清单](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/artifacts.md)给出实际完成状态；独立 WO-T2b-V 尚未收到所有者合入通知，科学表标为 `production_only_pending_independent`，不冒称双核验验收。
- [开工ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/baseline_anchor/source.zip)与[2426文件SHA清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/baseline_anchor/manifest.json)来自干净 `codex-work`、HEAD `146cc76b6e25598f00564438dee7f3282ad52e34`；仅字节快照，不是新鲜Git树。既有数学API、只读引理、eab2及三个静态分析器不改。
- [十例科学证书 science_02](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02/)保存每例下界实例/笼证书、只圆实例/证书及逃逸实例/路径、所有探针与来源。完整[汇总](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02/summary.json)记录源提交、实际未提交工具/核验器SHA、源ZIP及配置；[规范JSON重核](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02_serialized_recheck.json)实际检查20份下界证书。探索 science_01 保留历史，不与终版拼接。
- [真值 truth_02](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/truth_02/)有5笼证书和3条接受的逃逸路径；低房间只圆未证、封口链接受。[仓内固定小回放](file:///D:/eab-wt/cx-e2/tests/data/t2b_cage_replay.json)实际重核八边形与低房间证书，保留来源但不钉当前源码；[39份伪造](file:///D:/eab-wt/cx-e2/tests/data/t2b_forgeries/)是小型测试输入。
- [逐站静态账本](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/static_admissions.json)追加98个唯一证明缺口键（生产35、测试63），浮点汇点0；旧3659条和其他policy字段的JSON值不变。原policy是CRLF，本单按LF合同规范换行；[原字节副本](file:///D:/eab-evidence/reports/codex/T2b_evidence/policy_before_t2b.json)保留，不称旧policy原始字节未变。历史门仅机械计数/切片兼容，三分析器不改。
- [开工全档](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_baseline_20261025/summary.json)与后续具名收尾run分别保存节点、多重集合、逐模块实际执行和完整日志；收尾结果以报告实际回填为准。共享历史运行器及旧逃逸提议器输出的CRLF文本，先ZIP保留原字节并逐成员核SHA，再仅导出LF视图，JSON值和末行不变；映射见每个run的 `lf_export.json`、science_02 的 `lf_normalization.json`，不改旧来源证据。
- [外部逐文件SHA/路径清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/artifact_manifest.json)登记本单持久证据和仓内交付（排除tmp及清单自身）；[交付审计](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/delivery_audit.json)核准写域、受保护旧文件、UTF-8无BOM/LF、净增≤5MB。临时字节导出由各run source_manifest定位，不作远程备份声称。

不作Git写、不修改姊妹仓库或终止非本代理进程。回退只能先核开工ZIP的逐文件SHA，再保护所有者后续修改；独立核验器合入、双方伪造拒收代码对拍及所有者新鲜树/一路对抗验收仍须明确完成后另记。

### WO-T2b 生产侧收尾（2026-10-26，原工作树）

- [快档 t2b_final_fast_20261025](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_fast_20261025/summary.json)实际9694项；[全档 t2b_final_full_20261025](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_full_20261025/summary.json)固定四片共15800项；均GREEN、0 failed/skip，静态末行 `exact construction AST gate: 0 violation(s)`。跨日保留开跑时run名，不重命名或拼接运行。
- [机械审计](file:///D:/eab-evidence/reports/codex/T2b_evidence/final_pair_audit.json)核两个2488文件源清单完全相同，收集/分派/插件收集/实际call节点多重集合相等，70模块运行覆盖完整；620份代码/测试/工具/准入账本仍为受测字节。[受测源码ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_full_20261025/tested_source.zip) SHA `c15fb48bd58c9ab656738b469dd9d6e0f5be6b3575681aae60f8061f29ef4750`，2488成员逐字节与SHA复核。
- 全部测试完成后，仅回填报告/归档/交付元数据，代码不再改。[逐项P0核查](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/requirements.json)列明271个T2b执行节点和待独立交接状态。此前提议器资源修复有[前红后绿证据](file:///D:/eab-evidence/reports/codex/T2b_evidence/resource_repair/summary.json)，未重算或改写科学扫描；旧科学源ZIP仍按原SHA保存。
- 最终状态 **T2B_PARTIAL**：仅待所有者合入独立核验器后的全部入表证书双核验及双方伪造集拒收代码对拍；P1完整盖标签诊断未做不计作PARTIAL原因。内部多代理机械检查不冒称所有者新鲜树或独立对抗验收。

<!-- T2B_CONTINUATION_5c0f80f_BLOCKED -->
### WO-T2b 独立合入续单：BLOCKED（2026-10-26，HEAD 5c0f80f）

本段仅追加本次实测记录，不改历史结论。原25份与新d03/d08两份笼证书均双核验；8燕尾族125个不同δ实例相等；13条逃逸按有限独立oracle及生产无限尾射线边界复核。双方语料0判定/条件代码不一致；我方192次有效调用单列（71不同字节对），不与130/505组计数相加作去重总数。10例加d07四内点P1诊断已完成。

- [中文报告](file:///D:/eab-wt/cx-e2/reports/codex/T2b_report.md) · [续单机器摘要](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/continuation_summary.json) · [逐项核查](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/requirements.json)
- [终版14点诊断](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/diagnostics/final_03/summary.json) · [新笼证书](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/diagnostic_03) · [逐件来源SHA](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/new_certificates_copy.json)
- [阻塞最小复现](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/blocker_independent_policy_pin/summary.json) · [干净基线ZIP复现](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/blocker_independent_policy_pin/baseline_reproduction.json)：只读独立测试policy期望SHA与干净开工基线及当前未改policy不符；最小pytest复现原样末行 `1 failed in 0.08s`。不是引理数学分歧，未发现数学反例。
- [中断作废声明](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_dual_final_fast_20261026/INTERRUPTED_INVALID_RUN.json)：快档收集10269项，停止进度9830 calls、1 failed、0 skipped，Ctrl-C后作废；没有最终pytest末行。全档目录未创建、最终静态未运行。旧绿和非冻结静态预检0不替代当前通过。
- [中断源码ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_dual_final_fast_20261026/interrupted_source.zip) SHA `e0bff88dd7f8ce2305440d3cb87402f82fc0ea2cc10ed4a01858e740c854b8cd`；[中断日志原字节ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_dual_final_fast_20261026/interrupted_raw_bytes.zip) SHA `bde0a21e2e2f0a6c29f2754c27770a745358e8a95a85e39662ab057da78fd6f6`；[中断源码清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_dual_final_fast_20261026/source_manifest.json)。2614成员与清单尺寸/SHA核对；这是中断快照，不是通过测试的源码。原日志保留后再LF导出，raw parser输入不规范化。
- [交付文件审计](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/resume_delivery_audit.json) · [逐文件SHA清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/resume_artifact_manifest.json)。续单新增静态准入0；89项独立只读文件、既有生产数学源码、policy、三分析器和只读合同不改。文件完整性/范围审计不冒称全仓测试通过。

当前 `T2B_BLOCKED`；等待所有者裁定只读测试字节锚，之后须新run名重新执行快档/全档，不拼接。新鲜Git树及一路独立对抗验收未声称完成；本地证据不是远程备份，未作Git写。

### WO-T2b 验收返修完成（2026-10-26，c900033）

本段取代上文历史“当前BLOCKED/待独立”状态，不改原始冻结证据。所有者已修复独立策略钉子并解除阻塞；生产src、89项独立侧、引理、C++与三个分析器本轮均未改。最终科学表合并d03 `[1/4,21/50]`、d08 `[13/128,11377/51200]`，其余8例不变，仍无临界值等号声称。

- [最终中文报告](file:///D:/eab-wt/cx-e2/reports/codex/T2b_report.md) · [返修机器摘要](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/acceptance_repair_summary.json) · [最终科学表](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/scientific_summary.json)。累计27份笼文件文本双核验通过，最终表采用其中25份；7逃逸候选原文不改，旁记含源SHA/逐段验证，见[旁记清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/policy_sidecars/escape_reverification_02/summary.json)。
- [27份新增伪造双SHA](file:///D:/eab-wt/cx-e2/tests/data/t2b_forgeries/acc/manifest.json)仅CRLF→LF；原/入库54对全部拒收、代码一致。新10项卫生、接触边界及文本入口具名门保持生产语义；[97项最终轮](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/mutation97/definitive_04/acceptance_summary.json)82语义杀、15所有者允许存活、0其他存活。01/02作废、03仅诊断，不拼接04。
- [策略CRLF恢复](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/policy_sidecars/policy_restore.json)：相对146cc76仅1078行插入/0删除=98项，原JSON值不变。所有者2026-10-26追认证明缺口98、浮点汇点0，本轮新增准入0。
- [新快档](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_acceptance_fast_02_20261026/summary.json) 10309项、[新全档四分片](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_acceptance_full_02_20261026/summary.json) 16415项，均GREEN、0failed/skip；静态 `exact construction AST gate: 0 violation(s)`。[双轮审计](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/final_pair_audit.json)保存源码ZIP及成员SHA核验。报告仅在收尾后回填，受测代码不改；本代理未做新鲜Git树或Git写操作。
- H1路径/SHA映射：[返修逐文件归档清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/artifact_manifest.json)、[仓内修改清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/repository_manifest.json)、[净增/只读/编码审计](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/delivery_audit.json)。外置大件不入库，累计仓内净增≤5MB；policy是明确授权的CRLF例外，其余新/改文本UTF-8无BOM/LF。归档为本地保存，不冒称远程备份。

`T2B_DONE`；所有者对本轮返修的最终接收与新鲜Git树验证不由本代理自签。

## WO-T2c1（2026-10-26）：提议器与科学表 v2

- [中文报告](file:///D:/eab-wt/cx-e2/reports/codex/T2c1_report.md)给出实际验收边界。10例下界/上界均改善，两凸耳相对宽度≤1/256，八燕尾未达；只报括号，不给刚体临界值等号。tools整文件静态要求仍未闭合，不能由现有仓门0违例代替。
- [开工2674文件ZIP](file:///D:/eab-evidence/reports/codex/T2c1_evidence/baseline_anchor/source.zip)及[逐文件SHA](file:///D:/eab-evidence/reports/codex/T2c1_evidence/baseline_anchor/manifest.json)来源干净 `codex-work`、HEAD `cfa3e90b8fcca2117021bb12df188322199f3cfe`；不作Git写，仅字节导出，不冒称新鲜Git树。生产/独立核验器、引理、三个分析器及policy不改。
- [主扫证书与路径](file:///D:/eab-evidence/reports/codex/T2c1_evidence/certificates/joint_01/)保留每查询原始输入、双核验结果、源ZIP/提交/工具版本/资源参数；[最终端点选择及独立来源](file:///D:/eab-evidence/reports/codex/T2c1_evidence/final_selection_02/summary.json)另引用[d01高预算](file:///D:/eab-evidence/reports/codex/T2c1_evidence/high_budget_d01_01/summary.json)、[闭链专项](file:///D:/eab-evidence/reports/codex/T2c1_evidence/closed_chain_high_budget_01/summary.json)、[凸耳1/800终版](file:///D:/eab-evidence/reports/codex/T2c1_evidence/fine_escape_03/summary.json)，不拼接运行。fine02整轮作废，原件[独立字节归档](file:///D:/eab-evidence/reports/codex/T2c1_evidence/logs_lf_fine_invalid02/invalid_run_manifest.json)，未采用其中部分成功。
- [科学表v2](file:///D:/eab-evidence/reports/codex/T2c1_evidence/science_summary_02/table_v2.json)、[1917项一致性/计数](file:///D:/eab-evidence/reports/codex/T2c1_evidence/science_summary_02/consistency.json)：所有入表笼经生产文本与独立load_json；逃逸仍沿用T2b的生产无限尾+独立有限范围。新增数值边界审计不替代静态门。[仓内固定回放](file:///D:/eab-wt/cx-e2/tests/data/t2c1/)保存每例最终笼及新逃逸各一份，数据完整性哈希与历史来源保留，实际回放完整状态/计数，不钉当前源码。
- [端点观察20点](file:///D:/eab-evidence/reports/codex/T2c1_evidence/observer_endpoints_01/summary.json)另产生d07=1019/4096新笼；最终选择02增量采用，原170查询记录不改。规范证书交付副本见 [final_02](file:///D:/eab-evidence/reports/codex/T2c1_evidence/certificates/final_02/manifest.json)，原独立来源全部保留。
- [长路径修复映射](file:///D:/eab-evidence/reports/codex/T2c1_evidence/path_repair/move_map.json)记录54个JSON字节不变，目录缩为acc/ID；150字符basetemp两指定测试通过，复制根字面量亦缩为repo。既有数学合同不变。
- [有限分歧守护返修](file:///D:/eab-evidence/reports/codex/T2c1_evidence/guard_install_01/report.md)发生在科学源冻结结束后；旧52份审计未触发该分支，原来源SHA不改，不为文档重算扫描。
- [开工全档](file:///D:/eab-evidence/reports/codex/T2c1_evidence/t2c1_baseline_20261026/summary.json)、[收尾快档](file:///D:/eab-evidence/reports/codex/T2c1_evidence/t2c1_final_fast_20261026/summary.json)、[收尾全档](file:///D:/eab-evidence/reports/codex/T2c1_evidence/t2c1_final_full_20261026/summary.json)的实际执行状态及原样末行见报告；每run各有源清单、源码ZIP、节点多重集合/模块执行检查和原日志字节ZIP+LF视图。
- H1逐文件登记：[外置及仓内交付SHA清单](file:///D:/eab-evidence/reports/codex/T2c1_evidence/delivery_final_01/artifact_manifest.json)、[仓内清单](file:///D:/eab-evidence/reports/codex/T2c1_evidence/delivery_final_01/repository_manifest.json)、[范围/净增/编码审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/delivery_final_01/delivery_audit.json)。大件只在本单外置目录；tmp不作为持久交付，清单不自含。原始冻结字节不因LF展示或源码搬动而改写。

收尾快档10375项、全档四分片16491项均GREEN，0 failed/skip，70模块实际执行；全档静态原样 `exact construction AST gate: 0 violation(s)`。[双轮源ZIP/节点多重集合审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/final_pair_01/audit.json)核2695成员，两源ZIP同SHA `1cde35038f3628568bb83ccdec98b800972f96bd56871501e000620eccfbb89c`。报告在两轮结束后才回填，非reports代码/数据不再修改。

[逐项核查](file:///D:/eab-evidence/reports/codex/T2c1_evidence/requirements.json)明确 **T2C1_PARTIAL**：工具整文件显式扫描376条，286仅规则分类、90非证明缺口，新增准入0；既有仓门绿不替代此项。P1全40组合未开展，不单独算PARTIAL。所有者新鲜树及独立对抗验收待其安排，本地多代理审阅不替代；八燕尾未达目标宽度已如实报告。
