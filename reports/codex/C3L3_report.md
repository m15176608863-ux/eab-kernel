# WO-C3L3：profile1 刚体极限分析与临界参数 C++ 移植报告（验收返修）

## 1. 结论、范围与复核状态

本单 P0/P1 实现与 P2 实测已交付。本轮完成 MAJOR-1 门缺口修补及 MINOR-1/2 比较口径、文档订正；**不改生产求解代码，不削弱 C++ 的阈值证明**。完整构建、扩大差分和 Python 收尾快/全档见第 7 节。

- 本单原始基点为 `1b6b4f32ff3c5716f8e3a24ad73dd3cf6081f39c`；本轮入场为干净 `eab2-c3l3 @ c8718bb0850328defd8f0cc16fb4f3a09e922975`，同一工作树 `D:/eab-wt/cx-c0`。本代理未作 commit/push/reset/checkout/stash/worktree/branch 等 Git 写操作。
- Claude 告知：`c8718bb` 新鲜工作树复现构建、原五族差分 0 失配及 Python 全档 15056；外部静力路 0 缺陷、可收口，临界参数路因 MAJOR-1 未通过。该事实及问题全文见[原始验收报告副本](C3L3_repair_evidence/input/C3L3_acceptance.md)，不是本代理重复执行或替外部验收签署。
- 本轮已有具名回归、7 项内部变异、真实变异 DLL 假证拒绝及完整收尾证据；**仍待 Claude 对修复后临界参数路复验确认**。作者团队内部复查不冒充非作者对抗验收；本次新鲜字节副本也不冒充新的 Git 工作树。
- 设计依据 [eab2_design.md](../../docs/eab2_design.md) SHA-256 仍为 `6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`。返修只动测试、差分工具/测试输入及报告证据；`eab2/src`、`src/eab`、设计及静态准入策略均与 `c8718bb` 一致。
- profile1 是刚体、小变形、无限抗压、无黏聚、恒定 μ、关联流动模型；相对非关联库仑摩擦，它是不安全侧的承载力上界模型，不作工程安全承载力或姊妹轨迹等价宣称。
- 回退锚为 `c8718bb` 及[原字节归档映射](C3L3_repair_evidence/previous_archive.json)，不得覆盖所有者后续改动。未安装/下载、未写姊妹工作树、未结束非本代理启动的进程；仅向获准 `D:/eab-evidence` 追加本单归档。[本轮交付索引](C3L3_repair_evidence/deliverables.md)与[入场合同](C3L3_repair_evidence/intake.json)列明边界。

## 2. P0 装配与求解合同

实现：[statics.hpp](../../eab2/src/statics.hpp)、[statics.cpp](../../eab2/src/statics.cpp)；详细逐条映射见[静力合同自查](C3L3_evidence/statics_contract_review.md)。

标准形为 `max α`，`A=[G,projected_live]`、`b=-projected_dead`、`x≥0`，最后一个变量为 α。`eab2::statics` 仅装配及解释结果，求解一律调用现有 `eab2::opt::maximize`，并再次在原始精确模型核证。

| 工单合同 | 实现与具名门 |
|---|---|
| 保留接触点/段端点上 `g±=N±μT`，不归一化，N 指向受力体 a；a 受 +g、b 受 −g | `build_limit_problem2`；`test_statics.cpp::matrix_and_certificates` 独立核列、符号、未归一化法向 |
| 可动体 x/y/力矩三行；端板只取自由 DOF | `project` 先将 `M_o=(p−o)×g` 精确变到 `M_anchor=M_o−(anchor−o)×g`，再按 mask 取行；`g5_closed_form_and_masks` |
| 冻结参考点与物理锚点分开；恒/活荷载也作同样投影 | `build_limit_problem2`；换参考点时同步变换力矩，端板反例和参考点重参数化门守护 |
| 未解析接触集拒绝静力装配 | `limit_load_ideal_exact_2d` 保留 `MECHANICAL_UNRESOLVED`，无 problem/容量；完整性未知为 UNPROVED，非零容量猜测被拒绝 |
| 只有真 VV 的实际运动学冗余已证才不计入力 | 只消费 L1 `constraints`，保留 `true_vv_excluded_from_statics` 条件；不把全部原始 VV 来源再造力列 |
| 三态与原始证书 | `matrix_and_certificates` 及独立 `tools/eab2_c3l3_diff.py::verify_limit` |

证书按下列数学定义核验，而不是按求解器返回的坐标逐字比较：

- OPTIMAL：`x≥0, Ax=b, Aᵀy≥c, cᵀx=bᵀy=exact_value`。附 `mechanism=exact_y`；其接触列非负、活载列至少为 1，故驱动 ≥1，不能误用 −y。
- INFEASIBLE：`Aᵀf≤0, bᵀf=1` 的精确 Farkas 分离证书。
- UNBOUNDED：`x0≥0, Ax0=b` **以及** `r≥0, Ar=0, r_α=1`。不返回伪有限容量，不把它解释成几何锁定。可选自应力附件未实现。

**速度坐标约定（静力验收注记）**：不仅端板，所有自由体的三条平衡行也统一采用移到 `dof_anchor` 的力矩；`exact_y` / `mechanism` 是该锚点处的旋量，而非默认参考点 o 处的旋量。对全自由体这是保持功率配对的坐标变换，不改变可行性或承载力；端板再按 mask 取放开分量。C3-L4 读取 y 时必须采用相同锚点约定，并对约束、荷载及其导数作一致变换，不能把 y 的平移分量直接当作 o 处速度。具名门为 `matrix_and_certificates`、`rigid_units_and_anchor_translation` 及差分的原始几何独立重建；[详细合同说明](C3L3_repair_evidence/thickness_contract.md)区分参考点与物理支承。

**力矩微分范围**：本单 μ 查询中几何冻结，`dp=do=0`，精确仿射列满足 `dg±/dμ=±T`、`dM/dμ=(p−o)×(±T)`；上述式先在 o 处构造，再同步移至锚点（锚点处为 `(p−anchor)×(±T)`）；critical 从精确 A(0)、A(1) 构造该系数，不用浮点差商。任意几何种子的 `dp×g+(p−o)×dg`、完整 dA/db/dc 及 `evaluate_sensitivity2` 属设计 §8.2 的 C3-L4，本单没有交付该 API，不能将 L3 写成完整敏感性实现。

## 3. μ 临界参数与 ABI

实现：[critical.hpp](../../eab2/src/critical.hpp)、[critical.cpp](../../eab2/src/critical.cpp)；完整限制和具名门见[临界参数合同自查](C3L3_evidence/critical_contract_review.md)。

`μ_crit=inf{μ∈[0,μ_max]:UNBOUNDED}`，参数域按连续实数解释。只对 μ 二分；每次输入/输出端点必须 binary64 可精确表示，JSON 同时保留规范有理数与位模式，并核二者完全一致。精确中点不可表示时在 binary64 网格选严格内点；无内点时保留有效双端证书，报告 `input_resolution_limit`。

- 零点已无界：`lo=hi=0, attained=true`，附零点无界证书，不伪造下端机构。
- 上限仍有界：`hi=null, reason=bounded_on_domain`，附上限机构，不声称域外永久有界；不可行域保留 Farkas 和真实状态。
- 普通括号：两端证书核原始 LP；没有阈值证明时 `exact_threshold/attained=null`。
- 临界基：Q[μ] Bareiss 行列式/Cramer 分子；零/极点与一侧符号用精确 Sturm 核查。闭阈需阈值处无界及下侧有界延拓；开阈需阈值处有界、零恒载可行点和上侧归一化射线延拓。候选失败则保留括号，不猜根。
- `bisection_termination` 与 `threshold_proof_reason` 分字段；证明开/闭后也不抹掉迭代/分辨率退出原因。完整代数根对象后置；八个既有无理案例只交有证括号与多项式。

具名 C++ 门：`binary_grid`、`polynomial_guards`、`threshold_contracts`、`invariant_thresholds`、`unavailable_contracts`、`private_integer_budget`。覆盖次正规/正规边界、最大有限数、相邻端点、非 binary64 阈值、开闭/零阈/无证分支、内部根与极点、整数预算退出及恢复。

ABI 在[公共头](../../eab2/include/eab2/c_api.h)与[合同](../../eab2/ABI_CONTRACT.md)增加 `eab2_solve_limit2`、`eab2_critical_parameter`、`eab2_get_c3l3_abi_info`；既有结构不扩写，新增能力位 16384/32768。荷载按冻结体顺序提供 dead/live 三分量 binary64 bits，力矩关于冻结参考点。正式 DLL、测试 DLL、静态库均有 L3 入口；通用 LP 测试入口没有升级成生产 LP2。

ABI 门 `test_c3l3_abi.cpp::contract/unresolved/resource_limit` 及纯 C DLL/静态消费检查结构尺寸、精确 stride、空指针、数组溢出、失效/异属句柄、FP 环境、结果释放、资源失败后复用及输出原子性。不支持的参数直接返回 UNSUPPORTED，整个输出原样，**不发布数学 JSON**。`max_steps=0` 合法，超过 4096 返回 RESOURCE_LIMIT。

预算仍有明确边界：整数位长 scope 贯穿 critical 多项式证明，opt 每次有主元预算；LP/多项式每步算术并非都记入 GeometryWorkScope，`max_work_units` 不是统一 L3 运算次数或墙钟上限。

## 4. 独立差分、回归与闭式

权威结果为唯一一份 [differential.json.gz](C3L3_repair_evidence/differential.json.gz)，[原始日志 gzip](C3L3_repair_evidence/differential.log.gz)及[压缩/原始 SHA 核对](C3L3_repair_evidence/differential_archive.json)随附。原 `c8718bb` 差分已按 H1 外归档，不能与本次计数混用。工具独立解析语料与 DLL JSON；formal 使用 `formal_20261019_02/binary64` 冻结输入/期望，新增族调用未改的 Python 裁判。原五层 formal / t1b / regression / metamorphic / implication 全部保留，再加 wide、thickness。

| 族 | limit | critical |
|---|---:|---:|
| formal/TIA-G1 | 27 | 27 |
| formal/TIA-G5 | 27 | 27 |
| formal/named_regression | 7 | 7 |
| formal/TIA-G2 | 15 | 15 |
| formal/TIA-G3 | 15 | 15 |
| formal/TIA-G4 | 15 | 15 |
| formal/contract_coverage | 8 | 8 |
| t1b | 36 | 36 |
| closed_g5 | 6 | 0 |
| plate | 2 | 0 |
| closed_g1 | 0 | 9 |
| metamorphic | 19 | 12 |
| implication1 | 6 | 0 |
| implication2 | 24 | 0 |
| implication3 | 6 | 0 |
| converse | 4 | 0 |
| wide_g1 | 0 | 2310 |
| wide_incline | 0 | 16 |
| wide_quadratic | 0 | 6 |
| thickness | 75 | 25 |
| **总计** | **292** | **2528** |

formal 的 114 个 critical 项中仍含 1 个不支持参数的调用错误合同（不发布数学 JSON）；不把总计误称为同样多的已证阈值。原始末行：

```text
C3L3_DIFF limit=292 critical=2528 mismatch=0
```

`source_pre_post_equal=true`。状态、精确承载值、端点、退出原因、有效条件等保持精确比较。非唯一 x/y/机构、Farkas、可行点/射线由**原始顶点边、荷载 bits、参考点、锚点**重建 A/b/c 后按第 2 节核验，不信任 C++ 导出的法向/矩阵。临界基不硬等系数/基序：核有理多项式恒等式、精确一侧 Sturm、列表存在/空非空、分支角色与采样端点。

**attained / exact_threshold 的精确比较口径订正**：旧语料上的逐字段相等不能推广到宽括号及 Farkas 下端。双方阈值都非空时仍要求精确值、开闭相等；双方都空时保持 null 合同；仅一方非空时，先对双方执行独立 `verify_critical`，非空侧必须通过原始几何 LP、阈值证书及上下侧延续核验，才允许记录证明可用性订正。只规范化 `exact_threshold/attained/threshold_certificate/threshold_proof_reason` 四个相互派生字段，不放宽端点、状态、退出原因、有效条件或多项式有无。阈值证书的元合同及状态专属互斥附件也先检查，不能借整块规范化吞掉错误字段。

本轮 73 项证明可用性差异均独立核证通过，外部验收所报 **20 项逐一复现并处置**，详见[逐例台账](C3L3_repair_evidence/acceptance_enrichment_disposition.md)与[来源输入映射](C3L3_repair_evidence/acceptance_enrichment_inputs.json)。C++ 选出不同合法改进射线/基而取得更强证明，不是改错数；不为对齐 Python 而削弱生产证明。查询次数不同 28 项在权威结果保留双侧原值，不当数学真值比较。

[校验器具名门](../../tests/test_eab2_c3l3_harness.py)覆盖错误矩阵/原始切向、假证书、多项式恒等式、缺上下侧延续、双非空不一致、双向合法证明增益与非法元字段/附件；见[本轮定向日志](C3L3_repair_evidence/checker_tests.log)。生产内部变异另见第 6 节，不能用产出后手工改 JSON 代替内部缺陷注入。

### 宽括号与两个 MAJOR-1 回归

G1 三取向 × 11 组 `(t,h)` × `max_steps=0..6` × `mu_max={1/8,1/4,3/8,1/2,3/4,1,3/2,2,3,4}`，共 2310 项；另有斜面 Farkas 下端 16 项（真实开阈 0、1/13，各 8 个步数）及二次无理根括号 6 项，共 2332 critical。Farkas 例保留真实 INFEASIBLE 下端及 null 阈值，不强签开闭；根括号另以 `μ²+2μ−1` 核两端异号。

| `threshold_contracts` 具名回归 | `(t,h,mu_max,max_steps)` | 保留括号 | 真实闭阈 | 导出阈值/attained |
|---|---|---|---|---|
| `koureas_wide_four_steps_requires_below` | `(3/32,1/16,3/4,4)` | `[3/64,3/32]` | `2039/32768` | null/null |
| `koureas_wide_one_step_requires_below` | `(3/8,1/4,3/8,1)` | `[3/16,3/8]` | `119/512` | null/null |

### 回归 (d)、G5 与端板

G5 仅在规定的对称等高、轴向滑动端板 `[1,0,0]`、死荷载 P 和中块单位活载条件下核 `F=min(2μP,4Ph/(L−b))`。补点覆盖 n=3/5/7 和非单位 h/P；不能把此式推广到改掩码的模型。

| 场景 | 精确结果 |
|---|---:|
| 回归 (d)，N=L=3、h=P=b=1、μ=0 | 0 |
| 同上，μ=1/4 | 1/2 |
| μ=2，n=3/5/7，h=P=b=1 | 2 / 1 / 2/3 |
| μ=3/8，n=3，h=3/2，P=5/4 | 15/16 |
| μ=2，n=3，h=P=b=1，面中点锚定，放开竖向 `[1,1,0]` | 2/3 |
| 同上，放开转动 `[1,0,1]` | 4/3 |

### G1 与 T1b

G1 生成族块宽 ℓ=2，ρ=h/2，t≥0：t=0 时三取向均零开阈；t>0 时 `koureas=max(0,t−ρ(1+t²))` 为闭阈，`unreversed=t` 为开阈，`reverse_i1=t` 为闭阈。每取向核 `(t,h)=(0,1),(3/32,1/16),(1/4,1)`，共 9 项，并仍检查原始证书。

T1b 全 36 例均重跑 limit/critical：26 个有理闭阈、2 个有理开阈、8 个既有无理案例括号。其中必需的 zero-based index 与结果如下：

| index | exact_threshold | attained |
|---:|---:|---|
| 13 | 131009/2097408 | true |
| 16 | 98283/2097664 | true |
| 30 | 326839/6291456 | true |
| 8 | 1/16 | false |
| 17 | 7/128 | false |

无理案例 1/2/5/10/11/14/19/22 保留 `exact_threshold=null, attained=null`，检查两端证书、宽度 ≤2^-40 和临界基；本次没有重做无理性的不可约性证明。全部编号与核验方法见[差分合同自查](C3L3_evidence/harness_contract_review.md)。

### T1b 厚度样本的 ABI 输入域

上述 36 个形貌模型与厚度扫描不是同一语料。T1b 厚度的 39 个样点多数含非二进有理原始几何：32 个不在当前 binary64 ABI 的无损输入域内，不能舍入后冒充原模型。本次差分只纳入其中 **7 个完整模型精确可表示的样点及 18 个厚块对照**，共 25 个来源条目、19 个唯一模型（6 个重复来源如实保留）；每条 3 个 limit 和 1 个 critical，共 75/25 查询。外部静力路原已报告这 7+18 项通过，本轮把它们变为持久可重跑的输入族，不追认成旧原作者当时的覆盖。

[生成器](../../tools/eab2_c3l3_thickness.py)只读取[测试数据摘要](../../tests/data/eab2_c3l3_thickness_summary.json)，不依赖 Temp 验收目录或外部归档；所有实际传输的原始顶点、参考点、锚点、恒/活荷载及参数都逐项核 binary64 无损。[输入域与来源合同](C3L3_repair_evidence/thickness_contract.md)列出全部选入/排除规则、7 样点及重复身份。未覆盖的 32 个精确有理模型不是算例错误，也不是本 ABI 的测试通过项。

## 5. P1 元门与有效蕴含

- C++ `rigid_units_and_anchor_translation` 在精确有理旋转、尺度 `{1/1024,1,16}`、非原点大平移下保持有限无量纲容量 `1/4`，另守端板锚点平移；`invariant_thresholds` 守开/闭 μ 阈值、参考点重参数化及小特征/大坐标。私有有理输入不冒充 ABI 可无损表达任意旋转。
- ABI harness 以种子 6033 的 Pythagorean 旋转配合独立的几何/荷载尺度消去奇数分母，逐项断言 binary64 无损。12 个 G1 变换采用 `(3t/5,4t/5)`，**|translation| 精确为 `{0,1000,100000}`**，有由实际变换后顶点反推位移的门；另有 4 个端板旋转和 3 个参考点变换。一般旋转仅用于全自由体；90° 端板旋转同步交换 x/y mask，参考点变化同步变换荷载力矩。不是单独挪动真实支承后声称不变。
- 每个变换均核原始几何重建列、来源/行列标签及证书；保持顶点/体 ID 的变换采用对应特征标签。有限元门不是全输入域证明。
- `valid_implications_and_reverse_counterexample` 与 ABI implication 族核三条：① 单体零锥的 `Kᵀλ=±e_k, λ≥0` 证书配合 `(g−+g+)/2=N`，独立构造任意 wrench 的可行点和射线；测试非对称恒/活载及 μ=0/1/4/2（ABI 另取5/2）。② μ=0、零恒载的 free/plane/seam/cage 几何，六活载方向全无界当且仅当零锥。③ 活载仅在体 i，多体无界时固定其余体重核单体无界；G1 三取向均覆盖。
- 反向门：G5 中块单体无界，但多体 μ=1/4 的容量是 1/2，且中块一阶锥非零；拒绝“单体无界⇒多体无界”和“无界⇒几何锁定”。上述一般锥代数理由与有限实现测试分开，不以采样冒充所有几何证明。

## 6. 有牙自检与 P2 实测

正式源码内部 mutation 先执行未改基线，再编译隔离变体；指定语义断言必须报红，不能以编译失败、源码哈希或偶然解序代替。

- [静力 mutation](C3L3_evidence/statics_mutations.json)：忽略物理锚点、摩擦两列同号、作用反作用同号，共 3 项均被端板/G5 语义门拒绝。
- [本轮 critical mutation](C3L3_repair_evidence/critical_mutations.json)：保留原 5 项，再加“闭阈缺下侧延续”和“开阈缺上侧改进射线”共 7 项；正常基线先绿，变异必须触发具名语义断言。
- 闭阈变异由 `koureas_wide_four_steps_requires_below` 杀死；开阈变异由 `unreversed_open_requires_above` 杀死。第二个 koureas 宽括号回归另保留在正常门及差分中。
- 另外构建两个隔离真实变异 DLL，未经改写的原生导出分别假称 `3/32,true` 与 `0,false`；新比较器均在独立延续核验阶段拒绝，证明增益处置列表为空。[拒绝证据](C3L3_repair_evidence/continuation_dll_red_gates.json)记录输出、异常语义与 DLL/source SHA；不是在产出后追加假数据。

```text
C3L3_STATICS_MUTATIONS_OK baseline=1 rejected=3 semantic_failures=3
C3L3_CRITICAL_MUTATIONS_OK caught=7 escaped=0
C3L3_CONTINUATION_DLL_RED_GATES_OK rejected=2 admitted=0
```

第一行是 `c8718bb` 已验收静力路的历史证据；后两行是本轮实际末行。作者团队补充复查曾发现新证明增益比较可能掩盖阈值证书元字段，已在本轮正式收尾前补门；[内部复查记录](C3L3_repair_evidence/internal_checker_review.md)不冒充 Claude 非作者复验。

P2 沿用下述原始实测，不为本轮测试/文档修复重复跑规模；生产求解源未改，时长仍只代表旧采样时刻。

规模工具[可复跑脚本](../../tools/eab2_c3l3_scale.py)在新进程中由原几何建模：20 个独立可动体及互补锯齿固定支承、每接触界面 18 段，完整显式体对。实际 **60 行、1441 列、720 条保留约束**；C++ 与 Python 原始 A/b/c SHA-256 同为 `d558133ac08762519a48d58774841720696b9e2181fd576ba0c5dd183b188389`，均 UNBOUNDED 且独立核验 x0/r。不是手工塞入一张规模矩阵。

| 实现 | 冷接触装配（s） | L3 求解/导出（s） | 冷进程总时长（s） |
|---|---:|---:|---:|
| cpp | 12.404889 | 2.003203 | 14.987273 |
| python | 11.681963 | 1.939051 | 14.273452 |

[完整规模记录](C3L3_evidence/scale.json)。每端仅 1 次本机冷进程样本，取样期间未运行 H1；不是性能门、速度提升承诺或生产基准。C++ 求解计时含 JSON 导出，Python 不含，不能将比值包装成公平纯内核速度。formal 中冻结的历史 Python 时间也不用于此对照。

## 7. 全部验证原始末行与复跑

本轮[顺序运行记录](C3L3_repair_evidence/verification_runs.json)给出完整命令、返回码、耗时及原日志 SHA；[进度闭合记录](C3L3_repair_evidence/progress.json)为 complete。完整构建从新建字节副本开始，非增量复用；H1 收尾也为字节导出，均不是 Git 新树。被测代码从构建到全档期间冻结，最后再核当前源码字节一致。

### 本轮完整构建与 C++ 单测

```text
100% tests passed, 0 tests failed out of 12
Total Test time (real) =   4.16 sec
C3L3_STATICS_OK checks=3916
C3L3_CRITICAL_OK checks=346
EAB2_C3L3_ABI checks=128 failed=0
```

完整原始构建日志及编译命令在[本轮归档映射](C3L3_repair_evidence/archive_manifest.json)；[交付审计](C3L3_repair_evidence/delivery_audit.json)核导出隔离、第三方清单与 C0 编译合同。

### 原工单开工全档（4 分片，历史基线）

本轮是同一工单的验收续修，不重跑开工全档；原开工基线确在实现前执行，保留原样，与 Claude 告知的 `c8718bb` 新鲜全档 15056 分开标注。

```text
3759 passed in 818.19s (0:13:38)
3759 passed in 1090.41s (0:18:10)
3759 passed in 993.06s (0:16:33)
3758 passed in 1550.29s (0:25:50)
exact construction AST gate: 0 violation(s)
```

### 本轮收尾快档

[快档摘要](C3L3_repair_evidence/final_fast/summary.json)：GREEN，收集/执行 8996 项。

```text
8996 passed in 320.26s (0:05:20)
```

### 本轮收尾全档（4 分片）

[全档摘要](C3L3_repair_evidence/final_full/summary.json)：GREEN，收集/执行 15080 项。

```text
3770 passed in 1447.72s (0:24:07)
3770 passed in 770.28s (0:12:50)
3770 passed in 1084.42s (0:18:04)
3770 passed in 986.76s (0:16:26)
exact construction AST gate: 0 violation(s)
```

执行节点多重集合等于收集节点，0 skip、0 failed，逐模块实际执行核验齐备；纯度、大文件门均在快/全档内，静态准入无新增。运行未中断，不拼接日志；快档若超过日常约 5 分钟成本目标，按上述实际时长报告，不为凑数重跑。

### 本轮定向与差分

```text
45 passed in 4.38s
C3L3_CHECKER_AST diagnostics=0
EAB2_DELIVERY_AUDIT status=PASS findings=0 vendor_files=71 compiler_commands=23
C3L3_DIFF limit=292 critical=2528 mismatch=0
C3L3_REPAIR_FINAL_SEQUENCE_OK
```

复跑示例（名称必须新建，先把 TEMP/TMP 指到被忽略的 tmp 路径）：

```powershell
$env:TEMP = "$PWD/reports/codex/C3L3_repair_evidence/tmp"
$env:TMP = $env:TEMP
.\eab2\build_eab2.bat
python -X utf8 tools/eab2_c3l3_diff.py --dll "$PWD/eab2/build/eab2.dll" --family all --output "$env:TEMP/recheck_differential.json"
python -X utf8 tools/h1_run_gates.py --name recheck_fast --evidence-root reports/codex/C3L3_repair_evidence
python -X utf8 tools/h1_run_gates.py --name recheck_full --runslow --evidence-root reports/codex/C3L3_repair_evidence
```

H1 自带 `-p no:cacheprovider`、显式 basetemp 及忽略路径 TEMP/TMP；独立 pytest 同样必须采用。变异使用新的 `eab2/build/tmp/<name>`，critical 变异工具要求 `--root`。C0 编译合同保持 MSVC 19.44.35227.0、工具集 14.44.35207、C++20、/MD、/fp:precise、x64 SSE2、Boost 1.86.0 et_off。

## 8. 与设计的差异 / 比较口径、证据卫生与遗留

1. 未发现须修改设计的冲突；本轮没有修改设计、Python 数学合同或生产 C++。MAJOR-1 是门覆盖缺口，不是现有生产错数；保留下侧/上侧延续条件，新增宽括号与内部变异守护。
2. **MINOR-1 订正**：宽括号的非唯一 LP 基可导致两端实现证明强度不同；不是每一项 attained 都可当唯一字段。双方非空必须相等，仅单侧非空须通过独立数学与证书元合同核验，且逐项登记。20 个验收实例均在本轮重现，处置见第 4 节台账；不削弱 C++ 证明，也不豁免其他字段。Farkas 下端例保留 null 阈值。
3. **MINOR-2/静力注记**：第 4 节明确比较域，第 6 节补齐两个延续变异；第 2 节明确自由体与端板均使用锚点力矩及 y/机构锚点旋量；T1b 厚度只覆盖 binary64 精确 7 样点+18 对照，不能声称覆盖 32 个域外模型。
4. 原阶段范围仍然成立：ABI 不支持参数按调用失败返回、不发布 JSON；完整代数根对象、无理阈值 attained、任意参数敏感性/L4、可选自应力及稳定发布 ABI 未交付或未冻结。有理候选认证保守，不保证发现所有有理阈值。资源预算也不是全 L3 墙钟保证；P2 规模是报告而非性能门。
5. 本轮仅保留一个权威差分 gzip；旧差分与重复试运行、节点、原始日志、变异构建材料按 H1 追加外归档，逐文件原始/压缩 SHA 及读回核验见[旧证据映射](C3L3_repair_evidence/previous_archive.json)、[本轮映射](C3L3_repair_evidence/archive_manifest.json)和[总归档索引](../EVIDENCE_ARCHIVE.md)。冻结历史证据不重钉当前源码；外归档是本地保存，不是远端备份。
6. [卫生账](C3L3_repair_evidence/hygiene.json)按相对 `1b6b4f3` 的整体拟交付字节计算，并另列本轮相对 `c8718bb` 增量；门为净增 ≤2,000,000 B、修改/新增单文件 ≤1,000,000 B。编译产物不入库；UTF-8 无 BOM、换行一致、批处理 ASCII，`git diff --check` 通过。[完整性审计](C3L3_repair_evidence/delivery_integrity.json)核源、归档、链接和受测字节，最终只回填报告/归档索引及证据元数据，不改被测代码。
7. 报告回填检测到两份定向检查日志采用 PowerShell 默认 UTF-16LE；先追加归档原字节，再转为 UTF-8 无 BOM/LF，逐行内容与原始末行完全不变，未重跑或改写测试结果。[编码订正记录](C3L3_repair_evidence/encoding_corrections.json)保留原始/现行 SHA。

**仍需所有者行动**：Claude 对修复后临界参数路复验确认 MAJOR-1 关闭。`c8718bb` 的所有者新鲜树复现和静力路验收已据来函记录；本轮未自行创建 Git 树，也没有把作者自查当成修复后的非作者复验。

C3L3_PARTIAL：MAJOR-1 与 MINOR-1/2 返修及完整收尾验证已交付；待 Claude 对修复后临界参数路复验确认
