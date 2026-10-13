# WO-M3：凹块全局入口块构造报告

日期：2026-10-14。起点 `codex-work / 808216a`，初始干净；所有改动留在工作树，未提交。
范围仅 `D:/eab-wt/cx-e2`。未写姊妹库、其他工作树或理论正本；dependencies 仍为空。

## 1. 结论及理论边界

本单交付二维精确全局 E/O、带三态的平面剖分、局部盖裁剪、全局边界、距离、闭分离下确界及平移首入；
三维交付精确凸分解与闭/开凸片对并、射线区间和逃逸高度去暴力判决。不是全部 M3 验收矩阵完成，详见第六节。

理论先行稿：[m3_global_entrance_design.md](../../docs/m3_global_entrance_design.md)；
独立理论、文献核查：[theory_audit.md](M3_evidence/theory_audit.md)。初稿中文写入曾损坏为问号，随后用 UTF-8 原生写入修复；该事件没有隐去。

| 命题 | 条件与证明状态 | 实现/门 |
|---|---|---|
| E=B−A，O=∪int(Bj−Ai)，E=∪(Bj−Ai) | **已证**：有限全维闭凸片精确覆盖正则闭原体；开交集可避开有限分片边界 | 2D/3D 两个 global_entrance 模块；实体三态独立门 |
| O⊆int E，E=closure(O)，但 O 可不等于 int E | **已证**；紧配内缝是明确反例 | `test_m3_theory.py` 的 U 槽闭式门；`test_zero_clearance_contact_is_not_silently_regularized_to_open_union` |
| 全局凸胞边界裁剪恰得 ∂E | **已证**：有限全维凸胞并，完全切分，两侧闭占据不同，取闭包 | 2D `.boundary` 不调用局部 VE/EV 筛选；各家庭独立 ray/side 门 |
| 原有效局部盖裁剪强完备 | **条件定理已证，普遍局部弱覆盖证明仍为草稿**；包含非严格/共线退化；实验核对不能冒充全域证明 | `test_local_clipping_covers_the_independently_built_cell_boundary`，六家庭区间并精确覆盖 |
| d(t,E)=d(A+t,B) | **已证**，不需凸性 | `test_distance_to_e_matches_independent_features` |
| PD_closed=d(t,∂E) | **已证**（t∈int E）；是完全分离下确界，最近边界点仍相触 | `test_global_shortest_exit_distinguishes_tight_contact_seam`；`test_m3_exit_oracle.py` 独立解析 L 并 |
| rho=d(t,O补集) | **已证其定义关系，未实现一般二维最小 rho API** | U 槽 rho=1/8、PD_closed=2 的独立闭式门；不能把 `.shortest_exit` 当 rho |
| 平移首入 | **已证**：闭凸胞射线区间最小非负端点，单点切触不丢 | `test_global_first_entrance_is_complete_without_body_predicates` |
| 三维固定方向第一非贯入根 | **已证**：开区间严格合并；相接端点保留 | 新旧 exact 值回放、独立 wall oracle、零调用及内部端点变异 |

### 1.1 三态没有被静默改写

实体三态为 **−1=E 外、0=E\O、1=O**；拓扑三态为 **−1=E 外、0=∂E、1=int E**。
原 `polygons_overlap_exact`、`g0_oracle.overlap`、`polyhedra_overlap` 及其精确版本是前者；
原 `entrance_membership_exact`/`entrance_topology` 已有后者。不是这次才发现两个实现矛盾。

最小反例：A=((-1,0),(1,0),(1,1),(-1,1))；
B=((-2,-1),(2,-1),(2,3),(1,3),(1,0),(-1,0),(-1,3),(-2,3))。
t=(0,1) 时实体=0、拓扑=1；t=(±1/8,1) 时实体=1；t=(0,3) 才是真边界。
三矩形闭式 oracle 不用被测代码的任何几何原语。

### 1.2 与正本及文献的对应

只读正本00 §3.2–3.3/§4、01命题1–8、03 K1–K5及计划、canon_map已核。
00 §3.3 原裁剪细节未核，本单只称“本仓库给出的一种严格化”；01命题5仍在凸域，不能把未裁剪局部盖当凹体∂E。
01命题3(ii)对应 PD_closed，不对应任意 rho；命题7几何首入/全局出口不证明接触力唯一性、K4开闭收敛。
K1是配置空间约化，K2是标签边界，K3是首入选择；不宣称已复现K5“角的代数”。

文献逐项状态：Guibas–Ramshaw–Stolfi1983 **未核原文**；Kaul–O'Connor–Srinivasan1991 **未核完整原文**；
Wein2006 **已核同名 ACS 原稿**；Behar–Lien2011 **未核原文**；Hachenberger2009 **未核论文完整原文**；
Hachenberger 的 CGAL 3D Minkowski Sum 官方手册相关章节 **已核原文**。具体版本、链接及可支持范围见理论审计§7。
有效 VE/EV 与 reduced convolution 的方向筛选相关，但没有核证逐条一一等价；不将其作为本实现证明依据。

## 2. 实现与调用点

### 2.1 二维

[`src/eab/kernel2d/global_entrance.py`](../../src/eab/kernel2d/global_entrance.py)：

- `GlobalEntrance2(A,B)` / `global_entrance(A,B)`：简单环、精确耳切、三角片对差点凸包。
- `membership`（实体）、`topology`（E 拓扑），全部 Fraction 判定。
- `subdivision`：显式相对开 0/1/2 维胞及状态，外部无界区隐式为−1；E可有洞。
- `clipped_covers`：每个有效 VE/EV 的来源标签、子段、暴露标签、精确双侧探针。
- 来源标签的顶点/边索引对应自动归一CCW的`self.A/self.B`，不承诺保留顺时针原始环的索引。
- `boundary`：从**凸胞边界**独立构造，不拿局部盖假设循环证明自己。
- `distance_to_e`、`shortest_exit`：精确平方距离、最近点及 `tied_exact_points` 全部并列最优点。
- `ray_intervals`、`first_entrance`：精确区间和首时刻；float显示仅经 construction.py。

二维生产 `exact.entrance_membership_exact` 改用全局拓扑，凹体 `entrance._first_entrance_concave` 的实体裁决改用全局成员。
旧局部候选“漏了更早首入必须报错”的门仍保留；新全局首入 API 本身不依赖局部候选。
旧 `shortest_exit` 兼容 API 仍是局部选择，明确不冒称全局出口；一般 `polygons_overlap_exact`/`geom.polygons_overlap`、
G0 和 `first_entrance_brute` 保留为独立/历史核对用途，没有把 oracle 反过来接回新构造。

### 2.2 三维

[`src/eab/kernel3d/global_entrance.py`](../../src/eab/kernel3d/global_entrance.py)：
`convex_decomposition`、`global_entrance`、`GlobalEntrance3D.classify/line_sections`、
`LineSections3D.classify/first_nonpenetrating`。
非凸体使用有界面片精确 BSP（可有 Steiner 点），凸胞有有理内点及半空间/体积证书；可证凸合并减少片数。
凸片对闭/开 SAT 区间只用本模块几何；精确平移归一缓存和公分母整数投影不改变模型。
非平面输入环采用现有 API 的确定性投影耳切曲面合同，但不 import 其几何实现。
刚体协变的对象是固定三角曲面或平面面环；非平面环旋转后重新投影耳切可能改变所代表的曲面，不承诺这种重新建模仍协变。

`interlock._nonpenetrating_at` 改用全局射线标签，保留已有 surface_events/候选/证明框架与历史变异护栏。
这不是删除所有接触事件代码，而是判决不再调用暴力相交谓词。
没有实现三维显式全局边界、三维盖裁剪或一般三维拓扑 int E API。

## 3. 门与冻结证据

### 3.1 零失配矩阵

| 2D geometry | probes | mismatches | seconds |
|---|---:|---:|---:|
| bb52_historical_1260 | 1260 | 0 | 2.930 |
| thin_L | 561 | 0 | 0.342 |
| slot_wedge | 833 | 0 | 0.523 |
| interlock_section | 1213 | 0 | 1.010 |
| tight_fit | 873 | 0 | 0.591 |
| pocket_hole | 3349 | 0 | 5.669 |
| collinear | 2157 | 0 | 3.125 |
| star_0_scale_1_1000 | 1757 | 0 | 1.962 |
| star_0_scale_1_1 | 1757 | 0 | 1.833 |
| star_0_scale_1000_1 | 1757 | 0 | 1.834 |
| star_1_scale_1_1000 | 2025 | 0 | 2.462 |
| star_1_scale_1_1 | 2025 | 0 | 2.283 |
| star_1_scale_1000_1 | 2025 | 0 | 2.235 |
| star_2_scale_1_1000 | 1925 | 0 | 2.572 |
| star_2_scale_1_1 | 1925 | 0 | 2.185 |
| star_2_scale_1000_1 | 1925 | 0 | 2.124 |
| **TOTAL** | **27367** | **0** | **33.680** |

| 3D geometry (lazy convex-pair probes) | probes | mismatches | seconds |
|---|---:|---:|---:|
| L_prism | 280 | 0 | 1.929 |
| zero_clearance_pin | 264 | 0 | 1.833 |
| closed_cavity | 617 | 0 | 3.049 |
| TIA_nx3 | 877 | 0 | 7.211 |
| twisted_prism | 430 | 0 | 1.541 |
| random_concave_7_scale_1/1024 | 607 | 0 | 3.201 |
| random_concave_7_scale_1 | 607 | 0 | 3.138 |
| random_concave_7_scale_1024 | 607 | 0 | 3.180 |
| random_concave_23_scale_1/1024 | 607 | 0 | 3.327 |
| random_concave_23_scale_1 | 607 | 0 | 3.259 |
| random_concave_23_scale_1024 | 607 | 0 | 3.096 |
| **TOTAL** | **6110** | **0** | **34.762** |

二维证据脚本：[m3_scan_evidence.py](../../tools/m3_scan_evidence.py)，结果 [scans2d](M3_evidence/scans2d/)。
家庭/星形扫描包含该次构造全部剖分顶点、边中点、面内部样本、每条边的精确双侧事件探针，0排除。
**bb52 是历史21对×60的1260平移重放，不是21对全部巨大剖分的穷尽探针**；此缺口没有被“零失配”掩盖。
最大 bb52 对有1344个凸胞、4428条不同胞边；未对这个完整安排宣称已验收。
三维记录的是全部 **lazy 凸片对候选胞** 顶点/真棱中点/支撑面心及事件双侧，不是显式三维 overlay 的全部胞。

### 3.2 oracle 独立性、强完备与推论

二维主 oracle import 清单：`eab.oracle_construction.{sqrt_exact,scalar_exact}`、`fractions.Fraction`、`math.lcm`；
自身用整数绕数、边交及有理事件，不 import 盖、凸分解、全局构造。输入几何/采样坐标共用不是共用裁判。
三维 `geom3.polyhedra_overlap→exact_geom` 与 `e5b_wall_oracle→e5a2_surface_oracle` 用原表面分区/射线方法；
新模块不调用这些原语。完整AST import清单见 [二维扫描汇总](M3_evidence/scans2d/summary_all.json) 的 `oracle_imports` 及 [三维汇总](M3_evidence/three_d_summary.json) 的 `oracle_import_inventory`；适用边界另见 [理论审计](M3_evidence/theory_audit.md)。

强完备门逐暴露/不暴露段核独立拓扑 oracle，精确双侧分别分离/非分离；pytest固定8方向×6家庭，另证据脚本15个非bb52配置复用种子固定的12个随机有理方向，共180条射线（不是180个独立方向），独立oracle的出口全部落在暴露段与全局边界上。
六家庭每条独立生成的全局边界均由局部裁剪段并精确区间覆盖；反向以逐局部片中点及精确双侧oracle确认，不冒称另做了反向区间并算法。
距离用独立原体边特征平方距离；全局出口对 U 槽及非对称 L 并独立闭式验证。后者不是全部凹体穿透深度独立大扫描。

### 3.2a 逃逸逐值回放与零调用

[新旧逐字段对账](M3_evidence/three_d_replay_comparison.json)：392组完全相同输入，`input_sha256 / exact_height / exact_offset / state` 共1568字段对照全部相等。高度和偏移按Fraction精确序列化比较，没有浮点门限。
旧实现暴力谓词调用10761次，新实现0次；pytest另有打桩一旦调用即报错的门。旧实值来自起点HEAD的本树tmp导出，不运行其他工作树。

| 旧门输入族 | 实际回放数 |
|---|---:|
| wall（含window） | 240 |
| TIA | 50 |
| 单位尺度 | 16 |
| grid/audit | 5 |
| 局部规则反例 | 3 |
| 刚体/平移不变性 | 72 |
| window位移/再入 | 6 |
| 合计 | 392 |

这是392个实际输入，不冒充全部逃逸pytest节点数；所有原门是否保留且执行由第四节完整节点账证明。
独立`e5b_wall_oracle`看护解析高度，旧新实值相同另属回归证据，不把旧实现升级为独立数学证明。

### 3.3 数值、不变性与变异

2D 三档2^-400/1/2^397解析六边形逐字段对拍；3D三档2^-400/1/2^400非立方盒独立Cartesian参考核`parts_a`顶点/内点及射线端点。`parts_b`逐字段、faces有序子集和一般BSP Steiner点尚未完成全部独立三档对拍，不能称三维构造量数值验收完整。
有理旋转、独立大平移、单位缩放；精确证书不受binary64范围限制，显示越界响亮报错。
登记见 [r13fix_construction_inventory.md](../../docs/r13fix_construction_inventory.md) 的M3增量。

独立审查发现并修正：多最短点时，字典序单见证不是旋转协变量。
现在公开完整 `tied_exact_points`；距离与最优点**集合**协变，唯一最优点才保证单见证协变；字典序代表明确无该承诺。
人工竖直剖分的线段本身亦不旋转协变，协变的是其代表的集合与成员标签。

真实隔离子进程内部变异：[脚本](../../tools/m3_mutation_evidence.py)、[汇总](M3_evidence/mutations/summary.json)。
均先编译修改被测函数，再跑未包裹的守卫测试；9项均实际 pytest exit=1，命中预期 AssertionError；源文件从未被突变覆盖。

| 内部缺陷 | 正确报红断言 |
|---|---|
| 去掉局部盖裁剪 | cover clipping exposure mismatch |
| 成员标签取反 | body label mismatch |
| 闭区间退化端点改成开端点 | isolated closed contact |
| 凸分解/胞对漏片（2D） | body label mismatch |
| 接触内缝的拓扑传播错 | topological label mismatch |
| 全局出口退回未裁剪局部段 | global exit cannot return the local zero-gap seam |
| O开区间相接端点错误合并（3D） | open interval endpoint must remain physical contact |
| 凸分解漏片（3D） | global3d physical-state zero mismatch |
| 逃逸根退回首个局部事件 | global root not local cover event |

## 4. 全套、静态与性能

**最终全套：12761 collected = 12761 executed = 12761 passed；0 skip。**
原12662个节点全部保留，新增99、删除0。四片派发/实际收集/call节点多重集逐项相等。
[最终运行摘要](M3_evidence/final_suite_r3/summary.json)、[独立汇总审计](M3_evidence/final_audit.json)、[验收矩阵](M3_evidence/acceptance_matrix.json)。

最终四片最后一行原样：

```text
3191 passed in 942.75s (0:15:42)
3190 passed in 746.55s (0:12:26)
3190 passed in 1596.41s (0:26:36)
3190 passed in 643.94s (0:10:43)
```

起点808216a四片最后一行原样：

```text
3166 passed in 604.85s (0:10:04)
3166 passed in 786.90s (0:13:06)
3165 passed in 617.81s (0:10:17)
3165 passed in 1487.11s (0:24:47)
```

| 实测量 | 起点 | M3最终 | 变化 |
|---|---:|---:|---:|
| collection＋四分片＋静态总墙钟 | 1661.06s | 1864.61s | +12.25% |
| 四片pytest报告秒数合计 | 3496.67s | 3929.65s | +12.38% |
| 静态扫描 | 152.97s | 199.77s | 两次均0违例 |

本次全套观察增量在“约15%”目标内；运行期同机并行负载不完全相同，不把这个比值当隔离性能基准或跨机器保证。慢片包含既有全仓库静态生命周期缺陷注入门，并未为降耗skip。

静态原始末行：`exact construction AST gate: 0 violation(s)`。
最后文档指针修复`0 rewritten; 0 kept`，指针与摘要门`3 passed in 0.09s`，见[原始日志](M3_evidence/final_doc_pointers.log)。
最终审计核235个关键输入（src/tests Python文件及配置/策略）与r3快照逐字节相同；收尾改动只在文档、证据和汇总工具，不把源代码差异解释成“等价即可”。

验证迭代未隐去：最初导出在强完备家族扩为六组后主动停止；第二次导出真实发现`canon_map`第三行摘要被新提示占用，`test_canon_current_static_summary_matches_r12fixb_local_policy`报红。仅把提示移到既有合同摘要之后，原断言未改，定向27项通过，再冻结第三次全套。前两次均标`ABORTED_NOT_GREEN`，不拼接成绿。[第二次原始失败日志](M3_evidence/final_suite_r2/shard_2.txt)。
收尾汇总器首次把Windows原始变异日志末尾空行当作结果行而报RED；仅订正末尾空白读取，仍逐项核真实`E AssertionError`及`1 failed`，现汇总GREEN。首次结果保留为[解析失败记录](M3_evidence/final_audit_initial_parser_failure.json)，不是生产测试失败或放宽数值断言。

运行器：[m3_run_gates.py](../../tools/m3_run_gates.py)。每片插件记录实际 collection 和 call-phase nodeid，比较多重集而非仅检查派发清单；0skip。
起点用只读 `git archive HEAD` 导出到本树tmp，最后用当前文件字节副本；没有 worktree/branch/checkout/clone操作。
**这不是提交后新鲜Git worktree，也不是独立六路G6**。源导出逐文件SHA-256在各套export_manifest。

静态既有3103项豁免没有增加，续期19项已有scope指纹：原 `R12b-L0106/0107/0108` 三项的候选/接触显示表达式未变，仅实体状态提供者改变；另16项仅因三段docstring订正。
记录：[static_renewal.json](M3_evidence/static_renewal.json)、[doc_only_renewal.json](M3_evidence/doc_only_renewal.json)。
没有通过新增整函数白名单把新几何隐藏出门。静态0也不代表全域数值形式证明。

复杂度：二维朴素耳切最坏O(n³+m³)，K≤(n−2)(m−2)个常数复杂度凸胞（共线点归并可减少），成员O(K)；
边界两两切分与逐子段两侧检查保守O(S³)，S为凸胞边数；朴素竖直剖分二次再切分的保守最坏界O(S⁶)，不借用文献最优算法复杂度。
三维面平面安排最坏O(f³)胞，当前BSP、精确凸合并及SAT笛卡尔积可昂贵；有理位数增长另计。
这是研究级精确实现，不宣称工程实时。具体构造/扫描用时在各JSON；15%预算以全套实测比较，不能用小单元门时间代替。
392输入旧新回放176.688s→651.757s（3.689倍）；两次执行存在同机并行负载差异，不是隔离性能基准，但新精确BSP/SAT路径明显昂贵，不能宣称性能问题已解决。代表性的旋转TIA有68面片/体，BSP58片后凸合并到29片/体，构造约6.4s、29×29对射线SAT约19.4s。没有靠退回暴力谓词或局部规则规避成本。

证据落盘无新增大于5 MB文件进入提交候选路径。tmp中28个超过5 MB文件均为四份验证导出内的历史证据副本，完整路径/字节数/SHA-256见 [large_artifacts.json](M3_evidence/large_artifacts.json)，不提交tmp。回退锚为起点HEAD及其逐文件哈希导出，不自动覆盖当前修改。


<details>
<summary>tmp历史大文件副本的SHA-256（完整路径见上方JSON）</summary>

| File basename | Bytes | SHA-256 |
|---|---:|---|
| `baseline_HEAD_30ee153.zip` | 41426553 | `64bcb8a0c52e077d6898a750f7f2f0a851ae109b474c4af18d8b790aef6ffb8b` |
| `baseline_tracked.zip` | 9923570 | `5a131b90b248ca092a71c378f7cf775dd2dd18e3ca1703bd5d8ab7e5d3f533ef` |
| `baseline_tracked.zip` | 20432135 | `e350b679a2d737d3722c543b6320db2e4085b69719cb3bb1ad0b5acc7c883c7a` |
| `baseline_tracked.zip` | 83250278 | `712c08cd74e23ecdc54b287e4eea9b5e694005e8782d7f7f2e192c9c2bd48baa` |
| `exact_construction_policy.json.txt` | 20573320 | `115f74bf16f1cf9b4d9141441d13186ede28d0fc5be924531abf8738221e697a` |
| `test_driver_helpers_positive_subset_review.json` | 8959769 | `db4784615a443fa5a69ff50ed79b86fd0d4d8baf1d9ef2a939235e442ea9a958` |
| `test_final_waiver_review.json` | 5466459 | `0322e554cfa491d6c485b8397cf4eb63f5c1bc79477ebaa939463db1031496d0` |

</details>

## 5. 新发现与文档收尾

1. 双三态是已有正确区分，不是新bug；正本/旧概述里笼统“相触=∂E”的泛化必须限定。
2. 接触内缝上局部gap=0不能当global PD_closed；多解单见证旋转协变不可无条件要求，已补集合输出。
3. Xbloc **已找到可靠公开尺寸**：Bakker/Klabbers/Reedijk，Terra et Aqua94，2004，Figure7，D、D/3、圆角r=D/19；
   [作者原文](https://www.iadc-dredging.com/wp-content/uploads/2017/03/article-introduction-of-the-xbloc-breakwater-armour-unit-94-01.pdf)。
   未完成三维拓扑转写及圆角离散合同，故**未建模/未跑门**，不是“没有公开尺寸”。
4. README和canon_map不存在的第五轮Markdown报告引用改为“只留原始JSON”；计划补记M4b结果，来源为现有M4b报告，不冒称本单重新验证b-DDA。
5. `fix_canon_ptrs.py --apply` 和文档指针门随最终源码位置重跑；README测试计数按实际collection更新。

## 6. 遗留、下一步及退出判断

- 二维算法/API已实现，但bb52全部大安排的顶点/边双侧穷尽探针未完成；原局部盖普遍弱覆盖证明仍为草稿。
- 三维只有lazy凸片并，无显式overlay、∂E、盖裁剪/强完备，旧g03相交出口跳过缺口未关闭。
- 三维嵌入无自交表面为输入前提；局部manifold/体积证书不等于完整自交检测，不能称所有域外输入都已响亮拒绝。
- 三维`parts_b`、faces有序子集及通用BSP Steiner构造分支的独立三档逐字段对拍不完整；精确Fraction及静态0不能替代此合同。非平面环重新三角化的刚体协变不在保证域。
- Xbloc转写未做；一般最小rho、SE(2)/SE(3)未做。旧局部出口兼容接口没有偷换合同。
- 未执行所有者验收和独立六路G6，且按工单未新建Git worktree；不能宣布M3里程碑完全退出。
- 若大型剖分仍遇性能墙，下一步先可证凸合并和空间索引、事件扫描；不能退回浮点阈值或局部gap假规则。

M3_PARTIAL：bb52完整剖分探针、局部盖普遍弱覆盖证明、三维显式边界/强完备及完整数值逐值审计、自交输入完整拒绝、Xbloc转写、独立G6未完成；性能预算另见第四节。
