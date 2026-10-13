# 正本 ↔ 代码映射表（2026-09-24，M0 文档收尾）

> **WO-R15FIX 当前补充（2026-10-13，待独立复审）**：静态工具仍是辅助检查，不是安全保证；局部 AST／源码 pin 与 Fraction 数据流合同不变。[显示与完整构造合同](r15fix_design_sync.md) 订正 R14 的 JSON 词法预拒收及未标记向上 infinity；合力、骨形 jet、贯入证书与 profile 精确差分由新增 R15 门看护。逐条红绿/变异及原门保留情况见 [报告](../reports/codex/R15FIX_report.md)。外部设计正本只读未回写，M0/M4a 管理边界不变。

> **WO-R13FIX / R12FIXb 当前合同（2026-10-13，待独立复审）**：静态构造工具与子集准入是辅助代码检查，不是安全保证；主保证改为公开构造量对独立有理参考的运行时极端尺度差分。现行例外仅锁局部 AST 站点和最小封闭源码 SHA-256，不再锁全库依赖；已知 int/Fraction 变量可按数据流准入，不限整数字面量。本轮补类字段生命周期传播和返回事件端点绑定；覆盖范围、未补齐项与有限网格限制见 [R13FIX 设计同步](r13fix_design_sync.md)、[API 清单](r13fix_construction_inventory.md) 及 [报告](../reports/codex/R13FIX_report.md)。M0 所有者退出决定不变，不宣称新鲜 worktree 或独立 G6 已通过，M4a 离线合同与门保留。

> **WO-R14FIX 当前补充（2026-10-13）**：[分项数值合同及数学订正](r14fix_design_sync.md) 优先于下文笼统 D400 描述。μ、角度/指数、文本连续量与整数身份分别检查；圆锥/黏聚方向独立精确认证。README 的一般相对余弦承载界已撤回，固定 μ=.2 数值门不升级成一般定理。完整执行与改写账见 [报告](../reports/codex/R14FIX_report.md)；M0/M4a 管理边界不变，仍待独立复审。

> **WO-R11FIX（2026-10-12，工作树修复，待独立复审）**：输入实际为 G6K-K01、K02 两条 major；本轮修复与全部验证证据以 [R11FIX 报告](../reports/codex/R11FIX_report.md) 与 [本树设计同步](r11fix_design_sync.md) 为准。静态构造门合流 callable/绑定/舍入来源；数值谓词不得把任意精确输入的转换误差忽略。M0 已按所有者决定退出，独立正确性复审并行继续；本单不变更该决定、不宣称独立 G6 通过、不回写外部只读正本，保留 M4a 门。

> **WO-R10FIX（2026-10-12，未提交、待独立 G6）**：G6J-J01～J05 的修复、同类扫描及验证见 [R10FIX 报告](../reports/codex/R10FIX_report.md) 与 [设计同步](r10fix_design_sync.md)。本树结果不构成 M0 退出；外部设计正本保持只读。

> **WO-R9FIX（2026-10-12，工作树未提交、待独立 G6）**：处置 G6I-01～06：二维共线链首入先核有限源特征域；实体凸性/凹棱及公共法锥按声明三角拓扑；壳方向按嵌套分量核验；精确到浮点统一构造并有独立中点证书与 AST 门。源单盖描述符仍是独立窄域，不等于折面实体完整法锥。设计同步见 `docs/r9fix_design_sync.md`；红绿/变异/全套见 `reports/codex/R9FIX_report.md`。本单未新建 worktree，不是独立六路 G6，不宣称 M0 退出。


> **WO-R8FIX（2026-10-12，修复留树，待独立 G6）**：本轮 G6H 确认 6 条 major；逐条红绿、内部变异、旧门对照、同类扫描和全套实测见 [R8FIX 报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_report.md)。当前合同补充见 [R8FIX 设计同步](file:///D:/eab-wt/cx-e2/docs/r8fix_design_sync.md)。本树同步不等于只读外部正本已回写；M0 退出状态不升级。

> **WO-R6FIX（2026-10-12，修复留树，待独立复核）**：第六轮确认 12 条（1 critical / 7 major / 4 minor），原审查见 [G6F 输入](file:///D:/eab-wt/cx-e2/reports/codex/inputs/G6F_report.md)。修复、修前红/修后绿、内部变异、同类扫描和完整测试结果统一见 [R6FIX 报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_report.md)。本次本树测试不等于独立六路 G6，且按工单禁止创建 worktree；M0 退出状态不升级。


> **E5 已完成（窗口为局部贯入厚度口径，WO-PERF 所有者定稿）**：保留兼容参数名 `contact_window`；它不是整体最短分离平移的欧氏贯入深度 PD 阈值。贯入相触报告只承诺“六轴非贯入证书 ⇒ rho ≤ w”或“星核薄壳证书 ⇒ 每个重叠区位于径向厚度 ≤ w 的壳内”。这里 `rho = inf{||d||₂ : int(A+d)∩int(B)=∅}`；正本 01 的 `PD_closed = inf{||d||₂ : (A+d)∩B=∅}` 是闭集完全分离的下确界，两者对一般闭表面不相同，六轴不保证 PD_closed≤w；报贯入也不推出 PD_closed>w。六轴及 L1 壳构造依赖坐标系，斜向短脱离可能漏，不保证旋转不变性。默认精确路径不使用该政策。闭合空腔反例门 `test_r7fix_docs.py::test_g6g09_tight_closed_cavity_distinguishes_rho_from_pd_closed` 固定两种口径；其他独立 oracle、限制反例与内部突变门见 [窗口门](file:///D:/eab-wt/cx-e2/tests/test_perf_contact_window.py)，定稿与性能证据见 [WO-PERF 报告](file:///D:/eab-wt/cx-e2/reports/codex/PERF_report.md)。此“已完成”指工单契约项，不冒充未经执行的独立六路 G6。


> **WO-E5b（2026-10-12，工作树实现，未经 G6）**：默认按给定数据精确判定，`contact_window=None` 不含隐式 ctol；显式窗口是调用方的局部贯入厚度报告政策（非 PD）。精确运动事件与证明读取 `exact_height` / `exact_offset`（互锁）和 `exact_t` / `surface_label`（首入），不能将浮点显示高度再逐顶点舍入后当作同一证书。当前验收、窗口数学定义、全部原格迁移与残余限制以 [E5b 报告](file:///D:/eab-wt/cx-e2/reports/codex/E5b_report.md) 和 [三维设计](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md) 的 E5b 节为准。下文 E5a/E5a2 退出段是历史记录，不是 E5b 当前结果。


这份表补的是 2026-09-21 审查的**盲区 4**："没有人拿正本逐条对过代码"。正本三份，全部只读：

- `D:\E(A, B)\01 E(A,B) 理论内核·精细版.md`（下称 **01**）——命题 1–8；
- `D:\E(A, B)\03 广义接触·裕度即接触与理论内核的去岩石化.md`（下称 **03**）——膨胀恒等式、KKT、C^{1,1} 正则化、五件套 K1–K5；
- `D:\E(A, B)\00 石根华 E(A,B)·理论内核与向外发展分析.md`（下称 **00**）——谱系与三层诚实分类（§4.6）；
- `D:\E(A, B)\07 程序设计·统一接触内核方案.md`（下称 **07**）——设计正本：五层架构、ContactRecord 契约、G0–G5 门体系、Phase 0–5（2026-10-10 第四轮盲区 3 之后补入，见第八节）。

**状态更新（2026-10-10，G6 第五轮之后）**：本表的代码指针一律写成"`file.py:当前定义行 函数名`"，无名的行号 / 区间指针已全部改写（模块文档里的段落按节名指，不写行号），并由 `tests/test_doc_pointers.py` 逐条核"行号 = 该函数当前的定义行"——改代码挪了定义行，门就红在那个指针上，用 `tools/fix_canon_ptrs.py --apply` 重排。此前三次人工校正（第三轮后 34 处、第四轮又 13 处）都在之后的提交里再次过期（第五轮实核 40 处带名指针 29 处不在该行），这是建门的原因；下段"HEAD 094861c / 1209 passed / 尚未经过 G6"是 09-24 写表时的口径，此后 G6 第二轮（09-27，`reports/g6b_20260927.md`）与第三轮（10-10，`reports/g6c_20261010.md`）都读过本表；K4 行与附录 A.9 的 LP 契约数字按 HEAD 复跑订正（见各处 2026-10-10 注）。上述是截至第三轮的历史缺口；第四、第五轮已读取正本并逐条处置 GAP3，详见下段。内容映射的处置不等于剩余实现缺口已补齐，也不升级本轮 M0/G6 退出状态。

代码口径：`D:\eab-kernel` main，HEAD `094861c`。数字先在 `8376ec2` 上跑出；其后 `094861c` 只改 `src/eab/limit.py` 模块文档一行（诚实条款改指 `test_failure_mode_is_read_off_invariants_of_the_dual_face`），全套仍 `1209 passed`（`python -X utf8 -m pytest -q -p no:cacheprovider`，主工作树与新鲜克隆各跑一遍）。表里每一个"有门"都在 `094861c` 上跑过，命令见第八节。

**本表自身的状态**：本文件与本批 M0 收尾文档**一起提交**（HEAD `094861c` 上尚不存在）；它此后经过 G6 第二至第五轮的独立重审（第四轮 provenance-canon 镜头打开过 01、03 全文与 00 多节，第五轮核过第八节"07 对代码"），GAP3（正本对代码）已按各轮报告逐条处置（`reports/g6d_20261010.md`、`reports/g6e_20261010.md`）。按 README 的规矩，本表里任何比现有 README/报告更强的说法，都要等 G6 之后才能升级到那些文件里。

**E2 口径更新（2026-10-11，WO-E2）**：下文二维凸路径按本工作树的精确实现订正；只记录实现与定向门，不把历史 G6 覆盖移植到新代码上。全套结果、突变体和遗留问题见 `reports/codex/E2_report.md`。凹首入、已侵入后的局部最浅盖与局部单盖在 E3 补精确化，极限自校验在 E4 改有理数；新门、10 项源码突变和全套结果见 `reports/codex/E3E4_report.md`。不等于独立 G6 或新鲜 worktree 验证。

## 先说结论

1. **凸情形的核心命题 1、3(i)、4、5、6(i)、6(iii) 已实现且有门**，而且门的 oracle 大多不经被测代码（暴力相交谓词、显式 conv{b−a}、纸笔闭式）；
   **2(i)（位置无关）已实现且有门**：`test_kernel3d_covers.py::test_proposition_2i_position_independence` 带两条变异牙
   （m2-geom 68c311b；此外 `test_invariance_geom.py` 在平移下覆盖 `local_facets3`）；**2(ii) 间接有门**。
   （2026-09-27 订正：原文把 2 也算进"都已实现且有门"，与本文件自己的表矛盾；G6 minor 21 当时用变异确认"让 `local_facets3`
   在 A 沿 x 平移超过 3 时丢一个标签，全套照绿"——那是 68c311b 之前的状态，在现 HEAD 上同一变异让 2(i) 门与不变性门共 106 条红。
   2026-10-10 再订正：上一次订正把状态说低了。）
2. **命题 4 的"一般位置"前提，代码的处理方式是"不另起退化类型"**：平行贴面、棱平行于面、平行棱-棱都用**非严格**的普通盖来表达，凸成员谓词改用 E 的全部支撑半空间（不再依赖一般位置）。成员、距离、票二、票三在退化输入上都有门。**把一个退化族收成一个盖只做了一半**：三维首入的 `entrance3.merge_degenerate`（M2 第一版）把同一法向、同一平面上的并列盖收成 `("FF", …)` / `("FE", …)` **标签元组**并保留展开成员；但 `Cover3.kind` 注释里的 `FF` / `FE` / `EEP` 与 `contact_record.CoverType` 里的 `FF` / `FE` / `EE_PAR` 仍没有任何构造点（`enumerate_covers3` 不产出、`CoverType.FF/FE/EE_PAR` 全仓零引用），`EEP` 连标签也没有；二维 `FF` 只在凸全局构造 `convex_entrance_block` 里出现（`covers.py:364 convex_entrance_block`（段内）），局部枚举不产出。
3. **首入（命题 7）**：二维旧静态 `first_entrance_for_vertex` 对凹块分离时选错边，只保留作参考；二维、三维自 2026-10-10 起均有按运动方向定义的第一版（`kernel2d/entrance.py:140 first_entrance`、`entrance3.py:230 first_entrance3`，有门、未经独立重审，M2）。E2 的二维凸路径进一步精确化选路、初态与 E 的半空间射线裁剪（`test_kernel2d_convex_ray_exact.py`）；E3 凹对用局部盖 + 精确相交裁决，候选仿射根、各自时刻段内和前事件漏候选自检均用 Fraction；已侵入按精确平方距离选局部最浅盖（不等于一般凹对全局最小分离）。并列只取精确同时，接近项另报。bb52 的 53 条 legacy 窗口盖验证保留，精确初态为侵入的格子改核局部出口。门 `test_kernel2d_entrance_e3.py` 与原 bb52 门。
4. **穿透深度（命题 3(ii)）、碰撞锥（命题 8）没有实现。**
5. **`margin.py` 的"定理一到四"是本仓库自己编的号**，正本里没有这四个编号。但内容上一、二、四在正本都有出处（03 §1.1、01 命题 3(i)、03 §1.3 与 01 命题 6）；定理三的后半句（KKT 乘子 = 虚拟接触力）是 03 §1.2 的主张，代码没实现。真正属于本仓库的只有 Lipschitz 常数 2/δ 这个定量推论，而代码里给的一句理由不够，推导补在第三节。这一条与审查盲区 4（GAP3）"在 03 里没有对应""自创的定理"的说法相反，第三节开头是对审查的订正。
6. **"局部盖不构成凹块的全局判据"这条实测结论，和正本对石根华机器"一般凹 + 可证完备"的定位有张力**：局部盖对凹块只做到"∂E 被盖住"（有门），做不到"盖就是 ∂E"——本表复核时构造了一个严格有效、间隙为 0 的盖恰好落在 int E 里的例子。缺的是 00 §3.3 提到、正本自己标着"未核实"的那一步：**盖之间的裁剪**。01 开头说"凹块情形单独说明"，全文其实没有这段说明。

**状态用语**：
- **已实现+有门**：有函数，有以该性质命名的测试，本 HEAD 上通过；
- **已实现无门**：代码依赖或实现了它，但没有独立的测试看着；
- **部分**：只在部分前提下实现或只有部分门；
- **未实现**；
- **不一致**：代码与正本的说法对不上，写明哪里。

**编号说明**：01 的引言说"本文十二条命题"，正文只编到命题 8；`docs/plan_20260921.md` 说"01 精细版命题 1–12"，也是照引言写的。本表按正文编号，把带 (i)(ii)(iii) 的命题拆成子行，子行怎么拆是本表自己的做法，不是正本的。

---

## 一、01 精细版逐条

文件路径省略前缀：二维在 `src/eab/kernel2d/`，三维在 `src/eab/kernel3d/`，`margin.py`、`limit.py` 在 `src/eab/`。

| 命题 | 一句话 | 前提 | 实现 | 看护的测试 | 状态 |
|---|---|---|---|---|---|
| **1** 定义 | E(A,B) = a₀ + B⊕(−A)，正好是"平移后与 B 相交"的全部平移 | 任意紧集；a₀ 任取 | 二维凸：`covers.py:364 convex_entrance_block` 接精确 `kernel2d/exact.py::entrance_block_exact`（Fraction 极角归并，精确平行同向才并 FF，顶点最后转为浮点输出）；三维凸：`g03.py:125 g0_convex3`（段内）先有理化再构造差点，以精确锥交核对极点集；`margin.py:578 entrance_block_convex` 先有理化输入再作 b−a，保存精确差点后构造凸包（E5b）；门 `test_margin_exact.py::test_entrance_block_forms_differences_before_any_float_rounding` | `test_kernel2d_g0.py::test_g0_random_convex_pairs`、`::test_entrance_block_area_is_minkowski_area`、`test_kernel2d_exact.py::test_exact_parallel_edges_merge_into_ff_and_nothing_else_does`、`test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip`、`test_kernel3d_covers.py::test_g0_convex3_random_pairs`、`::test_g0_gate_has_teeth_flipped_normals_are_caught` | 凸：**已实现+有门**；E2 新路径待 G6。凹：**未实现**（没有全局 E，M3） |
| **1·注3** 三分判据 | a₀ 在 E 外=分离，在内部=重叠，在边界=恰好接触 | 同上 | `covers.py:441 membership_convex`（E2：tol=0 的分类与平移加法精确，非精确凸输入走 `polygons_overlap_exact`）、`covers3.py:861 membership_convex3`，都返回 −1/1/0 | 二维 `test_kernel2d_exact.py::test_exact_membership_equals_exact_separating_axis_oracle`、`::test_exact_membership_boundary_is_not_the_interior`、`::test_membership_nonexact_convex_input_uses_the_simple_polygon_path`；显式报告带 `test_kernel2d_report_band.py`。三维 `test_covers3_membership.py::test_membership_tetra_vs_box_sweep_along_x`、`::test_membership_box_vs_box_matches_closed_form`、`::test_membership_tetra_vs_offcenter_box_matches_closed_form` | 凸：**已实现+有门**。二维 G0 不再跳边界带；二维 tol>0 仅为无舍入地板的报告带，凸带为完整欧氏边界距离、非凸带为有精确四轴见证的保守子集。非凸一般相交回退已有门，但**盖裁剪/全局 E 成员判据仍未实现**（M3）。E5a 三维 G0 同样零跳样，边界探针包含全部 E 顶点/棱中点/面重心；E5a2 三维显式正 tol 改为到完整 E 边界的欧氏距离带，外角/外棱不能仅用支撑平面距离判带内（`test_e5a2_covers.py::test_membership_report_band_is_euclidean`） |
| **2(i)** 位置无关 | E 只依赖形状与朝向，可以预计算 | 只平移、不转动 | 结构上成立：法锥判据只读方向；`facet_gap`/`facet_gap3` 对平移是仿射的；`g0_convex3` 只算一次 `local_facets3` 给全部样本用（`g03.py:58 _hull_facets`（段内）） | `test_kernel3d_covers.py::test_proposition_2i_position_independence`（+ `::test_position_independence_gate_has_teeth_*` 两条牙）、`test_invariance_geom.py::test_cover_labels_and_strictness_are_invariant` | **已实现+有门**（附录 A.3 的一次性复核已升格为门） |
| **2(ii)** 凸性传递 | A、B 凸 ⟹ E 凸 | A、B 凸 | 作为前提被使用：二维凸成员由精确 facet 半空间符号判定，不再对浮点 gap 取符号；三维仍是支撑半空间路径 | 间接：票一（成员谓词 vs 独立相交 oracle 逐样本一致） | **已实现，间接有门** |
| **2(iii)** 紧性 | 紧+紧 ⟹ E 紧 | 块体有界 | 不需要实现（输入都是有界多面体） | — | 不适用 |
| **3(i)** 距离恒等式 | a₀ 到 E 的距离 = 两块的距离 | 无条件 | 凸：`margin.py:603 distance_to_convex_entrance`（显式 E）对 `margin.py:430 body_distance`（盖路径）；这正是 `margin.py` 的"定理二" | `test_margin.py::test_config_space_distance_equals_body_distance`（3 个种子，每种子分离样本 > 40）、牙 `::test_theorem_two_gate_has_teeth_shrinking_the_nearest_point_is_caught` | 凸：**已实现+有门**。凹：没有显式 E，恒等式本身量不了；能量的是"盖给的距离 = 暴力距离"（距离完备性，见第六节） |
| **3(ii)** 穿透深度 | 重叠时，最小分离平移 = a₀ 到 ∂E 的距离 | a₀ ∈ int E | 无。裕度层贯入时只回答"已违约"、不给深度（`margin.py` 模块文档「口径与边界」第二条）；二维出口完备性量的是**沿给定方向**的出口，不是最短出口 | — | **未实现** |
| **4** ∂E 的面结构 | 一般位置下，facet 只来自 顶点×面、面×顶点、交叉棱×棱；棱来自 顶点×棱；顶点来自 顶点×顶点 | **一般位置**（无平行面、无棱平行于面）；必须用法锥**相对内部** | 三维：`covers3.py:487 vf_cover`、`:503 fv_cover`、`:547 ee_cover`、`:592 ve3_cover`、`:611 ev3_cover`、`:623 vv3_cover`、`:678 enumerate_covers3`、`:724 local_facets3`；二维：`covers.py:470 local_facets`（E2 精确法锥）与精确 Minkowski 边归并 | 二维 `test_kernel2d_g0.py::test_g0_random_convex_pairs`（一般位置下局部严格 facet 集 = 全局 facet 集 = \|A\|+\|B\|）；退化输入由 `test_kernel2d_exact.py::test_g0_flat_chains_use_exact_support_sets_without_ambiguity_exemptions` 核对严格/边界支撑集。三维 `test_covers3_g0_vote2.py`、`test_kernel3d_covers.py::test_facet_count_matches_minkowski_theory_for_boxes`、`::test_crossing_edge_edge_cover`、`::test_wedge_on_wedge_gives_strict_crossing_edge_cover`；票三 `test_covers3_membership.py::test_g0_vote3_counts_only_extreme_points_on_degenerate_input` | 一般位置：**已实现+有门**。退化：**部分**，见第四节 (a)。二维表述**与正本不一致但无害**：正本说二维"顶-顶拆成两个 v-e 判定"，代码另有一个 `VV` 盖（E 的顶点），距离完备性的角对角情形靠它（`test_distance_completeness_has_teeth` 丢 VV 必红） |
| **4·退化** | 平行贴面、棱平行于面各给一个 facet，平行棱-棱给一条棱，要"另行处理" | 一般位置之外 | 见第四节 (a) | 见第四节 (a) | **部分**：正确性有门；退化族未合并成一个盖（M2） |
| **5** 有效入口 = 法锥条件 | 严格分离 ⟺ 法锥相对内部相交 ⟺ 该盖是 ∂E 的极大 facet；非严格 ⟺ 闭法锥相交 ⟺ 盖在 ∂E 上但可能是退化盖的一部分 | A、B 凸 | 二维凸：`kernel2d/exact.py::vertex_side_exact`；E3 局部单盖默认也用精确符号，`covers.py:114 normal_cone`、`:142 in_cone` 只接受调用方明示的域窗口，不抬噪声地板。三维 `covers3.py:262 vertex_cone_contains`、`:273 edge_arc_contains`、`:417 cone_relint_direction`（Gordan 判据）、`:439 cones_intersect_relint` | 二维 `test_kernel2d_exact.py::test_flat_vertex_cone_is_one_ray_not_a_line`、`::test_corner_cone_boundary_is_not_strict` 及票二；legacy 窗口 `test_kernel2d_review.py::test_r1_narrow_crevice_is_reflex_even_with_legacy_tolerance`、`test_bb52_g1.py::test_gate_has_teeth_strict_cone_loses_legacy_contacts`。三维 `test_kernel3d_covers.py::test_vertex_cone_of_box_corner`、`::test_edge_arc_of_box_edge`、`::test_tilted_vertex_face_cover_is_strict`、`test_covers3_strict_lowdim.py::test_stacked_boxes_corner_over_edge_is_not_strict`、`::test_generic_vertex_over_edge_is_strict` | 凸：**已实现+有门**。凹：局部单盖精确，显式域窗口只放宽（`test_kernel2d_covers_e3.py`）；正本只对凸陈述，"非严格 ⟺ 在 ∂E 上"对凹块**不成立**（第四节 (d)） |
| **6(i)** 外侧光滑 | E 外距离函数可微，梯度 = (x − P_E(x))/d，局部 C^{1,1} | E 闭凸 | `margin.py:609 inflated_normal`（凸，显式 E）；冻结路径对平移 x 的导数（`frozen.py:186 frozen_normal`、`:252 frozen_gap`） | `test_margin.py::test_inflated_normal_is_lipschitz`、牙 `::test_lipschitz_gate_has_teeth`（随机/常向量/径向/局部反号四种错误实现全抓）、`::test_lipschitz_gate_global_pairs_have_their_own_teeth`、`test_frozen_lowdim.py::test_low_dim_frozen_gradient_is_the_inflated_normal_of_the_explicit_entrance_block` | 凸：**已实现+有门** |
| **6(ii)** 内侧分片线性 | 侵入深度是有限个仿射函数的 min，在脊集上梯度跳 | a₀ ∈ int E，E 凸 | 无（依赖 3(ii)）。**类比**：L5 逃逸高度 h(δ) 也是"有限个盖的零间隙高度里取一个"的分片线性函数，拐点在并列切换处；`tools/tia_sensitivity.py:93 sensitivity_at` 在那里标 `differentiable=False`。方向固定为竖直，不是侵入深度，只是同类结构 | 类比部分：`test_interlock_sensitivity.py::test_phase_derivative_at_phase_zero_is_flagged_on_every_default_row`、`::test_differentiability_flag_agrees_with_one_sided_quotients` | **未实现**（正本意义下）；同类拐点在 L5 已被检测 |
| **6(iii)** 边界集值 | ∂E 上法向在 facet 内唯一，在棱、顶点处集值 | E 凸 | 盖带维数标签（`VV`/`VV3` 零维、`VE3`/`EV3` 一维）；重合时法向给 `None`（`covers.py:240 vv_cover` vv_cover、`covers3.py:623 vv3_cover`（段内）） | `test_margin.py::test_inflation_turns_a_set_valued_normal_into_a_single_valued_one`（同一 E 顶点、两个法向；膨胀后单值且 \|n₁−n₂\| = \|x₁−x₂\|/δ 精确） | 凸：**已实现+有门** |
| **7** 首入 | a₀ 首次触及 ∂E 的点定接触点与法向；已侵入取最短出口；是集值点上的确定性裁决 | 要有运动（"首次"） | 二维 `entrance.py:140 first_entrance`：E2 凸选路、初态与射线裁剪精确，浮点 gap 只作输出；E3 凹首入和已侵入后的 `shortest_exit` 采用精确有理数选择；后者只是局部最浅盖。旧静态 `covers.py:336 first_entrance_for_vertex` 仅作参考。三维 `entrance3.py:230 first_entrance3` + `shortest_exit3` + `merge_degenerate`（FF / FE 退化族，`members` 保留展开视图；M2 第一版） | 二维 `test_kernel2d_convex_ray_exact.py::test_convex_ray_time_matches_independent_fraction_sat`、`::test_convex_ray_decisions_do_not_use_constructed_facet_gaps`、`::test_corner_start_reports_both_exact_active_facets`；既有 `test_kernel2d_entrance.py` 含凹台阶、刚体运动、bb52 53 条 legacy v-e 对账。三维 `test_entrance3.py`、`test_entrance3_concave.py`、`test_entrance3_g2.py` | **二维、三维均有门·未经新一轮 G6**。二维 E3 精确门为 `test_kernel2d_entrance_e3.py`，brute 共用相交谓词仅作佐证，主 oracle 是闭式与测试内联 Fraction SAT；已知"凹 B + 分离选远边"指旧静态函数，不指新版运动首入（第四节 (b)） |
| **8** 碰撞锥 / 速度障碍 | CC = 从 a₀ 看 E 的正锥；VO 是它平移到 v_B；推论：盖分解经中心投影给碰撞锥一个"首撞模态"分划 | 匀速相对运动 | 无。沿射线找首个 ∂E 点的计算只以两种特例存在：二维 `g0.py:254 brute_ray_exit`（oracle，不带盖标签）；三维 `interlock.py:212 escape_candidates` / `:271 escape_height_covers`（方向固定 +z，带盖标签） | — | **未实现** |

---

## 二、03 去岩石化逐条

| 03 的内容 | 一句话 | 实现 | 看护的测试 | 状态 |
|---|---|---|---|---|
| **§1.1 膨胀恒等式** | E(A⊕B_δ, B) = E(A,B) ⊕ B_δ：给车加安全距离 = 给入口块做 δ 外平行体 | = `margin.py` 定理一（`margin.py` 模块文档「定理一」）。代码**直接拿它当定义**：`inflated_membership`（`margin.py:528 boundary_band`（段内））比较 `body_distance` 与 δ，从没造过 A⊕B_δ 或 E⊕B_δ 来对照 | `test_margin.py::test_inflated_membership_tracks_the_margin` 查的是推论（违约 ⟺ 落进 E_δ），它和实现用的是同一个 `body_distance`，不独立 | **已实现无（独立）门**。独立检验要造 A⊕B_δ（不是多面体），没做 |
| **§1.1 末句 / §1.2 前半** 裕度耗尽 = 广义接触闭合 | margin_gap = d − δ ≤ 0 即闭合 | `margin.py:475 margin_contacts`；贯入时返回已闭合的哨兵（`margin.py:130 effective_geom_tol`（段内）） | `test_margin.py::test_margin_contacts_are_generalized_contacts`、`test_margin_penetration.py` 全部 3 个函数 | **已实现+有门** |
| **§1.2 后半** KKT 乘子 = 虚拟接触力 | 把"不穿透"换成"不穿透裕度包络"，乘子就是虚拟接触力 | 无。`margin_contacts` 的结果没有接进任何互补/LP 求解；`limit.py` 只吃 `contacts_from_covers` 的物理接触 | — | **未实现**（审查盲区 6 同样指出） |
| **§1.2** DDA 开闭迭代 = 互补问题的活动集方法 | 一句可以认领的论断 | 没有形式化。相关的只有 G4 统计实验（`tools/g4_multistep.py`），03 砖一已据此关掉静态几何先验 | `test_g4_multistep.py`（钉数） | **未实现**（论断本身）；03 砖一的 09-18 回写段仍是 82/39/60 的旧口径，09-27 的订正（5/61）只在本仓库（正本只读，未回写） |
| **§1.3 C^{1,1} 正则化** | 球膨胀后边界 C^{1,1}、法向处处唯一，接触不确定性消失 | = `margin.py` 定理四；同 01 命题 6(i)(iii) 两行 | 同 01 命题 6(i)、6(iii) 两行 | 凸：**已实现+有门**。"Moreau–Yosida 式"的说法没有门，只是表述 |
| **K1** 配对约化 | 两形状的相互作用 → 一点相对 E 的位置 | 成员谓词、盖枚举 | 同命题 1 | 凸：已实现+有门；凹：只有盖枚举 |
| **K2** 边界语义化 | ∂E 分成有限个带模态标签的盖，每盖给点、法向、进入量 | `Cover`/`Cover3`（标签、`point_a`/`point_b`、`normal`、`gap`） | 同命题 4、5 | **已实现+有门**（凸完备；凹只到"∂E 被覆盖"） |
| **K3** 首入裁决 | 集值点上"谁先被进入"做确定性选择 | 同命题 7 | 同命题 7（二维、三维：并列集按枚举序裁决、如实报 `tied_labels`） | **二维、三维第一版有门·未经 G6** |
| **K4** 互补结构 | 约束激活 ⟺ 乘子非零 | L3 极限分析：下限 LP（静力容许）+ 对偶机构，`limit.py:552 limit_load`、`:857 check_duality`（E4：含黏聚耗散的静力、强对偶、互补均用有理数精确核；多体见 `limit_multi.py::check_duality_multi`，门 `test_limit_exact_selfcheck.py`、`test_limit_selfcheck.py`、`test_limit_multi.py`；浮点尺度仅作报告/输入可分辨性筛查，风险由 resolvability/statuses 另报、不改变原问题精确 status/alpha） | `test_limit.py`、`test_limit_duality.py`、`test_end_to_end_cb2.py`（`b26d7f5`，`8376ec2` 返修；均未经独立复核）、`test_lp_fail_loud.py`（"要么答对、要么抛 RuntimeError、绝不静默给错"；`8376ec2`；G6 第二轮 lp-limit 镜头与第三轮 claims-vs-code 镜头读过；HEAD 上 A.9 的 32 格全部答出、0 格抛错，见 A.9 的 2026-10-10 复跑） | **部分**：只有极限状态的互补，没有开闭迭代/活动集求解 |
| **K5** 有限覆盖 + 不等式代数 | 连续几何 → 有限可枚举组合代数 | 有限枚举：是（`enumerate_covers`/`enumerate_covers3` 是有限对的循环）。"角的代数"：无 | 同命题 4 | **部分** |
| **砖一** 几何引导活动集 | 盖胞腔结构作为活动集切换的先验 | G4 实验，03 已写入"静态版关闭" | `test_g4_multistep.py` | 已有否定性结果（不是实现） |
| **砖二** 首入控制 | 让首次接触落在指定盖上 | 依赖命题 7、8；命题 7 首入已有二维/三维 API 与门，命题 8 及完整首入控制仍未实现 | — | **未实现** |
| **砖三** 规则几何化 / **2×2 判据** | 方法论，不是代码 | — | — | 不适用 |

---

## 三、`margin.py` 的"定理一到四"对正本（回答 (c)）

**结论**：这四个编号是本仓库起的（`margin.py` 模块文档「定理一」至「定理四」、`reports/margin_layer.md:8-45`），正本里没有"定理一…四"。

**订正审查盲区 4（GAP3，2026-09-24）**：审查的原话是 `margin.py` 的"定理一..四" "have no counterpart in 03 (03 contains no 定理 at all, only one paragraph on C^{1,1})"（`reports/audit_20260921.json` 的 `gaps[3]`），`reports/audit_20260921.md` 盲区 4 称之为"自创的'定理'"。本表的结论与此**相反**：括号里前一分句字面成立（03 不给定理编号）；后一分句不成立——03 除 §1.3 C^{1,1} 一节外，另有 §1.1 膨胀恒等式与 §1.2 虚拟接触力 = KKT 乘子两节；"在 03 里没有对应"也不成立——**定理一 = 03 §1.1**（连名字都一样），**定理四 = 03 §1.3**（另有 01 命题 6），定理二 = 01 命题 3(i)。自创的只有编号本身和定理四的常数 2/δ。审查报告原文不改，以本段为订正；本段本身尚未经 G6 复核。

| 代码编号 | 内容 | 正本出处 | 性质 | 证明写在哪 | 门 |
|---|---|---|---|---|---|
| 定理一 | 膨胀恒等式 | 03 §1.1（连名字都一样） | 标准结果（Minkowski 和结合 + 球对称） | 03 §1.1；`margin.py` 模块文档「定理一」 同一条三步推导 | 无独立门（见上表） |
| 定理二 | 构型空间距离 = 工作空间距离 | **01 命题 3(i)**（正本在命题 3 标题上标"标准"；(i) 是一行等式链）；03 没写 | 标准 | 01 命题 3(i)；`margin.py` 模块文档「定理二」 一行 | `test_config_space_distance_equals_body_distance` + 牙 |
| 定理三 | margin_gap ≤ 0 即广义接触闭合；其 KKT 乘子 = 虚拟接触力 | 前半 03 §1.1 末句；后半 03 §1.2 | 前半是定义；后半是 03 的跨界主张（Signorini/KKT 对应），03 用文献核对论证，没有数学证明 | 无 | 前半有门；**后半无实现无门** |
| 定理四 | 膨胀法向单值、C^{1,1}；Lipschitz 常数 ≤ 2/δ | 单值与 C^{1,1}：03 §1.3、01 命题 6(i)(iii)。**常数 2/δ 正本没有** | 前半标准；**2/δ 是本仓库的定量推论** | `margin.py` 模块文档「定理四」 只有一句"凸集投影是非扩张映射"——这句不够，见下 | 双边门：上界 ≤ 2/δ，紧性下界 ≥ 0.9/δ |

**2/δ 的推导（本表补，未入门）**：记 u = x − P(x)，v = y − P(y)，\|u\|, \|v\| ≥ δ。要用的不是"P 非扩张"，而是"**I − P 也非扩张**"（凸集投影是坚定非扩张（firmly nonexpansive）的，因此 I − P 也非扩张），于是 \|u − v\| ≤ \|x − y\|。再用单位化不等式：不妨 \|u\| ≥ \|v\|，\|u/\|u\| − v/\|v\|\| ≤ \|u − v\|/\|u\| + \|\|v\| − \|u\|\|/\|u\| ≤ 2\|u − v\|/\|u\|。合起来 \|n(x) − n(y)\| ≤ 2\|x − y\|/δ。只用"P 非扩张"会得到 \|u − v\| ≤ 2\|x − y\|，常数变成 4/δ。

**实测**：δ = 0.25 时，局部差商与闭环上的最坏商 3.99999（= 1/δ，E 顶点处是紧的），66 个全局点对的最坏商 1.233，都在 2/δ = 8 之内（`test_inflated_normal_is_lipschitz` 断言这些界；数值由附录 A.5 的命令打印）。也就是说 2/δ 是一个**松**的上界，真实常数在这组探针上是 1/δ。

---

## 四、四个必须回答的问题

### (a) 命题 4 的"一般位置"前提：代码怎么处理退化

正本说一般位置之外的情形"另行处理"。代码的做法是**不另起类型**：退化接触由"非严格"的普通盖表达，需要全局判断的地方（成员谓词、票二、票三）改成不依赖一般位置的写法。逐项如下。

**二维**

- **二维凸包（E3）**：`kernel2d/geom.py::convex_hull` 接 `exact.hull_exact`，默认与显式 tol 均不丢真极点，tol 只保留签名兼容，不隐式简化；需简化的调用方应另行处理，不能以简化包作真值。门 `test_kernel2d_covers_e3.py::test_convex_hull_keeps_true_extreme_point_not_transitive_tolerance_pop`，第五轮 geom.py:434 的原构型与修前红断言见工单报告。
- **平行边（FF）**：E2 全局凸构造只把**精确平行同向**的两条边合并为 `FF`（`covers.py:364 convex_entrance_block` 接 `kernel2d/exact.py::entrance_block_exact`）。旧“方向可行窗”及链法向已删除；`facet_gap`/首入输出法向取 facet 自己那条边，间隙不参与凸成员或凸首入命中/时刻分支。局部单盖枚举仍不产出 FF；E3 保留明示 legacy 域窗口，不再抬到舍入地板（附录 A.4）。票二不能仅从全局集合删 FF：一边有平直分段、另一边没有时，剩余非 FF 也可能是边界支持分段，须按独立精确支撑集分类（`g0.py:149 g0_convex`）。
  门：`test_kernel2d_exact.py::test_exact_parallel_edges_merge_into_ff_and_nothing_else_does`、`::test_g0_flat_chains_use_exact_support_sets_without_ambiguity_exemptions`、`test_kernel2d_report_band.py::test_tiny_report_tol_never_uses_rounded_facet_gap`、`test_kernel2d_convex_ray_exact.py::test_convex_ray_decisions_do_not_use_constructed_facet_gaps`。
- **平直顶点**（转角精确为 0）：凸输入允许，精确法锥是单射线且须核同向，不是整条直线；E 的共线分段不作为严格凸顶点（`test_kernel2d_exact.py::test_flat_vertex_cone_is_one_ray_not_a_line`、`::test_strict_vertices_discard_flat_chain_subdivision_vertices`）。E3 局部 VV 对给定坐标精确判锥交与严格活跃，精确平直点不产 VV；舍入成真小角时按真实数据判，门见 `test_kernel2d_covers_e3.py` 及改写后的 `test_r3_numerically_collinear_vertex_yields_no_vv`。
- **非精确凸输入**（含微凹）：全局凸构造不再按“凸包深度 ≤ tol”夹平，任何精确反射均拒收；平直顶点经刚体舍入变成微凹也如实拒收，成员与首入选路改走非凸回退。折回、绕圈与零长边同样清晰报错。门：`test_kernel2d_exact.py::test_rounded_flat_vertex_is_refused_by_the_convex_path`、`::test_convexity_rejection_names_the_first_foldback_and_winding_defect`、`::test_first_entrance_routes_rounded_reflex_input_away_from_the_convex_path`。旧名 `test_kernel2d_review.py::test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start` 已改写为 2·tol、0.5·tol 两侧微凹都拒收，不再看护已删除的凸包深度函数。
- **二维 G0 三票**：票一精确成员对独立精确 SAT，随机及边界探针全计分；票二用独立全顶点投影核对严格/边界法锥集与全局构造，不设 ambiguous 豁免；票三用内联 Fraction 凸包对 E 的严格凸顶点，不计共线点、不设“说不清”带。独立性门 `test_kernel2d_exact.py::test_sat_oracle_uses_no_kernel_geometry_primitive`、`::test_g0_support_and_hull_oracles_use_no_tested_geometry_primitive`；旧 `test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip` 名称保留，缺陷注入已移入精确成员判定内部。
- **零长边**（连续重复顶点）：清晰报错（`covers.py:114 normal_cone`（段内））。门：`test_c19_zero_length_edge_is_a_clear_error_not_zerodivision`。
- **分界点**（分离方向恰在两锥公共边界上）：`test_distance_completeness_boundary_cases[vertex_vertex_on_cone_edge]`、`test_exit_completeness_boundary_cases[E_corner_VV]`。

**三维**

**E5a 口径（2026-10-12，所有者已在 WO-E5a2 澄清系统临时目录允许使用，按部分完成提交为 `5b09ea3`；未经 G6）**：显式凸 API 取顶点集的精确凸包，源 faces 只是来源提示。精确凸视图会拆开舍入后非共面的面，标签映射记录在 `source_vertices` / `source_faces`；一般 `vf_cover` 等单盖仍使用源面标签和精确 Newell 面向量，不是任意折面实体的完整法锥。凸定理不可直接外推到这一一般接口。设计与遗漏见 `docs/exact_3d_design.md`、`reports/codex/E5a_report.md`。

- **精确三票，不再是两把带宽尺**：票一独立原输入 SAT，全部随机与 E 顶点/棱中点/面重心计分；票二独立差点凸包按精确支撑集核全部标签；票三局部精确锥交与极点集一致。`ambiguous` 等兼容计数字段只能为零，不能成为通过理由。门 `test_g03_e5a.py` 含边界错票、错凸化、漏标签和极小真棱；oracle `g03_exact.py` 不调用被测几何原语。
- **原语迁移边界**：`exact_point_in_polyhedron` / `exact_segment_crosses_face` / `exact_triangle_intersection` 已有独立门；E5a2 的旧一般 `polyhedra_overlap` / `point_in_polyhedron` / `segment_crosses_face` 已接精确三角表面路径，限有效朝外闭合嵌入表面；一般重叠的平面分区/共面内部有理见证由 `test_e5a2_surface.py` 看护，源码删除共面支路的突变命中目标断言。`_seg_seg_distance` 近平行分支改用精确耦合参数（`test_geom3_e5a.py`）；此前 E5a2 外层只做必要兼容；E5b 后继精确化、实际三角标签与证明范围见本文件开头更新。

- **成员谓词——这就是审查 C5 的来源**（审查报告正文叫 critical C2，`audit_20260921.json` 的 `confirmed[5]`，M0 修复记录记为 C5）。旧 `membership_convex3` 只对严格 facet 取最大间隙；平行面、棱平行于面生成的 facet 都是非严格的，被整个丢掉。后果两个：四面体对单位方块沿 +x 平移，t ≥ 1 全判"相交"（误判）；两个轴对齐方块的严格 facet 集为空，对空集取 max **崩溃**。
  E5a：`membership_convex3(tol=0)` 对 canonical convex view 的有理支撑平面取精确符号，绝不读取浮点 gap 作分支；`support_gaps3` 仅作构造输出。此前的构造说明：`support_gaps3`（`covers3.py:850 support_gaps3`）对 A、B 的**每个**面法向取支撑半空间（A 的面外法向 m 对应 E 的 facet 法向 −m，支撑顶点取 argmin_B m·b），再加交叉 EE 标签，取最大值（`covers3.py:850 support_gaps3`（段内））。**不要求一般位置**。
  门：`test_covers3_membership.py` 全部——四面体扫描含 t = 1.0 与 t = −2.0 两个恰相触的分界点（正确答案是 0，不是"分离"）、偏心非均匀方块、×1e-3/×1e3、`test_membership_axis_aligned_boxes_does_not_crash`、`test_g0_convex3_box_vs_box_runs_and_passes`。
- **平行贴面（FF）与棱平行于面（FE）**：不单独成盖，表现为一组非严格的 VF/FV/EE。本表复核：两个等大方块面贴面，窗口 1e-9 内是 **4 个 VF + 4 个 FV + 8 个 EE，全部非严格**（附录 A.2）；bdda3d cb2 那种小块压大块，面内只剩 4 个非严格 VF（`test_stacked_boxes_give_four_vf_covers_like_bdda3d_cb2`）。
  `Cover3.kind` 的注释（`covers3.py:231 Cover3`（段内））和 `contact_record.CoverType` 都列了 `FF` / `FE` / `EE_PAR`（或 `EEP`），但这几种**三维**类型在**枚举**里没有任何产出者（二维 `FF` 由凸全局构造产出，见上面二维第一条；三维 `FF` / `FE` 只以标签元组出现在首入的退化合并里，`Cover3` / `CoverType` 的这几个值零构造）：本表复核，四面体/方块、方块/方块、叠放方块三组各 40 次随机平移，枚举出的类型只有 VF、FV、EE、VE3、EV3、VV3（附录 A.2）。
- **票二、票三的退化记账**：票二按支撑集的仿射维数把 (1,2)、(2,1)、(2,2) 记作退化 facet（`g03.py:58 _hull_facets`（段内）、`:92 facet_vote3`（段内））；票三只数 conv{b−a} 的**极点**，不数三角网格里落在面内/棱上的点（`g03.py:125 g0_convex3`（段内，票三））。门：`test_vote2_accounts_for_degenerate_facets_tetra_box`、`_box_box`（6 个 facet 全退化，严格集为空，照样通过）、`test_g0_vote3_counts_only_extreme_points_on_degenerate_input`（四面体/方块 E 恰 13 个顶点）。
- **平行棱-棱（EEP）**：`ee_cover` 对平行棱返回 None（`covers3.py:547 ee_cover`（段内））；它们的最近对只由**边界态（非严格）的 VE3/EV3** 承载。门：`test_parallel_edge_edge_nearest_pair_ve3_is_boundary_state`、`..._ev3_is_boundary_state`。
- **低维盖的 strict**：审查前 `ve3_cover`/`ev3_cover` 把 strict 写死为 True（C10）；现在按两个锥判据如实算（`covers3.py:592 ve3_cover`（段内）、`:611 ev3_cover`（段内））。同时**枚举不按 strict 过滤任何盖**（`covers3.py:678 enumerate_covers3`（段内））：若过滤，平行棱-棱的最近对就丢了，裕度层距离完备性会红。门：`test_distance_completeness_does_not_depend_on_strict`、`test_generic_vertex_over_edge_is_strict`、`test_stacked_boxes_corner_over_edge_is_not_strict`。
  顺带一处命名不一致（不影响结果）：三维 `VV3` 的 `strict` 恒为 True（只有两锥相对内部相交时才产出），"是否活跃"放在 `in_extent`（`covers3.py:623 vv3_cover`（段内））；二维 `VV` 却把"是否活跃"放在 `strict` 字段（`covers.py:240 vv_cover`（段内）、`:240 vv_cover`（段内））。
- **三角化输入的平面棱**：`edge_arc_contains` 仅对精确平直棱返回 −1（不按噪声压平微二面角）（`covers3.py:273 edge_arc_contains` `edge_arc_contains`），所以三角化的共面面要先 `merge_coplanar`（`geom3.py:1145 merge_coplanar`）。归并只并**共棱连通且精确共面**的面，非共面源面不能误并；带洞或 pinch 的区域抛 ValueError，不死循环。门：`test_geom3_merge.py` 全部。

**还没做的**：把一个退化族（例如一整块面贴面）收成**一个**带面片几何的盖，同时保留"展开成 4 个 VF"的视图给 DDA——这是 M2。与此相关，G2 对 bdda3d 只对账 np ↔ VF/FV（窗口 1e-6）；ee 入口或窗内的非 VF/FV 盖会让门**红**，而不是被对账（`test_g2_gate_red_on_fabricated_ee_legacy_entrance`、`test_g2_gate_red_on_extra_kernel_ee_cover`）；带内的牙从 `6f157ac` 起穿过枚举器（`test_g2_band_catches_a_real_kernel_defect_through_enumeration`，在内核里注入"顶点法锥恒返回边界"的缺陷，要求门红）。注意这颗牙的来历：g4 组合并（`b1bbd27`）时 C17 第二轮复核的结论是 NO_TEETH，`6f157ac` 才补上；而 `6f157ac` 是合并后直接进 main 的，**没有经过独立验证者复核**，要等 G6。

### (b) 首入（命题 7）

- **二维现行运动首入**：`entrance.py:140 first_entrance`。E2 凸路径在 Fraction 上裁剪半空间射线：微小非零斜率不夹平，错过 E 或超过 t_max 不由 tol 放行；初始恰相触时 t=0，角点全部精确活动 facet 报入并列集。门 `test_kernel2d_convex_ray_exact.py`。E3 的 tied_labels 仅含精确同时/同距，near_labels 另作可分辨性报告，不反馈选择；输出法向/间隙/接触点仍为浮点构造。凹首入、最浅局部出口与 brute 已精确化（`test_kernel2d_entrance_e3.py`）；brute 有扫描分辨率限制且与生产共用精确相交，不能冒充独立 oracle。
- **二维旧静态实现**：`covers.py:336 first_entrance_for_vertex`。对 A 的一个顶点，在 B 的“投影落在边内的有效 VE 盖”里取间隙最大的一个；没有就退到活跃 VV。它不接收运动方向，库内没有调用者，只有测试用它。以下错误说明针对这个参考函数。
- **什么情况下对**：B 凸时，单个顶点已侵入，"最大间隙"就是这个顶点到 B 边界的最短出口——与正本"已侵入取最短出口"在**单个顶点**的意义下一致（不是整个块对的穿透深度）。门只有一条：`test_first_entrance_picks_shallowest_penetration`（凸 B、已侵入、一个例子）。
- **凹块分离情形：错**。docstring 自己写着（审查 r8，`covers.py:336 first_entrance_for_vertex` 的 docstring）。本表复核复现（附录 A.1）：细臂 L 块凹槽里放一个三角形顶点 (0.5, 0.3)，两块分离；边内有效 VE 盖有两个——到水平内边间隙 0.2、到竖直内边间隙 0.4。函数选了 **0.4 那条远边**，而最近的正间隙是 0.2。没有门看着这个错误（它是已知错误，不是回归）。
- **三维：2026-10-10 起有第一版**（`src/eab/kernel3d/entrance3.py`，M2：沿运动方向的首入、最短出口、FF/FE 退化族合并；凹体上靠谓词裁决、局部规则到不了的位形抛错不静默）。此前零实现：三维里唯一"沿一个方向找第一个 ∂E 点"的计算是 L5 的逃逸高度（`interlock.py:212 escape_candidates`、`:271 escape_height_covers`），方向固定为 +z，而且是"离开"不是"进入"。
- 三维首入 M2 第一版已落地（有门、未经 G6）；在独立重审之前 README 只记"有门·未经复核"，不打 ✔。

### (c) `margin.py` 的"定理一到四"

见第三节。一句话：编号是本仓库的；一、二、四的内容在正本有出处；三的后半（KKT = 虚拟接触力）是 03 的主张、代码没实现；四的常数 2/δ 是本仓库加的，代码里的一句理由不够，需要"I − P 非扩张"，推导补在第三节，实测紧值是 1/δ。

### (d) "局部盖不构成凹块全局判据"与正本的张力

**实测结论**（都有门）：

- 局部法锥有效的盖，对凹块做到了"∂E 被盖住"：分离侧**距离完备性**、相交侧**出口完备性**都成立。bb52 真几何 1260 次平移里分离 603 次、距离完备性 603/603（误差 0），相交 657 次、出口完备性 657/657（`test_bb52_g1.py::test_g0_distance_completeness_real_concave_geometry`、`::test_g0_exit_completeness_real_concave_geometry`）；随机星形凹多边形 × 三个尺度、凹互锁块也都过（`test_kernel2d_g0.py::test_distance_completeness_general_position_concave`、`::test_exit_completeness_general_position_concave`、`test_interlocking.py::test_g0_distance_completeness_on_concave_interlocking_pair`）。
- 但**从局部盖读不出成员判定**：分离的凹互锁块之间有间隙 < −2.0 的有效盖（`test_interlocking.py::test_min_cover_gap_is_not_a_membership_rule_for_concave_bodies`）；二维"最小间隙的符号"两个方向都错——细臂 L 块 16/16 误报相交（`test_kernel2d_review.py::test_gap0_sign_of_min_gap_is_not_a_concave_membership_rule`），槽角楔块漏报相交（`::test_gap0_sign_of_min_gap_false_negative_wedge_in_channel`）。
- 更直接的一例（本表复核，附录 A.6，**没有入门**）：U 形槽（槽宽 1）里放一个宽 1.5 的菱形，让菱形下角恰好落在槽底边中点。此时有一个**严格**有效的 VE 盖，间隙 0、投影参数 0.5；而暴力谓词判两块**相交**。也就是说，这块盖在这个位置上不在 ∂E 上，而在 int E 里——它本该被槽壁"裁掉"。

**与正本的张力**：

1. **01 命题 5**："非严格 ⟺ 闭法锥相交 ⟺ 该盖落在 ∂E 上"。这句话正本只对凸块陈述，对凹块不成立（上面那一例连严格盖都不在 ∂E 上）。01 引言写着"凹块情形单独说明"，**全文没有这段说明**。
2. **01 归属总表与 03 §3**把石根华机器的独特处定为"一般凹多面体 + 显式边界几何 + **可证完备**的有限盖系统 + 力学可用"。代码的证据只支持弱意义的完备（∂E ⊆ 有效盖的并），不支持强意义（盖就是 ∂E，所以能拿它判 a₀ 的位置）。两者之间差的正是 **00 §3.3 记下的"盖之间要相互裁剪，只有暴露出来的部分参与接触检测"**——正本在那里标着"这个裁剪在原文里对应哪条命题，未核实"。实测说明裁剪不是可有可无的实现细节，而是凹块成员判定缺的那一步（M3）。
3. **`covers3.py` 模块文档**说"Phase 3 的凹块可以沿用同一实现——反射顶点/凹棱的局部锥为空，自动被排除"（`covers3.py` 模块文档第一段）。对**枚举**成立，对**成员判定**不成立。
4. 00 §3.3 转述 Zhao 2020 的工程流程"构造（局部）入口块 → 判 a₀ 位置"。如果那个流程是把局部入口块直接当凹块的成员判据，就与本仓库的实测冲突；原文没读到，**待核**。

---

## 五、"正本有、代码无"

1. **命题 3(ii) 穿透深度**，以及依赖它的 **6(ii)** 内侧分片线性结构。裕度层贯入时只给哨兵，不给深度。
2. **命题 7 首入**：二维与三维的 M2 第一版（按运动方向定义，2026-10-10）待独立重审；二维旧静态版对凹块分离情形的错已被新版绕开（新版凹对靠谓词裁决）；EEP 退化族没有自己的合并规则（由 VF/FV 边界态表达）。
3. **命题 8 碰撞锥 / 速度障碍 / 截断 VO**，以及"盖分解经中心投影成为碰撞锥分划"的推论。
4. **命题 4 退化族作为一个盖**：三维 `FF`/`FE` 只在首入的退化合并里以标签元组产出（`entrance3.merge_degenerate`），枚举不产出；`EEP`（及 `CoverType` 的 `EE_PAR`）有类型名、无产出者；二维 `FF` 只由凸全局构造产出，局部枚举不产出（M2）。
5. **凹块的全局 E、基于盖裁剪的成员判据、盖裁剪**（01 引言承诺的"凹块情形单独说明"、00 §3.3 的裁剪；M3）。二维已有一般多边形精确相交回退与闭式门，不等于这些全局结构已实现。
6. **03 §1.2 KKT 乘子 = 虚拟接触力**：裕度接触没有接进任何互补/LP 求解。
7. **"DDA 开闭迭代 = 活动集方法"的形式化**：只有 G4 的统计实验。
8. **K5 的"角的代数"**（01 归属表自己也标"正文未读，细节未核实"）。
9. **03 砖二（首入控制）**：依赖 7、8。

## 六、"代码有、正本无"

1. **距离完备性 / 出口完备性**："∂E ⊆ 有效盖平移线段之并"的两面。它是本仓库在凹块上**唯一有门的 ∂E 命题**，正本没有。证明草稿在 `g0.py:254 brute_ray_exit`（段内）（出口完备性 docstring）与 `g0.py:215 g0_distance_completeness`（段内）（`brute_ray_exit` 的依据）；三维距离完备性在 `g03.py:191 g0_distance_completeness3`。门见第四节 (d)。
2. **G0 三票的自证结构**（票一逐样本、票二局部 facet 集 vs 凸包 facet 集、票三 E 顶点 vs conv{b−a} 极点）：是检验方法，不是正本命题。
3. **定理四的常数 2/δ**（第三节）。
4. **贯入哨兵口径**：03 §1.1 说"三分判据、距离恒等式、首入准则全部原样继承"；代码在贯入时不继承距离（贯入时盖的见证距离是一个像深度的正数，不是 0），而是统一回答"已违约"（`margin.py` 模块文档「口径与边界」第二条，门 `test_margin_penetration.py`）。这是对正本的**必要限定**，不是矛盾。
5. **冻结盖可微层**（`frozen.py`、`dual.py`）：00 §6.2 有"片 + 划"的说法，01/03 没有对应命题。低维盖（VE3/EV3/VV3）的冻结法向随平移 x 转动。门：`test_frozen_lowdim.py` 全部。
6. **L3 极限分析**（`limit.py:552 limit_load`、`:857 check_duality`）：下限 LP + 对偶机构 + 含黏聚耗散的强对偶。正本 K4 只到"互补结构"，没有极限分析。端到端门 `test_end_to_end_cb2.py`（`b26d7f5`）把 bdda3d 夹具 → 盖 → 接触 → 极限分析接起来，对纸笔闭式：滑动 μW、轴向倾覆 W、对角倾覆 √2·W，含 μ = 1 与 μ = √2 两个分界（对角推门自 `8376ec2` 起把 μ = √2 本身列为一格，此前只用 1.3/1.5 夹住）、几何 ×1e-3/×1e3 与荷载 ×1e-2…×1e4、三种接触点侧。LP 层另有 `test_lp_fail_loud.py`（`8376ec2` 新增）钉住"要么答对、要么抛 RuntimeError、绝不静默给错"的契约（lp_tol None/1e-9/1e-12/1e-14 × 荷载/几何尺度 × k = 5/16；显式传 1e-12/1e-14 时 32 格中 6 格抛 RuntimeError（含黏聚 ×1e4 与一个未放大的块），契约允许；默认容差与 1e-9 下 16 格全部答出——这一点是本表逐格枚举所见，门本身只强制审查那一格（×1e4、k = 16）在默认容差下必须答出，即 `test_default_tolerance_answers_the_audited_case`；枚举脚本见附录 A.9）。**订正（2026-10-10）**：HEAD 上 A.9 实跑 raises 0 / answered 32——M0.2 把 LP 改成"对给定数据精确"之后，紧容差下不再抛错；"32 格中 6 格抛 RuntimeError"是 094861c 口径（G6 第三轮 minor）。
   **来历**：`b26d7f5`（端到端门）、`6f157ac`（C17 补牙）、`8376ec2`（端到端门返修与 `test_lp_fail_loud.py`）和 `094861c`（`limit.py` 模块文档的诚实条款跟改：门改指对偶面不变量测试，"是否转动"不再列为一般不变量）都是合并后直接进 main 的，**没有经过独立验证者复核**，要等 G6；本段引用的对偶面不变量测试、μ = √2 格与 `test_lp_fail_loud.py` 都来自 `8376ec2`。写它和复核它时的两个发现：
   - **对偶机构不唯一，"滑动无转动"不是不变量**：八边形内接锥下，推力恰落在锥棱上时，切向速度可以在 ±π/k 内任取（μ = 0.4、0.95 时求解器返回的偏角是 −22.5°，承载力精确）；而且对偶最优面里还有**带转动**的机构——力矩反号变异下求解器在 μ = 0.4 返回 (1, 0, 0.4, 0.117157, 0, −0.292893)，拿测试里的独立核算 `_power` 在**未变异**的原问题上验：最差接触功率 −1.1e-16、驱动 1、上限 4.0 = α（W = 10），即它同样容许、同样最优（μ = 0.95 同理，上限 9.5 = α）。所以 `b26d7f5` 里 `test_failure_mode_is_read_off_the_dual_mechanism` 滑动格的"无转动"断言依赖单纯形挑哪个顶点，是脆的。`8376ec2` 删掉了它，换成 `test_failure_mode_is_read_off_invariants_of_the_dual_face`：用**不调用 `eab.limit.wrench`** 的独立刚体虚功率核算（测试内的 `_power`），断言返回机构是最优对偶；滑动时"平动 + 关联剪胀"T = (1,0,μ,0,0,0) 也是最优对偶；倾覆时断言 R = (0,0,1,0,1,0)（绕前缘转动）是最优对偶、T 的上限 > α，且返回机构必须带转动（|ω| > 1e-6）；μ = 1 断言两者并列。"任何纯平动上限 ≥ μW > α，所以'带转动'只在倾覆时是真不变量"是测试 docstring 的纸笔论证（a = 3π/2 那条锥棱给出 v_z ≥ μ·v_x），测试只核算了 T 这一个平动。
   - **中心对称会藏缺陷**：cb2 四个接触点关于原点中心对称，"接触列力矩反号""接触列忘减参考点"两种缺陷在原点取中心时看不见——力矩反号在原点只是把列重排（本表复核：μ = 0.4、1.5 两例，变异前后 32 列排序后完全相同、顺序不同，即同一个 LP）。加了参考点不变性门 `test_capacity_is_independent_of_the_moment_reference_point`。本表复核（附录 A.7，只改 LP 内部的接触列、荷载不动），在 `8376ec2` 上：两种变异都是**只有**该门红（4/6 格，原点取 (0,0,0) 的 2 格照绿，符合预期），本文件其余测试全绿。在 `b26d7f5` 上力矩反号还会多红 2 格——`test_failure_mode_is_read_off_the_dual_mechanism[0.4-False]` 与 `[0.95-False]`，两格都是**滑动格**，挂在上面那条脆的"无转动"断言上。这 2 格是**门的脆性暴露**，不是牙：变异后求解器返回的是原 LP 的另一个最优对偶顶点，不是抓到了缺陷。这也说明 `b26d7f5` 提交说明里"力矩反号变异下其余测试全绿"是错的（提交说明已推送、不改，以 `8376ec2` 的提交说明与本段为订正）。
7. **L5 逃逸高度剖面与剪胀比**（`interlock.py`）：正本 04/06 的应用方向，01/03 无命题。它是 ∂E 沿竖直线的上边界，和命题 8 的"沿射线首触点"同构，但方向固定。门：`test_interlock_escape.py`、`test_interlock_sensitivity.py`。

## 七、对照 00 §4.6 三层诚实分类

- **第一层（重新发现）**：E 本身、距离恒等式、二维 NFP 构造。代码把它们当标准结果实现（显式 conv{b−a}、定理二），这是对的；文档里不应把它们写成本仓库或石根华的贡献。
- **第二层（可能新，须用对参照系）**：
  - 第 1 条"带语义、可证完备的盖系统"：本仓库给出的是**弱完备**的门（第四节 (d)），强完备（凹块成员判定）缺裁剪，不能主张。
  - 第 2 条"与开闭迭代衔接"：G4 已给出否定性数据（静态几何先验只抓到 61 个真翻转里的 5 个（09-27 按 df22 终判订正，原 5/82），03 砖一的 09-18 回写段仍是 82/39/60 的旧口径，订正只在本仓库 `reports/g4_multistep_first_datum.md`；正本只读、未回写），不能主张盖系统能预测活动集。
  - 第 4 条"接触不确定性的消解"= 首入：二维、三维自 2026-10-10 各有按运动方向定义的第一版（`kernel2d/entrance.py`、`kernel3d/entrance3.py`，有门、未经独立重审；三维 EEP 无合并规则、凹体靠谓词裁决），不能主张完整。
- **第三层（红线）**：扫了 README、AGENTS、reports、docs 里的优先性措辞。`AGENTS.md:3` 在 HEAD 上原写"石根华入口块 E(A,B) 理论的**第一份实现**"——00 §3.3 引的 Zhao et al. 2020 就是更早的实现，所以这句不成立。本批已改为"一份独立实现"，订正见 `AGENTS.md:5-7`。R7FIX 也撤掉姊妹对账通道的序数性宣传，仅表述为独立对账通道。

## 八、怎么复核这张表

**测试**（本表所有"有门"都在这里面）：

```bash
cd D:/eab-kernel
python -X utf8 -m pytest -q -p no:cacheprovider   tests/test_kernel2d_g0.py tests/test_kernel2d_review.py tests/test_bb52_g1.py   tests/test_kernel3d_covers.py tests/test_covers3_membership.py tests/test_covers3_g0_vote2.py   tests/test_covers3_strict_lowdim.py tests/test_geom3_merge.py tests/test_kernel3d_geom.py   tests/test_interlocking.py tests/test_margin.py tests/test_margin_penetration.py tests/test_frozen_lowdim.py   tests/test_interlock_sensitivity.py tests/test_interlock_escape.py   tests/test_limit.py tests/test_limit_duality.py tests/test_end_to_end_cb2.py tests/test_lp_fail_loud.py   tests/test_g2_bdda3d.py tests/test_g4_multistep.py
```

2026-09-24 先在 `8376ec2` 上跑出、再在 `094861c`（只改 `limit.py` 模块文档一行）上复跑，结果相同：上面这条命令（21 个文件）`682 passed`；只跑本表**逐个点名**的 59 个测试函数（nodeid 清单见附录 A.8，按函数取全部参数格；正文里只以整文件引用的，如"`test_covers3_g0_vote2.py` 全部 5 条""`test_margin_penetration.py` 全部 3 个函数""`test_geom3_merge.py` 全部"，不在清单里）是 `203 passed`；全套 `1209 passed`。这三个数在 `8376ec2` 的主工作树和新鲜克隆（`git clone --no-hardlinks`，继承系统级 `core.autocrlf=true`）里各跑了一遍；在 `094861c` 上，三个数在主工作树复跑，`1209`、`203` 两个数又在一份新鲜克隆里复跑，结果都相同。

**基线纪律**：`cc5d7cf` 之前，10 个 Phase 0 夹具在入库时被 autocrlf 规范成 LF，而溯源哈希记的是 CRLF 原件——GitHub 克隆下来，溯源门自己是红的；六路审查都在主工作树里跑，所以没发现。从那以后的规矩是**新鲜 worktree 的基线必须全绿**，所以本表的数字也在新鲜克隆里复跑过（见上）。顺带订正（2026-09-24）：`cc5d7cf` 的提交说明称"3DDA 与 3-b-dda 仍继承系统 true"，对 3DDA 是错的——查的是 `C:\3DDA` 根下的空壳 `.git`，真仓库 `C:\3DDA\3d-DDA-work` 本地自 09-18 起已是 `false`；提交说明已推送、不改，细节见 `docs/sibling_observations.md`。

## 附录 A · 本表复核时用的一次性检查（未入门）

这些检查只用来核实正文里的说法，**不是门**；要长期看着，得另写测试。都在仓库根目录下用 `python -X utf8` 运行，先 `import sys; sys.path.insert(0, "src")`。

**A.1 二维首入在凹块分离时选远边**（第四节 (b)）

```python
from eab.kernel2d.covers import first_entrance_for_vertex
from eab.kernel2d.geom import translate, polygons_overlap
L = [(0,0),(3,0),(3,0.1),(0.1,0.1),(0.1,3),(0,3)]
A = translate([(0,0),(1,0.2),(0.2,1)], (0.5, 0.3))   # 顶点 0 在 L 的凹槽里
assert polygons_overlap(A, L, 1e-12) == -1            # 分离
fe = first_entrance_for_vertex(A, 0, L, window=10.0, tol=1e-12)
print(fe.b_index, fe.gap)    # 3 0.4（竖直内边）；最近的正间隙是水平内边的 0.2
```

**A.2 三维退化接触的盖种类**（第四节 (a)）：`enumerate_covers3(box(center=(0,0,1), half=(.5,.5,.5)), box(half=(.5,.5,.5)), window=1e-9, tol=1e-9)` 给 4 个 VF + 4 个 FV + 8 个 EE，`strict` 全为 False；四面体/方块、方块/方块、叠放方块各 40 次随机平移（`random.Random(0)`，平移分量 ∈ [−1.6, 1.6]；枚举参数与上一句**不同**：`window=float("inf")`、`tol=1e-9`、`require_in_extent=False`——窗口若仍取 1e-9，随机平移下几乎没有盖进窗，"没有 FF/FE/EEP"就平凡成立），出现的种类只有 VF 2400、FV 2440、EE 4920、VE3 142、EV3 142、VV3 14。四面体取 `tetra((0,0,0),(1,0,0),(0,1,0),(0,0,1))`，方块取 `box(half=(.5,.5,.5))`，叠放方块的上块取 `box(center=(0,0,1), half=(.5,.5,.5))`；三组共用一个 `Random(0)` 依次抽样。

**A.3 位置无关**（命题 2(i)）：四面体 (0,0,0),(1,0,0),(0,1,0),(0,0,1) 对半边长 0.5 的方块，20 次随机整体平移 t（分量 ∈ [−5, 5]）下 `local_facets3(T.translated(t), B)` 与 `local_facets3(T, B)` 相同（7 个 facet），且每个标签的 `facet_gap3` 在"先平移 t 再平移 x"与"直接平移 t+x"之间相差 < 1e-12。

**A.4 二维平行边**：`enumerate_covers(translate(SQ, (1.0, 0.3)), SQ, window=1e-9, tol=1e-12)`（SQ 为单位正方形）给非严格 VE 1 个、非严格 EV 1 个，没有 FF。

**A.5 Lipschitz 实测值**（第三节）：

```python
import sys; sys.path[:0] = ["src", "tests", "tools"]
import test_margin as T
from eab.margin import inflated_normal
print(T._lipschitz_verdict(inflated_normal, 0.25))   # ((3.99998..., 1.23299...), True)
```

**A.6 严格有效的盖落在 int E 里**（第四节 (d)）

```python
from eab.kernel2d.covers import enumerate_covers
from eab.kernel2d.geom import translate, polygons_overlap
U = [(0,0),(3,0),(3,2),(2,2),(2,1),(1,1),(1,2),(0,2)]        # 槽宽 1
A = translate([(0,-0.5),(0.75,0),(0,0.5),(-0.75,0)], (1.5, 1.5))  # 宽 1.5 的菱形，下角在槽底中点
print([(c.kind, c.b_index, c.gap, c.param, c.strict) for c in enumerate_covers(A, U, window=1e-12, tol=1e-12)])
# [('VE', 4, 0.0, 0.5, True)]
print(polygons_overlap(A, U, 1e-12))   # 1：两块相交
```

**A.7 端到端参考点门的牙**（第六节第 6 条）：在 pytest 收集完 `tests/test_end_to_end_cb2.py` 之后（测试模块手里的 `wrench` 仍是原件），把 `eab.limit.wrench` 换成变异版，只影响 LP 内部的接触列：

```python
import sys, pytest
sys.path.insert(0, "src")
import eab.limit as L
orig = L.wrench
def mut(force, point, origin, dim):             # 力矩反号；另一种变异是 return orig(force, point, (0.0,)*dim, dim)
    w = orig(force, point, origin, dim); return w[:dim] + [-v for v in w[dim:]]
class P:
    def pytest_collection_finish(self, session): L.wrench = mut
pytest.main(["-q", "-p", "no:cacheprovider", "-rf", "tests/test_end_to_end_cb2.py"], plugins=[P()])
```

- 在 `8376ec2` 上：力矩三个分量取反 → `4 failed, 111 passed`；忽略参考点（origin 恒按原点算）→ `4 failed, 111 passed`。两者红的都**只有** `test_capacity_is_independent_of_the_moment_reference_point` 的 4 个非原点格（`[0.3-origin1]`、`[0.3-origin2]`、`[1.5-origin1]`、`[1.5-origin2]`）。
- 在 `b26d7f5` 上（`git archive b26d7f5` 导出后同样跑）：力矩反号 → `6 failed, 107 passed`，多出的 2 格是 `test_failure_mode_is_read_off_the_dual_mechanism[0.4-False]`、`[0.95-False]`（滑动格，"无转动"断言）；忽略参考点 → `4 failed, 109 passed`。那 2 格记为**门的脆性发现**而非牙，理由见第六节第 6 条。
- 力矩反号在原点只是列重排：`eab.limit._build_columns(cts, (0,0,0), 3, 8)` 在变异前后给出同一组 32 列（排序后逐一相等、原顺序不等），μ = 0.4 与 1.5 都如此。
- 带转动的最优机构：在上面的力矩反号变异下调 `test_end_to_end_cb2._capacity(CASES[0], 0.4, (1.0, 0.0))` 取 `r.mechanism`，恢复 `L.wrench = orig` 后调 `test_end_to_end_cb2._power(r.mechanism, 0.4, W)`，得 `(-1.1e-16, 1.0, 3.9999999999999996)`；μ = 0.95 得上限 `9.5`。

**A.8 第八节"逐个点名的 59 个测试函数"的 nodeid 清单**：从本文抽出所有 `test_…` 函数名（含 `_box_box`、`..._ev3_is_boundary_state` 两处缩写），去掉整文件名与 `8376ec2` 上已删除的 `test_failure_mode_is_read_off_the_dual_mechanism`，按函数定义所在文件组成 nodeid。把下面每行作为参数传给 `python -X utf8 -m pytest -q -p no:cacheprovider`，2026-09-24 在 `8376ec2` 与 `094861c` 上均为 `203 passed`（后者含新鲜克隆）。

```text
tests/test_kernel2d_review.py::test_c19_zero_length_edge_is_a_clear_error_not_zerodivision
tests/test_end_to_end_cb2.py::test_capacity_is_independent_of_the_moment_reference_point
tests/test_margin.py::test_config_space_distance_equals_body_distance
tests/test_kernel3d_covers.py::test_crossing_edge_edge_cover
tests/test_kernel2d_g0.py::test_degenerate_parallel_edges_membership_still_exact
tests/test_interlock_sensitivity.py::test_differentiability_flag_agrees_with_one_sided_quotients
tests/test_kernel2d_g0.py::test_distance_completeness_boundary_cases
tests/test_covers3_strict_lowdim.py::test_distance_completeness_does_not_depend_on_strict
tests/test_kernel2d_g0.py::test_distance_completeness_general_position_concave
tests/test_kernel2d_g0.py::test_distance_completeness_has_teeth
tests/test_kernel3d_covers.py::test_edge_arc_of_box_edge
tests/test_kernel2d_g0.py::test_entrance_block_area_is_minkowski_area
tests/test_kernel2d_g0.py::test_exit_completeness_boundary_cases
tests/test_kernel2d_g0.py::test_exit_completeness_general_position_concave
tests/test_kernel3d_covers.py::test_facet_count_matches_minkowski_theory_for_boxes
tests/test_end_to_end_cb2.py::test_failure_mode_is_read_off_invariants_of_the_dual_face
tests/test_kernel2d_g0.py::test_first_entrance_picks_shallowest_penetration
tests/test_covers3_membership.py::test_g0_convex3_box_vs_box_runs_and_passes
tests/test_kernel3d_covers.py::test_g0_convex3_random_pairs
tests/test_interlocking.py::test_g0_distance_completeness_on_concave_interlocking_pair
tests/test_bb52_g1.py::test_g0_distance_completeness_real_concave_geometry
tests/test_bb52_g1.py::test_g0_exit_completeness_real_concave_geometry
tests/test_kernel3d_covers.py::test_g0_gate_has_teeth_flipped_normals_are_caught
tests/test_kernel2d_g0.py::test_g0_random_convex_pairs
tests/test_covers3_membership.py::test_g0_vote3_counts_only_extreme_points_on_degenerate_input
tests/test_g2_bdda3d.py::test_g2_band_catches_a_real_kernel_defect_through_enumeration
tests/test_g2_bdda3d.py::test_g2_gate_red_on_extra_kernel_ee_cover
tests/test_g2_bdda3d.py::test_g2_gate_red_on_fabricated_ee_legacy_entrance
tests/test_kernel2d_review.py::test_gap0_sign_of_min_gap_false_negative_wedge_in_channel
tests/test_kernel2d_review.py::test_gap0_sign_of_min_gap_is_not_a_concave_membership_rule
tests/test_bb52_g1.py::test_gate_has_teeth_strict_cone_loses_legacy_contacts
tests/test_covers3_strict_lowdim.py::test_generic_vertex_over_edge_is_strict
tests/test_margin.py::test_inflated_membership_tracks_the_margin
tests/test_margin.py::test_inflated_normal_is_lipschitz
tests/test_margin.py::test_inflation_turns_a_set_valued_normal_into_a_single_valued_one
tests/test_margin.py::test_lipschitz_gate_global_pairs_have_their_own_teeth
tests/test_margin.py::test_lipschitz_gate_has_teeth
tests/test_frozen_lowdim.py::test_low_dim_frozen_gradient_is_the_inflated_normal_of_the_explicit_entrance_block
tests/test_margin.py::test_margin_contacts_are_generalized_contacts
tests/test_covers3_membership.py::test_membership_axis_aligned_boxes_does_not_crash
tests/test_covers3_membership.py::test_membership_box_vs_box_matches_closed_form
tests/test_covers3_membership.py::test_membership_tetra_vs_box_sweep_along_x
tests/test_covers3_membership.py::test_membership_tetra_vs_offcenter_box_matches_closed_form
tests/test_interlocking.py::test_min_cover_gap_is_not_a_membership_rule_for_concave_bodies
tests/test_covers3_strict_lowdim.py::test_parallel_edge_edge_nearest_pair_ev3_is_boundary_state
tests/test_covers3_strict_lowdim.py::test_parallel_edge_edge_nearest_pair_ve3_is_boundary_state
tests/test_interlock_sensitivity.py::test_phase_derivative_at_phase_zero_is_flagged_on_every_default_row
tests/test_kernel2d_review.py::test_r1_narrow_crevice_is_reflex_even_with_legacy_tolerance
tests/test_kernel2d_review.py::test_r3_numerically_collinear_vertex_yields_no_vv
tests/test_kernel2d_review.py::test_r4c_micro_concave_input_is_rejected_not_silently_mangled
tests/test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip
tests/test_covers3_strict_lowdim.py::test_stacked_boxes_corner_over_edge_is_not_strict
tests/test_kernel3d_covers.py::test_stacked_boxes_give_four_vf_covers_like_bdda3d_cb2
tests/test_margin.py::test_theorem_two_gate_has_teeth_shrinking_the_nearest_point_is_caught
tests/test_kernel3d_covers.py::test_tilted_vertex_face_cover_is_strict
tests/test_kernel3d_covers.py::test_vertex_cone_of_box_corner
tests/test_covers3_g0_vote2.py::test_vote2_accounts_for_degenerate_facets_box_box
tests/test_covers3_g0_vote2.py::test_vote2_accounts_for_degenerate_facets_tetra_box
tests/test_kernel3d_covers.py::test_wedge_on_wedge_gives_strict_crossing_edge_cover
```

**A.9 `test_lp_fail_loud.py` 逐格枚举**（第六节第 6 条）：在仓库根目录执行下面这段（复用测试里的 `_cohesive_block`，判据与门相同），2026-09-24 在 `094861c` 上得：6 格抛 RuntimeError——`(k=5, s=1e-3, g=1e3, 1e-14)`、`(k=16, s=1, g=1, 1e-14)`、`(k=16, s=1e4, g=1, 1e-12)`、`(k=16, s=1e4, g=1, 1e-14)`、`(k=16, s=1e4, g=1e-3, 1e-12)`、`(k=16, s=1e4, g=1e-3, 1e-14)`；其余 26 格 optimal 且落在径向夹逼内，没有静默给错的格。`lp_tol` 为 None 与 1e-9 的 16 格全部答出。**2026-10-10 复跑（G6 第三轮修复后的 HEAD）**：raises 0 / answered 32——契约"要么答对、要么抛错"仍成立，只是抛错一支在这组格子上不再出现（M0.2 的精确 LP 之后）。

```python
import sys; sys.path[:0] = ["tests", "src"]
from math import cos, pi
from test_lp_fail_loud import _cohesive_block
from eab.limit import limit_load
for k in (5, 16):
    for s, g in [(1.0, 1.0), (1e4, 1.0), (1e4, 1e-3), (1e-3, 1e3)]:
        for tol in (None, 1e-9, 1e-12, 1e-14):
            cts, dead, live, full = _cohesive_block(s, g)
            try:
                r = limit_load(cts, dead, live, dim=3, origin=(0, 0, 0), k=k, lp_tol=tol)
            except RuntimeError:
                print("raise", k, s, g, tol); continue
            assert r.status == "optimal" and cos(pi / k) * full * (1 - 1e-9) <= r.alpha <= full * (1 + 1e-9)
```


## 八、设计正本 07 对代码（2026-10-10 历史表；2026-10-12 增补 M4a）

前三列保留 2026-10-10 的历史核对；第四列登记已合入本树的 M4a 增量，不将离线检测合同冒充 07 的完整同构/在线切换合同。M4a 原始证据见 [接缝地图](m4_bdda_seam_map.md)、[差异台账](m4_difference_ledger.md) 与 [M4a 报告](../reports/codex/M4a_report.md)；G6L 在冻结 15 配对、45 帧的限定审查内未确认 M4a 新缺陷，不等于任意输入正确性证明。

| 07 的条目 | 代码现状 | 偏差 / 状态 | M4a 增量（2026-10-12） |
|---|---|---|---|
| §四 ContactRecord（按生命周期四组：身份 / 步内冻结 / 状态 / 转移；另列"溯源"一段） | `src/eab/contact_record.py`：四组生命周期字段齐；溯源只有 `source` 字段（对应 `source_engine`）与按 (块对, 盖类型, 特征) 排序的 `canonical_key()` 方法 | **溯源段没落地**：07 要的 `canonical_order_key`——"内核自己维护稳定序、与 legacy 序（tf06 跨步继承、df06 后写者胜）只做映射"——没有实现，`canonical_key()` 只是集合比较用的排序键；`cover_type` 枚举里的 FF / FE / EE_PAR 零构造（三维 FF / FE 只以标签元组出现在 `entrance3.merge_degenerate`） | 主特征键不是完整记录身份：M4 v01/v02 四例共 9 条额外主键重复，保留 multiplicity 与第二参考，不静默去重；VV 用两组三点的共享角点确定身份。门 `tests/test_readers_roundtrip.py`、`tests/test_m4_bdda_vv_reader.py`、`tests/test_m4_bdda_shadow.py::test_duplicate_primary_reference_second_row_metrics_are_not_skipped`。 |
| §六 Phase 0 "写六种现有表示的读取器" | 三种：`readers/bdda_df.py`、`readers/bdda3d.py`、`readers/tf_probe.py` | **bdda2 SoA 导出、DDA4.x 审计输出**两种未写。**订正（G6 第五轮 major）**：此前写的理由"DDA4.x 只有逐步汇总、无逐接触导出"是错的——07 §一指定的同一份 `DDAKernel.cpp` 自带逐接触导出 `contact_diagnostics_v3.tsv`（开关 `contact_diagnostics_output`、科学档位下对每个闭合接触写一行：顶点/边 id、状态前后值、法向贯入与刚度、法向力、摩擦），只有 `contact_topology_audit_output` 才是逐步汇总。DDA4.x 读取器没写是**缺口**，不是做不了；它可以当 G1 的第二个 oracle（M4 前补） | 沿用并修复 bdda_df VV 身份读取，未新增 bdda2 SoA 或 DDA4.x reader；读取器数量缺口未关闭。门 `tests/test_m4_bdda_vv_reader.py`。 |
| §六 Phase 0 "15 例 2D 家族与 3DDA 8 个 benchmark 的接触快照入库" | `fixtures/`：bdda_df 48 份生成型 + 原件；bdda3d 3 份；tf 探针 3 份 | 3DDA 侧是 3 份探针抽样，不是"8 个 benchmark 的接触快照"；G2 对 tf05 探针只做了普查（test_tf_reader），没做逐接触同构 | 新增 15 个 bb/db 输入配对 × 3 步 = 45 帧冻结离线数据；F038/S038 三步几何相同，实际为 14 份不同几何时序。不是完整 30–400 步轨迹，也未补 3DDA 8 benchmark。门 `tests/test_m4_bdda_shadow.py::test_family_capture_coverage_and_detection_products_are_not_all_identical`。 |
| §五 G0 自证门 | 二维 `kernel2d/g0.py`、三维 `kernel3d/g03.py`（三票） | E2 二维凸三票已改为零容差定理检验：票一随机及 E 顶点/facet 中点探针全计分，`band_skipped=0`；票二严格/边界集合精确核对，不设豁免；票三只比严格凸顶点。门见第四节 (a)，全套结果见 `reports/codex/E2_report.md`。这不等于已普遍实现 07 所说的每个边界点 ±ε 双侧构造。E5a 三维票一也零跳样，票二/三零豁免，强制全部 E 顶点/棱中点/面重心；门 `test_g03_e5a.py`。凹块盖系统只有距离/出口完备性，盖裁剪与全局 E 待 M3；二维一般多边形精确相交回退另有闭式门 | 本轮无增量；历史缺口不因 M4a 自动关闭。 |
| §五 G1 二维同构门 | `tests/test_bb52_g1.py`（bb52 53/53）、G4 多步（`tools/g4_multistep.py`）、`tests/test_kernel2d_entrance.py`（首入对 legacy 53 条逐条） | 只对 bb52 一例做了一级门；"15 例家族"未逐例对账；**判据也弱于 07**：07 要"锁态拓扑同构、滑动符号一致、位移 ≤ 1e-12"，实际只核顶点-边集合相同与 gap < 1e-6，不比锁态与滑动符号 | 新增静态显式域窗口内的 15 配对逐帧影子检测与具名差异核对；未分类为 0 不代表逐项与 legacy 相同，仍不核锁态/滑动符号/位移同构，也不是本步真实运动首入。门 `tests/test_m4_bdda_shadow.py::test_fifteen_family_three_steps_have_only_pinned_classified_differences`。 |
| §五 G2 三维同构门（vs tf05 / bdda3d） | `tools/g2_bdda3d.py`、`tests/test_g2_bdda3d.py`、`tests/test_entrance3_g2.py` | 只对 bdda3d 的**手写**入口清单（cases.py）；tf05 探针侧无同构门；"逐接触 gap/法向 1e-12"未做 | 本轮无增量；历史缺口不因 M4a 自动关闭。 |
| §五 G3 对偶门 | `tests/test_dual.py`、`test_interlock_sensitivity.py`（G3 收敛阶 1.9995） | "批量 vs 单通道逐位、零跳过审计"未做（那是 bdda2 的 Scalar 纪律，eab2 未开工） | 本轮无增量；历史缺口不因 M4a 自动关闭。 |
| §五 G4 活动集门（砖一，go/no-go） | 已做并**关闭**（5/61，09-27 订正） | 07 的 Phase 1 执行记录仍写 5/82 的旧口径（正本只读，未回写） | 本轮无增量；历史缺口不因 M4a 自动关闭。 |
| §五 G5 差异台账 | 无 | 未开（tf05 的 az=2°、平行入口择一与盖理论的分歧没有逐条记录） | 已开 b-DDA M4a 局部台账 `docs/m4_difference_ledger.md` 与冻结逐条摘要 `docs/m4_shadow_expected.json`；未知类别/缺有效盖仍拒收。tf05 az=2° 等其他线差异仍待做。门 `tests/test_m4_bdda_shadow.py::test_unknown_difference_never_passes`。 |
| §六 Phase 2 三维凸内核（三类 facet 盖、低维盖、退化盖、首入） | `kernel3d/covers3.py`（VF/FV/EE/VE3/EV3/VV3）、`entrance3.py`（首入 + FF/FE 合并，M2 第一版） | 退化盖只在首入合并里有，`enumerate_covers3` 仍不产出 FF/FE/EEP；首入未经 G6 | 本轮无增量；历史缺口不因 M4a 自动关闭。 |
| §六 Phase 3 凹块局部角覆盖 | 无（M3） | 未动；凹块仍靠暴力谓词裁决（`interlock.py`） | 本轮无增量；历史缺口不因 M4a 自动关闭。 |
| §六 Phase 4 可微与互补（Scalar 纪律、活动集方法、MLCP） | `dual.py`、`kernel3d/frozen.py`（冻结盖可微）；L3 极限分析 `limit.py` / `limit_multi.py`（07 未规划） | 开闭迭代改写为显式活动集方法、MLCP 交叉核对**未做**；极限分析是 07 之外加的一层（L3 互补层） | 本轮无增量；历史缺口不因 M4a 自动关闭。 |
| §六 Phase 5 接缝与切换（bdda2 `BDDA_DETECT`、bdda3d 引入 eab、tf.cpp 只探针） | 无（M4） | 未动；按 README 规矩等 M0 退出 + M2 首入落地 | 已有离线适配器 `src/eab/adapters/bdda2d.py`、接缝地图及 BDDA_DETECT 提案；只消费冻结导出，不切姊妹默认路径，不实施在线检测/装配/继承/开闭求解。门 `tests/test_m4_bdda_adapter.py`、`tests/test_m4_bdda_shadow.py`。 |
| §七 各仓库改动清单（姊妹仓库只读 / 只加接缝） | 本仓库从未改姊妹仓库（AGENTS 红线） | 一致 | 仍只读；本树编排复制 exe/输入到沙箱后捕获再冻结，不在姊妹源码运行或回写。R12FIX 仅消费既有夹具，不重捕获。 |
| §八 风险（tf06 顺序继承、顺序即物理、az=2°、单人带宽、两仓库无远程、bdda3d 第三份本构副本的 o3 / o3t 口径） | "顺序即物理"落实为同构门而非逐字节；其余是姊妹仓库事务 | 3DDA / 3-b-dda 的远程备份状态本仓库不掌握；本仓库自己也无远程（第四轮盲区 1）；第六条（bdda3d 本构副本 o3 vs o3t，统一时必须自报）本仓库还没碰到——M4 之前不涉及 | 已调查 b-DDA 检测、df06 转移及消费接缝；集合检测门没有证明有序参考可随意交换，第二参考/multiplicity 不丢失；bdda3d o3/o3t 等缺口仍保留。 |
| §六 Phase 0 的门"读取器往返逐字节" | `tests/test_readers_roundtrip.py` | **判据弱于 07**：做的是 `records_to_json` 往返与确定性，不是对原件逐字节；tf.cpp 三条探针 TSV 只读了 `contact_pair_stage` 与 `retry_contact_pair_probe` 两条，`solver_profile.tsv`（内容哈希列）未读 | 新增独立原始 CSV 身份/度量核验、冻结文件溯源；不是六种格式逐字节逆序列化，也不补 tf solver_profile.tsv。门 `tests/test_m4_bdda_shadow.py::test_legacy_reader_shifted_column_is_rejected_by_independent_raw_identity`、`::test_exported_legacy_metrics_are_checked_not_just_reconstructed`。 |
| §五 G4 的判据（15 例 m9 轨迹、事先定死的命中率阈值、对比迭代次数） | `tools/g4_multistep.py`、`reports/g4_multistep_first_datum.md` | **判据弱于 07**：只跑了 bb52 / bbF038 / bbW025 三份 dump（bbF038 翻转为 0），没有事先登记阈值，也没量迭代次数；"砖一关闭"是在这个缩水的实验上下的结论 | 未以三步静态 M4a 代替 G4 迭代/命中率实验；原 G4 缺口保持。 |
| 07 第 33 行旧称“它既是 2015 理论的第一份实现”（此主张不成立） | — | **撤回优先性主张**：改称“E(A,B) 理论的一份独立实现，以及姊妹三线的独立对账通道”；不能通过限定为 DDA 圈内或本课题组来保留优先性。只读正本 00 已列 Zheng/Jiao et al. 2016、Zhao et al. 2020、Feng & Tan 2020、Ni et al. 2020 等实现谱系，AGENTS 09-24 订正同样明确。07 正本按工单只读，此处登记矛盾并以本树订正为准，不声称已改正本 | 本轮无增量；历史缺口不因 M4a 自动关闭。 |

历史小结（2026-10-10；M4a 增量以第四列为准）：07 的 Phase 0–2 大体落地但**规模与判据仍有缺口**（读取器 6→3、G2 只对手写清单、G5 未开；E5a 三维 G0 与二维 E2 均已零跳样本，但未普遍构造逐边界点 ±ε 双侧探针，E5a2 已接通有效闭合三角表面的精确实体三态，但一般单盖折面法锥仍有限；E5b 后继精确判据见开头更新；G1 不比锁态、Phase 0 不逐字节），Phase 1 的 G4 go/no-go 在三份 dump 的缩水实验上执行并关闭了砖一，
Phase 3/5 未动，Phase 4 走了 07 没规划的极限分析路线。07 的 Phase 1 执行记录与 03 砖一回写一样停在 09-18 的口径。

### E5a2 补充边界（有门，未过 G6）

- 一般单盖：源非平面 ring 只解释为精确 Newell 向量、首顶点锚平面、投影绕数及源邻接描述符；即使算术精确，见证也不一定在折面实体上。门 `test_e5a2_covers.py::test_source_ring_descriptor_is_not_a_folded_surface_cover`、`::test_source_ring_descriptor_keeps_source_labels_separate_from_convex_views`。
- 枚举域窗与构造输出分开：六类盖从原数据比较精确距离平方；`Cover3.gap` 仍是浮点构造，不影响窗口开闭。恢复 gap 分支的内部突变由真实下溢格捕获。
- 本单没有新浮点过滤或新缓存层。性能改动为精确整数代数、既有缓存载荷的等价整数形式及不影响答案的延后计算；逐 Fraction 对拍见 `test_e5a2_integer_arithmetic.py`、`test_e5a2_bilinear_integer.py`。完整 profile/全套计时与未达项见 `reports/codex/E5a2_report.md`。


## WO-E5a2 退出状态：PARTIAL（2026-10-12）

本单指定底层门与整数化对拍通过，但完整测试未全绿，不构成里程碑退出。严格表面语义揭示旧 interlock 近竖直事件被噪声政策丢弃：原80个竖墙输入中7格存在独立认证的更低分离高度，当前返回约1.2不是最小逃逸。不能把原最小逃逸门改成只检查安全上界。另有旧并列窗口突变牙失效；加强草案只在证据中，未应用。完整失败清单、实测耗时、独立反证及 WO-E5b 交接以 `reports/codex/E5a2_report.md` 为准；竖墙证书见 `reports/codex/E5a2_evidence/a1/walls_handoff.md`。没有宣称全套≤900秒、正式G6、新worktree或全链精确化通过。
