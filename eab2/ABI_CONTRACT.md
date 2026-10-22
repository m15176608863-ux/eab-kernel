# eab2 C0 / C1 工作 ABI 合同

这是设计 §5.4 的 C0 工作接口，不是 C3 发布产品 ABI 冻结。公共 C 头只含固定宽度整数、长度与指针；无 C++ bool、STL、Boost、异常或 enum 布局。全部入口捕获 C++ 异常。调用方仍须提供真实有效且足够大的、互不重叠的描述符和缓冲区；本单不是恶意地址/宿主接缝加固。

## 正式导出与能力

`eab2_get_abi_info`、`eab2_self_test`、`eab2_context_create`、`eab2_context_destroy`、`eab2_context_get_error`。ABI version=1，`struct_size` 必须精确匹配；版本不匹配返回 UNSUPPORTED。构建身份包含工具链、ISA 与后端，由构建系统生成。`get_abi_info` 总是报告已实现能力；`requested_capabilities` 的未支持位完整返回 `unsupported_capabilities` 并返回 UNSUPPORTED。C1 正式 DLL 具有 CONTEXT/BODY2/ENTRANCE2/QUERY2/EXPORT_EXACT/LOCAL2 能力，没有 rho/SE2/LP2 或数值发布入口；不提供占位时间、距离或承载力。

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

context 是 `{owner,id,generation,type,reserved}` 的 32 字节 token，不是可供调用者释放的指针。context token 的 owner 必须等于 id；每次查表还核类型、世代与 reserved。context 与子对象槽位复用；每次分配使用库级单调递增 generation（溢出 RESOURCE_LIMIT），使同 id 的旧 token 仍无效。子对象 owner 为 context id；跨 context、错类型、旧 generation 均拒收。释放 context 同时销毁子对象。context 槽位元数据保留，全部几何/结果载荷释放。`test_abi.cpp::main/geometry2_matrix` 实际复用槽位后再尝试旧句柄，不仅检查不同 id。失败创建首先将整个输出清零；库内部创建/销毁唯一所有权对象，不跨 CRT free。全局锁仅管理注册表和访问串行化，错误保存在各 context，不使用全局 last_error。

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

两个状态都是独立的 uint32 值域：body OUTSIDE=0/CONTACT=1/OVERLAP=2；topology OUTSIDE=0/BOUNDARY=1/INTERIOR=2。合法 OVERLAP 是调用成功的数学 VALUE，不能读取 call_status 当是否重叠。输入点失败则数学 NOT_COMPUTED，两个状态均为 UINT32_MAX，避免伪造 OUTSIDE。

批查询先验证所有外层结构/尺寸/stride/容量、暂存结果再提交；结构或灾难性分配失败不改输出。合法批次外层 OK，非法数值点逐项失败，首项错误存 context。空批允许 NULL points/items。每批 ≤65536 点，body ABI ≤4096 点；几何核心另有确定性工作限额，超过 RESOURCE_LIMIT。测试有理查询每坐标 ≤4096 bytes；批次解析长度平方和 ≤67108864，耗尽后逐项 RESOURCE_LIMIT。

exact result 创建失败不改已有输出；成功创建的新 token 必须释放，不可把含活 token 的输出重复覆盖而不先释放。失败的 body/E 创建清全零 token。错误详情不依赖全局 last_error；C1 调用开始时清旧错误，逐项错误保留首错。context、Body/E 和结果不允许调用时并发重入。

`test_abi.cpp::geometry2_matrix` 守护尺寸、三态、部分成功、句柄槽位复用、跨 context、库释放、export 及有理测试入口；`tools/eab2_audit.py` 核查正式 DLL 无两个测试入口。所有 C1 计算入口重查当前线程 FP 合同。

构建身份由 `tools/eab2_audit.py` 调实际编译器 `/Bv` 获取版本，再与 `compile_commands.json` 的实际工具路径、`/MD /O2 /std:c++20 /fp:precise` 和无 `/arch:* /GL` 比对 DLL identity。受控源码在 `exact.hpp/c_api.cpp/fp_contract.cpp` 入口拒 `__AVX__`；geometry 经 exact.hpp 同样受控。此审计证明的是编译目标而非整个 CRT/STL 的二进制 ISA 纯度。


缓存关闭 `EAB2_ENTRANCE_NO_CACHE` 不改变 merge/compact 参数：每次全局或局部 JSON 请求从同一不可变 body/flags 创建临时 Entrance，导出后释放临时全局缓存；membership/topology 本身不物化全局缓存。`geometry2_matrix` 先全局导出、再局部查询，检查局部 `global_subdivision_materialized=false`，并检查重复导出语义不变；不是用关闭 merge 冒充关闭 cache。


## C1 可配置确定性工作限额

独立 `eab2_context_limits2`（struct_size/abi_version + 三个 uint64）与 `context_get_limits2/context_configure_limits2`，不扩写 C0 context_options。先 get 实际默认：max_work_units=50000000、max_elements=2000000、max_integer_bits=65536；三项输入必须显式正整数，0 拒收而不是隐含默认。配置只在该 context 无任何活 body/E/result 时允许；对象创建后冻结其几何限额，exact export 回显实际值。

C1 入口建立共享 `GeometryWorkScope`，嵌套几何调用/同批各点共用工作预算；Body/E 及方法各自保留直接 C++ 调用的范围。`IntegerLimitScope` 在 exact 算术层前置检查乘积/平移/有理交叉乘及加减的保守位长上界，并检查 owning 结果；超限抛专用 ResourceLimit，C ABI 转 RESOURCE_LIMIT，不产生几何否定。保守上界可能拒绝一个约分或消去后本可很小的结果，这是明确的资源拒签，不是数学误判。

这些位长限额不是整进程内存/墙钟预算，也不声称已证明 Boost 私有算法所有临时 limb 分配的物理峰值；前置算术界比单纯导出后验位长检查更强，但二者不能混称。C0 无 C1 scope 时保留原无固定几何预算的数学行为；scope RAII 在异常路径恢复，测试 `test_numeric.cpp::integer_budget_contract` 守护。配置与三类资源拒签门见 `test_abi.cpp::limits2_matrix`。十进制测试桥仍有独立固定协议工作预算。
