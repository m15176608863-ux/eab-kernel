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
