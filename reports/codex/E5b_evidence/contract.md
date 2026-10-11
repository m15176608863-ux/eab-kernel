# WO-E5b 执行契约

- 目标：修复/迁移 E5a2 的49红；默认精确 + 显式 contact_window；最早逃逸、首入、冻结精确化；全套绿。
- 范围：仅 D:/eab-wt/cx-e2；src/tests/tools/docs/README 与本工单证据。其它仓库只读。
- 非目标：不提交、不推送、不 reset/checkout/stash/worktree，不删 fixtures，不改变姊妹内核，不声称 G6 或工程验证。
- 成功判据：全部原测试节点保留，不加 skip/xfail；49项处置及改写台账；指定内部突变对应目标断言；全套测试零失败；900s为实测性能目标。
- 验证：PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=reports/codex/E5b_evidence/tmp/final；fix_canon_ptrs.py --apply；源哈希、fixture哈希、测试节点审计。
- 回滚锚：35667084fd2b6d3c89bd3d284534feea2d5771a5，初始工作树干净；baseline/保存该提交的全部src/tests/tools Python字节。用户禁止Git写操作，若需退回仅对本单自有修改做逐文件恢复。
- 边界：新鲜worktree门本单受用户禁止，最终只能报告本树验收；完整六路独立G6不伪称。
