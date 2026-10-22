# eab2 C0 工作 ABI 合同

这是设计 §5.4 的 C0 工作接口，不是 C3 发布产品 ABI 冻结。公共 C 头只含固定宽度整数、长度与指针；无 C++ bool、STL、Boost、异常或 enum 布局。全部入口捕获 C++ 异常。调用方仍须提供真实有效且足够大的、互不重叠的描述符和缓冲区；本单不是恶意地址/宿主接缝加固。

## 正式导出与能力

`eab2_get_abi_info`、`eab2_self_test`、`eab2_context_create`、`eab2_context_destroy`、`eab2_context_get_error`。ABI version=1，`struct_size` 必须精确匹配；版本不匹配返回 UNSUPPORTED。构建身份包含工具链、ISA 与后端，由构建系统生成。`get_abi_info` 总是报告已实现能力；`requested_capabilities` 的未支持位完整返回 `unsupported_capabilities` 并返回 UNSUPPORTED。C0 正式 DLL 仅有 CONTEXT 能力，没有 rho/SE2/LP2 或数值发布入口；不提供占位时间、距离或承载力。

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

`mathematical_status`: NOT_COMPUTED=0、VALUE=1、UNPROVED=2、NO_EVENT=3、OVERLAP=4、INFEASIBLE=5、UNBOUNDED=6。C0 只产生 NOT_COMPUTED/VALUE，其他类别冻结表示但不是已实现能力；不得将 UNPROVED 转成 false。`display_status`: NOT_AVAILABLE=0、VALID=1、RANGE=2。逐项失败 `bits_count=0`，**不写 bits 缓冲区**，不能读取其旧值当结果。RANGE 是显示失败标记，不伪造可导出的精确证书；C0 测试桥不导出该证书。

## 生命周期与错误

context 是 `{owner,id,generation,type,reserved}` 的 32 字节 token，不是可供调用者释放的指针。C0 无子对象，context token 的 owner 必须等于 id；每次查表还核类型、世代与 reserved。id 单调分配、不复用；销毁后 token 失效，重复释放拒收；混合两个 context 的 owner/id 拒收。后续对象应沿用所属 context 校验，不在 C0 创建占位对象。失败创建首先将整个输出清零；库内部创建/销毁唯一所有权对象，不跨 CRT free。全局锁仅管理注册表和访问串行化，错误保存在各 context，不使用全局 last_error。

错误由 context 持有 code/field/index 和消息，失败批次记录错误；正常批次将错误清空；逐项失败记录第一个失败的下标。`get_error` 不改变既有错误。两阶段获取消息：NULL/0 查询所需容量（含 NUL），再由调用方分配，库只复制；不足容量不写消息。消息长度上限 511 字节，field 上限 47 字节；错误 code/index 不截断。context 销毁后错误也失效。

## 测试批协议

输入为显式 UTF-8/ASCII 文本片段 `data/length`，无隐式终止符扫描；binary64 为最高位在前、小写恰 16 位 hex，−0=`8000000000000000`，NaN/Inf 拒收；有理串约分 n/d、d>0、零 0/1。输出 `uint64_t` 是位模式整数；序列化时格式化为 16 位小写 hex，不按主机字节序解释文本。

所有数组 stride 必须**等于对应元素的 sizeof**；数组乘法溢出、空指针与非零长度不一致、非零 reserved、未知 flags、容量不足均拒收，不截断/补零。item_count=0 可用 NULL items，仍需合法结构和 stride。测试协议确定性上限：65536 items、每项 65536 values、每文本 1048576 bytes，超过返回 RESOURCE_LIMIT。单个输出 capacity 可大于实际数量；计算后容量不足为逐项 INVALID_INPUT。

先验证全部描述符，再暂存全部计算结果，最后提交输出。结构错误/环境错误/批次分配失败：外层返回失败，输出描述符与 bits 都不改。结构正常：外层 OK，`output.item_count` 等于输入数量，每项分别返回状态；成功项复制 bits，失败项保留 bits 原存储并清 count。临时内存全部由库 RAII 释放，调用者始终拥有输入/输出缓冲区。禁止输入与输出重叠、描述符与 bits 缓冲区重叠。

测试 op 编码见 `testing.h`；数学参数形状由 `numeric.hpp` 的测试桥规定。decode 在 ctypes 只检查位回环，精确有理分子/分母由静态核心测试核验，不将位回环冒充完整解码证明。

## 浮点环境

`self_test`、创建 context、每次 numeric_batch 都核当前调用线程。首先核 MXCSR 第 7–12 位全屏蔽、FTZ/DAZ 关闭及 RN 模式，再核 binary64、ties-even、有符号零、渐进下溢和同 TU noinline 非 volatile 中间乘积的收缩探针。失败返回 FP_CONTRACT；不切换宿主控制模式。成功探针产生的 sticky flags 恢复为调用前原值，已有 flags 同样保留；该恢复不是替坏环境修复配置。调用方不得在调用期间异步修改 FP 环境。

`test_abi.cpp::environment_matrix` 实际注入 FTZ、DAZ、三种非 RN、分别解除 7–12 六个屏蔽位，验证 self_test/create/batch 都拒绝、失败输出不变，且调用前后完整 MXCSR 和 `_controlfp_s` 读值不变。默认 SSE2 无 FMA，因此有限收缩探针不是识别任意伪造构建配置的万能证明。
