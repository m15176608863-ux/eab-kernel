# M5a2 R5：精确边界修补独立复核

结论：**本轮限定范围通过；0 critical、0 major、0 minor。** 这不是整个 M5a2 的单独 G6 退出结论。

复核者负责的是仿射研究子任务，不是本轮受审的代数数/SE(2) 出口/极小残差修补作者。本复核没有修改任何数值生产源码、已有测试或静态准入；仅读取实现、运行独立检查与重跑已有门，证据写在本目录。

## 1. 范围

- `RealAlgebraic.as_rational()` 的有理重构、无理根排除和选定根区间约束；
- `se2_first_entrance()` 有理首时刻出口统一为 `QuadraticTime`；
- 任何严格正有理残差保持 `UNCERTIFIED_NONRIGID_ENDPOINTS`；
- 公共代数数构造器闭区间下端点根语义、独立 oracle 入口 exact-only 断言；
- 对应六个源码内部变异是否在禁用哈希绊线后命中真正相关的新语义断言。

## 2. 实现与证明审查

### 2.1 有理重构

审查 `_primitive` 后得到的整系数本原多项式。若有理根最简分母是 q，则 q 整除首项整系数，故 q≤B。两种分母≤B的不同有理数间距至少1/B²。代码把隔离区间收窄到宽度严格小于1/(2B²)，因此其中若存在有理根，该根与中点距离小于1/(4B²)，必为分母≤B的唯一最近有理数。`limit_denominator(B)` 后仍要求精确代回为零且候选处于当前区间，排除了返回同多项式其他有理根的错误。

二次分支用分子/分母整数完全平方判定，不使用浮点根；模素数排除只在该素数不整除首项系数时使用，因而不会把一个真正有理根错误排除。提前返回的“快速候选”同样受区间与精确代回双重约束。

未发现上述证明与实现不一致。保留的风险是无理高位系数无法被模素数排除时，最坏情况需很多精确二分；这不是错误返回，但本复核不承诺任意无界位宽输入的统一时间上限。

### 2.2 出口统一

代码在完成事件枚举和全部标签重建之后调用 `time.as_rational()`；只对识别出的有理根构造 `QuadraticTime`。没有翻译捷径、改动根选择或几何判定。此方案符合工单允许的“SE(2) 出口统一有理容器”，无需将所有原始 `RealAlgebraic` 对象变成可hash数。

一般无理 `RealAlgebraic` 仍不可hash，和 `QuadraticTime` 无理实例之间的整个跨类型数值协议并未扩展；这不在所选 A4 修补方案的主张内，不应在报告中写成“所有代数容器互通”。

### 2.3 正残差与闭端点

认证分支仍是精确 `delta == 0`，没有浮点转换或epsilon。公共构造器先校验闭区间恰好有一个根，再将命中的下/上端点收缩为同一有理点；两个端点分别为不同根的区间仍拒绝。独立 oracle 入口断言在几何计算前检查全部顶点、参数、平移与中心，并排除bool。

## 3. 独立数值检查

可重跑：`python reports/codex/M5a2_evidence/review_exact_checks.py`。

主oracle仅依靠 `fractions.Fraction`、已知因式分解、素数指数的有理根不可能性、杠杆解析高度和正方形横向缩放残差；`random.Random`仅生成固定seed输入。没有导入生产多项式运算、根隔离、旋转或拟合函数来构造期望值。生产 API 只作为被测对象。

| 检查 | 数量 | 期望值来源 | 失配 |
|---|---:|---|---:|
| 已知有理因子根，1/3/5次及正负系数缩放 |190|显式 `(x-r)` 因子；包含1/2^1074和巨大分母|0|
| 已知无理根与错误有理分支排除 |27|素数k次根、区间内sqrt(2)而有理根在外|0|
| 有理杠杆首入及公共容器 |36|独立设 `h=2Lut/(1+(ut)^2)`，故首入t；逐次核相等/hash/混排|0|
| 精确极小正残差 |5|正方形 `x'=(1+2δ)x` 残差恰δ；含2^-1075和10^-400|0|
| 公共闭下端点根 |95|同一已知因子根放在闭下端点|0|

共353项独立检查，1.37秒，零失配。杠杆检查另跨 `2^-400 / 1 / 2^397` 单位尺度与大平移，未借助任何显示量。

作者新门的独立重跑最后一行原样：

```text
24 passed in 0.35s
```

pytest 使用 `-p no:cacheprovider --basetemp=reports/codex/M5a2_evidence/tmp/review_exact_pytest`，TEMP/TMP均在本单tmp。命令由120秒监督进程运行，没有skip。

## 4. 变异逐项检查

重新运行 `python tools/m5a2_exact_mutations.py --name review_exact_mutations_r1`，所有control退出0、mutant退出1；先屏蔽`code_hashes/file_hash`，再编译并注入真实生产函数体变异。没有向产出追加伪数据。逐个读取mutant traceback，红的都是下表对应新语义，而不是导入、哈希或随机顶点选择。

| 内部变异 | 实际红断言 |
|---|---|
| 正残差≤2^-52当零认证 | `strictly positive exact residual must remain UNCERTIFIED` |
| SE(2)出口不调用有理重构 | `rational SE2 time equals the rational QuadraticTime protocol` |
| 有理重构提前返回原rational字段 | `exact rational reconstruction returns the factored root` |
| 删除候选位于选中根区间的检查 | `rational reconstruction must stay inside the selected root interval` |
| 闭下端点收缩赋值反向 | `closed lower endpoint root denotes that exact endpoint` |
| 删除独立oracle入口类型断言 | `DID NOT RAISE <class 'AssertionError'>` |

相应完整日志与汇总在 `review_exact_mutations_r1/`。本轮没有使用变异后重新冻结的夹具作为期望值。

## 5. 证据与限制

- `review_exact.json`：范围、判决、数量、证据及源文件SHA256；
- `review_exact_checks.json/.py`：353项独立检查及可重跑脚本；
- `review_exact_commands.json`、`review_exact_pytest.txt`：实际命令结果；
- `review_exact_mutations_r1/summary.json`：六类独立重跑变异及红断言。

上述是A2/A4及相关A6边界的独立复核；不替代A1回放语义、A3宽阶段、A5静态回调、全套四片或B研究性扩展的其他审查。本轮没有新增critical/major需要返修。
