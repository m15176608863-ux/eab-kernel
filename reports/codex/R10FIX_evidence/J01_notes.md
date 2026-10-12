# G6J-J01 修复分报告

## 范围与结论

- 仅改 `tools/check_exact_construction.py`，新增 `tests/test_r10_static_construction.py`；证据位于本目录。未改既有测试断言、未改运行内核、未操作其他工作树。
- 修前原始首跑：`J01_red.log`，`30 failed, 11 passed in 0.33s`。
- 最终版七种复审语法及其七个真实 cone 路径变异，在保存的修前 scanner 上重放：`J01_final_baseline_red.log`，`14 failed in 0.26s`。不是把假结果追加到生产输出之后。
- 修后：新门 65 格 + 原 R9 静态门 25 格，`J01_green.log` 最后一行 **`90 passed in 1.28s`**。
- 全仓 `src/` 和 `tests/` 扫描：`J01_scan.log`，**`exact construction AST gate: 0 violation(s)`**。

## 根因与修法

旧门只读 `Call.args`，忽略 `keywords[].value`（包括 `**kwargs`）；`Fraction(...)` 与 `map(Fraction, ...)` 无条件去掉来源标记，错误地把“对已经损失的信息精确表示”当成“恢复原始精确量”。此外，循环目标、增量赋值、容器变更与不同控制流分支没有完整传播来源。

修法是跟踪函数内已知构造来源，不改变算术：

1. 所有位置参数、关键字参数、`*args`、`**kwargs` 都进入同一检查入口。
2. `Fraction`/`Fraction.from_float` 和 `map(Fraction, ...)` 只保留原输入的性质，不再清除已知舍入来源。未发生本地舍入的给定浮点输入仍可 `Fraction` 化。
3. 处理普通/链式/解包/星号/注解/海象/增量赋值；局部下标和属性写、容器 `append/extend/insert/update/setdefault/add/__setitem__`、读取 `values/items/get/copy/__getitem__` 保留来源。
4. 处理 `for`/`async for`/`while` 的循环传播和固定点、推导式绑定、`with`/`async with` 目标、`match` 捕获、函数默认参数，以及 `if` 和 `try`/`except`/`except*`/`else`/`finally` 的保守合流。后遍历的分支不得擦除先前的可能舍入。
5. 构造函数别名覆盖导入、局部/属性、容器、解包、海象、条件表达式、显式 `.__call__` 与可直接识别的 lambda 调用形态；所有新增行为都有具体测试格，而非以文档宣称代替门。

## 七种复审语法：修前红 → 修后绿

共同断言：扫描结果中必须出现目标函数对应的目标规则，而不是“只要任意报错就算抓住”。

| 语法 | 目标规则 | 最终修前重放 | 修后 |
|---|---|---|---|
| `sqrt_rational(value=scalar_rational(q))` | `rounded-root` | 红，旧门 `[]` | 绿 |
| `norm_rational(values=vector_rational(q))` | `rounded-vector` | 红，旧门 `[]` | 绿 |
| `sqrt_rational(Fraction(scalar_rational(q)))` | `rounded-root` | 红，旧门 `[]` | 绿 |
| `norm_rational(tuple(map(Fraction, vector_rational(q))))` | `rounded-vector` | 红，旧门 `[]` | 绿 |
| 舍入向量 → `for x in v` → `square += x*x` → 开根 | `rounded-root` | 红，旧门 `[]` | 绿 |
| 局部 `append` 舍入量 → 开根 | `rounded-root` | 红，旧门 `[]` | 绿 |
| 舍入 `a,b` → `a -= b` | `subtract-rounded` | 红，旧门 `[]` | 绿 |

真实路径门将上述七种形态分别植入 `covers3.cone_intersection_margin` 原来的最终构造位置。输入为复审方的次正规四面体：`u = ulp(0)`，精确最近点为 `(-u/3,)*3`。测试独立验证有理 KKT 等式及平方舍入区间 `(u/2)^2 < u^2/3 < (3u/2)^2`；原内核输出 `u`，七个错误构造全部输出 `0`，然后检查 scanner 的指定规则。Oracle 不调用生产几何原语，也不以生产构造函数产生期望值。

## 源内回退变异与确切红断言

- 回退 scanner 内的 `arguments()`，把 `return [*node.args, *(item.value for item in node.keywords)]` 改为 `return node.args`；只在内存编译副本，不写回生产源文件。
- 在真实 cone 返回位置植入关键字分量先舍入错误，然后运行原参数化测试。
- `J01_mutation_red.log`：**`1 failed in 0.12s`**。失败的是 `test_j01_seven_mutations_inside_real_cone_path_are_rejected[norm_keyword]` 内的目标规则断言：

```text
assert any(row[2:4] == ("cone_intersection_margin", rule) for row in issues)
AssertionError: (1, 'rounded-vector', [])
```

数值 KKT、原内核 `u`、错误内核 `0` 三组断言都先通过。故红色确由指定漏检产生，不是几何构造或不稳定求解器选择导致。日常测试也保留一个内部回退自检，要求上述断言确实抛出 `AssertionError`。

## 同类扫描及窄例外审计

在原七格之外新增 `J01_scan_red.log`（11 个漏检）和 `J01_scan_red2.log`（5 个漏检）的修前证据；包括容器读取、`.__call__`、分支 callable、上下文/模式绑定、推导式、alias 重绑定、star-map、属性 callable、海象 callable、try 合流及位置/关键字默认参数。这些格子均已变绿。

增强全仓扫描实际新命中以下既有代码，审阅后明确属于给定模型或输入生成，而不是原始精确量的构造。因此只新增逐函数、逐规则例外及理由，未放宽整个文件、未放宽 Fraction 规则：

| 函数 / 规则 | 审阅结论 |
|---|---|
| `limit._tangents` / `subtract-rounded` | 既有契约明确规定 `t2 = n × 已返回 binary64 t1`；先将该给定模型精确有理化，完整完成叉积差后才最终舍入分量。 |
| `tests/e5a_escape_oracle._candidates` / `subtract-rounded` | `z-zprev` 是已构造候选显示值的缓存复用窗口；另行精确检验所选给定候选坐标的 facet extent。不是主 oracle 的精确派生量构造。 |
| `tests/perf_escape_oracle_reference._candidates` / `subtract-rounded` | 同上，为冻结性能参考路径。 |
| `tests/test_perf_2d_directions.direction_cases` / `subtract-rounded` | 用实际舍入工程坐标生成“给定数据”差，正是该门约定的输入，而不是对原始理想未舍入点求差。 |
| `tests/test_filtered_predicates.test_orient3d_filter_has_a_real_fast_path` / `direct-float` | 循环 callable `ctor` 在 float/Fraction 间切换，只把 0/1 变为指定输入类型，不涉及派生量或期望值构造。 |

与 J04 代理协调后，其新门中的 `float(Fraction(...))` 改为独立 `construction_oracle.scalar_exact`，没有为该新测试扩大白名单。父代理的报告尺度估计若只是对既有报告量缩放且未进入 root/vector 禁用构造，本门不声称它是精确几何 oracle。

### 交叉复核的四条追加同类反例

J04 代理只读复核发现四个进一步的函数内语法反例，均已纳入新门。`J01_peer_red.log` 在修复前得到 **`4 failed, 61 passed in 2.45s`**；修后都包含在上面的 90 passed 中：

1. 推导式 `[(x := a) for a in rounded_vector]` 的海象 `x` 属于外层，不能随推导式局部循环变量一起恢复丢弃。修法只保留这些外层海象绑定。
2. `a = a.x` 使原 canonical 用“完整展开字符串”判环永远不重复，导致不终止。新增子进程 2 秒超时保护门，红断言为 `canonical alias resolution must terminate for a=a.x`；修法以有限 alias 图的首段节点判环，而不是不断增长的字符串。
3. `try`/`except` 分支里后访问的 `root=abs` 会盖掉此前 `root=sqrt_rational` 的可能 callable。修法合并各路径可见 callable，而不仅合并数值来源。
4. `match` 的不同 case 有同一 callable 丢失；同样进行路径合流。

这四条没有被归入“任意跨过程 Python”边界而推迟，也没有删格。没有因修复超时问题而放宽超时断言。

## 测试改写台账与边界

- 既有测试：**0 删除、0 放松、0 skip/xfail、0 网格缩减、0 修改**。
- 新测试编写期间修正了真实 `local_append` 变异的最终算子：使用 `sqrt_rational(sum(x*x for x in v))`，使其与该格 `rounded-root` 目标规则一致；错误数值仍是 0，独立期望仍是 u。最终版本已在修前 scanner 上重放并得到 14/14 指定断言红，未把测试编写错误作为修复证据。
- scanner 原文件 CRLF 保持；修前 250/250 行均为 CRLF，修后也无孤立 LF。
- 本门不是任意 Python 程序的形式证明：反射、动态生成 callable、任意用户函数的跨过程传递不在已证明域内；没有声称静态穷尽所有 Python 程序。这不影响明确本地已知舍入来源经过本报告所列调用/赋值语法的看护。
- 未运行全套 pytest（由父代理统一运行）；不声称通过下一轮独立 G6 审查或 M0 退出。

## 复跑命令

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q tests/test_r10_static_construction.py tests/test_r9fix_construction_static.py --basetemp=reports/codex/R10FIX_evidence/tmp/j01_final
python -X utf8 tools/check_exact_construction.py
python -X utf8 reports/codex/R10FIX_evidence/J01_mutation_check.py --baseline # 预期 14 failed
python -X utf8 reports/codex/R10FIX_evidence/J01_mutation_check.py            # 预期 1 failed
```
