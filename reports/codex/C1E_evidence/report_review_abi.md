# C1E 主报告 ABI / C0 / 资源 / 构建作者文档 QA

范围：只读审阅 `finalize_report.py` 的相关段落，对照已冻结 C++ 源码、ABI 合同、build_06、C0 差分与最终 audit；未修改脚本或源码。这不是 Claude 指派的非作者独立对抗核查，也不替代其结论。

## 总结

相关已实现能力与数字总体有当前证据支持，未发现把工程验证、稳定产品 ABI、全域证明或物理内存峰值伪称为已证的表述。报告明确 PARTIAL、C3 未实现、独立核查/新鲜树待办、开工全档缺失，边界正确。

当前实际核对：numeric 558、ABI 764、geometry 700、local 233；C 头两路各 7；C0 差分 4483 cases / 6003 bits / 0 mismatches；build06 audit PASS / 0 findings / 13 compiler commands。当前测试 DLL SHA256 为 `dd64762305f62b56b3aa985f1988b36bc619d1dbc367942ae6a9c40fca66dbf8`。

## 建议改两处表述

1. **第4节 cache 行的“每次请求”过宽。** 实现仅在 `result_export_exact` / `local_origin2_exact` 的全局、局部 JSON 请求创建临时 Entrance；membership/topology 本来不物化全局缓存，不为每个请求重建；test-only covers 也不经过该临时构造路径。建议写：

   > NO_CACHE 对每次全局/局部 exact JSON 导出创建同参数临时 Entrance 并在导出后销毁；membership/topology 本身不物化全局缓存，不冒充关 merge。

   证据：`c_api.cpp::export2_impl` 对照 `query2_impl/eab2_covers2_exact`。

2. **第4节资源失败恢复最好限定“被测构造/导出路径”。** 当前句子“重复低预算调用不能靠渐进缓存绕限”有具名事务测试与实现支持，但直接读作所有未来 API 的全域性质略宽。建议写：

   > 在被测的 raw/skeleton/subdivision/export 构造路径，RESOURCE_LIMIT 后回滚本次新缓存；具名重复低预算回归确认不会通过渐进保留新缓存把该失败改成成功。

   不必削弱已经通过的实际门；只是避免有限测试被读成任意未来 API 的普遍证明。

## 准确且建议保留

- C0 原结构布局未改、C1 追加结构/函数；工作 ABI 与 C3 稳定发布 ABI 分界。
- 双三态与调用/数学状态分离；几何 JSON 的 -1/0/1 与 ABI 的 0/1/2 明确映射。
- get/configure limits 的正数约束、实际默认 50M / 2M / 65536、活子对象禁改、对象冻结及 JSON 回显。
- UNDERFLOW_ZERO 是显示状态细分；独立 Python harness 调整显示期望，不改 src/eab 数学实现。
- 槽位复用后的全局单调 generation，计数耗尽转 RESOURCE_LIMIT。
- 算术前保守位长上界、结果检查与嵌套不放宽；明确不保证 Boost 临时 limb 或进程物理内存峰值，避免过称。
- 编译目标 ISA 与 STL 运行时 AVX2 代码区分；实际 cl 版本、13 编译命令和逐对象显式头依赖均有 audit 支持。
- build_05 失败、6 个替换字符且原始 native 字节流未留存；build_06 成功且无替换字符；失败日志没有被冒充成功证据。

## 报告生成器的防漂移建议（不影响当前证据为绿的事实）

`technical_ok` 当前没有直接读取 C++/CTest/C0 差分返回码，也没有把 DLL hash 跨 diff、audit、C0 verification 做显式相等断言。当前文件人工核对均绿、DLL 哈希一致，因此当前叙述可据现有证据成立。若要让以后重跑脚本本身成为更完整的汇总闸门，可纳入 `abi/verification_build06.json` 的终态命令与最终 audit、C0 diff 状态，并显式检查它们与 diff_final 的 DLL SHA256 一致；不要把保留的第一次 audit 路径规范化误报计为最终失败。

本次未重跑 H1、未重新编译、未改受冻结源区。
