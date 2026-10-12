# R11FIX 同类只读扫描（独立子审）

## 范围与边界

- 仅阅读本树 `src/`、`tools/`、`tests/` 及已复制审查输入；只写本 `scan/` 下的探针与证据。没有写姊妹树、审查树或 Git 状态。
- `G6K_findings.json` 的 `counts` 为 0 critical / 2 major / 0 minor；`findings` 只有 G6K-K01、G6K-K02。工单正文中的“6 条”“11 条”不对应新增发现，不应伪造条目。
- 这是一轮针对同根因的代码盘点、有限压力与交叉检查，不代替新的六路 G6 独立退出门，也不证明任意动态 Python 或任意第三方数值子类。

## 过滤化精确谓词库存

| 路径 | 输入与快路性质 | 本轮检查结论 |
|---|---|---|
| `kernel2d.geom.orient2d` | 原仅识别 Fraction；混合大 int/float 在减法时先舍入 | K02 原错确认；修后严格普通 float 才使用未含换算误差的快速界，其他先 Fraction 化 |
| `predicates.cross2_sign`、`dot2_sign` | 乘积界原已含换算误差；纯 Fraction 分母消去为整数算术 | 原压力未检出错误；本轮收紧：非普通 float 输入直接精确计算（保留全 Fraction 整数优化） |
| `predicates.orient3d` | 普通 float 界与 Fraction 正确舍入换算界分开 | 原压力未检出错误；本轮任意 int/其他非普通 float/Fraction 直接精确，普通 Fraction 的已有换算界保留 |
| `kernel3d.exact_geom._iv` | 普通 float 本身是点区间；非 float 用上下 `nextafter` 包围换算；溢出退 `[-inf,inf]` | int/Fraction 超范围及次正规压力无错；不是只认 Fraction 的舍入假设 |
| `kernel3d.exact_geom.polygon_locate` | AABB/点线段平方窗/绕数行列式使用外向区间；不确定则精确回退 | 与自写 Fraction 平方距离、绕数 oracle 对拍 2,520 格无错，含 `2**2000` 平移与 `tol=1/3` |
| `kernel2d.geom.point_in_polygon`、`_triangles_overlap`、`polygons_overlap` | 入口逐坐标 Fraction 化；SAT 投影/窗口用有理数，不是过滤化 float 判定 | 阅读所有相关入口，未发现同类换算快路；K02 直接耳切路径原先确实依赖错误 orient2d |
| `kernel3d.geom3.exact_point_in_convex_polyhedron`、`exact_convex_overlap` | 凸壳定向经过 orient3d；投影入口 exact_vector；法向与轴点积精确 | 无另一只认 Fraction 的过滤分支；orient3d 收紧同时保护凸壳 |
| `kernel3d.exact_geom._convex_surface_sat`、`_integer_tetrahedron_overlap`、`_star_union_overlap` | 正公分母整数提升；SAT 和轴去重为整数，精确分离/边界判定 | 未引入 float 过滤；非整数源输入先 vector/Fraction 化 |
| `lp._Exact.reduced_sign` | `_Exact.__init__` 原始模型先 Fraction 化；成本、乘数、系数 float 视图均有换算/下溢界，失败精确回退 | 自写 Fraction 约化成本 1,000 极端指数格无错，包含指数 ±1100 与相消 |

普通非有限输入（NaN/Inf）不是有限精确有理几何输入；本轮没有把合理异常当静默错，也没有扩展恶意重载 `__float__`/算术运算的自定义类型合同。

### 可复跑数值证据

命令（在本树根目录）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/R11FIX_evidence/scan/numeric_probe.py
```

- 脚本：[numeric_probe.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/numeric_probe.py)
- 修前：[numeric_probe_baseline.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/numeric_probe_baseline.json)：10,025 次检查，7 个错误均为 orient2d 同 K02。
- 修后：[numeric_probe_results.json](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/numeric_probe_results.json)：10,025 次检查，0 错。counts = cross2 2800 / dot2 2800 / orient2d 448 / orient3d 448 / interval 9 / polygon 2520 / reduced cost 1000。
- oracle 不调用生产的 orient3d_fraction、polygon_locate_fraction、SAT/向量或三角化辅助函数；行列式、绕数、点线段平方距离与约化成本均在脚本中独立按 Fraction 写出。此有限探针不等于误差界形式证明。

## 静态门：原实现额外同类盲点

[修前最小源码/输出](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/static_baseline_probes.json) 中 9 格有 8 格漏检，均已反馈 K01 实现方：

1. `root=norm_rational; box=[root]; root=abs; box[0](vector_rational(...))`：容器保存的 callable 没有按赋值时冻结，后续 rebind 污染先前值。
2. `False and (root:=abs)`：短路的零次路径消失。
3. `(root:=abs) if False else 0`：条件表达式路径顺序覆盖。
4. `try: raise ...; root=abs` 的 `except` 中真实 root 调用：handler 应从任意异常前缀合流，不是先扫完 try 末态。
5. 同形 `finally`：必须承接早先异常路径，不能仅看末态。
6. `match 2` 的首个未取 case `root=abs` 污染后一个 case 的 root 调用。
7. `break; root=abs` 的死赋值污染循环出口。
8. 零次推导式内 `(root:=abs)` 擦除外层 callable。

另独立确认 import scope 问题：模块级 `norm_rational as build` 被另一个函数内部的 `abs as build` 在全局 AST import 预扫中覆盖，导致模块级别名调用漏门。已反馈实现方，不能以未知动态反射边界豁免此显式词法导入。

本节记录的是 K01 同根因的静态门盲区，不把它们夸大为多条新生产数值错。修后交叉复查结果另见追加小节。

## M4a 门与保护范围

- 门文件：`tests/test_m4_bdda_adapter.py`、`tests/test_m4_bdda_shadow.py`、`tests/test_m4_bdda_vv_reader.py`。
- 已独立定向运行：`109 passed in 7.14s`（`PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider`，basetemp 位于本树 `reports/codex/R11FIX_evidence/tmp_scan_m4`）。最终全套结果应以主执行日志为准。
- 保留 15 家族 × 3 detection snapshots、14 份不同几何、legacy row identity、逐行差异哈希及分类牙；本轮没有改这些测试、fixtures、shadow expected 或 adapter。
- scanner 已有 `src/eab/adapters/bdda2d.py::load_window` 精确命名豁免，仅 legacy CSV input parsing。不得因新 scanner 流分析误报而放宽成整文件豁免。

## 修后静态门交叉复核

独立复查第一版重写时额外钉住了 `with`/`async with` 异常抑制、lambda 的 positional-only / keyword-only 默认绑定，以及生成器的消费时 late binding。它们已经反馈 K01 实现方并在最终实现中修复，不把初版中间态伪称最终遗留。

- [static_probe.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/static_probe.py) 可重放 28 针；[最终结果](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/static_probe_results.json) `count=28, missed=0`。每针源码只含其实际危险调用，不额外追加一个足以误导通过的尾部 root 调用。覆盖循环内二次/三次回边才出现的 callable、容器快照、循环 allocation-site 的旧对象引用、异常前缀、分支、短路、推导式、词法 import 与延迟生成器；二次冻结追加 assert 成功/失败各一针与 Dict key/value 交替、`**` 解包次序各一针。
- [consumer_probe.py](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/consumer_probe.py) 复跑的[生成器消费组合与负例结果](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/static_consumer_and_negative_results.json) 18 针全部符合：13 种 consumer 钉住生成器原危险表达式行，包括 tuple、星号、next、`__next__`、for、map 链、嵌套生成器、成员比较、sum/any、容器取出后消费和未知 consumer；5 条负例维持零报告，包含“生成器仅存为容器元素而没有执行”“已物化 tuple 不重新执行耗尽生成器”“外层 iterable 在创建时捕获旧 callable”“确定 rebind”“推导式局部作用域”。
- 静态实现使用有限源节点/词法输入引用及冻结 callable 标签；状态合流同时包含 bindings 与 heap，回边迭代没有深度/轮数上限。读取循环堆别名为集合闭包，不递归生成合成 AST；review 未见无限增长的名字构造路径。
- 已阅读新门的两条内部变异：删除零路径 join 时，红的是实际 `cone_intersection_margin` 的 `rounded-vector` 看护断言；禁掉回边迭代时，红的是循环内部第 5 行 `saved(vector_rational(q))`，不是无关尾部调用。
- 当前源级整仓扫描实跑原样输出：`exact construction AST gate: 0 violation(s)`。
- 二次冻结定向实跑两份新增测试：`124 passed in 1.25s`。这包含实现方最后已确认修复的 assert/Dict/AugAssign 与保留注解扫描门；本子审未在此后重新扩大探索范围。[最终机读汇总及源码哈希](file:///D:/eab-wt/cx-e2/reports/codex/R11FIX_evidence/scan/final_independent_summary.json) 已替换首次冻结的哈希。

## 最终差异边界与遗留

- 当前 tracked diff 的运行代码只涉及 `src/eab/kernel2d/geom.py`、`src/eab/predicates.py`、`tools/check_exact_construction.py`。新增门为两个 `test_r11fix_*.py`；`git diff -- tests` 为空，没有改写/删除旧测试、没有 skip/xfail。
- 其余 tracked diff 为 README 与本仓设计/canon 文档同步；姊妹树、fixtures、M4a adapter/旧门均未修改。
- 本文的 10,025 数值检查、46 静态正/负针和 M4a 定向检查只是有限独立佐证。完整 fresh-copy 全套与最终退出标记由主执行报告给出，不以本 memo 冒称已完成新的 G6。
- 静态分析边界仍是已知本地 AST 值、容器与控制流；反射、任意未知调用返回值、跨未知过程的全语言闭包语义并未被形式化证明。没有借该边界豁免本轮明确的循环/分支/异常/推导式和延迟生成器路径。
