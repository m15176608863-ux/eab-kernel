# WO-C3L4 工作 ABI 入口草案

状态：入口设计，尚未发布冻结。真实 ctypes consumer 完整复跑和导出门通过后才更新发布冻结表；本文件不声称已实现或已验证。

## 保留与新增

- 旧结构尺寸、函数与能力位保持不变。新增 EAB2_CAP_SENSITIVITY2=524288，不挪用 RHO/SE2/LP2 保留位。
- 新入口 eab2_get_c3l4_abi_info(info) 与 eab2_evaluate_sensitivity2(context, base_result, input, output)。不增加 evaluate_sensitivity 别名。
- base_result 为已有 result token；内部必须持有 LimitResult2 或 CriticalParameter2 typed payload。普通 JSON result、错类型、跨 context、过期世代拒绝。
- L3 保存 typed payload 和 ContactSet2 快照。原 body/assembly/contact 释放后仍有效；L4 不重解 primal/critical，只解敏感性需要的 LP。

## 描述符

所有字段固定宽度，header 为 uint32 struct_size / abi_version。

1. eab2_string_array：uint64 value_count, value_stride；const eab2_string* values。exact seed 必须 canonical reduced n/d、正分母、零 0/1；元字段为严格 UTF-8 非空文本。
2. eab2_sensitivity_vertex2：eab2_string body_id；uint64 vertex_id，使用原始输入顶点 ID，不是 CCW 反转后位置。
3. eab2_sensitivity_channel2：header；eab2_string parameter；uint32 positive_direction_valid / negative_direction_valid（只能 0/1）；eab2_string_array validity_conditions / tied_labels。
4. eab2_sensitivity2_input：header；uint64 parameter_count / output_count / channel_count / body_count / vertex_count；uint64 channel_stride；const channel* channels；eab2_string_array body_ids；uint64 vertex_stride；const vertex* vertex_ids；eab2_string_array vertices / dead / live / dof_anchor / mu。

v1 单目标、多参数通道：P>=1、O=1、C=P；参数名唯一。body_ids 与快照按 UTF-8 body ID 排序完全相等；vertex_ids 与按 (body_id, original_vertex_id) 排序的全部顶点完全相等。拒绝缺项、重复、乱序、跨体错误，不静默重排遮蔽调用方错误。

固定连续行主序：vertices[P][V][2]、dead/live[P][B][3]、dof_anchor[P][B][2]、mu[P]。value_count 分别严格等于 P*V*2、P*B*3、P*B*3、P*B*2、P；每次乘法先查溢出。value_stride 必须为 sizeof(eab2_string)，channel_stride / vertex_stride 同样精确匹配 sizeof。声明非零长度须有指针；禁止截断或补零。

caller tied_labels 只接受 UTF-8 字符串。正式语料 caller ties 全为空，result ties 含嵌套 ColumnLabel2；自动临界标签由核心生成，variant string/ColumnLabel2 导出保持嵌套结构，不能变成 JSON 字符串。

## 数学绑定和输出

- finite 在 typed LimitResult2.problem 上精确传播。
- critical 在 threshold_certificate.problem 的精确 μ 上传播，不能拿 mu_max 或 bracket 端点替代；自动传播 threshold_mu_seed。
- 缺少临界证据时仍核全部输入结构、种子身份和形状，交 evaluator 返回无斜率 unresolved。
- 输入不含 dA/db/dc；C++ 从原始几何传播这些导出字段，由独立 Python harness 核验。
- 输出沿用 exact_result 原子发布与库侧释放；失败整个输出不变。计算检查 FP，释放不检查 FP。
- JSON 显式 parameter_count/output_count/channel_count，channels 数组每项含 parameter、完整 result、derived_seed、threshold_mu_seed（不适用为 null）。输出 Jacobian 采用 [output][channel] 固定行主序，只有 smooth 认证值填精确有理，其余为 null；不得补 0。

## 私有接口

namespace eab2::statics：LimitSeed2{Matrix dA; Vector db,dc; string parameter;}。SensitivityOptions2 含 parameter、variant 标签、validity_conditions、正负有效方向、lp_options。

两个单通道 overload：
- evaluate_sensitivity2(const LimitResult2&, const optional<LimitSeed2>&, const SensitivityOptions2&)
- evaluate_sensitivity2(const CriticalParameter2&, const optional<LimitSeed2>&, const optional<LimitSeed2>& threshold_mu_seed, const SensitivityOptions2&)

ABI 批通道循环上述入口；geometry helper 另由根代理实现，不改变数学算法。

## 待执行验证

- 新 ABI C++ 门：size/version/stride/count/积溢出/空指针、ID 乱序重复、UTF-8/有理非法、方向标志、错 token/跨 context/过期、原子失败、FP、释放、至少三通道互异。
- 独立 stdlib consumer 用 python -I，只加载发布 eab2.dll，不导入 src/eab 或差分 harness。默认 g1_unreversed_t1、g1_slender、g5_n3_mu0/1/2/3。
- 从 manifest/gzip/原始 bits 建所有 body 与 pair entrance，在原点双三态核对，继而 assembly/contact、lock/first_order、limit、critical、sensitivity；保留 L3 token 到 L4 结束。
- PE 门用 stdlib struct 完整枚举导出表，与头文件全部 EAB2_API 声明和发布冻结表精确一致；逐项核 capability、结构版本/尺寸，拒 test-only 泄漏。现 hasattr 白名单不足以证明全表相等。
- 构建 .\eab2\build_eab2.bat，自带 CTest、TEMP 在 eab2/build/tmp；不安装、不下载、不做 Git 写操作。