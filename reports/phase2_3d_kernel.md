# Phase 2：三维盖内核落地记录（2026-09-18）

按 07 号设计文档的 Phase 2，但按用户意见**直接上凹块**（互锁块），不从凸四面体起步——
凹几何才是这套理论独有的领土，而且它没有 legacy 可对，只能靠 G0 自证。

> **2026-09-24 订正说明。** 本文写于 09-18。09-21 的独立审查（`reports/audit_20260921.md`）推翻了其中几句，
> M0 修复后逐处订正。被推翻的原话没有删，用删除线保留，订正就写在原位，并注明依据的测试名；
> 读者可以看见判断是怎么变的。本文里凡是写着"订正/撤回（2026-09-24）"的地方，都以订正为准。
> 文中"审查 Cn"用 `reports/audit_20260921.json` 里 `confirmed[n]` 的编号（审查报告正文用的 C1/C2/M1… 是另一套编号，对照见该文末节）。

## 做成了什么

**几何层 `kernel3d/geom3.py`**：多面体（顶点表 + 面环，外看 CCW，允许非凸/非三角面）、
Newell 面法向、拓扑（棱、顶点-面、棱-面、**棱在各面里的遍历方向**）、二面转角、体积/体心、
**保证内点**、射线奇偶点在体内判定、线段穿面、暴力相交谓词、暴力特征距离、增量凸包。

> **订正（2026-09-24）**：当时"点是否落在面内"有两套写法——扇形三角化（点在面上、线段穿面、射线奇偶）和
> 半平面核（盖的 in_extent、面距离），**都只对凸面正确**（审查 C6/C7）。L 块顶底面、归并出的十边形侧面这类
> 凹面上会判错。现在五处（VF/FV 的 in_extent、`_point_face_distance`、点在体内的边界判定、射线奇偶、`segment_crosses_face`）
> 统一走 `geom3.face_polygon_locate` 这一个实现（投影到主轴平面 + 环绕数，返回 1/0/−1；`point_in_face_polygon` 是它的布尔包装，
> 即 `>= 0`）。有的调用点直接调 `face_polygon_locate`（射线奇偶、`segment_crosses_face`），有的经 `point_in_face_polygon`，底下是同一个函数。
> 由 `tests/test_geom3_face_polygon.py::test_all_five_call_sites_route_through_the_single_helper` 看着（它把 `face_polygon_locate`
> 换成恒答"外部"，五处必须全部跟着变）。

**盖层 `kernel3d/covers3.py`**：局部法锥判据（顶点用入射棱方向的线性不等式、棱用两相邻面法向
之间的球面弧）、三类 facet 盖（VF/FV/交叉 EE）、低维盖（VE3/EV3/VV3）、~~首入~~、
凸情形成员谓词（~~facet 间隙取 **max**~~）、局部 facet 集合、锥相交（Gordan 判据）。

> **撤回（2026-09-24）：三维首入零实现，列入里程碑 M2。** 这里把"首入"列为已交付是错的——
> `grep -rn "首入\|first_entrance" src/eab/kernel3d` 至今无结果（审查盲区 2）。首入是 DDA 真正消费的那条规则
> （集值点上由谁定接触点与法向），没有它，三维内核替换不了 DDA 的检测层。
>
> **订正（2026-09-24）：凸成员谓词不是"严格 facet 间隙取 max"。** 那样会把平行面、平行棱生成的退化 facet
> 整个丢掉：审查实测四面体 vs 方块在 +x 侧恒判"相交"，两个轴对齐方块对空集取 max 直接崩溃（审查 C5）。
> 现在的 `membership_convex3` 对 E = B ⊕ (−A) 的**全部支撑半空间**取 max——A、B 每个面法向各给一条
> （`support_gaps3`，含 FF/FE 退化 facet），再加严格交叉 EE 标签——**不要求一般位置**。
> 依据：`tests/test_covers3_membership.py` 的 `test_membership_tetra_vs_box_sweep_along_x`、
> `test_membership_axis_aligned_boxes_does_not_crash`、`test_membership_box_vs_box_matches_closed_form`、
> `test_support_gaps_are_supporting_half_spaces`。

**门 `kernel3d/g03.py`**：`g0_convex3` 三票（逐样本成员谓词 / 局部 facet 集合 / **E 顶点集 =
conv{b−a} 顶点集**）；`g0_distance_completeness3` 凹块距离完备性。

> **订正（2026-09-24）：写这句话时它是假的，现在属实，但含义要说准。** 09-18 的实现里票二只存了一个计数、
> 从不比较，`passed` 也不看它（审查 C23/C27：删掉任一严格 facet，190 次里 181 次仍 passed）；票三在退化输入上
> 也会误红（凸包三角网格顶点对极点：四面体/方块 19 对 13、方块/方块 26 对 8）。现在三票都参与 `passed`，含义是：
> - **票一**：逐样本，暴力相交谓词 vs `membership_convex3`，要求恒等；
> - **票二**：局部法锥规则给出的**严格** facet 标签（按定向法向）== 从 conv{b−a} 读出的 facet 集合
>   **减去 FF/FE 退化 facet**（退化 facet 按设计没有严格标签；用 A、B 各自支撑集的仿射维数判定）；
> - **票三**：局部锥相交规则判出的 E 顶点 == conv{b−a} 的**极点**（以前比的是凸包三角网格的全部顶点，
>   其中含落在 facet 内部或棱上的非极点，于是在退化输入上恒红）。
>
> 依据：`tests/test_covers3_g0_vote2.py`（六组随机对票二零差异；删任一严格 facet 190/190 必红；多塞一个假标签必红；
> 四面体/方块 严格 7 = 10 − 3 退化；方块/方块 严格 0、退化 6）、
> `tests/test_covers3_membership.py::test_g0_vote3_counts_only_extreme_points_on_degenerate_input`（E 顶点：四面体/方块 13、方块/方块 8）。

**互锁块生成器 `tools/osteomorphic.py`**：骨形块（顶底互补正弦起伏、分段平面近似），
参数化到可做界面几何灵敏度——这是 TIA 论文要的量。

## 门的结果

| 门 | 结果 |
|---|---|
| 流形/朝向自检（盒、四面体、互锁块四档） | 全过（面绕向错会静默污染所有盖的法向） |
| `g0_convex3` 六组随机凸多面体 | 逐样本零失配；票三 E 顶点集与凸包顶点集逐组相等 |
| 有牙测试：整体反号面法向 | G0 立刻报红 |
| 堆叠方块（bdda3d cb2 同构） | 恰 4 个 VF 盖、间隙 = 间距、法向 +z、`strict=False`（FF 退化，正确） |
| ↳ **订正（2026-09-24）** | 上一行只对**盖枚举**成立（`test_stacked_boxes_give_four_vf_covers_like_bdda3d_cb2`）。把它读成"G0 门覆盖了堆叠方块"是假的：当时 `g0_convex3(box, box)` 对空集取 max 直接崩溃（审查 C5）。现在由 `tests/test_covers3_membership.py::test_g0_convex3_box_vs_box_runs_and_passes`（200 样本零失配、三票全过）与 `::test_membership_box_vs_box_matches_closed_form`（三个尺度对闭式）看着 |
| 退化凸对（2026-09-24 补） | 四面体 vs 方块：200 样本零失配，E 有 10 个 facet（严格 7、FF 退化 3）、13 个顶点；方块 vs 方块：严格 0、退化 6、8 个顶点。`test_g0_convex3_tetra_vs_box_has_zero_mismatches`、`test_vote2_accounts_for_degenerate_facets_*`、`test_g0_vote3_counts_only_extreme_points_on_degenerate_input` |
| 楔-楔交叉 | 严格 EE 盖、间隙准确、两棱中点相碰（参数 0.5/0.5） |
| 互锁块凹性 | 16 条反射棱、体积恰 2.0（= lx·ly·lz）、内点可得 |
| 互锁性质 | 竖向抬 0.05 分离；侧向移 0.08/0.12/0.2 全部咬合锁死；沿无起伏方向不锁 |
| 抬起后法向间隙 | = 抬升 × cos(坡角)，误差 < 1e-9（不是抬升本身——面是斜的） |
| 凹块距离完备性（三种子） | 零失配，最坏绝对误差 < 1e-9 |

全仓 **146 个测试全绿**（09-18 当时）。

> **补注（2026-09-24）**：上表第二行的"六组随机凸多面体"全处于一般位置，没有任何平行面/平行棱，所以退化
> facet 的缺陷（成员谓词丢 facet、票二从不比较、票三数到非极点）在这里全都看不见——审查把这叫"参数化恰好避开
> 失败格子"。M0 之后同样六组上票二零差异（`test_vote2_local_facets_equal_hull_facets_on_random_pairs`），另补了
> 上面两个退化对。测试基线 8376ec2 全仓 1209 passed（`python -X utf8 -m pytest -q -p no:cacheprovider`，主树与新鲜克隆各跑一次；
> M0 合并后的 77600c9 时是 1174）；main 现为 094861c，它只改 `src/eab/limit.py` 第 41 行模块文档、直接进 main、未经独立复核，
> 在 094861c 上全套仍 1209 passed。以上订正都还没有经过 G6 独立重审。

## 四个被实测推翻的东西（都已修 + 钉定回归）

1. **二面角不能用"沿两外法向角平分线探测体内外"判凸凹。** 凸棱实体占小角、凹棱占大角，
   平分线两种情形都指向实体外，区分不了——L 块 16 条凹棱被全判成凸。正解：用**棱在面环里的
   遍历方向**定符号，`atan2((n1×n2)·t, n1·n2)`，不需要探测（也快得多）。
2. **暴力相交谓词会漏判**：两个方块共享 y、z 范围时，无顶点严格在对方内、无棱真穿面、两个
   内点也都不在对方里——但交集体积为正。补了 AABB 交集内的网格 + 伪随机证人搜索。
   **订正（2026-09-24）：这样补仍会漏。** 每个顶点都落在对方面平面上、又没有棱穿面内部时（L 块凹槽里咬进约
   0.05 的方块），网格采的是 AABB 交集而不是真交集，照样返回"相触"（审查 C9）。现在对每个"相触"顶点沿内法向
   微推做证人：`tests/test_geom3_overlap_witness.py::test_thin_notch_bite_is_detected`、`::test_audit_case_volume_is_0_012`。
3. **增量凸包的 `verts` 是顶点集的超集**：先入的极点在后续加点后可能变成内点，我从不移除。
   实测 43 vs 真实 31，直接让 G0 票三误红。修：构造完只保留被面引用的顶点并重编号。
4. **`min` 不是凹块的成员谓词**（我自己误用过一次，被钉定测试抓住）。VF 盖的 gap 是顶点到
   面**所在平面**的有符号距离；分离的两块之间常有顶点落在对方某面平面内侧，故 min 会报出
   −2.7 这类假侵入。凸块的成员谓词是 facet 间隙取 **max**（**订正 2026-09-24**：max 必须取遍 E 的全部支撑
   半空间、含退化 facet，只对严格 facet 取会错，见上文"盖层"处）；凹块的 E 非凸，max 与 min 都
   不成立——**凹块的全局成员判定需要入口块的全局构造，这正是 Phase 3 的目标**。凹块当下
   能测且该测的是**距离完备性**：法锥筛选不丢最近特征对。

## 诚实边界

- 退化盖（FF 平行贴面、FE、平行 EE）目前只标为 `strict=False` 并原样返回，**未做合并**。
  轴对齐堆叠方块的 4 个 VF 盖就是这种情形——DDA/bdda3d 正是用这 4 个 n-p 入口表达面-面接触，
  所以下游可用；但"把退化族合并成一个 FF 盖"还没写。
  **补充（2026-09-24）**：一维盖 VE3/EV3 处于边界态（分离方向恰在法锥边界）时同样原样返回、`strict=False`
  （此前被写死成 True，审查 C10）。平行棱-棱（EEP）的最近对**只**由边界态 VE3/EV3 表达（`ee_cover` 对平行棱返回
  None），所以 `enumerate_covers3` 对任何一类盖都**不按 strict 过滤**——一过滤，距离完备性就丢。
  依据：`tests/test_covers3_strict_lowdim.py` 的 `test_parallel_edge_edge_nearest_pair_ve3_is_boundary_state`、
  `..._ev3_is_boundary_state`、`test_distance_completeness_does_not_depend_on_strict`、`test_stacked_boxes_corner_over_edge_is_not_strict`。
  另：凸成员谓词 `membership_convex3` **不再需要一般位置**（用全部支撑半空间，见上文"盖层"处的订正）；
  但"盖清单只有四类"这条分类本身仍只在一般位置下成立（审查盲区 4 引用正本 01 精细版命题 4；本次未对照正本核实），退化族合并列入里程碑 M2。
- 凹块只有**距离完备性**与近接触盖枚举，没有全局 E 构造。
- 尚未对接 tf.cpp 探针（G2）与 bdda3d 的 cb2 夹具比对——下一步。（**补注 2026-09-24**：bdda3d 一侧已于 09-20
  对接，见 `reports/g2_three_dimensional.md`；tf.cpp 一侧仍因夹具不带顶点坐标而阻塞。）
- 性能未优化（纯 Python，O(V·F + E²) 全对枚举）。互锁块一对 72 个盖约十几毫秒量级，够做研究算例，不够做工程规模。

## 下一步

1. **G2**：把 3DDA 的 `retry_contact_pair_probe.tsv` 与 bdda3d 的 cb2 夹具接进来做集合同构比对
   （注意探针是抽样非全量，比较对象须限定同一筛选子集——见 `docs/sibling_observations.md`）。
2. 退化盖合并（FF/FE/平行 EE），把面-面接触收成一个盖。（**2026-09-24**：与三维首入一起列入里程碑 M2，至今未做。）
3. TIA 方向的第一枪：互锁块界面几何 → 承载力的灵敏度，需要接可微层（Phase 4）。
