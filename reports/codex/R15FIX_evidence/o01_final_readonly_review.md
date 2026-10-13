# O01 最终版独立只读复核

复核者：O02 分工代理；本次仅阅读生产源/测试，运行测试并新增本文和日志，没有编辑生产源或测试。

## 结论
**未发现最终 O01 两个 API 新引入的算术错误。** `exact_contact_forces` 与显示合力使用完全相同的 tol 选列结果；显式下溢标记满足 iff，而不是用“发生一般舍入”替代下溢。证书显示策略兼容原仓中已承诺的最小次正规承载量返回门，不修改旧门。

## 逐项检查
1. 单体 `limit_load` 和多体 `limit_load_multi` 的列力均为 `raw[j] * Fraction(column_component)`，不在乘积阶段转为 float。
2. 列筛选比较精确平方范数，保留 `>` 边界；tol=0/1 有产物互异门。原来会溢出的中间相反切力无需被构造成 binary64。
3. `forces` 从 `Fraction(0)` 开始，仅在同一 `on[j]` 为真时累加。先 `exact_forces = tuple(forces)` 再构造 float；该不可变 tuple 是 **tol 截断后的完整精确显示量证书**，不是未截断静力证书。
4. `force_underflow = any(bool(v) and display == 0 ...)`：当且仅当至少一项精确合力非零、显示为零才为真。正确舍入但非零的普通/次正规分量不触发。真正的精确零也不触发。
5. `scalar_rational(..., allow_underflow=True, quantity="contact force")` 保留 `-2^-1075` 的负零符号；允许下溢以返回完整证书，不允许上溢。两 API 的超界门仍期待具名 `ConstructionDomainError`。
6. 两个 dataclass 新字段均追加到原字段末尾，有空 tuple / False 默认值；已有位置参数构造仍兼容。非最优结果没有伪造合力证书。
7. 原始静力核仍基于 lambdas、原始接触列/力矩，不使用显示合力或新增证书代替。
8. 查看 `git diff -- tests/test_r13fix_mechanics_differential.py` 为空。原失败门未修改、未 skip/xfail、未缩网格。

## 独立实跑
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r15fix_force_reports.py 'tests/test_r13fix_mechanics_differential.py::test_public_limit_single_and_multi_match_analytic_sliding_capacity[-1073]' --basetemp=reports/codex/R15FIX_evidence/tmp/o01_final_readonly_review
```
最后一行原样：`49 passed in 0.17s`。

[实跑日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o01_final_readonly_review_run.log)

新门 48 格覆盖双 API、二维/三维、大动态范围相消、tol 边界、相反中间列力溢出、真正零、正负低于范围、正负最小次正规一半、可表达最小次正规及最终上溢。另独立重跑原 `[-1073]` 格，保持 `status=optimal`、`alpha=2^-1074` 和精确容量证书。

## 变异断言复核
12 格 = 6 种真实内部变异 × 两 API，实跑全部通过看护门：
|真实内部变异|应击中的指定断言|
|---|---|
|移除列乘积的 Fraction 转换|`O01 complete exact resultant`|
|累加初值改回 float 0.0|`O01 complete exact resultant`|
|把受检输出改成 `_fl`|最终上溢 `DID NOT RAISE`|
|恢复中间浮点范数|`O01 selected intermediates must not be constructed`|
|把下溢标记固定 False|`O01 nonzero force display underflow must be flagged`|
|返回空精确证书|`O01 exact underflow resultant certificate`|
变异仅改变运行内存中的真正生产函数，未在输出后追加伪数据；每条异常匹配的是对应故障断言。

## 解释边界
本结论是指定修复路径的代码审阅和有限参数验证，不是独立 G6 里程碑退出或任意 LP 的全域证明。已回读 `docs/r15fix_design_sync.md` 第 1 节：精确字段、标记 iff、负零、可表达次正规不误标、上溢拒答、同 tol 证书边界均已明确；README 顶条链接到该现行合同。“静力证明来自 lambdas”的边界保留。本轮最初新增的“最终下溢一律拒答”门属于实现中的中间策略，后因原仓成功域被破坏而调整，报告应如实列账，不能称 reject 与返回证书两个不同合同之间存在简单逻辑蕴含。

## 复核时文件 SHA-256
|文件|SHA-256|
|---|---|
|`src/eab/limit.py`|`e4bdf3c0c363b24b1bdbeee290e5aa6239e2a1c5a544d35e8c798a6f4b14a96f`|
|`src/eab/limit_multi.py`|`d3c6a6f6f0ccacfcd0b722b0dc46dd9ea26b7a5e69971e4c3cbe6d08cc6f3a65`|
|`tests/test_r15fix_force_reports.py`|`c2110b8b99f840509aa1f21eb67b5b5ee0e86fa96e8aeebdec8020c6bf5acea7`|
|`tests/test_r13fix_mechanics_differential.py`|`3ed3a3a7a626b1d830440899eb6682fc276b775d551f5b03e2b2ca06e92662db`|
