# WO-R9FIX 执行合同

- 目标：修复 G6I-01～06，精确构造统一并配 AST 防回归门；不宣称 M0 独立退出。
- 范围：D:/eab-wt/cx-e2 的 src、tests、tools、docs、README 及 reports/codex/R9FIX*。
- 非目标：姊妹仓库、其他 worktree、理论正本均不写；不做 Git 写操作，不删 fixture、不降低旧门。
- 验收：每条修前红、修后绿、真实被测路径变异目标断言红；完整收集所有测试恰跑一次且 0 skip/fail/error；指针门绿。
- 验证：PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider；新门、四独立完整模块分片全套、fix_canon_ptrs --apply。
- 回滚锚：baseline_tracked.zip + initial_state.json（字节快照及 SHA-256）；只按明确文件恢复，不 Git reset/checkout。
- 输入矛盾：“11 条逐条”与 JSON 的 6 条不符；采用 6 条确认发现 + 5 项结构性/同类工作组成报告 11 行，不编造额外审查 finding。
- 新鲜 worktree：本单明确禁止，不执行；独立 G6 仍由所有者另排。
