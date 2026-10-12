# tests oracle/performance：结构站点逐项只读审核

输入为 raw_scan_round4.json；只覆盖 tests/e5*oracle.py、tests/perf_*reference.py、tests/test_perf_*.py，并排除四类数值规则。

共 162 个 raw 站点，59 个函数作用域；本审查 **0 条 waiver 批准**。

| 分类 | 站点数 |
|---|---:|
| bounded_legacy_diagnostic | 27 |
| dynamic_numeric_rewrite | 44 |
| exact_proof_gap | 53 |
| intentional_mutation | 6 |
| metadata | 25 |
| test_harness | 7 |

## 必须保留的边界

- 数值 map、lambda 调用 _dot、容器内取出 _segment/_triangle、_outcome(func) 都需简单改写；不能由 caller 例外绕过。
- 有理见证、精确平方距离和最终 construction 边界的源类型缺失属于 proof gap，不是数值 waiver 的理由。
- escape oracle 的 raw-coordinate 噪声/搜索窗口确有近似几何派生量；仅有 bounded legacy diagnostic 角色，不能改写成‘无先舍入’。
- perf_escape 冻结参考的 move 先执行给定坐标平移；e5a_escape 当前 move 先分别转 Fraction。逐项理由保留了这一区别。
- 性能 witness reference 共用生产 exact_geom 原语，仅属性能对照，不是独立 correctness oracle。
- _mutant 的 exec/compile 是注入被测函数内部缺陷的专用基架；不推广为普通动态调用准入。

## 可重复核对

生成脚本只读输入 JSON 与选中源文件，仅写本审核的 JSON/Markdown；每项记录实际最小函数源码 SHA-256。
raw AST 节点在当前函数源码中未找到的站点：0。这是快照漂移标志，不会自动批准或删除记录。

