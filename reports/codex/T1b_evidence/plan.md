# WO-T1b 执行合同与进度

- Target：在给定有理多边形上，以独立证书判定公差平移困住，找到非退化形貌阈值；不把静力无界称锁定。
- Scope：仅本工作树及 D:/eab-evidence/reports/codex/T1b_evidence；不做 Git 写。
- Non-goals：不改冻结设计、tia2d-2 schema、姊妹代码、求解器数学合同；P2 可选。
- Success：独立证书核验、闭式与变异门、刚体与缩放门、快档与四分片全档、中文报告与精确证据。新鲜工作树与 Claude 独立核查须另由所有者安排。
- Verification：`tools/tia2d_t1b_run_gates.py --name <new> [--runslow]`；定向 `pytest -p no:cacheprovider --basetemp reports/codex/T1b_evidence/tmp/<new>`；静态/纯度门。
- Rollback：[rollback.json](rollback.json) 所列原字节备份，均逐项与 HEAD 核对；其他仅新增文件。恢复前先确认没有所有者后续修改，禁止自动覆盖。

## 单一在办阶段

1. COMPLETE：环境与冻结字节。基线一次全档在冻结 HEAD 字节副本中运行，预计约 25–35 分钟（参考 T1a 末次 1596 s，非本轮实测）；不阻止新代码开发。
2. COMPLETE：P0 通用算法、独立核验、120组政策/算例条目及最终数据。
3. COMPLETE：P1 非退化族、36点阈值/导数、闭式对照和设计曲线。
4. DELIVERED_PARTIAL：收尾全档14848项中2项仓库静态门失败（测试helper语法），最小修复后两原失败门通过、当前完整快档8800项GREEN。按一次收尾全档成本合同不追加完整四分片重跑；原RED、字节快照、完整数据及PARTIAL报告均归档交付。Claude独立核查与新鲜Git树核验待所有者安排。

并行任务只分工，不重复全档。基线采用只读 `git archive`；它是字节导出，不是新鲜 Git 工作树。

## 早期订正

严格屏障的紧性及正裕量排除“δ=0 被困住、任意正 δ 即逃逸”的标准例。改用正但很小的临界公差，具体证明与回归记录在最终报告；不改变设计合同。
