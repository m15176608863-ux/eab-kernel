# WO-R11FIX 执行契约与计划

- Target：处置输入 JSON 实际列出的 G6K-K01、G6K-K02；完整保留 M4a 和既有门。
- Scope：仅 D:/eab-wt/cx-e2 内必要 src/tools/tests/docs/README 与 reports/codex/R11FIX*；姊妹树、外部设计正本只读。
- Non-goals：不提交、不 Git 写操作、不创建 worktree、不改变 M0 所有者退出决定、不冒充独立 G6、不修改 fixtures。
- Success：每条最终测试在修前代码红、修后绿；关键内部变异击中目标断言；同类扫描；完整 pytest exit 0；文档指针和静态门通过；原有测试/fixtures/输入原字节保持。
- Verification：PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q --durations=20 -p no:cacheprovider --basetemp=reports/codex/R11FIX_evidence/tmp/full_suite；python -X utf8 tools/check_exact_construction.py；python -X utf8 tools/fix_canon_ptrs.py；python -X utf8 reports/codex/R11FIX_evidence/verify_delivery.py。
- Rollback：baseline/ 修前原字节副本 + baseline_manifest.json（HEAD c6ac67cfafbfa4540213215101401186b5284612）；不自动回滚用户内容。
- 输入计数：工单中“6 条”“11 条”与 findings 数组实际2条不符；按2条major修复，不虚造条目。旧第十轮5条由既有完整门保留核验。

## 顺序（同时仅一个总步骤进行中）
1. 已完成：两条红绿/变异及同类扫描；独立46针静态、10025次数值检查通过。
2. 已完成：整合662 passed；本树文档同步，canon --apply 0 rewritten / 0 kept。
3. 已完成：11256 passed in 1228.19s；墙钟1237.053s；211个代码文件无漂移；交付审计与报告链接核验通过。

本树验证不能代替新鲜工作树/独立六路 G6。本单按用户禁止 worktree；设计正本只读，以本树设计补充登记所有者后续同步。

最终启动前追加闭环：首次全套64.145s主动中止，补齐assert message条件求值、Dict交替求值、AugAssign左值单次求值及注解扫描保留；K01最终78新门，整合662全绿后二次冻结，从头重跑全套。
