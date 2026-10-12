# R12FIX-b：静态类型/数据流子层设计与独立对抗记录

本文件记录 `tools/exact_construction_flow.py` 的设计边界，不替代全仓门、最终例外台账或独立 G6 退出审查。

## 1. 旧门的挂钩与问题

- `exact_construction_subset.py` 是正向语法准入层；原版把除整数字面量之外的算术、普通记录字段、绝大多数一阶调用都交给 waiver。
- `check_exact_construction.py` 已有较成熟的有限不动点 CFG/heap/provenance：循环、分支、异常前缀、可变别名、生成器消费和显式构造污染不能另写一套弱化实现替代它。
- 旧测试对若干规则名、注入行以及 scanner 内的三处字符串有明确要求；本工单保留这些牙的目标断言。
- 旧的整库 SHA-256/整模块 AST 上下文不是数值证明；本次源类型层不读取政策，也不生成 waiver。

## 2. 新层职责

入口：`analyze(text, path, repository_root=None)`；输出 `Analysis`，供正向准入层和原 provenance/CFG 层共同使用。

### 值域

- 数值类型：`int`、`Fraction`、给定 `float`、未细分输入、布尔、文本、None、unknown。
- 每值另携带源表达式来源、已发生非精确构造/运算的来源、静态对象类型及分配身份。
- **来源与对象身份分离**：同样依赖输入 `q` 的两个独立列表不是别名；只有相同分配身份才共享可变污染。
- `Fraction(float_derived)` 不擦除已有舍入历史；函数、字段注解也不擦除真实赋值或实际构造参数的类型与污染。

### 一阶源摘要

- 从当前传入源码与 `src/`、仓库根、`tests/`、`tools/` 的静态 Python 源解析函数，不运行导入。
- 参数以符号来源摘要，缓存键为类型/污染状态/静态对象类型，不为每一个 AST 来源集合重新解释函数。
- 摘要包含返回值、内部 sink 效果、可变参数效果、字段写入及不能分析的调用面。
- callee 有 unknown/dynamic 调用时，caller 不因“找到了源码”而自动获准。
- `sink_arguments()` 区分真正进入 callee 构造的参数与只供报告/筛查的 `tol`、`window` 等参数；它不是按参数拼写判断。
- 先分析本模块一阶调用图入口，再用实际参数分析 callee；未触达定义仍检查，故新加一个未被调用的危险函数不能逃逸。
- 递归转移仍保守拒绝；没有为了缩小例外数加入猜测性的递归精确证明。

### 类型/纯数据模型

- `Fraction`/`int` 可证明精确的算术与比较；非整数除法和负整型幂不会被误认为整数运算。
- 统一构造模块的有限 API；已知 `math.isfinite`、`abs`、`min`/`max`、容器操作等。
- 已知布尔字面量的分支选择、显式序列连接/重复。
- 有限的 pathlib、json、csv、collections、random、pytest 数据/测试设施接口。其输出不被一概声明为精确数；例如测试断言对象仍是 unknown，不能作为精确几何量进入 sink。
- 标准库身份按实际词法绑定解析；同名参数、局部定义、类定义遮蔽 import 时，不继承标准库纯函数摘要。
- 模块赋值与函数默认值按定义时刻保存快照；保留旧值的别名不会在重新赋值后被偷偷重算。
- dataclass 构造参数按字段存储；自定义 `__init__` 的字段写入读取源码并向实例传播，不单凭字段注解断言精确。

## 3. 与原 CFG 层分工

本子层提供 `may_round()` 等保守类型事实。**复杂控制流/heap 的隐式浮点污染主分析仍由原 `Check` CFG 承担**，显式构造与隐式算术污染分开记位。

这样既保留原有循环/异常/生成器牙，也不会仅因为普通浮点报告算术存在就报错；污染必须进入指定构造 sink 或无法分析的调用面。

本层不是任意 Python 对象协议、反射、动态 callable 或几何算法数学正确性的证明器。不能分析的调用、递归、复杂数据关联不得包装为“已证明”；剩余证明缺口必须在最终报告中如实列数和说明。

## 4. 本轮发现并修复的绕过族

独立审查者的原始红日志与永久测试由 `local_policy_flow_audit.md` 及 `tests/test_r12fixb_flow_adversarial.py` 保存；这里仅汇总机制：

1. 参数/定义/类遮蔽 `math` 或 `isfinite` 后仍被当作标准库纯函数。
2. 闭包读取派生浮点，源摘要遗漏自由变量。
3. 可变别名与跨函数参数写入丢失污染。
4. break/continue/for-else、try/except/else 和可能抛错前缀的污染被后续赋值覆盖；改由成熟 CFG 主分析守护。
5. 默认参数的定义时快照、模块重新赋值前保留的快照丢失。
6. 字段 `Fraction` 注解覆盖已舍入 initializer、实际 dataclass 参数或自定义 `__init__` 赋值。

修复过程没有把这些形态加入数值 waiver。

## 5. 本子任务已运行的验证

所有 Python 调用设置 `PYTHONDONTWRITEBYTECODE=1` 并使用 `python -X utf8`。

- `tests/test_r12fixb_safe_subset.py` + `tests/test_r12fixb_flow_adversarial.py`：记录类型修复后 `64 passed in 0.26s`。
- `tests/test_r12fix_static_closed.py -k 'not full_repository_copy and not baseline_waiver'`：`110 passed, 2 deselected in 13.99s`。这里两项涉及尚在重新登记的全仓例外机制，须由最终集成验证补齐，不能算本次已过。
- 后续定向测试统一使用 `-p no:cacheprovider --basetemp=reports/codex/R12FIXb_evidence/tmp/<unique>`。

最终全套数量、例外数、零违例与耗时以 `R12FIXb_report.md` 的最后一次集成结果为准；本文件不声称这些已完成。
