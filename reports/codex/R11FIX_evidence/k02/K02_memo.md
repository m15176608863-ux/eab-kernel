# G6K-K02 修复备忘（主报告合并材料）

## 范围与根因

只改 `src/eab/kernel2d/geom.py`、`src/eab/predicates.py`，新增
`tests/test_r11fix_numeric_types.py`；既有测试文件零修改。

`orient2d` 的 Shewchuk 快路界原先只覆盖 binary64 运算误差，但入口仅排除
`Fraction`。Python `int - float` 先把整数舍入为 binary64，大于 `2**53` 时的
输入换算误差没有计入界，因此可以以错误符号远离旧界而被接受。同根因另一个
范围表现是 `2**1024`、`2**4096` 与浮点混合相减直接抛 `OverflowError`，尽管
符号谓词的整数/有理数计算完全可表示；本轮一并修复。

## 修前红 → 修后绿

最终测试逐字重放到冻结 `baseline/src`，排除尚未存在的修复定位 mutation harness：

```text
6 failed, 39 passed, 1 deselected in 0.69s
```

其中真正的语义失败是：

1. `test_mixed_integer_orientation_keeps_exact_negative_sign`：精确行列式 `-3`，却 `1 == -1` 失败。
2. `test_mixed_integer_orientation_keeps_exact_zero`：精确行列式 `0`，却 `1 == 0` 失败。
3. `test_all_3072_review_integer_float_orientations_have_exact_signs`：`wrong=102`、`sign_reversals=82`、`exact_zero_errors=20`。
4. `test_mixed_nondegenerate_triangle_is_not_silently_triangulated_to_empty`：精确两倍面积为 `1`，真实耳切输出 `[] != [(0,1,2)]`。
5. 大整数范围两格：`test_mixed_integer_float_subtraction_does_not_require_binary64_range[1024/4096]` 在生产 `detleft` 处抛 `OverflowError: int too large to convert to float`。

早期修前日志额外有 `source.count(repaired)==1` 失败，因为修复当时尚不存在；它不是数值缺陷证据，亦不计入变异杀伤结果。

最终新文件：

```text
46 passed in 0.55s
```

此前包含新门及原有同类门的定向合集（新门当时为 40 格，后另加 6 个三维 SAT 格）：

```text
488 passed in 28.93s
```

命令包含 `test_filtered_predicates.py`、`test_e5a2_bilinear_integer.py`、
`test_kernel2d_covers_e3.py`、`test_hull_robustness.py`、`test_geom3_e5a.py`、
`test_lp_certificates.py`；不替代主代理最终全套及 M4a 门。

## 治根修法

- `orient2d`：仅 `type(v) is float` 的全部普通 binary64 坐标可以进入原误差界快路；其余（任意大小整数、Fraction、混合）先在原输入上转 Fraction，精确求符号。没有预先舍入坐标。
- `cross2_sign` / `dot2_sign`：保留已有纯 Fraction 的共同分母整数快算；非普通 float 的其他组合统一精确求值，不再依赖数值类型隐式转换。纯 float 的有界快路不变。
- `orient3d`：保留已有普通 float / Fraction 快路，因为其转换误差已经显式纳入 `64u * M-permanent` 和绝对下溢传播项；对其他类型提前精确求值。原 `test_orient3d_filter_has_a_real_fast_path` 同时要求 float 与 Fraction 的真正快路，本轮完整保留，未弱化门。
- 没有改变任何构造输出契约，也未新增允许静默 0、Inf 或错号的路径。

## 变异牙

在内存中直接替换真实生产 `orient2d` 的入口类型门为旧版“仅识别 Fraction”，
不在产出后添加假结果，不修改磁盘源文件。重新调用上述前四条语义测试，全部
捕获相应的数值断言；完整 3072 格再次恰好得到 `102/82/20`。实际耳切路径也再次
产生空三角列表。`mutation.json` 保存每条 AssertionError 和生产调用栈。

## 同类全仓扫描与边界

| 位置/类别 | 审核结论及验证 |
|---|---|
| `kernel2d/geom.py::orient2d` | 唯一确认的同根因符号错误；另含超范围整数提前溢出，一并修复。3072 格完整独立 Fraction oracle、非退化三角传播。 |
| `predicates.py::cross2_sign/dot2_sign` | 旧转换界已含换算误差，未确认原答案错误；收紧到非 float 精确路径，97 组混合类型和既有 2616 对纯 Fraction 门。 |
| `predicates.py::orient3d` | 原 Fraction 转换界保守；收紧其他类型路由，3072 个审查二维格提升为四面体，含正/负/精确零；保留原快路实证门。 |
| `kernel2d/geom.py::_point_in_polygon/_triangles_overlap/polygons_overlap` | 原入口先 Fraction 化，投影/差/窗口平方均在原有理数上；二维解析矩形含重叠、接触、分离，以及直接三角 SAT。 |
| `kernel3d/exact_geom.py::_iv/_edge_window_filter/polygon_locate` | 非 float 输入向两侧 nextafter 扩区间，转换溢出给全区间、结果不确定退精确；无需无因改写。新增整数范围至 `2**4096`，尺度 `1e-400/1/1e400`、精确边界与内外、区间包含性。 |
| `kernel3d/geom3.py::exact_convex_overlap/exact_point_in_convex_polyhedron` | 输入向量先 exact_vector，面法向与边叉积 SAT 全精确；新增 6 格混合整数大平移/极小极大尺度三维 box 的解析 SAT/成员门。 |
| `kernel2d/exact.py`、`kernel3d/g03_exact.py`、`kernel3d/exact_sweep.py` | 原始坐标先有理数化；整数公共分母、投影、事件窗口并非 float 快路。未发现相同类型换算漏洞。 |
| `lp.py::_Exact.reduced_sign` | 输入统一 Fraction，浮点候选副本由保留精确值的 `_fl` 建立；误差界含 conversion/product/sum 及 tiny 放大，越界退原始 Fraction。原 `test_lp_certificates.py` 全部本次定向复跑；独立扫描代理另有 mixed-type pressure。 |
| 显示/名义诊断与旧私有 helper | 不是新增精确符号快路；不把普通浮点构造 helper 宣传为精确谓词。未因关键词搜索任意改动不相关内核。 |

测试 oracle 仅用自行展开的 Fraction 行列式和解析轴对齐 box 几何，不用生产的
Fraction reference、SAT、向量或几何 primitive。所有格子都执行；没有 skip、xfail、
缩网格或删旧断言。有限扫描与压力不是对任意自定义数值类重载行为的形式化证明。

## 可复跑证据

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 reports/codex/R11FIX_evidence/k02/run_evidence.py baseline
python -X utf8 reports/codex/R11FIX_evidence/k02/run_evidence.py green
python -X utf8 reports/codex/R11FIX_evidence/k02/run_evidence.py mutation
```

`final_baseline.json` / `final_green.json` 记录命令、源/测试 SHA-256、返回码和耗时；
对应 `.log` 是完整 pytest 输出。所有源码/测试于本备忘交付后冻结，等待主代理全套。

过程说明：证据 runner 初次使用 Windows 反斜杠作为 pytest `pythonpath` ini 覆盖，
被 ini 解析为错误路径导致收集期 ModuleNotFoundError；已改 `Path.as_posix()`，最终
两次重放正常，前述收集错误不计数值失败。没有新增静态门白名单；新测试原四处
`float(2**e)` 改为完全相同精确值的 `math.ldexp(1.,e)` / `2.**53`，不改变任何格子。
