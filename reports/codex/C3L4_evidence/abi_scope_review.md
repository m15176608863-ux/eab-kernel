# WO-C3L4 ABI / 真实使用者要求的范围审查

> 后续处置：下文第 4.1 项字段类型冻结缺口已按根代理授权修复并验证；原始审查记录保留，现状见第 7 节。人工使用者与全工单验收边界没有因此改变。

审查性质：作者团队内只读交付自查，不是设计要求的非作者独立对抗核查；本轮仅新增本文件，未改合同、源码、测试或冻结状态，未运行长任务。

## 1. 结论

**目前可以证明的是“独立标准库 ctypes 消费脚本实际跑通发布 DLL”，不能证明“一名真实 TIA 人工使用者已经复跑并验收”。** 实际执行者是本工单 Codex，脚本也由本工单编写；证据中没有人工使用者身份、操作记录或验收确认。所有者/真实使用者人工复跑仍未发生，不能把脚本名字 consumer 或脚本隔离性等同于设计 §8.5 的人员退出条件。

**当前 ABI 布局及导出表有可复核的冻结基线，但不应无条件宣告整个 C3-L4 或 C3 发布已完成。** 全量 L4 严格结果仍有 32 项 tied_labels RED，且上述人工条件未满足。ABI_CONTRACT 顶部“发布 ABI v1 合同”、末尾“发布 ABI v1 冻结表”及 JSON status=FROZEN 应增加明确范围/待办限定，避免读者把局部技术基线当成发布验收已闭合。

## 2. 本轮核对的事实

- [隔离证据](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer_isolation.json)记录：10 个文件，Python 3.12，-I -S -X utf8，工作目录为最小字节副本；没有 src、差分 harness、pybind、姊妹仓库或测试 DLL。
- [consumer 结果](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer.json)：6 个 G1/G5 代表例、18 条敏感性，mismatch=0；包括 open/closed 阈值、μ=0 singular、滑移、切换、铰接。
- 本轮重新计算隔离清单对应的当前来源文件 SHA-256：独立脚本、C 头、发布 DLL、manifest、6 份 gzip 共 10 项均与隔离清单一致；没有拿旧版 DLL 的成功冒充新源码结果。
- 代码实际调用 body/entrance → assembly/contact → lock/first_order → limit → critical → sensitivity；L3 result token 保留到 L4 完成，种子从原始 geometry_seed 输入，存储 dA/db/dc 仅作输出比对。
- [发布 ABI 证据](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/release_abi.json)记录 31 个完整 PE exports、28 个 C 结构、capability mask=581501、0 findings。
- [严格标签取证](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/tied_labels_analysis.md)记录全量原始末行 C3L4_DIFF sensitivity=402 mismatch=32：formal 280 与 thickness 50 没有差异；T1b 72 中 16 个模型的 A/t 共 32 项标签差异。此处引用已经落盘的取证，不声称本轮又重跑 402 项。数值斜率等字段一致也不能自行抹去标签合同 RED。

## 3. 维度、步长与生命周期审查

对照 [公开 C 头](file:///D:/eab-wt/cx-c0/eab2/include/eab2/c_api.h)、[C API 实现](file:///D:/eab-wt/cx-c0/eab2/src/c_api.cpp)与 [ABI C++ 门](file:///D:/eab-wt/cx-c0/eab2/tests/test_c3l4_abi.cpp)，未发现当前实际接口遗漏显式参数/输出/通道数：

| 项目 | 已有合同/实现 |
|---|---|
| 参数/输出/通道 | P>=1，O=1，C=P；参数名唯一；JSON 回显计数与 [1,P] 形状 |
| 固定行主序 | vertices[P][V][2]、dead/live[P][B][3]、anchor[P][B][2]、mu[P] |
| 数量与 stride | 全部 value_count 精确核对，stride 必须等于 sizeof；乘法溢出检查在遍历前 |
| 身份 | 显式 body_ids/vertex_ids，完整排序与原始 ID 核对，不以默默排序掩盖错误 |
| 有效方向 | 每通道显式 0/1 正负方向标志与有效条件 |
| 结果绑定 | typed LimitResult2/CriticalParameter2；普通 JSON、错类型、跨 context、过期 token 拒收 |
| 原始问题 | 保留 ContactSet2 快照；critical 在证书精确 μ 上传播而非二分端点 |
| 结果拥有权 | 失败不改变输出；成功由 result/context 销毁；计算 FP 门与释放行为分离 |
| Jacobian 无值 | 非 smooth 或无认证单元为 null，不补零或伪装唯一梯度 |

公共输出沿用 owned exact JSON，并非调用方提供的裸 Jacobian 二进制输出数组，因此没有额外的 Jacobian raw-buffer capacity 可核；参数/输出/通道数及固定排列已在描述符、JSON 与 consumer 中明定。若所有者原意要求独立裸数组输出，则是尚需确认的额外 ABI 设计项，不能声称当前 JSON 输出也有一个未实现的二进制 buffer 协议。

## 4. 尚存的冻结门范围不足

1. **结构字段类型未逐项冻结（加强项，不是当前运行已发现错误）**。当前机器表存 sizeof、字段名/offset、版本，并存函数参数 ctypes 类型名称；没有存每个结构字段的完整 C 类型/指针目标/数组长度。仅相同偏移和大小不总能证明字段类型合同相同。本轮作了纯内存探针：把 eab2_string.data 从 char* 替换成 uint32_t*（不修改任何磁盘文件），header_contract 前后比较仍完全相同，输出 in_memory_pointer_target_type_drift_detected=False。建议后续经所有者允许后，为机器表增加结构字段类型及嵌套数组描述，并加此类同尺寸错误的负门。当前真实头文件并未发生该错误。
2. **数学 JSON 语义不是 PE/sizeof 门证明的内容**。字段含义、方向符号、标签完整性由语义/差分门守护；32 项 tied_labels RED 正说明导出门绿不能代替 L4 输出合同绿。
3. **consumer 是代表例，不是全部语料裁判**。默认不含 T1b 形貌 72 条，所以 consumer 的 0 失配不会覆盖上述标签问题。脚本比对完整链的关键结果字段与标签/有效条件，但不是全证书独立数学验证器；该职责在独立差分 harness，不能把二者混称。
4. **平台范围**。实际只验证当前 MSVC x64 DLL / Python 3.12 ctypes；不是跨工具链、跨操作系统或任意宿主内存安全证明。最小字节副本也不是所有者安排的 Git 新树。

## 5. 建议补充的最小文案（仅建议，未修改合同）

建议放在 ABI_CONTRACT 开头与冻结表前：

> 本表固定本轮已实现的 C ABI v1 技术布局与函数集合，已由独立标准库 ctypes 脚本对发布 DLL 的代表例复跑及 PE 导出门验证；这里的 FROZEN 只表示该布局基线固定，不表示 WO-C3L4/C3 发布验收已完成。当前 L4 全量严格比较仍有 32 项 tied_labels 未关闭；真实 TIA 人工使用者复跑、所有者最终验收与独立对抗退出条件仍待完成。不得将本表或 consumer 的 6 例 0 失配写成全工单 DONE。

可再给机器表添加不影响既有布局的验收元数据，例如 release_acceptance=pending、freeze_scope=implemented_abi_layout_baseline。若所有者认为“发布冻结”必须以人工条件和全量合同绿为前提，应将标题改为“发布 ABI v1 待验收冻结基线/候选表”；这涉及当前门强制要求 status=FROZEN 的口径协同，不能只改单个状态字符串让门失败或伪绿。

## 6. 建议交付口径

- 已完成：脚本实际调用链、无源码依赖的最小字节复跑、代表例精确比对、显式种子维度/步长/身份协议、公开函数/尺寸/能力基线。
- 未完成：真正人工使用者复跑与确认；32 项严格标签差异的所有者处置及验证；全工单剩余最终验证和独立退出条件。
- 本审查不能据此把整单升级为 DONE，也不建议因斜率相同自行放宽 tied_labels。

审查完成：仅新增本文件；未改 ABI_CONTRACT 或任何被测源文件。

## 7. 后续授权修复记录

根代理随后明确授权修复第 4.1 项，并要求保持实际 C/C++ 布局不变。已在 release validator 中直接从公开头原文读取每字段规范 C 类型，保留 const、指针层级与数组维度；机器冻结表新增 field_types。旧 sizeof、offset、版本、函数签名与能力项逐项断言未变，consumer 脚本及 C 头/DLL/全部隔离输入 SHA 均未改变，不需要重复消费查询。

新增负门在 pytest basetemp 中改写被解析的头文件输入，实际注入 char*→uint32_t* 与移除 const；逐个结构的 sizeof/offset 仍相同，但冻结比较必须报 structures mismatch。另核多层指针与数组规范类型。当前结果：26 passed in 0.12s；EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0。完整命令、日志与哈希见 [补门证据](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/abi_field_types_checks.json)及 [日志](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/abi_field_types_checks.log)。

ABI_CONTRACT 顶部及冻结节已明确技术布局基线不等于整单/人工验收；机器 status 保持 FROZEN，新增 freeze_scope / release_acceptance 限定。32 项 tied_labels RED 与真实人工使用者待办保持原样，没有通过文案或补门消除。
