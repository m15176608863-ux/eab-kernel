# J01 静态门内部交叉检查

范围：只读核查 `tools/check_exact_construction.py` 和 `tests/test_r10_static_construction.py`。这是实现阶段的交叉检查，**不是独立 G6 / M0 退出复审**。

## 七原型与源内变异

`REVIEW_CASES` 列出关键字 sqrt、关键字 norm、Fraction 包装、map(Fraction)、局部循环、append、减法增强赋值七种原型。

`test_j01_seven_mutations_inside_real_cone_path_are_rejected` 不只测孤立字符串：七项均替换真实 `cone_intersection_margin` 的最终构造语句，再执行真实函数；独立 Fraction KKT 与平方中点给出正确值 u，原函数返回 u，变异函数返回 0；最后在完整 covers3.py 上检查对应函数与对应规则报错。检查路径符合“牙穿过被测路径”。

`test_j01_removing_keyword_step_inside_gate_trips_real_cone_assertion` 又撤回 scanner 的 keyword 遍历，确认真实 cone 的 `rounded-vector` 目标断言报红，未伪造 scan 结果。

## 新发现的四个具体语法问题

探针输出：[static_peer_probes.log](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/static_peer_probes.log)。每项在独立子进程运行，2秒超时防止分析器挂住；未写生产源文件。

1. **推导式海象赋值漏污**：`v=vector_rational(q); [(x := a) for a in v]; return sqrt_rational(x)` 返回 `[]`。Python 的 x 绑定属于外层，但 `visit_ListComp` 恢复旧 rounded 集时将其清除。
2. **自扩展别名无限循环**：`a=a.x; return sqrt_rational(a)` 超时。canonical 用完整名称作 seen；`a -> a.x -> a.x.x ...` 每次都不同，不能终止。
3. **try/except callable 分支漏合并**：先 `root=sqrt_rational`，try 中调用 risky，except 中 `root=abs`，最后 `root(scalar_rational(q))` 返回 `[]`。成功分支仍可运行 sqrt，不能被最后遍历的 except 覆盖。
4. **match callable 分支漏合并**：两个 case 分别令 root 为 sqrt_rational 与 abs，最后 `root(scalar_rational(q))` 返回 `[]`。同样需要可能函数集合合并。

四项均是同一函数中的可见语法，不属于任意动态反射或不可见跨过程数据流，已交 J01 实现者修复、增加持久门。本文件记录发现时状态；修后复核由后续日志补充。

## 契约边界

模块文档已经明确这是局部结构门，不是任意 Python 数据流的完备证明；未知跨过程或反射不在已证域。此限定合理，但不能借它豁免上述同函数可见语法。未在本次短检查中发现扩大文件级白名单；新增例外仍按具体函数和规则。

## 修后定点复核

J01 实现者修复并冻结代码后，检查者只读重跑上述完全相同的四个输入，未扩展范围、未修改源码或测试。四项仍分别放入独立子进程，并保留每项 2 秒超时上限。

复核日志：[static_peer_recheck.log](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/static_peer_recheck.log)。

| 原反例 | 修后实测 | 结论 |
|---|---|---|
| 推导式海象外层绑定 | 第 4 行 `sqrt_rational(x)` 报 `bad / rounded-root` | 目标污点保留 |
| 自扩展别名 | 子进程正常退出 0，返回 `[]`，未超时 | 终止问题修复；输入本身未含已知舍入，允许无告警 |
| try/except callable 合并 | 第 7 行 `root(scalar_rational(q))` 报 `bad / rounded-root` | 成功分支不再被 except 覆盖 |
| match callable 合并 | 第 8 行 `root(scalar_rational(q))` 报 `bad / rounded-root` | 保留可能的 sqrt 分支 |

日志最后一行：`4 peer counterexamples rechecked: 3 targeted rounded-root findings, 1 terminating self-alias scan; all PASS`。

本次只能确认这四个定点反例已修复，不等价于任意 Python 数据流完备性证明，也不替代独立 G6。
