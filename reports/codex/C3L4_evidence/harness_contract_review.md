# WO-C3L4 差分合同与覆盖范围只读复核

审查日期：2026-10-23。性质：作者团队内交付自查，不是独立对抗验收。初审只读取现有源码、正式语料与已完成证据；随后按根代理授权，定向补跑独立完整 T1b L3 族（不是中断拼接或重跑全网格），并更新本报告。未修改 harness、测试、期望或 Python 数学合同。下列数字是本次读取时的事实，最终 H1、归档路径和发布验收以根报告为准。

## 1. 结论先行

生产 DLL 全量 L4 原始末行是 **`C3L4_DIFF sensitivity=402 mismatch=32`**，不是 0 失配。175 个模型的 402 条查询均执行完，运行前后源哈希一致。32 项全部是 T1b 的严格 `tied_labels` 差异；不能因精确斜率相同而自行豁免。formal 与 thickness 无差异。

主要证据：[完整差分](differential/l4.json.gz)、[原始日志](differential/l4.log.gz)、[标签取证说明](tied_labels_analysis.md)、[逐项取证 JSON](tied_labels_forensics.json)。DLL SHA-256 为 `f6c109bfcc17edf4b8343c4cfa4c56f565bd725f3d1fcce75f0ad623b17df0cd`。

**不能据此宣告整单完成**：严格标签合同未闭合；独立 ctypes 自动复跑不等于一名真实 TIA 人工使用者已经复跑确认。初审曾发现 θ 链式转换没有具名门，现已另行增强公开元门，详见 §4.2；不得继续把该已补项写作当前缺失，也不能因此掩盖前两项。

## 2. 逐族实跑计数

| family | 模型数 | sensitivity | smooth | one_sided | singular | unresolved | 严格差异查询 | 斜率 floor 字段 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| formal/TIA-G1 | 27 | 75 | 14 | 0 | 8 | 53 | 0 | 42 |
| formal/TIA-G5 | 27 | 69 | 55 | 2 | 10 | 2 | 0 | 171 |
| formal/named_regression | 7 | 11 | 3 | 0 | 5 | 3 | 0 | 9 |
| formal/TIA-G2 | 15 | 39 | 0 | 0 | 3 | 36 | 0 | 0 |
| formal/TIA-G3 | 15 | 39 | 0 | 0 | 3 | 36 | 0 | 0 |
| formal/TIA-G4 | 15 | 39 | 0 | 0 | 3 | 36 | 0 | 0 |
| formal/contract_coverage | 8 | 8 | 1 | 0 | 4 | 3 | 0 | 3 |
| t1b | 36 | 72 | 54 | 0 | 0 | 18 | 32 | 162 |
| thickness | 25 | 50 | 2 | 0 | 0 | 48 | 0 | 6 |
| **合计** | **175** | **402** | **129** | **2** | **36** | **235** | **32** | **393** |

- formal 为 114 模型/280 查询，其中 limit 160、critical 120；通过 manifest 的分片哈希、完整 query index 集、limit/threshold 绑定校验，不是抽选几例冒充全量。
- 实际 method 计数：Mills/Freund 61、implicit_certificate 70、optimal_face_recession 36、无 method 235。**这批公开全量语料没有 stable_basis 实例**；稳定基三种子、未缩放 y 和 min/max 映射由 C++ 具名单测覆盖，不能写成 402 查询都覆盖了稳定基路径。
- 235 条 unresolved 不是 235 条认证导数：原因分别为 `threshold_on_domain_boundary_without_proof` 126、`finite_optimum_required` 63、`critical_basis_unavailable` 19、`exact_threshold_basis_and_seed_required` 16、`no_valid_direction` 11。它们与裁判一致，但“未伪造导数”不等于“已具备该处导数证明能力”。
- `quality=exact_jet` 不能单独作为存在认证斜率的判断。此语料中 singular/unresolved 也保留该 quality；必须联合 differentiability、非空导数字段和证书判断。

## 3. 闭式核对：对应的实际 query 与数值

以下 `右/左` 指坐标导数，`D− = −左`。正式 query index 是语料原始索引，不是本工具重新排列后的序号。数值取自本轮 DLL 差分行；完整字段通过严格比较与独立证书核验。

| 模型与实际参数 | query index / 参数 | 实际右 / 左 | D+ / D− | 状态及闭式对应 |
|---|---|---|---|---|
| `g5_n3_mu1`，实际 μ=1/4，P=h=1，L=3，b=1 | 3 / μ | 2 / 2 | 2 / −2 | smooth，2P |
| 同上 | 9 / P | 1/2 / 1/2 | 1/2 / −1/2 | smooth，2μ |
| 同上 | 10 / h | 0 / 0 | 0 / 0 | smooth，滑移区高度导数 0 |
| `g5_n3_mu3`，实际 μ=2，其余同上 | 3 / μ | 0 / 0 | 0 / 0 | smooth，铰接区 |
| 同上 | 9 / P | 2 / 2 | 2 / −2 | smooth，4h/(L−b) |
| 同上 | 10 / h | 2 / 2 | 2 / −2 | smooth，4P/(L−b) |
| `g5_n3_mu2`，实际 μ=1=2h/(L−b) | 3 / μ | 0 / 2 | 0 / −2 | one_sided |
| 同上 | 9 / P | 2 / 2 | 2 / −2 | smooth |
| 同上 | 10 / h | 0 / 2 | 0 / −2 | one_sided |
| `g5_n3_mu0`，μ=0 | 3 / μ，11 / P，12 / h | 均 null | 均 null | singular / possibly_discontinuous，非零回收射线经核验 |
| `g1_unreversed_t1`，t=1/32，h=1 | 8 / t | 1 / 1 | 1 / −1 | smooth，开阈机构基，dμcrit/dt=1 |
| 同上 | 9 / h | 0 / 0 | 0 / 0 | smooth |
| `g1_slender`，t=h=1/4，l=2 | 8 / t | 15/16 / 15/16 | 15/16 / −15/16 | smooth，1−2th/l |
| 同上 | 9 / h | −17/32 / −17/32 | −17/32 / 17/32 | smooth，−(1+t²)/l |
| `t1b/03`，A=1/2048，t=3/32，phase=0，periods=1，asymmetry=1/2 | 0 / amplitude | −2043/64 / −2043/64 | −2043/64 / 2043/64 | smooth，闭阈 16359/262144 |
| 同上 | 1 / tilt | 2043/2048 / 2043/2048 | 2043/2048 / −2043/2048 | smooth |
| `thickness/sample/thickness_00_08` | 0 / amplitude | −509/48 / −509/48 | −509/48 / 509/48 | smooth；该窄带子集仅此模型有两条非空导数 |
| 同上 | 1 / tilt | 509/512 / 509/512 | 509/512 / −509/512 | smooth |

注意 `g5_n3_mu1` 的后缀是采样编号，不是 μ 数值。未反转 G1 的 μ limit 查询仍 singular；细长 G1 的 μ limit 查询为 `finite_optimum_required`，不能把同模型已经认证的 critical 几何导数混称为 limit 导数。

`min p·x1` 不是上述正式公开几何查询。`eab2/tests/test_sensitivity.cpp::min_max_mapping_and_reverse_direction` 在 0≤x1≤1、p=0 上用 maximize 种子 dc=(-1,0) 核右导数映射回 min 后为 0，左导数为 1；不能把工单中的“导数 0”扩写成两侧 smooth 0。该门还要求两个方向精确 LP 证书与调用方 ties 保留。

## 4. 种子传播覆盖及真实边界

### 4.1 独立计算链

[L4 harness](../../../tools/eab2_c3l4_diff.py) 从原始 body/vertex ID、顶点、荷载、reference_point、dof_anchor 和几何 seed 重建矩阵，不读取 C++ helper 的中间几何作为 oracle：

1. 由标注的原始 CCW 源边重建 T 与 dT，并旋转获得 N、dN。
2. 对 g±=N±μT 计算 dg±=dN±(dμ·T+μ·dT)。
3. 自由体力矩行取 dof_anchor；微分 `((p−o)×g)` 时同时包含 dp−do 与 dg。
4. 荷载在 reference_point 与 dof_anchor 间精确换算；恒载进 db，活载导数进 **A 的 α 列**，不是只动 RHS。
5. 按物理列标签重排，独立精确核 dA/db/dc；critical 同时构造单位 μ seed。

正式 280 查询全部带原始 geometry_seed；其中 **276 条带存储的派生 dA/db/dc 期望**，逐项与独立重建值比较。其余 4 条缺可用 LP，要求 derived_seed=null，不臆造传播结果。T1b 和 thickness 的种子由原始几何重建后同样核验，但它们的派生矩阵不是新添进 tia2d-2 的“冻结字段”；不得把 fresh Python 派生值描述成源时代冻结期望。公共几何目标 c 固定，所以这些几何传播的 dc=0；任意非零 dc 的域无关公式另由核心三种子单测覆盖。

### 4.2 共享参数实际库存

| 正式家族 / 参数 | 查询数 | 带派生矩阵期望 | 非空斜率查询 | 真实覆盖 |
|---|---:|---:|---:|---|
| G1 / t | 24 | 24 | 7 | 所有 5 个体的原始顶点有非零共享 jet，包括两端固定体 |
| G1 / h | 24 | 24 | 7 | 同上 |
| G5 / h | 21 | 21 | 18 | 顶点、恒载与 dof_anchor 同步微分；边界/受载板不被冻结为“无参数” |
| named regression / h | 2 | 2 | 1 | 同类共享高度传播 |
| G2 / amplitude，wavelength | 各 12 | 各 12 | 各 0 | 两参数各覆盖所有 5 个体；传播可核，暂无该家族认证导数 |
| G3 / amplitude，wavelength | 各 12 | 各 12 | 各 0 | 同上 |
| G4 / amplitude，wavelength | 各 12 | 各 12 | 各 0 | 同上 |
| G5 + named regression / P | 23 | 23 | 19 | 非零恒载 seed |

正式 280 条的显式 `live` seed 全为零；因此不能拿这 280 条单独声称“非零活载种子已由正式语料实跑覆盖”。补充覆盖在 `test_c3l4_live_seed_enters_actual_A_not_only_rhs`、C++ `live_load_column_is_not_rhs`、ABI 三通道用例及公开 anchor-frame 元门中；其中前者是独立 checker 门，不是单独的生产变异证据。

**θ 的限定与补门**：`src/eab/adapters/tia2d.py::g1` 明示 `theta=atan(t)` 只是标签，几何使用精确有理 t。ABI 接收调用方给出的有理 jets，不从角度浮点函数自动生成它们；formal 本身没有 θ 参数，不能将 t 的 24 条自动改写成 θ 的 24 条。初审之后，`tools/eab2_c3l4_meta.py::theta_direction` 已按原始 G1 接口斜率精确构造 `dt/dθ=1+t²`，在共享顶点、恒/活载、anchor、μ 全通道同步缩放；`test_public_theta_chain_shared_geometry_reconstructs_scaled_raw_seed` 和 `test_public_theta_chain_scales_nonzero_load_anchor_and_mu_channels_too` 分别守护原几何矩阵传播及非零通道运输。公开 DLL 新增两例 θ 查询，细长例为 `255/256`，未反转例为 `1025/1024`，最新元门总数 26 模型/86 通道/0 失配。此增强补上了具名 θ 局部链式门，不等于重新冻结了带 θ 查询的整套 formal 语料，也不是三角函数近似生成任意角几何的证明。

### 4.3 负例与边界

- 独立 checker：五种 seed 通道尺寸错误、共享顶点 jet 冲突、伪造 dA/db/dc、活载遗漏、错号 D−、零回收射线、缺失有效条件、缺失 ties、在不稳定基上套固定基公式、丢弃已认证斜率等具名门。
- C++ geometry 门：遗漏/乱序顶点、错误原始 vertex ID、遗漏/乱序 body、共享接口冲突；另有非对称原始几何 + 荷载/锚点手算 oracle 和 reference/anchor 协变门。
- C ABI 门的 35 种无效请求：计数/步长/版本、非规范分数、空指针、重复参数/ID、溢出、非法方向标志、共享点冲突等；还检查 typed result、跨 context、过期 token 和失败输出不变。
- 这些负例证明已测试拒收条件，不证明任意参数扰动后 L1 骨架自动保持。`L1接触骨架不变` / `true_vv_excluded_from_statics` 必须原样保留；有效方向仍需调用方和临界证据提供支持。

## 5. T1b、窄带与 proof floor 的准确口径

### 5.1 T1b 期望版本

[T1b 冻结子表](../../../tests/data/eab2_c3l4_t1b_expected.json) 来自已验收 `T1b_evidence/acceptance_fix/p1_classification.json`，36 模型：A 导数 smooth 26、t 导数 smooth 28。工单提到的“23 个正形貌点”不是当前最终能力库存，不能为了与旧计数一致而丢弃后来获得认证的点。8 个无精确阈值点不提供斜率；两个 A=0 控制点的 A 方向不满足有效骨架，t 方向仍可认证。

T1b 每条完整 sensitivity 合同由未修改的 Python 裁判当前求值，并先检查状态/左右导数/reason 与冻结子表一致；完整标签等字段随后严格对比 C++。32 项 ties RED 正是在这一步留下，没有放宽为只核数值。

### 5.2 厚度窄带输入域

冻结窄带原有 39 样本 +18 厚控制。公共 assembly 输入是 binary64；当前选取可逐数无损表示的 7 样本 +18 控制=25 条模型记录，含 19 个唯一模型。**32 个非 binary64 精确样本未在 C++ 公共 ABI 中重跑，未四舍五入冒充原输入**。筛选与拒绝原因由 [厚度工具](../../../tools/eab2_c3l3_thickness.py) 固定核查。

窄带归档冻结的是阈值和 attained，不含导数；本轮 50 条导数的期望来源明确为 `fresh Python referee; frozen threshold only`。其 0 失配不能写成“完整 39 样本的源时代冻结导数全过”。

### 5.3 能力不弱于 Python

- 完整 L4 JSON 明确持久化 **393 个非空斜率字段**、0 exceptions：formal 225 + T1b 162 + thickness 6。它是 **131 个有斜率查询 ×3 字段**（directional/right/left），不是 393 个独立参数。quality 同时必须 exact_jet。
- 当前 L4 循环在每个绑定 base 上实际调用阈值 floor；按已完成的查询覆盖及冻结输入重建，所核非空 exact_threshold 为 **113 个字段**：formal 有 critical sensitivity 的 60 模型 + T1b 28 + thickness 25。此 113 是本次只读按执行循环重建的数，**L4 summary 没有把这个中间 `floor` 汇总持久化**，不能伪称 JSON 直接记录了 113。
- L3 的 frozen formal+T1b 完整库存是 114+36 个 critical 查询，其中 Python 非空 exact_threshold **106 个字段=78+28**。首个已正常完成的全族运行使用 `--family all --t1b-required`，实际 T1b 为 13 模型，末行 `C3L3_DIFF limit=269 critical=2505 mismatch=0`，floor **83=78+5**，不能误报该次已核 106。随后独立完整运行 `--family t1b`（不带 required）已经正常完成，末行 **`C3L3_DIFF limit=36 critical=36 mismatch=0`**，floor **28**，0 exceptions，运行前后源哈希一致，退出码 0，执行总耗时 87.59 秒。两个完整运行分别列示，交集不重复计数，故 distinct frozen threshold floor 为 **106** 而不是 83+28=111；补跑证据见 [T1b 全族 summary](tmp/l3_t1b_full/summary.json)、[原始日志](tmp/l3_t1b_full/summary.log)、[命令与退出码](tmp/l3_t1b_full/execution.json)。此范围比 L4 的 formal 60 更宽，但不含上述 thickness25；两数不可直接相加解释为唯一查询数。
- floor 无逐例豁免；C++ 不可将 Python 已认证字段退为 null。普通比较与能力下限分开：单侧证据允许由独立核验接受，但冻结语料还必须通过 floor。
- 入口检查发现 C3-L3 当前基线已经具有单侧阈值证据的**对称**接受逻辑与双向用例，因此“此前一定只接受 C++ 一侧”是工单前提订正，不应把原有逻辑写成本单新修复。此次实质新增是 frozen proof floor 及其负门。

## 6. 其余已证事实与未完成边界

- [公开 ABI 元门](tmp/public_meta_final.json) 原始末行 `C3L4_META cases=26 channels=86 mismatch=0`，包含后来新增的两条 θ 链式查询。四个 G1/G5 基例覆盖精确旋转、大平移、单位缩放、非对称 reference/anchor；G1 使用可无损输入的有理旋转，G5 因轴向 DOF mask 仅用精确四分之一转。不能声称 G5 已支持任意斜约束旋转，亦不是全部 T1b 的元门。
- [harness 定向测试历史日志](tmp/superseded_harness_trials/harness_tests_final.log) 原始末行 `87 passed in 9.00s`，包含 L3/L4 checker 测试。这些有意篡改输入/证书的 checker 负门不等于向生产源内部注入的六类变异；P1 生产变异应引用专门的 [构建/执行证据](checks/mutations.json.gz)，不由 checker 负门代证。
- [consumer 隔离证据](consumer_isolation.json) 原始末行 `EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0`；使用发布 DLL、标准库 ctypes、Python `-I -S`，最小十文件字节副本无 src/差分 harness/pybind/姊妹代码。执行者仍为本工单 Codex，**没有真实人工 TIA 使用者身份与复跑确认**；最小字节副本也不是所有者安排的 Git 新树。
- [ABI 证据](release_abi.json) 为 31 exports、28 结构、能力 mask 581501、0 findings。这证明当前布局/导出技术基线，不替代 32 项标签合同、人工作业或独立对抗退出条件。初审发现的字段类型冻结范围不足现已加强：逐字段规范 C 类型保留 const、指针层级与数组维度，同大小/同 offset 的指针类型替换与 const 丢失负门已加入；[补门证据](abi_field_types_checks.json) 记录 `26 passed in 0.12s` 及导出门继续 PASS。C 头、DLL 和 consumer 输入哈希均未改变，详见 [ABI 范围复核追加说明](abi_scope_review.md)。
- L4 diff 内的 Python formal 计时是冻结源时代时间；C++ 是预建接触后的 primal 与多通道 ABI 调用时间，不能当同机冷性能对照。P2 应引用根代理另写的独立冷进程计时工具/证据，且仅报告不设性能门。

### 对 12–22 人日目标的风险结论

有限用例通过不等于完整工单退出。除已公开的 32 项 ties 外，必须在最终报告显式保留：θ 现有两例局部链式门与 formal 原有 t 语料的区别；G2/3/4 幅值/波长仅传播而未有认证斜率；32 个非 binary64 窄带样本未执行；稳定基与非零 dc 不在正式 402 条公共几何语料内；实际人工使用者、所有者新鲜树/独立对抗确认未发生。前四项有的属于既有输入域/裁判能力边界而非新缺陷，但不写清会造成隐性扩大交付范围。不得为满足工期把它们静默改称已完成。

本报告结论：**严格 L4 保持 RED；只能支撑据实 PARTIAL，不能支撑 C3L4_DONE。**
