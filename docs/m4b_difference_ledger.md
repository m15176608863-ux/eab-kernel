# M4b 只读 shadow 差异台账

## 1. 审计边界与输入

实际独立进程回放覆盖 **15 例全部默认时程，共 1810 步**；raw-df05 与 post-df06 两个时间面均审计。审计 GREEN，未分类 0，未新增类别。所有类别和独立 Fraction 局部几何判据沿用 [M4a 台账](m4_difference_ledger.md)；不是物理等价、真正 eab 替换或完整运动首入的证明。

回归入库只保留各例前 30 步，合计 450 步；15 个 gzip 共 **578,345 B**，仅含步初几何、显式参数和两时间面 Tuple7。完整原快照合计 **15,093,485 B** 留在 b-DDA 专用工作树 build 内。完整回放的规范化逐条分类、计数与哈希位于 [full_replay](../reports/codex/M4b_evidence/full_replay/)，不会丢弃 MATCH 行或重复原始行。

前 30 步投影把 header.requested_steps 和 end.completed_steps 改为 30；manifest 明记这是重封装的前缀，不伪称原运行只做 30 步。原 header、end、完整原文件 SHA256、最终 exe、bb/db 输入哈希均在 [manifest](../fixtures/m4b_shadow/manifest.json)。本文件记录额外全 1810 步独立审计，以 [全时程摘要](../reports/codex/M4b_evidence/full_replay/summary.json) 为准。

源快照最初来自 pilot；已逐文件核对 15 个 pilot 与最终 byte matrix 运行的完整快照 SHA256 全同。fixture manifest 现指最终 modified_runs 源路径；无需用路径变化冒充重新运行。

## 2. 冻结 450 步与完整 1810 步计数

| 类别 | 前30步 raw-df05 | 前30步 post-df06 | 完整 raw-df05 | 完整 post-df06 |
|---|---:|---:|---:|---:|
| ANGULAR_WINDOW_COVER_NOT_SELECTED | 3012 | 1424 | 12793 | 5674 |
| EXACT_LOCAL_COVER_NOT_SELECTED | 3168 | 1529 | 11983 | 4858 |
| LEGACY_DUPLICATE_PRIMARY_REFERENCE | 270 | 9 | 1502 | 18 |
| LEGACY_OUTSIDE_FINITE_EDGE_WINDOW | 9271 | 6305 | 55470 | 42710 |
| LEGACY_VV_DIRECTION_OUTSIDE_OPEN_CONE | 1069 | 1069 | 5193 | 5193 |
| MATCH | 14286 | 17513 | 76854 | 91098 |
| VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL | 399 | 399 | 2575 | 2575 |

raw 与 post 计数不同来自 df06 有序历史转移/换半，两个时间面不能混称一个检测表。eab 每步只由几何和窗口枚举一次；任何 legacy 候选、排序、状态都不裁剪 eab。分类不把未选择局部盖判成 legacy 的物理错误。

## 3. 与 M4a 前三步的一致性

**45/45 帧分类计数完全相同**，44/45 帧逐条分类也完全相同。唯一逐条差异在 bbv01 第 3 步，两条 eab-only 分类互换，计数恰好抵消，故不能只核总数：

| 规范键 | M4a | M4b | 独立严格角窗判据 |
|---|---|---|---|
| `VE(21;59,60)` | `ANGULAR_WINDOW_COVER_NOT_SELECTED` | `EXACT_LOCAL_COVER_NOT_SELECTED` | 旧：`OUTSIDE_LOCAL_CONE_WINDOW`；新：通过 |
| `VE(59;21,22)` | `EXACT_LOCAL_COVER_NOT_SELECTED` | `ANGULAR_WINDOW_COVER_NOT_SELECTED` | 旧：通过；新：`OUTSIDE_LOCAL_CONE_WINDOW` |

该帧参数完全相同，legacy post-df06 有序 Tuple7 与 M4a df07 导出完全相同。这两条在双方均未被 legacy 选择；不是 tuple 时间面改写，也不是 M4a 分类器被改动。变动来自输入几何的 binary64 末位：例如顶点59 y 从 `97.00000000000001` 到 `97.00000000000003`，顶点21 y 从 `2.1469837675345558e-16` 到 `2.1470857157964797e-16`，局部支撑在严格零角窗边界翻转；放宽到 sin(3°) 后两侧均有效。

完整解释在 [bbv01 audit](../reports/codex/M4b_evidence/replay/bbv01/audit.json) 的 m4a_comparison。每个改变的规范键分别列出相关顶点及法锥邻边顶点坐标、d0/h1 变化、legacy 行重数、两侧放宽与严格 oracle 判据；不允许一处无关坐标变化豁免全帧。M4a 原冻结文件未改动；无关于哪个求解器物理正确的声称。

## 4. 各例时程

| 算例 | 全时程回放步数 | 冻结步数 | 未分类 |
|---|---:|---:|---:|
| bb52 | 50 | 30 | 0 |
| bb12 | 100 | 30 | 0 |
| bb50 | 50 | 30 | 0 |
| bb51 | 50 | 30 | 0 |
| bb03 | 100 | 30 | 0 |
| bb05 | 100 | 30 | 0 |
| bb06 | 100 | 30 | 0 |
| bb09 | 100 | 30 | 0 |
| bb10 | 100 | 30 | 0 |
| bbv01 | 100 | 30 | 0 |
| bbv01_dbv01a | 400 | 30 | 0 |
| bbv02 | 100 | 30 | 0 |
| bbv02_dbv02a | 400 | 30 | 0 |
| bbF038 | 30 | 30 | 0 |
| bbS038 | 30 | 30 | 0 |

## 5. 读取、失败与变异门

`tools/m4_shadow_replay.py` 严格核 header 字段/版本/模式、列名顺序、行宽、整数身份、有限数、跨块邻接、参数完备、逐步稳定拓扑、连续步号及终止计数；任何失败返回 2、持久化 audit RED，不写回源快照。空 legacy 表是合法空表，不能让 eab 停止枚举。

具名门：`tests/test_m4b_shadow_replay.py::test_real_snapshot_input_mutations_fail_closed` 实际改输入，覆盖少列、表头错位、Tuple 数据错位、步跳跃、缺步、截尾、非有限数、缺参数、重复顶点及生产者失败；`test_actual_l5_angle_window_defect_is_caught_by_replay_gate` 将实际生产枚举内部 cone_tol 置零，使未分类/冻结计数断言报红；`test_actual_unknown_classifier_result_makes_audit_red` 在实际分类函数注入未知类并验证 CLI RED。没有在被测路径之后追加假接触。

独立 R3 发现输出与输入存在硬链接时，仅 resolve 路径比较会漏掉文件同一性，造成源快照被覆盖。修复后在任何写入前用 samefile 核输入与两个输出以及输出之间的别名；`test_hardlinked_outputs_fail_without_mutating_source_or_existing_files` 三种硬链接反例均返回 2 且原文件逐字节不变。此冲突无法安全写 audit.json 时，明确在 stderr 报 RED，而非为了写红报告破坏输入。

冻结门：`test_fifteen_family_thirty_steps_have_frozen_classified_raw_and_post_tables` 核每例快照 SHA256、两时间面全步逐条分类摘要、冻结计数和 M4a 前三步计数/逐键解释；参数化产物互异由 `test_capture_manifest_has_exact_family_and_distinct_detection_products` 看护。

复跑单例：
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/m4_shadow_replay.py fixtures/m4b_shadow/bb52.jsonl.gz --expected-steps 30 --m4a-fixture bb52_N3 --out reports/codex/M4b_evidence/rerun/bb52
python -X utf8 -m pytest -q tests/test_m4b_shadow_replay.py
```

复跑全部前缀并重新冻结须显式执行 `tools/m4b_freeze_replay.py reports/codex/M4b_evidence/replay_sources_final.json`；它会验证完整来源，再裁切前30步并运行4个独立 Python 子进程。全时程可把同一 CLI 的 snapshot 参数换为 final sources JSON 中路径，不给 `--expected-steps 30`。

边界：这些门不代替真正替换所需的 Tuple7/ContactStore 映射、df06 顺序历史、双参考选择、锁态轨迹、装配/力/位移同构，也不构成全仓库 G6 退出判据。
