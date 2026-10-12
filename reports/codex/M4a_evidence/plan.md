# WO-M4a 执行合同与计划

- 目标：15 例家族的离线影子接缝、ContactRecord 适配、逐条分类的 T1 型门与中文证据。
- 范围：仅 D:/eab-wt/cx-m4；外部仅只读复制输入/exe；所有运行在本树 sandbox。
- 非目标：b-DDA 开关落地、替换求解器、复审线修复、commit/push/worktree 操作。
- 成功：15例各3步；无未分类差异；三处内部变异被对应断言捕获；全套绿；静态构造0违例。
- 验证：PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider --basetemp reports/codex/M4a_evidence/tmp；python -X utf8 tools/check_exact_construction.py；必要时 tools/fix_canon_ptrs.py --apply。
- 回滚锚点：开始时 git status --short 为空；分支 m4-seam，HEAD 0e9ef93。原有文档/脚本/溯源副本在 rollback/，不执行回滚或 git 写操作。
- 特殊边界：禁止新建worktree，故本单全绿不等于新鲜worktree或独立六路G6。

## 单项进度
1. 已完成：只读接缝地图与数据格式/家族核实。
2. 已完成：沙箱15例各3步×双跑、120文件与溯源。
3. 已完成：L5静态适配、VV身份读取修复、45帧逐条分类和锁计数门。
4. 已完成：三处内部变异目标断言已捕获并恢复；静态门0违例；全套10923 passed in 1191.84s，中文报告M4a_DONE。
