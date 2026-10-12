# R12FIX-b 最后机制复核（不是 G6）

范围：只读复核根任务新增的幂根 sink、`import_proved` 接线、局部源码 pin；按 root 授权新增实际执行缺陷的永久测试。实现修复均由 root 完成。本记录不批准生产 waiver，不替代全仓门、全套回归或独立 G6。

## 审查中实际找到的问题

1. **幂根与成熟 CFG 未贯通。** `for ... break ... else`、`try` 异常前缀留下 `r=q*q`，再 `r**(1/2)` 或 `math.pow(r,.5)`，最初 8 格 scanner 返回空。`q=1e-200` 实际输出 0，独立 Fraction 相邻 binary64 中点平方证书证明正确根为 q。随后同族 `r **= (1/2)` 又找到 4 格遗漏；需要同一 sink 规则覆盖 AugAssign，不是仅匹配 `**0.5` 文本。
2. **同名定义 pin 被后者覆盖。** 分支内两个 `choose.read`，改变第一个函数的非站点语句而保留 getattr AST，原 `site_contexts` 的字典后写覆盖使 pin 不变、无 stale、例外继续有效。修复必须绑定本地同名候选定义组，而非重新锁整库。
3. **调用返回的污染在 CFG/函数摘要边界丢失。** `math.sin`/`math.prod` 返回或 helper 内 `q*q` 经相同退出路径后流入 norm，初测 12 格全返回空。math.sin 是舍入来源政策牙，不声称以另一浮点 sin 为精确 oracle；prod/helper 用 Fraction 中点平方证明真值应为最小 subnormal、执行却为 0。
4. **嵌套 break/continue 的 helper 摘要仍会被覆盖。** helper 内 `if True: r=q*q; break/continue` 后的不可达 `r=q` 曾把摘要清洗，caller norm 的 4 格再次返回空。这说明“过程内成熟 CFG 正确”不足以担保较弱的跨过程摘要。
5. **With 抑制异常的前缀未进入 helper 摘要。** `pytest.raises(type(ZeroDivisionError()))` 内先 `r=q*q`，随后 `1//0` 跳过 `r=q`，外层 helper 返回污染值；2 格初测为空。使用 `type(exception_instance)` 是为了排除裸异常类恰好触发 callable-value 的假牙，不改实际运行语义。

所有红均来自扫描器真实被测路径，而不是在输出后添加假诊断。原证据保留，不用绿日志覆盖红日志。

## 已核对的修复与证据

- root 以 `flow.power_sink` 给出静态幂类型事实，成熟 `Check` 读取实际 left/first argument 的 rounding bits 触发拒绝；BinOp、math.pow、AugAssign 同属该规则。
- `call_may_round` 将单调用返回的 bad 事实交给成熟 CFG；flow 的 loop-else 保留退出 may-state，try handler 从语句前缀并集开始，避免用正常末尾状态洗白。
- 嵌套循环转移按最近匹配 loop frame 保存退出/回边环境快照，循环固定点合并这些状态；不按具体函数/缺陷站点名称放行。
- With 同样收集所有可能异常前缀，合入可能被 `__exit__` 抑制后的退出状态；除明确 file/pytest 断言 context 外，未知 context 协议传递为 unproved，不自动相信 source class。
- `site_contexts` 先统一换行；同 qualified binding 的候选源码一起哈希，不再 last-write-wins。无关绑定仍不进入该 pin。
- 永久门位于 `tests/test_r12fixb_final_mechanism.py`，目前 31 节点（12 幂根 CFG、1 同名 pin、12 调用返回、4 嵌套退出、2 With 抑制异常）。
- `final_mechanism_red.log`：最初 **9 failed in 0.12s**，包括 8 幂根＋1 pin。
- `final_augpower_red.log`：**4 failed, 9 passed in 0.13s**。
- `final_mechanism_call_return_probe.json`：12 格修前真实空诊断；随后永久测试启动时 root 修复已落，`final_call_return_red.log` 名称沿用原计划，但实际内容是 **12 passed, 13 deselected in 0.09s**，不能误称该日志为红证据。
- `final_mechanism_last_green.log`：在最后 4 格嵌套退出加入前，**131 passed, 1 deselected in 0.56s**。
- `final_nested_exit_red.log`：**4 failed, 25 deselected in 0.11s**；统一 loop snapshot 后 `final_mechanism_closed.log` 为 **135 passed, 1 deselected in 0.59s**。
- `final_with_prefix_red.log`：**2 failed, 29 deselected in 0.10s**。
- **最终复测 `final_mechanism_verified.log`：`139 passed, 1 deselected in 0.60s`**，包含新增 31 格、既有 safe/adversarial/structure/local-maintenance 及 root 新增 2 格 unknown context 牙。仅实际全仓复制的注释门未在本子任务运行，留给 root 安装最后局部清单后的全套验证。

## import 接线与局部性的小型复核

`final_mechanism_import_probe.json` 使用本工作树证据目录下新建的微型源码工程，不运行被导入模块：

- 新增源模块的直接 int 函数调用、固定模块别名、字符串常量：3 绿，不需要重建 imports/waiver 库。
- 不存在的包、存在但含 getattr 间接调用的 callee、模块别名写后再调用：3 红。
- 因而 import 准入只表示源绑定可解析，不会把未知 callee 变成可信函数。此抽样不等于证明所有 Python 导入副作用或运行时协议。

`final_mechanism_locality_probe.json`：

- 改兄弟函数：只兄弟 pin 改变。
- 加无关模块注释：函数 pin 不变。
- 改本函数注释：本函数 pin 改变。
- LF/CRLF 等价转换：pin 不变。
- 当前 policy 顶层无 dependency/snapshot 字段；局部审查 pin 不是跨模块语义依赖证明，修改被调函数仍靠重新扫描其源码和源摘要，而不是全库 waiver 冻结。

## 当前结论与报告边界

**本次针对性审查中实际发现的上述问题均已由 root 修复，并由真实执行/目标扫描断言复测关闭。实现及本子任务测试已冻结。**

即便这些针对性牙全部变绿，也只证明列出的修复和有限正向子集。不能写成“任意 Python 数值代码形式完备证明”，不能称本轮为独立 G6，不能将旧近似窗口/随机姿态/诊断幅度改称无先舍入。最终例外超过目标、未改写动态 helper 和保留近似路径应由主报告逐项列为 PARTIAL 遗留。全仓注释实际复制门及完整 pytest 最后一行以 root 的最后证据为准。
