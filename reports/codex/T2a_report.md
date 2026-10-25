# WO-T2a：接触允许的 SE(2) 路径与刚体逃逸证书

**一句话结论：有理八边形 K 的五例（含墙保留和墙腐蚀）及方形 K 的五个对照例，虽在 T1b 中平移困住，本次都找到了从精确原位出发且经两条独立数值路径核验的转动逃逸证书，收尾快档、全档四分片和静态门全部通过；这不确定刚体临界公差，也不给出任何 SE(2) 困住结论。**

日期：2026-10-25。执行：Codex；所有者：Claude。未 commit；现有数学 API、设计正本、C++/eab2、其他工作树未改。

## 1. 开工合同、范围与证据导航

| 项目 | 合同与实况 |
|---|---|
| 目标 | 接触允许的首次贯入、逐段刚体逃逸证书、真值/独立复核、10例表、诊断和性能；P2可选 |
| 写域 | 本工作树与 `D:/eab-evidence/reports/codex/T2a_evidence/` |
| 非目标 | SE(2)困住证书、多体运动、摩擦静力、真实积分路径推断、SE(2)最短出口或新颖性宣传 |
| 基线 | 实查 HEAD `239ec30863db52d531531f77003da46fc3441908`，开工干净，Python 3.12.10 |
| 回滚锚 | [2398文件字节ZIP](file:///D:/eab-evidence/reports/codex/T2a_evidence/baseline_anchor/source.zip)及[逐文件SHA256](file:///D:/eab-evidence/reports/codex/T2a_evidence/baseline_anchor/manifest.json)；恢复须保护后续修改，不自动reset |
| 成功条件 | 真值一致、1024独立对拍、接受路径全段核验、命名变异红、快/全档0 failed/skip及静态0违例 |
| 完成实况 | 续裁定落实；受影响门、快档9415、全档15521及静态0违例；收尾运行期间源码冻结，运行后仅回填报告/归档/交付审计 |

关键入口：[新增实现](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/se2_paths.py)、[机器小汇总](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/summary.json)、[完整交付证书](file:///D:/eab-evidence/reports/codex/T2a_evidence/certificates/)、[静态最小复现](file:///D:/eab-evidence/reports/codex/T2a_evidence/static_minimal_repro.json)、[交付清单](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/artifacts.md)。外部归档是本地保存，不是远程备份。

归属照所有者 D1：**用石的接触边盖系统 C(0,1)/C(1,0)（2015 §7.3–§8.2，A11/A23）与 §7.4 端点论断，结合本仓库的 SE(2) 首入。SE(2) 指定路径首入是本仓库 M5a 的结果（A29），不是石根华原文。** 锁定态不得用最短出口“解决”（A37）。本次核对仓内归属表与设计合同，不冒称重新核读了石原文全文。

## 2. 定义、支持域和新增语义

设 `P={s∈[0,1]:int(X_A(s,A))∩int(X_B(s,B))≠∅}`，`τ_P=inf P`。本单保持原 M5a 有理 Cayley 轨迹，`u(s)=s*u1`，不是匀角速度模型。

- `FREE`：P为空；`exact_time=None`，`immediate=False`。相触或沿边贴行均允许。
- `PENETRATES`：初态不贯入，稍后有贯入；返回其精确下确界，包括“初态接触、任意小正时间即贯入”的 `τ_P=0`。
- `INITIAL_OVERLAP`：初态内部相交；新API按本单定义返回时间0、`immediate=True`，与初态仅接触后立即贯入明确区分。
- 有理时间返回 `QuadraticTime`；非有理时间返回 `RealAlgebraic`。`incidences` 是 τ_P 处全部闭段关联；`features` 是复用 `_features` 法锥筛选的盖标签及 VV。它们不等同于完整配置空间边界证书。
- `touches_end=(end_state==0)`，即 s=1 实体相触；贯入中的边界关联不算此字段。many 的该字段是任一障碍对末端相触的 OR，仍须查各 `results`，不能掩盖其他障碍的贯入。
- many 取最小精确时间并保留全部并列障碍索引；`INITIAL_OVERLAP` 优先，但同在0时刻的立即贯入障碍仍保留。
- 仅支持精确整数/Fraction 输入、非退化单简单环、每段每体 `|u1|≤1`。邻居固定的逃逸证书不扩展为多体 SE(2)ⁿ。

旧 `se2_first_entrance` 是闭集首次接触，初始相触立即报0；它不能替代本单贯入判定。**`no_contact⇒FREE`，反向一般不成立**：门洞临界公差路径 FREE 但有贴门接触。既有函数完全未改。具名门：`test_contact_departure_and_endpoint`、`test_initial_contact_can_penetrate_immediately`、`test_irrational_infimum`、`test_many_preserves_all_earliest_obstacles`、`test_strictly_separated_no_contact_fast_check_agrees_with_penetration`。

## 3. 完整事件划分与正确性论证

1. 轨迹保持每块的简单性、边长、正面积；旋转分母 `1+s²u²` 严格为正。对所有双向 VE/EV 对复用 `_line_polynomials` 的 F/G/H，点在对方闭边上当且仅当 `F=0,G≥0,H≥0`。
2. F非零时保留[0,1]内所有满足线段条件的实根。F恒零时还保留G/H的非零多项式根和窗口端点，不能丢弃持续共线接触。全体合法事件精确判等排序，加0、1切成有限个开区间。
3. 内部相交是连续刚体参数下的开条件。若沿参数从不相交变为相交，边界事件不能仅是稳定的非平行边内部横交；首次边界接触必须含顶点落在对方闭边上，平行重叠亦有端点落边。持续共线时，闭段成员关系只能在投影端点条件变化处改变。因此相邻事件之间“是否内部相交”不变；无需假设分离与接触彼此也恒定。
4. 对相邻不同代数根精确细分隔离区间，直到左上界小于右下界；其有理中点严格位于该开区间。用 `polygons_overlap_exact` 判该点的内部相交状态。第一个相交区间的**左端点**就是 τ_P，不是该探针。
5. 初始贯入另判；s=1亦单独精确判实体状态。若s=1贯入，开性保证其左邻域也贯入，算法应已找到相交区间，否则响亮报错。s=1仅接触则允许，但 `touches_end` 必须报出。
6. 在得到的 τ_P 重枚举全部关联和盖，不只返回触发最小根的一对。对多障碍取最小并保留等时项即得并集的贯入下确界。

这是一份给定支持域内的数学论证；有限测试不是全输入形式化证明，静态零诊断也不能替代数值安全证据。对应门：`test_partition_excludes_supporting_line_only_events`、`test_persistent_collinearity_uses_projection_endpoints`、`test_internal_overlap_with_free_endpoints`、本单真值和独立对拍门。

## 4. 逃逸证书及不可信提议器

`SE2EscapePath` 保存有序逐顶点 `poses` 与 `motions`，位姿数=段数+1。核验器先要求首位姿与输入块逐点精确相同，再核每段变换端点与下一位姿逐点相同；不允许任何坐标容差。吸附起点只有显式补一段平移且该段同样通过核验才可用。

`from_waypoints` 的相邻绝对 Cayley 参数采用 `u_rel=(u_b-u_a)/(1+u_a*u_b)`；分母为0或相对转动超过90°拒收。`verify_se2_escape` 每段对每个障碍要求 `FREE`。末姿态作为新基体，另将以(0,0)起始的有理平移折线 `ray` 交给原 `verify_escape_certificate`；它核有限前缀和包围盒外明确向外的无限坐标轴射线。仅“顶点高于墙顶”不是该核验器的替代。

网格工具仅提出候选：以腐蚀后块的**精确参考点**为网格原点，浮点SAT占据、洪泛、回溯、恢复有理节点、同向合并；精确节点是 `c0+(i,j)h` 和有理半角参数，起点不吸附。粗到细 h=0.02→0.01→0.005；d01粗档未找到，细档找到；其余本批在0.02找到，0.005分支未需执行。不以搜索失败证明困住。工具烟门另核合并不能构成>90°段。

Claude scoping脚本仅只读参考。这里使用自己的原位中心网格重新提议，段数和终点不同，**未复制旧证书冒称独立复现**。全部10例286段共858个刚体段—障碍对通过生产核验；oracle对同样858对及射线有限前缀30对，共888次 `first_contact` 全通过。10例生产闭集首入补充检查858次均 `no_contact`，与 `FREE` 一致。独立oracle不负责无穷射线，必须与既有射线证明合取。

具名门：`test_escape_rejects_discontinuous_or_snapped_poses`、`test_escape_rejects_free_endpoints_with_blocked_interior`、`test_escape_requires_certified_tail_and_strict_motion_support`、`test_waypoint_relative_cayley_parameters_close_exactly`。

## 5. 真值库：手算 / 生产程序 / 独立 oracle

几何在 `tests/t2a_truth_geometry.py`；前七行每项均独立检查四个障碍，贯入行全部四重并列。`∅`表示无贯入时间。

| 真值项 | 手算 | 生产程序 | 独立oracle |
|---|---|---|---|
| 风车 u1=1/2 | FREE，τ=∅，末接触 | 精确相同 | 精确相同 |
| 风车 u1=1 | PENETRATES，τ=1/2 | 1/2，末接触 | 1/2，末接触 |
| 风车 u1=−1/2 | PENETRATES，τ=0 | 0，immediate | 0，非探针时刻 |
| 中点楔 u1=1/2 | PENETRATES，τ=0 | 0 | 0 |
| 中点楔 u1=−1/2 | PENETRATES，τ=0 | 0 | 0 |
| 菱形四板 u1=1 | FREE，首末接触 | FREE，末接触 | FREE，末接触 |
| 菱形四板 u1=−1 | FREE，首末接触 | FREE，末接触 | FREE，末接触 |
| 门洞 δ=1/8 | 可贴两门侧逃逸 | 3段15对FREE，射线通过 | 含尾段共20对通过 |
| 门洞 δ=129/1024 | 逃逸侧 | 3段15对FREE，射线通过 | 含尾段共20对通过 |
| 门洞 δ=127/1024 | 伪造穿门路径应拒 | 第3段对左右门柱贯入 | 同两对贯入；共6个相交探针 |
| 随机有理纯平移64例 | 与原平移核验器一致 | FREE / 非FREE逐例相同 | 独立耳切+仿射SAT；覆盖三种初态结果 |

门洞路径：中心从(0,1/2)平移至(0,3)，原位转90°，再向上平移5，最后平移100并接向上无穷射线。腐蚀在块的自身坐标系完成，八边形K的坐标支撑均为1，矩形精确变为 `[-3/2+δ,3/2−δ]×[δ,1−δ]`。边界δ=1/8转后宽度=3/4，贴门通过；下侧宽度385/512>3/4，直穿门伪证被拒。下侧拒收只针对该路径，不是 SE(2) 困住证明。门洞族“δ<1/2始终平移困住”未作为本单新结论验证。

具名门：`test_hand_truth_and_independent_oracle`、`test_doorway_octagon_closed_form_and_segment_oracle`、`test_doorway_contact_allowed_escape_and_false_crossing`、`test_random_rational_pure_translation_matches_existing_segment_verifier`。手算与精确结果无不符项，未修改真值迎合程序。

## 6. T1b 平移困住样本中可被刚体运动逃出的表

δ*_T均引用T1b的**平移**临界公差。本表10个δ严格低于对应δ*_T；“墙政策e”0=保留，1=同腐蚀。前8行为燕尾 h=2、wall=2；后2行为凸耳segments=4的8条实际弦，不外推圆形极限。最大倾角是诊断显示；终点余量是最小顶点y减最高墙顶y的精确有理数。P/O分别是生产刚体对数 / oracle刚体+尾段对数。

| ID | wk, wn；K；e | δ | δ*_T | 段数 | 最大倾角(°，诊断) | P / O | 终点余量（精确） |
|---|---|---:|---:|---:|---:|---:|---:|
| d01 | 5/2,3/2；方形；0 | 3/10 | 1/3 | 68 | 76.858883 | 204 / 207 | 806/36965 |
| d02 | 7/2,3/2；方形；0 | 2/5 | 1/2 | 28 | 73.901877 | 84 / 87 | 40869/999700 |
| d03 | 5/2,1；方形；0 | 21/50 | 3/7 | 22 | 14.611519 | 66 / 69 | 7551/154600 |
| d04 | 5/2,1；方形；1 | 1/5 | 3/14 | 38 | 75.684374 | 114 / 117 | 29426/586925 |
| d05 | 7/2,3/2；八边形；0 | 9/20 | 24/41 | 64 | 55.140274 | 192 / 195 | 52609/1300000 |
| d06 | 3,1；八边形；0 | 11/20 | 24/41 | 8 | 82.371850 | 24 / 27 | 1519/33900 |
| d07 | 5/2,3/2；八边形；0 | 7/20 | 24/65 | 22 | 76.215154 | 66 / 69 | 10803/210050 |
| d08 | 3,3/2；八边形；1 | 6/25 | 12/49 | 18 | 5.849956 | 54 / 57 | 36529/752720 |
| k01 | 凸耳；方形；0 | 8/25 | 1/3 | 10 | 19.927608 | 30 / 33 | 402169/9314250 |
| k02 | 凸耳；八边形；0 | 2/5 | 12/29 | 8 | 19.808366 | 24 / 27 | 375763/8282250 |

本批没有“未找到”的最终条目；这不表示提议器对一般输入完备。每例独立完整JSON见[交付证书目录](file:///D:/eab-evidence/reports/codex/T2a_evidence/certificates/)和[逐例链接汇总](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/summary.json)。原计算记录保留在verification_01；交付版把门洞尾段的整数坐标规范为有理字符串，并添加 `delivery_serialization` 来源元数据，数值与核验结果逐项不变，原SHA不重写，见[序列化清单](file:///D:/eab-evidence/reports/codex/T2a_evidence/certificates/serialization_manifest.json)。未重算全量证据。

### 6.1 D5登记，不改写T1b历史报告

对 `wk=5/2,wn=3/2,h=2,wall=2,e=0`，本管线重新确认：

| K | 本次原位转动证书δ | T1b平移临界值 | 平移困住但可刚体逃出的区间 |
|---|---:|---:|---|
| 方形（对照） | 3/10 | 1/3 | [3/10,1/3) |
| 有理八边形（标题模型） | 7/20 | 24/65 | [7/20,24/65) |

区间扩展用腐蚀嵌套性：较大δ下移动块在自身坐标系内是较小块；沿相同刚体变换仍包含于原路径占据集合，e1时障碍亦缩小。因此证书的可行性向更大δ传递（保留非退化支持域）；不是对区间每点逐一扫描，也不是刚体临界公差的确定。正式T1b追加勘误仍由Claude验收时处理。

## 7. 独立复核、变异与固定小子集回归

oracle沿用测试内 `m5a_independent_oracle.first_contact`：六个有理样本插值事件多项式，独立Sturm隔离、gcd判等；实体状态由G0的整数提升、绕数/横交及同向共线边检查判定，**不是生产 `exact.polygons_overlap_exact`，也不是三角剖分法**。新helper从其每个开区间probe对应的独立cuts恢复左端点，不把probe当τ。复核路径不调用生产se2/algebraic求根代码。结构导入门只是补充，主证据是逐例语义对拍。

1024个不同有理段分16批×64：初态接触136、分离654、重叠234；移动体旋转954，对方旋转301，双旋281；正/负转均覆盖。随机库是非对称凸三角/矩形，不冒称1024覆盖了所有一般凹环。状态、精确时间、incidences、features、immediate、末态逐项一致。[随机对拍日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/oracle_1024_01.log)原样末行：

```text
16 passed, 2 deselected in 45.01s
```

所有命名变异均在实际被测函数源代码内部注入，先执行原版语义guard绿，再确认指定语义AssertionError红；不是给返回值加假数据或靠哈希不符。

| 缺陷 | 守护断言 |
|---|---|
| τ返回首个相交探针 | 精确时间必须是区间左端1/4；中点楔另守τ=0 |
| 漏闭线段条件 | 非法支撑线根不能进入合法事件分区；仅多分区未必改变最终τ，不能用无效变异冒称守住 |
| 漏s=1 | 无贯入但终点接触必须报告 |
| 接触当贯入 / 贯入当接触 | 持续接触FREE；内部穿越PENETRATES |
| 放行超过90°段 | `|u|>1` 必须拒收 |
| 段首尾容差相等 | 2^-90顶点缝隙仍须拒收 |
| 起点吸附不补段 | 2^-90原位偏移须拒；补段并核验可接受 |
| 只查端点 | 两端自由、区间中间穿障碍的路径须拒 |

测试文件：`test_t2a_mutations.py`、`test_t2a_escape.py`。固定回归只保存八边形d07和门洞等号两条小证书，实际重跑状态、标签、精确时间及计数；不以当前源码哈希钉冻结数据，不要求外部证据目录/Git/姊妹程序。[小输入](file:///D:/eab-wt/cx-e2/tests/data/t2a_escape_replay.json)、`test_fixed_escape_replay_compares_states_labels_times_and_counts`。

作者内部QA发现并修正“G0三角剖分”的文档误述，非docstring AST完全相同；冻结证书原生产哈希未重写。[作者QA](file:///D:/eab-evidence/reports/codex/T2a_evidence/author_qa.json)记录前后SHA、随机覆盖及边界。该QA不是Claude安排的独立对抗验收，未宣称0 critical/major的所有者验收。

## 8. 瓶颈诊断（浮点，不参与结论）

每段65个均匀样本，采样局部极小附近再作golden-section细化。如下是**路径最紧处估计**和近活动VE/EV候选，不是连续全局最小值下界、真实零距离incidence、精确法锥通过集或临界公差证书。编号为证书输入的0基障碍/顶点/边；VE=(移动顶点,障碍边)，EV=(移动边,障碍顶点)，形状与 `_features` 一致。分组容差只用于“诊断”归组。

| ID | 估计最小分离量 | 段号（0基） | 近活动标签组合（障碍号:标签） |
|---|---:|---|---|
| d01 | 0.00565653 | 8,9 | 1:VE(1,0) |
| d02 | 0.01010803 | 23 | 1:EV(0,0),VE(1,0),EV(1,0),VE(1,3) |
| d03 | 0.01115298 | 19,20 | 0:EV(3,2) |
| d04 | 0.01118286 | 23,24 | 0:EV(2,2) |
| d05 | 0.01102168 | 17–19 | 2:VE(0,2) |
| d06 | 0.01123894 | 5,6 | 0:EV(2,2) |
| d07 | 0.01124906 | 21 | 0:EV(2,2),VE(3,1),VE(3,2),EV(3,2) |
| d08 | 0.01196195 | 13,14 | 0:EV(3,2) |
| k01 | 0.01197606 | 7,8 | 0:EV(10,5) |
| k02 | 0.01239876 | 5,6 | 0:EV(8,5) |

完整286段见[诊断与已核路径关联](file:///D:/eab-evidence/reports/codex/T2a_evidence/diagnostics_verified_paths.json)。原提议阶段诊断中的 `accepted=false` 保留其历史含义，不篡改为当时已认证；关联文件另指向后来精确核验记录。

## 9. 性能与可选P2

Windows / Python3.12.10；每负载同进程连续三次，无额外预热；用perf_counter取中位数。测试期间存在开工基线并行负载，数值仅作本机诊断，不作工程性能承诺。每次状态和精确τ相同，输入与源码前后SHA完整保存于[性能记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/performance_01.json)。

| 负载 | 调用 | 三次中位数 |
|---|---|---:|
| 有理16边星形对16边星形，非对称参考点/双体运动 | se2_first_penetration | 0.3460385 s |
| 八边形K腐蚀燕尾对三固定障碍 | se2_first_penetration_many（整次3对） | 0.0232923 s |

P2-9 §7.4端点论断专门实验**未做**；不写“本次验证了石原文端点论断”。P2-10已对首次贯入原语做精确元门：三种随机有理整体旋转、0/10³/10⁵大平移、缩放、镜像取反转向、循环身份置换，含10⁵坐标上的10^-8特征尺度、双体非零转动和非对称参考点。具名门在 `test_t2a_metamorphic.py`；未另将整条多段逃逸证书及many包装器作全套元变换，不能把原语门说成所有新增API均有独立元门。按工单，P2缺项不单独计PARTIAL。

## 10. 续裁定后的静态审查与实测门

### 10.1 原阻塞记录与续裁定

原定向数值快档末行 `65 passed, 16 deselected in 10.27s` 及1024段对拍保留；原166项静态诊断、纯度固定计数失败不是数值反例，也不是可忽略的绿门。[166项历史诊断](file:///D:/eab-evidence/reports/codex/T2a_evidence/static_01.json)及[8例最小复现](file:///D:/eab-evidence/reports/codex/T2a_evidence/static_minimal_repro.json)均未覆盖。

2026-10-25所有者续裁定允许证明缺口类逐站审查，禁止任何rounded/浮点构造汇点准入；允许纯度52→53机械计数维护。续工前保存了[原BLOCKED交付ZIP](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/blocked_delivery_anchor.zip)及[逐成员SHA入口](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/intake.json)，不把旧红日志改写成通过。

<a id="t2a-static-admission-review"></a>
### 10.2 精确复用的逐站审查准入

只追加 `tools/exact_construction_policy.json` 的waivers；原3522条waiver及imports=648、members=432、其他策略字段均保持。三分析器 `check_exact_construction.py`、`exact_construction_subset.py`、`exact_construction_flow.py` 的SHA256与开工锚逐一相等。每条新准入按AST节点、最小外围源码SHA钉住，含具体reason及指向本节的review_evidence；没有跨调用方继承旧豁免。

先做闭子集友好重构，再准入：

- 生产：`_checked_motion` 显式 `_parameter` 再验精确标量；复用一个frozen静止运动实例；删除重复局部导入。没有改 `se2.py` 或既有类型。首次审查57项降至46条证明缺口诊断，对相同AST/外围源去重后为44条实际准入。显式循环替代many的精确min曾增加缺口，未保留无益改写。
- 测试：嵌套辅助移到模块级、随机用例改列表返回、身份索引用显式循环、元变换算术前归一有理分量；独立oracle分离事件根与标签，比较精确根证书副本后显式排序去重。仍复用原M5a独立插值/Sturm/G0，不调用生产求根，不修改旧oracle。
- 审计：新增普通helper `tests/t2a_oracle_audit.py`，先生成全部精确位姿，再独立构造报告元数据，避免把数值几何与异构JSON元数据混在原位累积容器内；行仍为dict、`pairs`仍为list。新helper完整参加同一静态扫描，**不是test driver豁免**；原生产路径逻辑仍全部在 `src/`。三门洞共60对旧新报告逐值与JSON SHA相同，见[兼容性证据](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/helpers_audit_compatibility.json)。
- 最后移除新结果类不必要的 `.time` binary64显示转发，新增 `test_new_path_results_never_request_binary64_display`；只保留 `exact_time`。既有 `QuadraticTime/RealAlgebraic` 及其显示接口完全未改。最终生产源码SHA：`14bfd823dda1c438ffd136128f73545236d5e2bbbb428a3b1eb5e09efc79bbdf`。

测试辅助109条历史诊断降至93条证明缺口。合计139条诊断对应137条独立站点记录，所有原10条rounded诊断均由代码重构消除，没有一条被准入。记录见[逐站候选及原始诊断](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/admission_candidates.json)、[本次审查写入记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/admission_authoring.json)。

**以下计数为去重后的实际新增准入条目，不是重复诊断行数。生产与测试辅助分列；rounded或同类数值汇点准入为0。** 同一函数中相同AST节点使用同一条策略记录，例如两次frozen字段写入共用 `object.__setattr__` 属性节点。

<!-- T2A_STATIC_ADMISSIONS_COUNTS_BEGIN -->
| 规则 | src/ 生产 | tests/ 辅助 | 合计 |
|---|---:|---:|---:|
| closed-dynamic-call | 2 | 6 | 8 |
| closed-import-call | 4 | 22 | 26 |
| closed-method-call | 4 | 8 | 12 |
| closed-runtime-reflection | 1 | 0 | 1 |
| closed-unknown-call | 1 | 0 | 1 |
| closed-unknown-member | 4 | 6 | 10 |
| closed-unproved-call | 28 | 51 | 79 |
| **总计** | 44 | 93 | 137 |
<!-- T2A_STATIC_ADMISSIONS_COUNTS_END -->

完整逐站记录见[准入账本](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/static_admissions.json)。`closed-runtime-reflection` 仅批准 `SE2EscapePath.__post_init__` 内 `object.__setattr__`，且自动门限定两个直接调用必须分别把已验精确poses/motions写入frozen记录；`closed-unknown-call` 仅为classmethod的 `cls(...)` 精确记录构造。代数根、隔离区间细分、有理端点和精确SE2记录调用是证明可达性缺口，不涉及先转浮点再包装Fraction。测试辅助中的编译/替换只为内部缺陷注入，未将生产算法搬进test driver。

具名自动门：[test_t2a_static_admissions.py](file:///D:/eab-wt/cx-e2/tests/test_t2a_static_admissions.py)。逐条核对旧策略、分析器、当前AST及外围源、reason/review_evidence、报告/账本/策略计数；审查范围内禁止float、math、numpy、struct/ctypes和二进制位操作。13种注入在实际 `_checked_motion` 函数内部触发语义断言，不靠源码SHA变化冒充杀变异。该有限词法核查不是任意Python程序的数值正确性证明。

### 10.3 受影响测试、纯度及静态门

纯度只将旧52改为53，旁注新增 `se2_paths`；禁词、白名单、依赖图不放宽。原数学公共函数及设计合同保持原字节。受影响测试及静态实测：

在本次生产数值源码上运行当时已有的全部T2a快慢测试（含1024段全部批次、新显示禁用门、准入注入门）及纯度门，另跑旧静态机制回归。随后新增的历史计数维护和3项守门测试另见§10.4的30项定向，并已包含在最终快档/全档中。0 failed/skip；静态回归35个deselected是默认slow过滤，非skip，不代替后面的快慢全档。

```text
135 passed in 67.54s (0:01:07)
228 passed, 35 deselected in 2.18s
exact construction AST gate: 0 violation(s)
```

[命令/退出码/时间汇总](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/checks_01/summary.json)、[T2a与纯度原日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/checks_01/t2_all.log)、[旧静态回归日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/checks_01/static_regression.log)、[全仓静态原日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/checks_01/static.log)。新准入门15项均包含在135项内，13种内部浮点/位操作注入均由语义断言拒绝。

### 10.4 收尾全仓快档及全档四分片

H1包装器沿用原运行、进度及逐模块实际执行监测；TEMP/TMP与全部运行输出位于本单外部目录。运行准入条件要求收集节点、分派节点、实际call节点的多重集合一致，0 failed/skip，运行前后源码字节不变。运行源为只读字节导出，**不是新鲜Git树**。本次工具将新增准入账本纳入导出；禁止在运行时修改工作树。

开工基线15421节点及其四片末行保留在[baseline_full](file:///D:/eab-evidence/reports/codex/T2a_evidence/baseline_full/summary.json)，不作为本次新增实现的收尾绿。其原样末行为：

```text
3856 passed in 1444.62s (0:24:04)
3855 passed in 1844.53s (0:30:44)
3855 passed in 1537.35s (0:25:37)
3855 passed in 1935.45s (0:32:15)
exact construction AST gate: 0 violation(s)
```

首轮 `resume_final_fast` 超过900s上限，被运行器明确作废；没有完整pytest末行或GREEN汇总，不能拼接为通过。[作废状态](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_fast/state.json)、[原日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_fast/shard_1.txt)完整保留。进度中的11个历史门失败，经独立定向复现为 `11 failed, 1 passed in 0.34s`：旧 `policy_history_view.COUNTS` 仍要求3522，而本次获准追加后实际3659；不是旧条目或历史指纹被改写。

作为已授权追加的配套计数维护，仅将 `tools/policy_history_view.py` 的waivers计数改为 **3659=3522+137** 并加注释；所有投影逻辑、其他计数及历史测试指纹原样。新增 `test_t2a_policy_history.py` 锁住该机械差异，并实际确认再增/删一条仍被冻结计数拒绝。修后历史门、新计数门及准入门原样末行：`30 passed in 2.12s`。[修前日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/history_counter_before.log)、[修后日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/ruling_resume_20261025/history_counter_after.log)。三个静态分析器仍一字未改。

最终新run名改为 `resume_final_fast_r2`、`resume_final_full`，分别完整单片快档和包含快慢的固定四分片全档。初始快档5分钟估计不足，重跑上限提高到1800s，不删测试；全档按基线最慢片约32分钟预估35–45分钟，每片上限10800s。最终实耗以原始日志为准。没有拼接作废运行，也没有为文档重算全量冻结证书。

**收尾实测：快档9415项、全档15521项均GREEN，0 failed、0 skip；收集/分派/实际call节点多重集合逐项相等。** 两次均完成69个模块的实际执行核对（62个函数模块、7个声明模块），包含 `se2_paths`；导出源及现场源前后无变化。快档总墙钟1464.640s（约24分25秒）；全档含静态扫描总墙钟2101.003s（约35分01秒），静态扫描128.063s。快档超过日常约5分钟的成本目标，未通过删测试或将慢项伪装过滤来缩时。

[最终快档汇总](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_fast_r2/summary.json)、[快档原日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_fast_r2/shard_1.txt)的原样末行：

```text
9415 passed in 1451.20s (0:24:11)
```

[最终全档汇总](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/summary.json)的四分片原日志（[1](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/shard_1.txt)、[2](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/shard_2.txt)、[3](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/shard_3.txt)、[4](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/shard_4.txt)）及[静态日志](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/exact_construction.txt)原样末行：

```text
3881 passed in 1458.26s (0:24:18)
3880 passed in 1863.95s (0:31:03)
3880 passed in 1534.40s (0:25:34)
3880 passed in 1949.65s (0:32:29)
exact construction AST gate: 0 violation(s)
```

两次使用同一份源字节清单。最终受测字节另存[源码ZIP](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/tested_source.zip)及[逐成员核验记录](file:///D:/eab-evidence/reports/codex/T2a_evidence/resume_final_full/tested_source_archive.json)；其中报告保留运行时的“待收尾”文本，当前报告是运行完成后回填，不能据此误读测试状态。代码、测试、工具及准入账本仍逐字节等于受测版本；文档/交付文件差异由[最终交付审计](file:///D:/eab-wt/cx-e2/reports/codex/T2a_evidence/delivery_audit.json)单独记录。

可复跑（需新的run名，已存在目录拒绝复用）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP='D:/eab-evidence/reports/codex/T2a_evidence/tmp'
$env:TMP=$env:TEMP
python -X utf8 tools/t2_run_gates.py --name <new-fast-name>
python -X utf8 tools/t2_run_gates.py --name <new-full-name> --runslow
```


## 11. 工单订正清单

1. 真值数值：无订正；风车、中点楔、菱形、门洞均精确吻合。
2. 流程合同已裁定：2026-10-25所有者允许证明缺口逐站审查，禁止任何浮点汇点准入；本次按§10实施，不改三分析器。新调用方不能继承旧站点豁免是门的原设计，不登记为T2a数值缺陷。
3. 门维护已裁定：指定新增模块使旧纯度硬计数52变53，已机械更新并注释；禁词、白名单和依赖图未放宽。
4. 执行中自纠：最初门洞测试误用不存在的erosion导入名，两次收集错误后改为既有 `erode_polygon_exact`；此为测试接线错误，不是几何真值订正。后续同测试12项通过，原轮最终定向65项通过。
5. 作者QA将G0误述“三角剖分”更正为实际整数提升/绕数/横交原语；无数值代码变化。1024日志由PowerShell UTF-16输出无损规范化为UTF-8无BOM，前后SHA及文本相同证据在QA JSON；无重跑拼接。

## 12. 建议并入设计的新增清单（仅Python草案）

| 名称 | 新增合同 |
|---|---|
| SE2Penetration2 / se2_first_penetration | FREE/PENETRATES/INITIAL_OVERLAP；exact_time、immediate、incidences、features、touches_end、initial_state/end_state |
| SE2PenetrationMany / se2_first_penetration_many | obstacle_indices全并列；逐障碍results；带障碍索引标签；可选同数motions_b |
| SE2EscapePath / from_waypoints | 逐顶点poses、每段motions；有理Cayley相对角；原位与连续性由核验器强制 |
| SE2EscapeVerification / verify_se2_escape | valid/reason、checked_segments/checked_pairs、segment_results、ray_verification；末段后无限射线合同 |
| 工具/证据schema | t2a-untrusted-se2-proposal-1、t2a-exact-se2-escape-1、t2a-fixed-replay-1及diagnostic字段；不冒用旧schema |

`docs/eab2_design.md`和C++引擎完全未改；本清单不是正式设计批准。源码/测试/小汇总留仓，完整证书、日志及SHA归外部，映射见[EVIDENCE_ARCHIVE](file:///D:/eab-wt/cx-e2/reports/EVIDENCE_ARCHIVE.md)。

## 13. 遗留与交接

- P0/P1及续裁定收尾已完成；快档、全档四片和静态门均有完整GREEN记录。首轮作废快档仍保留，不拼接、不计为绿。
- 所有者安排的新鲜Git树及一路独立对抗核查未做；作者QA不能替代。
- §7.4专门实验可选未做；二阶、16边形K、笼子证书和多体运动继续留后续工单。
- T1b正式勘误由Claude验收追加；未改历史报告，未把平移δ*_T说成刚体临界值。

T2A_DONE
