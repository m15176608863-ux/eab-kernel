# WO-PERF：接触窗口口径定稿与全套提速报告

> **R7FIX 口径订正（2026-10-12）**：正本 01 的 `PD_closed = inf{||d||₂ : (A+d)∩B=∅}` 是闭集完全分离的下确界；窗口六轴只证明 `rho = inf{||d||₂ : int(A+d)∩int(B)=∅} ≤ w`。恰好贴合的封闭空腔有 rho=1/8、PD_closed=19/8，独立门为 `tests/test_r7fix_docs.py::test_g6g09_tight_closed_cavity_distinguishes_rho_from_pd_closed`。下文历史性能数字不重写，运行政策不变；旧泛化为 PD 的结论在此撤回。

## 结论

全套最后一行：**8582 passed in 865.95s (0:14:25)**；独占进程墙钟 **873.327553 s**。
原 **8267** 个收集节点全部保留，最终 **8582** 个节点；88份原 `test_*.py` 文件逐字节不变，断言、函数主体、参数网格 AST 零修改；5个测试oracle helper的等价改动另行审计。新增 skip/xfail 为零；62 份 fixtures 字节哈希不变。
相对 E5b 记录的1498.403447 s进程墙钟，本轮减少 **41.72%**；距900 s阈值余量 **26.672 s**。时间对比绑定同机记录，仍受系统负载影响。
窗口已按所有者批准定稿为**局部贯入厚度窗口**，保留 `contact_window` 参数名，未改变现有窗口计算语义。未新增浮点过滤；性能优化仅为精确整数代数、精确包围区间排除、重复构造消除和完整内容缓存。
这是指定工作树的验收，不是新鲜 worktree 或六路独立 G6 退出，也不是姊妹求解器部署、工程标定或生产验证。

[全套日志](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/final_full.log) · [命令/墙钟/源码哈希](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/final_full.json) · [JUnit](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/final_full.xml) · [保留审计](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/audit/retention_audit.json) · [完整证据索引](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/INDEX.md)

## 1. 执行契约、范围与回滚锚点

- 目标：局部贯入厚度口径定稿；不弱化任何原门；全套绿色且独占墙钟 ≤900 s。
- 仅改 `D:\eab-wt\cx-e2`；初始干净工作树、分支 `codex-work`、HEAD `c194dbb`。未 commit/push/reset/checkout/stash/worktree。只读边界未写入；临时目录位于本树 PERF_evidence/tmp。
- 非目标：不实现完整欧氏 PD、不更改默认精确语义、LP、本构或姊妹仓库；不删除 fixtures、减网格或新增 skip/xfail。
- 回滚锚：只读 HEAD 与 [字节快照目录](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/baseline)、[基线 SHA-256 清单](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/baseline_manifest.json)。未执行回滚。

## 2. A：窗口口径、可靠性和明确限制

原默认 `None/0` 仍按给定坐标精确判定。显式 `contact_window=w` 只是报告政策，不是库内噪声，也不是完整 PD 判据；参数未改名，所以无需兼容别名迁移。

|分支/声称|精确命题|独立门（test_perf_contact_window.py）|
|---|---|---|
|分离侧|真实距离平方 ≤w² 才纳入相触报告；沿用原有精确距离门|原 test_margin_exact.py 等门保持不变|
|六轴相触|存在 d∈{±w e_x,±w e_y,±w e_z} 使两体内部不交，因此 rho≤\|\|d\|\|₂=w；一般闭表面不保证 PD_closed≤w，原18格仅为凸盒特例|test_each_of_six_axis_certificates_proves_pd_at_most_window（18格）|
|薄壳相触|经认证星核 K 与另一体内部不交；原体每处重叠都落在闭径向壳内，各径向段欧氏厚度≤w|test_shell_certificate_contains_every_overlap_region_but_does_not_bound_pd|
|贯入报告|有限证书未通过，不推出 PD>w|test_shorter_oblique_escape_can_be_missed_so_penetrating_does_not_mean_pd_exceeds_w|
|六轴坐标依赖/不保旋转|同一精确长盒对旋转前相触、旋转后贯入，真实 PD=9/40<w=1/4|test_six_axis_coordinate_dependence_means_rotation_invariance_is_not_guaranteed|
|L1径向壳亦不保旋转|双壁夹持键仅原坐标的 core_A 可证，旋转后壳证书不再通过|test_local_shell_rotation_invariance_is_not_guaranteed_either|

薄壳使用 α=min(w/R,1/2)，R 为相对星心的最大顶点 L1 半径；L2≤L1，加上面上凸组合的范数上界，保证整个径向壳连续体厚度≤αR≤w，而非只检查几个接触采样点。双壁门取 w=1/64、两侧重叠3w/4，独立区间构造证明 PD>1 仍可局部相触。
独立 oracle 只用 Fraction 标量、预给精确正交基、区间积、笛卡尔积和平方范数；先检查全部八个顶点正好等于完整区间积角点，不把 AABB 近似冒充实体。未共用被测 SAT/星核/法向/三角化/距离原语。
[窗口门](file:///D:/eab-wt/cx-e2/tests/test_perf_contact_window.py) · [窗口证明/限制与分项记录](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/window_summary.md) · [独立窗口突变记录](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/mutation_results.json)

四份文档已同步“E5 已完成（窗口为局部贯入厚度口径）”：[README](file:///D:/eab-wt/cx-e2/README.md) · [canon_map](file:///D:/eab-wt/cx-e2/docs/canon_map.md) · [三维设计](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md) · [精确谓词计划](file:///D:/eab-wt/cx-e2/docs/exact_predicates_plan.md)。旧 E5a/E5a2/E5b 报告保留为历史证据，不覆盖历史结论。canon_map 源码指针重新生成，并由全套中的指针门验证。

## 3. B：热点定位（先定位后优化）

使用 E5b 最终 JUnit（8267 passed in 1479.80s；独占墙钟1498.403447 s），先按文件汇总。前20如下；JUnit时间是各节点时间之和，不能拿文件和代替进程墙钟。

|#|测试文件|格数|JUnit累计秒|
|---|---|---|---|
|1|tests.test_invariance_interlock|574|384.060|
|2|tests.test_invariance_geom|2406|199.445|
|3|tests.test_interlocking|17|143.715|
|4|tests.test_interlock_sensitivity|41|93.656|
|5|tests.test_interlock_walls|12|75.465|
|6|tests.test_bb52_g1|17|70.898|
|7|tests.test_interlock_escape|19|61.974|
|8|tests.test_frozen_lowdim|15|37.837|
|9|tests.test_entrance3|37|35.211|
|10|tests.test_invariance_2d|851|27.406|
|11|tests.test_g4_multistep|7|26.787|
|12|tests.test_limit|67|24.580|
|13|tests.test_frozen_ee_sign|99|22.493|
|14|tests.test_kernel2d_predicates|151|21.372|
|15|tests.test_kernel2d_g0|115|18.802|
|16|tests.test_limit_scale|146|17.832|
|17|tests.test_hull_robustness|185|16.603|
|18|tests.test_covers3_g0_vote2|95|15.415|
|19|tests.test_kernel3d_geom|68|12.666|
|20|tests.test_lp_certificates|171|11.864|

另对几何9个代表参数节点和互锁“2次escape+2次候选”做 cProfile。以下为两种代表负载叠加后的生产函数累计时间前20；累计包含子调用、互有重叠，不能加总为全套占比。原始 pstats 与逐文件自身时间均保存。

|#|生产函数|调用数|自身秒|累计秒|
|---|---|---|---|---|
|1|src/eab/kernel3d/covers3.py:576::enumerate_covers3|27|0.018863|5.471307|
|2|src/eab/kernel3d/interlock.py:220::escape_height_covers|2|0.000151|4.721824|
|3|src/eab/kernel3d/interlock.py:187::_exact_escape|2|0.000036|3.161004|
|4|src/eab/kernel3d/interlock.py:192::_exact_escape_cached|2|0.000143|3.160951|
|5|src/eab/kernel3d/interlock.py:130::_candidates|4|0.003895|2.999951|
|6|src/eab/kernel3d/covers3.py:451::ee_cover|23182|0.070646|2.784018|
|7|src/eab/margin.py:336::_resolved|45|0.000158|2.764850|
|8|src/eab/margin.py:344::_resolved_cached|14|0.000176|2.764692|
|9|src/eab/margin.py:295::_resolve|14|0.000552|2.764510|
|10|src/eab/margin.py:170::_witnesses|17|0.000193|2.327553|
|11|src/eab/margin.py:352::body_distance|12|0.000126|2.189803|
|12|src/eab/kernel3d/covers3.py:146::_qedge_contains|56257|0.187072|2.173899|
|13|src/eab/kernel3d/geom3.py:547::polyhedra_overlap|51|0.000879|1.827470|
|14|src/eab/kernel3d/exact_geom.py:819::surface_overlap|51|0.001240|1.826591|
|15|src/eab/kernel3d/interlock.py:173::_nonpenetrating_at|36|0.000155|1.782056|
|16|src/eab/rational3.py:19::dot|409098|0.773444|1.650590|
|17|src/eab/kernel3d/geom3.py:61::dot|385555|0.121251|1.477266|
|18|src/eab/kernel3d/interlock.py:162::escape_candidates|2|0.000172|1.440799|
|19|src/eab/kernel3d/exact_sweep.py:46::surface_events|2|0.000154|1.378213|
|20|src/eab/kernel3d/exact_sweep.py:59::_events_cached|2|0.063133|1.376815|

[JUnit前20文件/节点](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/profile/baseline_top20.md) · [几何cProfile命令/源码绑定](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/profile/geom_representative.json) · [互锁优化前profile](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/interlock/before_top20.txt) · [生产前20 JSON](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/production_profile_top20.json)

### 第一轮全套与第二轮定位

第一轮独占全套原样末行：`1 failed, 8450 passed in 1239.16s (0:20:39)`，墙钟1247.504792 s。这不是交付绿灯。失败来自原有“五个调用点必须经过同一三角形谓词”的内部突变门：整数点—三角形距离绕过了统一 helper。修复为整数齐次投影后仍调用原 triangle_locate；不改原测试。19个相关门绿后再进入最终全套。
真实 pytest 节点的第二轮 cProfile：tied-set 34.977 s 中独立测试 oracle candidates 23.668 s；height 18.216 s 中 exact_escape 11.422 s；interlocking-distance 56.188 s 中 enumerate_covers3 37.199 s。累计时间含子调用，不相加。由此才优化独立 oracle 的整数代数/延迟构造和生产 arrangement witness。原 test_* 门、独立 Gram 路线及完整格数均保留。
[第一轮完整日志](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/first_full.log) · [真实pytest profile与微基准](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/profile_round2) · [单一helper路由修复验证](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/integer_route_fix.xml)

## 4. 等价优化与同输入微基准

|优化|输入/事件数|优化前秒|优化后秒|比值|逐值门文件|
|---|---|---|---|---|---|
|segment_distance_squared|162|0.014103|0.002482|5.68×|test_perf_integer_geometry.py|
|point_triangle_distance_squared|153|0.013186|0.003807|3.46×|test_perf_integer_geometry.py|
|_convex_surface_sat|91|0.063186|0.018521|3.41×|test_perf_integer_geometry.py|
|_qclosest_simplex|360|0.092813|0.006227|14.91×|test_perf_covers.py|
|_qclosest_hull_uncached|180|0.008884|0.004473|1.99×|test_perf_covers.py|
|candidate_content_cache_warm/general|同一输入热命中|0.187981|0.00001450|12964.23×|test_perf_interlock.py|
|exact_static_axis_pruning/general|34|0.191559|0.02309150|8.30×|test_perf_interlock.py|
|candidate_content_cache_warm/degenerate|同一输入热命中|0.185958|0.00001380|13475.21×|test_perf_interlock.py|
|exact_static_axis_pruning/degenerate|89|0.246863|0.05530950|4.46×|test_perf_interlock.py|
|candidate_content_cache_warm/engineering|同一输入热命中|0.177241|0.00001550|11434.91×|test_perf_interlock.py|
|exact_static_axis_pruning/engineering|34|0.196453|0.02412410|8.14×|test_perf_interlock.py|
|3D edge frame正比例整数化|1152|0.008916|0.007018|1.27×|test_perf_edge_frame.py|
|2D VE共分母整数化|3840|0.026465|0.016967|1.56×|test_perf_2d_directions.py|
|2D优化/BB52端到端|samples_per_pair=3, seed=0|0.589181|0.540045|1.09×|test_perf_2d_directions.py|
|精确arrangement/box_same|相同首Fraction witness/None|0.000367|0.000340|1.08×|test_perf_surface_witness.py|
|精确arrangement/box_touch|相同首Fraction witness/None|0.004474|0.003129|1.43×|test_perf_surface_witness.py|
|精确arrangement/box_partial|相同首Fraction witness/None|0.000525|0.000495|1.06×|test_perf_surface_witness.py|
|精确arrangement/box_disjoint|相同首Fraction witness/None|0.003339|0.000279|11.96×|test_perf_surface_witness.py|
|精确arrangement/interlock_seated|相同首Fraction witness/None|0.273684|0.160415|1.71×|test_perf_surface_witness.py|
|精确arrangement/interlock_intruding|相同首Fraction witness/None|0.027029|0.007906|3.42×|test_perf_surface_witness.py|
|精确arrangement/interlock_exact_root|相同首Fraction witness/None|0.178880|0.070188|2.55×|test_perf_surface_witness.py|
|精确arrangement/interlock_seated_engineering|相同首Fraction witness/None|0.299773|0.174361|1.72×|test_perf_surface_witness.py|
|精确arrangement/interlock_intruding_engineering|相同首Fraction witness/None|0.030267|0.008007|3.78×|test_perf_surface_witness.py|
|精确arrangement/interlock_exact_root_engineering|相同首Fraction witness/None|0.190783|0.077375|2.47×|test_perf_surface_witness.py|
|独立测试oracle（非生产）|6个互锁完整候选集|8.401774|4.478385|1.88×|test_perf_oracle_algebra.py|

- 距离/SAT/最近单纯形：统一清除正分母，不作浮点近似。分别保留全部距离活动集、原始曲面凸性证书/完整SAT轴集、最近点及最小支持与平局次序。
- 静止轴排除：速度某分量精确为零时，源特征沿该轴的闭区间必须相交；严格不交才可提前排除。不改变任何事件的有理时间、标签、法向或排序。内循环棱/反向速度仅构造一次。
- 新候选缓存：A/B 顶点及面环、offset、tol、extent_tol、数值类型与直接实现身份构成签名；返回新list防污染。float与Fraction同数值不能混用。热命中微基准不代表全套加速比，也不声称唯一输入首次计算获得该倍数。
- 二维 VE：三向量使用同一正分母，长度阈值精确乘该分母，角度阈值不变；三维 edge frame：各方向独立正比例整数化，归一化内积状态不变。两个既有缓存的签名均未删项，未新增缓存。
- 曲面 arrangement：对体精确平面去重外提、原三角形与对体闭AABB严格分离早停、整三角形同侧切割无效早停、按含offset的完整支持平面分组。保留单元次序和首个Fraction witness，不仅比较布尔状态。
- 独立测试 oracle：只改 dot/cross/vertex/arc/facet 五个 helper 定义，新增局部_minor；用自写整数LCM代数、不导入生产几何，保留原Newell/Gram判据。冻结参考与基线AST一致；逐值对拍模型、状态、完整盖集和完整候选，浮点回退逐位一致。此项是测试执行成本优化，不冒称生产API提速。
- 每项在随机/一般位置、精确退化/平局、单位变化与工程坐标逐值对拍；另含次正规及极端指数输入。精确运算无误差界，**本单没有新增浮点过滤**，因此“新过滤误差界缩小十倍”无适用项。不能将此写成旧过滤已完成新一轮验证。
[整数微基准](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/integer_benchmark.json) · [单纯形微基准](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/profile/covers_benchmark.json) · [互锁微基准](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/interlock/microbench.json) · [异作者整数实现复核](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/profile/independent_review.md)

[witness证明和微基准](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/witness_draft/WITNESS_NOTES.md) · [edge frame证据](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/edge_draft/APPLIED_RESULT.md) · [oracle helper独立审计](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/audit/oracle_helper_audit.json) · [第二轮独立轻审](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/final_independent_review.md)

## 5. C：突变表

突变都注入被测函数内部，不在输出后追加假数据。新门先核对正常路径，然后要求特定看护断言报红；全套中的预期捕获为通过。窗口两条另留直接运行的独立失败日志。

|对象|内部突变|看护门|正确报红断言|
|---|---|---|---|
|窗口薄壳 w → 2w|star_core 的 alpha=min(w/radius,1/2) 改为 2w/radius|test_shell_window_doubling_mutation_is_caught_by_public_rejection|reject-thicker-than-w-shell|
|六轴 → 五轴|contact_models 内去掉 +z 方向|test_five_axis_mutation_is_caught_by_the_missing_direction_gate|axis-public-report|
|新候选缓存删 offset|_candidates 内签名去掉 offset、计算参数仍保留 offset|test_candidate_cache_has_teeth_when_signature_omits_offset|offset content must not alias|
|全局/本地 EE 内部缺陷|covers3.ee_cover / interlock.ee_cover 返回 None|test_candidate_cache_does_not_hide_a_cover_implementation_mutation|原输出确实不同、缓存结果必须等于未缓存缺陷路径|
|精确 AABB 错删闭端点|_events_cached 内严格不相交 < 改为 <=|test_exact_aabb_pruning_keeps_tangent_events_and_detects_strict_bound_mutation|tangent events must survive|
|段距少除一个 D|segment_distance_squared 内 /D² 改为 /D|test_perf_integer_distance_scale_mutation_has_teeth|squared scale restoration|
|SAT 接触报分离|_convex_surface_sat 内 gap>0 改为 >=0|test_perf_integer_sat_boundary_mutation_has_teeth|independent box state|
|单纯形平局改序|_qclosest_simplex 内严格更优比较改为允许相等|test_integer_simplex_support_tie_gate_has_internal_teeth|原最小支持及顺序逐值相等|
|单纯形漏回缩|_qclosest_simplex 内返回点漏除共同分母 scale|test_integer_simplex_rescaling_gate_has_internal_teeth|参考点与支持逐值相等|
|3D整数方向丢符号|_integer_ray 对各分量取abs|test_integer_edge_direction_sign_mutation_has_teeth|analytic edge direction/window state|
|3D整数方向漏分母|_integer_ray 遗漏分量分母，非等比缩放|test_integer_edge_anisotropic_rescaling_mutation_has_teeth|analytic edge direction/window state|
|2D长度阈值漏缩放|_ve_side_directions 内tol省略乘D|test_integer_ve_length_rescaling_mutation_has_teeth|length window retains exact scale and boundary|
|2D严格性错收边界|_ve_side_directions 内strict >改为>=|test_integer_ve_strict_boundary_mutation_has_teeth|exact boundary cannot become strict|
|arrangement错删AABB闭边界|_surface_interior_witness 中严格不交改为闭界剔除|test_arrangement_aabb_is_closed_and_mutation_removing_boundary_has_teeth|coplanar witness must survive|
|arrangement同侧符号错|_surface_interior_witness 原三角形同侧判据反号|test_arrangement_source_plane_sign_mutation_is_caught_by_first_witness|first exact witness changed|
|arrangement平面分组丢offset|仅从coplanar分组键去掉offset，支持平面去重不改|test_coplanar_grouping_keeps_the_plane_offset_not_only_its_direction|parallel planes are not coplanar; pinned (-3/32,-7/16,1/8)|

[机读突变表](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/mutation_table.json)

## 6. 收集节点、标记与全套验证

基线收集 8267；最终收集 8582；增加 315；基线节点丢失0。原 test_*.py 门的断言、函数主体、模块参数格 AST 全部未改；oracle helper例外已独立列账。最终 JUnit 节点集与收集节点集逐项一致，无 failure/error/skipped。
未使用 exhaustive 标记：标记文件0、标记格数0。未另建快速套（工单仅在等价优化后仍>900 s时允许标记）；普通不带 `-m` 命令执行全部原格与新增门。

全套运行前后 src/tests/tools 的逐文件 SHA-256 完全一致：`True`。全套日志 SHA-256：`f00c3855ed5135540f2113caf7b7b4e03543775be59c06f8e75ad97c3685f9b8`。最终文件耗时前20另见 [最终JUnit按文件时间](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/final_by_file.json)。

### 最终 JUnit 前20文件（与E5b同口径）

|#|测试文件|格数|基线累计秒|最终累计秒|
|---|---|---|---|---|
|1|tests.test_invariance_interlock|574|384.060|177.153|
|2|tests.test_invariance_geom|2406|199.445|120.412|
|3|tests.test_interlocking|17|143.715|85.781|
|4|tests.test_bb52_g1|17|70.898|57.991|
|5|tests.test_interlock_walls|12|75.465|45.778|
|6|tests.test_interlock_sensitivity|41|93.656|29.942|
|7|tests.test_interlock_escape|19|61.974|29.684|
|8|tests.test_frozen_lowdim|15|37.837|24.699|
|9|tests.test_invariance_2d|851|27.406|23.883|
|10|tests.test_kernel2d_predicates|151|21.372|20.084|
|11|tests.test_limit|67|24.580|18.117|
|12|tests.test_g4_multistep|7|26.787|17.882|
|13|tests.test_kernel2d_g0|115|18.802|16.832|
|14|tests.test_hull_robustness|185|16.603|15.502|
|15|tests.test_lp_certificates|171|11.864|11.498|
|16|tests.test_limit_scale|146|17.832|11.266|
|17|tests.test_covers3_g0_vote2|95|15.415|11.253|
|18|tests.test_frozen_ee_sign|99|22.493|11.098|
|19|tests.test_entrance3|37|35.211|10.033|
|20|tests.test_invariance_limit|529|10.353|9.770|

### 全套最后一行（原样）

```text
8582 passed in 865.95s (0:14:25)
```
独占进程墙钟：**873.327553 s**；未运行并行 pytest 工作者、未与其他测试/微基准并发。

### 复跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/PERF_evidence/verify_run.py run rerun -- -m pytest -q -p no:cacheprovider --basetemp=reports/codex/PERF_evidence/tmp/rerun --junitxml=reports/codex/PERF_evidence/rerun.xml --durations=30 --tb=short
python -X utf8 reports/codex/PERF_evidence/audit_perf.py --junit reports/codex/PERF_evidence/rerun.xml
python -X utf8 reports/codex/PERF_evidence/benchmark_integer.py
python -X utf8 tools/perf_interlock_benchmark.py
```

## 7. 遗留与信任边界

- 局部窗口本来就不保证完整PD、斜向脱离完备性或旋转不变性；这三项是批准语义的限制，不是暗中声称已修复。
- 几何证明域仍为有效、朝外、闭合嵌入表面；自交/非流形输入、任意凹体全局E、一般折面完整法锥、工程标定和姊妹线接入不在本单。
- 异作者复核没有发现本次整数优化的critical/major，但范围和人数不是正式六路G6；本单禁建worktree，未谎称常驻纪律D/G6退出。
- 热缓存不保证唯一输入工作负载同样提速；耗时绑定本机、当前Python与这次独占运行，不是任意硬件性能承诺。

PERF_DONE
