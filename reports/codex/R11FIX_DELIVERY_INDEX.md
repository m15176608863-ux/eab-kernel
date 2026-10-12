# R11FIX 交付索引

工作树未提交；本索引给出全部实现/测试/文档及关键证据链接。

## 实现、门和文档

- [README.md](file:///D:/eab-wt/cx-e2/README.md)
- [docs/canon_map.md](file:///D:/eab-wt/cx-e2/docs/canon_map.md)
- [docs/exact_3d_design.md](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md)
- [docs/exact_predicates_plan.md](file:///D:/eab-wt/cx-e2/docs/exact_predicates_plan.md)
- [src/eab/kernel2d/geom.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/geom.py)
- [src/eab/predicates.py](file:///D:/eab-wt/cx-e2/src/eab/predicates.py)
- [tools/check_exact_construction.py](file:///D:/eab-wt/cx-e2/tools/check_exact_construction.py)
- [tests/test_r11fix_static_flow.py](file:///D:/eab-wt/cx-e2/tests/test_r11fix_static_flow.py)
- [tests/test_r11fix_numeric_types.py](file:///D:/eab-wt/cx-e2/tests/test_r11fix_numeric_types.py)
- [docs/r11fix_design_sync.md](file:///D:/eab-wt/cx-e2/docs/r11fix_design_sync.md)
- [reports/codex/R11FIX_report.md](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_report.md)

## 证据与复跑

- [PLAN.md](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/PLAN.md)
- [baseline_manifest.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/baseline_manifest.json)
- [input_manifest.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/input_manifest.json)
- [full_suite.log](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/full_suite.log)
- [full_suite.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/full_suite.json)
- [integration.log](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/integration.log)
- [delivery_audit.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/delivery_audit.json)
- [delivery_manifest.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/delivery_manifest.json)
- [run_full_suite.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/run_full_suite.py)
- [run_integration.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/run_integration.py)
- [verify_delivery.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/verify_delivery.py)
- [verify_artifacts.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/verify_artifacts.py)
- [artifact_qa.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/artifact_qa.json)
- [collection.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/collection.json)
- [build_report.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/build_report.py)
- [k01/result.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/result.json)
- [k01/SUMMARY.md](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/SUMMARY.md)
- [k01/run_final_baseline.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/run_final_baseline.py)
- [k01/run_mutation.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/run_mutation.py)
- [k02/K02_memo.md](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k02/K02_memo.md)
- [k02/run_evidence.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k02/run_evidence.py)
- [scan/readonly_scan_memo.md](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/readonly_scan_memo.md)
- [scan/final_independent_summary.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/final_independent_summary.json)
- [全部证据目录](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/)
- [修前原字节副本](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/baseline/)

baseline 为回滚锚；tmp 为pytest临时夹具；dev/new_scan 为开发过程证据，不是生产入口。
正式源入口仅 tools/check_exact_construction.py 与 src/eab 下的已列模块。
