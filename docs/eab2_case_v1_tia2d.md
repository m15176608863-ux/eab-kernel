# eab2.case.v1 — TIA2D 已批准字段（tia2d-2）

设计钉版：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`，第二版 r3b。批准号 **CLAUDE-APPROVED-TIA2D-2**，日期 **2026-10-19**，schema_revision=`tia2d-2`。批准的是数据 schema，不是 C ABI 冻结、实现完成或批次验收声明。[批准前原文归档](file:///D:/eab-evidence/reports/codex/T1a_evidence/resume3/schema_before_approval.md)保留历史字节。

两处获批的设计接口偏离（设计原文件不修改）：

1. `Assembly2` 边界描述新增 **`dof_anchor`**；mask 约束该点的速度，与代数力矩参考点无关。TIA-G5 主锚点取端板面中点；释放转动主反例为 4/3；原点锚点的 1/3 仅作不同边界诊断。
2. 极大共线正长度段内部的平坦顶点不生成约束（其约束是两端点约束的凸组合）。接触点 **`boundaries`** 完整保存几何 F_p 边界；**`retained`** 独立记录该点是否实际贡献解析法向约束。`TRUE_VV` 与已证冗余的 `REDUNDANT_PROVED` 也为 retained=false，不能仅由此布尔值推断 F_p 类型。

## 1. 顶层信封

```json
{
  "schema": "eab2.case.v1",
  "schema_revision": "tia2d-2",
  "case_id": "TIA-G5-N3-example",
  "input_version": "tia2d-input-1",
  "design_sha256": "6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac",
  "profile": "profile1",
  "assembly": {},
  "input_audit": {},
  "family_parameters": {},
  "alias_of": null,
  "role": "primary",
  "queries": [],
  "provenance": {},
  "python_wallclock": {}
}
```

这是结构示意，空对象不构成有效算例；不存在的结果不填 0，不将 UNPROVED 编码成 false。输入与期望结果分离，查询以 `assembly_ref={id,version}` 与 `contact_set_ref={id,version}` 显式绑定同一 Assembly/ContactSet；ID 为精确输入/接触语义记录哈希，仅作绑定与追踪，不是源码改变就失败的回归条件。lock 另明确 moving_body/fixed_neighbors，因为它将这些邻体视为固定，不复用多体边界的隐含默认。

## 2. 数值、来源与状态

- binary64 输入：`bits` 为小写恰 16 位十六进制串，最高位在前；`-0` 必须保留 `8000000000000000`。拒绝 NaN/Inf 位型。JSON 不以浮点十进制数充当真值。
- 正式 C++ 子集的所有原始数值输入（含参考点、约束锚点、原始荷载/作用点、μ 和几何参数）都须 binary64 可表示，并同时保存 bits 与其精确有理解释；只写有理点不豁免此要求。派生力矩、LP 系数、导数种子和证书可为非 binary64 有理数。纯有理输入只进入另列的 `python_only` 诊断集，不进入本正式 schema 或 C ABI。
- 精确有理数：约分 `n/d` 串，十进制整数，d>0；唯一零编码 `0/1`。精确坐标、力矩、LP 系数、证书与种子使用此格式。
- 代数数：`polynomial`（有理系数，低次在前）、`isolating_interval`（两个有理端点）、`root_id`（证书内身份）；不得拿显示近似量判断同根。
- 阈值 `mu_lo_bits/mu_hi_bits/mu_max_bits` 只能存可表示的有限 binary64；非 binary64 精确阈值放 `exact_threshold`，不得塞入 double 字段。
- 身份：body_id、原 vertex_id、原有向边的端点 ID、原环至 CCW 映射显式保存；容器次序不是身份。每个接触点保留全部 VE/EV 来源，包括原段端点关联及反向体对来源。
- 每个查询显式保存 `source`（产生路径/工具与证据来源）和 `observable`（所求数学量及单位）；它们不得仅藏在自由文本 provenance 内，值由具体查询约定。
- 每个查询有 `call_status`、`mathematical_status`、`display_status` 三个独立字段。OVERLAP/INFEASIBLE/UNBOUNDED/UNPROVED 可以是调用成功的数学结论。

已冻结词汇原样保留：`profile1`、`ideal_exact_2d`、`FIXED_BODY`、`FORCE_CONTROLLED_PLATE`、`completeness_unknown`、`MECHANICAL_UNRESOLVED`，Lock 四状态/两细化，以及 `smooth/one_sided/tie/singular/unsupported/unresolved`；quality 按设计为 `approximate/bounded/exact_jet`，几何精确不自动意味着导数精确。

本版已批准的补充串：成功调用 `OK`；精确结果显示 `EXACT`、无适用显示值 `NOT_APPLICABLE`；已认证阈值括号 `CERTIFIED`；完备输入 `complete`；已解析接触 `RESOLVED`；一阶锥 `ZERO_CONE/NONZERO_CONE`；F_p 类型 `CONVEX/TRUE_VV/REDUNDANT_PROVED`。错误类沿用设计 §5.4；不增 discontinuous。

## 3. Assembly2 / ContactSet2

### assembly

| 字段 | 编码与条件 |
|---|---|
| bodies[] | body_id、vertices_xy_bits、原 vertex_ids、ccw_vertex_ids、几何版本 |
| reference_point | 每体与参数无关的常量有理点；所有输入载荷旋量明确 about 此点 |
| boundary_type | 普通可动体显式 null；边界为已冻结枚举；省略不等于固定 |
| dof_mask | 每体显式三个 0/1，顺序 x,y,rotation；固定体须 [0,0,0] |
| dof_anchor | 每体显式有理点；与代数参考点独立，同参考点也必须写出；部分掩码的非固定体必须显式提供。随几何参数改变时必须提供其种子 |
| dead/live | 三个精确有理分量；`load_source` 明确是关于参考点的直接旋量（附 dead_bits/live_bits），或作用点/力/纯力偶源；不混淆原输入与派生量 |
| adjacency | 显式候选体对与排除证明；工作实现首版直接枚举全部体对，不默认遗漏者已排除 |
| completeness | 裸输入 completeness_unknown；只有候选全覆盖且几何逐对核验后才可标 complete |
| mu_bits | 本次公共摩擦参数输入 |

### contact_set

`assembly_id/version`、`completeness`、逐对 `OUTSIDE/CONTACT/OVERLAP`、`raw_sources[]`、`points[]`、`constraints[]`、`unresolved[]`、`redundancy_certificates[]`。

每点记录精确 p、a/b、F_p 类型、局部入射边、原始来源、保留半平面。每条约束记录 a/b、p、未归一化 tangent e、N=rot90(e)、label、全部来源。正长度最大共线段记录两个端点和方向，不同坡度不得合并。

对外 a/b、dofs 和逐对状态用稳定 body_id；lock 原始来源转换回原 vertex_id/有向 edge 两端 ID，局部胞地址另带 neighbor_body_id，不能用规范环位置冒充原 ID。

真 VV 冗余证书必须保存实际 twist DOF 顺序、法向矩阵、禁止开锥齐次归一化 LP 与精确不可达证书；不得只写 `redundant=true`。未解析则数学状态 MECHANICAL_UNRESOLVED；不枚举模态。

## 4. 六查询族与精确证书

| query.kind | 必备输入 / 输出 |
|---|---|
| assembly | Assembly2 → ContactSet2；同上 |
| lock | moving_body、显式邻体；LockCertificate.status/refinement；逐邻体初态；过 0 胞与活动边/切锥；S¹ 射线与开弧三分类、阻挡特征；有理半径 r 及逐边严格平方距离界；分离/缝滑有理射线；拒签原因 |
| first_order | ContactSet2 ID；G、实际 DOF 顺序、精确 rank、归一化 LP；cone_is_zero（未解析为 null）；非零锥全生成元与线性空间两向；零锥每个 ±e_k 的非负 Gᵀ组合证书 |
| limit | LimitProblem2：profile、原始 exact A/b/c、max 约定、行列标签/作用反作用、reference_points/dof_anchors、载荷；LimitResult2：状态、精确值/x/y；INFEASIBLE 有 Farkas；UNBOUNDED 必有 x0≥0,Ax0=b 和 r≥0,Ar=0,r_alpha=1；自应力仅可选附件 |
| critical | param=mu；域和双端 binary64 bits；上下端实际状态与机构/Farkas、x0+r，及各自精确 LP；另有 threshold_certificate/threshold_proof 时同时存临界点 LP（非 binary64 μ 只用有理）；attained=true/false/null；exact_threshold 与开/闭证书、临界基多项式；bounded_on_domain 时 mu_hi=null；input_resolution_limit 保留已认证双端括号 |
| sensitivity | SensitivityResult2：模型、参数/方向/精确种子 dA/db/dc、selected_piece/tied_labels/near_labels/piece_jacobians、differentiability/quality、directional_derivative、reason、validity_conditions；稳定基或两侧回收锥证据，或 ±d Mills LP；有限承载力以 limit_query_ref 绑定原问题，阈值导数以 threshold_query_ref / threshold_certificate_ref 绑定原阈值及临界端 LP，另存 threshold_mu_seed、临界端基/全部越零分量/有效方向 |

Lock OVERLAP：status/refinement=null，数学状态 OVERLAP，成功调用且拒签。refinement 仅在 NOT_SEPARABLE_TRANSLATION 给出。

敏感性查询的 `directional_values={D_plus,D_minus}` 保存正向、反向方向导数；原结果对象保持 `right_derivative=D_plus`、`left_derivative=−D_minus`，比较 D_plus=−D_minus。无效方向及无认证导数用 null，不能把不存在的导数填 0。`validity_conditions` 必含设计原文“L1接触骨架不变”（无空格）。μ=0 的 G5 输出 singular/possibly_discontinuous、回收射线、导数 null；闭式右导 2P 只能放报告的非认证闭式注记，不能写入认证导数字段。

敏感性补充查询字段（本版已批准，不改变公共 `SensitivityResult2`）：

| 字段 | 编码与独立验算所需语义 |
|---|---|
| seed | 生产 `LimitSeed2` 的 parameter、dA、db、dc，均为从 geometry_seed 传播得到的派生期望字段，不代替 C3 几何输入；数值为精确 n/d |
| direction_domain | positive / negative 两个显式布尔值，表示调用者声明的有效方向；不是由导数是否为零推断 |
| declared_validity_conditions | 调用者提供的有效域条件；结果的 validity_conditions 另外保留模型强制条件及临界基条件 |
| limit_query_ref | 有限承载力导数引用同例唯一 limit 查询；其 problem 含原始 A/b/c，其 result 含 V*、原/对偶最优点；结合 seed 可重建两次 Mills LP，forward_certificate / reverse_certificate 分别给出该 LP 的精确 x/y |
| threshold_query_ref | 阈值导数引用同例唯一 critical 查询；原阈值证书及上下侧延拓数据不得仅以导数摘要替代 |
| threshold_certificate_ref | `{query:"critical",field:"result.threshold_certificate"}`；该端点内嵌精确 problem，seed 必须与该问题绑定，不能误用初始 μ 处的矩阵列次序或参数值 |
| threshold_mu_seed | 同临界点问题的精确 μ 种子；连同 seed、threshold_proof 的适用端基及 implicit_components，可独立重建 −φ_p/φ_μ；开阈只用机构基，不用发散原侧力 |
| implicit_components | 全部 `(label,slope,phi_mu,phi_p,index)`，不任意丢掉并列越零分量；不同斜率保留 tie，无单一认证方向导数 |

工具的 `include_sensitivity=True` 保留 μ 便捷查询；额外 P/h 或阈值参数查询由调用者通过工具私有请求传入生产精确种子和它对应的原问题，codec 不含几何族闭式或硬编码种子。原问题不匹配、缺阈值查询/临界端证书时拒绝构造该请求。具名门在 `tests/test_tia2d_cases.py` 中从解码 JSON 重建 P/h 两种模式及切换点的 Mills LP，并重建 G1 开阈 dt、细长闭阈 dt/dh 的隐式导数；这些仍是内存门，不是批准后的批量数据集。

## 5. 墙钟与来源

每个查询记录 `seconds`（非负有限 JSON 数）、`clock="perf_counter"`、`repeat_index`、`cache_state="cold"/"warm"`、`scope`（明确是否含装配）。每批只有一份 `source_manifest.json`：

- `schema="eab2.source-manifest.v1"`、`schema_revision="tia2d-2"`、`schema_approval="CLAUDE-APPROVED-TIA2D-2"`、`approval_date="2026-10-19"`；
- `git_commit` 仅作来源锚点；没有本树 Git checkout 时为 null，`git_commit_reason="no_git_checkout"`；不继承父目录 checkout。存在 checkout 时 `git_commit_reason="working_tree_source_manifest_authoritative"`，提交号不宣称等于未提交工作树字节。来源提交待 Claude 重建后登记。`source_manifest_basis="actual_root_src_tests_tools_bytes_v1"`，`source_files=[{path,sha256},...]` 为实际 ROOT 下 src/tests/tools 的完整文件字节清单（排除 __pycache__），`source_files_sha256` 为排序清单摘要；不是 Git dirty 列表，被忽略的字节副本也记录自己的源码；
- `tool_version`、`command`、Python/OS 版本、`design_sha256`；`inputs=[{case_id,input_sha256},...]` 绑定本批每个完整 Assembly 输入；
- 每例 `provenance` **只有** `source_manifest_sha256`，为该来源文件实际 UTF-8 字节的 SHA256，不在例内重复源码清单。构造与批生成/写出前后核完整源码；变化则作废，不生成成功 manifest。写出阶段失败目录留下 INVALIDATED.json，不允许拼接恢复。

主性能样本采用新进程冷启动后**不计解释器启动**的单查询墙钟；另记构造与证书成本，不以手装 LP 探针替代完整链计时。C++目标只能引用实际导出查询的计时。墙钟不是数学正确性证据。

来源清单摘要的精确定义为 `sha256(json.dumps(source_files,sort_keys=True).encode("utf-8"))`；输入摘要同样对完整 assembly 用默认 JSON 分隔符、`sort_keys=True,allow_nan=False` 编码。文件摘要始终针对实际文件字节，不混用这两个语义摘要。

每例内嵌 exact A/b/c 与所需证书；每个 JSON 文件不得超过 1 MB。正式文件采用无缩进的 compact JSON（`ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False`，末尾一个换行），只压缩空白、不删证书。`export_cases` 按完整查询顺序分片，不截断点/射线/多项式/种子。每片重列同一 Assembly 与信封，`queries` 只含该片查询，`fragment={index,count,query_indices}` 明确零基片号与原查询索引。

`manifest.json` 布局：

```text
schema: eab2.case-batch.v1
schema_revision: tia2d-2
schema_approval: CLAUDE-APPROVED-TIA2D-2
approval_date: 2026-10-19
source_manifest: {path, bytes, sha256}
cases: [{case_id, input_sha256, query_count,
         parts: [{path, bytes, sha256, query_indices}, ...]}, ...]
```

parts 有序，query_indices 不重不漏覆盖 `[0,query_count)`；跨片 limit_query_ref / threshold_query_ref 引用逻辑整例的查询，不要求在同一文件。读取器先核文件 SHA/长度/来源引用，再拼回整例后核算。单个查询或来源清单自身超过 1 MB 时明确拒绝，不能静默丢证书；若出现该情况，须另订完整证书子分片合同。

## 6. 批准记录与导出条件

**当前状态：APPROVED — CLAUDE-APPROVED-TIA2D-2 / 2026-10-19。** schema_revision=`tia2d-2`。函数映射仍为 translation_lock_certificate→query_lock、first_order_free_twists→first_order_mobility；evaluate_sensitivity2 不另造别名。

`export_cases` 仍要求显式传入批准号，默认只允许新建工作树内输出目录；源清单不一致、源变化、超限不可分片时拒绝/作废。单体 first_order 使用独立完整 Assembly 算例，显式固定其余体；不引入额外边界 override 公共字段。正式批注册、生成及独立读回由各自工具承担，schema 批准不等于这些步骤已经完成。

本版 critical 固定调用 `max_steps=64`，工具拒绝不可由本 schema 重建的自定义步数，不额外引入预算字段。

本轮工单订正 C03：TIA-G1 t=0 的零阈值为开阈；若 μ_max>0，exact_threshold=0/1、attained=false；μ_max=0 则 bounded_on_domain。该订正来自 Claude 裁定，不改变设计合同。

## 7. tia2d-2 修订合同（Claude 验收裁定，2026-10-19）

本节对应综合验收 §9 第 12–17 条及 D5/D17 裁定。批准引用 **CLAUDE-APPROVED-TIA2D-2 / 2026-10-19**；本节与前版不一致处以本节为准，不新增其他公共字段。

### 7.1 几何种子、族参数与派生 LP 种子

每个查询有 `geometry_seed`。无求导的查询使用空参数轴（`parameters=[]` 及所有导数数组 `[]`），不是缺失；导数查询必须有其完整几何输入。工具私有的手装 LP 诊断可以缺少几何种子，但不得作为正式导出 C3 查询。公共结构为：

```text
geometry_seed: {
  parameters: [parameter_name, ...],
  vertex_ids: [[body_id, original_vertex_id], ...],
  vertices: [parameter][vertex][2],
  body_ids: [body_id, ...],
  dead: [parameter][body][3],
  live: [parameter][body][3],
  dof_anchor: [parameter][body][2],
  mu: [parameter]
}
```

`vertex_ids` 按 `(body_id, original_vertex_id)` 排序，`body_ids` 按稳定 body_id 排序；每个坐标/荷载/锚点/μ 种子是约分 n/d。零种子显式填 `0/1`，固定体同样参与共享界面的几何参数。参考点始终冻结，`d(reference_point)=0`，不能用锚点种子替换代数参考点。投影转动平衡行须计入 `−d(anchor−reference)×force`；接触力矩微分须计入 `dp×g+(p−o)×dg`，活载列种子属于 dA 而不是 db。

顶层 `family_parameters` 给实际 t/h/A/wavelength/P/N/widths/μ 等族参数的精确值（数值用 n/d，orientation/family 用字符串；正式族参数均检查可表示为 binary64）。`wavelength` 在当前同相形貌族中就是一周期占满的块高，不宣称有独立波长设计轴。该元数据不参与 Assembly 输入哈希；不同种子角色即使 Assembly 相同仍须单独保留查询。

敏感性 `seed={parameter,dA,db,dc}` 是派生期望量，必须从 `geometry_seed`、原顶点 ID、未归一化接触边与冻结荷载参考点传播复算；不得以 LP 种子替代 C3 几何输入。共享点的两侧顶点种子必须相同。具名门：`test_geometry_vertex_load_anchor_jets_rebuild_every_non_mu_seed`、`test_geometry_jet_propagation_has_teeth_for_shared_vertices_loads_and_anchors`；正式 factory 对每个非 μ 查询再次精确比对传播结果。

### 7.2 审计与空值

`input_audit` 位于顶层，**不属于 assembly、不参与 input_sha256**：

- `lossless_binary64`：逐坐标 RN 后与精确原输入比较；
- `exact_pair_states`：逐对用 `polygons_overlap_exact` 重算 OUTSIDE/CONTACT/OVERLAP；
- `exact_parallel_edge_pairs`：实际边向量精确叉积为零的边对；
- `concave_vertices_before/after`：每体 `{body_id,ccw_indices}`，逐顶点计算入射边叉积负号；
- `no_new_concave_vertices`：比较上述两次结果，不硬编码 true；
- `expected_contact_pairs`：预期 CONTACT 骨架，正式链族显式给全部相邻体对；
- `contact_skeleton_matches`：预期与 RN 后 CONTACT 对集合相同，否则拒绝导出。

一阶未解析时实际 `dofs` 仍完整；未计算的 `matrix/rays/lineality/generators/zero_certificates` 为 null，不能用空列表伪装零锥。无认证导数、无承载数值、无一阶锥结论、无阈值括号时 `display_status=NOT_APPLICABLE`；状态的名称仍放 mathematical_status。这里阈值括号须同时有 lo/hi；`bounded_on_domain`、`infeasible_on_domain` 保留其端点证书，但没有阈值显示数值。OVERLAP 拒签和非法输入的 lock 同样不显示一个不存在的四状态结论。具名门：`test_input_audit_evaluates_concavity_and_rejects_false_expected_contacts`、`test_null_observables_never_claim_exact_display`、`test_no_finite_threshold_bracket_has_no_threshold_display_number`。

上述 null 规则明确用于 mobility 的未计算矩阵/生成元/零锥证书。ContactSet2 的 OVERLAP 拒收仍沿用既有空 `constraints/points` 记录，表示拒收 payload，不是已证无接触；读取方必须先检查调用/数学状态，不得由空接触列表推断 NOT_CONTACT。

### 7.3 比对合同、别名及显示注记

顶层 `alias_of` 为同批先出现的相同 assembly 哈希算例 ID，或 null；`role="alias"/"primary"`。这是重复输入角色标记，不允许删掉不同种子、不同查询的角色。每例 `input_audit` 与族元数据均不改变 Assembly 哈希。

每查询 `comparison_contract={default:"exact",rules:{path_pattern:category,...}}`，路径相对于该 query；`.` 分隔，`**` 匹配任意层后代；更具体规则优先。未被规则覆盖的叶字段按 exact。类别固定为 `exact / set / verify_certificate / informational`：

| 类别 | C++ 比对要求 |
|---|---|
| exact | 状态、精确最优值/阈值/导数、输入、几何边向量和原始 A/b/c 等严格相等 |
| set | 来源、标签、点/约束/段集合、有效条件等不依赖枚举次序，身份按 body/vertex/edge ID 与精确几何核对 |
| verify_certificate | x/y/基、可行点/射线、Farkas、零锥组合、Mills 与临界基证明等不唯一；必须核其原始等式/不等式与目标，不要求与 Python 枢轴选择逐字节一致 |
| informational | Python 墙钟、局部 cell_index 地址和显示注记不决定数学一致性 |

原始 A/b/c 与法向 G/dofs 须先按稳定体 ID、DOF 名及接触列/行标签对齐，再执行 exact 比较，不要求 C++ 复刻 Python 集合枚举次序。lock 的弧分区/采样/阻挡引用不唯一，`result.arcs` 归 verify_certificate；各层 sources 归 set；critical 的 `result.queries` 计数归 informational。

`result.selected_piece/piece_jacobians` 的见证表示归 verify_certificate；`tied_labels/near_labels` 归 set。正式 G5 的 sliding/hinging 来自闭式适配器，**不再注入裁判 tied_labels**，仅放 `query.display_note={source:"closed_form_adapter_not_certified",labels:[...]}`，该字段始终 informational。

`validity_conditions` 使用枚举码而非中英文同义自由文本。本批使用设计原文 `L1接触骨架不变`，以及 `axial_only_plate / frozen_reference_points / shared_interface_parameter / nonnegative_t / positive_h / fixed_polygon_table / positive_amplitude / positive_wavelength`。临界基隐式导数另使用固定码 `临界证书基非奇异 / 所列越零分量及方向保持有效`；有运动学冗余已证真 VV 时，limit/critical/sensitivity 必含 `true_vv_excluded_from_statics`。此规则表示 profile1 在 L3 不给该 VV 放接触力，不等价于把其摩擦半平面保留下来。

### 7.4 阈值查询与终止原因

每 critical 查询显式 `param`；只有 `mu` 执行单调二分，`param="h"` 返回 UNSUPPORTED。不新增预算字段，固定 max_steps=64。

`midpoint_rule="exact_mean_else_floor_to_binary64_then_strict_interior_v1"`：精确有理中点若 binary64 可表示就取它；否则令局部网格间距 `u=2^max(floor(log2(mid))−52,−1074)`（指数用整数位数和精确比较计算），取 `floor(mid/u)*u`；若不大于 lo 则加 u。只有严格内点才查询；不存在内点则终止 `input_resolution_limit`。不是简单从 lo 向 hi 走一 ULP。

`result.bisection_termination` 独立记录二分终止；`result.threshold_proof_reason` 独立记录阈值证明结果，不能互相覆盖；旧 reason 保留二分终止原因的兼容摘要，不被 exact_basis_continuation 覆盖。`threshold_proof.lower_signs/upper_signs=null` 表示没有延续证明，`[]` 表示退化区间，两者不可混同。无基证据 `critical_basis_unavailable` 为 unresolved；定义域边界 0 提前返回缺少跨越基证明时为 `threshold_on_domain_boundary_without_proof`，本版不新增边界认证 0 斜率分支。未解析接触传播 `contact_set_unresolved`；全域不可行使用 `infeasible_on_domain` 并保留 Farkas，而非 bounded_on_domain。

### 7.5 覆盖与文件布局

新增正式角色：侧向恒载自由体 Farkas；分离方块 NOT_CONTACT；重叠拒收；completeness_unknown；非 μ critical；input_resolution_limit 括号；负零/顺时针环/旋转起点/anchor≠reference/每体不同参考点；五族每个内块的单体 first_order；Koureas 块 2/4 及一个 G5 内块的分别邻体 lock；回归 c 的 μ_max=2。每个角色保存实际计算的完整证书，不只保存期望状态标签。

正式 binary64 文件布局为 `fixtures/eab2_cases/tia2d-2/<batch>/`。JSON 分片使用 gzip level=9、mtime=0；batch manifest 的 bytes/sha256 始终针对**解压后 UTF-8 JSON 字节**，单独 gzip 索引记录压缩文件字节与 SHA。每批来源清单仅一份，其他大证据外归档；旧批不与新批并存。冻结 fixture 回归不得要求当前源码哈希等于历史来源清单。
