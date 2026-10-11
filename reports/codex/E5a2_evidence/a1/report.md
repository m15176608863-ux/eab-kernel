# WO-E5a2 A1 一般闭表面：实现与证据

## 结论、范围和前提

三个旧入口现已接到给定坐标的有理数语义：`point_in_polyhedron`、`segment_crosses_face`、`polyhedra_overlap`。不暗中凸化非凸源表面，不再用坐标噪声、网格或有限阶梯微推裁决三态。

**适用域是有效、向外一致定向、闭合、嵌入的三角化表面。** 本实现不负责把开口、自交、朝向不一致的输入修成实体；非平面 face-ring 按既定投影耳切表示折面。没有宣称 G6 或新 worktree 退出。既有启发式私有辅助函数为兼容仍保留，但旧公共相交入口不再调用它们。

- 零 tol：严格按给定有限浮点数的精确有理值分类。
- 点 tol > 0：点到**实际三角表面**的欧氏距离不大于 tol 时报告 0；否则保留精确内外。
- 相交 tol > 0：真实内部相交始终为 1；仅当严格分离且真实表面距离不大于 tol 时报告 0。不再把微贯入吞成相触。
- 横截：排除端点、共面和源环边界；内部折棱命中另以沿线一侧内部、一侧外部核验，纯切向屋脊接触不算穿面。

## 完备性结构（不是随机证人）

1. 精确 AABB 只作必要条件排除。
2. 逐三角平面核验所有源顶点均位于内侧，成立时才允许凸 SAT；它证明**输入表面本身**凸，不以其凸包替代微凹输入。
3. 一般路径先核顶点包含。闭边界不相交时，其每个连通分量上的内外状态恒定，包含测试足以决定是否有包含。
4. 有边界相交时，把每个三角形按对方所有三角平面分割；对共面三角形额外按其三条边的垂直平面分割。每个开二维凸 cell 内，对方的边界/内外状态恒定。
5. 非空有界三维交集必在某侧表面具有开二维边界 patch。此 patch 或位于另一实体内部，或双方表面重合且内侧相同，因而被上述 cell 穷尽。共同棱附近的重叠不会被“没有顶点严格在内”漏掉。
6. cell 顶点平均值严格处于 cell 相对内部。沿其源面内法向，步长取所有正平面截获参数的最小值的一半，精确保证不越过下一个平面；所得 Fraction 证人必须在双方严格内部。共面分支单独保留并有内部突变牙。
7. 只有没有内部证人时，闭三角相交/完整点面及棱棱距离决定接触与正 tol 报告带。

这是一条有限、完备的排列分割路径；并非固定 epsilon 或有次数上限的试探。代价是临界非凸/微凹输入可能昂贵，尤其旧 escape 二分不再因“噪声相触”零次退出。

## 独立 oracle 与新门

[新门](file:///D:/eab-wt/cx-e2/tests/test_e5a2_surface.py) 使用独立有理矩形并集真值，以及[独立 oracle](file:///D:/eab-wt/cx-e2/tests/e5a2_surface_oracle.py) 的星形体径向四面体并集整数 SAT、独立点三角/棱棱距离。oracle 只读原始顶点和面环；不 import 生产法向、三角化、点包含、凸包、SAT 或 arrangement 原语。星形核点需逐面严格内侧证书，不能核验时明确 assert 拒绝，不暗中凸化 U 形等无核输入。

覆盖：L 凹体凹口填满、2^-70 薄交/薄缝、相同凹体共面内部交、共同棱、1e-3/1/1e3 缩放、0/1e3/1e6 平移、有理旋转、原浮点工程坐标舍入、随机偏移、凸 SAT 对强制一般 Fraction 路径逐项对拍、真正欧氏角点报告带、切向屋脊与真正折棱横截。共面证人本身另通过独立矩形并集成员式。

没有新增浮点过滤或缓存：新增 AABB 是原值 Fraction 比较，SAT/安排均精确，故 A1 没有可缩小误差界或需删除对象身份的新增缓存键。性能代理的其它修改单独记账。

## 旧测试逐条改写台账

全部保留原测试函数、参数格与原浮点构造；没有 skip/xfail、删测试或缩小网格。

| 文件/函数 | 旧断言的问题 | 新断言与不减弱理由 |
|---|---|---|
| `test_kernel3d_geom::test_face_touching_stack_is_touching_under_rigid_motion`，32 格 | 舍入后仍硬判理想相触 0，escape 必须 0 | 原输入逐格由独立整数 tetra SAT/真距离核三态；原 escape 调用保留，非贯入须 0，hi 仍内须正确抛错，其余须返回正高度且独立证实出口非内；另加同系数有理仿射的理想相触门，未替换原输入。 |
| `test_kernel3d_geom::test_overlap_coplanar_crossing_gate_has_teeth` | monkeypatch 已不走的旧 `_contact_cone_witness` | 原 X 交输入与贯入断言保留；内部修改实际 `_convex_surface_sat` 最终状态表达式，按零 tol 直接检查真内部被误报分离。专门共面 arrangement 缺失牙另外覆盖。 |
| `test_geom3_face_polygon::test_all_five_call_sites_route_through_the_single_helper` | 表面不再使用拟合面 helper | 原 cover/构造距离 helper 注入保留；原三条边界/射线/横截断言改在实际 `triangle_locate` 内注入。原几何输入不变。 |
| `test_geom3_overlap_witness::test_thin_notch_bite_is_detected` | exact_fill 舍入后可能真实微贯入 | 所有稳定 bite/gap 原解析真值不变；仅原边界格用独立原源面星形并集 oracle；另外保留轴对齐 exact_fill=0。 |
| `test_geom3_overlap_witness::test_x_crossing_lifted_boundaries` | 理想相触层舍入后未必 0 | 全部原抬升深度与变换格保留，稳定内外解析门不变；原相触层逐格对独立实际表面 oracle。 |
| `test_geom3_overlap_witness::test_overlap_resolution_is_documented` | 原四深度中两格要求吞真实微贯入 | 原 1e-10/1e-11/1e-13/1e-14 四格全部保留，独立 Fraction 原始 x 区间证实严格相交，四格都必须答 1。 |
| `test_g03_two_rulers::test_a_plate_thinner_than_the_coordinate_resolution_fails_loudly_with_the_reason` | 真可分离薄体要求旧 resolution 异常 | 保留工程/原点原输入，独立整数 tetra SAT 证明工程格分离，入口必须正确答 -1，body_distance 必须正且非贯入哨兵；原点 1e-6 距离原断言不变。 |

`test_margin_penetration` 和 `test_invariance_geom` 的联动迁移由 root 负责，不混入本表声称完成。

## 验证记录

- [一般及迁移定向组](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/corrected.log)：`82 passed in 9.95s`。
- [保留原 escape 调用的 32 格](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/stack_final.log)：`32 passed in 87.91s (0:01:27)`。
- [其余六文件组](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/all_nonstack.log)：`370 passed, 32 deselected in 59.08s`，32 格仅为分组运行，已在上一日志完整执行；该组早于新增折棱横截补门。
- [新增屋脊补门及相邻回归](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/fold.log)：`31 passed in 3.81s`。
- [共面源码突变记录](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/mutation_coplanar.json)、[目标失败日志](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/mutation_coplanar.log)：内部 `elif loc == 0` 改为永不进入，9 个目标格均在 `assert G.polyhedra_overlap(a,a)==1` 报红；不是求解器择点断言。磁盘生产源未改，函数源码 SHA256 已保存。
- 折棱内部横截守卫去掉时，解析屋脊 `not segment_crosses_face(...)` 目标断言报红（新门中的受控 mutation 测试）；普通面内部快路没有新增全体查询。

上述是开发过程分组证据，不是最终全套和非并行性能实测。早期 `legacy.log` / `gates.log`、被中断的 `revised.log` 为中间失败/过期代码诊断，明确不算最终绿。源/旧测试按 HEAD 原 LF 换行保留。

## WO-E5b 交接

`margin`/`entrance3`/`interlock`/`frozen` 的其它分支仍按各自旧政策，不能由本次三入口精确化推导全链精确。特别是 escape 的初始微贯入现在会真实进入二分，需以性能证据而非删调用处理；`Polyhedron.translated` 的 float 加法仍可能把额外 Fraction 理想仿射测试重新舍入，上层不得冒称保持有理输入。旧构造距离仍是浮点输出，A1 只关闭指定成员、横截和实体相交语义。

## 最后补充：精确值的本次调用内复用

- `_point_in_triangles` 接受同次相交查询已构造的 `planes` / `bounds`；边界与射线共享同一批有理平面偏移，`triangle_locate` 可使用已精确算出的法向。它不是持久缓存，不存在跨对象键或失效策略。独立 L 矩形并集的 180 个点逐项核 fresh/prepared 两路径。
- [局部优化前](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/point_query_before.json) 与[优化后](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/point_query_after.json)：192 次查询 0.0768979 s → 0.0502599 s，逐项结果完全相同；这是微基准，不能推出全套加速比例。运行期间其它代理也在优化精确算术，整套归因需 root 的冻结后 profile。
- [最后核心组](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/final_core.log)：`83 passed in 3.08s`（30 个新 A1 格 + 既有 E5a 原语 + 活路径 monkeypatch 门）。
- 指定共面分支突变已在局部复用之后重放，`mutation_coplanar.json` 内源码 SHA256 是最新函数；仍 9 个目标断言红。
