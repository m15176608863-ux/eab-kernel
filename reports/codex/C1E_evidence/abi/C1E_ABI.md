# WO-C1E ABI 与 C0 小项实现记录

本文是实现者记录，不是 Claude 安排的独立对抗核查；全工单结论以 [主报告](../../C1E_report.md) 为准。

## 范围与回滚锚

只修改当前工作树 `eab2/` 和 `tools/eab2_audit.py/eab2_diff.py`，未改 Python `src/eab` 数学合同、未碰 vendor、姊妹仓库、Git 写操作或系统配置。回滚锚是所有者给定基线 `8269d1d`，没有自行 reset/checkout/建树。新增 C1 结构不改变 C0 `eab2_abi_info/context_options/context` 的布局。

## ABI 增量

| 类别 | 实现 | 守护 |
|---|---|---|
| 能力与尺寸 | BODY2/ENTRANCE2/QUERY2/EXPORT_EXACT/LOCAL2，test-only TEST_EXACT2；`get_c1_abi_info` 自报新结构 sizeof | `test_abi.cpp::main/geometry2_matrix`；audit |
| 环/E 生命周期 | bits 环创建；context/type/generation 校验；E 自有 body 副本；错误创建清 token | `geometry2_matrix` |
| 批量几何 | `query2_batch/membership2_batch/topology2_batch` 双三态；合法 OVERLAP 不是调用错误；失败点状态 UINT32_MAX/NOT_COMPUTED | `geometry2_matrix` |
| exact JSON | 全局和 0 处局部，data/byte_count/result token；库分配库释放；context 析构释放载荷 | `geometry2_matrix/child_context_reuse` |
| 测试入口 | canonical n/d exact 查询；显式 window/tol/cone_tol/seg_tol 的 covers JSON；正式 DLL 无这些符号 | audit；C1 Python harness |
| cache 开关 | NO_CACHE=4 保留 merge/compact；每次 JSON 请求的临时 Entrance 导出后销毁 | `geometry2_matrix`（build_06 已过） |

输入 batch 描述符先核尺寸/stride/乘法溢出/容量，计算暂存后再提交；外层失败不改输出。合法 batch 中数值错误逐项返回，保留首项 context 错误，不把无效位模式或坏点当成数学零/OUTSIDE。

## C0 遗留小项

| 小项 | 处置 | 验证 |
|---|---|---|
| 允许下溢显示状态 | 新 `EAB2_DISPLAY_UNDERFLOW_ZERO=3`；精确零仍 VALID；向量任一分量下溢则该项报告 UNDERFLOW_ZERO | numeric `input_and_dispatch`；ABI `numeric_status_matrix`；4483 例独立 Python 差分 |
| Python 裁判口径 | 仅 harness 显示层按允许/严格下溢调用判别；未改 construction 数学实现 | `tools/eab2_diff.py::expected` |
| 构建身份 | 审计实际 `cl /Bv` 版本与 compile_commands、DLL identity；不是只信 CMake 文本 | audit 最终 JSON 含 measured compiler_versions/commands/identity |
| AVX 编译拒绝 | exact.hpp、c_api.cpp、fp_contract.cpp 受控入口 `#if defined(__AVX__) #error`；geometry 经 exact.hpp | audit 源检查，实际所有 13 编译命令无 arch/GL/fast |
| 句柄世代 | context/子对象槽位真实复用，全库单调 generation；context id 重用后旧子对象仍拒收 | main/geometry2_matrix/child_context_reuse |
| 十进制工作预算 | 单有理文本≤4096 bytes；batch 总values≤65536，总字节≤4194304，长度平方和≤67108864；超限 RESOURCE_LIMIT | numeric解析门；ABI单项+aggregate工作预算门 |
| STL AVX2 说明 | README 明确测试 DLL 含运行时分派 AVX2 整数代码，ISA 身份仅指受控编译目标 | 文档及 actual compile audit |

## 最终已运行证据（build_06，含 cache / limits / 事务恢复）

```
EAB2_NUMERIC_TESTS checks=558 failed=0
ABI_TESTS: 764 assertions, 0 failures
C_HEADER_PRODUCTION_DLL checks=7 failures=0
C_HEADER_STATIC checks=7 failures=0
EAB2_GEOMETRY2_TESTS checks=700 failed=0
EAB2_LOCAL_TESTS checks=233 failed=0
EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS
EAB2_DELIVERY_AUDIT status=PASS findings=0 vendor_files=71 compiler_commands=13
```

- [build_06 完整日志](build_06.log)
- [C0 差分汇总](c0_diff_build06.json) / [原始末行日志](c0_diff_build06.log)
- [编译身份与交付审计](delivery_audit_build06_final.json) / [日志](audit_build06_final.log)
- [CTest](ctest_build06.log) / [命令与返回码](verification_build06.json)

初始失败是（1）geometry test 文件尚未落盘的配置输入错误；（2）ABI test 的 JSON schema 字面落后于双方约定；（3）新增故意跨 context 错误使旧“第二context从未报错”测试假设失效。分别修正输入/测试口径，没有通过放宽数学断言让缺陷过门。每次 build 保存独立完整日志，未拼接为成功证据。

## 边界与遗留

- C1 工作 ABI，不是 C3 稳定产品 ABI，不是宿主接入许可。
- 已实现独立 `eab2_context_limits2` + get/configure（capability=256），默认 work=50000000/elements=2000000/integer_bits=65536；三项必须显式正数，任一活子对象存在时拒重配；不改 C0 options 布局。Body/E 冻结设置，全局和局部 JSON 回显。C0 文本协议另保留固定工作预算。
- exact 位长约束在算术入口先核保守位长上界，再核 owning 结果；嵌套 scope 取不放宽的最小正上限；资源耗尽都返回 RESOURCE_LIMIT，几何 batch 保持逐项失败合同。此为算术工作预算，不是对 Boost 私有临时 limb/进程物理内存峰值的全量证明。
- `NO_CACHE=4` 的临时 Entrance 策略、generation 计数耗尽异常映射、三个可配置预算以及嵌套 scope 恢复门均在 build_06 通过。
- 全局规范集合、局部语义、近退化、元门与规模数据由主任务及 harness 提供；本分报告不代替那些验收。


## 构建依赖故障与修复证据

`build_05.log` 是保留的失败日志：MSVC 中文 `/showIncludes` 与 Ninja 依赖前缀编码不一致，旧 `test_geometry2_local.cpp.obj` 没有因 header 签名改变而重编，产生旧构造函数 LNK2019。没有通过恢复旧接口绕过。CMake 增加全部受控头（含 generated identity）的显式 OBJECT_DEPENDS；`build_06.log` 实际重新编译本地测试并成功。

最终 audit 对 compile_commands 的 13 个 object 逐个运行 Ninja `-t query`，核验每个受控 header 都在依赖图中（JSON `explicit_header_dependency_checks`）；不依赖主机诊断语言。审计首次把构建目录内生成头的相对路径误报为缺失，修正路径归一化后独立保存 final PASS；没有修改编译源码或 DLL。所有失败日志未拼接为成功证据。

```
100% tests passed, 0 tests failed out of 6
Total Test time (real) =   0.21 sec
```

实现/头/文档和证据总清单见 [交付清单](manifest.json)。本分任务完成；全工单 657 正式差分、10000 近退化、全档 Python、独立核查等由主任务最终汇总，不从本 ABI 单测推定。


日志编码另见 [编码审计](encoding_audit.json)：全部现存文件严格 UTF-8、无 BOM/混行。`build_05.log` 的 6 个 U+FFFD 是 UTF-8/errors=replace 捕获中文原生诊断时的替换；原始 native 字节流未留存，不伪造原始 SHA。成功 `build_06.log` 无替换字符。所有现存文件各自有 SHA256；这些日志不是逐字节 native 输出归档。
