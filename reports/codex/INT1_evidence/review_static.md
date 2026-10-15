# INT1 R3：比较器高阶调用与统一插桩域独立复核

结论：**修复后限定范围通过，0 critical、0 major、0 minor；初审 1 项 major 已关闭。**
审查者未修改静态门、policy 或统一 helper 的实现；所有探针为注入文本或 `INT1_evidence/tmp` 副本。

## 初审发现与关闭

最初版本只追踪 import 别名及字面量反射。真实可执行的以下 10 种形式，在测试驱动路径均返回零诊断：

1. `name='scalar_algebraic'; getattr(module,name)(compare)`；
2. `getattr(module,'scalar_'+'algebraic')(compare)`；
3. `module.__dict__['scalar_algebraic'](compare)`；
4. `globals()['scalar_algebraic'](compare)`；
5. 模块级 `Base=RealAlgebraic` 后子类覆写 `compare`；
6. `fetch=getattr` 别名再反射；
7. `vars(module)['scalar_algebraic'](compare)`；
8. `operator.attrgetter('scalar_algebraic')(module)(compare)`；
9. `from operator import attrgetter as getter` 后同类调用；
10. 测试驱动内 `Base=RealAlgebraic`、嵌套子类覆写并读 `.time`。

原始失守证据完整保留于 [review_static_initial.json](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_initial.json)。
实施者随后增加有限赋值别名闭包、目标拼写的变量/拼接追踪、下标反射与 attrgetter/itemgetter 路径，并将十例纳入普通 pytest 及内部检查器变异。

恢复后独立复验：十例分别以普通路径和 `tests/test_review_comparator.py` 输入，共 **20 格全部命中 `algebraic-comparator-site`**，不是恰好被不相关规则弄红。

## 统一插桩证明域

当前一次 review 有 9 个精确源码 scope：统一 helper 的模块/三函数、两处旧变异 selector，以及新语义测试的调度/哈希屏蔽/变异 selector。没有把数值 oracle 或测试断言函数加入该域。

对全部 9 个 scope 独立核对：

- 已列明的插桩规则可使用该 review；
- `direct-float`、`algebraic-comparator-site`、`closed-unproved-arithmetic`、`closed-rounded-call`、`closed-modulo`、`closed-reduction` 及两种数值 provenance 规则不因该 review 获豁免；
- 改动 scope 内容、换成未经审核的 oracle 函数均使 review 失效；
- 在独立临时副本中只给 helper 增加一个注释字节段，9 个 scope 全部失效；真实 helper 和源文件未改写；
- 新的二次式时刻与 L∞ 残差数值门均不在插桩 review 域内。

`closed-syntax` 被列入只为精确钉住的哈希屏蔽 lambda；它不自动批准该函数的未来修改，也不撤销任何比较器或数值规则。

## 完整专项验证

重启后使用全新 `review_static_pytest_resume_r1` 基础临时目录完整重跑静态/runner 文件；没有拼接旧进程输出：

```text
76 passed in 3.25s
```

命令含 `-p no:cacheprovider` 和显式 `--basetemp`，`TEMP/TMP` 均在 INT1 专用 tmp 内；日志经 Python 明确 UTF-8 写出。

- [机器复核记录](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static.json)
- [专项完整日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_pytest_resume_r1.txt)

## 边界

这是有限正子集辅助静态门，不是任意 Python 反射、运行时构造选择器或外部高阶工厂的完备证明。旧 test-driver 的 closed-subset 辅助豁免仍存在；本次验证的 **algebraic-comparator-site 不受该豁免**。全树静态零违例与四片完整执行身份由总报告另验，不能以本专项替代。

R3_PASS_SCOPED_REVIEW
