# WO-M3b：M3 收尾报告

日期：2026-10-15。执行树：`D:/eab-wt/cx-m4`；起点 `m4-seam / 3bf5e955d8ea669846a088f50223e17e76475947`。

> 收口验证已完成：最终 r4 新鲜字节副本 **13,187 tests 全绿、收集=执行、0 skip，静态构造 0 违例**；独立机器审计 GREEN（0 缺失、0 失败）。这是研究级 **M3b_PARTIAL**，不是完整 M3/G6 验收；未闭合项见第 1/10 节。

## 1. 逐项处置

| 工单项 | 当前交付 | 状态与边界 |
|---|---|---|
| 1 二维遗留 | T2a 普遍弱覆盖正式证明；T2b 可证凸合并和等价语义剖分；bb52 全 21 对 7,113 探针零失配 | 本实现域内完成。扫描的是完整**等价语义粗化剖分**，不是原三角胞全部人工内缝 overlay；二者不可混称 |
| 2 三维边界/强完备/出口 | 新 `boundary.py`，显式闭片边界、VF/FV/EE 裁剪、最短闭集出口平方及全并列见证；T3B、条件 T3L；g03 相交侧不跳样 | 条件域交付。任意退化原始盖弱覆盖 H 未普遍证明；g03 相交侧检验的是给定一般方向的出口，**不是一般凹体最短出口的全样本独立 G0** |
| 3 构造数值审计 | parts_b、有序面、一般 BSP Steiner/斜切三档逐值代数证书；边界真实公开入口全字段独立 Cartesian 参考 | 有限族审计，不等于独立复制整个 BSP 分支/拓扑顺序或全部一般裁剪 Steiner 分支 |
| 4 三维输入拒绝 | 精确三角交集、顶点 link、边 incidence、逐壳体积及嵌套定向；负例及变异门 | 对面定义的有理多面曲面认证。非平面环按既有确定性三角化解释；局部盖 API 另要求平面面环 |
| 5 性能 | 任意方向精确包围盒剪枝、不可变结构 hash 缓存、精确线区间缓存 | **PARTIAL**：热查询提速；新增完整认证使冷启动 box/TIA 变慢，尚未达到完整逃逸流程提速目标 |
| 6 Xbloc | 核原论文 Fig.7，取得厂商官方 DWF，来源/散列/资源审计可重跑 | **PARTIAL**：未完成可靠实体、圆角离散/误差证书、Xbloc 两类算例和圆角方向变异；没有用猜造形体顶替 |

研究结果不是工程标定、姊妹求解器替换或 M3/G6 退出。全部改动留在工作树，未 commit/push/reset/checkout/stash/worktree/branch。没有写入或运行只读姊妹树；PROVENANCE 未改，因为本单没有新增已认证夹具。

## 2. 理论先行：证明及适用域

详见 [二维设计补充](file:///D:/eab-wt/cx-m4/docs/m3_global_entrance_design.md)、[三维设计](file:///D:/eab-wt/cx-m4/docs/m3b_boundary3d_design.md)、[输入认证论证](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/construction3d_notes.md)。这是本仓库自包含推导，不冒称原论文同号命题。

### T2a：闭有效 VE/EV 弱覆盖

域为无零边/回折的全维正则闭简单多边形，允许平直顶点、非严格有效、平行/共线及多重接触。
有限凸并的边界是有限闭线段并。去掉有限 VV 平移后，非 VV 边界配置在边界稠密；非贯入接触必含顶点—边相对内部接触，或共线区间端点退化为此情形。局部不贯入强迫顶点邻域位于接触边的外侧闭半平面，正是**闭**局部支撑法锥有效性。有限闭盖并取闭包补回 VV/端点，得 `∂E ⊆ ∪有效 VE/EV`。平直顶点的法锥是正确朝向单射线，不能用严格筛选删除。

与原 T2 合并后，完整切分和双侧闭占据裁剪得到二维强完备。门 `test_nonstrict_flat_collinear_local_covers_weakly_cover_boundary`、原六家庭裁剪门及 strict-only 真实内部变异支撑实现；有限实验不充当普遍证明。

### T2b：可证降规模而非省略样本

原体耳切片内点互不交；仅当精确 `area(conv(P∪Q))=area(P)+area(Q)` 才合并，面积证书保证并集真凸。不能把此公式用于重叠的配置胞。
全部原体 VE/EV 几何段安排包含 `E\O=∂O`。完整交点切分后，仅去掉恒为贯入的相对开段/点，保留所有接触段及**孤立接触点**；再作完整竖直剖分，保持 E/O 和每胞标签。默认旧细剖分不变；`merge_convex=True, compact_subdivision=True` 显式选择新路径。

### T3B 与 T3L

- **T3B**：有限认证满维紧凸片 `C_ij=B_j−A_i` 的面按全部支撑平面加细。相对开二维片两侧位于标签恒定的开胞；精确最近事件半步不跨其他平面。闭占据异标恰为暴露片；正则闭有限多面并的低维边界由暴露片闭包补全。**不要求一般位置**，支持共面/多重/平行退化。
- **T3L**：原始闭有效 VF/FV/非平行 EE 候选先弱覆盖，再与全局暴露片裁剪即强完备。正文给出明确的非循环 GP 充分条件：跨实体面/面、棱/面、棱/棱相应非平行。稠密二维接触层只剩 VF/FV/EE；局部不贯入推出闭法锥有效；EE 先排除反射楔，再由凸切锥分离得到叉积法向。任意退化输入仍要求 H，**不能用“微扰后成立”把 H 删除**。有限退化家族的独立原子覆盖验证只认证这些输入。

输出为闭凸多边形片覆盖，不是焊接半边网格。`E` 是闭接触集合，`O` 是体内贯入集合；紧配内缝可以属于 `int(E)\O`，不能把物理状态 0 当外边界。`shortest_exit` 返回到 `∂E` 的距离平方和所有并列有理见证；见证仍相触，是严格分离距离下确界而非已严格分离。

### 相交侧出口

`g03.py` 不再 `continue` 跳过相交/接触。独立原表面 VF/FV/EE 支撑事件超集沿确定性 moment-curve 一般方向枚举，逐事件开区间判闭分离（含最后无界区间），与全局闭区间出口逐 Fraction 对拍。恢复跳样变异红在执行样本数断言。
这是相交侧**方向出口**缺口的关闭；不把它写成对一般凹体最短分离量的全域独立验收。

## 3. 二维 bb52 全量穷尽探针

[21 对逐对结果及源码哈希](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/two_d_bb52/summary.json)；[规模墙](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/two_d_scale.json)。输入按原夹具读取器产生的 binary64 值精确有理化，不偷换为理想十进制几何。

| 类别 | 执行数 |
|---|---:|
| 全部剖分顶点 | 1041 |
| 全部边中点 | 1773 |
| 全部开面内部样本 | 753 |
| 每条边的精确双侧事件探针 | 3546 |
| **合计** | **7113** |
| 失配 / skip | **0 / 0** |

21 对单次冻结扫描耗时 **56.4959 s**；同时核存储标签、成员查询、拓扑查询，**3546 个侧点另逐个核实际相邻开面或外框外侧**，零豁免。代表子集入 pytest，大扫描不进入常规全套。
原最大三角对 `(1,2)` 为 1344 胞对，经原体可证合并为 1075 对；4029 条原胞边切为 **619780 原子边 / 308957 个 x 事件**，朴素竖直展开约 1,244,783,724 次边×事件访问，未展开这份无必要的原人工 overlay。其完整语义粗化为 76V/132E/57F；所有 21 对中实际最多 V/E/F 的 `(1,3)` 为 97/168/72。完整剖分对象的改变有 T2b 证明，不是抽少量历史平移冒充穷尽。

### 末轮独立复核抓到并修复的侧探针缺陷

原 compact 路径只按保留接触骨架的非零支撑线事件限步：旋转 PIN/U 时探针可落在紧配缝端点；POCKET 顶边插入平直顶点后可恰落孤立接触点。原门仅核落点状态，所以仍绿。该发现推翻了旧扫描关于“邻开面探针”的声称，但不推翻 T2a/T2b 及原所取点三态零失配。

修复后使用**最终完整剖分的全部边**支撑线限步，未构造 compact 剖分时保持旧路径；`_contact_edges` 仍仅表示物理接触骨架。三档反例门以自持行列式严格开凸面包含核实际邻面，不照抄被测限步公式；删除新增限步分支的真实内部变异报红。全 21 对也对每条剖分边的两侧点直接核其相邻开面或外边界外侧，旧扫描作为 superseded 保留后整轮重跑。修后另一次不按被测步长公式构造期望的独立旁路，覆盖 36 格、4542 侧点，0 失配、0 skip（5.394 s）；覆盖孤立/平直孤立/紧配缝、四种有理旋转及三档尺度/平移。[独立发现与修后复核](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/two_d_theory_peer.md)

## 4. 三维全部安排探针与强覆盖有限证据

[完整扫描](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/boundary3d_scan.json)覆盖**内部与暴露**安排片，不只探测最终外表面。

| 家族 | 凸片对 | 安排片 | V | 棱中点 | 面重心 | 双侧点 | 局部盖原子覆盖 |
|---|---:|---:|---:|---:|---:|---:|---:|
| L | 2 | 60 | 50 | 106 | 60 | 119 | 409 |
| tight | 3 | 147 | 91 | 232 | 147 | 293 | 577 |
| cavity | 6 | 1054 | 685 | 1722 | 1054 | 2096 | 868 |
| general_tetra | 1 | 14 | 12 | 24 | 14 | 28 | 14 |
| **合计** | 12 | **1275** | **838** | **2084** | **1275** | **2536** | **1868** |

总 **6733 个类别—坐标探针，0 失配、0 skip**，另逐安排面检查双侧拓扑、逐独立投影原子片检查局部盖覆盖。相同坐标在不同类别出现时分别执行。最大实例 1366 个含来源重复的安排片；尚未测大型 Xbloc 网格规模墙。全支撑平面安排最坏可达 `O(N H²)` 片，候选盖×暴露片裁剪仍可能昂贵；精确查询域/BBox 局部化是待实现方案，不写成已提速。

**独立 GP 补例另计，不混入 6733**：原 `general_tetra` 只是非轴对齐例，其中有跨体 EF 平行，不能因名字就称满足 T3L 的强 GP。另选原坐标整数四面体对，自持 Fraction 逐项核满维 2、跨体 FF 非平行 16、两向 EF 非零内积 48、EE 非平行 36，共 **102/102** 条充分条件；对选定输入全部 **72 个探针**（V11/E22/F13/侧26）及 **13 个局部原子片**检查，0 失配、0 skip，0.3313 s。49 个登记源/脚本哈希前后一致。[GP 证据](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/gp_boundary_probe.json)

## 5. Oracle 独立性、数值合同及输入域

| 门 | 主 oracle / import 与原语 | 不共用范围 |
|---|---|---|
| 二维三态/拓扑/完整剖分 | `kernel2d.g0_oracle`：Fraction、math.lcm、oracle_construction.sqrt_exact/scalar_exact；原始边环的独立整数相交/绕数 | 不调用被测耳切、凸并、bbox index、盖裁剪或安排切分 |
| 三维安排三态 | `geom3.polyhedra_overlap → exact_geom`：Fraction、functools、itertools、math、rational3；独立原表面三角分割/奇偶 | 新 `global_entrance` 自持 BSP/SAT/三角化，未 import 该 oracle 的原语 |
| 三维方向出口 | `g03_exit_oracle`：Fraction、itertools、g03_surface_oracle；后者 Fraction/functools/math/g0_oracle.sqrt_display | 独立整数平面/面绕数、射线奇偶、原始距离；不 import 被测 BSP/SAT/边界裁剪/盖枚举 |
| 原始局部盖强覆盖 | 测试自持投影安排、行列式、线性插值、凸片包含 | 不调用 B/G 的 hull/clip/cross/split/in_polygon |
| parts_b/面/一般 Steiner | 测试自持 Fraction 行列式、Cramer 和源面半空间；itertools.combinations/product | geom3/既有测试 helper 仅造输入；不调用被测 normal/clip/BSP/SAT 生成期望 |
| 边界与出口构造 | 独立笛卡尔差盒、解析距离/投影及有理刚体变换 | 不用另一遍同实现或 float 精度门冒充逐值参考 |
| 输入拒绝 | 手工解析非法曲面；附加 400 对独立重心坐标活动约束三角交检查 | 400 对参考用独立线性方程求解，不调用生产 cross/normal |

逐文件直接 import、别名、行号与源码散列见 [20 文件 import 清单](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/oracle_import_inventory.json)。该清单包括测试同时引用的被测对象与输入构造器，不把 import 不相交当成独立性证明；判据原语的独立性以表中调用路径和门 docstring 为准。

逐项登记见 [construction inventory 的 M3b 增量](file:///D:/eab-wt/cx-m4/docs/r13fix_construction_inventory.md)。parts_a/b 非对称不同盒的全部顶点/有序面/内点在 **2⁻⁴⁰⁰、1、2⁴⁰⁰** 对拍；一般 BSP 每档 4 胞、21 顶点记录、20 面记录、5 个新 Steiner 点逐值认证，斜切两侧也核。一般 BSP 的参考证明每个值属于独立源平面精确解、全部极点被表示并核支撑/绕向，不假装是独立重演全部 BSP 合并次序。

补审后新增 `test_m3b_boundary3d_fields.py`：真实公开入口的非对称双盒，三档尺度 × 公共平移模长 `{0,10³,10⁵,10⁶}` 共 **12 格**，采用 seeded 整数 quaternion 构造一般有理 SO(3)。独立参考逐值核完整冗余 SAT 平面表、全部 patches/arrangement 的坐标/法向/侧点/状态/来源、probes、所有原始/裁剪 VF/FV/EE 的 label/坐标/raw normal、最短出口平方与全最优集合。只对实际产物取指纹的另门确认 **12/12 互异**。这完整覆盖该 box 分支；不将其外推为一般相互切片 Steiner 分支全部构造量已独立穷尽。原 10 个边界门加 12 格为 `22 passed in 7.09s`。[字段覆盖明细](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/boundary3d_fields_audit.md)

输入入口精确检查：面索引/零面积、边反向双 incidence、顶点 link 多重圆、全部非邻接/邻接三角交是否超出允许共享 simplex、逐壳非零有向体积与奇偶嵌套定向。负例覆盖穿插、共面重叠、仅共享顶点非流形、缺面、翻面、被大正体积掩盖的反向小壳、零体积片。无长度/角度浮点阈值。面引用定义几何，未引用 buffer 被独立重映射，不进入 bbox；这不是对已引用坏片的豁免。

交叉复核确实发现并修复两项：合法共线细分产生的 2-edge vertex link 必须保留平行多重边；独立表面 oracle 把 unused buffer 当孤立实体，曾把解析距离平方 9 错判 None，现独立 remap 后有交换 A/B 门。既有外层 escape 缓存可遮住深层 monkeypatch；变异进程必须清相关缓存，不声称新增缓存 key 提供任意动态代码替换失效保证。

## 6. 真实内部变异表

下列实际子进程的源码哈希类门均**未执行**；验收依据为最后未捕获 `AssertionError`，不是字符串哈希绊线、下游偶然报错或人为追加错误产物。

| 缺陷注入 | 预期语义断言 | 状态 |
|---|---|---|
| 三维取消盖裁剪 | `local cover clipping removes buried polygons` | 真红 |
| 误以片上物理 0/1 判暴露 | `closed occupancy boundary not physical 0/1 seam` | 真红 |
| g03 恢复相交跳样 | `intersecting exit sample must execute` | 真红 |
| 三维真实共享整面邻接分支绕过凸性守卫，错误凸化非凸并 | `full-facet nonconvex merge filled independently excluded region` | 真红；两四面体实际被错误合为外包盒 |
| 三维 bbox 漏掉贡献凸片 | `all exact box candidates are retained` | 真红 |
| 自交交集检测漏共面重叠 | `overlapping coplanar shells must be rejected before decomposition` | 真红；变异确实错误接受非法表面 |
| 二维非凸并被错误合并 | `nonconvex union must not be filled by convex merging` | 真红 |
| 二维空间索引漏候选 | `spatial index omitted a contributing cell` | 真红 |
| 二维仅保留 strict 有效盖 | `nonstrict local weak cover omits boundary` | 真红 |
| 二维侧探针退回仅接触骨架限步 | `compact side probe left its adjacent open face` | 真红；探针命中紧配缝端点/孤立接触点的真实缺陷 |
| 二维删孤立紧配接触点 | `isolated contact vertex was regularized away` | 真红 |
| 三维侧点最近事件步长 1/2 错为 1/3 | `independent exact canonical-plane side points` | 真红；状态可仍正确，构造坐标不可蒙混 |
| EE 原始法向数值错误乘 2 | `independent every local VF/FV/EE label coordinate normal` | 真红；点和方向不变，raw 数值仍被审计 |
| Xbloc 圆角离散方向反转 | 没有认证模型，不能执行 | **NOT_RUN / 未满足** |

细目及红日志：[二维](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/two_d_mutations.json)、[三维边界](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/boundary3d_mutations.json)、[构造/认证](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/construction3d_mutations.json)。
[两项数值构造真红及 12 格互异](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/boundary3d_numeric_mutations.json)与上列十一项几何/状态真红分别保存，共 13 个实际未捕获语义红；Xbloc 项未执行，不计入通过数。
必须区别等价变异：完整安排的双侧开胞物理值只为 −1/1，字面把 `>=0` 改成 `>0` 不改变结果，不能虚报杀死它。真正误收内缝的变异是片上 0/1 替代双侧闭占据。

## 7. 性能与逐 Fraction 回放

精确任意方向 AABB 参数区间交为空才剪枝；等号切触保留。结构 hash 缓存不作几何判据；线区间缓存保存精确端点，不退回 gap 或浮点阈值。
全部既有 **392** 逃逸输入在二维侧探针修复后的新鲜字节副本再次完整重跑，对 `input_sha256/exact_height/exact_offset/state` 共 **1568 字段完全相等**，暴力谓词调用 **0**。本次正式冻结轮一次完成：392 项回放循环 **687.6583 s**（外层整进程 **698.5341 s**），298 个注册源码/测试/工具/driver 文件前后哈希不变；同时对本单修改前基线和历史 pre-M3 冻结输出全等。[正式对账](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/construction3d_frozen_r4_comparison.json)、[执行认证](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/construction3d_frozen_r4_replay_attestation.json)

本次另记录真实 import 文件及 driver，不只假定静态文件集合就是运行闭包。独立审计核冻结副本、最终 r4 与当前生产源码及实际导入 helper 的相等关系。[真实 imports](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/construction3d_frozen_r4_actual_imports.json)

完整基线 **677.498 s**，修后本次 **687.658 s**，观测约慢 **1.50%**。并发条件不同，不能视为稳定测速结论。较早过渡轮 679.415 s 和旧冻结轮 649.483 s 均保留为历史，不把其中较快值选作最终性能。冷启动微基准仍明确退步，完整逃逸提速目标未完成。

| 每族 5 次独立冷热微基准（中位数） | 修改前 | 修改后 | 结论 |
|---|---:|---:|---|
| box 冷完整逃逸 | 0.017498 s | 0.030834 s | 约慢 1.76 倍 |
| wall 冷完整逃逸 | 1.609613 s | 1.623101 s | 约同速 |
| TIA 冷完整逃逸 | 0.163881 s | 0.316236 s | 约慢 1.93 倍 |
| box 热状态查询 | 84.264 μs | 2.460 μs | 34.25 倍加速 |
| wall 热状态查询 | 705.915 μs | 4.247 μs | 166.21 倍加速 |
| TIA 热状态查询 | 260.152 μs | 3.546 μs | 73.36 倍加速 |

[原始微基准摘要](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/construction3d_micro_summary.json)。热次每轮 100 个不同参数查询；冷次清空模型/事件缓存。新增完整输入认证抵消冷启动优化，故性能项保持 PARTIAL，不能拿热查询倍数替代整体提速。

## 8. Xbloc：来源已核，实体未伪造

Bakker、Klabbers、Reedijk，*Introduction of the Xbloc Breakwater Armour Unit*，Terra et Aqua 94（2004-03），Fig.7（印刷页 7），已核 `D、D/3、r=D/19`，图形与独立文字层均读取。[原始论文 PDF](https://www.iadc-dredging.com/wp-content/uploads/2017/03/article-introduction-of-the-xbloc-breakwater-armour-unit-94-01.pdf)

厂商页面公开提供 **4 m³ Xbloc DWF**；已取得真实 ZIP/DWF、资源清单、描述符及缩略图，确认不是可以随意以三根正交方柱替代的几何。[官方模型页面](https://xbloc.com/en/design/xbloc-hatching)、[官方 DWF 下载](https://xbloc.com/beheer/upload/3/Download/4cub_xbloc.zip)

本轮未完成 W3D/HSF 压缩 shell 的可靠解码/拓扑认证，也没有所有连接处圆角/倒角定义和到设计实体的误差上界。不能把显示 tessellation 当成精确设计 CAD，不能编造圆角外/内离散方向。缺口是**本轮没有完成认证转写**，不是声称可靠公开模型不存在。

因此无 Xbloc 夹具、无 PROVENANCE 新条目、无 Xbloc×Xbloc / Xbloc×cube 零失配与逃逸门，也无圆角方向变异。`tools/m3b_xbloc_sources.py --download` 可重新取两份固定散列来源；上游变化会失败而不是自动续签。[来源审计](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/xbloc_sources.json)

## 9. 全套、静态门与证据纪律

基线 HEAD 导出共 **13,110** 节点，四片全绿、0 skip、静态 0。不以旧 M3 报告的 12,761 代替本单实际起点。基线与最终均在本树 `tmp/` 的新鲜字节副本执行；因所有者禁止 worktree，此验证**不是 fresh Git worktree 门，更不是 G6**。

第一次 `final_suite` 因复核发现新边界字段数值门覆盖不足而主动作废；仅停止已确认的本单 runner/四个子 pytest，日志移至本树 ignored tmp。[作废记录](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/run_invalidations.json)
第二次 `final_suite_r2` 抓到两项：第 1 片文档门的 canon_map 旧行号失效，第 2 片既有 M4c 450 帧冻结结果的生产源码绑定过期。前者只更新本单造成位移的十个指针；后者必须真实重算全部 450 帧再逐帧核旧结果，不能直接续签哈希。提前启动的 r3 因第二项已主动停止并整体作废；最终 `final_suite_r4` 从头收集、从头四片，不拼接任何旧轮绿片或单门补跑。

### M3b 导致的既有 M4c 证据绑定刷新

没有弱化 `test_frozen_full_computation_is_bound_to_current_production_sources`，也没有只替换摘要哈希。修后源代码下，独立编排原回放 CLI，一次完整运行 **15 家族 × 30 帧 = 450 帧**（190.5988 s），逐帧 JSON 与既有冻结结果深比较、原帧哈希相等、15 个 gzip 逐字节相等，0 失配/0 skip。23 项生产闭包前后不变；全部 fixtures（含 PROVENANCE）保持原字节。随后全部 M4c 定向门 **347 passed in 17.70s**。

只刷新 `reports/codex/M4c_evidence/frozen_summary.json` 为真实新批摘要；原摘要与首轮重跑摘要均保留在 M3b evidence。此文件是 M3 源修改触发的依赖证据更新，不修改平行 M5a/SE(2) 实现。[450 帧认证](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/m4c_refresh_attestation.json)、[可重跑编排](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/m4c_refresh.py)

### 最终四片最后一行（r4，原样）

```text
3297 passed in 1498.32s (0:24:58)
3297 passed in 615.52s (0:10:15)
3297 passed in 1003.62s (0:16:43)
3296 passed in 882.36s (0:14:42)
```

静态最后一行：

```text
exact construction AST gate: 0 violation(s)
```

最终 **13,187** 节点，比本单基线新增 **77**、删除 **0**。296 项当前/冻结源码、测试、工具及 policy/刷新摘要字节一致；最终独立机器审计 **GREEN，0 缺失、0 失败**。四片总墙钟含收集/静态：基线 **1692.386 s**，修后 **1677.171 s**，观测差 **-0.90%**，本次未见超过约 10% 的全套耗时增量。分片节点归属及并发负载不同，此值是执行记录而非受控性能基准，不抵消第 7 节冷启动退步。

独立汇总器对 dispatch / collected / setup / call / teardown 作 **Counter** 核验：每节点恰好一次、每阶段 pass、0 skip；能抓住只比较 set 会漏掉的重复 call。还核源码/测试/工具/policy 的冻结字节及两种完整扫描的源码链、真实变异日志。[最终审计](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/final_audit.json)

静态本地审核新增 **39** 个精确 AST 位点：25 个测试变异/清缓存脚手架，3 个不可变结构 hash，11 个精确调用或报告输出的保守分析缺口。人工续签 **23** 个旧位点：g03 21 个、独立 surface oracle 最终显示 2 个。全局 import/call 白名单未扩张；每项理由/节点/context 均保留。[静态审核清单](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/static_review.json)。零违例不等于静态分析已证明任意 Python，也不等于零人工证明缺口。

范围/编码检查同时核全部交付链接可打开、无 UTF-8 BOM、无新增大日志进入可提交路径。既有 M4c 摘要原本使用 CRLF，本次保持该风格；Git 空白检查在只读命令级加 `cr-at-eol`，不改 Git 配置，真正的行尾空格/制表符仍检查，默认检查把 CR 视作空白的退出码也保留。[范围审计与链接检查](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/scope_audit.json)

命令均在本树运行，`PYTHONDONTWRITEBYTECODE=1`、`python -X utf8`；pytest `-p no:cacheprovider --basetemp <本树证据tmp子目录>`，TEMP/TMP 同样定向。大于 1 MB 的节点清单/执行记录及源副本仅保留 ignored tmp；既有 policy 本身超过 1 MB 是配置，不是新增执行大日志。

## 10. 复跑入口、交付及遗留

在本树 PowerShell 先设置：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Join-Path $PWD 'reports/codex/M3b_evidence/tmp/driver')
$env:TMP=$env:TEMP
python -X utf8 tools/m3b_run_gates.py --name <未存在的新名称>
python -X utf8 tools/m3b_finalize_evidence.py --final-name <相同名称>
```

全量二维、三维扫描及变异入口分别见 `tools/m3b_scan2d.py`、`tools/m3b_boundary3d_evidence.py`、`tools/m3b_construction3d_evidence.py`；运行前阅读模块说明及参数入口。**boundary3d 脚本不支持 `--help`**：默认直接全量扫描，`--mutations` 执行变异，会写固定证据文件；重跑前须由所有者另存当前冻结轮，不要覆盖正在运行或需要保留的证据。原始 HEAD 与基线 archive 是回退锚，仅由所有者决定回退/提交。README、计划、canon_map、inventory 只改 M3 相关行/新增节及本单导致位移的十个精确行号指针，不重排平行 M5a 段落。

**遗留**：Xbloc 认证转写/误差及全部相应门；完整逃逸冷启动/总流程提速；任意退化原始盖 H 的普遍证明；一般凹体相交侧最短出口的普遍独立 G0；大型显式安排规模/精确局部化；所有者独立六路 G6。三路子任务交叉复核不是六路退出门。

M3b_PARTIAL：Xbloc认证与相应门、完整逃逸提速、任意退化局部盖H、一般凹体最短出口独立G0、独立G6未闭合
