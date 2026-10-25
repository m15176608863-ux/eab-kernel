# WO-C3L4：敏感性、真实使用者全链与发布 ABI v1

## 0. 本轮结果与验收边界

本轮按 Claude 澄清执行：不改变 C++/Python 数学算法及冻结 ABI，只加强双侧证书核验、收窄阈值标签比较例外并显式登记 ABI 域外输入。fresh CMake `eab2/build/clarified_r2` 完整构建、15项 CTest、构建审计、发布 ABI 门、最小隔离 consumer 及 C0/C1/LP/L1/L3 已完整通过；中断的 L4 整轮作废后从头复跑，**175模型、402条敏感性、0失配**。

```text
C3L4_DIFF sensitivity=402 mismatch=0
```

70条阈值隐函数查询的140侧均独立核验原始几何、LP、临界基、多项式恒等式、单侧 Sturm、全部 crossing 与每个斜率；32项合法跨基标签不同进入差异台账，不是失配。32个非 binary64 原始窄带样本逐条记录输入域排除，未舍入、未计为执行通过或静默 skip。最终 Python 快档9109项、全档四分片15193项及静态构造门全部通过；本轮执行范围已完成，证据归档及净增核验见§9。

**所有者验收边界**：现有 stdlib ctypes consumer 已满足设计 §8.5，Claude 验收亲自运行。最新 Claude 裁定明确：所有者新鲜 Git 树验证与一路非作者独立对抗由 Claude 负责，记录为“待所有者验收”，不作为 Codex 执行任务 PARTIAL 的原因。此处不冒称两项已通过，不将 fresh CMake 或最小字节副本称为 Git 新树。本轮执行门全部绿，Codex 工单以 C3L4_DONE 交付；所有者后续验收状态另列。

| 工单项 | 本轮实证 / 保留范围 |
|---|---|
| P0.1 精确敏感性 | 新产物263项核心检查通过；稳定基、回收锥、Mills/Freund ±d、阈值隐函数证书齐备 |
| P0.2 种子传播 | 新产物42项几何种子门；独立 harness 原始几何重建并比较派生期望 |
| P0.3 差分 | 六层全部完成；L4 402/0，32项基依赖标签差异与32项 ABI 域外样本分别登记 |
| P0.4 对称证明/能力下限 | 对称规则沿用基点；本轮393字段能力下限、0例外，未放宽认证要求 |
| P0.5 全链/冻结 | 新发布 DLL 隔离 consumer 6例/18敏感性/0失配；§8.5 已满足 |
| P0.6 ABI | 新产物87项ABI检查；31导出/28结构/能力/字段类型冻结门0 findings |
| 比较器补门 | 81门通过；8个checker源内变异产生9个目标语义红，前后基线绿 |
| P1 元门/生产内部变异 | 沿用上一轮26模型/86通道/0失配及6个生产源内变异证据，明确旧产物身份，未冒称本次中断后重跑 |
| P2 规模耗时 | 沿用上一轮3对6冷进程报告，不设门，不冒称新产物性能测量 |
| Python收尾 | 快档9109、全档15193项GREEN；四片节点多重集合一致，0 failed/skip，静态0违例 |

## 1. 输入、范围与回退锚点

- 工作树 `D:/eab-wt/cx-c0`，分支 `eab2-c3l4`；开工 HEAD 为 `b34c966957b681b45cdb13acaaa09bfc1d6c5fe6`，当时干净。
- 设计 `docs/eab2_design.md` 实读 SHA-256：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`，与工单一致。
- 实际写域：本树 `eab2/`、`tools/`、`tests/`、本单报告/证据；没有改 `src/eab` 数学实现，没有写姊妹树、设计正本，没有安装/下载，没有 Git 写操作，没有结束非本单启动的进程。
- Python 3.12.10；沿用 C0 固定编译器及浮点合同、`core.autocrlf=false`，不改设置。源码 UTF-8 无 BOM；新增批处理为零。
- 回退锚点是上述干净基点与逐文件交付清单；本单不执行 reset/checkout。H1 使用带哈希的字节导出，不冒称新鲜 Git worktree。
- 开工先完成 Python 四分片全档，随后才编辑生产实现。运行记录及命令落盘，所有 pytest 禁 cacheprovider 且显式 basetemp，构建临时文件位于 ignored tmp。

本次澄清前的完整交付回退锚点为 [上一轮120文件原样归档](file:///D:/eab-evidence/reports/codex/C3L4_evidence/clarification_20261023/prior_handoff/prior_delivery.zip)（SHA-256 `2ad375af3b9ba1259dd0537f8f379140031efd6222c567cb7c917bdfd5e64bb3`），见 [intake](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/intake.json)。未执行任何 Git 写或自动回退。

## 2. 敏感性合同与实现对照

实现见 [sensitivity.hpp](file:///D:/eab-wt/cx-c0/eab2/src/sensitivity.hpp)、[sensitivity.cpp](file:///D:/eab-wt/cx-c0/eab2/src/sensitivity.cpp)，具名门见 [test_sensitivity.cpp](file:///D:/eab-wt/cx-c0/eab2/tests/test_sensitivity.cpp)。泛型域无关 statics 层不含 TIA 专用解析。

| 合同 | 实现与核验 |
|---|---|
| 稳定基：满秩、原/对偶可行、基本变量严格正、全部非基约化成本非零 | 先核原始精确证书及严格稳定性；`stable_original_unscaled_dual_three_seeds`、`validity_direction_and_dimension_contracts` |
| `dV = xᵀdc + yᵀ(db−dA·x)` | 使用原始未缩放 LP 的 exact_x 和 maximize exact_y；不重新使用浮点显示量；`stable_original_unscaled_dual_three_seeds` |
| 不稳定时先核两侧最优集回收锥 | 精确求原侧、对偶侧射线；非零射线及可行性核过才报 singular/possibly_discontinuous，无斜率；`both_optimal_recession_guards` |
| 两最优集有界时 Mills/Freund | 单个精确 LP 对 ±d 各解一次，dA/db/dc 同时反号；左斜率是反向 LP 值的负数；`g5_mills_smooth_and_switch`、`min_max_mapping_and_reverse_direction` |
| 不能把不稳定基套固定基公式 | `unstable_basis_cannot_hide_switch`，并有生产源码内部变异门 |
| 活载系数位于 A | 微分活载列，不仅 RHS；`live_load_column_is_not_rhs` |
| 阈值隐函数 | 闭阈用阈值处仍有效的改进射线基；开阈用机构基；逐越零分量求 `−φ_p/φ_μ`；奇异基/零分母/缺失证据不给认证斜率；`open_and_closed_threshold_implicit_derivatives`、`threshold_ties_singularities_and_missing_evidence` |
| 多分量/有效方向 | 同斜率保留所选基全部 tied_labels，不同斜率 one_sided/tie；方向域进入最终分类；非 smooth 的批 Jacobian 为 null，不把单侧值伪装成唯一梯度 |

### 锚点与标量约定

自由体力矩平衡行、exact_y/mechanism 都是 **dof_anchor 旋量**。接触列微分为
`d[(p−a)×g] = (dp−da)×g + (p−a)×dg`；`g=N±μT`，`dg=dN±(dμ·T+μ·dT)`。
参考点 o 不变而锚点 a 具有种子时，荷载锚点矩微分是
`dM_a=dM_o−(a−o)×dF−da×F`。参考点重参数化时同时变换输入力矩。所有算术以原始有理数据进行，浮点仅承担既有几何 ABI 的精确 binary64 输入。

`quality=exact_jet` 沿用 Python 裁判输出，包括保留 null/unresolved 的结果；这表示所执行的精确算术路径，**不把 null 当作已认证导数**。所有非空斜率都须经过独立证书核验。此口径不是将未知斜率升级成证书。

## 3. 几何种子传播与独立差分

[geometry_seed.cpp](file:///D:/eab-wt/cx-c0/eab2/src/geometry_seed.cpp) 从排序的 body/原始 vertex ID 接收 `[参数][顶点][2]` 有理种子，验证完整维度、ID 顺序、共享顶点同速。由接触标签反查原始边，精确传播接触点、T/N、接触力矩、恒载 RHS、活载 A 列和锚点效应，不把已存 dA/db/dc 当输入。

- [test_geometry_seed.cpp](file:///D:/eab-wt/cx-c0/eab2/tests/test_geometry_seed.cpp)：42 项检查，含非对称手构公式、顺/逆顶点顺序的 original ID、共享顶点冲突、大平移、参考点重参数化。
- [独立 L4 harness](file:///D:/eab-wt/cx-c0/tools/eab2_c3l4_diff.py) 用 Python Fraction 从原始几何重建 A/b/c 与种子，逐项比较语料的派生期望 dA/db/dc；不复用 C++ helper。解证书、Mills 两次 LP、回收射线和隐函数分量均另核。
- [具名 harness 门](file:///D:/eab-wt/cx-c0/tests/test_eab2_c3l4_harness.py) 覆盖截断通道、错误形状、共享顶点冲突、活载漏列、原始种子偏差、伪最优/伪回收射线、±d 符号、开闭阈基、丢失有效条件及证明能力退化。
- 比较 differentiability、quality、左右值、reason、validity_conditions；标签按 §4 区分阈值逐侧完整基证核验与非阈值严格比较。保留 `L1 接触骨架不变` 与 `true_vv_excluded_from_statics` 解释界限。未将 finite tests 称为任意输入域证明。
- formal 280 条均带 geometry_seed，其中 276 条有可用 LP 及存储派生期望；另外 4 条要求 derived_seed=null。G2/G3/G4 的 amplitude、wavelength 各 12 条/族均覆盖共享两侧/边界体的传播，但 Python 该族无认证斜率，不能写成已有这些家族的解析灵敏度证明。formal 的显式 live seed 全零；非零活载另由核心、ABI 三通道及公开锚点元门实际覆盖。稳定基和非零 dc 路径由核心单测覆盖，不冒充在这 402 条中出现。

### 本轮全量 L4 实际计数

| 来源族 | 敏感性查询数 | 本轮失配 |
|---|---:|---:|
| formal/TIA-G1 | 75 | 0 |
| formal/TIA-G5 | 69 | 0 |
| formal/TIA-G2 | 39 | 0 |
| formal/TIA-G3 | 39 | 0 |
| formal/TIA-G4 | 39 | 0 |
| formal/named_regression | 11 | 0 |
| formal/contract_coverage | 8 | 0 |
| T1b 形貌 | 72 | 0 |
| thickness 厚度窄带 | 50 | 0 |
| 合计 | **402** | **0** |

本轮分类为 smooth 129、one_sided 2、singular 36、unresolved 235，402条均实际调用；无认证斜率的查询保留 null 与原因，不只选择好算点。完整重跑耗时 171.109151 s，源码前后相同，发布 DLL SHA 与本轮完整构建一致。逐查询结果及32项非失配标签台账见 [L4汇总](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/l4_summary.md) / [机器汇总](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/l4_summary.json)，完整结果在 [L4数据](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/differential/l4.json.gz)。

### 闭式与基准核对

G5 滑移区 `dF/dμ=2P, dF/dP=2μ, dF/dh=0`；铰接区 `0, 4h/(L−b), 4P/(L−b)`；N=3、L=3、h=P=1、μ=1 时 μ/h 的右斜率 0、左斜率 2，P 方向 smooth 2；μ=0 为 singular 并返回回收证据。G1 未反转 `dμcrit/dt=1`，细长例 `dμcrit/dt=1−2th/l`、`dμcrit/dh=−(1+t²)/l`；T1b A=1/2048、t=3/32 的 `dμ/dA=−2043/64`、`dμ/dt=2043/2048`。min `p·x1` 导数 0 由显式 min/max 映射单测守护。上述公式只在相应具名模型、稳定骨架和有效域内宣称。

T1b 当前验收数据比工单“23 正形貌点”更强：36 行中 A 有 26 个、t 有 28 个认证 smooth；本单按当前 acceptance_fix 的 13/16/30 升级点执行，而非退回旧数量。厚度窄带历史材料无导数字段，其新导数期望由未改动的 Python 裁判生成并核验，不称历史冻结斜率。

**窄带输入域限制与本次裁定**：原有 39 样本+18 厚控制中，公共 binary64 ABI 无损可表达的是 7 样本+18 控制，即上述 25 模型记录（19 个唯一几何）；另外 **32 个非 binary64 精确原始样本属于已冻结 ABI 输入域之外**，没有四舍五入冒充原输入。本次 Claude 裁定要求逐条登记其 ID、来源、不能精确传输的具体量与理由；在域外清单完整且域内全部执行的前提下，不因这些样本单独判 PARTIAL，也不扩写发布几何 ABI。域外条目不能计入执行通过数、差分失配数或静默跳过数，更不能宣称“全部精确有理原样输入已通过”。

本轮32项域外清单已由新diff实际输出，每项记录 source_summary、input_fixture、source_name、ratio、reason=`non_binary64_exact_input`、failed_fields及first_failure（body/字段/精确有理值）；详见 [L4逐项汇总](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/l4_summary.md) 和完整L4的 `abi_input_domain_exclusions`。域内25条窄带模型记录全部执行、50条敏感性0失配；只有 thickness/sample/thickness_00_08 的两斜率非空，A为−509/48、t为509/512。输入域排除与32项标签差异是不同台账，不能混计。

`min p·x1` 在 0≤x1≤1、p=0 的精确结论是右导数 0、左导数 1；本单不把工单简写“导数 0”扩大成 smooth 双侧 0。设计 min/max 符号映射未变，因此登记这一解释后继续。

## 4. 比较规则澄清、完整证书与有牙的负门

C3-L3 “仅一侧有阈值证明也可接受”的对称规则在 b34c966 已存在；本单不虚构再次修复。通用比较器允许证明能力不同，但非空一侧必须独立核验；冻结语料的“不弱于Python”是额外门。新L3对冻结formal/T1b实际检查106字段、0例外；新L4实际检查393字段、0例外。Python已认证的阈值/斜率不得退成null或近似。

### 阈值 labels：逐侧完整，跨基差异登记

只有 `target=critical` 且双方 `method=implicit_certificate` 时，才把基依赖 tied_labels 从跨后端集合相等比较中移出；比较器入口自身先完成双方 `verify_critical` 与 `verify_sensitivity`，不依赖外层偶然先验过Python。每侧均：

1. 从原始几何重建矩阵和种子，核精确阈值、attained、原/对偶或归一化射线证书；开阈选择仍有效的机构侧，闭阈选择仍有效的改进射线侧。
2. 绑定 threshold_certificate.problem 的列标签顺序，核临界基非奇异、端点分量可行、有效方向及 continuation；用独立Fraction消元核全部多项式恒等式，单侧Sturm排除区间内部根。
3. 从该基所有分子独立枚举全部越零分量，逐项核标签、phi_p、phi_mu、`−phi_p/phi_mu`、piece_jacobians及selected_piece；标签/分量的extra、missing、duplicate均拒收，不能用set吞重复。
4. 完整证书核过后，合法临界基不同造成的标签差异进入台账；精确斜率、D+/D−、分类、quality、reason、validity_conditions仍严比。非阈值tied_labels仍严比。

本轮70条隐函数查询/140侧核证，32项合法标签差异位于16个T1b模型的A/t方向；台账保留每侧selected_piece、完整标签、全部phi/斜率及相同语义字段，不删除标签、不强迫求解器复制Python偶然基序。通用ABI caller字符串标签保留原合同并与派生结构化标签合法合并；本轮语料准入另外核实caller标签为空，不把这一语料事实变成ABI限制。

详见 [独立证书复核](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/certificate_review.md)、[L4台账](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/l4_summary.json)。建议下一版设计§4.6明确“所选临界基相关的证书标签”及逐侧完整性要求，并交叉说明§7.4的跨后端比较；本单不改设计正本，也不发明跨所有合法基标签并集作为新的Python合同。

### 新正负门与 checker 内部变异

```text
81 passed in 12.32s
10 passed in 2.19s
10 passed in 2.20s
C3L4_CERTIFICATE_MUTATIONS_OK baseline=2 rejected=8 semantic_failures=9
```

[81门记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/harness_tests.json) 与 [checker内部变异记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/certificate_mutations.json) 的全部受测源SHA与本轮比较器一致。负输入覆盖Python侧、C++侧、双方共同错误、合法不同基、合法caller标签和非阈值仍严格；源内变异不是在结果后追加假数据。

| checker内部缺陷 | 目标语义门 | 实测红数 |
|---|---|---:|
| 跳过Python敏感性核证 | each_threshold_side_rejects_false_labels_and_slopes[component_slope-python] | 1 |
| 跳过C++敏感性核证 | 同族[component_slope-cpp] | 1 |
| set去重掩盖重复crossing | 同族[duplicate-cpp] | 1 |
| 漏crossing标签精确成员 | 同族[extra-cpp]、[missing-cpp] | 2 |
| 漏component/phi/slope等式 | 同族[component_slope-cpp] | 1 |
| 跳过Python临界证书 | each_threshold_side_rechecks_full_critical_proof[polynomial-python] | 1 |
| 跳过C++临界证书 | 同族[sturm-cpp] | 1 |
| 例外扩成非阈值忽略标签 | non_threshold_tied_labels_remain_strict | 1 |

8个隔离mutant源码SHA互异，9个失败均为目标语义断言，非编译/导入/哈希失败；前后各10节点基线绿。此处是独立checker的守护门，不冒充P1的六项C++生产内部变异，也不替代Claude的非作者验收。

## 5. 真实使用者全链与发布 ABI v1

[eab2_tia_consumer.py](file:///D:/eab-wt/cx-c0/tools/eab2_tia_consumer.py) 只使用标准库ctypes并从公共C头读取定义；不导入src/eab、差分harness、pybind或姊妹代码。新构建位于 `eab2/build/clarified_r2`，发布DLL SHA-256：`b08c5558572831b52f17a60253e2ce1ede450a31eed800d8a5b3b053124c75df`；同次test DLL SHA：`95fcb7b6e979c0d54d19b1cc29fd3403014781fb942bd25caee8a0ea00a8915e`，后者只供既有C0/C1/LP测试接口，不能替代真实消费产物。

主代理将新发布DLL、C头、独立脚本、manifest、六份gzip共10文件刷新复制到 `eab2/build/clarified_r2/consumer_standalone`，在该cwd以Python3.12 `-I -S -X utf8` 完整复跑。逐文件SHA、命令及新产物身份可沿 [cpp_execution](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) 核到原始记录；最终 [consumer结果](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer.json)、[隔离清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer_isolation.json) 和 [完整输出](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer_isolation.log.gz) 保留一份权威副本。

链为 body/entrance → assemble_contact_set2 → lock/first_order → solve_limit2 → critical_parameter → evaluate_sensitivity2；L3结果token保留到L4，不二次求解。6个G1/G5代表例涵盖开/闭阈、μ=0 singular、滑移、切换、铰接，18条敏感性与固定期望精确比对，逐条输出D+/D−。新运行原始末行：

```text
EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0
EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0
```

按Claude裁定，该consumer满足§8.5，不再等待额外人工使用者。完整语料数学裁判仍由独立差分harness承担。最小副本不是Git新树；所有者新鲜树和独立对抗待Claude验收，但不阻塞Codex执行任务完成。

[ABI_CONTRACT](file:///D:/eab-wt/cx-c0/eab2/ABI_CONTRACT.md)机器冻结表保持不变。表中旧release_acceptance字串是冻结时历史元数据，当前口径已由正文澄清；不能另行制造人工待办。新构建实读31个完整PE导出、28个结构、全部字段类型/偏移/尺寸、能力581501，0 findings；不是只检查已知符号存在。

### 发布 ABI v1 冻结表（正文索引）

以下函数名统一加 `eab2_` 前缀；完整签名和逐字段类型/偏移以机器可核表为准。

| 函数族 | 数量 | 冻结函数 |
|---|---:|---|
| 基础/错误 | 5 | get_abi_info, self_test, context_create, context_destroy, context_get_error |
| 确定性限额 | 2 | context_get_limits2, context_configure_limits2 |
| 各族版本/尺寸 | 4 | get_c1_abi_info, get_c3l1_abi_info, get_c3l3_abi_info, get_c3l4_abi_info |
| 体/入口 | 4 | body2_create, body2_destroy, entrance2_create, entrance2_destroy |
| 双三态/精确输出 | 6 | query2_batch, membership2_batch, topology2_batch, result_export_exact, local_origin2_exact, result_destroy |
| 装配/接触 | 5 | assembly2_create, assembly2_destroy, assemble_contact_set2, contact_set2_destroy, contact_set2_export_exact |
| 锁定/一阶 | 2 | query_lock, first_order_mobility |
| 静力/临界 | 2 | solve_limit2, critical_parameter |
| 敏感性 | 1 | evaluate_sensitivity2 |

28 个结构中，20 个有 header，`abi_version=1`；8 个嵌入记录无独立版本字段，布局随 v1 冻结。尺寸（字节，均省略 eab2_ 前缀）：

- v1 有头：abi_info 248、context_options 16、error_info 72、context_limits2 32、body2_input 40、entrance2_options 16、query2_input 32、query2_output 40、exact_result 64、c1_abi_info 40、assembly_body2 96、assembly2_input 64、lock2_input 40、c3l1_abi_info 32、limit2_input 40、critical_parameter_input 56、c3l3_abi_info 24、sensitivity_channel2 80、sensitivity2_input 224、c3l4_abi_info 32。
- 无独立头：context 32、point2_bits 16、query2_item 16、string 16、pair2 16、body_load2 48、string_array 24、sensitivity_vertex2 24。Body/Entrance/Assembly/ContactSet/Result 是 context 的别名，运行时另核 type，不重复计结构。
- 生产能力位：CONTEXT=1、BODY2=4、ENTRANCE2=8、QUERY2=16、EXPORT_EXACT=32、LOCAL2=64、LIMITS2=256、ASSEMBLY2=512、CONTACTSET2=1024、LOCK2=2048、MOBILITY2=4096、LIMIT2=16384、CRITICAL_PARAMETER=32768、SENSITIVITY2=524288。测试能力和未实现的预留能力不冒充发布支持。

敏感性输入显式参数数、输出数、通道数及固定行主序，拒绝尺寸/步长/计数溢出、ID 排序错误；多通道产物互异。base result 为同上下文 typed token，保留原问题与证书；不从显示 JSON 反构造原始问题。句柄代次、销毁、FP 环境和失败输出原子性沿用既有合同。[C++ ABI 门](file:///D:/eab-wt/cx-c0/eab2/tests/test_c3l4_abi.cpp) 87 检查；[PE/合同门](file:///D:/eab-wt/cx-c0/tools/eab2_release_abi.py) 实读完整 PE 导出表，逐项比对头文件、冻结表、运行时能力与结构，不只探测已知符号。同尺寸字段类型漂移由逐字段 canonical C type（const、指针层数、数组维数）冻结及负门守护；新发布DLL的完整PE/头/能力/结构门已通过。

## 6. P1 元门与生产内部变异（沿用已执行历史证据）

**证据身份**：本节26模型/86通道及六项生产变异来自上一轮发布DLL `f6c109bf…17df0cd` 和当轮比较器，不是本次L4中断后重新执行。相关C++敏感性/几何种子源及具名单测字节未变，生产变异记录的源SHA仍匹配；但本轮阈值比较器已澄清修改，不能笼统称历史元门全部依赖SHA都未变。新meta/timing阶段未启动，未重复运行或补造记录。

[公开 ABI 元门](file:///D:/eab-wt/cx-c0/tools/eab2_c3l4_meta.py) 当轮 **26 模型、86 通道**，原始几何重建矩阵/种子并独立验返回证书。G1 使用固定种子的精确有理旋转，并联合单位缩放确保所有传输量仍能被 binary64 精确表示；G5 的部分轴向自由度掩码仅能用精确四分之一转，不将斜约束伪装成轴掩码。平移范数为 0、10³、10⁵，另有小特征/大坐标，参考点单独重参数化、锚点大偏移及非零锚点种子。承载系数及 μ 方向导数不变，长度参数导数按 1/s，力单位按参数链式规则变换，标签随几何映射严格比较。

正式 G1 几何的真实参数为 t，`theta=atan(t)` 原来仅为标签。补充两个 θ 通道门，不改 Python 数学合同：从原始接口边重建 t，全部顶点、荷载、锚点及 μ 种子统一乘 `dt/dθ=1+t²`。开阈未反转结果为 1025/1024，闭阈 slender 为 255/256；双方/边界共享参数和独立 dA/db/dc 重建均核过。另有非零荷载/锚点/μ 探针避免“只乘顶点”漏项。新增输入门最终 `6 passed in 0.19s`，不冒称 formal 中原有 θ 查询。

```text
C3L4_META cases=26 channels=86 mismatch=0
C3L4_MUTATIONS_OK baseline=2 rejected=6 semantic_failures=6
```

[变异运行器](file:///D:/eab-wt/cx-c0/tools/eab2_c3l4_mutations.py) 在 ignored 隔离目录修改生产源码内部、编译替换单元，不在产出后追加假数据。两个未变异基线先绿；六个变异的源文件 SHA 各异且全部由目标语义断言杀死，不把编译失败、哈希失败或偶然排序当成功。

| 内部缺陷 | 杀死它的具名门 |
|---|---|
| 原始 y 错乘缩放量 | stable_original_unscaled_dual_three_seeds |
| 漏活载 A 列导数 | live_load_column_is_not_rhs |
| 不稳定基套固定公式 | unstable_basis_cannot_hide_switch |
| 开阈取原侧发散分量 | open_and_closed_threshold_implicit_derivatives |
| ±d 两次 LP 值直接比较、不取负号 | g5_mills_smooth_and_switch |
| 几何种子仅微分 RHS | test_geometry_seed 的活载/接触矩阵手构断言 |

初次变异记录的预期断言文字与实际语义报错文字不一致，修正的是运行器识别串；完整 r2 重跑，未拼接日志。公开元门 r1 为 checker 输入 ID 重映射接线错误，r2 全量重跑；未改生产结果来迎合元门。

## 7. 实测末行、运行完整性与失败历史

### 本轮同一受测产物的已完成阶段

cpp阶段监视638个源文件，前后哈希一致；源清单SHA为 `b212e190ac5860ad08e9f06466dabc1b53bd134a7a5c3e8b3739100a1f1fb3b8`。实际发布DLL与test DLL的SHA见§5。C0/C1/LP/L1/L3均在中断前完整结束、日志与输出SHA核过，Claude 裁定允许复用；不重算已绿阶段，也不复用中断L4的任何partial row。

| 项目 | 原样末行 / 汇总 | 证据 |
|---|---|---|
| fresh CMake / CTest | `100% tests passed, 0 tests failed out of 15；Total Test time (real) =   6.54 sec` | [完整cpp阶段](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) |
| 敏感性核心 | `sensitivity: 263 checks passed` | [完整cpp阶段](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) |
| 几何种子 | `C3L4_GEOMETRY_SEED_OK checks=42` | [完整cpp阶段](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) |
| C ABI | `EAB2_C3L4_ABI checks=87 failed=0` | [完整cpp阶段](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) |
| 构建合同审计 | `EAB2_DELIVERY_AUDIT status=PASS findings=0 vendor_files=71 compiler_commands=28` | [完整cpp阶段](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) |
| 发布 ABI | `EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0` | [完整cpp阶段](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) |
| 隔离 consumer | `EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0` | [完整cpp阶段](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/cpp_execution.json) |
| C0 | `EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS` | [完整阶段复用记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/completed_layers_reuse.json) |
| C1 | `C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086` | [完整阶段复用记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/completed_layers_reuse.json) |
| LP | `OPT_DIFF selected=745 completed=745 mismatches=0` | [完整阶段复用记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/completed_layers_reuse.json) |
| L1 | `C3L1_DIFF assembly=186 first_order=186 lock=404 mismatch=0 strict_fields=495` | [完整阶段复用记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/completed_layers_reuse.json) |
| L3 | `C3L3_DIFF limit=292 critical=2528 mismatch=0` | [完整阶段复用记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/completed_layers_reuse.json) |
| L4从头完整重跑 | `C3L4_DIFF sensitivity=402 mismatch=0` | [新收尾执行](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/closeout_execution.json) / [L4汇总](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/l4_summary.json) |

本轮L3使用一次完整 `--family all`：292 limit、2528 critical、0失配，包含完整T1b；冻结能力下限106字段、0例外。不再把上一轮主运行和补跑拼接为一次。L4新运行逐族计数见§3；能力下限393字段、0例外。正式发布链只用新 `eab2.dll`；C0/C1/LP测试桥明确使用同次 `eab2_test.dll`。

### 最终Python快档与全档四分片

最终快档 **9109** 项、全档四分片 **15193** 项全部 GREEN；四片分派/收集/执行分别为3799、3798、3798、3798，各片节点多重集合一致，0 failed、0 skipped，逐模块实际执行完整。以下依次为快档、全档1–4片及全档静态门的原始末行：

```text
9109 passed in 353.42s (0:05:53)
3799 passed in 993.79s (0:16:33)
3798 passed in 1534.15s (0:25:34)
3798 passed in 873.56s (0:14:33)
3798 passed in 1191.75s (0:19:51)
exact construction AST gate: 0 violation(s)
```

[快档摘要](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarified_fast/summary.json) / [全档摘要](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarified_full/summary.json) 保存完整命令（所有pytest均 `-p no:cacheprovider` 和显式 `--basetemp`，全档另含 `--runslow`）。快档原始5文件、全档原始15文件已追加归档并逐件核SHA，见 [快档归档清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarified_fast/archive_manifest.json) / [全档归档清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarified_full/archive_manifest.json)。

快档与全档使用相同源清单（SHA-256 `22278df56908980455cbe91c944a447a091b332aed6f5aa713d7021322c7075c`），各自 `export_changed=[]`、`live_tree_changed=[]`；638项构建/差分代码源锁也从构建至收尾保持不变。完整受测字节导出1983成员均逐件核SHA，见 [源归档记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/tested_source_archive.json) / [受测源码ZIP](file:///D:/eab-evidence/reports/codex/C3L4_evidence/clarification_20261023/clarified_full/tested_source.zip)。全档后只回填报告、本索引及证据，不改受测代码；字节导出不冒称新鲜Git树。

### 新构建审计路径问题与重跑

首次fresh子目录构建已15/15通过，但构建审计的authored编码扫描误纳既定ignored `eab2/build` 下旧DLL/obj/变异产物，产生570条非源码编码诊断。分类是验证工具路径范围错误，不是编译/算法失败。最小修复显式排除已知 `ROOT/eab2/build`，仍保留args.build/vendor排除；逐条570路径都在旧build内。AST对照证实除此赋值外全部逻辑未变，新nested源码集合等于旧默认集合，编译标志、依赖、/Bv、身份及导出检查不放宽。见 [失败记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/build_audit_failure.json) 与 [只读复核](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/build_audit_review.md)。

修复后从全新 `clarified_r2` 完整重跑cpp阶段，15/15及263/42/87、build audit、release ABI、consumer全绿；不把旧失败阶段日志拼接成绿。

### 被中断的L4与从头复跑

前次L4因模型容量中断，末次进度384条/0失配不作为完成证据。该轮整体作废，partial rows复用数为0；[中断记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/interrupted_layers_execution.json)与 [复用边界](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/completed_layers_reuse.json)保留事实。新 `run_closeout.py.txt` 使用同一已核SHA的r2发布DLL，在新 `tmp/clarified_closeout_1` 从头执行完整402条，之后顺序执行 `clarified_fast` / `clarified_full`。源码、进度、命令、退出码和日志哈希持续落盘。

### 上一轮RED和修复记录（历史，不映射到当前权威gz）

以下原始末行及原始表、日志、旧报告全部取自 [上一轮120文件原样归档](file:///D:/eab-evidence/reports/codex/C3L4_evidence/clarification_20261023/prior_handoff/prior_delivery.zip)，不是当前L4/CTest数据。旧严格集合比较的32红不被改写为0：

```text
C3L4_DIFF sensitivity=402 mismatch=32
9070 passed in 293.14s (0:04:53)
1 failed, 3788 passed in 907.79s (0:15:07)
3789 passed in 785.09s (0:13:05)
1 failed, 3787 passed in 1105.37s (0:18:25)
3788 passed in 717.45s (0:11:57)
exact construction AST gate: 44 violation(s)
118 passed in 393.27s (0:06:33)
exact construction AST gate: 0 violation(s)
```

旧全档15154节点正常结束、2 failed/15152 passed/0 skipped；两项静态失败同源于新增测试顶层纯数据装配helper，随后仅内联真实test驱动，gate/policy未改、未增准入。PE1024字节与AST、L4选择/数据/断言均有等价记录，118项定向与整仓静态0违例为真实修后结果；这些历史绿不被当作新完整全档。详情见旧ZIP内的 `abi_static_repair.json` 及[历史 checks/static_repair_verification.json 原字节](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/superseded_prior_outputs_20261023/static_repair_verification.json)等。

### 开工四分片基线（保留原样）

在编辑生产实现前，15080节点、四片各3770，0skip/0failed，收集/执行多重集合一致，逐模块实际执行完整，源前后不变：

```text
3770 passed in 1423.28s (0:23:43)
3770 passed in 781.18s (0:13:01)
3770 passed in 1079.88s (0:17:59)
3770 passed in 969.15s (0:16:09)
exact construction AST gate: 0 violation(s)
```

基线及旧最终日志见原ZIP与 [外部运行归档](file:///D:/eab-evidence/reports/codex/C3L4_evidence/20261023_run1/)。本轮完整复验是Claude 裁定授权，不再以“第三次全档”作为未决理由；每次中断运行仍必须整体作废，不拼接。

### 复跑入口

[完整构建与分层运行器](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/run_verification.py.txt)、[授权收尾运行器](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/run_closeout.py.txt) 保存全部实际命令；运行器要求新输出目录/固定源锁，不覆盖旧进度。pytest均 `-p no:cacheprovider` 加显式basetemp，slow收集以 `--runslow`明确启用；测试不依赖Git。构建临时产物全部在ignored build/tmp，不入交付证据。

## 8. P2 规模与冷耗时（历史报告项，非门）

本节为上一轮已完整执行的冷耗时，DLL为 `f6c109bf…17df0cd`；本次未启动新timing，不将旧值冒充新DLL测量。

<!-- TIMING_TABLE_BEGIN -->
六个新进程串行执行，无并行 H1；每模型均 5 个体。下表为秒，C++/Python 每格按相同顺序列出；primal 状态、精确值与导数逐项相等。

| 模型 | LP 行×列 / 通道 | primal C++ / Python | 多通道导数 C++ / Python | 冷进程总时 C++ / Python |
|---|---|---|---|---|
| g1_slender（critical） | 9×17 / 2 | 0.361295 / 0.346894 | 0.002627 / 0.006017 | 0.487163 / 0.521441 |
| g5_n3_mu1（滑移） | 10×17 / 3 | 0.003299 / 0.002439 | 0.158589 / 0.179659 | 0.280762 / 0.350206 |
| g5_n3_mu2（切换） | 10×17 / 3 | 0.002758 / 0.002626 | 0.137356 / 0.159442 | 0.262072 / 0.327453 |

原始末行 `C3L4_TIMING_REPORTED pairs=3 cold_processes=6`；[完整计时](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/checks/cold_timing.json) 同时保留构造时间、精确结果、DLL/脚本 SHA 和每个子进程命令。
<!-- TIMING_TABLE_END -->

计时工具 [eab2_c3l4_scale.py](file:///D:/eab-wt/cx-c0/tools/eab2_c3l4_scale.py) 将接触构造、primal、精确种子+多通道导数分开计时。C++ 含 ctypes/JSON 开销，Python 无对应传输开销；每后端/例仅一个冷进程样本，不作为大装配吞吐、统计显著加速或工程性能承诺。

## 9. 证据卫生、真实净增与实际遗留

[完整交付清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/deliverables.md)、[逐文件SHA与净增（历史原字节归档）](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/superseded_prior_outputs_20261023/hygiene.json)、[交付完整性核验](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/delivery_integrity.json) 保存最终落盘后的哈希、链接、运行状态与净增核验。相对b34c966的**真实候选树净增**：**<!-- NET_BYTES -->1570198<!-- /NET_BYTES --> B**；算式为当前候选树 **<!-- CANDIDATE_BYTES -->55448790<!-- /CANDIDATE_BYTES --> B** 减基点全部Git blob **53,878,592 B**，不是新增与修改文件大小之和。目标≤2,000,000 B；未stage/commit，候选树不等于已提交树。旧净增1,142,030 B只属于历史，不用来冒称当前净增。

WO-C3L4-fix 仅将四项已被新运行取代的历史 JSON 原字节追加归档；[精确映射](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/superseded_prior_outputs.json)另链接[原 tied_labels 取证](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/superseded_prior_outputs_20261023/tied_labels_forensics.json)与[原构建审计](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/superseded_prior_outputs_20261023/build_audit.json)。这些文件的字节、SHA、旧 RED/GREEN 结论和上述原 C3L4 净增数字均未改写；修复轮最终净增另由修复报告记录，不把本节历史快照冒称当前修复结果。

- 无编译产物入库；单文件≤1MB的既有门与允许列表不放宽。UTF-8无BOM，批处理纯ASCII；构建TEMP不进入已提交证据目录。
- `src/eab`数学、设计SHA与静态构造policy保持原合同；新增比较器/审计修复不增加准入，不改历史哈希过门。
- 每个差分阶段最终保留一份权威完整数据及原始日志；新结果覆盖当前位置之前，旧120文件已原样ZIP归档并逐文件验SHA。历史RED只链接旧归档，不误指当前权威gzip。
- 旧来源归档、完整源清单和映射见 [归档总入口](file:///D:/eab-wt/cx-c0/reports/EVIDENCE_ARCHIVE.md)、[clarification intake](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/intake.json)。本地归档不是远端备份，不自动回退或覆盖后续所有者修改。

### 与设计/原预期的差异及处置

1. **阈值标签口径已裁定并实际复验**：70查询/140侧完整证书通过；32项合法跨基标签差异登记而非失配，非阈值严比。台账见 [L4汇总](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/clarification/l4_summary.md)、[完整L4](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/differential/l4.json.gz)。建议下一版设计§4.6补明基相关证书标签，与§7.4比较对象分开列示；不修改生产择基或Python数学。
2. **32项ABI域外已显式排除**：逐项来源/精确有理/失败字段可追溯，不舍入、不算执行通过、不算静默skip；这是发布输入域边界，不单独造成PARTIAL。与32条标签差异不同，见同一汇总的独立域外表。
3. 对称证明规则原已在b34c966，本单新增能力不退化门；本轮393字段、0例外。T1b当前验收库存与新生成厚度导数不混称历史冻结字段。
4. min `p·x1` 的工单简写“导数0”按方向解释：p=0处右0、左1，不伪称smooth双侧0。exact_jet含null沿用Python字段口径；null不冒充认证斜率。
5. consumer满足§8.5，发布ABI表及能力冻结不变。平台仅MSVC x64/Python3.12 ctypes；公开几何传输为精确binary64，资源限额非全算法墙钟/内存保证。
6. P1旧元门/6生产内部变异、P2旧冷计时以真实历史产物身份保留；本次未启动新meta/timing。相关C++源未变，但新checker规则不能凭历史元门声称已重新测过。新81门及8checker内部变异另有当前源SHA匹配证据。
7. **待所有者验收**：新鲜Git树与一路非作者独立对抗核查由Claude负责；Claude 已裁定这两项不是Codex执行任务PARTIAL的原因。作者不冒称已经取得0critical/0major或新鲜Git验收。
8. **实际遗留与完成判定**：本轮Codex执行范围无未完成项。L4从头完整402/0，正负门及台账齐备；最终快档9109/全档15193、静态0违例，归档/链接/真实净增核验通过。已裁定的标签、consumer与ABI域外边界不重新列为阻塞；第7项所有者验收明确另列。因此交付判定为C3L4_DONE，不等同于作者代签所有者验收。

C3L4_DONE

## 修复轮 WO-C3L4-fix（cb14522之上；2026-10-23）

本节只追加，不覆盖上述历史。Claude验收发现开阈多分支时Python/C++同错，旧402/0不能证明分支完备；本轮按Claude新合同开工后，进一步核实该合同的双无穷小定理在搜索域上边界存在反例，已按工单要求停止生产实现。

取 `mu*=mu_max=1`、活载参数 `t=1-epsilon`；在域外 `mu=1+(1±eta)epsilon` 原文(a)(b)精确证书同时成立，但整个 `[0,1]` 内LP最优值均为0，无UNBOUNDED点，因此域内阈值没有有限右导数1。真实两矩形L1/L3及独立标准库K运算均已核验。详见 [修复轮报告](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_report.md)、[完整定理反例](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/theorem_domain_counterexample.md)、[真实几何证据](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/historical_compaction.json)。

开工全档15193项、四分片、静态0违例已完整通过，源前后不变；这是未修复cb14522的基线，**不是新算法验收**。未改生产代码、数学、ABI、已有测试或冻结语料；验收小项也未实施；没有commit或结束非自身进程。原有阈值导数缺陷仍在。

归因勘误：按 WO-C3L4-fix 要求，上方相关归因已订正为“Claude 裁定”；除此类归因及已归档证据链接订正外不覆盖历史。原字节保存在归档。

需Claude明确域内夹逼前提、阈值出域/空集的方向导数语义及上下边界专用规则，再继续实现。所有者新鲜树/非作者验收另列，不是本轮阻塞原因。当前证据与相对b34c966真实净增见 [本轮交付清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/historical_compaction.json) 和修复轮报告。

C3L4FIX_BLOCKED：双无穷小定理缺少搜索域边界前提；需 Claude 裁定域内夹逼与空集/边界导数语义


### Claude 续裁定后的继续实施（进行中）

Claude 已补充域内夹逼前提、原始域绑定与完整高阶 primitive 重建要求，前节 BLOCKED 是历史停止点，不代表当前状态。当前 Python/C++ 与独立 K checker 已接入；正在完成奇异候选标签及非零荷载分支探测。最终完整验收尚未执行，见[修复轮当前报告](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_report.md)与[进度](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/progress.json)。


修复轮续裁定后的实现、Claude 返修草稿与本次收尾证据已统一收口至[修复轮报告](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_report.md)及[收尾报告](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_close_report.md)；以上历史正文不改，最终新鲜树与非作者结果仍由 Claude 填入并验收。

所有者终验（2026-10-25）：新鲜 Git 树 fa481ba 上下层全部 0 失配、L4 全族 1252 条 0 失配、Python 全档 15421 全绿，三轮非作者对抗的全部发现已关闭，详见[修复轮报告](C3L4_fix_report.md)末节。

C3L4FIX_DONE
