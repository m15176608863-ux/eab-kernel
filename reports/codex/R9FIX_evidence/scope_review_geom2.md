# R9FIX 收尾只读核查：有限域与声明表面

本核查由执行团队内的二维/法锥修复者完成，不是独立 G6。收尾阶段只读源码、测试及既存日志；仅新增本报告，未运行长测试，未改源码、测试或设计文档。目标是核对同类扫描边界及输入六条的看护证据，不声称全仓形式证明。以下定向绿是各修复阶段的快照，最终冻结全套以总报告为准。

## 1. 有限接触域覆盖

- 凸 `first_entrance`：同向共线支撑先合并裁剪，保留源 facet；精确到达时刻之后，VE/EV 的源边投影及 FF 的闭段重叠进入 `_facet_in_domain`。获选、精确并列和 near 标签都核有限源域；VE/EV 见证不再 clamp。平直分段内点、分界点双标签、交换 EV、FF 初触和不等长链均有门。
- 凹 `first_entrance`：原有精确 gap 与闭段投影范围共同筛选；不是只筛最终单一标签。`shortest_exit` 的 selected/tied/near 来自已核段域的候选集合。
- `covers.enumerate_covers` / `first_entrance_for_vertex`：使用 `_in_segment_exact`；正窗口和显式 `require_in_segment=False` 是候选枚举契约，不应混淆为精确接触认证。
- `local_facets` / `ambiguous_facets` 是平移无关源盖描述，不声称当前位形接触；成员判定的非零报告带使用有限 E 边界段距离，也不自行选择接触标签。
- 证据边界：加强版 150 对 polyomino 脚本核了全部成功首入的 selected/tied 标签与同点见证；2160 个首入完成，原 23 个 FF 异常不再出现。该有限网格不是任意多边形完备性证明。`shortest_exit` 仍是局部盖选择，不是一般凹体全局穿透深度。

详见 [二维小结](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_summary.md) 与 [压力日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_stress.log)。

## 2. 声明表面与源描述符的明确分界

| API 类别 | 当前实际语义 |
|---|---|
| `Polyhedron.is_convex` / `reflex_edges` / `dihedral_turn` | 先 `exact_surface`，按声明折面三角拓扑；内部折棱属于真实棱 |
| 公共 `vertex_cone_contains` / `edge_arc_contains` / `cone_constraints` | 先 `exact_surface`，不能以源 Newell 法向替代实际三角法向 |
| `cone_intersection_margin` / 公共 `cones_intersect_relint` | 实体表面约束；公共 Gordan 缓存与源描述符缓存分离 |
| `vf_cover` / `fv_cover` / `ee_cover` / `ve3_cover` / `ev3_cover` / `vv3_cover` / `enumerate_covers3` | 保留源特征标签；对非平面源环是 **source-ring descriptor**，不是折面实体接触盖；模块契约明确说明 |
| `_source_cone_constraints` / `_source_cones_intersect_relint` 及内部 `_qvertex_contains` / `_qedge_contains` | 上述源单盖内部专用；不是公共实体法锥的替代入口 |
| `face_normal` / `vertex_edge_dirs` / `vertex_edges` | 源环描述符工具；实体调用方必须先选声明表面 |
| `exact_convex_view` 及显式凸 API | 输入顶点凸包语义，与声明凹折面实体不同 |

已逐源码确认 `exact_surface` 保留所有原顶点及恒等 source-vertex 映射，仅把非平面源环换为声明三角形，平面面环保留；不经过凸包重排。新门含源环没有的内部凸对角线查询、旋转、尺度及大平移。公共法锥旧实现的邻接面法向端点会错报 -1，新门要求 0；不是仅给旧错误添加 descriptor 注释。

`topology_summary.md` 的早期扫描段把公共局部锥一并视作 source descriptor，是**后续法锥修复之前的历史状态**；现代码和 [法锥小结](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_summary.md) 以上表为准，已请 root 标注历史修订。

`manifold_issues` 现在逐闭壳分量核朝向及嵌套奇偶，拒绝分量接触/相交的嵌套推断；空列表仍不认证单分量无自交、顶点链接为圆或所有输入有效性。一般非嵌入网格的全套拓扑有效性不在本轮修复证明范围。

## 3. 六条输入与绿/变异断言对照

| 输入 | 正向看护门 / 关键断言 | 变异真正进入的内部步骤与命中断言 |
|---|---|---|
| G6I-01 | `test_collinear_support_chooses_only_contacting_source_edge` 精确标签集合；FF 两门核全部 ties 有真实闭段接触、见证同点 | `_facet_in_domain` 恒真；命中 `finite source edge labels`，独立变异日志 16 failed，端点 8 格仍绿 |
| G6I-02 | `test_g6i02_declared_folded_surface_is_not_convex`、`reflex_edges_include_declared_internal_ridge`、`dihedral_uses_incident_declared_triangles`；另有公共法锥 39 格 | 真实函数体 `P = exact_surface(self)` 改回 `P = self`；命中 `declared-roof-midpoint-concavity`、`declared-folded-reflex-ridge`、`actual-surface-right-angle`；公共法锥移除表面包装另有 37 failed |
| G6I-03 | `test_g6i03_cone_margin_rounds_exact_norm_not_nearest_point`，24 个次正规量值的有理平方/中点证书 | 实际返回改回 `norm(_float_vector(p))`；命中 `G6I-03 exact cone margin` |
| G6I-04 | `test_g6i04_margin_oracle_certifies_root_across_squared_range` 与 `near_parallel_oracle_display_preserves_small_gap` | 真实 `body_distance` / `margin_contacts` 的根构造换成提前舍入；修复后的独立 oracle 分别命中 `default-exact distance construction` / `default-exact cover distance`。此牙验证 oracle 能抓生产构造错误，不把 oracle 和生产共用几何原语 |
| G6I-05 | `test_g6i05_disconnected_inward_component_is_not_hidden_by_total_volume`，另有空腔奇偶、分量接触/相交及有效分离实体门 | `_component_orientation_issues` 换回只看总体积；命中 `disconnected-inward-component` |
| G6I-06 | `test_current_contracts_do_not_repeat_superseded_status` 的三个实际文件条目 | 向实际文件读得的文本植入各条旧说法，直接重跑同一文本检查；三格均命中 `G6I-06`，并非伪造几何输出 |

已读取日志摘要：二维定向 `1152 passed in 52.80s`；拓扑新门 `200 passed in 0.97s`；法锥组合门 `264 passed in 7.71s`；构造组合门 `241 passed in 3.21s`；文档门 `6 passed in 0.05s`。这些记录包含常驻内部变异测试的“预期红被捕获”结果；独立直接红日志仍保留。六条都能定位正向断言及缺陷穿透路径，没有以删除原门、缩格或 skip/xfail 代替修复。

## 4. 集成补扫与剩余审查边界

- 全套首轮发现显式窗口的距离曾从分别舍入后的全局见证点相减；现 `margin` 的最终距离改从对应精确平方量统一开方，原 cover-witness 自检继续测展示点误差，不掩盖坐标注入。原 68 个不变性失败已消除，原完整模块 `576 passed in 180.19s (0:03:00)`，旧自检牙六格仍绿。详见 [窗口距离小结](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_summary.md)。
- 统一构造的独立随机 Fraction 中点探针未找到数值反例；AST 门曾被六类 alias/dataflow 写法绕过，均已移交 root 并增加对抗 snippets。AST 扫描是指定语法和数据流看护，不是 Python 任意动态反射/运行时代码的形式证明，其最终绿以总报告为准。
- 收尾只读时仍见 `entrance.py:10` 旧句“取到最大值的 facet 就是首入 facet”和 `:55` 的“FF：两条边的起点”。前者遗漏新增有限域回映步骤；后者与当前真实重叠同点构造相矛盾。已向 root 提供精确一行替换，本子任务未改冻结源码；总报告应依据后续同步和复验记录关闭此文本残项。
- 输入 JSON 实际是 6 条，不把同根补扫虚增为另一组独立审查发现。本报告仅核上述调用链、具体反例及证据闭环；不代替下一轮独立六路 G6，也不宣称 M0 退出。

### 第三轮全套启动前补记

已只读确认 root 完成上述 `entrance.py:10` / `:55` 的一行文本同步：现在分别说明有限域精确复核、FF 真实重叠同点，原文本残项关闭；功能未由本子任务再次改动。第二轮全套另暴露 R8 旧普通 gap 变异格的数值区分力依赖已修复的距离误差；原输入、断言及 8 格变异网格完整保留，附加普通 binary64 中点格恢复实牙，单模块 18 passed、直接 8/8 变异命中目标断言、静态门 0 violation。详见 [补强台账](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/gap_gate_strengthening_summary.md)。第三轮冻结全套仍由 root 汇总，不以定向绿代替。

## 主执行者收尾订正

entrance 模块和 _facet_points 两处旧 docstring 已按建议同步，并由新文案门看护；README 路线已标历史，不再冒充现态。第二轮唯一失牙格保留原网格和断言，再加独立普通中点格，8/8 原变异均命中目标断言。

[最终主报告](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_report.md)。
