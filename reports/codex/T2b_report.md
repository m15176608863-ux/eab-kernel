# WO-T2b：SE(2) 笼证书与刚体临界公差双侧括号

**一句话结论：10例都已有经生产核验的“困住下界—逃逸上界”，其中7例上界收窄；独立核验器尚未合入，整单双核验验收仍未完成。**

开工日期：2026-10-25；收尾：2026-10-26（Asia/Singapore）。执行：Codex；所有者：Claude。本文按已完成运行回填；不把待办写成结果。

## 1. 开工合同、范围、回退与归属

| 项目 | 记录 |
|---|---|
| 目标 | P0 精确笼核验、有限提议器、真值/伪造/变异门、十例双侧括号；P1 可选 |
| 实查基线 | `codex-work`，HEAD `146cc76b6e25598f00564438dee7f3282ad52e34`，开工干净；Python 3.12.10 |
| 写域 | `D:/eab-wt/cx-e2` 与 `D:/eab-evidence/reports/codex/T2b_evidence/` |
| 非目标 | C++/eab2、既有数学函数语义、理论合同修改、多体运动、精确墙函数、临界值等号或新颖性表述 |
| 回退锚 | [2426 文件字节 ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/baseline_anchor/source.zip)与[成员 SHA256](file:///D:/eab-evidence/reports/codex/T2b_evidence/baseline_anchor/manifest.json)；不自动 reset，不覆盖所有者后续修改 |
| 成功标准 | P0 逐项证据、真值一致、24 内部变异报红、静态零违例、收尾快/全档真实执行；独立核验器合入后每份入表证书双核验且伪造拒收代码一致 |
| 新鲜树边界 | 本代理只使用字节快照/导出，不作 Git 写操作，不宣称所有者新鲜 worktree 验收 |

[机器工作合同](file:///D:/eab-evidence/reports/codex/T2b_evidence/work_contract.json)。`docs/t2b_cage_lemma.md` 第 5 版为只读理论合同；正确性论证引用其 §4，不另写替代理论。SE(2) 指定路径首入归本仓库 M5a；石根华原文归属沿用 T2a D1–D3、D6–D8。单块、邻居固定；块在自身坐标中按 δK 腐蚀；有理八边形 K 为标题模型，方形 K 仅为 T1b 对照。

## 2. 生产核验器与合同对照

[实现](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/se2_cage.py)只使用标准库与精确整数/Fraction。浮点提议、搜索失败、显示舍入均不进入接受条件。输入实例与证书分开传入，逐顶点、逐障碍、逐顺序核对。

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

## 4. 真值门

理论输入来自引理 §5 与 `tests/t2a_truth_geometry.py`；新增低/高房间精确环在[生产侧真值几何](file:///D:/eab-wt/cx-e2/tests/t2b_truth_geometry_prod.py)。未读取 WO-T2b-V 的任何文件。

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

[终版真值与计数](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/truth_02/summary.json)；每项实例/证书/逃逸路径见[对应目录](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/truth_02/)。所有笼证书状态仍为 `production_only_pending_independent`。
<!-- T2B_TRUTH_END -->

每个被接受的真值笼另核 T1b 平移困住；低房间只圆提议必须 `UNPROVED`，成功必须封口链。高房间与门洞等号/上侧需实际通过 `verify_se2_escape` 的逐段路径和无穷尾射线，不以图示代替。

## 5. 十例科学表（独立复核待办）

[扫描工具](file:///D:/eab-wt/cx-e2/tools/t2b_science.py)复用未改的 `t2_se2_grid.CASES/geometry`：`tia2d` 生成器 + 精确 `erosion`。所有 δ 保持同一有理中心 `(0,1)`。从零以 `1/32` 粗步上扫，在最后成功/首个未证之间二分到 `1/256` 网格（k=8≤20），分别运行只圆与完整提议；“未证”不是困住上界。上界从 T2a 已验 δ 重新精确核验，再尝试三次向下二分的逃逸提议。只接受实际核验通过的上界。

相对宽度明确定义为 `(δ_esc−δ_cage)/δ*_T`。所有括号外结论写“未证”；本单不写十例的 `δ*_SE2 = ...`。

<!-- T2B_SCIENCE_BEGIN -->
| ID | K；邻居腐蚀 | δ_disk | δ_cage | δ_esc | δ*_T | 宽度 | 相对宽度（精确） | N | 封口 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| d01 | 方形；0 | 23/128 | 23/128 | 3/10 | 1/3 | 77/640 | 231/640 | 2 | 否 |
| d02 | 方形；0 | 63/256 | 63/256 | 1851/5120 | 1/2 | 591/5120 | 591/2560 | 2 | 否 |
| d03 | 方形；0 | 63/256 | 63/256 | 21/50 | 3/7 | 1113/6400 | 2597/6400 | 2 | 否 |
| d04 | 方形；1 | 13/128 | 13/128 | 1/5 | 3/14 | 63/640 | 147/320 | 2 | 否 |
| d05 | 八边形；0 | 63/256 | 63/256 | 2043/5120 | 24/41 | 783/5120 | 10701/40960 | 2 | 否 |
| d06 | 八边形；0 | 93/256 | 93/256 | 5393/10240 | 24/41 | 1673/10240 | 68593/245760 | 2 | 否 |
| d07 | 八边形；0 | 13/64 | 13/64 | 849/2560 | 24/65 | 329/2560 | 4277/12288 | 2 | 否 |
| d08 | 八边形；1 | 25/256 | 25/256 | 11377/51200 | 12/49 | 6377/51200 | 312473/614400 | 2 | 否 |
| k01 | 方形；0 | 75/256 | 75/256 | 3923/12800 | 1/3 | 173/12800 | 519/12800 | 2 | 否 |
| k02 | 八边形；0 | 93/256 | 93/256 | 977/2560 | 12/29 | 47/2560 | 1363/30720 | 2 | 否 |

标题模型八边形 K 为 d05–d08、k02；其余为方形对照。全部10例本次 `δ_cage=δ_disk`，仅表示此资源/网格下区间链没有提高下界，不能推断圆判据完备。7例逃逸上界收窄（d02、d05–d08、k01、k02），其余保留重核通过的 T2a 上界。

终版扫描总耗时 **132.8529 s**，源文件运行前后字节不变。每例下界实例为 `science_02/<ID>/instance.json`、证书为 `certificate.json`；圆证书另列 `disk_instance.json/disk_certificate.json`，逃逸端点/路径另列 `escape_instance.json/escape_candidate.json`。每个成功的下界探针都另核 `TRAPPED_TRANSLATION`；10个最终逃逸端点的笼提议均为 `UNPROVED`。

[完整科学表/探针轨迹/参数](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02/summary.json) · [10例证书](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02/) · [20份规范JSON复核](file:///D:/eab-evidence/reports/codex/T2b_evidence/certificates/science_02_serialized_recheck.json)。

固定小子集实际回放两份证书（八边形 d07 和低房间封口），比较完整状态、计数及有理端点，不钉当前源码：[输入](file:///D:/eab-wt/cx-e2/tests/data/t2b_cage_replay.json)、[具名门](file:///D:/eab-wt/cx-e2/tests/test_t2b_replay.py)。来源提交/工具与源ZIP保留在外置目录，不将历史哈希改成当前哈希。
<!-- T2B_SCIENCE_END -->

## 6. 变异与伪造集

[24 项具名变异门](file:///D:/eab-wt/cx-e2/tests/test_t2b_mutations.py)在运行中编译生产源码的内部变体：原版同一语义 guard 先绿，再要求指定语义 AssertionError 红；不接受源码哈希或偶然异常为杀变异证据。[39 份精确伪造](file:///D:/eab-wt/cx-e2/tests/data/t2b_forgeries/)逐项断言拒收编号；[对应表](file:///D:/eab-evidence/reports/codex/T2b_evidence/tests_summary.json)覆盖引理各版修订类别。

零轴门直接进入生产 SAT 辅助函数，因为合法公共入口的严格凸守卫已把重复顶点先拒；这是内部防线门，不冒称删除它就能越过仍在的前置守卫。绕数 +2 和 −2 都须接受，不能用奇偶性代替带符号整数。起点贯入门确认已通过 V4/V5 并在 V6 拒收，排除前置数据错误遮挡。

## 7. P1 诊断与性能

各探测记录含生成/核验耗时、区间数、是否封口、折线顶点数与有限搜索失败原因。时间仅为本机诊断，不作性能保证；基线测试并行负载会影响耗时。完整失效盖标签与逐角度瓶颈诊断列入可选 P1 未做项，不计 P0 PARTIAL。

### 7.1 下界证书性能（诊断）

| ID | 生成含核验/s | 其中核验/s | 区间数 | 区间Γ总顶点数 | 全部折线顶点数 | 首个未证δ |
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

区间Γ顶点数含闭合重复端点；全部折线顶点数另加连接/封口链中每条折线（按序列计数，不去重）。完整10例“失败角度—严格见证段—盖标签”诊断 **未做（P1可选）**。仅保留 d07 的 δ=53/256 单次20秒探索：连接区间3、step22/128、segment77找不到四点见证；该失败不是不可逃结论，且只有运行后source SHA、没有运行时源快照，不升级为终版科学依据。[探索记录](file:///D:/eab-evidence/reports/codex/T2b_evidence/diagnostics/d07_53_256_exploratory_01.json)。

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

原policy含42297个CRLF，本单修改后按工单统一为LF；旧3659条与其他字段是JSON值/规范摘要不变，不是原始文件字节不变。[旧原字节](file:///D:/eab-evidence/reports/codex/T2b_evidence/policy_before_t2b.json)及开工ZIP完整保留。三分析器仍逐字节不变。

最终完整静态随收尾全档执行，原样末行：`exact construction AST gate: 0 violation(s)`。此前静态预检虽0违例，但扫描期间提议器测试在改动，准确标为NON_FROZEN；不拿它替代最终完整静态。
<!-- T2B_STATIC_END -->

<!-- T2B_GATES_BEGIN -->
开工全档 `t2b_baseline_20261025` 已完成，15529项、0 failed/skip；69模块实际执行覆盖完整，2426文件与开工ZIP相同。四分片原样末行：
```text
3883 passed in 1492.69s (0:24:52)
3882 passed in 1968.88s (0:32:48)
3882 passed in 1568.37s (0:26:08)
3882 passed in 2059.05s (0:34:19)
exact construction AST gate: 0 violation(s)
```

[完整基线](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_baseline_20261025/summary.json)。以下另列新代码收尾运行，不混用基线。

### 收尾快档（原样末行）
[t2b_final_fast_20261025](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_fast_20261025/summary.json)
```text
9694 passed in 1529.96s (0:25:29)
```

### 收尾全档固定四分片（原样末行）
[t2b_final_full_20261025](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_full_20261025/summary.json)
```text
3950 passed in 1480.50s (0:24:40)
3950 passed in 2122.24s (0:35:22)
3950 passed in 1652.57s (0:27:32)
3950 passed in 1828.83s (0:30:28)
exact construction AST gate: 0 violation(s)
```

快档实际执行 **9694** 项、全档 **15800** 项；两次均0 failed、0 skip，收集/分派/实际call节点多重集合相同，逐模块运行监测覆盖完整。两次source_manifest完全相同，运行期间导出树与现场树均未改。快档耗时 1542.976 s，全档耗时 2288.878 s；全仓快档未达到单进程约5分钟的长期成本目标，本单未改既有测试或算法以追求时限。

[受测字节ZIP](file:///D:/eab-evidence/reports/codex/T2b_evidence/t2b_final_full_20261025/tested_source.zip)保留临时导出的实际运行版本。日志LF视图转换前的原字节另存各run `raw_runner_bytes.zip`，对应 `lf_export.json`逐文件给出双SHA；JSON值、测试结论和末行未改。

仅在两次运行完成后回填报告与交付元数据；`src/`、`tests/`、`tools/`及静态准入账本仍为受测字节。这是H1字节导出验证，不是所有者安排的新鲜Git树。

[双轮节点/来源机械核对](file:///D:/eab-evidence/reports/codex/T2b_evidence/final_pair_audit.json)确认70模块实际执行覆盖（63函数模块、7声明模块），620份代码/测试/工具/准入账本仍为受测字节。[逐项P0交接核查](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/requirements.json)机器记录271个T2b节点、24变异、39伪造、198个成功下界探针及明确待办；它不是独立核验器或里程碑对抗核查。

复跑（将run名换成全新名称；包装器固定外置TEMP/TMP、禁cache、显式basetemp、禁pyc）：
```powershell
python -X utf8 tools/t2b_run_gates.py --name <new_fast_name>
python -X utf8 tools/t2b_run_gates.py --name <new_full_name> --runslow
python -X utf8 tools/t2b_delivery_audit.py
```
<!-- T2B_GATES_END -->

## 9. 工单订正清单

1. 未发现足以改变笼定理接受集合/真值结论的最小反例；理论合同不改。
2. `where/reason` 的具体字符串与对象级缺失键定位在引理中未编码，本实现另明示诊断约定；不改变条件编号。
3. 工单许可逐站证明缺口准入；T2a旧门把整个追加尾段及总数固定，本单仅做上述机械计数/切片兼容，不删门、不放宽规则、不修改分析器。已询问所有者但未收到额外回复；此处按工单授权边界实施，不冒称另获来函批准。

## 10. 建议并入设计的新增清单

- `SE2CageCertificate`：`from_json/from_data/to_json/to_data`，精确值往返；数据类本身不等于接受。
- `verify_se2_cage(instance, certificate)`、`SE2CageVerification(valid, condition, reason, where, counts)`；成功 `ACCEPTED`，拒收 `V0/CHAIN/V1/.../V6`。
- `counts` 保存已检查片、收缩不等式、屏障段、连接四边形、起始片对及带符号绕数；不是覆盖率证明。
- 工具 `CageResources`、`propose_cage`、`scientific_instance`；状态 `CERTIFIED_CAGE/UNPROVED/PROPOSAL_UNVERIFIED`。
- 科学汇总显式 `production_only_pending_independent`，不与双路验收混用。

`docs/eab2_design.md` 未修改；上述为建议清单，不是已并入设计。

完整新增函数、内部辅助函数、类字段及方法签名见[源码级新增清单](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/api_inventory.json)；下划线函数明确是内部实现，不建议升级为公共API。JSON字段严格沿用引理§7；新增诊断字段 `source/generation_seconds/verification_seconds/mode/intervals/uses_caps/loop_vertices` 仅属不可信提议器运行记录，不构成笼条件。

## 11. 遗留与最终状态

<!-- T2B_RESIDUAL_BEGIN -->
1. **P0待外部交接**：尚未收到所有者合入 WO-T2b-V 的通知，未读取或修改该独立实现。每份入表笼证书还须双核验，双方伪造集的判定与拒收代码必须一致；不一致即停下报告。现有科学表全部为 `production_only_pending_independent`，不是最终双核验入表验收。
2. 所有者新鲜Git树复现与Claude安排的一路独立对抗核查尚待办理；内部多代理检查不替代此项。
3. **P1可选未做**：十例完整盖标签瓶颈诊断未做；单次d07探索仅作诊断，不计入本单PARTIAL原因。已记录逐例生成/核验性能。
4. 下界搜索仅k=8有限网格与有限资源，区间链未改善10例圆法下界；不能声称最优、完备或临界值等号。计时是协作式，不保证抢断单次昂贵调用。
5. 本地证据不是远程备份；未commit/push，也未修改任何既有数学API、只读引理或C++。完整改动链接见[交付清单](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/artifacts.md)，SHA与边界见[交付审计](file:///D:/eab-wt/cx-e2/reports/codex/T2b_evidence/delivery_audit.json)。
<!-- T2B_RESIDUAL_END -->

T2B_PARTIAL：待所有者合入独立核验器，完成全部入表证书双核验及双方伪造集拒收代码对拍。
