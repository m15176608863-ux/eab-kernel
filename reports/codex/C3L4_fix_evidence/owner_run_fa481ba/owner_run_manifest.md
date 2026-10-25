# 所有者新鲜运行证据索引

来源：`C:\Users\m1517\AppData\Local\Temp\claude\C--Agent--claude\659f270b-c2f6-43a9-9717-6dc28c605be4\scratchpad\cx\c3l4fix5_fresh_out`；提交（调用者标注）：`fa481ba`。
只读快照，不复制大文件、不启动运行、不代签验收；退出码仅取 summary.txt / JSON exit_code。

| 层 | 状态 | 退出码 | 原样最后一行（JSON 优先） |
|---|---|---:|---|
| build | complete | 0 | `Total Test time (real) = 172.21 sec` |
| c0diff | complete | 0 | `EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS` |
| c1diff | complete | 0 | `C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086` |
| consumer | complete | 0 | `EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0` |
| l1diff | complete | 0 | `C3L1_DIFF assembly=186 first_order=186 lock=404 mismatch=0 strict_fields=495` |
| l3diff | complete | 0 | `C3L3_DIFF limit=292 critical=2528 mismatch=0` |
| l4_asym0 | pending | unknown | `C3L4_DIFF sensitivity=140 mismatch=0` |
| l4_asym1 | pending | unknown | `C3L4_DIFF sensitivity=139 mismatch=0` |
| l4_asym2 | pending | unknown | `C3L4_DIFF sensitivity=140 mismatch=0` |
| l4_asym3 | pending | unknown | `C3L4_DIFF sensitivity=141 mismatch=0` |
| l4_asym4 | pending | unknown | `C3L4_DIFF sensitivity=142 mismatch=0` |
| l4_asym5 | pending | unknown | `C3L4_DIFF sensitivity=134 mismatch=0` |
| l4_branch | pending | unknown | `C3L4_DIFF sensitivity=14 mismatch=0` |
| l4_formal | pending | unknown | `C3L4_DIFF sensitivity=280 mismatch=0` |
| l4_t1b | pending | unknown | `C3L4_DIFF sensitivity=72 mismatch=0` |
| l4_thickness | pending | unknown | `C3L4_DIFF sensitivity=50 mismatch=0` |
| l4diff | pending | unknown | `L4_SHARD_AGGREGATE status=pending shards=10 cases=341/341 sensitivity=1252 mismatch=0` |
| meta | complete | 0 | `C3L4_META cases=64 channels=163 mismatch=0` |
| optdiff | complete | 0 | `OPT_DIFF selected=745 completed=745 mismatches=0` |
| python_full | pending | unknown | `` |
| relabi | complete | 0 | `EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0` |

L4 分片清单：341/341 个算例；0 条合并校验错误。清单来自冻结输入与生成器声明，未运行求解器。
L4 artifact_complete=True；process_exit_status=pending。完整 JSON 可产生比较台账，但未知退出码始终保留 pending，不推定进程成功。

日志/JSON 的字节与 SHA-256、DLL 字段哈希、原始 summary.txt、计数及诊断摘录见 [manifest](owner_run_manifest.json.gz)。大型诊断仅保留计数/分类及内容哈希，详情留在来源 JSON。
L4 台账：[JSON.gz](errata_ledger.json.gz) / [Markdown.gz](errata_ledger.md.gz)（无损压缩，逐字节读回核验）。
Python 全档若位于另一目录，此索引保留 pending；不据此推断所有者运行失败。

OWNER_RUN_PACK status=partial layers=21 pending=12 failed=0 errata=generated
