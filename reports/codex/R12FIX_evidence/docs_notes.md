# R12FIX 文档同步记录

## 输入数核对

`reports/codex/inputs/G6L_findings.json` 的 confirmed_counts 为 0 critical / 1 major / 0 minor，findings 数组仅含 G6L-01。工单模板中的“6 条”“11 条”不构成额外发现，不制造不存在的逐条记录。

## 已同步内容

- `docs/canon_map.md` 第八节保留历史三列，增加 M4a 第四列；逐项登记冻结 15 输入配对 × 3 步 / 45 帧、局部 G5 差异台账、离线适配器与接缝提案，以及未满足的完整 G1 / G4 / G5 / 在线切换合同。
- `README.md` 与 `docs/canon_map.md` 顶部登记 R12FIX 当前边界；新增 `docs/r12fix_design_sync.md`，明确闭集前检、未知返回保守、站点/上下文 pin、人工例外不等于机器证明、测试驱动子树显式豁免和 M4a 保留。
- `README.md` 的 L5 历史表订正 bdda_df 主特征键全面唯一的陈述：M4a 四例合计 9 条额外主键重复，须保留 multiplicity 与第二参考，不无声去重。
- M0 所有者 2026-10-12 的退出决定保持；本单不宣称 0 critical / 0 major 的独立 G6 已通过，不回写 `D:/E(A, B)` 只读正本。

## 文档局部验证

命令：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests/test_doc_pointers.py tests/test_r7fix_docs.py --basetemp=reports/codex/R12FIX_evidence/tmp/docs`

原样摘要：`15 passed in 0.20s`。

本记录不替代根代理最终全套、变异、扫描证据。最后文档复验仍为 `15 passed in 0.20s`；本树设计同步引用的 5 个 `test_l01_*` 函数名通过 AST 存在性核验，README/canon_map 保持原 LF 换行。未运行 `fix_canon_ptrs.py --apply`，由根代理统一执行。

## 追加：跨函数白名单钉住与测试 helper 误报审核

- 文档改为完整模块 AST + 全部 src/tests Python 原字节依赖图；任何源文件字节/路径集变化均使新增白名单失效，扫描副本使用副本自己的图。
- 已逐函数读取 strict_scan 的 tests 非 closed 且非 test_ 驱动站点，共 298 站点 / 131 函数域；英文逐点候选见 `test_numeric_waiver_review.json`，含代码表达式、路径/行/规则及原文件 SHA-256。
- 282 项 candidate；16 个旧浮点 oracle / legacy tie 站点明确标 needs_parent_review（9 函数域），没有把近似 legacy 参考包装成精确保证或自动安装白名单。
- 补充复验：候选 298 项无重复、理由非空；文档门仍为 `15 passed in 0.20s`。

## 最终策略订正

最终实现不采用“未知返回一概视为已舍入”的中间策略。未证明返回值/副作用摘要的普通调用直接 `closed-unproved-call`，已舍入实参跨界另 `closed-rounded-call`，保留参数舍入传播；existing call sites 逐站点审核，不给同名函数建立普遍安全摘要。README/canon_map/设计同步均已更新。

`test_numeric_waiver_review.json` 是被替换中间策略下 298 个保守误报候选的历史审核证据，不代表最终白名单自动接纳；最终白名单与实测数量以 `tools/exact_construction_policy.json` 及根报告为准。补录 intrinsic 同名遮蔽、`**kwargs`、key 回调、间接写入与装饰器默认拒绝，并列出新增永久门；文档不把中间 298 项计数当最终现存发现。

## 最终依赖范围和 M4a 收集核对

依赖快照最终包含 `src/tests/tools` 的全部 Python 原字节；静态分析仍仅 `src/tests`。README/canon_map/设计文档已区分两个范围。本子任务未修改 src/tests/tools。

M4a 三文件 collect-only 总计 109 项（adapter 56、shadow 29、vv_reader 24），无重复 nodeid，三文件均与 HEAD 原字节一致；见 `m4_inventory.json` 与 `m4_collection.log`。这是收集/完整性核验，不是本轮执行通过声明。R11 和 G6L 历史全套时间分别为 1228.19s / 1460.86s，机器负载不同，不承诺四进程分片必达900s。R11最慢20项中bb52合计233.53s只是不完整慢项下界，不是该文件完整计时。

额外排版核验抓到 §8 新列第三/四列之间缺少分隔符，已修复；现表头与每个数据行均为实际四列（5个pipe），没有仅在同格追加文字冒充新列。

## 最终 helper 调用边界逐点复核

按根代理分工，本子任务只处理剩余 `tests/test_*.py` 条目，不触及 red_teeth 负责的独立 oracle/perf helper 非 test 文件。读取实际调用方、被调辅助函数和测试用途，完成 704 个 `closed-unproved-call` 站点 / 250 函数域：704 个 reviewed_candidate，0 个 needs_review。每条保留原调用表达式、限定 callee 和英文具体理由，另记录 caller/callee 原字节及可解析 AST 哈希。

其中 220 站点 / 59 函数域是明确的 legacy scope exemption：有限差分、显示残差、旧采样/接近筛选、旧噪声窗口、旧 tie/诊断参考等，不冒称精确主 oracle。精确 Fraction/integer oracle、给定输入生成、actual SUT 调用、I/O/拓扑记账分别归类；不把同名函数授予普遍安全摘要。`test_legacy_call_review.json`、`test_legacy_call_scope_exemptions.json` 与 `test_legacy_call_review_summary.json` 是本轮有限人工候选证据，须经完整站点/模块 AST 及全部 src/tests/tools 原字节依赖图匹配后才可安装，不自动刷新白名单。

本次复核未编辑 src/tests/tools、未运行长全套。输入 key 集 704 项完整覆盖、无重复，JSON 解析/非空理由/真实函数 AST 存在性均通过。设计同步 §4 已链接这些精确边界记录。

## 默认拒绝边界追加（属性/隐式算术）

独立追加审计指出注解/dunder/普通属性、f-string、% 格式化，以及 int/int、负幂、Fraction×float 和混合 sum 可携带/产生隐式舍入。设计同步已明确最终自动证明的算术子集只限纯整数字面量 AST；变量算术（包括真实 Fraction 算法）、AugAssign、sum 与未知属性/格式化仍逐站点人工审查，不能靠名字或注解猜类型。不将先前704调用边界审核误当成对新增算术/属性站点的自动授权。等待新增 raw scan 后另作有限逐点审核。

## 新增算术/属性 helper 审核完成

`final_raw_scan_v2.json` 减 `final_raw_scan.json` 中 tests/test_* 独立 helper 新增 4727 站点 / 550 函数域；逐站点候选见 `test_driver_helpers_positive_subset_review.json`。其中 630 属性/格式化站点复用 red_teeth 对相同精确表达式的已审理由；其余结合显式 Fraction lift、实参类型链、整数拓扑、给定输入生成、终端诊断及故意内部变异用途审核，未将整个 test 文件作为 harness 放行。0 needs_review，723 站点 / 87 域明确 legacy 近似/有限观察豁免，另表 `test_driver_helpers_positive_subset_exemptions.json`，汇总见 `test_driver_helpers_positive_subset_summary.json`。

特别核实：`_rounding_cells` 的 3/7 和 2*ulp 只选给定浮点 anchors，F lift 后 midpoint/jitter 才是精确构造；`_power_cases` 的负幂基数是 F(2)，半整数p乘偶数指数后 int 转换为精确整数；`_finite_contact` 位移由参数网格保留为 Fraction。原字节/调用方 AST 哈希和代码上下文逐点保存；不是机器类型证明，也不泛化新调用。新增三组 implicit-arithmetic / annotation-reflection / formatting 永久门名称已据当前测试 AST 核验并同步设计文档。
