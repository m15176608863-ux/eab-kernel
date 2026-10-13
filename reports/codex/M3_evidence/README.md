# M3 证据入口

主结论与未达项以 [中文报告](../M3_report.md) 为准；理论先行稿见 [设计](../../../docs/m3_global_entrance_design.md)。这不是独立六路G6退出证据。

## 核心证据

1. [起点12662节点四分片](baseline_suite/summary.json)；[最终12761节点四分片](final_suite_r3/summary.json)；[最终独立汇总核对](final_audit.json)：全部GREEN、0skip；[逐要求验收矩阵](acceptance_matrix.json)仍为M3_PARTIAL。
2. [二维27367查询汇总](scans2d/summary_all.json)：每家族JSON另含全部查询点、存储胞标签、盖片中点与12条随机方向射线；bb52只重放历史1260平移，不含其大剖分穷尽探针。
3. [三维6110探针](three_d_scan.json)：lazy凸片对探针而非显式3D overlay；[逐项范围与import清单](three_d_summary.json)。
4. [392旧新逃逸逐字段对照](three_d_replay_comparison.json)，及[旧值](three_d_old_replay.json)/[新值与零调用](three_d_new_replay.json)。
5. [九项内部变异实际红断言](mutations/summary.json)，每项同目录原始pytest输出，没有突变覆盖生产源文件。
6. [理论、文献与独立代码审查](theory_audit.md)。该审查不是六路G6。
7. [原三项scope续期](static_renewal.json)与[16项docstring续期](doc_only_renewal.json)：3103项总数不变，新增豁免0。
8. [大文件完整路径及SHA-256](large_artifacts.json)：只在被忽略的tmp目录；[改动清单](change_inventory.json)在交付收尾生成。

## 复跑

在本仓库根目录PowerShell中：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = (Join-Path $PWD 'reports/codex/M3_evidence/tmp')
$env:TMP = $env:TEMP
python -X utf8 tools/m3_scan_evidence.py --section all
python -X utf8 reports/codex/M3_evidence/three_d_scan.py --help
python -X utf8 tools/m3_mutation_evidence.py
python -X utf8 tools/m3_run_gates.py --name owner_recheck_01
python -X utf8 tools/m3_finalize_evidence.py
python -X utf8 tools/fix_canon_ptrs.py --apply
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_doc_pointers.py
```

全套运行器要求输出名称尚不存在，防止覆盖既有证据；`--source`只接受本工作树的M3 tmp内冻结源码。
三维脚本的scan、旧新replay是分开的模式，请以其`--help`为准。旧版本回放须用baseline冻结源码，不能拿新代码两次充当旧新比较。汇总审计工具固定核本次`baseline_suite`与`final_suite_r3`；复查新名字的运行仍须另读其summary，不能误以为此工具已改指向。

## 未被冒称为绿的历史运行

- [first export](final_suite/ABORTED.json)：强完备家族扩展后停止。
- [r2](final_suite_r2/ABORTED.json)：文档摘要位置门真实失败；[原失败输出](final_suite_r2/shard_2.txt)。修改文档而未弱化断言，再跑r3全套。
- `three_d_existing_gates.log`有607通过，但外层工具结束时被中断，故只是补充原始日志；正式结果只取完整四分片执行账。

数值/源码和测试在r3前冻结；之后报告及汇总措辞的收尾不修改被测实现。所有者提交前仍应独立复核。
