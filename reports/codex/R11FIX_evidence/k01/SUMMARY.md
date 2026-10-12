# G6K-K01 分项证据摘要

## 结论

已修复。代码最终冻结于第 78 条新增测试完成之后；本摘要不是全套退出证据，全套由主代理执行。

- 修改：[静态门](file:///D:/eab-wt/cx-e2/tools/check_exact_construction.py)。
- 新增：[78 条测试](file:///D:/eab-wt/cx-e2/tests/test_r11fix_static_flow.py)（76 条语义/非回退门，2 条内部变异门）。
- 最终 targeted 原样末行：`168 passed in 13.03s`。
- 最终 76 条语义门对冻结修前 scanner：`59 failed, 17 passed, 2 deselected in 0.41s`。仅排除依赖新代码锚点的 2 条变异 harness，不是 skip/xfail。
- EXCEPTIONS 新增 0 条，原表内容相同；scanner 保留 CRLF；原测试文件未改。

## 根因与修法

旧循环只合流 rounded；aliases 和绑定保留最后一次遍历结果，零次路径被覆盖。绑定还保存 AST Name，而不是赋值时的值：`box=[root]; root=abs` 会回溯改写 box 的原可调用对象。try/match 串行访问替代真正分支，短路/条件表达式/推导式以及异常中间前缀也丢失可调用与对象绑定。

修法采用统一的有限 may-state：每个值是不可变的 `(rounded, callable labels, abstract object refs)` 快照，状态包含绑定和对象堆摘要；所有集合按 union 合流。对象身份只来自源 AST 节点或词法输入名，标签只来自有限源码名/导入命名空间成员，所以不动点不靠次数上限或新建嵌套 AST 终止。循环收集 entry、正常回边、continue、break、return、raise，并把 loop-else 与 break 出口分开。堆用弱更新保存前一轮仍被别名引用的分配对象，但不把容器写入反向污染到其所有元素引用。

## 同类扫描与新增守门范围

| 类别 | 修复/验证点 |
|---|---|
| 循环 | for/while/async-for 零次路径、循环目标绑定、循环携带 callable/container、break/continue、else |
| 分支 | if、IfExp、and/or、链式比较短路，匹配 case 独立入口、guard 失败出口、模式捕获 |
| 异常 | try 各语句/表达式前后可能异常前缀、相互独立 handler、except*、else/finally；with/async-with 的异常抑制后续路径 |
| 推导式 | list/set/dict/comprehension 目标局部作用域、零次/过滤/嵌套、walrus 外层副作用不动点 |
| 生成器 | 外层 iterable 创建时冻结，body 使用消费时外层绑定；next、tuple/list、for、starred、已知方法消费、未知消费者 may-执行、map 链；已立即消费的结果不重新执行已耗尽生成器 |
| 绑定 | 普通别名、容器/属性快照、导入作用域、with/match 绑定、lambda positional-only/keyword-only 默认值、partial 预绑定参数 |
| 最后语法清点 | Assert 成功路径跳过 message；Dict 键值逐对交替及 ** 展开；AugAssign 左值只求一次；保留旧门对注解表达式的检查 |

最后语法清点新增 5 格在开发中先跑 `4 failed, 1 passed`，随后全绿；注解旧能力非回退 2 格在新实现补扫前均红，补后绿。

## 真实被测路径与变异牙齿

1. 审查方 3 种真实 `cone_intersection_margin` 内植入（空 tuple for、range(0) for、while False）全部保留：以 Fraction KKT 和二进制 midpoint cell 独立证明正确非零结果为最小 subnormal；原路径返回该值，植入路径错误返回 0。现在三种植入均在 `cone_intersection_margin / rounded-vector` 断言被拒绝。
2. 内存删除 `new_head = joined(entry, head, backedge)` 的 entry 合流：外部变异运行 exit 1，精准失败 `K01 real cone rounded-vector assertion`，issues 为 `[]`。不是伪造扫描输出。
3. 内存取消回边不动点迭代：外部变异运行 exit 1，精准失败 `K01 loop-internal callable fixed-point assertion`；要求注入函数第 5 行 `saved(vector_rational(q))` 报 rounded-vector。函数尾部将 root/saved 都改回 abs，无尾部危险调用代替循环内部断言。
4. 所有包含内部危险调用的新增语法门都钉其 lineno，而不是仅要求任一地方出现同规则。

## 证据与重跑

- [机器摘要/哈希](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/result.json)
- [最终修前红日志](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/final_baseline_red.log)
- [最终 targeted 绿日志](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/targeted_green.log)
- [零次路径变异红日志](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/mutation_zero_path_red.log)
- [回边变异红日志](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/mutation_backedge_red.log)
- [全部命令及退出码](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/k01/final_runs.json)

PowerShell：`$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 -m pytest -q tests/test_r11fix_static_flow.py tests/test_r10_static_construction.py tests/test_r9fix_construction_static.py --basetemp=reports/codex/R11FIX_evidence/tmp/k01_recheck`

## 边界

这是有限、保守、过程内局部数据流门，不是任意 Python 程序的形式化正确性证明。容器/属性摘要是 field-insensitive 的 may 分析；未知跨过程返回、反射、自定义调用协议，以及一般协程/生成器函数调度不在已证明域。注解表达式保留源表达式检查，并保守合流“执行/不执行”，不解释类型系统或承诺具体 Python 注解求值模式。本次没有新增白名单，没有改写旧测试，没有修改姊妹树、fixtures 或输入文件，没有 Git 写操作。
