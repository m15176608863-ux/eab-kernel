# WO-T2b：SE(2) 笼证书与刚体临界公差双侧括号

**当前工单状态：T2B_DONE。** 所有者旧阻塞已解除；本轮补门、97项语义变异重跑、策略CRLF修复、逃逸旁记和新全仓收尾均已完成，未修改生产核验器或独立侧。

**一句话结论：10例的“困住下界—逃逸上界”已完成双路复核，原25份与诊断新增2份笼证书全部双核验通过，d03与d08的下界另有提高；括号仍有宽度，不能据此声称临界值已求出。**

开工日期：2026-10-25；验收返修：2026-10-26（Asia/Singapore）。执行：Codex；所有者：Claude。旧中断运行永久作废；新收尾独立运行，不拼接历史日志。

## 1. 开工合同、范围、回退与归属

| 项目 | 记录 |
|---|---|
| 目标 | P0 精确笼核验、有限提议器、真值/伪造/变异门、十例双侧括号；2026-10-26续裁定补做双核验与P1瓶颈诊断 |
| 实查基线 | `codex-work`，HEAD `146cc76b6e25598f00564438dee7f3282ad52e34`，开工干净；Python 3.12.10 |
| 写域 | `D:/eab-wt/cx-e2` 与 `D:/eab-evidence/reports/codex/T2b_evidence/` |
| 非目标 | C++/eab2、既有数学函数语义、理论合同修改、多体运动、精确墙函数、临界值等号或新颖性表述 |
| 回退锚 | [2426 文件字节 ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/baseline_anchor/source.zip)与[成员 SHA256](file:///D:/eab-evidence/reports/codex/T2b_evidence/baseline_anchor/manifest.json)；不自动 reset，不覆盖所有者后续修改 |
| 成功标准 | P0 逐项证据、真值一致、原24内部变异与核查方97项变异语义复跑、静态零违例、收尾快/全档真实执行；独立核验器合入后每份入表证书双核验且伪造拒收代码一致 |
| 新鲜树边界 | 本代理只使用字节快照/导出，不作 Git 写操作，不宣称所有者新鲜 worktree 验收 |

[机器工作合同](file:///D:/eab-evidence/reports/codex/T2b_evidence/work_contract.json)。`docs/t2b_cage_lemma.md` 第 5 版为只读理论合同；正确性论证引用其 §4，不另写替代理论。SE(2) 指定路径首入归本仓库 M5a；石根华原文归属沿用 T2a D1–D3、D6–D8。单块、邻居固定；块在自身坐标中按 δK 腐蚀；有理八边形 K 为标题模型，方形 K 仅为 T1b 对照。

### 1.1 独立核验器合入后的续工基线

所有者将原交付提交为 `ce14142`，合入已验收的 WO-T2b-V（main `1361e91`）后通知续工。本次实查 `codex-work`、HEAD `5c0f80f4c4eea9406c672dd28954eb1722961fbe`、工作树干净。另保留[2579文件续工ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/baseline_anchor/source.zip)、[成员与89项独立只读文件SHA](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/baseline_anchor/manifest.json)、[续工合同](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/contract.json)。不修改独立实现、独立测试/实例/数据或原生产数学代码。

独立核验一律经其原始文件解析入口 `load_json`（或调用它的 `_load_result`），保留重复键及整数原记号检查；不将普通 `json.load` 结果直接送入 `verify_cage`。只将成功状态 `ACCEPTED` 与 `OK` 视作语义相同，拒收条件 `V0/CHAIN/V1…V6` 必须逐字相同；check id、reason、where及实现计数不要求相同。

### 1.2 验收返修基线与所有者裁定

本轮实查干净 `codex-work`、HEAD `c900033aa809170bb0cbb5d0dbe33b439cd187e7`。所有者将前轮整合提交为 `7b09646`，并自行修正独立静态测试策略钉子（`86b337b`，经 main `1aabd70` 合入），旧 BLOCKED 已解除。回退锚为 [2616文件字节ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/baseline_source.zip)及[成员SHA与执行合同](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/baseline.json)。本轮不改 `src/` 或独立侧任何文件；policy只按明确裁定恢复CRLF，注释补追认日期。

以下是**所有者验收回函**而非本代理新跑数量：25份入表笼证书三方接受；实例独立重建一致；13条逃逸上界经独立SE(2)路径核验成立；不变圆下界在1/256网格上为该方法最优（解析推导）；18147差分逐项一致，2844份接受证书整体碰撞抽检0问题；98个新准入均属证明缺口、浮点汇点0。原测试集的变异牙未通过：97项中49存活，因此本轮必须补门重跑，不能仅凭核验器正确就声称测试充分。

## 2. 生产核验器与合同对照

[实现](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/se2_cage.py)只使用标准库与精确整数/Fraction。浮点提议、搜索失败、显示舍入均不进入接受条件。输入实例与证书分开传入，逐顶点、逐障碍、逐顺序核对。

**证据级判定一律走 JSON 文本入口。** Python dict 入口为内存精确数据便利接口，允许 int/Fraction，且无法恢复已被普通JSON解析丢弃的重复键与 `-0`；不据此冒称解析卫生已检查。具名门 `test_truth_and_science_rechecks_use_json_text_entry` 在5份真值与10份科学下界的实际回放中监视生产参数必须为str、独立侧必须逐文件调用 `load_json`；不是源码字符串或哈希断言。

| 引理条件 | 生产函数 | 具名门（另见参数项及伪造目录） |
|---|---|---|
| §7 规范 JSON、整数原记号、有理数、齐全键 | `_load`、`_decode`、`_rational`、`_index` | `test_certificate_json_exact_round_trip`、`test_noncanonical_rational_is_v0`、`test_noncanonical_integer_token_is_v0`、`test_json_hygiene_is_v0` |
| V0 实例绑定、半径与顶点界 | `_check_v0` | `test_mutation_unbound_instance_geometry_is_killed`、`test_mutation_missing_radius_vertex_bound_is_killed`、`test_mutation_nonpositive_radius_is_killed` |
| §2.0 简单/严格凸环、闭合折线、零轴 | `_simple`、`_convex`、`_closed`、`_axes` | `test_named_forgery_has_contract_rejection_code`、`test_mutation_nonconvex_inner_polygon_is_killed`、`test_mutation_open_connection_and_cap_polylines_is_killed`、`test_mutation_zero_separating_axis_is_killed` |
| §4.1 划分含于、弱分离、面积 | `_contained`、`_partition`、`_weak_separated` | `test_mutation_partition_checks_only_area_is_killed`；伪造 `equal_area_outside_partition` |
| CHAIN、图、起始区间、连接/封口簿记 | `_chart`、`_check_chain` | `test_mutation_independent_endpoint_charts_is_killed`、`test_mutation_interval_crosses_chart_boundary_is_killed`、`test_mutation_start_interval_without_zero_is_killed`、`test_mutation_both_caps_at_same_end_is_killed`、`test_mutation_unchecked_connection_endpoints_is_killed` |
| V1 收缩界 | `_check_v1` | `test_mutation_halved_rotation_contraction_bound_is_killed`、`test_disk_only_intervals_require_no_artificial_rotation_shrink` |
| V2 所有源边的距离界 | `_check_v2` | `test_mutation_omitted_contracted_halfplane_is_killed` |
| V3 圆宿主半平面与 D 顶点 | `_check_v3` | `test_mutation_negative_disk_host_halfplane_is_killed`；伪造 `unused_bad_disk` |
| V4 给出的每段严格片对见证 | `_check_v4`、`_strict_points` | `test_mutation_nonstrict_penetration_is_killed`、`test_mutation_truncated_supplied_witnesses_is_killed`、`test_mutation_searches_for_omitted_witnesses_is_killed` |
| V5 四点同一严格片、图与侧别 | `_check_v5`、`_resolve` | `test_mutation_closed_seam_uses_first_chart_is_killed`、`test_mutation_cap_uses_absent_side_is_killed`、`test_mutation_skipped_connections_is_killed`、`test_mutation_skipped_caps_is_killed` |
| V6 起点自由与带符号绕数 | `_check_v6`、`_winding_value` | `test_mutation_unchecked_initial_pose_is_killed`、`test_mutation_winding_parity_instead_of_integer_is_killed` |
| 条件先后 | `verify_se2_cage` | `test_first_failed_condition_order_is_fixed` |
| 刚体/单位/大坐标小特征 | 全证书变换 | `test_whole_certificate_rigid_frame_and_unit_covariance`、`test_translation_coordinate_is_not_shifted_by_world_origin` |

精确复用 `translation_certificates._orientation`、`_between`、`_intersects`、`_axis_rows`：分别为有理行列式、闭段成员/交点判据和凸片投影区间。`_axis_rows` 与引理的分离轴条件相同；调用前先核严格凸且显式拒零轴，随后只检查证书给出的见证。没有调用会逆序/删点的旧 `_validated_ring` 替代原始环验证，也没有调用旧见证搜索替代证书见证。

`where` 是本单新增诊断字段，不是引理定义的字符串编码：缺失键/破损对象定位到所属对象；半径与顶点的关系定位到 `radius`；划分关系定位到相应 `pieces`。接受集合与拒收编号仍由引理决定。

## 3. 不可信提议器与资源边界

[提议器](file:///D:/eab-wt/cx-e2/tools/t2b_cage_proposer.py)从生成器输入构造候选，不改实例。先严格凸划分，再选择固定中心圆的有理半径下近似和 20 个勾股有理圆周点。D 的闭链使用两图区间。转动片以有理上界距离收缩每条半平面。

区间优先共享 Γ；不同 Γ 时保留全部原始顶点，统一折线参数，用精确断点片给线性连接链的四点同见证。失败区间可局部二分。封口有限尝试向原点缩放；此构造不是一般封口完备算法。区间、折线、凸片、封口步数和耗时均有限制；超限返回 `UNPROVED`，不返回“可逃”。默认成功必须由生产核验器接受；`verify=False` 仅返回 `PROPOSAL_UNVERIFIED`。

具名门见[提议器门](file:///D:/eab-wt/cx-e2/tests/test_t2b_proposer.py)。这些有限候选成功不等于一般输入完备，也不保证最大可能下界。

内部交叉检查发现并修复了圆闭链绕过区间上限、核验结束后未检查时限两个资源入口；新增具名门另覆盖折线顶点、凸片对和连接步数上限。计时采用协作式检查，不抢断单次昂贵调用，故实际返回可能晚于限时；但超时完成的候选会丢弃为 `UNPROVED`，不再返回已认证状态。[修复前后门及来源](file:///D:/eab-evidence/reports/codex/T2b_evidence/resource_repair/after_source_and_checks.json)。

科学扫描来源仍保留修复前的提议器ZIP，不改历史源码哈希：198个成功下界探针均为N=2（上限8），最大生成含核验0.142683 s（上限2 s），未触及这两项缺陷；生产核验器字节未改。修复后以真值/固定小回放验证，不为报告重算全量冻结科学扫描。

### 3.1 续单低资源边界修复

续单发现 `_cap` 在 `max_cap_steps∈{0,1,7}` 时跳过循环，随后读取未赋值的 `failed`，抛出 `UnboundLocalError`。在 `steps=8` 前仅增加两行 `<8` 的 `SearchLimit("homotopy_step_limit")` 守卫，转为提议器原有 `UNPROVED` 资源出口；`max_cap_steps≥8` 分支逐字不变，不改核验器或数学合同。

修前具名门末行 `3 failed, 1 passed in 0.58s`；修后资源、提议器、双核验门合跑末行 `67 passed in 13.79s`。证据见 [前红后绿与两行差异](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/resource_edge_repair)。`diagnostics/final_03` 用修前提议器、128步参数；该分支没有触及缺陷，保留其历史源码快照，不把来源改成修后SHA，也不为文档重算14点。

## 4. 真值门

理论输入来自引理 §5 与 `tests/t2a_truth_geometry.py`；新增低/高房间精确环在[生产侧真值几何](file:///D:/eab-wt/cx-e2/tests/t2b_truth_geometry_prod.py)。原生产交付构造时未读取 WO-T2b-V；本次在所有者合入通知后只读调用独立实现。

<!-- T2B_TRUTH_BEGIN -->
| 真值输入 | δ | 引理预期 | 程序/证书 | N | 屏障段/连接四点 |
|---|---:|---|---|---:|---:|
| 门洞下侧 | 127/1024 | 困住 | 笼 ACCEPTED；圆闭链 | 2 | 20/20 |
| 门洞等号 | 1/8 | 可逃 | 笼提议 UNPROVED；逃逸 ACCEPTED | — | —/— |
| 门洞上侧 | 129/1024 | 可逃 | 笼提议 UNPROVED；逃逸 ACCEPTED | — | —/— |
| 风车 | 0 | 困住 | 笼 ACCEPTED；圆闭链 | 2 | 16/16 |
| 中点楔 | 0 | 困住 | 笼 ACCEPTED；圆闭链 | 2 | 16/16 |
| 菱形对四板 | 0 | 困住 | 笼 ACCEPTED；圆闭链 | 2 | 16/16 |
| 低房间长烟囱 | 0 | 困住 | 笼 ACCEPTED；封口链、只圆 UNPROVED | 1 | 8/128 |
| 高房间长烟囱 | 0 | 可逃 | 笼提议 UNPROVED；逃逸 ACCEPTED | — | —/— |

**合计：5 份笼证书、3 条接受的逃逸路径。** 低房间独立构造为 N=1、Γ 9 顶点、每端8步缩放，转角端点对应半角参数 ±1/23；不复用非作者证书。

[终版真值与计数](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/truth_02/summary.json)；每项实例/证书/逃逸路径见[对应目录](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/truth_02/)。本次5份笼证书全部独立 `OK`，生产仍为 `ACCEPTED`；三条逃逸均复核通过。历史原始JSON中的 `production_only_pending_independent` 是产生时状态，保留来源字节不改；当前验收状态由[逐份双核验记录](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/our_corpus/results.json)补充，不再列为待办。
<!-- T2B_TRUTH_END -->

每个被接受的真值笼另核 T1b 平移困住；低房间只圆提议必须 `UNPROVED`，成功必须封口链。高房间与门洞等号/上侧需实际通过 `verify_se2_escape` 的逐段路径和无穷尾射线，不以图示代替。

## 5. 十例科学表（入表笼证书双核验通过）

[扫描工具](file:///D:/eab-wt/cx-e2/tools/t2b_science.py)复用未改的 `t2_se2_grid.CASES/geometry`：`tia2d` 生成器 + 精确 `erosion`。所有 δ 保持同一有理中心 `(0,1)`。从零以 `1/32` 粗步上扫，在最后成功/首个未证之间二分到 `1/256` 网格（k=8≤20），分别运行只圆与完整提议；“未证”不是困住上界。上界从 T2a 已验 δ 重新精确核验，再尝试三次向下二分的逃逸提议。只接受实际核验通过的上界。

相对宽度明确定义为 `(δ_esc−δ_cage)/δ*_T`。所有括号外结论写“未证”；本单不写十例的 `δ*_SE2 = ...`。

<!-- T2B_SCIENCE_BEGIN -->
| ID | K；邻居腐蚀 | δ_disk | δ_cage | δ_esc | δ*_T | 宽度 | 相对宽度（精确） | N | 封口 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| d01 | 方形；0 | 23/128 | 23/128 | 3/10 | 1/3 | 77/640 | 231/640 | 2 | 否 |
| d02 | 方形；0 | 63/256 | 63/256 | 1851/5120 | 1/2 | 591/5120 | 591/2560 | 2 | 否 |
| d03 | 方形；0 | 63/256 | 1/4 | 21/50 | 3/7 | 17/100 | 119/300 | 4 | 是 |
| d04 | 方形；1 | 13/128 | 13/128 | 1/5 | 3/14 | 63/640 | 147/320 | 2 | 否 |
| d05 | 八边形；0 | 63/256 | 63/256 | 2043/5120 | 24/41 | 783/5120 | 10701/40960 | 2 | 否 |
| d06 | 八边形；0 | 93/256 | 93/256 | 5393/10240 | 24/41 | 1673/10240 | 68593/245760 | 2 | 否 |
| d07 | 八边形；0 | 13/64 | 13/64 | 849/2560 | 24/65 | 329/2560 | 4277/12288 | 2 | 否 |
| d08 | 八边形；1 | 25/256 | 13/128 | 11377/51200 | 12/49 | 6177/51200 | 100891/204800 | 2 | 是 |
| k01 | 方形；0 | 75/256 | 75/256 | 3923/12800 | 1/3 | 173/12800 | 519/12800 | 2 | 否 |
| k02 | 八边形；0 | 93/256 | 93/256 | 977/2560 | 12/29 | 47/2560 | 1363/30720 | 2 | 否 |

标题模型八边形 K 为 d05–d08、k02；其余为方形对照。上表已合并诊断新增下界：**d03 [1/4,21/50]、d08 [13/128,11377/51200]**；其他8例不变。原science_02扫描时全部10例 `δ_cage=δ_disk`，仅表示此资源/网格下区间链没有提高下界，不能推断圆判据完备。7例逃逸上界收窄（d02、d05–d08、k01、k02），其余保留重核通过的 T2a 上界。

原science_02完整扫描总耗时 **132.8529 s**，源文件运行前后字节不变。最终d03/d08下界取 `diagnostic_03/<ID>/instance.json` 与 `certificate.json`；其他8例下界取 `science_02/<ID>/instance.json`、`certificate.json`；圆证书另列 `disk_instance.json/disk_certificate.json`，逃逸端点/路径另列 `escape_instance.json/escape_candidate.json`。每个成功的下界探针都另核 `TRAPPED_TRANSLATION`；10个最终逃逸端点的笼提议均为 `UNPROVED`。

[原冻结科学表/探针轨迹/参数](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02/summary.json) · [最终合并科学表](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/scientific_summary.json) · [10例原证书](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02/) · [20份规范JSON复核](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02_serialized_recheck.json)。

固定小子集实际回放两份证书（八边形 d07 和低房间封口），比较完整状态、计数及有理端点，不钉当前源码：[输入](file:///D:/eab-wt/cx-e2/tests/data/t2b_cage_replay.json)、[具名门](file:///D:/eab-wt/cx-e2/tests/test_t2b_replay.py)。来源提交/工具与源ZIP保留在外置目录，不将历史哈希改成当前哈希。
<!-- T2B_SCIENCE_END -->

### 5.1 入表证书、实例与逃逸复核

- **25/25笼文件接受**：truth_02的5份、science_02的10份下界与10份只圆证书，均生产 `ACCEPTED`、独立 `OK`。原科学扫描有理数、原证书和原扫描源ZIP不变；最终展示表合并两份已核验的提高下界；没有用后来的源码哈希覆盖旧来源。
- **8个燕尾族、121个不同 `(case, δ)` 实例相等**：覆盖此次科学扫描用到的全部成功/失败下界与上界探针，包括73个不同成功下界点（原198条成功记录中有重复），以及24份保存的cage/disk/escape端点实例。生产实例与 `dovetail_instance` 经 `canonical_instance` 比较逐项相等。[实例明细](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/instance_escape/run_01/instances.json)。
- **凸耳k01/k02：无独立生成器，验收时已按支撑距离与竖条剖分独立复核。** 本次实例仍由生产生成器给出，不把独立复核说成已有任意δ的独立生成器。
- **13条逃逸通过**：10条科学上界与3条真值路径，共396段、1204次生产片对检查、1249次独立oracle调用，有限段语义、并列标签/精确事件时刻和所有中间端点位姿一致。独立oracle核的是有限刚体段与尾射线前缀；无限尾射线仍由现有生产精确平移核验器接受，不声称新增了独立无限射线证明。[完整复核](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/instance_escape/run_01/summary.json)。

快档[具名双核验门](file:///D:/eab-wt/cx-e2/tests/test_t2b_dual_verifier.py)固定保存5份真值及10份原下界，另核8个燕尾族的原cage/escape两端、8类拒收条件和4种原始JSON记号；前轮44项通过，本轮新增2项文本入口spy后为46项。冻结数据只核自身完整性，不钉当前源码，不依赖Git或外置目录。[输入与历史来源](file:///D:/eab-wt/cx-e2/tests/data/t2b_dual_cases/manifest.json)。本轮另将原25份及新增d03/d08共27份外置笼文件全部经生产文本与独立load_json重核，全部接受且输入/源码不变：[逐份当前结果](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/cages_text_recheck.json)。不将固定15份spy声称为27份完整回放。

7份收窄上界候选的原 `PROPOSAL_UNVERIFIED` 标签和字节不改；旁置 `science_02/<ID>/escape_verification.json` 明列δ、源SHA、逐段计数和结论。[七份旁记索引与SHA](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/policy_sidecars/escape_reverification_02/summary.json)：260个刚体段、780个生产片对、801次独立oracle调用，全部通过；无限尾射线为生产精确核验，独立有限oracle边界未扩大。

### 5.2 合并下界的来源（原始文件不改）

瓶颈诊断增加资源后，在原“首未证δ”处找到以下两份封口笼证书；两核验器均接受，且平移另核为 `TRAPPED_TRANSLATION`。原 science_02 表和外置JSON仍为冻结历史结果；这两行现已合并进§5最终表；不改原 δ_disk。上界继续使用§5.1已复核的逃逸证书。

| ID | 新 δ_cage | δ_esc | δ*_T | 新宽度 | 相对宽度 | N | 封口 |
|---|---:|---:|---:|---:|---:|---:|---|
| d03 | 1/4 | 21/50 | 3/7 | 17/100 | 119/300 | 4 | 是 |
| d08 | 13/128 | 11377/51200 | 12/49 | 6177/51200 | 100891/204800 | 2 | 是 |

所以累计已复核**原25份笼文件＋2份新下界证书**且全部双核验通过；最终表采用其中25份（5真值＋10当前下界＋10圆），另2份旧下界保留溯源，不是27个独立几何实例。[新增证书](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/diagnostic_03)，[逐字节复制与SHA](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/new_certificates_copy.json)，[诊断实例复核](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/instance_escape/diagnostic_instances_final_03/summary.json)。8个燕尾族原121个不同 `(case,δ)` 加4个新d07内点，共125个不同δ实例独立比对相等；14份诊断保存实例中12份有独立燕尾构造器且全部相等。凸耳两例与无限尾射线的独立性边界仍按§5.1保留。

## 6. 变异与伪造集

[24 项具名变异门](file:///D:/eab-wt/cx-e2/tests/test_t2b_mutations.py)在运行中编译生产源码的内部变体：原版同一语义 guard 先绿，再要求指定语义 AssertionError 红；不接受源码哈希或偶然异常为杀变异证据。[39 份精确伪造](file:///D:/eab-wt/cx-e2/tests/data/t2b_forgeries/)逐项断言拒收编号；[对应表](file:///D:/eab-evidence/reports/codex/T2b_evidence/tests_summary.json)覆盖引理各版修订类别。

零轴门直接进入生产 SAT 辅助函数，因为合法公共入口的严格凸守卫已把重复顶点先拒；这是内部防线门，不冒称删除它就能越过仍在的前置守卫。绕数 +2 和 −2 都须接受，不能用奇偶性代替带符号整数。起点贯入门确认已通过 V4/V5 并在 V6 拒收，排除前置数据错误遮挡。

### 6.1 双方语料交叉

生产侧初轮130次配对（25份入表、39份伪造、66份附加正例）全部判定/条件代码一致。独立侧505次配对（462个字节不同的实例/证书对；67接受、438拒收）也全部一致，包含acceptance与hand_cages全部保存样例、独立非变异测试实际生成输入、35份变异测试的原版输入，以及解析/CLI补集。409项独立非变异测试实际执行通过；故意禁用守卫后的变异核验器不参与原版判定对拍。

[生产侧逐项记录](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/our_corpus/results.json) · [独立侧覆盖清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/v_corpus/inventory.json)。这些是有限语料实测，不将所有者先前9042例差分或95项变异的验收数字冒称本次重跑结果。

补充运行我方6个原测试文件，245项通过；仅在未变异生产原函数上捕获192次有效调用，独立文件解析核验192次 `OK`，共71个不同原始(instance,certificate)字节对。覆盖这6个原测试文件中全部实际正例构造，动态编译的禁守卫变体从未参与对拍。新资源8步正例及两份新诊断证书另外双核验，不计入这192次。这192次不是与原130次、独立侧505次合并去重后的总数，三组计数分别保留。[逐nodeid捕获记录](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/our_corpus/positive_capture/summary.json)。

### 6.2 所有者变异核查后的补门

原24项门不能代替核查方97项单项变异：原测试集有49项存活，本次补足遗漏防线而不修改生产核验器。[新增27个具名伪造测试](file:///D:/eab-wt/cx-e2/tests/test_t2b_acceptance_forgeries.py)逐项断言首个拒收代码；[54个JSON及双SHA清单](file:///D:/eab-wt/cx-e2/tests/data/t2b_forgeries/acc/manifest.json)仅作CRLF→LF，未重编码JSON。原文与入库版本共54对双核验全部按预期拒收、0分歧，见[逐项复核](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/forgeries/dual_recheck.json)。原39份伪造保留，现共66份。

| 条件 | 新增伪造ID |
|---|---|
| V0 | B0x、P06、P02、A01、P03、P04、R03、R07、H12、H13、R06 |
| CHAIN | K03、K06、K07、K08、K10、K11 |
| V2 | V201、V204 |
| V3 | V302 |
| V4 | V401、V403 |
| V5 | V501、V502、V503、V505 |
| V6 | V603 |

[新增卫生与接触门](file:///D:/eab-wt/cx-e2/tests/test_t2b_acceptance_hygiene.py)逐项覆盖 radius `"6/2"`、`3.0`、rho布尔、嵌套未知键、错误format/kind、三坐标点、凸环共线点、区间数不符、内核片下标越界，均以原始文本双核验拒收V0；`test_strict_points_edge_touching_vertex_is_not_penetration` 用边恰接顶点及严格重叠正对照。首次卫生/接触及文本入口门末行 `57 passed in 3.34s`；27伪造门末行 `27 passed in 2.63s`。补强单侧接触、未知嵌套键及结构化越界拒收后，最终三文件合跑 `84 passed in 6.57s`。只将I/O和调用断言直接写入真实具名测试驱动体，不新增数值oracle、策略白名单或准入；原24条helper证明缺口诊断随其消除，三个修改测试文件局部静态0。

<!-- T2B_ACCEPTANCE_MUTANTS_BEGIN -->
最终轮 `definitive_04`：**97项全部完成，82项被语义测试杀死，15项仅落在所有者明确允许列表，非允许存活0。** 控制原版末行 `365 passed in 24.58s`；每项执行同一365节点，共35405个变异节点调用，无skip。总耗时 645.850 s。97份变体源码SHA互异，每份为核查方定义的一个生产内部变异；不在结果后追加假数据。

| 条件/范围 | 单项变异 | 语义杀死 | 允许存活 |
|---|---:|---:|---:|
| V0/parse | 14 | 13 | 1 |
| V0/binding | 3 | 3 | 0 |
| V0/rings | 10 | 7 | 3 |
| V0/radius | 3 | 3 | 0 |
| V0/partition | 7 | 6 | 1 |
| V0/disk | 2 | 2 | 0 |
| V0/counts | 8 | 7 | 1 |
| V0/indices | 2 | 1 | 1 |
| CHAIN | 12 | 9 | 3 |
| V1 | 7 | 5 | 2 |
| V2 | 7 | 6 | 1 |
| V3 | 4 | 4 | 0 |
| V4 | 4 | 4 | 0 |
| V5 | 9 | 8 | 1 |
| V6 | 5 | 4 | 1 |
| **总计** | **97** | **82** | **15** |

允许存活：`H01、R02、R05、R10、P05、C03、C10、K01、K04、K05、V103、V104、V206、V508、V601`。全部是所有者预列的等价或不影响健全性项；未引入任何额外豁免或新蕴含论证。所有者原允许的H11、V404也已被新增具名门杀死。这里不将“存活”改称“杀死”，亦不把82/97当全输入域正确性证明。

仅统计原版先绿、变体触发的语义AssertionError（含明确的“非法下标/区间数必须返回V0而非泄漏IndexError”公共返回合同断言）。静态准入10次、站点不唯一/源匹配23次失败单独排除，源码哈希不作杀死；未捕获的意外异常不算语义杀死。01轮因外部basetemp父目录未创建作废；02轮因补门追加而中断作废；03轮完整82/15但为闭子集整理前的诊断轮，不拼进04。最终只采用04当前测试字节。

[最终97项汇总](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/mutation97/definitive_04/acceptance_summary.json) · [逐项测试/源码差异/原始日志](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/mutation97/definitive_04/results/) · [受测字节ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/mutation97/definitive_04/tested_source.zip)。
<!-- T2B_ACCEPTANCE_MUTANTS_END -->

## 7. 瓶颈诊断与对 T2c 的含义

### 7.1 原 science_02 扫描性能（历史诊断）

| ID | 生成含核验/s | 其中核验/s | 区间数 | 区间Γ总顶点数 | 全部折线顶点数 | 原扫描首未证δ |
|---|---:|---:|---:|---:|---:|---:|
| d01 | 0.016996 | 0.005793 | 2 | 14 | 42 | 47/256 |
| d02 | 0.020707 | 0.007161 | 2 | 14 | 42 | 1/4 |
| d03 | 0.017025 | 0.005902 | 2 | 14 | 42 | 1/4 |
| d04 | 0.018330 | 0.006062 | 2 | 14 | 42 | 27/256 |
| d05 | 0.015629 | 0.005453 | 2 | 14 | 42 | 1/4 |
| d06 | 0.023098 | 0.007766 | 2 | 14 | 42 | 47/128 |
| d07 | 0.023262 | 0.007851 | 2 | 14 | 42 | 53/256 |
| d08 | 0.022111 | 0.007586 | 2 | 14 | 42 | 13/128 |
| k01 | 0.124002 | 0.024209 | 2 | 22 | 66 | 19/64 |
| k02 | 0.124061 | 0.023290 | 2 | 22 | 66 | 47/128 |

上述为冻结 science_02 的原测量，不是本续单最终性能。顶点计数含闭合重复端点，全部折线计数包含连接/封口且不去重。旧d07单次探索不替代下面的完整final_03；本次P1已实际补做。

### 7.2 续单两份新笼证书性能（诊断）

以下直接读取原 `proposal.diagnostic` 的生成含核验秒数与核验秒数，不重跑计时。区间数和顶点数由对应原证书精确计数；全部折线顶点数等于各区间Γ顶点数，加所有links/caps内每条chain折线顶点数，包含闭合重复端点，不去重。

| ID | δ_cage | 生成含核验/s | 其中核验/s | N | 区间Γ总顶点数 | 全部折线顶点数 |
|---|---:|---:|---:|---:|---:|---:|
| d03 | 1/4 | 7.165003 | 1.745146 | 4 | 388 | 13580 |
| d08 | 13/128 | 4.858031 | 2.045540 | 2 | 514 | 17990 |

[两份原proposal及证书](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/diagnostic_03)。[内部数值复算记录](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/diagnostics/review.json)核对14点读数、444项V1/比值和334个原点样本；这是内部只读复算，不是所有者安排的里程碑独立对抗验收。

### 瓶颈诊断与对 T2c 的含义（续单实测）

切片与失败读数均为**诊断**，不能单独形成困住结论；仅下述两份新双核验笼证书提供新增困住下界。以 `final_03` 为唯一完整测量轮；14 点均完成，源码输入 SHA256 在运行前后相同。`pilot_d01` 为开发试测；`final_01` 因观测器连接角标注被外层局部变量覆盖而停止，`final_02` 为切换原 T2a 角范围而在首例结束前停止；两轮均明列作废，未拼接结果。本轮测量时既有核验器、提议器和原科学表未改；其后提议器低资源边界修复的来源版本须与此轮历史快照分列。

#### 测量定义与边界

- 每点原提议器采用合作式 20 s 预算、最多 32 区间、每折线 1025 顶点、连接/封口最多 128 步、4 次细化。观测器临时包裹 `_cells`/`_witness`，不改变返回判定；观测开销计入预算，20 s 不是强制打断的硬实时上限。
- 角范围来自**原 WO-T2a** 的 `certificates/<id>.json`，不是后续缩小上界的路径；逐段有理复合旋转保存全部累计角端点。原路径只提供角范围，绝不声称该路径在本次较小 δ 下仍可达。
- 在该范围按有理 λ 分 8 段，并在图边界拆段，检查端点与中点；另加实际捕获失败区间的端点/中点。ρ=0 只用精确转动片，不加不变圆片。候选 Γ 须逐段具有同一严格片对见证、闭合且对原点绕数非零。未找到只表示该有限构造未证。
- 对固定 ρ=0 Γ 及固定片对，逐条宿主半平面统一内移 `ρ × 有理欧氏法向范数上界`，用精确算术重新检查全部端点严格 SAT。12 次二分给成功/失败 ρ 包络；失败上界再次实际检查。若搜索上限仍成功，仅报单侧成功下界，不冒称最大值。容量定义是本 Γ/本见证/本有理内移构造的容量，不是所有 Γ 的最优值。
- 需求量为 V1 **规定的最小充分收缩界** `ρ_V1 = 2r sqrt(max ((u−u_mid)^2/((1+u²)(1+u_mid²))))`。保存其有理平方；平方根、比值与归一 SAT 排名仅为诊断浮点。比较同一中点区间原宽与 1/2、1/4 宽。严格约束的失败边界不当成等号成功。
- 比值 >1 仅说明所选 Γ/见证在当前收缩构造下损失余量，不能证明引理方法全局太松；比值 ≤1 仅关于 V2/V4 局部覆盖，不含连接/封口。所有采样切片成功也不证明全转角范围成立。部分角度的 t=0 已贯入，绕原点屏障成功不等于该角存在原点自由分量。
- 失败盖选取规则：在该次实际查询点中，对每个片对取所有 SAT 轴/点的最小欧氏归一重叠量，再选最大者；并列保留生成顺序。保存原始精确分子、法向平方、支撑顶点索引，可复算。它是“最接近覆盖”的诊断标签，不是分离证书。

#### 10 个首未证点与 d07 的 4 个内点

下表的比值取**实际最后捕获失败所处区间**；若该处没有可用区间/ρ=0 屏障，则明确未定义。已成功的新证书行改列采样区间，不虚构最终失败。`采样屏障` 包含额外失败区间样本；`t=0贯入` 只计这些样本。

|例/点|δ|20 s 提议结果|采样屏障|t=0贯入|比值所用 λ 区间|ρ_V1/容量（原宽）|区间宽/4 后|
|---|---:|---|---:|---:|---|---|---|
|d01/first_unproved|47/256|UNPROVED|27/27|22|['-1/8', '0']|[1.3307, 1.3377]|[0.33232, 0.33406]|
|d02/first_unproved|1/4|UNPROVED|23/23|16|['-1/8', '-1/16']|[0.40767, 0.40898]|[0.10174, 0.10207]|
|d03/first_unproved|1/4|CERTIFIED_CAGE|23/23|4|['35/312', '5/39']|[0.12266, 0.12313]|[0.030645, 0.030761]|
|d04/first_unproved|27/256|UNPROVED|23/23|15|['-1/8', '-1/16']|[0.47638, 0.47817]|[0.11889, 0.11934]|
|d05/first_unproved|1/4|UNPROVED|23/24|16|['-1/8', '-1/16']|[0.45426, 0.45589]|[0.11337, 0.11378]|
|d06/first_unproved|47/128|UNPROVED|25/25|15|['-1/2', '-7/16']|[0.32471, 0.32571]|[0.08047, 0.080717]|
|d07/first_unproved|53/256|UNPROVED|28/28|21|['-1/16', '0']|[0.61214, 0.61508]|[0.15299, 0.15373]|
|d07/interior_1|2929/12800|UNPROVED|25/25|20|['-1', '-15/16']|[1.8127, 1.8631]|[0.4479, 0.46034]|
|d07/interior_2|1629/6400|UNPROVED|22/25|17|['-1', '-15/16']|未取得ρ₀屏障，未定义|未取得ρ₀屏障，未定义|
|d07/interior_3|3587/12800|UNPROVED|21/25|15|['-1', '-15/16']|未取得ρ₀屏障，未定义|未取得ρ₀屏障，未定义|
|d07/interior_4|979/3200|UNPROVED|21/25|15|['-1', '-15/16']|未取得ρ₀屏障，未定义|未取得ρ₀屏障，未定义|
|d08/first_unproved|13/128|CERTIFIED_CAGE|21/21|2|['49/1096', '7/137']|[0.044096, 0.044245]|[0.011023, 0.01106]|
|k01/first_unproved|19/64|UNPROVED|20/20|0|['-1', '-15/16']|[1.765, 1.8127]|[0.43612, 0.4479]|
|k02/first_unproved|47/128|UNPROVED|20/20|0|['-1', '-15/16']|[2.2357, 2.3128]|[0.55241, 0.57146]|

#### 原 T2a 转角范围的独立读数（不混入额外失败角）

本表仅取 `sample_origin=escape_angle_range_grid` 的 8 个区间及其 17 个端点/中点。下面的最小/最大比值包络分别由各中点比值下/上界取 min/max；“最差区间”按最大比值上界排序，是包络意义的最差候选，非连续角优化。缩宽/4仍固定原中点Γ。无法构造ρ=0屏障的具体角单列；该角的容量比值未定义，绝不由别的角替代。比值汇总仅覆盖已经取得Γ的中点。

|例/点|原T2a源δ|原λ范围|原范围采样成功|额外样本成功|原范围ρ0未证角|中点比值最小值包络|中点比值最大值包络|最差中点区间|缩宽/4后最大包络|法向上界最大相对因子|
|---|---:|---|---:|---:|---|---|---|---|---|---:|
|d01/first_unproved|3/10|['0', '169/213']|17/17|10/10|无|[0.52206, 0.52377]|[1.1556, 1.1624]|['169/1704', '169/852']|[0.28766, 0.28934]|1.00000023702|
|d02/first_unproved|2/5|['0', '85/113']|17/17|6/6|无|[0.53881, 0.54032]|[2.1909, 2.228]|['595/904', '85/113']|[0.53884, 0.54797]|1.00000001006|
|d03/first_unproved|21/50|['0', '5/39']|17/17|6/6|无|[0.093237, 0.093503]|[0.12266, 0.12313]|['35/312', '5/39']|[0.030645, 0.030761]|1.00000018586|
|d04/first_unproved|1/5|['0', '94/121']|17/17|6/6|无|[0.3824, 0.38341]|[1.0097, 1.0149]|['47/484', '47/242']|[0.25138, 0.25268]|1.00000021585|
|d05/first_unproved|9/20|['0', '59/113']|17/17|6/7|无|[0.32347, 0.32425]|[0.4724, 0.47409]|['59/904', '59/452']|[0.11788, 0.1183]|1.00000001006|
|d06/first_unproved|11/20|['0', '7/8']|17/17|8/8|无|[0.47173, 0.47306]|[1.0173, 1.022]|['7/64', '7/32']|[0.25299, 0.25417]|1.00000016465|
|d07/first_unproved|7/20|['0', '40/51']|17/17|11/11|无|[0.54121, 0.54292]|[1.1561, 1.1629]|['5/51', '10/51']|[0.28782, 0.28951]|1.00000002628|
|d07/interior_1|7/20|['0', '40/51']|17/17|8/8|无|[0.57777, 0.57973]|[1.3923, 1.4021]|['5/51', '10/51']|[0.3466, 0.34906]|1.00000028427|
|d07/interior_2|7/20|['0', '40/51']|17/17|5/8|无|[0.63107, 0.63341]|[1.8829, 1.901]|['5/51', '10/51']|[0.46873, 0.47324]|1.00000052158|
|d07/interior_3|7/20|['0', '40/51']|16/17|5/8|['40/51']|[0.70091, 0.70379]|[4.3024, 4.4458]|['35/51', '40/51']|[1.0571, 1.0924]|1.00000010191|
|d07/interior_4|7/20|['0', '40/51']|16/17|5/8|['40/51']|[0.79916, 0.80291]|[26.675, 33.344]|['35/51', '40/51']|[6.5543, 8.1929]|1.00000035004|
|d08/first_unproved|6/25|['0', '7/137']|17/17|4/4|无|[0.038024, 0.038135]|[0.044096, 0.044245]|['49/1096', '7/137']|[0.011023, 0.01106]|1.00000034328|
|k01/first_unproved|8/25|['0', '13/74']|17/17|3/3|无|[0.44142, 0.44583]|[22.372, 44.744]|['39/592', '13/148']|[5.5898, 11.18]|1.00000706448|
|k02/first_unproved|2/5|['0', '11/63']|17/17|3/3|无|[0.66486, 0.67509]|[7.4316, 8.9179]|['11/252', '11/168']|[1.8572, 2.2286]|1.00000422752|

法向相对因子为 `有理范数上界 / sqrt(精确法向平方)` 的最大诊断值；原始实例、旋转λ、有理范数上界算法及源快照可重算每条边，表中浮点仅显示舍入。因子接近1不等于对所有几何误差作上界证明。
原范围采样中，d07内点3与4仅在λ=40/51没有构造出ρ=0屏障，其余原范围样本均取得严格绕数屏障；额外负角失败不能混称为原T2a角范围失败。端点未证处不做容量比值，已取得的其他中点比值仍单独列示。

#### 实际失败位置与盖标签

- **d01/first_unproved，δ=47/256**：最后捕获 `_connect`，λ区间=['-1/8', '0']，λ端点=0，连接/封口 at=4，段=77，步=3/16。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=1、parent内片=0、扁平片=1；限制特征 edge-edge，移动支撑顶点=[1, 2]，障碍支撑顶点=[0, 1]，归一重叠=-0.013377。
  - 最后**完成**尝试返回：`{"mode": "capped:1/4:8", "detail": {"reason": "connection_four_point_witness_missing", "where": {"step": 22, "segment": 77, "steps": 128}, "interval": 3}}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d02/first_unproved，δ=1/4**：最后捕获 `_cap`，λ区间=['-1/8', '-1/16']，λ端点=-1/8，连接/封口 at=0，段=74，步=43/64。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=1、parent内片=0、扁平片=1；限制特征 vertex-edge，移动支撑顶点=[2]，障碍支撑顶点=[0, 1]，归一重叠=-0.010952。
  - 最后**完成**尝试返回：`{"mode": "capped:1/16:4", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d03/first_unproved，δ=1/4**：本轮成功，不存在最终失败位置。新证书通过生产与独立核验器，并复核为 `TRAPPED_TRANSLATION`；原有限预算扫描的“未证”不是不可笼证明。该新证书保存在诊断目录，不回写冻结科学表。
- **d04/first_unproved，δ=27/256**：最后捕获 `_cap`，λ区间=['-1/8', '-1/16']，λ端点=-1/8，连接/封口 at=0，段=294，步=52/64。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=0、parent内片=0、扁平片=0；限制特征 vertex-edge，移动支撑顶点=[0]，障碍支撑顶点=[1, 2]，归一重叠=-0.00028838。
  - 最后**完成**尝试返回：`{"mode": "capped:1/16:4", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d05/first_unproved，δ=1/4**：最后捕获 `_cap`，λ区间=['-1/8', '-1/16']，λ端点=-1/8，连接/封口 at=0，段=2，步=19/32。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=1、parent内片=0、扁平片=1；限制特征 edge-vertex，移动支撑顶点=[1, 2]，障碍支撑顶点=[0]，归一重叠=-0.0054613。
  - 最后**完成**尝试返回：`{"mode": "capped:1/16:4", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d06/first_unproved，δ=47/128**：最后捕获 `_cap`，λ区间=['-1/2', '-7/16']，λ端点=-1/2，连接/封口 at=0，段=213，步=50/64。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=1、parent内片=0、扁平片=1；限制特征 vertex-edge，移动支撑顶点=[2]，障碍支撑顶点=[0, 1]，归一重叠=-0.0011501。
  - 最后**完成**尝试返回：`{"mode": "capped:1/4:16", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d07/first_unproved，δ=53/256**：最后捕获 `_connect`，λ区间=['-1/16', '0']，λ端点=0，连接/封口 at=4，段=39，步=10/128。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=1、parent内片=0、扁平片=1；限制特征 edge-edge，移动支撑顶点=[1, 2]，障碍支撑顶点=[0, 1]，归一重叠=-0.0045346。
  - 最后**完成**尝试返回：`{"mode": "capped:1/8:8", "detail": {"reason": "connection_four_point_witness_missing", "where": {"step": 21, "segment": 77, "steps": 128}, "interval": 3}}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d07/interior_1，δ=2929/12800**：候选Γ逐顶点覆盖检查失败（尚无对应完整见证段，查询点=[['2', '2']]），λ区间=['-1', '-15/16']，λ端点=None，连接/封口 at=None，段=None，步=None/None。最近盖：移动 {'kind': 'rotated', 'piece': 0}，障碍 parent=1、parent内片=0、扁平片=1；限制特征 vertex-edge，移动支撑顶点=[1]，障碍支撑顶点=[0, 3]，归一重叠=-0.088111。
  - 最后**完成**尝试返回：`{"mode": "capped:1:32", "detail": {"reason": "individual_interval_has_no_winding_loop", "interval": 0}}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d07/interior_2，δ=1629/6400**：封口目标原点检查失败（尚未开始缩放链，无链步数），λ区间=['-1', '-15/16']，λ端点=-1，连接/封口 at=0，段=None，步=None/None。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=0、parent内片=0、扁平片=0；限制特征 vertex-edge，移动支撑顶点=[0]，障碍支撑顶点=[1, 2]，归一重叠=-0.027359。
  - 最后**完成**尝试返回：`{"mode": "capped:1:32", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d07/interior_3，δ=3587/12800**：封口目标原点检查失败（尚未开始缩放链，无链步数），λ区间=['-1', '-15/16']，λ端点=-1，连接/封口 at=0，段=None，步=None/None。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=0、parent内片=0、扁平片=0；限制特征 vertex-edge，移动支撑顶点=[0]，障碍支撑顶点=[1, 2]，归一重叠=-0.060736。
  - 最后**完成**尝试返回：`{"mode": "capped:1:32", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d07/interior_4，δ=979/3200**：封口目标原点检查失败（尚未开始缩放链，无链步数），λ区间=['-1', '-15/16']，λ端点=-1，连接/封口 at=0，段=None，步=None/None。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=0、parent内片=0、扁平片=0；限制特征 vertex-edge，移动支撑顶点=[0]，障碍支撑顶点=[1, 2]，归一重叠=-0.094114。
  - 最后**完成**尝试返回：`{"mode": "capped:1:32", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **d08/first_unproved，δ=13/128**：本轮成功，不存在最终失败位置。新证书通过生产与独立核验器，并复核为 `TRAPPED_TRANSLATION`；原有限预算扫描的“未证”不是不可笼证明。该新证书保存在诊断目录，不回写冻结科学表。
- **k01/first_unproved，δ=19/64**：封口目标原点检查失败（尚未开始缩放链，无链步数），λ区间=['-1', '-15/16']，λ端点=-1，连接/封口 at=0，段=None，步=None/None。最近盖：移动 {'kind': 'exact', 'piece': 1}，障碍 parent=1、parent内片=1、扁平片=5；限制特征 vertex-edge，移动支撑顶点=[2]，障碍支撑顶点=[0, 3]，归一重叠=-0.17469。
  - 最后**完成**尝试返回：`{"mode": "capped:1:32", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。
- **k02/first_unproved，δ=47/128**：封口目标原点检查失败（尚未开始缩放链，无链步数），λ区间=['-1', '-15/16']，λ端点=-1，连接/封口 at=0，段=None，步=None/None。最近盖：移动 {'kind': 'exact', 'piece': 0}，障碍 parent=1、parent内片=1、扁平片=5；限制特征 vertex-edge，移动支撑顶点=[6]，障碍支撑顶点=[0, 3]，归一重叠=-0.24777。
  - 最后**完成**尝试返回：`{"mode": "capped:1:32", "detail": "cap_origin_not_covered"}`。捕获失败可来自随后耗尽预算的当前尝试，二者不强行视为同一位置。

#### 诊断性判断

1. d03 在原首未证点 δ=1/4、d08 在 δ=13/128 得到新的双核验笼证书，二者同时复核 `TRAPPED_TRANSLATION`，直接表明至少这两处原下界未抬高含有提议器资源/搜索不足；不是引理不可用。原science_02外置JSON不回写，两项改进已合并§5展示表。
2. ρ=0 切片成功但同区间收缩比值较大，且细分后下降，只定位当前固定 Γ/见证的收缩余量损失；不能据此宣称全部屏障都失败。比值已经较小而实际连接/封口仍失败，则观测到的是本提议器该连接/封口构造未成功，未证明不存在其他连接。
3. 对未取得 ρ=0 屏障的采样角，不能计算那条尚未获得的 Γ 的容量，也不能强行在“方法过松”和“搜索不足”间二选一。d07 四内点给出切片成功数、具体局部失败与适用的比值，供 T2c 按D4先改进 Γ、连接与封口构造，而不是不可逃结论。
4. k01/k02 的所有已采样 t=0 均无严格贯入，最后实际阻断于封口目标原点检查；当前转动片分支只尝试封口弧，不搜索转动片覆盖整周的无封口闭链。这是本提议器明确的搜索边界，不是“不存在笼”的结论。
5. 本单没有实现按 u 精确墙函数；所有者已据这些有限、可复算事实作出下述D4裁定，暂不放开。

证据：`diagnostics/final_03/summary.json`、逐点 `proposal_trace.json`/`slice_diagnostics.json`、`diagnostic_readout.json`、`slice_origin_audit.json`。原路径来源、δ、完整累计角端点、各 Γ 及固定见证、ρ 成功/失败有理包络和源快照均落盘。

完整可点击入口：[终版14点](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/diagnostics/final_03/summary.json) · [诊断源快照](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/diagnostics/final_03/source_manifest.json) · [全部诊断逐件SHA](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/diagnostics/artifact_manifest.json)。

**所有者2026-10-26 D4裁定：T2c先改进提议器**（封口目标选取、整周闭链、自适应细分），暂不放开按转角精确的墙函数。依据是区间细分后V1所需收缩/可用余量大多小于1，当前失败集中于封口目标和连接构造，凸耳缺整周闭链搜索，且增加资源已提高d03/d08下界；这是下一单的方法选择，不是未证点“不可逃”的结论。

## 8. 静态准入与收尾验证

<a id="t2b-static-admission-review"></a>

先按闭子集友好写法消除诊断：异常构造去不必要反射；`where` 元数据先显式 `str`，避免混合容器引发虚假的 rounded 传播；规范数词改小型 ASCII 词法检查；fixture 用递归精确拷贝代替不透明 deepcopy；真值 factory 用显式分支。初扫与中间诊断保留，不冒称静态零诊断为数值安全证明。

<!-- T2B_STATIC_BEGIN -->
只对证明缺口追加 **98个唯一准入键**（生产35、测试辅助63），对应103条原始诊断、111个规则/源码出现站点；同一AST键的多处出现完整列入 `occurrences`，不重复盖章。rounded/浮点汇点准入 **0**。旧3659条及全部其他policy字段保留，三分析器SHA不变。

<!-- T2B_STATIC_ADMISSIONS_COUNTS_BEGIN -->
| 规则 | src | tests | 总数 |
|---|---:|---:|---:|
| `closed-callable-value` | 10 | 3 | 13 |
| `closed-dynamic-call` | 0 | 2 | 2 |
| `closed-import-call` | 0 | 6 | 6 |
| `closed-method-call` | 2 | 6 | 8 |
| `closed-runtime-reflection` | 0 | 2 | 2 |
| `closed-unknown-call` | 0 | 2 | 2 |
| `closed-unproved-call` | 23 | 42 | 65 |
| **总计** | 35 | 63 | 98 |
<!-- T2B_STATIC_ADMISSIONS_COUNTS_END -->

生产站点仅涉及规范JSON的固定token hooks、递归精确容器编码/解码、类型身份检查及失败后的JSON顺序诊断；后者不能把拒收变成接受。测试站点另含显式fixture复制、既有精确逃逸API复用和24变异的编译执行基础设施，不是生产数值准入。每条理由钉住函数context、AST及所有出现位置；自动门向真实生产作用域注入浮点/二进制操作后按语义拒收。

[逐站账本](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/static_admissions.json) · [候选与审查记录](file:///D:/eab-evidence/reports/codex/T2b_evidence/static_reviewed_01.json) · [可复跑审查工具](file:///D:/eab-wt/cx-e2/tools/t2b_static_review.py) · [自动门](file:///D:/eab-wt/cx-e2/tests/test_t2b_static_admissions.py)。候选01曾误计同文本Expr外壳，已保留为无效历史；候选02修正并经逐站审查才准入。

机械兼容仅三处：历史视图3659→3757及注释；T2a只审自己的137条切片；历史源码门先撤销T2b计数/注释再核原指纹，并继续对增删一条准入报红。纯度门仅53→54并注明 `se2_cage`，禁词、白名单、依赖图不放宽。

原policy含42297个CRLF；首轮错误地整份改为LF，本轮按所有者裁定恢复CRLF（43375个CRLF、无裸LF），JSON内容不改。`git diff 146cc76 -- tools/exact_construction_policy.json` 为1078行插入、0行删除，恰为98项追加，不再整份换行抖动。`BASE_POLICY_SHA=621df…` 是146cc76中真实存在的原CRLF策略blob，保留其历史含义，不替换成当前哈希；当前SHA为 `03aaf6b35227c38fd6a6a80ddc1d49214cbd3f87779ffb44092c9a1547daeb92`。[字节恢复审计](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/policy_sidecars/policy_restore.json)。98条证明缺口、浮点汇点0已由**所有者2026-10-26追认**，`policy_history_view.py` 注释与机械历史逆变换同步。三分析器不改，本轮新增准入0。

原生产交付的完整静态随当时全档执行，历史原样末行：`exact construction AST gate: 0 violation(s)`。此前静态预检虽0违例，但扫描期间提议器测试在改动，准确标为NON_FROZEN；不拿它替代最终完整静态。
<!-- T2B_STATIC_END -->

<!-- T2B_GATES_BEGIN -->
### 原生产交付的运行记录（历史，仅供溯源）

旧基线15529项、旧快档9694项、旧全档15800项均属于独立核验器合入前的原生产交付，不是当前续单收尾。旧报告全文保存在续工基线ZIP的 `reports/codex/T2b_report.md`，不丢弃原始证据；不把旧节点数量、旧受测字节或当时待办状态搬作当前结论。

- [旧基线摘要](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_baseline_20261025/summary.json) · [旧基线日志原字节](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_baseline_20261025/raw_runner_bytes.zip)
- [旧快档摘要](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_fast_20261025/summary.json) · [旧快档日志原字节](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_fast_20261025/raw_runner_bytes.zip)
- [旧全档摘要](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_full_20261025/summary.json) · [旧全档日志原字节](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_full_20261025/raw_runner_bytes.zip)
- [旧全档受测源码ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_full_20261025/tested_source.zip) · [续工基线与旧报告全文](file:///D:/eab-evidence/reports/codex/T2b_evidence/resume_5c0f80f_20261026/baseline_anchor/source.zip)

本次独立核验器及新增门已包含的新运行，只在下列§8.1按实测结果列出。
<!-- T2B_GATES_END -->

### 8.1 本轮新收尾（c900033验收返修）

旧 `t2b_dual_final_fast_20261026` 因只读policy钉子冲突中断，永久作废；原最小复现 `1 failed in 0.08s` 与[中断档案](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_dual_final_fast_20261026/INTERRUPTED_INVALID_RUN.json)保留。所有者已在c900033前修复只读测试，本代理没有修改独立侧文件。此处不再把已解除的历史阻塞当当前待办。

<!-- T2B_ACCEPTANCE_GATES_BEGIN -->
**本轮快档与全档均GREEN。** 快档10309项；全档16415项、固定四分片，均含已合入独立核验器测试。0 failed、0 skipped；收集/分派/插件收集/实际call节点多重集合相等；70个生产模块运行覆盖完整。两轮2673文件源清单相同，运行前后live和导出字节无变化。

| 新run | 分片 | 原样末行 |
|---|---:|---|
| `t2b_acceptance_fast_02_20261026` | 1 | `10309 passed in 1844.12s (0:30:44)` |
| `t2b_acceptance_full_02_20261026` | 1 | `4104 passed in 1936.59s (0:32:16)` |
| `t2b_acceptance_full_02_20261026` | 2 | `4104 passed in 2610.53s (0:43:30)` |
| `t2b_acceptance_full_02_20261026` | 3 | `4104 passed in 1746.74s (0:29:06)` |
| `t2b_acceptance_full_02_20261026` | 4 | `4103 passed in 2118.91s (0:35:18)` |

静态原样末行：

```text
exact construction AST gate: 0 violation(s)
```

快档含收集审计耗时 1861.186 s，全档 2807.664 s；快档超过5分钟成本目标，准确记录，不宣称达标。第一轮 `t2b_acceptance_fast_20261026` 在1800s预算到期时作废，最后进度10224/10309、0失败/跳过，无最终pytest末行；原文/源码已归档，见[作废记录](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_acceptance_fast_20261026/INVALID_RUN.json)。本轮 `_02` 从头重跑，不拼接；仅外部[预算适配器](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/run_extended_budget.py)把快档墙钟预算1800→3600s，测试、覆盖/多重集合/冻结审计、900s停滞守卫和全档10800s预算均不变，仓内运行器一字未改。独立侧文件89项与c900033开工字节相同；本轮新准入0，原98项仍为src35＋tests63、浮点汇点0。

[快档完整结果](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_acceptance_fast_02_20261026/summary.json) · [全档完整结果](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_acceptance_full_02_20261026/summary.json) · [双轮及ZIP成员审计](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/final_pair_audit.json)。两轮各有 `tested_source.zip`、逐文件 `source_manifest.json`、保存原始日志字节的 `raw_runner_bytes.zip` 与LF视图映射；不重算测试或拼接日志。收尾后只回填报告/元数据，1532份非report受测文件仍逐字相同；这是字节导出验证，不冒称新鲜Git树。
<!-- T2B_ACCEPTANCE_GATES_END -->

## 9. 工单订正清单

1. 未发现足以改变笼定理接受集合/真值结论的最小反例；理论合同不改。
2. `where/reason` 的具体字符串与对象级缺失键定位在引理中未编码，本实现另明示诊断约定；不改变条件编号。
3. 工单许可逐站证明缺口准入；T2a旧门把整个追加尾段及总数固定，本单仅做上述机械计数/切片兼容，不删门、不放宽规则、不修改分析器。所有者2026-10-26已追认98条证明缺口准入、浮点汇点0；本轮仅补追认注释与CRLF恢复，不新增准入。

4. 续单补充：`_cap` 在步数上限小于8时真实抛出未赋值局部变量异常；已按§3.1仅加两行资源守卫，前3红1绿、后67绿。既有≥8分支与诊断final_03的128步路径不变；不修改引理或迁就真值。

5. 历史policy钉子阻塞已由所有者解除；旧作废快档不恢复为绿。生产核验器无误但原测试集变异牙不足，本轮按97项核查补门；不通过修改生产代码或放宽独立侧来使结果一致。
6. 证据级文本入口与内存dict便利入口明确分离；7份原逃逸候选保留 `PROPOSAL_UNVERIFIED` 产生时状态，以旁置核验记录给出实际验证，不改候选字节。

## 10. 建议并入设计的新增清单

- `SE2CageCertificate`：`from_json/from_data/to_json/to_data`，精确值往返；数据类本身不等于接受。
- `verify_se2_cage(instance, certificate)`、`SE2CageVerification(valid, condition, reason, where, counts)`；成功 `ACCEPTED`，拒收 `V0/CHAIN/V1/.../V6`。
- `counts` 保存已检查片、收缩不等式、屏障段、连接四边形、起始片对及带符号绕数；不是覆盖率证明。
- 工具 `CageResources`、`propose_cage`、`scientific_instance`；状态 `CERTIFIED_CAGE/UNPROVED/PROPOSAL_UNVERIFIED`。
- 原科学来源JSON保留产生时 `production_only_pending_independent`；当前仓内汇总以 `production_and_independent_verified` 补记实测验收，不改原来源字节。

`docs/eab2_design.md` 未修改；上述为建议清单，不是已并入设计。

完整新增函数、内部辅助函数、类字段及方法签名见[源码级新增清单](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/api_inventory.json)；下划线函数明确是内部实现，不建议升级为公共API。JSON字段严格沿用引理§7；新增诊断字段 `source/generation_seconds/verification_seconds/mode/intervals/uses_caps/loop_vertices` 仅属不可信提议器运行记录，不构成笼条件。

### 10.1 续单诊断接口与字段

[续单AST接口清单](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/continuation_api_inventory.json)记录 `ProposalTrace`、`pair_margin`、`closest_cover`及其余诊断函数、类字段、字典键与状态字面量；每项由当前受测源码AST抽取。`source=诊断`、`proposal_status`、`last_failure_per_stage`、`closest_cover`、法向平方/精确重叠分子、ρ容量包络与比值均是诊断字段，不是新的笼条件或求解器公共状态。现有 `_cap` 低预算只使用原有 `SearchLimit/UNPROVED` 出口，不增加数学状态。原 `api_inventory.json` 明确保留为第一单交付清单；设计正本未改。

### 10.2 验收返修新增项

本轮不增加生产函数、数学状态或准入；新增内容仅为具名测试与外置核验记录。旁记schema `t2b-escape-verification-record-1` 的主要字段为 `delta/verdict/candidate_status_preserved/candidate_sha256/instance_sha256/provenance.source_sha256/production/independent_finite_oracle/segment_counts/ray_prefix_counts/all_pose_endpoints_equal/all_pair_semantics_equal/diagnostic_timing_seconds/scope_note/audit_file`。`VERIFIED_ESCAPE` 为已核验证据记录，原候选 `PROPOSAL_UNVERIFIED` 不改；`independent_finite_oracle.infinite_ray_verified=false` 明确独立范围。返修汇总 `t2b-acceptance-repair/1`、变异KILLED/SURVIVED和运行GREEN仅为验收记录，不是新的内核状态。设计正本仍未修改。

## 11. 遗留与最终状态

<!-- T2B_RESIDUAL_BEGIN -->
1. 原25份与新增2份笼文件双核验、双方语料/实例/逃逸专项与14点诊断已完成；最终科学表已合并两例提高下界，仍不能声称临界值等号。
2. 本轮97项语义变异82杀/15允许存活、新快/全档与静态均完成；旧阻塞已解除，旧中断轮仍作废，不拼接。
3. 所有者已给出四路验收结论，本轮针对变异牙返修；本代理仍只做字节导出复现，不冒称新鲜Git树，也不自签所有者对返修的最终验收。
4. 诊断为有限资源/固定Γ见证；缺失ρ=0屏障时比值未定义。T2c依D4先改善提议器，不从搜索失败推出可逃或不可逃。
5. 凸耳无独立生成器，验收时已按支撑距离与竖条剖分独立复核；本代理逃逸oracle的有限段/尾前缀边界与所有者独立路径验收分列，不混称同一验证。
6. 未作Git写，未改src、独立侧、引理、C++或三个分析器；policy仅按本轮明确裁定恢复CRLF。范围、净增与逐文件SHA见[本轮交付审计](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/delivery_audit.json)及[逐件SHA清单](file:///D:/eab-evidence/reports/codex/T2b_evidence/acceptance_repair_c900033_20261026/artifact_manifest.json)；累计仓内净增小于5MB。本地保存不等于远程备份。
<!-- T2B_RESIDUAL_END -->

T2B_DONE
