# WO-T2d：凸耳族的刚体临界公差——精确核验报告

**一句话结论：** P0完成：12行精确值一致、9种临界逃逸精确成立、93份有限证书双接受；另3种方形仅有宽度小于2^-12的临界括号，等号仍为猜想；原交付全档16630项通过，本轮8项验收返修闭合，快档10510项、含慢定向78项及静态门全部通过。

## 1. 白话结论与边界

同一个凸耳，能否转着退出，不只取决于刻面有多细，也取决于采用哪一种腐蚀容差元。本单严格区分：九种满足条带条件的情形，可以在精确临界值处“先转后升”；方形容差元的 N=8、16、32 不能用这条特定路径证明等号，只能报告已核验的上下界与猜想。

定理与证明归属所有者的第 2 版定理稿；石根华入口块理论的归属沿用 WO-T2a D1（SE(2) 指定路径首入是本仓库 M5a 的结果）；不作新颖性或实现序数宣传。

这里的“自由”允许边界接触，禁止内部相交；不是工程间隙裕量、力学轨迹等价、材料标定或生产工程验证。不涉及 C++/eab2。

只讨论 `head_width=2, neck_width=1, height=2, wall=2`、固定墙不腐蚀、N∈{4,8,16,32}、三种指定 K。N=64、128 的结果只用于标注为“数值”的趋势展示，不冒称生产生成器支持这些 N。

依据与只读合同：[T2d 第2版定理稿](file:///D:/eab-wt/cx-e2/docs/t2d_knob_family_theorem.md)、[T2c2 定理稿](file:///D:/eab-wt/cx-e2/docs/t2c2_knob_theorem.md)、[T2b 引理](file:///D:/eab-wt/cx-e2/docs/t2b_cage_lemma.md)。三者及生产/独立核验器均不修改。

## 2. 精确计算的可信边界

- [精确辅助模块](file:///D:/eab-wt/cx-e2/tests/t2d_knob_family_exact.py)只以整数、`Fraction`、整数 `isqrt`、支持枚举和半平面交运算作判定，无浮点或数值开方。
- 不同二次域比较以 `sign(A+B√q+C√r)` 为基本问题。先令 `x=A+B√q`、`y=C√r`；同号直接判定，异号使用 `sign(x)·sign(x²−y²)`，后者只有一个根式。因此相等时也终止，不依赖近似区间分离。
- [独立水平截面腐蚀](file:///D:/eab-wt/cx-e2/tests/t2d_sections_exact.py)使用
  `g(y)=min_v[a(y+δv)−δk(v)]`；所有腔体断点、容差元顶点层及仿射下包络交点都进入分区。端点/中点检查依赖明确的分段仿射证明，不是无说明的采样。被省略的外部截面必须严格为负，不能漏掉零宽点或线段。
- `erode(conv(A))` 仅作为真实非凸腐蚀体的**外侧半径界**，从不声称它就是 `erode(A)`。实际证书实例使用上述精确截面构造的真实腐蚀体。
- [精确计算 JSON](file:///D:/eab-evidence/reports/codex/T2d_evidence/exact_01/exact_summary.json)保存代数系数、全部最小弦、C 的界及临界转动；其 `NUMERICAL` 字段只作显示。源清单和产生它的基线提交分列，不把现在的源码哈希当作数学回归条件。
- [精确表出处补记](file:///D:/eab-evidence/reports/codex/T2d_evidence/exact_01/provenance_addendum.json)以原记录的生产工具SHA作为内容版本，将4份原生产源逐字节解析到受测源ZIP；未改原数据或原哈希，未重算精确表。

## 3. 定理条目到具名门

|合同条目|具名门（均位于 tests/）|验证范围|
|---|---|---|
|跨二次域精确最小值|`test_t2d_values.py::test_t2d_cross_field_order_signs_and_scaled_equalities`|符号分支、不同根式表示的相等、精确有理包络交叉核对|
|§2.4 全表|`test_t2d_values.py::test_t2d_theorem_table_all_fields_exact`|12行 δ_disk、全弦 δ_T、e*、S、比值|
|Q 的中心对称/包含/截颈|`test_t2d_values.py::test_t2d_q_symmetry_containment_and_neck_heights`|逐 N 的全断点包含检查，不只检查圆上点|
|Q 边与支持数据绑定|`test_t2d_geometry_binding.py::test_t2d_Q_order_and_all_supports_bind_bijectively`|全部 2N 有向边与候选支持双射|
|K16 的精确定义|`test_t2d_geometry_binding.py::test_t2d_elements_have_declared_exact_symmetries_and_K16_radius`|16点、D4对称、单位圆、h(e_x)=99/101|
|对象及实际墙绑定|`test_t2d_critical_escape.py::test_t2d_independent_whole_cavity_matches_production_generator`|独立 A/左右墙/地板与未改生产生成器一致|
|C|`test_t2d_values.py::test_t2d_C_by_convex_hull_outer_erosion`|12例真实腐蚀体的严格转动半径上界|
|9例临界逃逸|`test_t2d_critical_escape.py::test_t2d_nine_exact_critical_rotations_and_projection_equalities`|正交转动、恰为[-1/2,1/2]、全转与整条上移射线|
|方形细刻面不能套条带定理|`test_t2d_critical_escape.py::test_t2d_square_finer_facets_do_not_pass_the_strip_theorem`|N=8、16、32明确拒绝，不以路径失败证明困住|
|平移阈值与生产自由空间|`test_t2d_translation.py::test_t2d_n4_translation_thresholds_match_exact_free_space` 及 `n8/n16/n32` 同名门|12例每例 δ_T−2^-12、δ_T、δ_T+2^-12，分别困住/逃逸/逃逸|
|生产 critical_tolerance|`test_t2d_translation.py::test_t2d_full_production_critical_tolerance_has_exact_critical_upper_endpoint`|N4方形生产二分上端点精确落在1/3；不改 API 的 attained=None|
|截面算法与生产腐蚀交叉核对|`test_t2d_translation.py::test_t2d_sections_match_production_arrangement_erosion_on_all_elements`|N4/N8三K，零公差及阈值附近逐顶点、rings一致|
|分解及圆模型精确根|`test_t2d_values.py::test_t2d_circle_limit_exact_roots_and_ratios`、`test_t2d_facet_exact_decomposition_and_n64_n128_trend`|确切根式/多项式恒等式；64/128有限趋势不代替全序列证明|
|欧氏圆盘解析模型|`test_t2d_circle_model.py::test_t2d_circle_model_inner_disk_and_outer_strip_have_same_threshold` 及支持/上移多项式恒等式门|内含圆盘与水平条带在1/2夹逼；沿用喉道分离论证，不是生产曲边API验证|
|冻结证据实际回放|`test_t2d_replay.py::test_t2d_N4_cage_real_replay_and_translation`、`test_t2d_N8_octagon_cage_real_replay`、`test_t2d_N16_K16_cage_real_replay` 及6个逃逸回放门|固定9份实际重跑，完整返回的状态、标签、精确时刻和计数一致；独立笼实际走load_json|
|冻结代理与几何身份|`test_t2d_replay.py::test_t2d_frozen_identity_and_exact_directed_transfer`、`test_t2d_replay_manifest_scope_provenance_and_no_same_delta_contradictions`|9份固定实例重建＋93项δ方向/唯一性/来源元数据一致性；不声称这两个门重建全部93身体|
|全部93真实几何绑定|外置 `audit_certificate_results.py` 的正式只读审计，见§6链接|逐例重建真实截面腐蚀体与固定墙；不是新增pytest门，也不代替固定子集运动回放|
|静态与幂指数|`test_t2d_static.py::test_t2d_exact_sources_reject_internal_floating_injections`|新测试/辅助源无浮点汇点，`**`指数必须为整数常量，含内部注入反门|

对应反向门修改辅助模块内部的数值常量、符号、支持、几何或候选分区。它们不是完成计算后追加假输出；计数/身份守卫另列，不冒充数学缺陷门。所有参数化产物的独立性另由不同阈值/不同腐蚀体检查守护。

## 4. §2.4 全表复核

下表的 δ_disk 与 δ_T 均为精确值；精确比值定义为同一行二者相除，JSON 另存其代数系数。显示小数不是判据。

|N|K|δ_disk（精确）|e* 正角弦 [u1,u2]|S|δ_T（精确）|δ_disk/δ_T（数值）|
|---:|---|---|---|---|---|---:|
|4|方形|2/3−√5/6|[0,1/2]|成立|1/3|0.881966011250|
|4|八边形|24/29−6√5/29|[0,1/2]|成立|12/29|0.881966011250|
|4|K16|109/121−109√5/484|[0,1/2]|成立|109/242|0.881966011250|
|8|方形|9/13−√85/26|[1/4,1/2]|不成立|2/5|0.844274571414|
|8|八边形|48/53−6√17/53|[0,1/4]|成立|24/53|0.969223593596|
|8|K16|101/104−101√17/832|[0,1/4]|成立|101/208|0.969223593596|
|16|方形|19/27−√365/54|[3/8,1/2]|不成立|35/86|0.859773707402|
|16|八边形|11/12−√1105/72|[1/8,1/4]|成立|48/101|0.957350819446|
|16|K16|3815/3839−109√1241/7678|[1/4,3/8]|成立|101/203|0.992167163523|
|32|方形|149/211−√22265/422|[3/8,7/16]|不成立|73/178|0.859696141110|
|32|八边形|201/218−3√4505/436|[3/16,1/4]|成立|131/274|0.962531305559|
|32|K16|4343/4351−101√16705/26106|[1/16,1/8]|成立|202/401|0.988845908786|

**与定理稿不符处：没有发现精确数值不符。** 稿中 (32,K16) 的 e* 栏空缺，本单补出 `[1/16,1/8]` 及其镜像，但不修改定理稿。N=4的三比值均精确等于 `2−√5/2`；N=8八边形/K16均等于 `2−√17/4`。全部平移阈值按全弦最小式计算，不退回仅看主弦的旧公式。

截颈高度逐项为 `11/6, 37/20, 67/36, 567/304`。Q 的全有向支持、严格凸环序、中心对称与 Q⊆A 均有门；C 的全部12个严格余量保存在精确JSON，不以显示舍入判定正负。

## 5. 临界逃逸为何是精确核验

令 `E=A⊖δK`。在 δ=δ_disk 处：

1. 对 Q 的全部 2N 个支持精确核 `r_e−δH_e>0` 及 `(r_e−δH_e)²≥q_e/4`，得到 `B(c,1/2)⊆Q⊖δK⊆E`；至少一个支持取等号。
2. S 给出 E 沿活动单位法向的投影包含于 `[-1/2,1/2]`。C 由 `E⊆conv(A)⊖δK` 的所有可行顶点范数上界给出，该界严格小于 Q 的内切圆半径平方。因此整段转动均自由。
3. 转角取 `cos=m_x/√q, sin=−m_y/√q`，正交恒等式在相应二次域中精确成立。内含圆片的两个明确点转后恰为 `(−1/2,1)`、`(1/2,1)`，故水平投影不是仅“至多”，而是**恰好** `[-1/2,1/2]`。
4. 腔体在 y≤1 的截面半宽单调不减，y≥1 至墙顶的半宽均≥1/2；墙顶以上无墙，地板不高于0。因此旋转后每一点的整条上移射线都自由。

这不是近临界有理代理的极限外推，也不调用 `se2_paths`；有理证书在下一节只是有限 δ 的另外佐证。δ≥δ_disk 的路径延伸依赖凸 K 含原点时腐蚀的单调包含。

## 6. 有限 δ 证书、方形括号与一致性

正式 `run_01` 从头完成，耗时1093.31秒，**93/93 双接受：36笼、54先转后升、3混合路径**；没有拼接pilot。每族笼目标取 `δ_disk−2^-k, k∈{6,8,10}`；九个S族逃逸目标取 `δ_disk+2^-k, k∈{6,9,12,15,18,20}`。

|N|K|不变圆片笼（双接受）|先转后升（双接受）|混合路径（双接受）|
|---:|---|---:|---:|---:|
|4|方形|3|6|0|
|4|八边形|3|6|0|
|4|K16|3|6|0|
|8|方形|3|0|1|
|8|八边形|3|6|0|
|8|K16|3|6|0|
|16|方形|3|0|1|
|16|八边形|3|6|0|
|16|K16|3|6|0|
|32|方形|3|0|1|
|32|八边形|3|6|0|
|32|K16|3|6|0|

[逐例δ/证书/全部返回/435份数据SHA](file:///D:/eab-evidence/reports/codex/T2d_evidence/certificates/run_01/manifest.json)、[只读一致性审计](file:///D:/eab-evidence/reports/codex/T2d_evidence/certificates_audit_01/summary.json)、[源清单](file:///D:/eab-evidence/reports/codex/T2d_evidence/certificates/run_01/source_manifest.json)与[源字节ZIP](file:///D:/eab-evidence/reports/codex/T2d_evidence/certificates/run_01/source_snapshot.zip)分别保留。源清单SHA为 `908a613521f7a69ec7021144750107e2f5062c188a160528cdc290351b1920b2`，证书清单SHA为 `4a0f194a54c6eec8d36567cda4751a27c89fed7bd2476622214ec94cf8d9f72b`，二者不可混称。来源提交是开工基线84bcc04，实际生成树含本单未提交改动；651成员ZIP完整核对，82份active科学依赖逐例前后及结束时无漂移。

全部36笼在同一δ处由原生产T1b判为 `TRAPPED_TRANSLATION`，同δ笼/逃逸矛盾0。实际数学输入有50289个Fraction、2580个整数、0浮点。笼合计500屏障段、500连接四边形、独立侧644703次检查；生产逃逸有限段对计数399，独立侧含射线前缀计数570，二者检查范围不同，不强凑相同计数。

采用已验收T2c2的有向有理代理口径：笼使用略大于目标 δ 的有理代理（较小实体仍困住，则目标较大实体也困住）；逃逸使用略小于目标 δ 的代理（较大实体能逃，则目标较小实体也能逃）。代数目标没有伪装为原有理接口直接接收的输入。

所有笼只用不变圆片；中央 Q⊖δK 只是**真实实体完整凸分区中的宿主片**，不是替换成更小被验身体。完整分区、无重叠、盘包含、屏障及连接由未改的两个核验器检查。独立笼走 `load_json` 文本入口。

逃逸由 `verify_se2_escape` 与 WO-T2a 独立 oracle 双核验。旧独立 oracle 的 `infinite_ray_verified=false` 必须原样保留；另用其独立重建的终点和精确“最低y大于所有墙最高y”的半平面论证补足无限尾，不倒写旧接口的能力。

审查者的pickle未反序列化：隔离进程只作opcode检查，原字典/列表容器不满足“仅数值与元组”的字面条件，因此没有宣布可加载；只从静态文本中读取数值三元组作为提议，原`certified`标志不继承。N32原输入δ略高于目标上限；将其精确减少 `2235567/60816609368011177984` 后，同一5段路径重新双核验通过。过程提议与作废记录见[pilot边界清单](file:///D:/eab-evidence/reports/codex/T2d_evidence/pilot_inventory.json)，不当作正式证明。

方形精确括号为 `δ_disk ≤ δ*_SE2 ≤ U_N < δ_disk+1/4096`：

|N|已双核验逃逸上界 U_N（精确有理数）|有限段数|
|---:|---|---:|
|8|185792159389/549755813888|10|
|16|384996244747/1099511627776|10|
|32|21457082189314646865/60816609368011177984|5|

三个严格gap的二次域表达式及96位有理开区间见[方形括号审计](file:///D:/eab-evidence/reports/codex/T2d_evidence/certificates_audit_01/square_brackets.json)。这只是临界值的括号，不断言其下端点可达。

[固定9份回归索引](file:///D:/eab-wt/cx-e2/tests/data/t2d/index.json)及压缩数据共138773字节；三笼、三条带逃逸、三方形混合逃逸实际重跑，核对完整返回而非当前源码哈希。9个必需ID逐个检查恰好出现一次，杜绝空循环绿；圆片半径>1/2、中心(0,1)、全部圆上顶点及内切半径平方>1/4另有特设守卫。独立 `load_json` 调用受spy守卫。5份快回放和4份慢回放并存；旧slow清单仅追加4个具名节点，原220节点及历史字段不变。[定向回放记录](file:///D:/eab-evidence/reports/codex/T2d_evidence/replay_validation_01/summary.json)：`16 passed in 202.61s (0:03:22)`，运行源无漂移。

**方形 N≥8 的等号仍是猜想。** 本单不得将 G_disk 或路径搜索成功自动升级为 δ*_SE2=δ_disk。P1临界处混合运动的精确构造未作为P0完成条件。

## 7. 分解表与圆形极限

精确分解统一写成

`G_disk=1−δ_disk/δ_T`，`G_facet=√(N²+4)/N−1`，差值为前两式之差。

九个S情形中 `G=G_disk`；三个细刻面方形仅以 `G_disk` 作真实G的上界。下表全为**数值展示**，精确双根式保存在JSON。

|N|K|G_disk|G_facet|G_disk−G_facet|
|---:|---|---:|---:|---:|
|4|方形|0.118033988750|0.118033988750|0|
|4|八边形|0.118033988750|0.118033988750|0|
|4|K16|0.118033988750|0.118033988750|0|
|8|方形|0.155725428586|0.030776406404|0.124949022181|
|8|八边形|0.030776406404|0.030776406404|0|
|8|K16|0.030776406404|0.030776406404|0|
|16|方形|0.140226292598|0.007782218537|0.132444074061|
|16|八边形|0.042649180554|0.007782218537|0.034866962017|
|16|K16|0.007832836477|0.007782218537|0.000050617940|
|32|方形|0.140303858890|0.001951221368|0.138352637522|
|32|八边形|0.037468694441|0.001951221368|0.035517473073|
|32|K16|0.011154091214|0.001951221368|0.009202869846|

三个方形的实际收益只写 `1−U_N/δ_T ≤ G ≤ G_disk`，其中左端依次精确为 `170550830831/1099511627776`、`2686614961959/19241453486080`、`310125927083404425431/2219806241932407996416`。数值区间分别约为 `[0.155115077024,0.155725428586]`、`[0.139626404206,0.140226292598]`、`[0.139708557092,0.140303858890]`。G−G_facet 的已证区间由这两个端点同时减去精确G_facet得到，不把上界冒充确定收益。

圆模型的平移阈值逐 K 顶点核方程 `|k|²δ²+k_xδ−3/4=0` 的最小正根，非预设取最右顶点而略过其余顶点。

本单只精确计算了圆形模型本身；有限 N 收敛到它的论证来自定理稿，本单只以 N = 64、128 的数值显示趋势，未作精确证明。

|K|δ_T∞（精确）|δ_disk∞/δ_T∞（精确）|圆形模型下的比值（数值）|
|---|---|---|---:|
|方形|(√7−1)/4|(√14+√2)/6|0.859311824858|
|八边形|(6√651−72)/169|(√651+12)/39|0.961915426778|
|K16|(2√10101−99)/202|(99+2√10101)/303|0.990123638772|

记号精度说明：方形的极限比值不是单一二次无理数，而在 `Q(√2,√7)` 中，满足 `9x⁴−8x²+1=0`；定理稿给出的根式值正确。不能为了“二次无理数”的措辞将它舍入或误放进单二次域。欧氏圆盘的[独立解析模型门](file:///D:/eab-wt/cx-e2/tests/test_t2d_circle_model.py)给出 δ_T∞=1/2、比值1、收益0：内含盘半径与外侧水平支持同为1−δ，结合全射线分区和喉道分离论证。生产多边形核验器没有假装接收圆边界，这也不是全体有限N收敛的生产门。

|N|K|δ_disk（数值）|δ_T（数值）|比值（数值）|
|---:|---|---:|---:|---:|
|64|方形|0.353333977360|0.411301859800|0.859062435390|
|128|方形|0.353490507992|0.411378943637|0.859281967294|
|64|八边形|0.461130903621|0.479493365501|0.961704450570|
|128|八边形|0.461452789970|0.479700045448|0.961961113718|
|64|K16|0.499596264971|0.504519971289|0.990240809881|
|128|K16|0.499882789801|0.504907132280|0.990048977015|

比值可以围绕极限振荡；这些有限N不是单调收敛证明。64/128两种非方形的最小弦在这次检查中仍满足S，不推断更大N永不漂出允许锥。

**含义（仅限已支撑部分）：** 九个S情形的精确收益并非都等于刻面项；五个主弦例精确相等，另外四例的正差值有精确比较门。指定三K的表仅比较不同容差元在圆形模型下的比值。`N²G_facet=4/(√(1+4/N²)+1)` 给出刻面项的2/N²渐近式。方形约14.07%的圆模型差值仍按δ_disk计算，不把尚未证明的方形刚体阈值等号写成已证含义，也不推广到任意“更接近圆”的容差元序列。

## 8. 静态门、成本与回退锚点

开工工作树干净，分支 `codex-work`、HEAD `84bcc048b22883f1faeab1930414e55885cfcaac`，Python3.12.10，`core.autocrlf=false`。[2713文件回退ZIP](file:///D:/eab-evidence/reports/codex/T2d_evidence/baseline_anchor/source.zip)及[逐文件SHA](file:///D:/eab-evidence/reports/codex/T2d_evidence/baseline_anchor/manifest.json)只作字节锚点，不是新鲜Git树。

新增静态准入清单为 `[]`，浮点汇点准入0、证明缺口准入0；三个分析器、原CRLF policy不改。新测试扫描窄允许标准库整数`isqrt`，并不放开 `math.sqrt` 或其他浮点运算。幂指数不是整数常量（包括变量、Fraction、布尔常量）的`**`被标记；负例植入真实辅助源的AST内。

日常快档5分钟是项目目标，不是本单虚报结果；基线历史快档约32分钟，包装器仅将快档墙钟上限7200秒沿用到本单，全档10800秒及900秒停滞守卫不改。全部pytest关闭cacheprovider、显式basetemp，TEMP/TMP在本单外置tmp，`PYTHONDONTWRITEBYTECODE=1`。

定向第一轮：[命令/源清单/完整日志](file:///D:/eab-evidence/reports/codex/T2d_evidence/targeted_01/)。既有文件仅追加[归档登记](file:///D:/eab-wt/cx-e2/reports/EVIDENCE_ARCHIVE.md)及4个slow节点；24个新增文件，最终仓内净增小于0.32MB，单个新文件最大44195字节。新源码/文档UTF8无BOM/LF，slow清单保留原CRLF。见[仓内逐文件SHA](file:///D:/eab-evidence/reports/codex/T2d_evidence/delivery_final_01/repository_manifest.json)、[交付边界/只读/编码审计](file:///D:/eab-evidence/reports/codex/T2d_evidence/delivery_final_01/delivery_audit.json)及[外置成果逐文件SHA](file:///D:/eab-evidence/reports/codex/T2d_evidence/delivery_final_01/artifact_manifest.json)。净增精确字节数以最终清单为准，避免报告自改造成循环计数。

可复跑命令（PowerShell；使用新的、未占用run名）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP='D:/eab-evidence/reports/codex/T2d_evidence/tmp'
$env:TMP=$env:TEMP
python -X utf8 D:/eab-evidence/reports/codex/T2d_evidence/run_gates.py --name NEW_FAST
python -X utf8 D:/eab-evidence/reports/codex/T2d_evidence/run_gates.py --name NEW_FULL --runslow
```

包装器沿用未改H1运行器，只有外置路径及基于实测的快档时限覆盖。证书工具版本、Python版本、基线提交及实际源字节保存在各自manifest；完整证书重算入口为 `python -X utf8 tools/t2d_certificates.py --run-certificates --output D:/eab-evidence/reports/codex/T2d_evidence/certificates/NEW_RUN`，必须用新目录，预计约18分钟。本次不因整理报告重算冻结数据。内部复核修正了本报告“9份固定几何重建”与“外置93份全审计”的归因范围，未改任何数学结果、测试或证书。

## 9. 全仓验证（原样末行）

<!-- T2D_GATE_RESULTS_BEGIN -->
开工全档 [t2d_baseline_20261026_01](file:///D:/eab-evidence/reports/codex/T2d_evidence/t2d_baseline_20261026_01/summary.json)：GREEN，16558节点，0failed/skip，四片执行节点多重集合等于收集节点，全部内核模块实际执行。原样末行：

```text
4140 passed in 2141.28s (0:35:41)
4140 passed in 2500.15s (0:41:40)
4139 passed in 1759.64s (0:29:19)
4139 passed in 2446.25s (0:40:46)
exact construction AST gate: 0 violation(s)
```

收尾快档 [t2d_final_fast_20261026_01](file:///D:/eab-evidence/reports/codex/T2d_evidence/t2d_final_fast_20261026_01/summary.json)：GREEN，原样末行：

```text
10504 passed in 1919.44s (0:31:59)
```

收尾快慢全档 [t2d_final_full_20261026_01](file:///D:/eab-evidence/reports/codex/T2d_evidence/t2d_final_full_20261026_01/summary.json)：GREEN，16630节点，四分片及静态门原样末行：

```text
4158 passed in 2038.05s (0:33:58)
4158 passed in 2454.32s (0:40:54)
4157 passed in 1721.27s (0:28:41)
4157 passed in 2418.25s (0:40:18)
exact construction AST gate: 0 violation(s)
```

快/全档均0failed、0skip，收集节点与实际调用节点的多重集合一致；70个src/eab模块全部导入并实际执行（63函数模块＋7声明模块），缺失0。两轮2737成员源manifest和[受测源码ZIP](file:///D:/eab-evidence/reports/codex/T2d_evidence/t2d_final_full_20261026_01/tested_source.zip)逐字节相同，ZIP SHA256 `d5bdce41c3987c501f794d392af69c51a381f5a96597c28a10815ce9f47b6dd9`；运行期间导出树及活树漂移均空。两轮结束后仅本报告与归档登记回填，代码/数据不变。[双轮节点与源审计](file:///D:/eab-evidence/reports/codex/T2d_evidence/delivery_final_01/gate_pair_audit.json)保留复核结果。

所有运行采用H1字节副本，`fresh_git_checkout=false`，不是所有者安排的新鲜Git树；没有借用T2c2旧绿或拼接中断运行。每轮 `original_text_bytes.zip`、`text_encoding_map.json` 和 `gate_archive_audit.json` 封存Windows原始文本字节及LF展示映射，JSON语义/末行逐项核对。fast归档器曾遇 `static=null` 的工具分支错误，旧脚本和两个未完成归档ZIP在 `archive_attempt_01_failed/` 标为作废；原日志与测试源未变，修复后独立重做归档，未重跑或拼接测试。

另4份辅助运行文本的[原字节ZIP](file:///D:/eab-evidence/reports/codex/T2d_evidence/misc_original_text_bytes.zip)及[LF映射](file:///D:/eab-evidence/reports/codex/T2d_evidence/misc_text_encoding_map.json)单列。回放summary中的 `log_sha256` 仍指ZIP内原始发出字节，现路径提供LF展示，不改原记录哈希；数学证书文件未做此转换。
<!-- T2D_GATE_RESULTS_END -->

## 10. 遗留与验收边界

- P0逐项闭合见[requirements.json](file:///D:/eab-evidence/reports/codex/T2d_evidence/requirements.json)。本单未发现需要停单的定理错误；方形极限比值的代数次数措辞已在§7明确，不擅改所有者定理稿。
- P1的方形临界混合运动精确构造、N64全套证书未开展，不因此单列PARTIAL。
- 本地多代理内部复核不是Claude安排的独立对抗验收；所有者的新鲜树/合并后最终验证仍由所有者安排。本代理不作Git写，也不代签里程碑验收。

## 11. 验收返修（2026-10-26，基线52d3b63）

所有者本轮裁定告知：三路非作者核查均通过；另份独立实现核对12行精确表、93份证书代理方向及方形严格上界，比较器独立参考178360例0分歧。该结论归于所有者提供的验收结果，不冒称本代理重新执行了这些核查。本节仅记录本轮8项测试与措辞返修。

开工为干净 `codex-work @ 52d3b631118f70750e6af355bd35ddd725e05df5`；[2737文件回退ZIP](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/baseline_anchor/source.zip)与[基线SHA](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/baseline_anchor/manifest.json)已保存。只修改测试与文档；`src/`、核验器、独立侧、精确辅助模块、定理稿、引理、三个分析器、policy及冻结证书只读。不作Git写。

<!-- T2D_ACCEPTANCE_REPAIR_RESULTS_BEGIN -->
### 11.1 八项返修与具名门

本轮八项已闭合；完整可机读对照见[返修 requirements](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/requirements.json)。下面的测试均为最终源版本实际运行，不借用所有者核查结果代替本轮门。

|项|改动及边界|具名门／核验|
|---|---|---|
|1 比较器|补齐 `Surd(3) < Surd(3,1,2)`、`Surd(3) > Surd(3,-1,2)`、`Surd(3,1,2) > 3`。固定种子20261026，10896对、双向21792次比较。|[values](file:///D:/eab-wt/cx-e2/tests/test_t2d_values.py)：`test_t2d_cross_field_order_signs_and_scaled_equalities`、`test_t2d_comparator_fixed_seed_independent_interval_fuzz`、`test_t2d_interval_oracle_rejects_internal_comparator_mutation`；M04被目标断言杀死。|
|2 条件C|`verify_C(4, "square", F(3,20))` 必须在旋转半径处以 `rotation radius` 报错。|同上：`test_t2d_C_unsafe_delta_is_rejected_by_rotation_radius`；M23、M24均杀死。|
|3 圆盘余量|全部12例在 δ_disk+2^-40 调用 `verify_disk_subset`，必须报 `disk is not contained`，不能以稍后另一条断言替代。|[critical escape](file:///D:/eab-wt/cx-e2/tests/test_t2d_critical_escape.py)：`test_t2d_disk_subset_rejects_a_tiny_positive_threshold_excess`；M32杀死。|
|4 台账方向|复制实际台账的笼／逃逸行，分别改到错误的一侧。JSON使用δ_disk±2^-40的96位有理包围区间向错侧端点，精确检查错侧距离在[2^-40,2^-39)；不修改冻结台账。|[replay](file:///D:/eab-wt/cx-e2/tests/test_t2d_replay.py)：`test_t2d_ledger_rejects_tiny_wrong_side_proxy_for_each_kind`；M40由方向语义断言杀死。|
|5 浮点门|`**`／`**=`同查；非整数常量指数拒绝；负指数须能确认底数为Fraction／Surd。标记pow、operator.pow、.__pow__、cmath、decimal、动态import、F.__float__及可解析别名；可静态确认int/int的真除（含1/2与/=）被标记。|[static](file:///D:/eab-wt/cx-e2/tests/test_t2d_static.py)：`test_t2d_exact_sources_reject_internal_floating_injections`、`test_t2d_exact_runtime_outputs_reject_internal_float_injections`；60项AST内部注入、3项运行时内部注入全部拒绝。|
|6 归属|报告开头逐字采用所有者指定的定理稿、石根华理论和M5a归属句。|[requirements第6项](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/requirements.json)保存原句及逐字核对；不改归属合同。|
|7 圆形模型|§7逐字补充“本单只精确计算了圆形模型本身……”限制句；表头改为“圆形模型下的比值”。|同清单第7项逐字核对；有限N的精确收敛证明仍归于定理稿，本单只提供数值趋势。|
|8 原变异复跑|原45条替换及脚本字节不改；最终版本39项非等价全部语义杀死，恰有6项预定等价存活，0环境／收集错误。|[最终逐项语义复核](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/mutation_audit_02/semantic_review.json)，见下表。|

区间oracle仅以原始有理三元组、`Fraction`、整数`isqrt`和有理闭区间细化计算，不调用被测比较器、符号函数或bounds；独立处理精确相等后，非等值须区间严格分离。样本为10000对一般输入、256对Pell近零、512对跨域近等、128对缩放精确等值；按本oracle倍增细化，Pell／跨域两组至少各有一对样本分别细化到不低于512／256位才区间分离，不称每对样本均有此精度下界。精度耗尽报错，不猜相等；另把实际比较器内部替换为恒零，验证oracle语义断言报红。有限模糊测试不冒充比较器全域证明。

静态源局部筛查对解包、海象、循环／with／推导式、函数／异步函数／lambda参数及except／match捕获等简单重绑定保守置为unknown，不把影子变量误认精确构造器。原有故意验证Surd转换抛TypeError的测试，只在**确切调用AST、确切assertRaises上下文和确切测试函数名**同时匹配时窄允许；F.__float__和其他转换仍拒绝。此筛查不是任意Python动态调度的通用类型证明。原三个分析器一字不改，policy原CRLF保留，新增准入清单 `[]`，证明缺口／浮点汇点新增准入均0。

运行时门遍历三个精确模块的120个代表性输出根：含全部12行、9个S情形临界逃逸、3个圆形模型和截面输出；递归检查Surd的a/b/q、字典键值和容器成员，拒绝float及未知输出类型。三处真实内部计算变异分别在弧坐标计算前、墙体构造前、仿射斜率计算处引入整数真除，均由输出检查报红，不在输出列表末尾追加假浮点。这是具名代表输入的输出闭包检查，不称为所有输入的无浮点证明。[最终静态子集记录](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/static/recorded_03/summary.json)。

### 11.2 原45项变异与六项存活理由

[最终完整运行](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/mutation_audit_02/README.md)对45/45条逐一确认唯一字面替换，保存原／变异源、diff、完整stdout/stderr和命令。核查方原脚本SHA256为 `a2b8005088b4997d463293a5347b1d415f9b81cfadb7f20fc84ed5c531d01fe2`，未修改；外置包装只改输出／隔离临时路径及记录，仍用原8 worker、`-x`快档参数，不插入`--runslow`。含慢范围由独立的完整定向运行负责。

39项首失败节点、失败断言与相关栈上下文均逐项核对，不以非零退出码、哈希断言或收集失败充数。M30／M31／M34／M39虽由运行时输出门先触发，栈内失败仍是实际转动对齐、支持点、条带几何或独立截面下确界断言，不是词法拦截。所有6项存活均属所有者预先列明的等价项，理由限于当前合同域：

|存活项|逐项理由|
|---|---|
|M15|只删u1=1/4的正侧候选，其镜像保有相同r/q/H；后续并列极小弦仍从完整edges枚举。并非同时删掉一对镜像弦。|
|M29|12行的非空极小弦镜像对具有相同S真假，因此all／any在本族相同；不推广到混合状态或非对称输入。|
|M33|活动弦定义δ=(r−√q/2)/H，故所核width精确恒为1/2；圆盘包含与端点支持另核。此处==改<=不改变合同域结果。|
|M36|改选镜像活动弦只反转转向；A、K及左右墙反射对称，仍是有效临界逃逸；合同不要求唯一转向。|
|M37|固定对称Q和K的左右支持余量逐项相等，重复右侧不改变结果；[精确事实](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/mutation_audit_02/equivalence_facts.json)核了180对支持，不授权推广到非对称域。|
|M38|保留交点重合的零宽包络段只增加冗余表示；消费者集合去重切点，并在开区间重新取实际最小线，逐点包络与核验结果不变。|

详见[六项等价边界](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/mutation_audit_02/equivalent_survivors.md)。没有其他存活项。

### 11.3 最终验证与原样末行

[targeted_02](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/targeted_02/summary.json)运行全部7个 `tests/test_t2d_*.py`，显式`--runslow`，随后运行未改全仓静态门；源字节全过程不变。原样末行：

```text
78 passed in 307.75s (0:05:07)
exact construction AST gate: 0 violation(s)
```

最终新快档 [t2d_repair_fast_01](file:///D:/eab-evidence/reports/codex/T2d_evidence/t2d_repair_fast_01/summary.json) 为GREEN，10510节点，0failed／0skip，执行节点多重集合与收集相同；70个模块实际执行且缺失0。原样末行：

```text
10510 passed in 1843.71s (0:30:43)
```

完整第一轮targeted_01与mutation_audit保留为前一静态修订版的过程证据；最终只认targeted_02与mutation_audit_02，不拼接两轮结果。第二轮新增的是简单重绑定保守拒绝与11个反例，最终AST反例总数60。快档只跑本轮这一新run；按所有者裁定**不重跑全档**。所有者另行安排的新鲜树全档不是本代理运行，本报告不预签其结果；上轮§10中的验收安排是历史状态，本轮三路非作者通过仅按所有者已提供裁定记载。

### 11.4 字节、归档与交付边界

最终含慢定向与快档的2737成员源清单逐字节一致；原变异脚本复制的911成员中，908个源码／数据成员与该清单逐SHA一致，另3个是既有 `tools/__pycache__` 字节码（h1_execution_plugin、h1_module_coverage、m5c_publish_combined的cpython-312.pyc），不属于H1源码清单。911复制成员运行期间均无漂移，不把这3个缓存冒称源码。[跨运行源与要求审计](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/closure_checks.json)、[快档受测源码ZIP](file:///D:/eab-evidence/reports/codex/T2d_evidence/t2d_repair_fast_01/tested_source.zip)（SHA256 `7ae06a42cdb201e93fa9b16f4e14ed3b076468febc7c7560a00974deb5682c89`）保存实际受测字节。这里仍是H1字节副本，`fresh_git_checkout=false`，不冒称新鲜Git树。快档结束后仅本报告和归档登记回填，代码不变。

只改4个测试和2份报告／登记，0新增或删除仓内文件；其余2731文件与52d3b63锚点一致，671项旧外置成果及核查输入逐SHA未变，93份冻结证书未重算或改来源哈希。新／改仓内文件UTF8无BOM、LF；[只读／编码／净增审计](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/delivery/readonly_encoding_growth.json)给出精确净增字节（门限<5MB），[仓内SHA](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/delivery/repository_manifest.json)、[全部本轮外置成果SHA](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/delivery/artifact_manifest.json)按H1登记在[EVIDENCE_ARCHIVE](file:///D:/eab-wt/cx-e2/reports/EVIDENCE_ARCHIVE.md)。

运行文本的原字节先封存，再提供LF展示：[本轮原文本ZIP](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/repair_original_text_bytes.zip)与[换行／哈希映射](file:///D:/eab-evidence/reports/codex/T2d_evidence/acceptance_repair_20261026/repair_text_encoding_map.json)，快档另有原字节ZIP及映射；JSON语义和日志末行保持不变。日志记录中的原始raw_sha256仍指归档原字节，不为展示换行改写历史哈希。

本轮无未闭合返修项。不改科学结论：方形N≥8的刚体阈值等号仍仅为猜想与括号；P1未开展不计PARTIAL。无commit、push或其他Git写操作。
<!-- T2D_ACCEPTANCE_REPAIR_RESULTS_END -->

T2D_DONE
