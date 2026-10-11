# E4 只读交叉复核（入口子代理）

范围：`limit.py` / `limit_multi.py` / `lp.py` 新有理数见证、自校验与逐体分辨筛查；不是六路 G6，也不作为 G6 退出证据。

## 复核结论

截至本次审读，未在有理数见证传递、精确模型一致性或反作用重新装配中发现阻断问题：

- `LPResult.exact_x/exact_y` 从有理数证书返回，maximize 正确翻转对偶号；`_lp_values` 只为仍等于对应float显示值的普通 float 复用证书，Fraction/ExactFloat 手改按新数读。
- `_check_columns` 共享锥方向/列序这一定义，但从原始坐标独立计算力矩、从原始 c/area 独立精确计算容量。没有复用 `_exact_wrench/_exact_shift` 的力矩错误；调用方原点处直接检查与内部形心精确移回机构等价。
- 多体检查器重新按 `body_a` 正、`body_b` 负装配每体列；`_pair_powers` 用有理数 `y_a-y_b`。没有全局速度带吞掉慢体贯入。
- 多体噪声估计使用各体接触形心/臂长及该体到调用方原点距离；扰动在本体帧施加再精确移到公共LP原点。全局形心不再充当本体臂長。

## 实测

- `tests/test_limit_exact_selfcheck.py`：`78 passed in 0.27s`（`cross_review_limit_new_tests.log`）。没有执行源码突变。
- `cross_review_limit_probe.json`：分别给 alpha、首个非零 lambda、mechanism、row_dual 的 exact 值加 `1/10^100`，新 `_ExactFloat` 与旧标量**float读数完全相同**，但 exact 不同；全部 `ok=False`。alpha/lambda 静力失败，mechanism/row 的强对偶/容许或互补失败。3D两体含远处重体的 alpha×(1−10^-100) 同样 `static_ok=False`。
- 探针第一版误选零lambda：从0变1e-100并不保持float相同，因此测试前提红；改选非零项后完成。此为探针输入错误，不是实现缺陷。
- 不可能的声称排除：`float(1−10^-100)==1.0`，纯float注入先舍回原值后数据没有变化；任何检查器均无从“抓到”已丢失的信息。测试/报告必须说 Fraction保留的任意k误差，而不是声称浮点能保留任意k。
- 手改 `contact_forces` 显示字段不影响证明通过，是当前明确契约：证书静力来自完整 lambdas，显示力/active会按tol截断。应避免把“静力全部核”误读为显示字段也逐项认证。

## 非阻断意见与发现后续

1. `worst_power_rel` 新实现当时直接返回 raw negative power，并非无量纲相对值；已告知 limit 代理修正或明确其报告定义。它不参与ok判定。
2. 模块头部当时还留“驱动不为1、相对间隙超标”旧措辞；精确LP对偶是drive>=1，alpha>0时由互补强制等号，alpha=0允许drive>1。已告知清理。
3. 旧可分辨性筛查会以±舍入邻域不可行覆盖原始LP status/alpha，与用户精确答案原则冲突。limit代理独立找到，父任务已批准改成只报告 `resolvability/resolvability_statuses`；本交叉复核随后接手其LP证书旧门改写。这个策略修正仍须新门/全套确认，本文件不提前声称完成。
4. `tests/test_lp_certificates.py::_exact_limit_lp` 的容量oracle原用 `Fraction(C.cap)`（已经浮点乘过），不是精确c*A。将按原输入Fraction乘积加固并记录测试台账，避免“同数据精确对照”自己用错模型。
