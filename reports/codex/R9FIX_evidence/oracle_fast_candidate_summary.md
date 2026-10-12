# 独立构造参考组：已认证候选快路径草案

**本轮仅写 evidence scratch，没有改 src/tests。**

## 建议的最小改法

保留现有位模式二分不动，在 `_round_positive` 前增加候选快路径：

1. scalar 用 `float(Fraction)` 给候选；平方根用 80 位 Decimal 除法与 sqrt 给候选。候选只用于寻找一个 binary64，绝不作为答案依据。
2. 对每个候选，把它与上下相邻 binary64 的中点转为 Fraction，按 power=1 或 2 比较完整精确输入，使用候选最低位奇偶检查 RN-even。
3. 两侧证书通过才返回；证书失败、Decimal 异常、非有限候选一律回退到原位模式二分。
4. 获准舍零及默认非零下溢异常契约不变；最大有限值的上邻点用精确 `2^1024` 构造中点，不把 inf 转 Fraction。
5. `scalar_exact` identity 快路径同时从 `isinstance(value,float)` 收紧为 `type(value) is float`，不让带精确语义的 float 子类绕过处理。

候选算法与 production 的 integer-isqrt 仍不同；不 import 生产 construction 或任何几何原语。最终正确性只取决于 Fraction 证书与原有独立位二分，不取决于 Decimal 的 80 位是否足够。

## 已验证

运行 [scratch 脚本](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/oracle_fast_candidate.py)，结果保存在 [JSON](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/oracle_fast_candidate.json)。

- **4114 格**与原位二分结果一致；每个有限结果另由测试侧独立 Fraction 中点证书核验。
- 包括现有 48 个标量中点、48 个平方根中点、4000 个随机有理尺度、18 个在 Decimal80 分辨率以内跨中点的精确扰动。
- 3523 格获证快返，591 格回退位二分（含真正上溢与特意制造的中点歧义），没有将错误候选升级为答案。
- 将候选强制污染为零：96 格中 90 格证书拒绝并回退，6 格零本来就是合法 RN 结果；结果仍全部一致。
- default 不允许下溢时，scalar/root 都仍抛 `ArithmeticError`。
- 3000 个常见有限 root、禁用缓存的局部计时：原位二分 **0.3267754 s**，认证候选 **0.0524291 s**，约 **6.23 倍**。这是构造局部基准，不是全套或 bb52 的承诺加速。

可应用草案：[统一 diff](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/oracle_fast_candidate.patch)。它仅增加 Decimal imports、两个私有候选/证书 helper、`_round_positive` 的认证前置路径，并收紧 identity 类型检查；本代理没有应用它。

## 应用后必查

- 为 candidate helper 的内部 float 转换登记“仅候选，逐值精确核验，不作答案或分支”的静态白名单理由；不允许调用方绕过统一边界。
- 把强制零候选及中点歧义回退移入正式测试，保留全部现有构造中点门。
- 重跑 construction/helper 门与下一次完整套件；下一套按实际 JUnit 模块耗时重新均衡分片，构造局部加速不能替代全套计时。
