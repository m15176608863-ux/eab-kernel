# WO-E5a2 执行契约

- 起始状态：`codex-work` / `5b09ea399a5277f359f833312638c9bb86f09192`；起始 `git status --short` 空。
- 范围：只修改 `D:\eab-wt\cx-e2`；系统临时目录可用，但本单主动将 pytest 与 Python 临时路径置于本证据目录。旧系统临时文件不删除、不移动。
- 禁止：Git 写操作、姊妹仓库/其他工作树修改、删除 fixtures、减少原测试网格、降精度、skip/xfail。
- 目标：完成 A1 精确一般表面旧入口，A2 明确且测试固定一般源面局部盖解释边界，A3 精确搜索窗与欧氏报告带；profile 驱动答案不变提速；全套目标 <=900 秒（理想 <=600 秒）。
- 回滚锚：起始 HEAD 和 `tmp/profile_baseline/` 原始源码/测试/tools 字节副本；只供人工定点恢复，不运行 checkout/reset。
- 验证：独立精确 oracle、每项优化快路/参考对拍、内部源码突变命中目标断言、完整测试库存及原参数格保留、`fix_canon_ptrs.py --apply`、最终独占全套及前后源哈希。
- 复跑：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 reports/codex/E5a2_evidence/verify_run.py run final -- -m pytest -q -p no:cacheprovider tests --basetemp=reports/codex/E5a2_evidence/tmp/final_pytest --tb=short --durations=30 --junitxml=reports/codex/E5a2_evidence/final.xml`（PowerShell 用 `$env:PYTHONDONTWRITEBYTECODE='1'`）。
- 验收限制：用户禁止新建 worktree；本工作单不冒称新 worktree/G6 里程碑退出。任何未达项按 PARTIAL 报告。

## 计划状态

1. 基线核验与冻结：完成。六文件完整 cProfile 全部通过，前20热点已交付。
2. A1/A2/A3、整数化优化及 interlock 最小桥接：实现和定向验证完成，源码冻结。
3. 突变、库存、文档与最终全套：突变/逐条台账/指针修正完成；完整全套尝试完成：7953 passed / 49 failed，墙钟1578.67s；失败后有短诊断并发，不算独占速度成绩；原7907节点全部保留。最终状态：E5a2_PARTIAL：全套49失败（竖墙最早逃逸、旧门语义迁移及突变牙）；≤900s未达，实测墙钟1578.67s。
