# 证据外部归档（WO-H1，2026-10-19）

历史报告正文不逐个改链接。路径映射：旧 `reports/codex/<名称>_evidence/<相对文件>` 对应 `D:/eab-evidence/reports/codex/<名称>_evidence/<相对文件>`；H1 当前运行目录不归档。
测试实际读取的输入优先映射到 `fixtures/frozen/<去掉 reports/ 的原路径>`；输入原字节保留，嵌入的历史路径/哈希不重写。
保留仓库内的报告正文、当前 `reports/codex/inputs/`、本单 H1 证据及其他小型索引；不重写 Git 历史。

- 首批测试输入：136 文件，11,662,520 字节已搬入 fixtures；[初批专属清单](codex/H1_evidence/frozen_inputs_initial_136.json)（从当前总清单减去明确追加项复原，逐文件行未改）。
- 外归档：32 目录，实际 274,244 文件、20,061,143,706 字节（含旧 ignored 临时/沙箱产物）；其中 Git 跟踪 5,551 文件、521,250,702 字节。
- 每目录清单含原相对路径、字节数、SHA256、是否原 Git 跟踪；巨大清单只存仓库外。
- 验证：搬迁前逐文件 SHA256；同卷目录 rename 保留原字节；搬迁后逐文件存在性/长度核对。输入迁移另外重算目标 SHA256；无覆写与无删除操作。
- 归档脚本：[tools/h1_archive_evidence.py](../tools/h1_archive_evidence.py)；[机器结果](codex/H1_evidence/archive_result.json)。

| 原目录 | 实际文件数 | 实际字节 | 跟踪文件数 | 跟踪字节 | SHA256 逐文件清单 |
|---|---:|---:|---:|---:|---|
| `reports/codex/E2_evidence` | 250 | 1,373,863 | 97 | 1,018,251 | [reports__codex__E2_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E2_evidence.sha256.jsonl) |
| `reports/codex/E3E4_evidence` | 257 | 5,125,829 | 137 | 4,209,859 | [reports__codex__E3E4_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E3E4_evidence.sha256.jsonl) |
| `reports/codex/E5a2_evidence` | 758 | 19,524,060 | 229 | 14,755,975 | [reports__codex__E5a2_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E5a2_evidence.sha256.jsonl) |
| `reports/codex/E5a_evidence` | 990 | 13,908,187 | 193 | 5,531,982 | [reports__codex__E5a_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E5a_evidence.sha256.jsonl) |
| `reports/codex/E5b_evidence` | 560 | 9,655,072 | 305 | 9,022,482 | [reports__codex__E5b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__E5b_evidence.sha256.jsonl) |
| `reports/codex/INT1_evidence` | 151 | 718,037 | 151 | 718,037 | [reports__codex__INT1_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__INT1_evidence.sha256.jsonl) |
| `reports/codex/M3_evidence` | 22,897 | 2,250,334,257 | 89 | 1,343,958 | [reports__codex__M3_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M3_evidence.sha256.jsonl) |
| `reports/codex/M3b_evidence` | 179 | 1,684,890 | 179 | 1,684,890 | [reports__codex__M3b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M3b_evidence.sha256.jsonl) |
| `reports/codex/M3c_evidence` | 105 | 258,424 | 105 | 258,424 | [reports__codex__M3c_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M3c_evidence.sha256.jsonl) |
| `reports/codex/M4a_evidence` | 84 | 2,694,906 | 84 | 2,694,906 | [reports__codex__M4a_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M4a_evidence.sha256.jsonl) |
| `reports/codex/M4b_evidence` | 30 | 343,538 | 30 | 343,538 | [reports__codex__M4b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M4b_evidence.sha256.jsonl) |
| `reports/codex/M4c_evidence` | 36,792 | 3,585,974,700 | 388 | 3,989,846 | [reports__codex__M4c_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M4c_evidence.sha256.jsonl) |
| `reports/codex/M5a2_evidence` | 34,708 | 3,290,853,547 | 377 | 1,274,766 | [reports__codex__M5a2_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5a2_evidence.sha256.jsonl) |
| `reports/codex/M5a_evidence` | 15,536 | 1,452,456,181 | 121 | 703,929 | [reports__codex__M5a_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5a_evidence.sha256.jsonl) |
| `reports/codex/M5b_evidence` | 17,014 | 1,587,625,943 | 92 | 682,890 | [reports__codex__M5b_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5b_evidence.sha256.jsonl) |
| `reports/codex/M5c_evidence` | 22,575 | 1,549,886,215 | 98 | 2,906,500 | [reports__codex__M5c_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5c_evidence.sha256.jsonl) |
| `reports/codex/M5d_evidence` | 19,509 | 1,505,727,055 | 102 | 4,515,024 | [reports__codex__M5d_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5d_evidence.sha256.jsonl) |
| `reports/codex/M5e_evidence` | 40,086 | 2,382,095,499 | 0 | 0 | [reports__codex__M5e_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5e_evidence.sha256.jsonl) |
| `reports/codex/M5f_evidence` | 40,285 | 1,403,719,378 | 0 | 0 | [reports__codex__M5f_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__M5f_evidence.sha256.jsonl) |
| `reports/codex/PERF_evidence` | 520 | 11,271,956 | 258 | 10,637,992 | [reports__codex__PERF_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__PERF_evidence.sha256.jsonl) |
| `reports/codex/R10FIX_evidence` | 411 | 5,020,313 | 273 | 4,514,973 | [reports__codex__R10FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R10FIX_evidence.sha256.jsonl) |
| `reports/codex/R11FIX_evidence` | 746 | 5,639,361 | 373 | 4,603,848 | [reports__codex__R11FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R11FIX_evidence.sha256.jsonl) |
| `reports/codex/R12FIX_evidence` | 779 | 101,644,612 | 124 | 55,480,495 | [reports__codex__R12FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R12FIX_evidence.sha256.jsonl) |
| `reports/codex/R12FIXb_evidence` | 2,524 | 105,028,673 | 518 | 75,962,260 | [reports__codex__R12FIXb_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R12FIXb_evidence.sha256.jsonl) |
| `reports/codex/R13FIX_evidence` | 3,109 | 200,078,361 | 123 | 25,526,019 | [reports__codex__R13FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R13FIX_evidence.sha256.jsonl) |
| `reports/codex/R13FIXb_evidence` | 3,551 | 110,528,236 | 173 | 28,711,823 | [reports__codex__R13FIXb_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R13FIXb_evidence.sha256.jsonl) |
| `reports/codex/R14FIX_evidence` | 4,382 | 133,382,384 | 185 | 38,210,567 | [reports__codex__R14FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R14FIX_evidence.sha256.jsonl) |
| `reports/codex/R15FIX_evidence` | 3,747 | 128,365,388 | 129 | 32,467,477 | [reports__codex__R15FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R15FIX_evidence.sha256.jsonl) |
| `reports/codex/R6FIX_evidence` | 491 | 12,678,140 | 175 | 11,945,094 | [reports__codex__R6FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R6FIX_evidence.sha256.jsonl) |
| `reports/codex/R7FIX_evidence` | 298 | 26,447,626 | 107 | 25,819,120 | [reports__codex__R7FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R7FIX_evidence.sha256.jsonl) |
| `reports/codex/R8FIX_evidence` | 311 | 48,515,676 | 170 | 48,158,630 | [reports__codex__R8FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R8FIX_evidence.sha256.jsonl) |
| `reports/codex/R9FIX_evidence` | 609 | 108,583,399 | 166 | 103,557,147 | [reports__codex__R9FIX_evidence.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__R9FIX_evidence.sha256.jsonl) |

## 验证与回退

`archive_result.json` 另记录每份清单自身的 SHA256。如需回退，先确认原路径不存在，再依据清单将目标目录移回原位置，并把 fixtures/frozen 输入移回其 source；不得覆盖所有者后续生成的数据。归档是本地原字节保存，不是远端备份。

## 追加：历史对抗复现与展示产物

运行输入依赖扫描未发现 G6F–G6O 复现目录的生产/测试/工具引用；这些目录及 showcase 作为历史证据原字节外移，不执行旧复现。旧 `reports/<相对路径>` 映射为 `D:/eab-evidence/reports/<相对路径>`。

追加 11 目录、496 文件、2,023,407 字节；两批合计 43 目录、274,740 文件、20,063,167,113 字节，其中原 Git 跟踪 6,047 文件、523,274,109 字节。

[依赖审计](codex/H1_evidence/g6_repro_dependency_audit.json)；[追加归档结果](codex/H1_evidence/archive_additional_result.json)。

| 原目录 | 实际文件数 | 实际字节 | 跟踪文件数 | 跟踪字节 | SHA256 逐文件清单 |
|---|---:|---:|---:|---:|---|
| `reports/codex/inputs/G6F_repro` | 50 | 146,381 | 50 | 146,381 | [reports__codex__inputs__G6F_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6F_repro.sha256.jsonl) |
| `reports/codex/inputs/G6G_repro` | 73 | 166,238 | 73 | 166,238 | [reports__codex__inputs__G6G_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6G_repro.sha256.jsonl) |
| `reports/codex/inputs/G6H_repro` | 70 | 177,442 | 70 | 177,442 | [reports__codex__inputs__G6H_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6H_repro.sha256.jsonl) |
| `reports/codex/inputs/G6I_repro` | 58 | 163,297 | 58 | 163,297 | [reports__codex__inputs__G6I_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6I_repro.sha256.jsonl) |
| `reports/codex/inputs/G6J_repro` | 43 | 113,774 | 43 | 113,774 | [reports__codex__inputs__G6J_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6J_repro.sha256.jsonl) |
| `reports/codex/inputs/G6K_repro` | 42 | 86,370 | 42 | 86,370 | [reports__codex__inputs__G6K_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6K_repro.sha256.jsonl) |
| `reports/codex/inputs/G6L_repro` | 20 | 67,042 | 20 | 67,042 | [reports__codex__inputs__G6L_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6L_repro.sha256.jsonl) |
| `reports/codex/inputs/G6M_repro` | 36 | 122,865 | 36 | 122,865 | [reports__codex__inputs__G6M_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6M_repro.sha256.jsonl) |
| `reports/codex/inputs/G6N_repro` | 45 | 172,597 | 45 | 172,597 | [reports__codex__inputs__G6N_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6N_repro.sha256.jsonl) |
| `reports/codex/inputs/G6O_repro` | 51 | 206,856 | 51 | 206,856 | [reports__codex__inputs__G6O_repro.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__codex__inputs__G6O_repro.sha256.jsonl) |
| `reports/showcase` | 8 | 600,545 | 8 | 600,545 | [reports__showcase.sha256.jsonl](file:///D:/eab-evidence/_manifests/reports__showcase.sha256.jsonl) |

### 留在 reports 的文件类别

- 历史 `*_report.md` 正文与小型文字/JSON 汇总：保留为证据导航，不重新计算或更新历史结论。
- `reports/codex/inputs/` 的 Shi 双读者/对照材料、历史 findings JSON 与审查报告：文档性输入保留；十个 `_repro` 子目录已外移。
- `reports/codex/H1_evidence/`：本工单的计划、审计清单、迁移映射与当前验证；ignored 临时目录不属于可交付文件。
- 根 `reports/` 的小型报告/指标记录及本归档索引：未把它们冒作当前运行证据；实际测试输入已按清单移到 fixtures。

## 晚发现的测试输入与最终核对

快档实跑发现 `M5c_evidence/research_diagnostics.json` 也是固定门输入：从外归档原字节**复制**到 `fixtures/frozen/codex/M5c_evidence/research_diagnostics.json`，782,733 字节，外归档原件及其 SHA256 清单均未修改。最终输入为 **136 搬迁 + 1 复制 = 137 文件，12,445,253 字节**；不重算冻结数据。

[追加映射](codex/H1_evidence/frozen_inputs_addendum.json)；[当前完整输入清单](codex/H1_evidence/frozen_inputs_manifest.json)；[最终校验](codex/H1_evidence/archive_validation.json)。`archive_result.json` 的 `input_manifest` 是当时读取的路径（当时为 136 项），不是现已追加为 137 项的内容快照；初批专属清单明确记录复原方法，不伪称有未保存的原清单文件哈希。回退时，追加复制项的原件已在外归档，不应再次覆盖它。

单文件上限为 1,000,000 字节；唯一例外是本单冻结、只准机械重键的 `tools/exact_construction_policy.json`。具名门见 [test_repository_size.py](../tests/test_repository_size.py)，包含无 Git 副本中实际写入 1,000,001 字节文件后报红的牙。
