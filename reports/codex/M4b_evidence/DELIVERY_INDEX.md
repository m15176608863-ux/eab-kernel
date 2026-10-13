# WO-M4b 交付索引

两个专用工作树保持未提交；未批准真正 eab 替换。此索引覆盖代码、夹具、报告、审查与运行证据。

## 主要入口

- [中文完成报告](file:///D:/eab-wt/cx-m4/reports/codex/M4b_report.md)
- [两侧逐文件变更与哈希](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/change_inventory.json)
- [15 例三模式逐字节矩阵](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/byte_matrix.json)
- [全时程差异台账](file:///D:/eab-wt/cx-m4/docs/m4b_difference_ledger.md)
- [最终 eab 全套与静态门](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/summary.json)
- [b-DDA 全套验证摘要](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/bdda_verification_summary.json)
- [交付文件哈希清单](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/delivery_manifest.json)
- [最终交付 QA（生成后）](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/final_delivery_qa.json)

## 保留的目录与大体积证据

- [eab 专用工作树](file:///D:/eab-wt/cx-m4)
- [b-DDA 专用工作树](file:///D:/bdda-wt/shadow)
- [紧凑 30 步回归夹具](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow)
- [完整 1810 步逐记录回放](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay)
- [450 帧冻结前缀回放](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay)
- [本次全部 eab 证据](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence)
- [eab 最终新鲜导出（无 Git 元数据）](file:///D:/eab-wt/cx-m4/build/m4b_fresh_r2)
- [首轮环境失败日志（不计为通过）](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1)
- [b-DDA 原始运行/构建/复算证据](file:///D:/bdda-wt/shadow/bdda2/build/m4b)
- [改前源码/二进制回退锚](file:///D:/bdda-wt/shadow/bdda2/build/m4b/baseline)
- [改前拟改文件副本](file:///D:/bdda-wt/shadow/bdda2/build/m4b_source_before)
- [最终安静计时全部样本](file:///D:/bdda-wt/shadow/bdda2/build/m4b/timing.json)

## 两侧改动文件

### bdda

- [00_START_HERE.md](file:///D:/bdda-wt/shadow/00_START_HERE.md) — modified，+4/−0
- [HANDOFF.md](file:///D:/bdda-wt/shadow/HANDOFF.md) — modified，+5/−0
- [bdda2/CMakeLists.txt](file:///D:/bdda-wt/shadow/bdda2/CMakeLists.txt) — modified，+7/−0
- [bdda2/README.md](file:///D:/bdda-wt/shadow/bdda2/README.md) — modified，+27/−0
- [bdda2/build.bat](file:///D:/bdda-wt/shadow/bdda2/build.bat) — modified，+2/−0
- [bdda2/driver/main.cpp](file:///D:/bdda-wt/shadow/bdda2/driver/main.cpp) — modified，+30/−0
- [bdda2/driver/run.hpp](file:///D:/bdda-wt/shadow/bdda2/driver/run.hpp) — modified，+46/−0
- [bdda2/io/detect_snapshot.hpp](file:///D:/bdda-wt/shadow/bdda2/io/detect_snapshot.hpp) — new，+111/−0
- [bdda2/studio/engine_bridge.cpp](file:///D:/bdda-wt/shadow/bdda2/studio/engine_bridge.cpp) — modified，+71/−2
- [bdda2/studio/engine_bridge.hpp](file:///D:/bdda-wt/shadow/bdda2/studio/engine_bridge.hpp) — modified，+6/−1
- [bdda2/studio/main.cpp](file:///D:/bdda-wt/shadow/bdda2/studio/main.cpp) — modified，+1/−1
- [bdda2/test/test_shadow.cpp](file:///D:/bdda-wt/shadow/bdda2/test/test_shadow.cpp) — new，+77/−0
- [docs/PROJECT_STATUS.md](file:///D:/bdda-wt/shadow/docs/PROJECT_STATUS.md) — modified，+4/−0
- [studio/engine2.py](file:///D:/bdda-wt/shadow/studio/engine2.py) — modified，+32/−3
- [tests/test_m4b_detect_switch.py](file:///D:/bdda-wt/shadow/tests/test_m4b_detect_switch.py) — new，+132/−0
- [tools/bdda/verify_cpp.py](file:///D:/bdda-wt/shadow/tools/bdda/verify_cpp.py) — modified，+4/−1
- [tools/bdda/verify_fast.py](file:///D:/bdda-wt/shadow/tools/bdda/verify_fast.py) — modified，+2/−0
- [tools/bdda/verify_force.py](file:///D:/bdda-wt/shadow/tools/bdda/verify_force.py) — modified，+4/−1
- [tools/bdda/verify_m4b_shadow.py](file:///D:/bdda-wt/shadow/tools/bdda/verify_m4b_shadow.py) — new，+237/−0
- [tools/bdda/verify_t0.py](file:///D:/bdda-wt/shadow/tools/bdda/verify_t0.py) — modified，+2/−0

### eab

- [docs/m4b_difference_ledger.md](file:///D:/eab-wt/cx-m4/docs/m4b_difference_ledger.md) — new，+79/−0
- [fixtures/PROVENANCE.json](file:///D:/eab-wt/cx-m4/fixtures/PROVENANCE.json) — modified，+136/−0
- [fixtures/m4b_shadow/bb03.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb03.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb05.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb05.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb06.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb06.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb09.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb09.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb10.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb10.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb12.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb12.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb50.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb50.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb51.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb51.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bb52.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bb52.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bbF038.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bbF038.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bbS038.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bbS038.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bbv01.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bbv01.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bbv01_dbv01a.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bbv01_dbv01a.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bbv02.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bbv02.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/bbv02_dbv02a.jsonl.gz](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/bbv02_dbv02a.jsonl.gz) — new，+binary/−0
- [fixtures/m4b_shadow/byte_matrix.json](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/byte_matrix.json) — new，+5869/−0
- [fixtures/m4b_shadow/manifest.json](file:///D:/eab-wt/cx-m4/fixtures/m4b_shadow/manifest.json) — new，+1126/−0
- [tests/test_m4b_byte_evidence.py](file:///D:/eab-wt/cx-m4/tests/test_m4b_byte_evidence.py) — new，+47/−0
- [tests/test_m4b_shadow_replay.py](file:///D:/eab-wt/cx-m4/tests/test_m4b_shadow_replay.py) — new，+184/−0
- [tools/m4_shadow_replay.py](file:///D:/eab-wt/cx-m4/tools/m4_shadow_replay.py) — new，+378/−0
- [tools/m4b_freeze_replay.py](file:///D:/eab-wt/cx-m4/tools/m4b_freeze_replay.py) — new，+110/−0
- [tools/m4b_run_eab_gates.py](file:///D:/eab-wt/cx-m4/tools/m4b_run_eab_gates.py) — new，+108/−0
- [tools/m4b_verify_byte_evidence.py](file:///D:/eab-wt/cx-m4/tools/m4b_verify_byte_evidence.py) — new，+72/−0

## 报告与证据文件逐项链接

以下不逐列 build 中的编译中间文件；其目录已给出。哈希清单不自哈希，最终 QA 另绑定报告哈希。

- [bdda_verification_summary.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/bdda_verification_summary.json)
- [build_delivery_index.py](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/build_delivery_index.py)
- [build_report.py](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/build_report.py)
- [change_inventory.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/change_inventory.json)
- [full_replay/bb03/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb03/audit.json)
- [full_replay/bb03/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb03/normalized.jsonl.gz)
- [full_replay/bb03/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb03/replay.log)
- [full_replay/bb05/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb05/audit.json)
- [full_replay/bb05/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb05/normalized.jsonl.gz)
- [full_replay/bb05/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb05/replay.log)
- [full_replay/bb06/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb06/audit.json)
- [full_replay/bb06/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb06/normalized.jsonl.gz)
- [full_replay/bb06/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb06/replay.log)
- [full_replay/bb09/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb09/audit.json)
- [full_replay/bb09/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb09/normalized.jsonl.gz)
- [full_replay/bb09/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb09/replay.log)
- [full_replay/bb10/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb10/audit.json)
- [full_replay/bb10/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb10/normalized.jsonl.gz)
- [full_replay/bb10/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb10/replay.log)
- [full_replay/bb12/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb12/audit.json)
- [full_replay/bb12/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb12/normalized.jsonl.gz)
- [full_replay/bb12/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb12/replay.log)
- [full_replay/bb50/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb50/audit.json)
- [full_replay/bb50/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb50/normalized.jsonl.gz)
- [full_replay/bb50/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb50/replay.log)
- [full_replay/bb51/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb51/audit.json)
- [full_replay/bb51/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb51/normalized.jsonl.gz)
- [full_replay/bb51/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb51/replay.log)
- [full_replay/bb52/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb52/audit.json)
- [full_replay/bb52/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb52/normalized.jsonl.gz)
- [full_replay/bb52/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bb52/replay.log)
- [full_replay/bbF038/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbF038/audit.json)
- [full_replay/bbF038/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbF038/normalized.jsonl.gz)
- [full_replay/bbF038/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbF038/replay.log)
- [full_replay/bbS038/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbS038/audit.json)
- [full_replay/bbS038/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbS038/normalized.jsonl.gz)
- [full_replay/bbS038/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbS038/replay.log)
- [full_replay/bbv01/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv01/audit.json)
- [full_replay/bbv01/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv01/normalized.jsonl.gz)
- [full_replay/bbv01/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv01/replay.log)
- [full_replay/bbv01_dbv01a/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv01_dbv01a/audit.json)
- [full_replay/bbv01_dbv01a/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv01_dbv01a/normalized.jsonl.gz)
- [full_replay/bbv01_dbv01a/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv01_dbv01a/replay.log)
- [full_replay/bbv02/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv02/audit.json)
- [full_replay/bbv02/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv02/normalized.jsonl.gz)
- [full_replay/bbv02/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv02/replay.log)
- [full_replay/bbv02_dbv02a/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv02_dbv02a/audit.json)
- [full_replay/bbv02_dbv02a/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv02_dbv02a/normalized.jsonl.gz)
- [full_replay/bbv02_dbv02a/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/bbv02_dbv02a/replay.log)
- [full_replay/summary.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_replay/summary.json)
- [full_suite_r1/collection.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/collection.txt)
- [full_suite_r1/environment_error.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/environment_error.md)
- [full_suite_r1/export_manifest.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/export_manifest.json)
- [full_suite_r1/node_coverage.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/node_coverage.json)
- [full_suite_r1/shard_1.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_1.txt)
- [full_suite_r1/shard_1_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_1_nodes.txt)
- [full_suite_r1/shard_2.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_2.txt)
- [full_suite_r1/shard_2_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_2_nodes.txt)
- [full_suite_r1/shard_3.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_3.txt)
- [full_suite_r1/shard_3_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_3_nodes.txt)
- [full_suite_r1/shard_4.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_4.txt)
- [full_suite_r1/shard_4_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r1/shard_4_nodes.txt)
- [full_suite_r2/collection.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/collection.txt)
- [full_suite_r2/exact_construction.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/exact_construction.txt)
- [full_suite_r2/export_manifest.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/export_manifest.json)
- [full_suite_r2/node_coverage.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/node_coverage.json)
- [full_suite_r2/shard_1.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_1.json)
- [full_suite_r2/shard_1.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_1.txt)
- [full_suite_r2/shard_1_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_1_nodes.txt)
- [full_suite_r2/shard_2.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_2.json)
- [full_suite_r2/shard_2.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_2.txt)
- [full_suite_r2/shard_2_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_2_nodes.txt)
- [full_suite_r2/shard_3.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_3.json)
- [full_suite_r2/shard_3.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_3.txt)
- [full_suite_r2/shard_3_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_3_nodes.txt)
- [full_suite_r2/shard_4.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_4.json)
- [full_suite_r2/shard_4.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_4.txt)
- [full_suite_r2/shard_4_nodes.txt](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/shard_4_nodes.txt)
- [full_suite_r2/summary.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/full_suite_r2/summary.json)
- [independent_r1_r2_checks.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/independent_r1_r2_checks.json)
- [junction_guard_evidence.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/junction_guard_evidence.json)
- [plan.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/plan.md)
- [replay/bb03/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb03/audit.json)
- [replay/bb03/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb03/normalized.jsonl.gz)
- [replay/bb03/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb03/replay.log)
- [replay/bb05/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb05/audit.json)
- [replay/bb05/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb05/normalized.jsonl.gz)
- [replay/bb05/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb05/replay.log)
- [replay/bb06/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb06/audit.json)
- [replay/bb06/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb06/normalized.jsonl.gz)
- [replay/bb06/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb06/replay.log)
- [replay/bb09/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb09/audit.json)
- [replay/bb09/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb09/normalized.jsonl.gz)
- [replay/bb09/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb09/replay.log)
- [replay/bb10/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb10/audit.json)
- [replay/bb10/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb10/normalized.jsonl.gz)
- [replay/bb10/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb10/replay.log)
- [replay/bb12/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb12/audit.json)
- [replay/bb12/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb12/normalized.jsonl.gz)
- [replay/bb12/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb12/replay.log)
- [replay/bb50/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb50/audit.json)
- [replay/bb50/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb50/normalized.jsonl.gz)
- [replay/bb50/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb50/replay.log)
- [replay/bb51/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb51/audit.json)
- [replay/bb51/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb51/normalized.jsonl.gz)
- [replay/bb51/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb51/replay.log)
- [replay/bb52/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb52/audit.json)
- [replay/bb52/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb52/normalized.jsonl.gz)
- [replay/bb52/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bb52/replay.log)
- [replay/bbF038/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbF038/audit.json)
- [replay/bbF038/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbF038/normalized.jsonl.gz)
- [replay/bbF038/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbF038/replay.log)
- [replay/bbS038/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbS038/audit.json)
- [replay/bbS038/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbS038/normalized.jsonl.gz)
- [replay/bbS038/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbS038/replay.log)
- [replay/bbv01/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv01/audit.json)
- [replay/bbv01/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv01/normalized.jsonl.gz)
- [replay/bbv01/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv01/replay.log)
- [replay/bbv01_dbv01a/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv01_dbv01a/audit.json)
- [replay/bbv01_dbv01a/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv01_dbv01a/normalized.jsonl.gz)
- [replay/bbv01_dbv01a/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv01_dbv01a/replay.log)
- [replay/bbv02/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv02/audit.json)
- [replay/bbv02/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv02/normalized.jsonl.gz)
- [replay/bbv02/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv02/replay.log)
- [replay/bbv02_dbv02a/audit.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv02_dbv02a/audit.json)
- [replay/bbv02_dbv02a/normalized.jsonl.gz](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv02_dbv02a/normalized.jsonl.gz)
- [replay/bbv02_dbv02a/replay.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay/bbv02_dbv02a/replay.log)
- [replay_sources_final.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay_sources_final.json)
- [replay_sources_pilot.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/replay_sources_pilot.json)
- [rerun_verification_v2_summary.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/rerun_verification_v2_summary.json)
- [review_R1_modes.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R1_modes.md)
- [review_R2_snapshot_isolation.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R2_snapshot_isolation.md)
- [review_R3_counterexamples.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R3_counterexamples.json)
- [review_R3_counterexamples_recheck.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R3_counterexamples_recheck.json)
- [review_R3_R4_targeted_pytest.log](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R3_R4_targeted_pytest.log)
- [review_R3_replay_input.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R3_replay_input.md)
- [review_R3_schema_recheck.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R3_schema_recheck.json)
- [review_R4_counterexamples.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R4_counterexamples.json)
- [review_R4_document_recheck.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R4_document_recheck.json)
- [review_R4_geometry_ledger.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R4_geometry_ledger.md)
- [review_R5_byte_gate.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R5_byte_gate.md)
- [review_R5_checks.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R5_checks.json)
- [review_R6_capture_protocol.md](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R6_capture_protocol.md)
- [review_R6_checks.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/review_R6_checks.json)
- [timing.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/timing.json)
- [timing_environment.json](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/timing_environment.json)
- [verify_delivery.py](file:///D:/eab-wt/cx-m4/reports/codex/M4b_evidence/verify_delivery.py)

所有原始失败、变异、修后复核和空 junction 负门布局均保留；没有自动清理或隐藏失败。
