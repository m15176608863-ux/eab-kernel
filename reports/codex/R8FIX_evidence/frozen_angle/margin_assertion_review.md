# 全套失败后的只读复核：裕度差的旧舍入顺序断言

## 扫描结论

检查全仓 tests 中 `margin_gap` / `frozen_gap` / `distance - delta` 相关断言，并人工阅读冻结路径局部变量 g/g0/g5 的检查。

- 唯一直接强制旧浮点顺序的逐值断言是 `test_invariance_geom.py::test_margin_layer_is_invariant` 原 line 419：`contact.margin_gap == contact.distance - s * delta`。
- `test_margin.py`、`test_frozen_lowdim.py`、`test_frozen_ee_sign.py` 的距离减 delta 对照使用既有近似界；它们没有要求这种逐值浮点顺序，本次没有修改/放宽。
- `test_margin_penetration.py`、`test_invariance_interlock.py` 的 `margin_gap == -delta` 针对零距离哨兵或明确钳零状态，仍是精确适用的表达式。
- `test_margin_exact.py` 的 `distance == margin_gap == 0` 是带精确证书的显式显示下溢合同，不应替换为“非零就必须抛错”。
- `test_margin_exact.py` 的冻结 gap 等于 body distance 用 delta=0、轴向精确输入，没有第二次差值舍入问题。

机器可读断言清单：`margin_assertion_inventory.json`。这属于静态关键字/AST 扫描及相关调用段人工核对，不是全程序等价关系的形式分析。

## 独立严格 oracle 建议

1. 从**原始输入坐标**独立构造该 label 的有理平方距离 q，不直接信任生产字段；核 `contact.exact_distance_squared == q`。
2. 对候选 `g = contact.margin_gap`，取其相邻 binary64 中点 `lo, hi`。
3. 判定 `sqrt(q)-delta` 与有理数 r 的顺序：若 `delta+r<0`，目标必大于 r；否则比较 `q` 与 `(delta+r)^2`。没有开方、Decimal 精度假设或几何容差。
4. 目标须落在 g 的唯一 round-to-nearest 舍入区间；恰到 midpoint 时按 g 的尾数最低位验证 ties-to-even。显式下溢显示及无穷边界应按 API 合同单列。

这样不是把旧断言放宽成“一 ULP 内都行”，而是检验**独立几何模型下唯一正确的最终浮点值**。

特别注意 `test_invariance_geom` 调用的是显式 contact_window wrapper。源面标签与默认精确三角化标签不一定相同；非共面 VF/FV 要沿既有 test-only surface oracle 构造真实面距离，不能无条件把源标签索引进另一套三角标签字典。clamp 为零也必须由独立窗口规则决定。

## 已实跑的独立 EE 检查与内部变异

`margin_rounding_oracle_review.py/.log` 对首个失败格 `box_box_face / R7 / t=0 / s=.001` 的 EE `(0,1) × (5,6)`，以测试自写 Fraction endpoint/Gram/叉积公式独立重算 q：

- 显示 distance：`5.000000000000007e-05`。
- 最终精确表达式正确舍入：`-4.999999999999995e-05`，midpoint 证书通过。
- 旧显示 distance 再减 delta：`-4.9999999999999935e-05`，同一证书拒绝。

在生产函数体内编译回退 `gap = w - delta`，以及在内部代数构造 helper 注入“忘减 delta”“delta 反号”“距离翻倍”，四组真实内部变异均被上述唯一 midpoint 断言拒绝；没有在结果后追加伪造记录。脚本只改本进程函数绑定，并在 finally 恢复，未写源码。

变异必须保留真实窗口 w：`exact_sqrt(q)-delta` 不是原 `w-delta`，因为窗口显示 w 自身可能已有一 ULP 近似差。本次初试把变异写为 exact_sqrt(q) 再减，恰得到正确最终值而未红，随后改为在真实函数体恢复旧语句；最终脚本及日志记录的是正确的原路径回退。

## 修改边界

本次复核只新增 evidence 文件；未修改 src、tests 或 docs。旧门的严格替换由 gate_teeth 代理负责，最终参数网格和全套结果由主代理登记。
