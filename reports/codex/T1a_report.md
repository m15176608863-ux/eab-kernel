# WO-T1a：Python 二维裁判返修与退化形貌网格

**结论：tia2d-2返修、114例正式语料、独立解码回读、无Git副本与完整快档/四分片均已通过；这是带精确证书的刚体接触/极限分析裁判，不是真实材料承载力预测或新的形貌设计发现，P2同相族退化，按裁定以PARTIAL交付。**

用白话说：程序把石根华接触理论中的局部入口锥——接触处哪些方向不发生贯入——做成精确分数计算和可复验证书，并用于岩体以外的拓扑互锁砌块。G1/G5 的手算闭式与原生产结果一致，Claude 的独立求解器也复核了 264 个 LP 及证书、未找到错数；这项独立验收结论来自所有者提供的综合报告，不冒充本轮自产结果。本轮证据另行生成，具体见下文。

这支持“通用刚性块体组装的精确前端已在外域算例上接受检验”，**不支持“原创理论成功外推并发现新的科学规律”**：模型不能预测真实材料峰值；G2–G4 网格没有获得形貌依赖；真圆格的多边形化会增加不安全伪互锁；有限运动、公差、破裂均未研究。程序此处明确不走盖分解。关于局部入口锥与机器人学 C-障碍的相近性、以及盖分解的原创性地位，仅沿用所有者的研究判断，具体归属以[归属总表](../../docs/shi_attribution.md)为准，不自行扩大历史优先性主张。非退化形貌族与真正需要盖分解的问题转后续研究。

## 1. 范围、锚点与验收层次

- 工作树：`D:/eab-wt/cx-e2`；本轮开工 HEAD 为 `b0c1cbf8043e48b02070f814d121ffa987a62f09`，即 Claude 暂存的本地提交。本轮是在其上返修的**未提交工作树**，没有 commit/push/reset/checkout/stash/worktree/branch 等 Git 写操作。
- 钉版设计 SHA-256：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`；设计正文未改。获批差异仅 §10 两条。
- 本轮额外获准写入 `D:/eab-evidence/reports/codex/T1a_evidence/` 作原字节归档；其他工作树和姊妹仓库保持只读。回退锚点为 b0c1cbf、原字节 SHA 清单及外归档，不执行自动 Git 回退。
- 批准版为 **CLAUDE-APPROVED-TIA2D-2 / 2026-10-19**。Claude 将从 fc9675c 重建干净提交；**来源提交待 Claude 重建后登记**。实际源码字节由每批唯一 SHA 清单绑定，不把 HEAD 误称为全部工作字节。
- 五路独立对抗验收已经执行，定级**有条件通过**；本轮修复后的独立复验、所有者安排的新鲜 Git 树最终核验仍待所有者确认。当前树测试与无 Git 字节副本都不能替代该最终确认，不宣称 C3 已合入。
- 本轮计划与验收清单：[返修计划](T1a_evidence/accept_fix/plan.md)。成功条件是批准语料/读取器、负门、仓库卫生、无 Git 复现、纯度/静态零诊断及完整快档/四分片，不以过程性预检冒充收尾完成。

## 2. 模型口径及工单订正

`profile1`：刚体、小变形、无限抗压、无黏聚、恒定 μ、**关联流动**。其承载力相对非关联库仑摩擦给不安全侧上界；相应**正 μ_crit 为非关联阈值的下界，偏不安全**。μ=0 的结论不受两种流动法则之别影响；15/128、t 这类正阈值受影响。

全部算例无自重。TIA-G1～G4 无恒载；G5 有工单规定的端板预压 P，这不是自重。固定端无恒载的可行域是锥，刚体容量只为 0 或 UNBOUNDED；有限容量来自 G5 力控边界。**UNBOUNDED 既不等于锁定，也不是有限承载力。**固定措辞：“锥 = {0} 推出不可动；锥非零推不出可动”。SE(2) 有限运动、公差 TRAPPED、有限抗压 profile2、一般恒载研究不在本单。

| 编号 | 原工单问题 | 订正、证据与具名门 |
|---|---|---|
| C01 | G5 各点都进入有界最优集敏感性公式 | μ=0 先核回收锥，返回 singular / possibly_discontinuous，附射线、不输出斜率；2P 右导仅为闭式注记。`test_g5_production_switch_and_zero_friction_preserve_contract` |
| C02 | 放开端板转动反例 1/3 未声明约束锚点 | 面中点锚点 `[1,0,1]` 得 4/3；`[1,1,0]` 得 2/3；原点锚点 1/3 是不同边界的诊断。`test_g5_claude_approved_boundary_counterexamples` |
| C03 | Koureas 闭零阈误含 t=0 | t=0 是 μcrit=0 的**开阈**：μ0 精确 OPTIMAL0，任意 μ>0 无界；t>0 保留原闭式。`test_g1_zero_slope_owner_corrected_open_threshold`；[原精确反证](file:///D:/eab-evidence/reports/codex/T1a_evidence/resume/zero_slope_probe.json) |
| C04 | “表 2 范围 θ≤15°” | K22 表 2 在 p.9，仅有 θ=5°，不是 ≤15° 扫描；本单二进 t 扫描不是论文角度扫描。原文文本核读与验收综合报告 §7 均确认；属文献来源核对，**无数值生产门**，不伪造具名数学门 |

上述预期订正不改钉版设计合同。C03 的任意 μ>0 证书可取 `P*=max(1/(2μ),1/h)`，四面剪力 `(1/2,1/2,−1/2,−1/2)`，合力高度 `(0,1/P*,1/P*,0)`；端点分配给出非负 α=1 改进射线。t=0 与 A=0 的开零阈无界完全来自固定刚体之间的夹持自应力，不是实际有限强度材料的承载预测。μmax=0 时只能说域内无无界点，不宣称域外结论。

停止规则：工单预期/分类不符而设计不冲突时登记并继续；只有钉版接口/语义/状态/证书冲突或必须新增静态准入才停。当前未新增静态准入。

## 3. 八项裁判合同与门

通用模块在 `src/eab/kernel2d/`，域几何在 `src/eab/adapters/tia2d.py`；旧 `lp.py` 数学合同未改。以下文件均位于 `tests/`。

| 项 | 生产合同 | 门与本轮返修 |
|---:|---|---|
| 1 | `translation_lock_certificate`：单对/combined；OVERLAP 成功拒签，不入四状态；OUTSIDE 不贡献；局部胞/切锥、S¹ 三类精确覆盖、阻挡来源、严格有理半径；仅不可分离细化 | `test_lock_all_states_and_refinements`、`test_lock_independent_sector_oracle`、`test_lock_koureas_pairs_removable_combined_seam_not_immobile`、`test_lock_radius_is_strict_and_excludes_outside_neighbors` |
| 2 | `assemble_contact_set2`：t=0 原 VE/EV 含端点；按接触点 F_p 取边界，极大共线段两端、同向去重、作用反作用一次；实际 twist/mask/anchor 的齐次精确 LP 才能证 VV 禁止开锥不可达 | `test_tia2d_contacts.py` 回归 a–f；平坦内部点保留 boundaries/sources、retained=false；真 VV 未解析和已证冗余不混同 |
| 3a | `limit_load_ideal_exact_2d`：未归一化 g±=N±μT；原 exact A/b/c；冻结参考点、活载在 A；辅助精确 LP 给可行 x0、改进 r 且 rα=1，另保留 Farkas | `test_unnormalized_generators_and_live_column_are_preserved`、`test_auxiliary_certificates_do_not_decode_float_rays`、`test_unbounded_certificate_ignores_poisoned_float_ray`；D17 条件传播 |
| 3b | `evaluate_sensitivity2`：稳定基原始 x/y；两侧最优集回收锥；有界时 Mills/Freund；临界基隐式导数必须有对应延续证明 | `test_tia2d_sensitivity.py`、`test_tia2d_critical_acceptance.py`；无基为 unresolved，域边界原因准确，无导数显示 NOT_APPLICABLE |
| 4 | `critical_parameter`：只对 μ 单调二分；binary64 严格内点/相邻终止；Cramer 多项式与 Sturm 根数证延续；无精确阈值证据不造 attained 或斜率 | C1/C2/C11/C10/C9 真实源码变异均被语义断言检出；二分终止与证明原因独立保存 |
| 5 | `first_order_free_twists`：只法向；满列秩及归一化精确 LP；双描述含线性空间两向，零锥给 ±e 非负旋量组合；未解 VV 不给结论 | `test_first_order_cage_zero_has_full_rank_normalized_lp_and_both_sign_certificates`、`test_double_description_matches_independent_cofactor_oracle`、`test_first_order_bare_corner_both_apis_remain_mechanical_unresolved` |
| 6 | 批准 [tia2d-2 schema](../../docs/eab2_case_v1_tia2d.md)：bits/n/d、三状态层、六查询族、几何种子、非唯一证书比对合同、唯一来源清单、逐查询墙钟 | cases/export/readback/seed/fixture 门；独立解码不导入编码函数，但复算仍调用生产查询，不称独立力学求解器 |
| 7 | 数值输入：共享界面一次构造/一次 RN；binary64 恒等子集、实际顶点 CONTACT/共线/平行/凹角核验；纯有理族分目录 | `test_tia2d_assembly.py`、families、seed 门；部分掩码必须显式 dof_anchor，改变 o 同步变荷载后实际约束与 LP 不变 |
| 8 | profile1、ideal_exact_2d、边界/函数/对象名与状态串冻结；call_status / mathematical_status / display_status 分离；未知不变 false，无效数不填 0 | `test_null_observables_never_claim_exact_display`、`test_domain_lexical_classes_reject_real_source_injections`、`test_optional_git_provenance_does_not_inherit_a_parent_checkout`；普通词只增 differentiability，精确模块数47 |

`ContactSet2` 拒收 OVERLAP 后的空接触记录不表示“已证明无接触”；必须先看拒收状态。一阶未解的 matrix/rays/lineality/generators/zero_certificates 才是未计算的 null，不能读成空零锥。

一般代数阈值完整隔离后置；非 binary64 精确点只放 exact_threshold，不塞 double 字段。普通有宽括号若没有独立精确开闭证明，attained=null。无界端有精确可行点+射线；低端有精确驱动机构或 Farkas。全域不可行明确 `INFEASIBLE / infeasible_on_domain`，未解接触传播 `contact_set_unresolved`，不错误写 bounded_on_domain。

### 3.1 D17：真 VV 的运动学冗余不代表静力保留

profile1 中，运动学冗余已证的真 VV **不计入力**，不是把它改成两条摩擦半平面。相关 limit/critical/sensitivity 的 validity_conditions 必含 `true_vv_excluded_from_statics`。回归 c 增加 μmax=2 变体：在 μ=2 返回 **OPTIMAL、精确容量0**，域[0,2]仍有界、mu_hi=null，下端精确机构保留；若诊断性地保留该角点为摩擦半平面，μ>1 会变成 UNBOUNDED，μ=2 的精确可行点/射线由具名门核验。两种模型在 μ>1 分歧，不能用原 μmax=1 的相同结果掩盖此规则。

具名门：`test_regression_c_mu_max_two_excludes_kinematically_redundant_vv_from_statics`，自产[变异与合同证据](T1a_evidence/accept_critical_mutations_03/handoff.md)。

## 4. TIA-G1 / G5 主数据与闭式

本节主参数和数值沿用已获独立验收确认的**历史 48 例诊断**，不把旧墙钟/旧输出字段当本轮新 schema 的结果：[中文表](file:///D:/eab-evidence/reports/codex/T1a_evidence/p0_diagnostic_20261019_01/README.zh.md)、[精确诊断](file:///D:/eab-evidence/reports/codex/T1a_evidence/p0_diagnostic_20261019_01/diagnostics.json)、[CSV](file:///D:/eab-evidence/reports/codex/T1a_evidence/p0_diagnostic_20261019_01/table.csv)。诊断不是 eab2.case.v1，正式语料另见 §6.3。

| 族 | 参数与边界 | 原精确结果 |
|---|---|---|
| TIA-G1 Koureas，15 例 | l=2；h={1,3/2,2}；t={0,1/32,1/8,1/4,17/64}；块1/5固定，块3向下单位力 | t=0 开零阈；t>0 闭零阈 |
| TIA-G1 取向，8 例 | h=1；t={0,1/32,1/4,17/64}；未反转/只反转 I1 | t>0 阈值为 t，前开后闭；t=0 均开 |
| TIA-G1 细长，1 例 | t=1/4，h=1/4，l=2 | 闭阈 15/128 |
| TIA-G5 主例，12 例 | N=3/5/7；h=P=宽度=1；μ={0,1/4,1,2} | 下表 |
| TIA-G5 变化，9 例 | h=3/8、3/2 及 P=1/4、2 各两档 μ；另对称不等宽 | 均吻合实际顶点闭式 |
| TIA-G5 边界，3 例 | N=3，μ=2；释放竖向/面中点转动/原点转动 | 2/3、4/3、1/3 |

主数据实际使用非对称参考点 `(5/8,−3/8)`；边界、mask、anchor、dead/live、参考点、xy_bits 与版本逐例明确。历史 48 例的 RN 恒等、预期 CONTACT/OUTSIDE、平行/无新增凹角均通过；432 个接触点均 CONVEX。原诊断监测清单曾漏 assembly.py/critical.py，不把当时局部 SHA 不变称完整依赖快照；新正式批使用完整源码清单，不篡改历史证据。

### 4.1 G5 两模式闭式自行推导

对称两半各承担 F/2，竖直界面水平压力 P 恒定，摩擦要求 `F≤2μP`。左支承到中块左面距离 `(L−b)/2`；法向合力高度差 `F(L−b)/(4P)` 不能超过 h，所以 `F≤4Ph/(L−b)`。反之，两式成立时由支承底边沿半链按剪力/P 线性提升合力高度，中块两侧同高；端点法向压力非负，剪力按压力比例分配，力/矩与摩擦约束全部成立。因此

`F=min(2μP,4Ph/(L−b))`，`μswitch=2h/(L−b)`。

P=0 时无压力/黏聚，F=0。等宽 N=3/5/7 的铰接项分别为 `6Ph/L`、`5Ph/L`、`14Ph/(3L)`；μswitch 是模式切换，不是无界阈值 μcrit。

| N（L=N，b=h=P=1） | μ=0 | μ=1/4 | μ=1 | μ=2 |
|---|---:|---:|---:|---:|
| 3 | 0 | 1/2 | 2 | 2 |
| 5 | 0 | 1/2 | 1 | 1 |
| 7 | 0 | 1/2 | 2/3 | 2/3 |

主例均 OPTIMAL，零容量不是 INFEASIBLE；G5 在所查 [0,4] 有界，mu_hi=null，不声称域外永不无界。端板仅轴向自由，dof_mask=[1,0,0]、dof_anchor 为面中点；换 mask 则闭式失效。`test_g5_two_bidirectional_guides_independently_match_mask` 以旧 limit_multi 的两对无摩擦 ±ey 导轨核对新 LP mask；正式语料另有自由体侧向恒载的 INFEASIBLE/Farkas 角色，不伪造 G5 主族不可行点。

### 4.2 G1 分类与阈值

Koureas 取向 t>0 且 `h/l≥t/(1+t²)` 为闭零阈；细长段 `μcrit=t−(h/l)(1+t²)` 为闭阈。未反转为 t 开阈，只反转 I1 在 t>0 时为 t 闭阈；t=0 各取向均为开零阈特例。闭式只作实际顶点参考，不倒灌生产认证。

历史 10 次二分代表：细长括号 `[119/1024,15/128]` 与精确闭阈 15/128；未反转 t=1/4 为 `[1/4,257/1024]` 与精确开阈 1/4；只反 I1 为 `[255/1024,1/4]` 与精确闭阈 1/4。这是历史有限预算，不是本轮固定 64 步正式字段。

历史 48 例多体一阶均 NONZERO_CONE；192 个逐体平移查询为 140 缝滑、52 可分离。Koureas 块2/4对单个邻体可移除，combined 为 SEAM_SLIDING；块3可上移。未反转代表三个内块均可平移移出，块2可以掉出；G5 内块均竖向缝滑。因此所述 G1/G5 不存在单块互锁，不绘其“互锁设计曲线”。本轮另把逐体一阶与单对 lock 补入正式语料。

## 5. P1 敏感性与临界基认证

稳定基用原始未缩放 exact_x/exact_y（Aᵀy≥c），`dV=xᵀdc+yᵀ(db−dA*x)`，不使用旧 limit.py 的显示 lambda。非稳定基先检查原/对偶最优面回收锥；非零报 singular/possibly_discontinuous 并附射线。两侧最优集有界才用 Mills/Freund，对 ±d 同时反转 dA/db/dc：右导 D+，左导 −D−，不能直接比较两次 LP 值。

人工非退化例与 `test_min_max_mapping_and_reverse_query_sign_on_tied_optimum` 分别核稳定基及 min/max 映射；`min p*x1, x1+x2=1` 在 p=0 正向导数为 0 而非 1。共享参数传播顶点、T/N、力矩与荷载列，do≡0；活载在 A 中，不能只改 RHS。有效条件使用精确固定串 `L1接触骨架不变`。

| 区域 | dF/dμ | dF/dP | dF/dh | 裁判路径 |
|---|---|---|---|---|
| 滑移，μ>0 | 2P | 2μ | 0 | Mills/Freund |
| 铰接 | 0 | 4h/(L−b) | 4P/(L−b) | Mills/Freund |
| N3，h=P=1，μ=1 | 左2、右0 | 两侧2 | 左2、右0 | μ/h 为 one_sided；P 为 smooth |
| μ=0 | 不输出 | 不输出 | 不输出 | singular 与回收射线；2P 右导仅闭式注记 |

**计数口径**：63 个主数据查询 = 21 个主例 × μ/P/h 三参数，为 52 smooth、2 one_sided、9 singular；另有 3 个放开掩码反例的 dF/dμ，均 smooth 0。合计 66 个 G5 敏感性查询，为 55/2/9，不能把 63 和 66 混用。闭式 sliding/hinging 标签仅置于 informational 显示注记，不再倒灌裁判 tied_labels。

阈值导数在仍于临界点有效的证书端取 φ：闭阈取改善射线分量，开阈取机构非基 slack，不用开阈时发散的原侧接触力。必须先有该端基延续证明；None 表示无证明，空 signs 只表示退化区间，不能混同。临界点比值须非负，φμ=0 或基奇异才报 singular；`critical_basis_unavailable` 按设计报 unresolved。所有越零分量逐个计算并保留并列标签/有效方向，不任取首项。

本轮[14 项正阈值导数重核](T1a_evidence/accept_critical_mutations_03/threshold_slopes.json)全部 PASS：未反转/单反各三组 dt=1、dh=0，细长 dt=15/16、dh=−17/32。差商只作同基/同骨架收敛佐证，步长写 Δ，绝不从普通括号中点签斜率。

本轮[166 个非 μ 几何种子重构](T1a_evidence/accept_schema/all_geometry_seeds.json)覆盖原 91 例，t24、h47、P23、A36、λ36，22.869s；从原始顶点 ID、共享点、荷载与锚点 jets 重建全部原始 LP 种子并逐项精确相等。该项是种子传播证据，不代替最终批回读或全档。

## 6. P2：同相形貌族退化及曲面边界

### 6.1 历史扫描的有效内容与未取得的设计结果

三族局部 `p=(λu,A*s)` 经精确 90°架变为 `(x_k−A*s,λu)`；四面同相、同取向，块1/5固定，块3顶部 x=0 下压，基面 θ=0。**λ 就是块高（一周期占满）**，并非独立波长轴；这也不同于 K22/K23 的 θ=5°。所有共享面一次构造/RN 恒等，两侧共享同一组点。

| 族 | 固定表多边形轮廓 | 扫描 |
|---|---|---|
| TIA-G2 | (u,s)=(0,0),(1/2,1),(1,0)，2 段 | A={0,1/16,1/8,1/4} × λ={1/2,1,2} |
| TIA-G3 | u=i/8；256s=(0,169,222,248,256,248,222,169,0)，8 段圆弧表形多边形 | 同上；一般伸缩不是真圆 |
| TIA-G4 | u=i/8；256s=(0,181,256,181,0,−181,−256,−181,0)，8 段正弦表形多边形 | 同上 |

历史 36 格全部解析、1008 个 F_p 均 CONVEX。正幅 27 格的三个内块及多体均为一阶零锥，三个单体 TRANSLATION_IMMOBILE，μcrit=0 闭阈；零幅 9 格为直面缝滑/非零一阶锥，μcrit=0 开阈。因此 **μcrit 恒为 0，正幅的闭零阈是一阶不可动性的直接推论，没有得到形貌依赖，P2 设计网格退化**。非退化取向/相位/倾斜基面族转 T1b，不将本扫描写成已完成非退化设计曲线。

历史扫描：[36 格摘要](file:///D:/eab-evidence/reports/codex/T1a_evidence/resume2/morphology_scan/summary.json)、[逐例原字节清单](file:///D:/eab-evidence/reports/codex/T1a_evidence/resume2/morphology_scan/manifest.json)。原墙钟 67.518s、最大单例 738350 B；旧独立点积核过 18 最优证书、63 可行点/射线、972 零锥组合。此处保留原数学数字，不拿旧 reason/display 字段冒充修订后的结果。

### 6.2 边界导数与真圆格反例

三族 A=1/8 与 A=0、λ=1 的六格[原幅值再试](file:///D:/eab-evidence/reports/codex/T1a_evidence/resume3/amplitude_retry/summary.json)保留：正幅时 μ=0 所选满秩改善基分量严格正，无越零分量；μ=0 的 g± 重合也允许不同标签基。零幅处 L1 骨架改变。形式负 μ 延拓只作多项式诊断，物理域仍 μ≥0。

当前准确措辞是：**跨越基导数合同不适用于钉在定义域边界的阈值；裁判不认证斜率，但只要一阶不可动性保持，μcrit 局部就恒为 0。**生产原因是 `threshold_on_domain_boundary_without_proof`，不是“缺少精确阈值”；不新增“边界认证零斜率”分支。该分支留 T1b。允许诚实 unresolved 不等于本单取得了新的形貌设计结果。

**独立自产真圆格证据**：[全弧恒等式与多边形零锥证书](file:///D:/eab-evidence/reports/codex/T1a_evidence/accept_fix/curvature_probe.json)、[推导与具名门](T1a_evidence/accept_fix/geometry_repair_notes.md)。TIA-G3-A3-W0 的 A=1/4、λ=1/2，真圆半径 R=1/4，圆心依次 `(-3,R),(-1,R),(1,R),(3,R)`。五体关于全局原点的向上机构 twist 为

`(0,0,0), (R,3,1), (0,2,0), (−R,3,−1), (0,0,0)`。

四界面相对角速 `(1,−1,−1,1)`；块2/4反向转动、块3竖移速度2。对每个圆心 c、相对原点 twist `(a,b,w)`，整条圆弧法向功多项式

`(p−c)·((a,b)+w Jp) = (−cx*a−cy*b)+(a−w*cy)x+(b+w*cx)y`

的全部系数精确为零，不是有限采样。取反向机构，向下单位载荷驱动为 2，μ=0 接触功及固定支座功均为 0，故平衡要求 2F=0；零接触力与 F=0 可行，因此光滑真圆容量为 0。这是一阶/静力功证书，不是有限 SE(2) 运动证书。

而生产固定 G3 多边形及真圆的有理 2/4/8/16 弦内接多边形，全为 ZERO_CONE：9 DOF、秩9、每例18个 ±单位旋量组合证书均通过独立点积核验。**这四次加密仍保留不安全伪互锁，没有向正确光滑一阶结论收敛**；不能据有限四档外推所有 n 的定理。此反例只证明真圆格；其余椭圆、正弦格未做光滑对照，不作全称结论。其方向与 K22 p.13“曲面促进滑移”相反，因此撤回原来与 K23 曲面“定性趋势一致”的说法。

图件：[G5 容量与敏感性](T1a_figures/g5_capacity_sensitivity.png)、[G2–G4 退化网格](T1a_figures/g2_g4_design_grid.png)、[图注/SVG/PDF](T1a_figures/captions_zh.md)。图1d直接标 h−:2 / h+:0，不把 h 两侧误看成横轴 μ 两侧；图2纵轴为块高、一周期占满，明示退化与伪互锁限定。只读取冻结诊断、不重算；两 PNG 已目视核验，六图件均 <1 MB；PDF由同一Figure导出但未单独栅格核看，见[视觉 QA](T1a_figures/visual_qa.md)。

### 6.3 tia2d-2 正式语料与独立解码回读

**独立解码回读（复算生产查询，另以独立点积核证书）**：读取器不导入 codec 编码函数，独立 struct/Fraction 解码后重建生产调用，另用直接等式/不等式核证书。这不是另一个独立几何或力学求解器。Claude 五路验收中的独立力学复核与此读取器是两件事。

本轮正式目录：[tia2d-2 批次](file:///D:/eab-wt/cx-e2/fixtures/eab2_cases/tia2d-2/formal_20261019_02/)，[批清单](file:///D:/eab-wt/cx-e2/fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64/manifest.json)、[gzip 双 SHA 索引](file:///D:/eab-wt/cx-e2/fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64/gzip_index.json)。以下实测来自[正式批摘要](T1a_evidence/accept_fix/formal_summary.json)、[压缩清单](T1a_evidence/accept_fix/fixture_pack.json)、[导出进程](T1a_evidence/accept_fix/export_execution.json)和[首次回读进程](T1a_evidence/accept_fix/readback_execution.json)。加强后的读取器还须单独重跑，不能把首次回读当作最终增强验证；该项及完整收尾门留在 §9。

| 项 | 本轮合同 | 已完成批次实测（不替代最终收尾门） |
|---|---|---|
| 算例 | 原91含48主例、具名a–f共7例、36形貌格；Python-only另目录 | 114 binary64角色 = 原91 + 8覆盖 + 15逐体；另2个Python-only角色。7个alias组共16角色，不当作16个独立几何 |
| 查询/状态/F_p | 六族逐查询，逐点F_p、retained、来源；同一输入不同种子角色保留alias_of/role | 1086正式查询；114角色计1796 CONVEX、2 TRUE_VV、2 REDUNDANT_PROVED，共1800点；retained=true 1568、false 232 |
| 数值与种子 | bits小写16位大端、−0为8000000000000000；有理n/d约分、d>0、零0/1，拒NaN/Inf；geometry_seed含参数×原顶点×2及dead/live/anchor种子，dA/db/dc为派生期望 | 原91角色的166个非μ种子另已逐项精确重构（§5）；正式批首次解码通过；加强读取器的最终重核见§9 |
| 空值/状态 | 无显示数值NOT_APPLICABLE，未解一阶保留真实dofs及null数组；UNPROVED不变false；input_audit移到assembly哈希之外并真正计算凹角与预期接触 | call_status为1085 OK、1 UNSUPPORTED；display_status为777 EXACT、309 NOT_APPLICABLE；数学状态分布见下表 |
| 比对合同 | exact/set/verify_certificate/informational；x/y/基/射线/弧覆盖不要求复制Python解序；先按稳定标签对齐A/G列行 | 全部1086正式查询均携比对合同；首次解码回读PASS；增强证书核验另留最终结果，不以旧PASS代替 |
| 来源 | 每批一份实际src/tests/tools SHA清单；无Git时git_commit=null、原因no_git_checkout；源字节变化整批作废 | 导出进程398.985s、退出0，前后源码守卫通过；唯一source_manifest SHA为 `ec5d81cb0bfc6508eaf9b3e54481eca42a642f709d86cf098ad47af6177dd157`；来源提交待Claude重建后登记，无Git验证留§9 |
| 包装与回读 | JSON≤1 MB按完整查询拆分，gzip−9、mtime=0；内容SHA按解压字节，另有gz SHA索引；严格解码/证书核验/固定小子集重跑 | 165分片；解压80,343,492 B、单片最大999,453 B；gz合4,581,793 B、单片最大58,312 B；压缩索引SHA `887cca52e4463b795c3ec37e171c7fbaf231bf93bea0fc568eff2ad1c38db476`。固定小子集门及增强回读留§9 |
| Python墙钟 | 每个目标新进程一次，预构造按scope排除；冷调用不等于清OS缓存，未绑核、不承诺加速倍数 | 1086次目标调用合63.626092s，中位0.004284750s、最大1.889000300s；全导出398.984660s包含编排，不能拿其总时长作C++单查询目标 |

| 正式查询族 | 数量 | mathematical_status（不与call_status混加） |
|---|---:|---|
| assembly | 114 | 111 RESOLVED、2 MECHANICAL_UNRESOLVED、1 OVERLAP |
| first_order | 114 | 74 NONZERO_CONE、36 ZERO_CONE、2 MECHANICAL_UNRESOLVED、1 OVERLAP、1 UNPROVED |
| limit | 114 | 51 OPTIMAL、58 UNBOUNDED、2 MECHANICAL_UNRESOLVED、1 INFEASIBLE、1 OVERLAP、1 UNPROVED |
| sensitivity | 280 | 97 OPTIMAL、120 CERTIFIED、58 UNBOUNDED、2 MECHANICAL_UNRESOLVED、1 INFEASIBLE、1 OVERLAP、1 UNPROVED；这里不是differentiability枚举计数 |
| lock | 350 | 276 NOT_SEPARABLE_TRANSLATION、71 REMOVABLE_TRANSLATION、2 NOT_CONTACT、1 OVERLAP |
| critical | 114 | 108 CERTIFIED、5 UNPROVED、1 INFEASIBLE |

二分算法与 `param` 显式；max_steps固定64，midpoint规则是精确均值可表示则用之，否则落binary64网格并取严格内点。`bisection_termination` 不被 `threshold_proof_reason` 覆盖，input_resolution_limit保持认证括号而不降成UNPROVED。本批终止计数为15 iteration_limit、9 input_resolution_limit、90 null；阈值证明原因另为24 exact_basis_continuation、90 null。这些分别计数，不把“64步用完”解读成阈值证明失败。

首次解码回读的全116角色（114正式+2 Python-only）共1100查询，比较6,283,924个字段，核323个LP、122个Mills、656个锥和56个回收证书；读取器内部墙钟88.844865s，外部进程89.006478s。原样末行 `independent readback: 114 cases PASS` 只统计正式角色。这是首次读取器版本的证据；**最终加强版读取器结果已在§9单列**，不得与上述墙钟混称一次运行。

导出完成后，只加强读取器的族参数独立核验及未知顶层键拒收，不改冻结数据或生产数学代码；49项定向门通过。最终全批再次回读通过，内部85.737379s、进程85.923469s。导出时源码清单仍如实保留；后续验证器SHA另见[执行记录](T1a_evidence/accept_fix/strict_readback_execution.json)，不将历史来源清单改成当前哈希。读取器还独立重建单位μ种子、不回灌预期tied_labels，并拒绝将整个result降为informational的比较规则。

**历史计数仅供版本对照**：tia2d-1 原批为91 binary64+2 Python-only，934冷查询、139分片，最大994974 B；旧L3为45 OPTIMAL（23零、22正有限）、44 UNBOUNDED、2未解析；F_p为1466 CONVEX、2 TRUE_VV、1 REDUNDANT_PROVED。旧934查询目标墙钟和59.778s、全批375.710s、回读83.097s均是旧版本，**不是本轮C++性能目标**。当前C++性能目标只取本轮正式case/query明确scope的实测Python墙钟。

逐点 F_p 与 profile 适用性索引如下（计数针对原91个几何角色，来自[历史逐例摘要](file:///D:/eab-evidence/reports/codex/T1a_evidence/resume3/formal_summary.json)；本批全部114角色的1796/2/2计数已在上表另列，不与这张历史分族表混加；两张图仍只消费历史36个G5源数据行和36个形貌格，不冒称覆盖全部114角色）：

| 族/角色 | 接触点 F_p | profile1 适用性 |
|---|---|---|
| TIA-G1，24例 | 192 CONVEX | 解析；无恒载，仅0/无界及阈值 |
| TIA-G5，24例 | 240 CONVEX | 解析；有指定力控端板预压，可有限容量 |
| TIA-G2，12例 | 144 CONVEX | 仅此2段多边形，不能外推曲面 |
| TIA-G3，12例 | 432 CONVEX | 仅此8段多边形；真圆格有已证伪互锁局限 |
| TIA-G4，12例 | 432 CONVEX | 仅此8段多边形；光滑正弦对照缺失 |
| 具名回归7例 | 26 CONVEX、2 TRUE_VV、1 REDUNDANT_PROVED | b/e保持MECHANICAL_UNRESOLVED；c按D17排除静力 |

**每个接触点**的精确坐标、F_p类型、boundaries、retained、全部VE/EV来源、原始顶点/边ID均在新批各例 `assembly` 查询的 `result.points`，由批清单绑定，不只保留上面的汇总数。每例输入另冻结边界/mask/anchor、恒定参考点、dead/live、输入与schema版本。

### 6.4 验收覆盖缺口逐项交代

| 验收列出的缺口 | 本轮处理/仍缺失 |
|---|---|
| INFEASIBLE/Farkas | 增加自由体侧向恒载角色，精确Farkas；不与G5零承载混同 |
| lock NOT_CONTACT/OVERLAP | 增加分离方块和重叠拒收角色 |
| lock UNPROVED | **缺失**：正式语料未造自然有效输入的UNPROVED样本，不用内部异常注入冒充真实case |
| assembly OVERLAP/completeness_unknown | 增加显式重叠与未知完整性角色 |
| call_status非OK | 增加critical param=h的UNSUPPORTED；**INVALID_INPUT正式算例缺失**（输入数值拒收有单元门，不冒充有效assembly语料） |
| critical input_resolution_limit | 增加认证括号角色，并有C9终止/证明双原因门 |
| critical iteration_limit | `single_TIA-G5_body2` 在正式64次二分下自然产生该终止；小预算1–4步另外用于认证负门 |
| −0/CW/起点旋转/anchor≠reference/各体不同o | 新输入角色显式覆盖；原始bits与ID保留，不以规范环掩盖输入差别 |
| 单体first_order | 五族各三个内块，共15角色；其他所有体含端板一律固定，保留实际单体边界 |
| 成对lock | Koureas t=1/4块2/4对各邻体及一个G5内块对各邻体，另保留combined查询 |
| D17掩盖分歧 | 回归c扩μmax=2并明确true_vv_excluded_from_statics |

以上新增角色已进入本批114角色并完成首次解码回读；加强读取器及完整收尾门以 §9 最终清单为准。未补项如实列缺失，不宣称状态空间全部覆盖。

## 7. 文献对照：可比量、差异及证据等级

[原核读笔记](T1a_evidence/resume2/literature_notes.md)保留版本、页码与原文SHA；指定文本不拷入仓库，下载PDF不进提交路径。K22下列事实由原核读和Claude验收共同核对；K23/DB19的数字与公式明确标注来源等级，不冒称验收独立核对。

| 来源/可比内容 | 原文量或结论 | 本单量与解释 |
|---|---|---|
| [K22 arXiv:2207.01688v2](https://arxiv.org/pdf/2207.01688v2)，表2 p.9、图6 p.11 | h=1/1.5/2mm，l=2mm，θ仅5°；FE饱和摩擦读数μsat=0.4/0.6/0.8 | 本单t=1/4即θ≈14.04°，三高度闭零阈；角度不匹配，且刚体/FE不同，不能拟合或报误差 |
| K22 式A.4–A.6、图10 | 解析边界μreq(φ)=tan(φ−θ)，在由h_eff/l_eff定义的φ=β处取值 | 必须与图6 FE读数分开；无限抗压刚体可在几何允许域任取推力线方向，没有同一个β选择规则 |
| 最接近的细长刚体对应量，非论文FE峰值 | — | tanγmax=h/(l−ht)；t=1/4、h/l=1/8给4/31，tan(θ−γmax)=15/128，与生产认证闭阈相等 |
| K22 pp.5–6，二维取向/可移除性 | 不完全互锁；反转外侧界面用于自重完整性 | Koureas块3可上移、块2/4为缝滑而非单块锁定；主族 t>0 且 h/l≥t/(1+t²) 无自重下压μ0无界（不含t=0或细长例）。未反转三内块均可移出，块2可掉出；这才是成立的几何定性一致 |
| K22 图1e、8b及p.13 | 折线界面是自然比较对象；曲面促进滑移，曲面μsat=2而平面0.8 | TIA-G2可作折线多边形对应；G3真圆格却显示多边形伪互锁，不能声称曲面趋势一致 |
| [K23 arXiv:2212.06454v3](https://arxiv.org/pdf/2212.06454v3)，式4 | μeff=μ+μgeo，正弦形貌在低材料μ达到较高FE峰值；**引自 Codex 下载 PDF，验收未独立核对** | μgeo是FE映射的等效量，不是材料μ；本单θ0同相退化多边形没有形貌依赖，撤回原“定性趋势相同”比较 |
| [DB19 IJSS171](https://www.colorado.edu/lab/barthelat/sites/default/files/attached-files/ijss2019b.pdf)，pp148/150/152 | 恒轴向位移台钳、预压下滑移/铰接；相关数值/公式**引自 Codex 下载 PDF，验收未独立核对** | 本单恒P、刚体关联极限不同。G5 min闭式是本单推导，不署为DB19公式；仅“五块、θ0、预压”装置另获K22引用与图4佐证 |

FE与刚体差别不只是“参数不同”：K22饱和容量由弹性跳越、大转动和极限挠度约等于h决定，并使用圆角；profile1是小变形尖角、无限抗压。开零阈的自应力夹持不能与FE峰值等同。此处不新增未核的论文数字，不把局部一阶证书宣传成制造公差或破裂研究。

## 8. Oracle、内部变异、蕴含与元门

L1主oracle直接从两体接触入射边及反向构造临界射线和相邻L1和/rot90，在认证r处用 `polygons_overlap_exact` 分类；不读取 GlobalEntrance2 胞/排布，不调用 entrance_membership_exact。docstring明确共用原语与不重合路径。回归a–f分别守护锯齿两段/端点、裸VV未解、实际twist冗余证、平齐角0与1/2、同对VV+边不能按体对凸化、凸尖入凹口只取两法向。

既有八类内部变异继续保留：漏非凸整段、intE当O、VV析取改AND、∂E盖替t0骨架、生成元归一化、端点原关联作半平面、按体对判凸、仅平移证据丢VV。本轮新增六个**真实源码副本变异**均命中数学断言，不靠哈希、导入失败或后加假数据。自产[总清单](T1a_evidence/accept_critical_mutations_03/summary.json)：

| 变异 | 缺陷与具名门 | 变异进程原样最后一行（红为预期） |
|---|---|---|
| C1 | 闭阈跳过低端机构延续；`test_endpoint_states_do_not_replace_opposite_side_continuation` | `1 failed in 0.27s` |
| C2 | 开阈跳过高端射线延续；`test_low_budget_threshold_never_certifies_a_false_root` | `18 failed, 30 passed in 7.12s` |
| C11 | 忽略分子内部根；`test_branch_signs_rejects_interior_numerator_roots_even_when_midpoint_positive` | `1 failed in 0.19s` |
| C10 | 接受负约化成本机构基；`test_mechanism_basis_rejects_negative_reduced_costs` | `1 failed in 0.18s` |
| S7 | 丢对偶回收锥LP见证；`test_dual_recession_requires_the_lp_witness_not_only_lineality` | `1 failed in 0.18s` |
| C9 | 最后一次二分终止原因被覆盖；`test_last_allowed_bisection_step_retains_resolution_reason_and_proof_reason` | `1 failed in 0.28s` |

同一副本未变异基线 `113 passed in 10.78s`。小预算门对1–4步、多μmax核精确非二进/低位有理例：Koureas t=1/3,h=3/16真值11/48闭阈，未反转t=3/16真值3/16开阈，单反I1 t=5/16；只允许真阈值或不认证，不能靠正确端点状态制造错误阈值。

三蕴含仅对解析且使用同一ContactSet2：单体零锥⇒单体L3任意载荷无界；零恒载μ0时零锥⇔六基荷载均无界；只在i有活载时多体无界⇒其他全固定的单体无界。G5中块单体μ>0无界而多体有限反证逆命题。禁止“L3无界⇒锁定”。

元门对90°倍数旋转/反射/二进平移缩放要求精确不变，覆盖2^17大坐标、小特征与非对称实际参考点；随机旋转RN后重核新输入/实际矩阵，不强求旧分类。mask/anchor/o/荷载按各自语义变换。纯度精确47模块、真实源注入tia_block/tiaprism/TiaAssembly/differentiability_tia仍被拦；没有以放宽计数替代覆盖。

## 9. 仓库卫生、验证与复跑

### 9.1 文件布局与来源

旧大证据已按许可原字节外移：272文件、95,543,532 B，逐文件复制核SHA后移除工作树副本；[自产归档清单](T1a_evidence/accept_fix/archive_original.json)。第二批再归档81文件、962,073 B，包括resume历史诊断、前两次变异尝试及真圆完整证书，[二级归档清单](T1a_evidence/accept_fix/archive_secondary.json)保存逐文件SHA；两批合353文件、96,505,605 B。统一登记[外归档索引](../EVIDENCE_ARCHIVE.md)。这是本地归档，不是远端备份；不得覆写历史清单来迎合当前源码。

新正式批原始JSON/Python-only/计时进度另归档176文件、81,175,040 B，见[新批归档清单](T1a_evidence/accept_fix/archive_formal_v2.json)；历史门摘要另归档61文件、163,738 B，见[历史摘要清单](T1a_evidence/accept_fix/archive_historical_summaries.json)。四批合590文件、177,844,383 B，逐文件SHA已复核；工作树只保留新gzip语料、当前验证摘要及必要小型证据。

新binary64语料只保留 `fixtures/eab2_cases/tia2d-2/formal_20261019_02/` 一批 gzip−9/mtime0；JSON内容SHA与gz SHA分开，[fixture来源登记](../../fixtures/PROVENANCE.json)。Python-only及原始大运行证据另归档，不与正式binary64混放。图工具走 `frozen_evidence.data_path`（fixture优先，外归档次之）；冻结fixture快门做解压、SHA、严格解析与固定小子集实际重跑，不钉当前源码必须等于历史哈希。相对fc9675c实际候选文件的净增为 **6,761,647 B**，口径见[卫生清单](T1a_evidence/accept_fix/hygiene.json)。略高于约5–6MB目标：114角色比原91角色新增23个覆盖角色；没有为凑体积删除要求的覆盖、证书或图件。所有新增单文件均小于1MB；旧大blob历史仍由Claude重建清除。

来源清单在无Git副本中写 `git_commit=null` 与 `no_git_checkout`，而非调用失败或捏造SHA；Git档案副本覆以本轮返修字节的边界必须在运行记录说明。**来源提交待 Claude 重建后登记**，不得把b0c1cbf宣称为返修后完整源码提交。

### 9.2 当前运行与历史证据分离

本轮早期 coverage_reader 因 lock.display_status 不符失败、registry_preflight 因并行源码变化被完整性守卫作废；均保留FAILED_OR_INTERRUPTED原记录，不从已完成前缀拼成成功。历史完整快档8375/全档14351是旧版结果，不能给返修代码背书。

已完成的定向自产证据：几何/纯度/曲率快档 `121 passed, 39 deselected in 18.21s`（39慢档未执行）；临界源码副本基线113项及六变异如§8；原166非μ种子全部精确重构；图件语义门 `figure semantic gate: 36 G5 source rows + 36 morphology cases + 6 artifact hashes verified; 0 solver runs`。这些不替代下面的完整收尾门。

后续23个新增coverage/逐体角色已独立解码回读通过，其中8个coverage角色另完成cold_worker回读，见[覆盖回读第二次完整运行](T1a_evidence/accept_fix/coverage_reader_02.json)。最新集成定向150项通过（25.41s），morphology+retry含slow的50项通过（80.20s），本轮改动src/tests定向静态0诊断（6.84s）。这些是本轮局部证据，不冒称全库静态或完整快档已绿；最初失败的预检未被拼接或改写。

<!-- CURRENT_VERIFICATION_START -->
### 最终当前工作树验证（由完整运行实测填写）

| 门/产物 | 实测结果 |
|---|---|
| tia2d-2完整导出、一次性源码守卫 | PASS；114正式+2 Python-only，398.984660s；实测摘要见§6.3 |
| 加强版独立解码回读与全部精确证书 | [本轮完整加强回读](T1a_evidence/accept_fix/readback.json)：114 binary64 + 2 Python-only，1100查询全PASS；6,283,924字段、323 LP证书、122 Mills证书、656锥证书、56回收证书，进程85.923s |
| gzip fixture、逐文件SHA、固定小子集重跑 | 165分片已压缩并登记双SHA；固定9例实际重跑连同既有来源门共 `394 passed in 6.03s`，见[记录](T1a_evidence/accept_fix/fixture_target.json) |
| 无Git archive字节副本：0失败、来源null及原因 | [无Git验证](T1a_evidence/accept_no_git/summary.json)：`587 passed in 147.77s (0:02:27)`，实际git探测失败、源码前后未变；read-only git archive覆以当前工作字节，不冒称新鲜Git工作树 |
| 当前工作树完整快档 | [GREEN](T1a_evidence/accept_fix_fast/summary.json)：8689项，0失败/跳过；wrapper进程295.945s |
| 当前工作树全档四分片 | [GREEN](T1a_evidence/accept_fix_final/summary.json)：14665项，四分片全绿；含全库静态门的wrapper进程1596.327s |
| 执行/派发/收集节点多重集合、0skip/0failed | 两档每片node_sets_equal=true，skip_count=failed_count=0；export_changed/live_tree_changed均空 |
| 逐模块实际执行见证 | 两档均63/63：56个函数模块+7个声明模块，无缺导入/执行/调用；[全档见证](T1a_evidence/accept_fix_final/module_coverage.json) |
| 核纯度、全库静态构造0违例、无新增准入 | purity 0；全库AST 0；静态准入清单相对fc9675c逐字节未改，未新增准入 |
| 文件大小、UTF-8无BOM、diff检查、净跟踪体积 | [卫生清单](T1a_evidence/accept_fix/hygiene.json)：新增/修改文本UTF-8无BOM，新增文件无超1MB，diff无诊断；实际净增见§9.1 |

快档最后一行原样：

```text
8689 passed in 273.79s (0:04:33)
```

全档四分片最后一行按1–4原样：

```text
3667 passed in 986.58s (0:16:26)
3666 passed in 822.18s (0:13:42)
3666 passed in 1407.21s (0:23:27)
3666 passed in 764.22s (0:12:44)
```

静态构造原行：`exact construction AST gate: 0 violation(s)`。
<!-- CURRENT_VERIFICATION_END -->

完成门后只补报告、归档台账和交付索引；[门后字节核对](T1a_evidence/accept_fix/post_gate_source_check.json)确认源码、测试、工具、schema与fixtures仍是全档验证字节。完整[交付目录](T1a_evidence/accept_fix/artifacts.md)及[逐文件SHA](T1a_evidence/accept_fix/artifact_manifest.json)供Claude重建提交时核对；这不是把当前源码哈希钉成历史证据测试。

历史快档/全档与开工基线只保留历史引用，不重复大段旧末行造成“当前绿”歧义。顺手H1小项仍保留：m3_global2d提示对准production boundary；A08/A18/A29各晋升一小格快档，旧实测 `3 passed in 4.35s`、test-call合4.131s、整次4.861s，是三个小格成本，不是本轮净耗时增量。

复跑环境与代表命令（必须使用新的输出目录/名称）：

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='D:/eab-wt/cx-e2/reports/codex/T1a_evidence/tmp'
$env:TMP=$env:TEMP
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp reports/codex/T1a_evidence/tmp/new_targeted tests/test_tia2d_critical_acceptance.py tests/test_tia2d_curvature.py
python -X utf8 tools/h1_kernel_purity.py
python -X utf8 tools/check_exact_construction.py
python -X utf8 tools/tia2d_export.py --output reports/codex/T1a_evidence/new_formal_batch
python -X utf8 tools/tia2d_readback.py reports/codex/T1a_evidence/new_formal_batch/binary64 --output reports/codex/T1a_evidence/new_formal_batch/readback.json
python -X utf8 tools/tia2d_critical_mutations.py --output reports/codex/T1a_evidence/new_mutation_batch
python -X utf8 tools/tia2d_run_gates.py --name new_fast
python -X utf8 tools/tia2d_run_gates.py --name new_final --runslow
python -X utf8 tools/tia2d_figures.py --check-only
```

长跑落进度，中断/源码变化整次作废；pytest禁cache并显式basetemp；大型临时日志/副本留忽略tmp或外归档。UTF-8无BOM，不改.gitattributes/Git配置。禁止为整理文字重算全量冻结历史数据。

## 10. 设计接口差异、剩余工作与交付结论

与钉版设计的**获批偏离恰为两条**：

1. `Assembly2` 边界描述增加 `dof_anchor`，约束该点速度，与代数力矩参考点独立。部分掩码必须显式锚点；主端板面中点锚点已冻结。改变o须同步变荷载，物理锚点不跟随。
2. 极大共线正长度段内部平坦顶点不生成约束，它是两端点约束的凸组合；完整F_p boundaries和sources保留，retained单独表示是否放入解析约束。具名门 `test_maximal_collinear_segment_drops_interior_force_point_but_not_sources` 核保留来源和精确凸组合。

其余tia2d-2六类字段/覆盖改动已由CLAUDE-APPROVED-TIA2D-2批准；没有第三条未经批准的设计公共偏离。工具私有诊断不自动进入公共schema，数据schema获批不等于C ABI或C++里程碑已验收。

P0/P1所列返修与正式语料交付已完成，本轮完整验证见§9；没有用上一轮绿或局部预检代替。**P2同相形貌族设计网格退化，μcrit恒为0、λ轴即块高，未交付非退化形貌设计结论**；无跨越基时诚实unresolved并非认证失败，但也不抵消该研究缺口。非退化形貌族及边界阈值斜率认证分支转T1b。

其他边界：正式语料中lock UNPROVED、INVALID_INPUT缺口已在§6.4列明；iteration_limit已由正式单体角色覆盖。有限运动、制造公差、有限抗压、破裂和真实FE定量容量不在本单。真圆反例不得外推未核椭圆/正弦格。五路“有条件通过”不是返修后独立复验通过，最终合入及新鲜树验证由Claude安排。本轮未commit；来源提交待Claude重建后登记。

T1a_PARTIAL：P2 同相形貌族设计网格退化（μ_crit≡0，λ 轴即块高），非退化形貌族转 T1b
