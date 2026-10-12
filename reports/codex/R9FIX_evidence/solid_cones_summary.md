# R9FIX 同类补扫：折面实体公共法锥

本项属于 G6I-02 同根扩展，不另虚增发现数量。独立只读复核发现：原折面盒输入的 `edge_arc_contains(P,(4,5),(0,0,1))` 返回 -1，而原始 roof 方程表明该方向正是邻接三角面的外法向，应为弧端点 0。边 (4,7) 相同；(5,6)/(6,7) 的邻接面法向 (-1,-1,2) 同样被错误拒绝。只给公共入口添加 descriptor 注释不足以满足此次实体法锥同类修复。

## 根治与边界

- 公共 `vertex_cone_contains`、`edge_arc_contains`、`cone_constraints` 先取 `geom3.exact_surface`，使用声明三角拓扑。`cone_intersection_margin` 的约束和 noise 也使用该实体表面；公共 `cones_intersect_relint` 从公共 constraints 取值。
- 逐源码确认 `exact_surface` 保留所有原顶点且 source_vertices 是恒等映射，平面源面保留，不做 convex hull 或顶点重排。源棱仍用原顶点编号，折面内部对角也可直接查询。
- 单盖语义没有偷改。新增显式 `_source_cone_constraints` / `_source_cones_intersect_relint` 供 `vv3_cover` 的源描述符路径；原 `_qvertex_contains` / `_qedge_contains` 为 source 单盖内部路径加清晰注释。
- 公共与源描述符 Gordan 缓存 key 分别带其 constraints 实现；公共 key 另含 exact_surface 实现身份，缓存函数消费传入实现，避免绕过拓扑步或串用。

## 红绿与变异

- [新门](file:///D:/eab-wt/cx-e2/tests/test_r9fix_solid_cones.py)：39 格。独立预期来自 roof 方程、手写邻接三角法向和原始边向量，未调用被测 triangulator、normal、cone 作真值。含 3 种尺度、1e8 平移、精确 3-4-5 旋转、源环没有的内部凸折棱。
- [修前红](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_red.log)：初始 20 格全部红，另 2 变异格尚未执行。`declared-triangle-cone-endpoint` 实际 -1、预期 0；`declared-internal-ridge-constraint` 缺少 5→7 与反向精确边约束。
- [定向绿](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_final.log)：`264 passed in 7.71s`。包括新门、G6I03、既有 cone strict / lowdim / E5a / E5a2 source-descriptor / kernel covers 与 G0 真内部变异门；既有门无删除或放松。
- [内部变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/run_solid_cone_mutation.py)：编译真实函数体，只移除内部 exact_surface 包装，未改返回记录、未写生产源文件。
- [变异红](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_mutation.log)：`37 failed, 2 deselected in 0.20s`；命中目标法锥、声明内部对角断言，不是无关路径错误。

## 附：统一构造独立复核

[脚本](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/independent_construction_probe.py) / [日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/independent_construction_probe.log)：1200 随机 Fraction，指数 [-4200,2200]，生产与独立 bit-search 两套分别逐值取 Fraction 中点证书。2342 sqrt、1948 scalar 通过，58 sqrt / 452 scalar 正确溢出，200 signed unit 逐分量证书与负零符号通过，0.422s，未找到新数值反例。

附加静态门对抗先找出 6 类语法绕过：类型注释赋值、局部 converter alias、局部 sqrt alias、map(converter)、全局捕获、海象赋值。已新增红门交 root 根治：[修前证据](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/static_adversarial_initial.json) / [pytest 红日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/static_adversarial_red.log)。静态门最终结果由总报告记录。

此为执行团队内补扫，不冒充正式六路独立 G6 退出复审。
