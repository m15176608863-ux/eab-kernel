# eab2 发布 ABI v1 合同（C0 / C1 / C3-L1 / C3-L3 / C3-L4）

前面的 C0/C1/C3-L1/C3-L3 章节记录各族进入时的历史工作接口；本文件末尾是 C3-L4 经独立 ctypes 使用者脚本实际复跑后的发布 ABI v1 冻结表。公共 C 头只含固定宽度整数、长度与指针；无 C++ bool、STL、Boost、异常或 enum 布局。全部入口捕获 C++ 异常。调用方仍须提供真实有效且足够大的、互不重叠的描述符和缓冲区；本单不是恶意地址/宿主接缝加固。

**冻结范围与验收口径（2026-10-23 Claude 澄清）**：这里的 `FROZEN` 表示已实现 C ABI v1 的技术布局、函数与能力基线固定，不单独代替 WO-C3L4/C3 的全部收尾验证。按 Claude 本次裁定，现有独立标准库 ctypes consumer 已满足设计 §8.5 的使用者全链要求；Claude 在验收环节亲自复跑，不再另列“待安排真实人工使用者”作为本单未完成项。上一轮 32 项 `tied_labels` 差异是旧严格集合比较口径的历史记录，后续按本次裁定及差异台账独立核验，不把旧 RED 数量作为永久 ABI 冻结条件。最新构建、差分与验收状态以主报告及本次 clarification 证据为准，不能仅由代表例 0 失配或 PE 门绿推定整单完成。

## 正式导出与能力

`eab2_get_abi_info`、`eab2_self_test`、`eab2_context_create`、`eab2_context_destroy`、`eab2_context_get_error`。ABI version=1，`struct_size` 必须精确匹配；版本不匹配返回 UNSUPPORTED。构建身份包含工具链、ISA 与后端，由构建系统生成。`get_abi_info` 总是报告已实现能力；`requested_capabilities` 的未支持位完整返回 `unsupported_capabilities` 并返回 UNSUPPORTED。C1 正式 DLL 具有 CONTEXT/BODY2/ENTRANCE2/QUERY2/EXPORT_EXACT/LOCAL2/LIMITS2 能力，没有 rho/SE2/LP2 或数值发布入口；不提供占位时间、距离或承载力。

`eab2_numeric_batch` 只在 `EAB2_ENABLE_TEST_API` 测试构建导出，测试 DLL 额外报告 TEST_NUMERIC 能力；正式 DLL 没有该导出。单元测试见 `tests/test_abi.cpp`，生产 C 头/能力检查见 `tests/test_c_header.c`。

## 状态表

| call_status | 数字 | 含义 |
|---|---:|---|
| OK | 0 | 调用成功，仍须看逐项数学/显示状态 |
| INVALID_INPUT | 1 | 输入、尺寸、stride、容量或描述符非法 |
| INVALID_HANDLE | 2 | 错误 owner/type/generation、失效或过期句柄 |
| UNSUPPORTED | 3 | 未实现能力/操作/版本，不是数学 false |
| CONSTRUCTION_RANGE | 4 | 精确构造不满足显示范围合同 |
| RESOURCE_LIMIT | 5 | 确定性限额或分配失败，无数学结论 |
| FP_CONTRACT | 6 | 当前调用线程浮点合同不满足 |
| INTERNAL_ERROR | 7 | 未预期异常/不变量破坏，结果不可用 |
| CANCELLED | 8 | 预留外部取消类别，不与资源限额混淆 |

`mathematical_status`: NOT_COMPUTED=0、VALUE=1、UNPROVED=2、NO_EVENT=3、OVERLAP=4、INFEASIBLE=5、UNBOUNDED=6。C0 只产生 NOT_COMPUTED/VALUE，其他类别冻结表示但不是已实现能力；不得将 UNPROVED 转成 false。`display_status`: NOT_AVAILABLE=0、VALID=1、RANGE=2、UNDERFLOW_ZERO=3。显式 `allow_underflow` 允许精确非零舍入为 ±0 时，数学 VALUE 不变，显示单列 UNDERFLOW_ZERO；精确零仍为 VALID。向量任意分量触发即标记该项；bits 仍返回正确有符号零。Python construction 数学合同不变，`tools/eab2_diff.py::expected` 用独立 Python 严格/允许下溢两次调用判定该显示细分。逐项失败 `bits_count=0`，**不写 bits 缓冲区**，不能读取其旧值当结果。RANGE 是显示失败标记，不伪造可导出的精确证书；C0 测试桥不导出该证书。

## 生命周期与错误

context 是 `{owner,id,generation,type,reserved}` 的 32 字节 token，不是可供调用者释放的指针。context token 的 owner 必须等于 id；每次查表还核类型、世代与 reserved。context 与子对象槽位复用；每次分配使用库级单调递增 generation（溢出 RESOURCE_LIMIT），使同 id 的旧 token 仍无效。子对象 owner 为 context id；跨 context、错类型、旧 generation 均拒收。释放 context 同时销毁子对象。context 槽位元数据保留，全部几何/结果载荷释放。`test_abi.cpp::main/geometry2_matrix` 实际复用槽位后再尝试旧句柄，不仅检查不同 id。失败创建首先将整个输出清零；库内部创建/销毁唯一所有权对象，不跨 CRT free。全局锁仅解析/修改注册表并固定 shared ownership；随后释放全局锁，按 context mutex 串行计算。destroy 标记旧 state 失效再回收槽位，generation 原子单调推进；不同 context 可以并行。错误保存在各 context，不使用全局 last_error。

错误由 context 持有 code/field/index 和消息，失败批次记录错误；正常批次将错误清空；逐项失败记录第一个失败的下标。`get_error` 不改变既有错误。两阶段获取消息：NULL/0 查询所需容量（含 NUL），再由调用方分配，库只复制；不足容量不写消息。消息长度上限 511 字节，field 上限 47 字节；错误 code/index 不截断。context 销毁后错误也失效。

## 测试批协议

输入为显式 UTF-8/ASCII 文本片段 `data/length`，无隐式终止符扫描；binary64 为最高位在前、小写恰 16 位 hex，−0=`8000000000000000`，NaN/Inf 拒收；有理串约分 n/d、d>0、零 0/1。输出 `uint64_t` 是位模式整数；序列化时格式化为 16 位小写 hex，不按主机字节序解释文本。

所有数组 stride 必须**等于对应元素的 sizeof**；数组乘法溢出、空指针与非零长度不一致、非零 reserved、未知 flags、容量不足均拒收，不截断/补零。item_count=0 可用 NULL items，仍需合法结构和 stride。测试协议确定性上限：65536 items、每项 65536 values、每文本 1048576 bytes，超过返回 RESOURCE_LIMIT。另有工作上限：单有理文本 ≤4096 bytes；解析前估算每文本长度平方（十进制逐位乘法/约分的保守输入工作代理）；批次总 values≤65536、文本≤4194304 bytes、长度平方和≤67108864。单项有理解析超限为逐项 RESOURCE_LIMIT；结构/总预算超限为批次 RESOURCE_LIMIT，均不是数学否定。单个输出 capacity 可大于实际数量；计算后容量不足为逐项 INVALID_INPUT。

先验证全部描述符，再暂存全部计算结果，最后提交输出。结构错误/环境错误/批次分配失败：外层返回失败，输出描述符与 bits 都不改。结构正常：外层 OK，`output.item_count` 等于输入数量，每项分别返回状态；成功项复制 bits，失败项保留 bits 原存储并清 count。临时内存全部由库 RAII 释放，调用者始终拥有输入/输出缓冲区。禁止输入与输出重叠、描述符与 bits 缓冲区重叠。

测试 op 编码见 `testing.h`；数学参数形状由 `numeric.hpp` 的测试桥规定。decode 在 ctypes 只检查位回环，精确有理分子/分母由静态核心测试核验，不将位回环冒充完整解码证明。

## 浮点环境

`self_test`、创建 context、每次 numeric_batch 都核当前调用线程。首先核 MXCSR 第 7–12 位全屏蔽、FTZ/DAZ 关闭及 RN 模式，再核 binary64、ties-even、有符号零、渐进下溢和同 TU noinline 非 volatile 中间乘积的收缩探针。失败返回 FP_CONTRACT；不切换宿主控制模式。成功探针产生的 sticky flags 恢复为调用前原值，已有 flags 同样保留；该恢复不是替坏环境修复配置。调用方不得在调用期间异步修改 FP 环境。

`test_abi.cpp::environment_matrix` 实际注入 FTZ、DAZ、三种非 RN、分别解除 7–12 六个屏蔽位，验证 self_test/create/batch 都拒绝、失败输出不变，且调用前后完整 MXCSR 和 `_controlfp_s` 读值不变。默认 SSE2 无 FMA，因此有限收缩探针不是识别任意伪造构建配置的万能证明。


## C1 增量合同

`get_abi_info` 保持原 C0 结构尺寸；`eab2_get_c1_abi_info` 另外报告新增描述符尺寸。C1 版本仍为工作 ABI v1，不冒称 C3 末发布稳定 ABI。

| 族 | 工作入口 / 输出 |
|---|---|
| 环 | `eab2_body2_create/destroy`：有限 binary64 x/y 位模式，简单无洞环；保留原序 bits/顶点与边 ID；输入不变；失败 token 全零 |
| E | `eab2_entrance2_create/destroy`：复制不可变 body，因此 body 可先释放；flags=0 默认 merge/compact；NO_MERGE=1、NO_COMPACT=2、NO_CACHE=4 |
| 批查询 | `eab2_query2_batch`，以及 `eab2_membership2_batch/topology2_batch` 同义双三态入口；每点返回 call_status/mathematical_status/body_state/topology_state |
| 全局精确 | `eab2_result_export_exact`：UTF-8 JSON，有理 canonical n/d；双方规范骨架由 Python harness 计算 |
| 局部精确 | `eab2_local_origin2_exact`：0 处局部胞/切锥、精确排除证据、全部原始 VE/EV 来源；不主动构造全局 subdivision |
| 释放 | `eab2_result_destroy` 在库侧释放 exact_result.result；data 只读，byte_count 不含尾 NUL；释放 result 或 context 后失效 |
| 测试隔离 | `eab2_query2_exact_batch` 接 canonical 有理坐标；`eab2_covers2_exact` 接显式精确窗口/容差；仅 test DLL 导出，测试能力 TEST_EXACT2 |

`eab2_local_origin2_exact` 默认通过合并后的胞计算（继承 entrance flags；显式 NO_MERGE 另论）。它不能代替 `query_lock` 使用的未合并耳切积胞、逐胞证据或严格半径界；两者在原点状态相同不意味着胞分解与半径证书可互换。

两个状态都是独立的 uint32 值域：body OUTSIDE=0/CONTACT=1/OVERLAP=2；topology OUTSIDE=0/BOUNDARY=1/INTERIOR=2。合法 OVERLAP 是调用成功的数学 VALUE，不能读取 call_status 当是否重叠。输入点失败则数学 NOT_COMPUTED，两个状态均为 UINT32_MAX，避免伪造 OUTSIDE。

批查询先验证所有外层结构/尺寸/stride/容量、暂存结果再提交；结构或灾难性分配失败不改输出。合法批次外层 OK，非法数值点逐项失败，首项错误存 context。空批允许 NULL points/items。每批 ≤65536 点，body ABI ≤4096 点；几何核心另有确定性工作限额，超过 RESOURCE_LIMIT。测试有理查询每坐标 ≤4096 bytes；批次解析长度平方和 ≤67108864，耗尽后逐项 RESOURCE_LIMIT。

exact result 创建失败不改已有输出；成功创建的新 token 必须释放，不可把含活 token 的输出重复覆盖而不先释放。失败的 body/E 创建清全零 token。错误详情不依赖全局 last_error；C1 调用开始时清旧错误，逐项错误保留首错。同一 context 的调用被串行化；result / context 销毁后，返回的 data 指针失效。调用者须自行协调借用 data 的读取与销毁，串行化 API 调用不延长借用指针的生命周期。

`test_abi.cpp::geometry2_matrix` 守护尺寸、三态、部分成功、句柄槽位复用、跨 context、库释放、export 及有理测试入口；`tools/eab2_audit.py` 核查正式 DLL 无两个测试入口。所有 C1 计算入口重查当前线程 FP 合同；`body2_destroy/entrance2_destroy/result_destroy/context_get_limits2` 以及 C3 释放入口不运行 FP 自检，在坏环境下仍可清理/读配置。`test_c3l1_abi.cpp::release_bad_fp` 实际检查 FTZ/DAZ、三种非 RN、六个屏蔽位和宿主状态不变。

构建身份由 `tools/eab2_audit.py` 调实际编译器 `/Bv` 获取版本，再与 `compile_commands.json` 的实际工具路径、`/MD /O2 /std:c++20 /fp:precise` 和无 `/arch:* /GL` 比对 DLL identity。受控源码在 `exact.hpp/c_api.cpp/fp_contract.cpp` 入口拒 `__AVX__`；geometry 经 exact.hpp 同样受控。此审计证明的是编译目标而非整个 CRT/STL 的二进制 ISA 纯度。


缓存关闭 `EAB2_ENTRANCE_NO_CACHE` 不改变 merge/compact 参数：每次全局或局部 JSON 请求从同一不可变 body/flags 创建临时 Entrance，导出后释放临时全局缓存；membership/topology 本身不物化全局缓存。`geometry2_matrix` 先全局导出、再局部查询，检查局部 `global_subdivision_materialized=false`，并检查重复导出语义不变；不是用关闭 merge 冒充关闭 cache。


## C1 可配置确定性工作限额

独立 `eab2_context_limits2`（struct_size/abi_version + 三个 uint64）与 `context_get_limits2/context_configure_limits2`，不扩写 C0 context_options。先 get 实际默认：max_work_units=50000000、max_elements=2000000、max_integer_bits=65536；三项输入必须显式正整数，0 拒收而不是隐含默认。配置只在该 context 无任何活 body/E/result 时允许；对象创建后冻结其几何限额，exact export 回显实际值。

C1 入口建立共享 `GeometryWorkScope`，嵌套几何调用/同批各点共用工作预算；Body/E 及方法各自保留直接 C++ 调用的范围。`IntegerLimitScope` 在 exact 算术层前置检查乘积/平移/有理交叉乘及加减的保守位长上界，并检查 owning 结果；超限抛专用 ResourceLimit，C ABI 转 RESOURCE_LIMIT，不产生几何否定。保守上界可能拒绝一个约分或消去后本可很小的结果，这是明确的资源拒签，不是数学误判。

这些位长限额不是整进程内存/墙钟预算，也不声称已证明 Boost 私有算法所有临时 limb 分配的物理峰值；前置算术界比单纯导出后验位长检查更强，但二者不能混称。直接 C++ 数值核心无显式 scope 时保留原行为；C0 测试 ABI 的每项 evaluate 现在独立建立 context 的 `IntegerLimitScope(max_integer_bits)`，超限按逐项 RESOURCE_LIMIT 提交，其他项仍可成功。scope RAII 在异常路径恢复，测试 `test_numeric.cpp::integer_budget_contract` 与 `test_abi.cpp::numeric_compute_budget_matrix` 守护。配置与三类资源拒签门见 `test_abi.cpp::limits2_matrix`。十进制测试桥仍有独立固定协议工作预算。


## C3-L1 增量合同

`eab2_get_c3l1_abi_info` 单独返回 C3 描述符尺寸，不扩写冻结 C0/C1 布局。新增正式能力 ASSEMBLY2=512、CONTACTSET2=1024、LOCK2=2048、MOBILITY2=4096；仅测试 DLL 有 TEST_OPT=8192。LP2 仍保留给未实现的 L3 发布族，不以 test-only opt 入口冒充生产 L3。数学状态新增 MECHANICAL_UNRESOLVED=7；精确 JSON 保留更细的状态串，零/非零锥不是有限运动的 true/false。

| 族 | 工作入口 / 合同 |
|---|---|
| Assembly | `assembly2_create/destroy`；复制同 context body，非空唯一 UTF-8 ID（每个≤4096 bytes），显式 binary64 参考点和 dof_anchor，mask 的 bit0/1/2 表示 x/y/rotation 自由；FIXED_BODY 要求 mask=0 |
| 候选对 | flags COMPLETE=1 / EXPLICIT_PAIRS=2；`EAB2_ASSEMBLY_COMPLETE` 必须与 `EAB2_ASSEMBLY_EXPLICIT_PAIRS` 合用，complete 必须显式包括所有无序体对；未声明完整性不自动补证。profile 必须1；仅未知 profile 返回 UNSUPPORTED |
| ContactSet | `assemble_contact_set2` 返回独立快照 token；assembly 可先释放。`contact_set2_export_exact` 输出逐点类型/保留边界/来源/不可达证书/未解析真VV及状态；`contact_set2_destroy` 库侧释放 |
| 锁定 | `query_lock(assembly, input, result)`；input 显式 moving index 与 neighbor index 数组，每个邻体在本次查询视为固定；不据 mask 推断遗漏邻体。OVERLAP call OK + math OVERLAP、JSON status=null，不能伪造四状态 |
| 一阶 | `first_order_mobility(contacts,result)`；只用法向，固定/掩码/锚点来自不可变快照。未解析真VV返回 MECHANICAL_UNRESOLVED，不枚举模态；完整性未知返回 UNPROVED |
| 测试 LP | `opt_solve_exact`，标准型 min/max，文本顺序 row-major A、b、c；sense 0/1，显式正 max_pivots；输出精确 x/y/归一化射线和统计。只在测试 DLL，供独立 Python 差分 |

外层结构、数组乘法、精确 stride、指针、尺寸与 owner/type/generation 均检查；失败创建 token 全零，失败精确查询不改变原输出。没有借用输入内存。结果仍按 C1 result 生命周期库侧释放，不能覆盖未释放的活 result。所有计算入口核 FP；释放与 get_limits2 不核 FP。

Assembly≤1024 bodies，candidate pair/neighbor count≤context.max_elements；几何/整数限额沿 C1 scope。opt测试入口≤1024行、4096列、65536个精确数（A+b+c），单文本≤4096 bytes、长度平方和≤67108864；主元预算含辅助LP，耗尽返回 RESOURCE_LIMIT 而非数学 UNPROVED。位长统计为存储输入/基逆/证书分量高水位，不声称所有算术临时峰值或进程内存上界。默认无浮点候选加速，只有全有理冷启动/候选精确重建。**LP 运算使用独立主元预算与整数位长限制，不消费 GeometryWorkScope 的 max_work_units；不能声称几何工作计数覆盖 LP 算术。**

`numeric_batch` 同时受固定输入/解析预算和逐项算术整数位长预算约束：每个 evaluate 使用 context.max_integer_bits，覆盖 VECTOR / NORM / UNIT 的平方和及其他 exact 算术；超限项不改 bits 缓冲区并返回 RESOURCE_LIMIT，不产生数学结论。此 scope 不消费 GeometryWorkScope.max_work_units，也不是整进程内存或任意算法的统一墙钟保证。对抗 NORM 批由 `test_abi.cpp::numeric_compute_budget_matrix` 及收尾对手脚本复跑核验。

NO_COMPACT 导出仅作诊断；不把未压缩排布当规范接触骨架产品输出。C1 差分现检查 exterior_state 与 CONTACT 剖分层/接触骨架集合一致，见 `tools/eab2_c1_exact.py::verify_contact_layers/compare_exports`。

并发验证：test-only `test_context_rendezvous` 在真实 context 计算锁内设置两方会合；`test_c3l1_abi.cpp::concurrent_contexts` 用不同 context 的两个线程证明确实重叠，不以两个串行成功调用冒充并行。测试超时只报测试失败，无数学结论；此入口不在生产 DLL。


## C3-L3 增量合同（公开布局纳入发布 ABI v1）

不扩大已有结构。新增能力位 LIMIT2=16384、CRITICAL_PARAMETER=32768，以及 `eab2_get_c3l3_abi_info` 查询三个新描述符尺寸。`solve_limit2` 与 `critical_parameter` 在正式/测试 DLL 和静态库均可用；不把通用 LP 测试入口升级为生产 LP2。具名门：`test_c3l3_abi.cpp::contract/resource_limit/unresolved`、`test_c_header.c`、`tools/eab2_audit.py`。

- `eab2_body_load2` 为 dead/live 各三项有限 binary64 位模式，顺序 fx、fy、关于**冻结 reference_point** 的力矩。数组与 ContactSet2 快照的 body 顺序/数量严格一致，固定体也占记录；count、stride、指针、乘法溢出检查，不补零/截断。装配转到物理 dof_anchor 的虚功坐标，只保留自由 DOF 平衡行。
- `eab2_limit2_input` 为 header、mu_bits、body_count/body_stride/loads。mu 非负有限。`eab2_solve_limit2(context, contacts, input, output)` 拒无效/过期/跨 context/错类型的句柄；不接受裸接触列表冒充 complete。
- `eab2_critical_parameter_input` 为 header、mu_max_bits、max_steps、body_count/body_stride/loads、parameter/reserved。只支持 EAB2_PARAMETER_MU=1，其余返回 UNSUPPORTED，**不发布数学 JSON**。max_steps=0 合法；超过 4096 返回 RESOURCE_LIMIT；reserved 必须为零。非 binary64 的精确阈值只保存在有理证书字段，不回灌 double 查询。
- 调用失败保持整个 exact-result 输出原样，无半初始化 token。调用成功的 OPTIMAL、INFEASIBLE、UNBOUNDED、UNPROVED、MECHANICAL_UNRESOLVED 保留数学语义；critical 的 CERTIFIED 映射为 VALUE，不可行域为 INFEASIBLE。data/byte_count/结果句柄按已有库侧释放合同。
- `LimitResult2` 与 Python 字段同义，额外导出 `problem` 原始 exact A/b/c/行列标签/参考点/锚点及 OPTIMAL 的 `mechanism=exact_y`。机构核 `G^T y>=0, live^T y>=1`，非最优不附机构。有限 exact_value 不强制舍入为 double；display_status=EXACT 仅指有理输出。无界只给 x0 与 alpha=1 改进射线，不给伪有限容量或锁定结论。
- critical 同时导出 canonical mu_lo/mu_hi 与 mu_lo_bits/mu_hi_bits，两套必须精确一致。attained 为 true/false/null；exact_threshold、单侧多项式证明、bisection_termination、threshold_proof_reason 分开。input_resolution_limit 可与已证明的开/闭阈并存。一般代数根对象仍未实现。
- WO-C3L4-fix 新增 `search_domain`，不改旧字段：`mu_min`/`mu_max` 是原始闭搜索域的 binary64 输入值，`mu_min_binary64`/`mu_max_binary64` 为对应 16 位十六进制位模式，`exact_mu_min`/`exact_mu_max` 为其精确有理值；下界固定 0。它绑定原始输入，不是收窄后的 `mu_lo`/`mu_hi`，阈值方向证书只能使用此域。
- 限额沿用 context 几何工作/矩阵元素/整数位长预算和 opt 每次调用默认 1,000,000 次主元预算；critical 私有入口整数 scope 贯穿多项式延拓。**LP 算术和多项式算术并不逐次消费 GeometryWorkScope.step；max_work_units 不是整个 L3 的统一运算/墙钟预算。** 4096 次二分上限不保证运行时间，资源拒签不产生数学结论。

差分独立解析原始几何/荷载 bits 重建矩阵，非唯一证书按定义核验。临界基以精确有理高斯求值和度数界核多项式恒等式，以单侧 Sturm 核开闭证明。见 `tools/eab2_c3l3_diff.py::verify_limit/verify_branch/verify_critical`、`tests/test_eab2_c3l3_harness.py`。profile1 是关联流动上界模型，不是安全承载力。发布稳定 ABI、真实宿主接入、所有者新鲜树与独立对抗签字不由本工作接口自动满足。

## C3-L4 敏感性族

新增正式能力 SENSITIVITY2=524288，生产总能力位为 581501。新增 eab2_get_c3l4_abi_info 和 eab2_evaluate_sensitivity2；旧结构不扩写。后者接收已保留的 solve_limit2 / critical_parameter 结果 token，不重解原值或阈值。库侧 result 保存 typed 数学结果与独立 ContactSet2 快照；原 body/assembly/contact 可先释放，只有 result/context 释放使此结果失效。普通 JSON result、错误类型、跨 context、过期世代拒收，失败输出整体不变。

输入结构见 c_api.h：P=parameter_count>=1、output_count=1、channel_count=P；参数名唯一。body_ids 按 UTF-8 body ID 排序，vertex_ids 按 (body ID, 原输入顶点 ID) 排序，必须完整且精确匹配快照。vertices[P][V][2]、dead/live[P][B][3]、dof_anchor[P][B][2]、mu[P] 为固定连续行主序 canonical n/d 文本。每次数量乘法先查溢出；全部 stride 精确等于 sizeof，不接受缺项、补零、重复或静默排序。每通道显式正负方向标志、有效条件与 caller 字符串标签；自动阈值列标签保持结构化 ColumnLabel2，不改成 JSON 字符串。

**种子的 B 轴遵循排序后的 `body_ids`，不是装配输入顺序；`solve_limit2` / `critical_parameter` 的 loads 则按 ContactSet2 保存的装配顺序。** 两者不得共用未经重排的数组。阈值敏感性通道的 `mu` 种子必须为精确零；非零表示无意义的 `dμ_crit/dμ` 请求，返回 INVALID_INPUT，错误详情指向种子数组及通道/元素下标。普通极限值对 μ 的导数不受此限制。

有限值在原始未缩放 LP 上传播。临界值在已保留 threshold_certificate.problem 的精确 μ 上传播，自动构造 μ 种子；不能回灌二分端点或舍入后的临界数。缺精确证据时仍核全部结构和身份，诚实无斜率。JSON 含 sensitivity_model、parameter_count/output_count/channel_count、jacobian_layout=output_major_channel_minor、jacobian_shape=[1,P]、channels 和 flat jacobian；channels 含 parameter/result/derived_seed/threshold_mu_seed。只有 smooth 且 exact_jet 的认证导数进入 jacobian，其余单元 null。derived_seed 为实际几何传播产物，不读取语料存储的 dA/db/dc 当输入。

确定性输入限额：P<=1024，种子总标量数<=context.max_elements；每文本<=4096字节，总文本<=4194304字节，长度平方和<=67108864。精确算法继承整数位长和每次 LP 主元预算；不声称 max_work_units 是敏感性全部算术或墙钟上限。测试 test_c3l4_abi.cpp 覆盖三条互异通道、全部描述符与句柄拒收、快照生命周期、无证阈值、原子失败和 FP 状态不变；C 头生产/静态门同时核新增尺寸和能力。

### 敏感性 JSON 与阈值分支证书 v1

- `right_derivative=D+`；`left_derivative` 是**普通左导数 `−D−`**，不是沿反向种子计算的 D−。`directional_derivative` 与正向右导同义；无证方向保持 null，不能用另一侧填充。
- `method` 包括 `stable_basis`、`mills_freund`、`optimal_face_recession` 与阈值路径 `branch_certificate`；`differentiability`、`quality`、`reason`、`validity_conditions` 不由浮点差商决定。只有有精确证书的方向值才可标 `exact_jet`；单侧有证不冒充 smooth。
- 阈值 `branch_certificate` 为可复核对象：`version=1`、`order="epsilon_then_eta"`、与 critical 完全一致的 `search_domain`，以及 `forward`/`reverse`。各方向含 `status`，认证时含有理 `s`、`lower` 机构证书、`upper.point` 可行点和 `upper.ray` 改进射线；基行/列、标签与邻近探测点随证据保存。稀疏多项式条目为 `[epsilon指数, eta指数, 有理系数]`，有理函数保存完整分子/分母；不得凭截断后全零系数推断精确为零。
- 证书由原始仿射顶点/锚点/荷载路径重建完整多项式。按 `0<epsilon<<eta<<1` 核下界对偶可行、上界原点/射线可行和两条原始域条件；邻点只是选基候选，不是证明。失败方向 unresolved：不能满足原始域条件时 reason 为 `threshold_search_domain_boundary`，其余候选/基无法认证时为 `threshold_branch_certificate_unavailable`；内部已报 certified 却缺下端对偶/上端点/射线时降为 `internal_certificate_shape`，不得输出该方向值（门：`test_certified_direction_without_witnesses_is_never_a_value`、C++ `branch_face2_regression`）。下界钳制导数为零不属于本版合同。
- `candidate_branches[].components` 保存所选候选基中根斜率等于所证 `s` 的全部约束标签与偏导。`tied_labels` 是这些标签的集合，属基依赖证书字段，不要求不同后端集合相同；每侧必须独立核所有匹配分量与斜率，集合差异逐例登记。非阈值固定基/Mills-Freund 的原比较合同不变。
- `candidate_branches[].singular=true` 表示原点退化候选基；其分量不伪造 `partial_mu` / `partial_parameter`，而记录 `index`、`label`、`s`、`leading_epsilon_order` 与 `leading_polynomial`（按升幂排列的完整有理系数，次数至少 1、最高系数规范为 1）。它保留首个非零 epsilon 阶及全部重根信息，所证 `s` 必须使该多项式精确为零；这些仍只是候选根元数据，导数认证仍依赖完整下/上 K 夹逼。consumer 仅核阶数/规范化/根的内部一致性，不代替 L4 从原始几何重建并核首阶系数及完整标签集合。

完整独立核验入口为 `tools/eab2_branch_verify.py`；实施及实际门结果见修复轮报告，不把协议说明当作已完成验收。公开 C 结构布局不变，新增证明信息只在 JSON 与内部结果快照中保存。
工具档案 `.certificates.jsonl` 的顶层 `mu_max_binary64` 必须来自调用方原始请求，并独立核与返回 `search_domain` 相等；缺字段拒绝，不从返回域补值。此为工具档案接线，不改公开 C 布局或下方冻结表；具名门为 `test_certificate_archive_writer_binds_the_original_caller_request` 与 `test_archive_caller_domain_forgery_is_rejected_by_independent_checker`。

消费者对旧冻结语料的元数据订正使用显式版本 `WO-C3L4-fix/20261023/branch-proof-v1`：只有阈值 `method=branch_certificate` 可移除旧“临界证书基非奇异”“所列越零分量及方向保持有效”两条单基假设，并逐查询输出 `condition_errata.old/new`；其他条件与语义数值仍严格比较。这不是放宽有效域，也不声称旧冻结语料逐字不变。consumer 的分支标签检查仅为所收 JSON 的内部结构与根斜率一致性，跨冻结基差异逐项输出；完整原始几何 K 核验由独立 L4 门承担，consumer 不导入该门。

## 发布 ABI v1 冻结表

本节冻结的是**已实现接口的技术基线**；整单完成须由最新实测收尾及 Claude 验收确认。按 2026-10-23 Claude 裁定，现有 consumer 满足设计 §8.5，不追加另一名人工使用者待办；旧标签差异的核验口径与处置见主报告及 [原 ABI 审查](../reports/codex/C3L4_evidence/clarification/abi_review.md)。WO-C3L4-fix 补齐机器表遗漏的 `constants` 与 `return_types`，既有常量值、导出和公开布局均不变。旧 `release_acceptance` 历史标记已移出冻结块：验收说明版本为 `WO-C3L4-fix/20261023`，本轮状态以 [修复轮报告](../reports/codex/C3L4_fix_report.md) 为准，不能用冻结表的存在替代所有者验收。

冻结依据：独立 tools/eab2_tia_consumer.py 以 python -I 从冻结原始 bits/几何种子出发，只加载发布 eab2.dll，对 G1 开阈/闭阈、G5 奇异/滑移/切换/铰接 6 例实际跑完 body/entrance、assemble_contact_set2、lock/first_order、limit、critical、18 条 sensitivity。原始结果见 ../reports/codex/C3L4_evidence/consumer.json；末行 EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0。该脚本不是 Python 裁判或差分 harness，也不是所有者新鲜树和非作者对抗签字的替代品。

进一步最小隔离复跑只复制 10 个文件（脚本、C 头、发布 DLL、manifest、6 份 gzip），以 python -I -S 禁用环境路径与 site，仍得到同一零失配末行；目录没有 src、差分 harness、pybind、姊妹内容或测试 DLL。逐文件 SHA、完整命令与计时见 ../reports/codex/C3L4_evidence/consumer_isolation.json，完整输出见 consumer_isolation.log.gz。它是明确的最小字节副本，不称 Git 新树。

| 函数族 | 发布入口（共同 eab2_ 前缀） |
|---|---|
| 基础与错误 | get_abi_info / self_test / context_create / context_destroy / context_get_error |
| 限额 | context_get_limits2 / context_configure_limits2 |
| 版本尺寸 | get_c1_abi_info / get_c3l1_abi_info / get_c3l3_abi_info / get_c3l4_abi_info |
| 体与入口块 | body2_create / body2_destroy / entrance2_create / entrance2_destroy |
| 双三态与精确输出 | query2_batch / membership2_batch / topology2_batch / result_export_exact / local_origin2_exact / result_destroy |
| 装配与接触 | assembly2_create / assembly2_destroy / assemble_contact_set2 / contact_set2_destroy / contact_set2_export_exact |
| 锁定与一阶 | query_lock / first_order_mobility |
| 静力与临界 | solve_limit2 / critical_parameter |
| 敏感性 | evaluate_sensitivity2 |

以下机器可读表逐项冻结全部 31 个函数的参数 ABI 类型及 C 返回类型、28 个实际 C 结构的 sizeof/字段 offset/header version 与每字段规范 C 类型（保留 const、所有指针层级与数组维度），以及全部 64 个整数 `#define EAB2_*` 的宽度/值、全部能力位的 presence。同尺寸、同偏移的 `char*`→`uint32_t*` 或 const 漂移也必须拒收。Body/E/Assembly/ContactSet/Result 句柄都是 eab2_context 的同布局别名，运行时仍检查类型与世代。无 header 的嵌入记录 version 为 null（随所属 ABI v1 冻结），不是可独立协商的版本。tools/eab2_release_abi.py 自含标准库头解析，可在 `python -I -S` 运行且不导入 consumer；枚举所有 `eab2_*(...)` 原型后检查 EAB2_API 与返回类型，不能因新增函数缺宏或返回 void 就漏查。完整 PE 导出表与头声明和本表精确比较；不只做 hasattr 白名单；拒绝额外导出、漏导出、ordinal-only、转发导出和测试能力泄漏。后续扩展仅版本化追加，不能修改这份已冻结 v1 的布局或既有字段语义。

发布 DLL 为 `/MD` 的 x64 MSVC 产物，依赖 Microsoft Visual C++ 2015–2022 x64 运行库的 `MSVCP140.dll`、`VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`；须由宿主准备，本工具不安装、不下载。

<!-- EAB2_RELEASE_ABI_V1_BEGIN -->
```json
{
  "abi_version": 1,
  "platform": "MSVC_x64",
  "exports": [
    "eab2_assemble_contact_set2",
    "eab2_assembly2_create",
    "eab2_assembly2_destroy",
    "eab2_body2_create",
    "eab2_body2_destroy",
    "eab2_contact_set2_destroy",
    "eab2_contact_set2_export_exact",
    "eab2_context_configure_limits2",
    "eab2_context_create",
    "eab2_context_destroy",
    "eab2_context_get_error",
    "eab2_context_get_limits2",
    "eab2_critical_parameter",
    "eab2_entrance2_create",
    "eab2_entrance2_destroy",
    "eab2_evaluate_sensitivity2",
    "eab2_first_order_mobility",
    "eab2_get_abi_info",
    "eab2_get_c1_abi_info",
    "eab2_get_c3l1_abi_info",
    "eab2_get_c3l3_abi_info",
    "eab2_get_c3l4_abi_info",
    "eab2_local_origin2_exact",
    "eab2_membership2_batch",
    "eab2_query2_batch",
    "eab2_query_lock",
    "eab2_result_destroy",
    "eab2_result_export_exact",
    "eab2_self_test",
    "eab2_solve_limit2",
    "eab2_topology2_batch"
  ],
  "signatures": {
    "eab2_assemble_contact_set2": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_context"
    ],
    "eab2_assembly2_create": [
      "eab2_context",
      "LP_eab2_assembly2_input",
      "LP_eab2_context"
    ],
    "eab2_assembly2_destroy": [
      "eab2_context",
      "eab2_context"
    ],
    "eab2_body2_create": [
      "eab2_context",
      "LP_eab2_body2_input",
      "LP_eab2_context"
    ],
    "eab2_body2_destroy": [
      "eab2_context",
      "eab2_context"
    ],
    "eab2_contact_set2_destroy": [
      "eab2_context",
      "eab2_context"
    ],
    "eab2_contact_set2_export_exact": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_exact_result"
    ],
    "eab2_context_configure_limits2": [
      "eab2_context",
      "LP_eab2_context_limits2"
    ],
    "eab2_context_create": [
      "LP_eab2_context_options",
      "LP_eab2_context"
    ],
    "eab2_context_destroy": [
      "eab2_context"
    ],
    "eab2_context_get_error": [
      "eab2_context",
      "LP_eab2_error_info",
      "LP_c_char",
      "c_ulonglong",
      "LP_c_ulonglong"
    ],
    "eab2_context_get_limits2": [
      "eab2_context",
      "LP_eab2_context_limits2"
    ],
    "eab2_critical_parameter": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_critical_parameter_input",
      "LP_eab2_exact_result"
    ],
    "eab2_entrance2_create": [
      "eab2_context",
      "eab2_context",
      "eab2_context",
      "LP_eab2_entrance2_options",
      "LP_eab2_context"
    ],
    "eab2_entrance2_destroy": [
      "eab2_context",
      "eab2_context"
    ],
    "eab2_evaluate_sensitivity2": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_sensitivity2_input",
      "LP_eab2_exact_result"
    ],
    "eab2_first_order_mobility": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_exact_result"
    ],
    "eab2_get_abi_info": [
      "LP_eab2_abi_info"
    ],
    "eab2_get_c1_abi_info": [
      "LP_eab2_c1_abi_info"
    ],
    "eab2_get_c3l1_abi_info": [
      "LP_eab2_c3l1_abi_info"
    ],
    "eab2_get_c3l3_abi_info": [
      "LP_eab2_c3l3_abi_info"
    ],
    "eab2_get_c3l4_abi_info": [
      "LP_eab2_c3l4_abi_info"
    ],
    "eab2_local_origin2_exact": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_exact_result"
    ],
    "eab2_membership2_batch": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_query2_input",
      "LP_eab2_query2_output"
    ],
    "eab2_query2_batch": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_query2_input",
      "LP_eab2_query2_output"
    ],
    "eab2_query_lock": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_lock2_input",
      "LP_eab2_exact_result"
    ],
    "eab2_result_destroy": [
      "eab2_context",
      "eab2_context"
    ],
    "eab2_result_export_exact": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_exact_result"
    ],
    "eab2_self_test": [],
    "eab2_solve_limit2": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_limit2_input",
      "LP_eab2_exact_result"
    ],
    "eab2_topology2_batch": [
      "eab2_context",
      "eab2_context",
      "LP_eab2_query2_input",
      "LP_eab2_query2_output"
    ]
  },
  "capabilities": {
    "EAB2_CAP_ASSEMBLY2": {
      "value": 512,
      "present": true
    },
    "EAB2_CAP_BODY2": {
      "value": 4,
      "present": true
    },
    "EAB2_CAP_CONTACTSET2": {
      "value": 1024,
      "present": true
    },
    "EAB2_CAP_CONTEXT": {
      "value": 1,
      "present": true
    },
    "EAB2_CAP_CRITICAL_PARAMETER": {
      "value": 32768,
      "present": true
    },
    "EAB2_CAP_ENTRANCE2": {
      "value": 8,
      "present": true
    },
    "EAB2_CAP_EXPORT_EXACT": {
      "value": 32,
      "present": true
    },
    "EAB2_CAP_LIMIT2": {
      "value": 16384,
      "present": true
    },
    "EAB2_CAP_LIMITS2": {
      "value": 256,
      "present": true
    },
    "EAB2_CAP_LOCAL2": {
      "value": 64,
      "present": true
    },
    "EAB2_CAP_LOCK2": {
      "value": 2048,
      "present": true
    },
    "EAB2_CAP_LP2": {
      "value": 262144,
      "present": false
    },
    "EAB2_CAP_MOBILITY2": {
      "value": 4096,
      "present": true
    },
    "EAB2_CAP_QUERY2": {
      "value": 16,
      "present": true
    },
    "EAB2_CAP_RHO": {
      "value": 65536,
      "present": false
    },
    "EAB2_CAP_SE2": {
      "value": 131072,
      "present": false
    },
    "EAB2_CAP_SENSITIVITY2": {
      "value": 524288,
      "present": true
    },
    "EAB2_CAP_TEST_EXACT2": {
      "value": 128,
      "present": false
    },
    "EAB2_CAP_TEST_NUMERIC": {
      "value": 2,
      "present": false
    },
    "EAB2_CAP_TEST_OPT": {
      "value": 8192,
      "present": false
    }
  },
  "supported_capabilities": 581501,
  "structures": {
    "eab2_context": {
      "size": 32,
      "abi_version": null,
      "fields": {
        "owner": 0,
        "id": 8,
        "generation": 16,
        "type": 24,
        "reserved": 28
      },
      "field_types": {
        "owner": "uint64_t",
        "id": "uint64_t",
        "generation": "uint64_t",
        "type": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_abi_info": {
      "size": 248,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "requested_capabilities": 8,
        "supported_capabilities": 16,
        "unsupported_capabilities": 24,
        "context_size": 32,
        "context_options_size": 36,
        "error_info_size": 40,
        "binary64_bits": 44,
        "pointer_bits": 48,
        "reserved": 52,
        "build_identity": 56
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "requested_capabilities": "uint64_t",
        "supported_capabilities": "uint64_t",
        "unsupported_capabilities": "uint64_t",
        "context_size": "uint32_t",
        "context_options_size": "uint32_t",
        "error_info_size": "uint32_t",
        "binary64_bits": "uint32_t",
        "pointer_bits": "uint32_t",
        "reserved": "uint32_t",
        "build_identity": "char[192]"
      }
    },
    "eab2_context_options": {
      "size": 16,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "flags": 8,
        "reserved": 12
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "flags": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_error_info": {
      "size": 72,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "code": 8,
        "reserved": 12,
        "index": 16,
        "field": 24
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "code": "uint32_t",
        "reserved": "uint32_t",
        "index": "uint64_t",
        "field": "char[48]"
      }
    },
    "eab2_context_limits2": {
      "size": 32,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "max_work_units": 8,
        "max_elements": 16,
        "max_integer_bits": 24
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "max_work_units": "uint64_t",
        "max_elements": "uint64_t",
        "max_integer_bits": "uint64_t"
      }
    },
    "eab2_point2_bits": {
      "size": 16,
      "abi_version": null,
      "fields": {
        "x_bits": 0,
        "y_bits": 8
      },
      "field_types": {
        "x_bits": "uint64_t",
        "y_bits": "uint64_t"
      }
    },
    "eab2_body2_input": {
      "size": 40,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "vertex_count": 8,
        "vertex_stride": 16,
        "vertices": 24,
        "flags": 32,
        "reserved": 36
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "vertex_count": "uint64_t",
        "vertex_stride": "uint64_t",
        "vertices": "const eab2_point2_bits*",
        "flags": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_entrance2_options": {
      "size": 16,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "flags": 8,
        "reserved": 12
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "flags": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_query2_input": {
      "size": 32,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "point_count": 8,
        "point_stride": 16,
        "points": 24
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "point_count": "uint64_t",
        "point_stride": "uint64_t",
        "points": "const eab2_point2_bits*"
      }
    },
    "eab2_query2_item": {
      "size": 16,
      "abi_version": null,
      "fields": {
        "call_status": 0,
        "mathematical_status": 4,
        "body_state": 8,
        "topology_state": 12
      },
      "field_types": {
        "call_status": "uint32_t",
        "mathematical_status": "uint32_t",
        "body_state": "uint32_t",
        "topology_state": "uint32_t"
      }
    },
    "eab2_query2_output": {
      "size": 40,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "item_capacity": 8,
        "item_stride": 16,
        "item_count": 24,
        "items": 32
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "item_capacity": "uint64_t",
        "item_stride": "uint64_t",
        "item_count": "uint64_t",
        "items": "eab2_query2_item*"
      }
    },
    "eab2_exact_result": {
      "size": 64,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "call_status": 8,
        "mathematical_status": 12,
        "result": 16,
        "data": 48,
        "byte_count": 56
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "call_status": "uint32_t",
        "mathematical_status": "uint32_t",
        "result": "eab2_result",
        "data": "const char*",
        "byte_count": "uint64_t"
      }
    },
    "eab2_c1_abi_info": {
      "size": 40,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "body2_input_size": 8,
        "entrance2_options_size": 12,
        "query2_input_size": 16,
        "query2_item_size": 20,
        "query2_output_size": 24,
        "exact_result_size": 28,
        "point2_bits_size": 32,
        "reserved": 36
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "body2_input_size": "uint32_t",
        "entrance2_options_size": "uint32_t",
        "query2_input_size": "uint32_t",
        "query2_item_size": "uint32_t",
        "query2_output_size": "uint32_t",
        "exact_result_size": "uint32_t",
        "point2_bits_size": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_string": {
      "size": 16,
      "abi_version": null,
      "fields": {
        "data": 0,
        "length": 8
      },
      "field_types": {
        "data": "const char*",
        "length": "uint64_t"
      }
    },
    "eab2_assembly_body2": {
      "size": 96,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "body": 8,
        "body_id": 40,
        "reference_point": 56,
        "dof_anchor": 72,
        "boundary_type": 88,
        "dof_mask": 92
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "body": "eab2_body2",
        "body_id": "eab2_string",
        "reference_point": "eab2_point2_bits",
        "dof_anchor": "eab2_point2_bits",
        "boundary_type": "uint32_t",
        "dof_mask": "uint32_t"
      }
    },
    "eab2_pair2": {
      "size": 16,
      "abi_version": null,
      "fields": {
        "a": 0,
        "b": 8
      },
      "field_types": {
        "a": "uint64_t",
        "b": "uint64_t"
      }
    },
    "eab2_assembly2_input": {
      "size": 64,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "flags": 8,
        "profile": 12,
        "body_count": 16,
        "body_stride": 24,
        "bodies": 32,
        "pair_count": 40,
        "pair_stride": 48,
        "pairs": 56
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "flags": "uint32_t",
        "profile": "uint32_t",
        "body_count": "uint64_t",
        "body_stride": "uint64_t",
        "bodies": "const eab2_assembly_body2*",
        "pair_count": "uint64_t",
        "pair_stride": "uint64_t",
        "pairs": "const eab2_pair2*"
      }
    },
    "eab2_lock2_input": {
      "size": 40,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "moving_index": 8,
        "neighbor_count": 16,
        "neighbor_stride": 24,
        "neighbors": 32
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "moving_index": "uint64_t",
        "neighbor_count": "uint64_t",
        "neighbor_stride": "uint64_t",
        "neighbors": "const uint64_t*"
      }
    },
    "eab2_c3l1_abi_info": {
      "size": 32,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "assembly_body2_size": 8,
        "assembly2_input_size": 12,
        "pair2_size": 16,
        "lock2_input_size": 20,
        "string_size": 24,
        "reserved": 28
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "assembly_body2_size": "uint32_t",
        "assembly2_input_size": "uint32_t",
        "pair2_size": "uint32_t",
        "lock2_input_size": "uint32_t",
        "string_size": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_body_load2": {
      "size": 48,
      "abi_version": null,
      "fields": {
        "dead_bits": 0,
        "live_bits": 24
      },
      "field_types": {
        "dead_bits": "uint64_t[3]",
        "live_bits": "uint64_t[3]"
      }
    },
    "eab2_limit2_input": {
      "size": 40,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "mu_bits": 8,
        "body_count": 16,
        "body_stride": 24,
        "loads": 32
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "mu_bits": "uint64_t",
        "body_count": "uint64_t",
        "body_stride": "uint64_t",
        "loads": "const eab2_body_load2*"
      }
    },
    "eab2_critical_parameter_input": {
      "size": 56,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "mu_max_bits": 8,
        "max_steps": 16,
        "body_count": 24,
        "body_stride": 32,
        "loads": 40,
        "parameter": 48,
        "reserved": 52
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "mu_max_bits": "uint64_t",
        "max_steps": "uint64_t",
        "body_count": "uint64_t",
        "body_stride": "uint64_t",
        "loads": "const eab2_body_load2*",
        "parameter": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_c3l3_abi_info": {
      "size": 24,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "body_load2_size": 8,
        "limit2_input_size": 12,
        "critical_parameter_input_size": 16,
        "reserved": 20
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "body_load2_size": "uint32_t",
        "limit2_input_size": "uint32_t",
        "critical_parameter_input_size": "uint32_t",
        "reserved": "uint32_t"
      }
    },
    "eab2_string_array": {
      "size": 24,
      "abi_version": null,
      "fields": {
        "value_count": 0,
        "value_stride": 8,
        "values": 16
      },
      "field_types": {
        "value_count": "uint64_t",
        "value_stride": "uint64_t",
        "values": "const eab2_string*"
      }
    },
    "eab2_sensitivity_vertex2": {
      "size": 24,
      "abi_version": null,
      "fields": {
        "body_id": 0,
        "vertex_id": 16
      },
      "field_types": {
        "body_id": "eab2_string",
        "vertex_id": "uint64_t"
      }
    },
    "eab2_sensitivity_channel2": {
      "size": 80,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "parameter": 8,
        "positive_direction_valid": 24,
        "negative_direction_valid": 28,
        "validity_conditions": 32,
        "tied_labels": 56
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "parameter": "eab2_string",
        "positive_direction_valid": "uint32_t",
        "negative_direction_valid": "uint32_t",
        "validity_conditions": "eab2_string_array",
        "tied_labels": "eab2_string_array"
      }
    },
    "eab2_sensitivity2_input": {
      "size": 224,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "parameter_count": 8,
        "output_count": 16,
        "channel_count": 24,
        "body_count": 32,
        "vertex_count": 40,
        "channel_stride": 48,
        "channels": 56,
        "body_ids": 64,
        "vertex_stride": 88,
        "vertex_ids": 96,
        "vertices": 104,
        "dead": 128,
        "live": 152,
        "dof_anchor": 176,
        "mu": 200
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "parameter_count": "uint64_t",
        "output_count": "uint64_t",
        "channel_count": "uint64_t",
        "body_count": "uint64_t",
        "vertex_count": "uint64_t",
        "channel_stride": "uint64_t",
        "channels": "const eab2_sensitivity_channel2*",
        "body_ids": "eab2_string_array",
        "vertex_stride": "uint64_t",
        "vertex_ids": "const eab2_sensitivity_vertex2*",
        "vertices": "eab2_string_array",
        "dead": "eab2_string_array",
        "live": "eab2_string_array",
        "dof_anchor": "eab2_string_array",
        "mu": "eab2_string_array"
      }
    },
    "eab2_c3l4_abi_info": {
      "size": 32,
      "abi_version": 1,
      "fields": {
        "struct_size": 0,
        "abi_version": 4,
        "string_array_size": 8,
        "sensitivity_vertex2_size": 12,
        "sensitivity_channel2_size": 16,
        "sensitivity2_input_size": 20,
        "reserved": 24,
        "reserved2": 28
      },
      "field_types": {
        "struct_size": "uint32_t",
        "abi_version": "uint32_t",
        "string_array_size": "uint32_t",
        "sensitivity_vertex2_size": "uint32_t",
        "sensitivity_channel2_size": "uint32_t",
        "sensitivity2_input_size": "uint32_t",
        "reserved": "uint32_t",
        "reserved2": "uint32_t"
      }
    }
  },
  "status": "FROZEN",
  "consumer_evidence": "reports/codex/C3L4_evidence/consumer.json",
  "consumer_summary": "EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0",
  "freeze_scope": "implemented_abi_layout_baseline",
  "return_types": {
    "eab2_assemble_contact_set2": "eab2_call_status",
    "eab2_assembly2_create": "eab2_call_status",
    "eab2_assembly2_destroy": "eab2_call_status",
    "eab2_body2_create": "eab2_call_status",
    "eab2_body2_destroy": "eab2_call_status",
    "eab2_contact_set2_destroy": "eab2_call_status",
    "eab2_contact_set2_export_exact": "eab2_call_status",
    "eab2_context_configure_limits2": "eab2_call_status",
    "eab2_context_create": "eab2_call_status",
    "eab2_context_destroy": "eab2_call_status",
    "eab2_context_get_error": "eab2_call_status",
    "eab2_context_get_limits2": "eab2_call_status",
    "eab2_critical_parameter": "eab2_call_status",
    "eab2_entrance2_create": "eab2_call_status",
    "eab2_entrance2_destroy": "eab2_call_status",
    "eab2_evaluate_sensitivity2": "eab2_call_status",
    "eab2_first_order_mobility": "eab2_call_status",
    "eab2_get_abi_info": "eab2_call_status",
    "eab2_get_c1_abi_info": "eab2_call_status",
    "eab2_get_c3l1_abi_info": "eab2_call_status",
    "eab2_get_c3l3_abi_info": "eab2_call_status",
    "eab2_get_c3l4_abi_info": "eab2_call_status",
    "eab2_local_origin2_exact": "eab2_call_status",
    "eab2_membership2_batch": "eab2_call_status",
    "eab2_query2_batch": "eab2_call_status",
    "eab2_query_lock": "eab2_call_status",
    "eab2_result_destroy": "eab2_call_status",
    "eab2_result_export_exact": "eab2_call_status",
    "eab2_self_test": "eab2_call_status",
    "eab2_solve_limit2": "eab2_call_status",
    "eab2_topology2_batch": "eab2_call_status"
  },
  "constants": {
    "EAB2_ABI_VERSION": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_ASSEMBLY_COMPLETE": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_ASSEMBLY_EXPLICIT_PAIRS": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_BODY_CONTACT": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_BODY_OUTSIDE": {
      "type": "uint32_t",
      "value": 0
    },
    "EAB2_BODY_OVERLAP": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_BOUNDARY_NONE": {
      "type": "uint32_t",
      "value": 0
    },
    "EAB2_CANCELLED": {
      "type": "uint32_t",
      "value": 8
    },
    "EAB2_CAP_ASSEMBLY2": {
      "type": "uint64_t",
      "value": 512
    },
    "EAB2_CAP_BODY2": {
      "type": "uint64_t",
      "value": 4
    },
    "EAB2_CAP_CONTACTSET2": {
      "type": "uint64_t",
      "value": 1024
    },
    "EAB2_CAP_CONTEXT": {
      "type": "uint64_t",
      "value": 1
    },
    "EAB2_CAP_CRITICAL_PARAMETER": {
      "type": "uint64_t",
      "value": 32768
    },
    "EAB2_CAP_ENTRANCE2": {
      "type": "uint64_t",
      "value": 8
    },
    "EAB2_CAP_EXPORT_EXACT": {
      "type": "uint64_t",
      "value": 32
    },
    "EAB2_CAP_LIMIT2": {
      "type": "uint64_t",
      "value": 16384
    },
    "EAB2_CAP_LIMITS2": {
      "type": "uint64_t",
      "value": 256
    },
    "EAB2_CAP_LOCAL2": {
      "type": "uint64_t",
      "value": 64
    },
    "EAB2_CAP_LOCK2": {
      "type": "uint64_t",
      "value": 2048
    },
    "EAB2_CAP_LP2": {
      "type": "uint64_t",
      "value": 262144
    },
    "EAB2_CAP_MOBILITY2": {
      "type": "uint64_t",
      "value": 4096
    },
    "EAB2_CAP_QUERY2": {
      "type": "uint64_t",
      "value": 16
    },
    "EAB2_CAP_RHO": {
      "type": "uint64_t",
      "value": 65536
    },
    "EAB2_CAP_SE2": {
      "type": "uint64_t",
      "value": 131072
    },
    "EAB2_CAP_SENSITIVITY2": {
      "type": "uint64_t",
      "value": 524288
    },
    "EAB2_CAP_TEST_EXACT2": {
      "type": "uint64_t",
      "value": 128
    },
    "EAB2_CAP_TEST_NUMERIC": {
      "type": "uint64_t",
      "value": 2
    },
    "EAB2_CAP_TEST_OPT": {
      "type": "uint64_t",
      "value": 8192
    },
    "EAB2_CONSTRUCTION_RANGE": {
      "type": "uint32_t",
      "value": 4
    },
    "EAB2_DISPLAY_NOT_AVAILABLE": {
      "type": "uint32_t",
      "value": 0
    },
    "EAB2_DISPLAY_RANGE": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_DISPLAY_UNDERFLOW_ZERO": {
      "type": "uint32_t",
      "value": 3
    },
    "EAB2_DISPLAY_VALID": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_ENTRANCE_NO_CACHE": {
      "type": "uint32_t",
      "value": 4
    },
    "EAB2_ENTRANCE_NO_COMPACT": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_ENTRANCE_NO_MERGE": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_FIXED_BODY": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_FORCE_CONTROLLED_PLATE": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_FP_CONTRACT": {
      "type": "uint32_t",
      "value": 6
    },
    "EAB2_HANDLE_ASSEMBLY2": {
      "type": "uint32_t",
      "value": 5
    },
    "EAB2_HANDLE_BODY2": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_HANDLE_CONTACTSET2": {
      "type": "uint32_t",
      "value": 6
    },
    "EAB2_HANDLE_CONTEXT": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_HANDLE_ENTRANCE2": {
      "type": "uint32_t",
      "value": 3
    },
    "EAB2_HANDLE_RESULT": {
      "type": "uint32_t",
      "value": 4
    },
    "EAB2_INTERNAL_ERROR": {
      "type": "uint32_t",
      "value": 7
    },
    "EAB2_INVALID_HANDLE": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_INVALID_INPUT": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_MATH_INFEASIBLE": {
      "type": "uint32_t",
      "value": 5
    },
    "EAB2_MATH_MECHANICAL_UNRESOLVED": {
      "type": "uint32_t",
      "value": 7
    },
    "EAB2_MATH_NOT_COMPUTED": {
      "type": "uint32_t",
      "value": 0
    },
    "EAB2_MATH_NO_EVENT": {
      "type": "uint32_t",
      "value": 3
    },
    "EAB2_MATH_OVERLAP": {
      "type": "uint32_t",
      "value": 4
    },
    "EAB2_MATH_UNBOUNDED": {
      "type": "uint32_t",
      "value": 6
    },
    "EAB2_MATH_UNPROVED": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_MATH_VALUE": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_OK": {
      "type": "uint32_t",
      "value": 0
    },
    "EAB2_PARAMETER_MU": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_PROFILE1": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_RESOURCE_LIMIT": {
      "type": "uint32_t",
      "value": 5
    },
    "EAB2_TOPOLOGY_BOUNDARY": {
      "type": "uint32_t",
      "value": 1
    },
    "EAB2_TOPOLOGY_INTERIOR": {
      "type": "uint32_t",
      "value": 2
    },
    "EAB2_TOPOLOGY_OUTSIDE": {
      "type": "uint32_t",
      "value": 0
    },
    "EAB2_UNSUPPORTED": {
      "type": "uint32_t",
      "value": 3
    }
  }
}
```
<!-- EAB2_RELEASE_ABI_V1_END -->
