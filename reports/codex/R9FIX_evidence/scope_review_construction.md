# R9FIX 构造边界快速只读审查

## 范围与结论

本次完整阅读 `src/eab/construction.py`、`src/eab/oracle_construction.py`、`tools/check_exact_construction.py`，重点核验次正规、最大有限值的舍入中点、非有限候选、float 子类及 AST 白名单。仅运行数个只读内存探针和新增 evidence 草稿门；没有修改 src/tests/tools/docs。全套正在运行，本报告不是独立 G6 退出审查。

**确认两个需要补齐的点**：

1. `normalized_difference_rational` 没有把 nn 转为 Fraction，同一给定 float 可在平方中间量下溢时返回错误的零；非正 nn 也缺少明确输入域检查。已即时通知主代理。
2. AST 门未识别已检查构造接口之间的错误串接：先 `scalar_rational` 再 `sqrt_rational` 等模式目前会通过。已即时通知主代理，不是白名单合理豁免。

## 1. 已确认：normalized difference 的 nn 漏有理化

函数只转换 c 与 offset，表达式 `c*c/nn` 在 nn 是 float 时重新进入浮点运算。因此：

```text
normalized_difference_rational(1e-200, 1e-200, 0.0) -> 0.0
同一给定数先逐项 Fraction 化后                     -> 1e-100
```

最终结果可表达，但原入口静默清零；`1e200` 同类输入也会中间溢出。另 `c=0, nn=0, offset=1` 返回零，而表达式本身未定义。正常几何调用者目前往往已传 Fraction，但统一构造边界的公开输入不能依赖这一偶然条件。

已按主代理要求仅在 evidence 准备：

- [测试草稿](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/test_r9fix_normalized_input.py)：两侧可表达尺度、float/Fraction 等价性、独立 Fraction 中点证书、nn≤0 明确拒收、去掉 nn 有理化的真实内部变异。
- [修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/normalized_input_red.log)：`10 failed, 1 deselected in 0.11s`。deselected 的是尚待修复语句存在后才能运行的变异测试，并非历史测试 skip/xfail。
- [最小补丁草案](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/normalized_input_fix.patch)：同时有理化 c/nn/offset，nn≤0 抛明确 ValueError。**尚未应用**。

## 2. 已确认：AST 名字集合漏掉统一接口的错误串接

只调用 `scan_text` 的内存探针结果：

| 被扫描表达式 | 当前返回 |
|---|---|
| `sqrt_rational(scalar_rational(q))` | `[]` |
| `sqrt_exact(scalar_exact(q))` | `[]` |
| `unit_rational(tuple(ratio_rational(x,d) for x in v))` | `[]` |
| `math.sqrt(float(q))` | `rounded-root` 与 `direct-float` 两项 |

原因：root 名字集合缺 `sqrt_rational/sqrt_exact`，rounded-converter 集合缺 `ratio_rational/ratio_exact` 等返回浮点的统一构造接口。调用者把旧坏表达式改写为统一函数的串接后仍能先舍入中间量，不能因为全部名字来自统一模块就放行。

建议：扩展有限名字集合并给每种模式加静态门的牙；维持 AST 门“不是任意 Python 数据流证明”的显式边界。未建议扩大白名单来掩盖这些模式。

## 3. 未发现新反例的部分

### 生产标量、平方根、norm/unit

- `scalar_rational` 先 Fraction，内建 float 作最终 RN-even 转换，随后拒绝未获准的非零下溢；真正上溢抛错。
- `sqrt_rational` 先精确确定指数，再以输出 ULP 为单位整数平方根与中点比较；`float(significand)` 的整数不超过 2^53，转换本身精确。
- 次正规 quantum 固定为 2^-1074，0 与首个非零值的中点由同一整数不等式处理；ties-to-even 在零侧也适用。
- 最大有限值上方仍存在合法舍入单元；虚拟下一值是 2^1024，中点及更大值必须上溢。现有构造门已经逐值验证这一边缘。
- norm/unit 保留精确平方和；unit 的每个最终分量单独正确舍入，不要求未单位化范数本身能表示。
- 标量 Fraction 化会剥离 float 子类额外的 exact 元数据；这是显示构造而不是保留 LP 见证的协议。

### 独立 oracle 候选与证书

- Decimal80 与 `float(value)` 只产生候选；候选有限且非负、两侧 Fraction 中点及最低位奇偶全部通过后才能返回。
- 非有限候选、None 或错误邻值被拒绝，回原位模式二分；数值候选不改变最终正确性。
- 最大有限值的上边界使用精确 `2^1024`，没有 `Fraction(inf)`。
- 私有 `_round_positive` 的非负输入、power∈{1,2} 来自公开 wrapper；不把该私有 helper 当作任意参数的独立 API。
- `scalar_exact` 已收紧为 `type(value) is float` 的 identity 路径，float 子类走 Fraction，再返回真正内建 float，不保留 exact 附带证书。
- 之前已保存的候选门覆盖有限/极端中点、Decimal80 分辨不了的精确中点两侧、错误候选回退与去掉证书的真实内部变异；本次没有重复长测试。

## 4. 白名单判断与剩余边界

当前白名单以“路径＋具名函数＋规则”匹配，没有整文件豁免。

- `_candidate_positive/direct-float` 的理由成立：返回值仅为候选，后续逐值 Fraction 证书才决定接受。
- `scalar_rational/direct-float` 与 `sqrt_rational/direct-float` 对应受测的唯一最终边界与精确整数 significand。
- `test_exact_witness_is_preserved_by_copy_not_by_float_arithmetic` 中的两处 builtin float 是刻意剥离见证的协议测试，不能迁成 scalar helper。
- `_iv`、谓词 filter 的 cast 必须继续受区间包围与精确回退约束；此次只核白名单理由与已读调用形态，没有重新证明其全部误差界。
- reader/反序列化、Dual 的公共 Number 输入 coercion 是输入接口例外，不应成为派生 Fraction 输出的绕行通道。
- 故障注入函数的坏 sqrt 是具名测试牙；不应复制到 oracle expected 值或生产调用者。

每个函数级例外仍可容纳未来新加的同类 cast，故需要代码审查配合，不能把 AST 绿灯描述为任意 Python 中间量的形式证明。此次最具体的漏检已在第 2 节列出，主代理可在下一次冻结前补齐。

## 5. 后续实施状态

以上第 1 节的“尚未应用”记录的是本次只读审查时点。主代理归档全套 attempt2 并解除冻结后，已授权落实最小补丁：`normalized_difference_rational` 现在逐项 Fraction 化 c/nn/offset，并明确拒收 nn≤0；测试草稿已复制到 `tests/test_r9fix_normalized_input.py`。

定向验证（新门、构造中点、R8 frozen、候选证书）结果为 `280 passed in 0.81s`，见 [修后及内部变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/normalized_input_green.log)。真实去掉 nn 有理化的变异在目标断言 `normalized difference preserves representable root from float nn` 报红，输出 `assert (0.0 == 1e-100)`。AST 补齐仍由主代理处理，本代理未改静态门。

## 主执行者收尾订正

root 已补 AST 对统一构造族串接的识别：新增 6 格先红后绿，完整静态门 25 passed、全仓 0 violation；同时保留逐函数/规则例外理由。先前“待补”是过程状态。

[最终主报告](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_report.md)。
