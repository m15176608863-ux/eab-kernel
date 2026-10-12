# R12FIX 最终报告草稿交叉核对

## 结论

只读核对当前报告、policy、scanner/正向子集代码、R12 永久门与已改测试、设计同步和证据日志。**未发现必须阻断的确认不实陈述或把人工例外冒称机器证明的表述**。本核对不是另一轮 G6 数值正确性审查，也不为所有人工例外重新提供数学证明。

本次唯一写入是本反馈文件；未修改 README/docs/src/tests/tools/policy，也未启动全套或更改运行中的冻结内容。

## 实际核验

- 当前 policy：16936 个逐站点 waiver、213 个 src/tests/tools `.py` 依赖；逐项重新计算原字节 SHA-256 及路径集，与 policy.dependencies 完全一致；全部 waiver.reason 非空。
- raw_v1 为 9392，raw_v2 为 18630，与报告一致；它们是默认拒绝诊断，不是确认缺陷数。
- 九份修前日志末行与报告逐字一致。部分为 UTF-16 BOM，按实际编码读取后核对，无末行误报。
- `mutation_teeth.json` 四个 case 均为 `EXPECTED_ASSERTION_FAILURE`，回退后的 issue_count 都是 0；捕获断言为真实 `cone_intersection_margin` 行的 `G6L-01 closed-subset rejection assertion`，不是别处全图失效碰巧报红。
- git diff 显示没有 src 生产文件或 fixtures 修改；已改旧测试仅三个静态门文件，R9/R10/R11 台账与实际 diff 匹配，保留旧舍入 false-positive 禁止与 R10 2 秒超时。
- 数值保证范围与源码相符：自动 BinOp 仅纯整数字面量闭包；负幂/真除法/变量算术/AugAssign/sum 默认拒绝；普通未知属性、namespace 值、注解中的调用、反射/格式化须精确站点审阅。允许执行普通类型注解并不等于允许任意注解数值调用。
- 报告正确保留 test scaffold/top-level driver 子树边界；未把顶层独立 helper 按文件名整体豁免。Fraction 算法的人工理由、legacy 近似/显示检查和机器保证也明确分开。

## 建议的两处文案收口（非实现缺陷）

1. 报告第 40 行第 8 组写“执行注解及所有 dunder 反射默认拒绝”。“执行注解”可能被理解为普通 `x: int` 也一律拒绝；建议改为“**注解内调用及运行时 `__annotations__` / dunder 反射默认拒绝**”。这与正向子集 `visit_Call` 的 `in_annotation` 分支及设计 §2 更精确一致。普通类型注解不是全面禁用。
2. 报告第 96 节与末行仍是明确的等待占位；当前 `verification_summary.json` 尚不存在。最终请补原样全套末行、串/并行口径、各分片计时/总体 wall time、11368 收集与执行集合无漏重、最终源码无漂移，随后更新末行。建议 §5 同时直列 **16936 人工站点 / 213 Python 依赖**，并给 tests/test_* 新增 4727 站点审核及其 723 个 legacy 范围豁免的直接链接，避免读者只看源码/独立 oracle 两个列表而漏掉这部分证据。

建议链接：
- [helper 正向子集人工审核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/test_driver_helpers_positive_subset_review.json)
- [helper legacy 范围豁免](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/test_driver_helpers_positive_subset_exemptions.json)

## 冻结说明

本核对时报告 SHA-256：`34202a4eb468e55616557c0afc5593819b000e786eeaa27544bbc0ab1100f7d2`。policy SHA-256：`115f74bf16f1cf9b4d9141441d13186ede28d0fc5be924531abf8738221e697a`。报告之后可补最终数据；源码/policy 在全套期间不应变化。定向 280 passed / M4+docs 124 passed 数据由根代理告知，本反馈没有重新执行这些门，也不提前声称运行中的全套已通过。
