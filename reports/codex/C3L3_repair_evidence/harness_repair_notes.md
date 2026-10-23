# C3-L3 返修：差分 harness 实现自检说明

本文件为执行方实现自检，不是 Claude 独立对抗核查结论。生产 C++ 与 `src/eab` 未由本子任务修改。

## 1. 比较边界

- 两侧 `exact_threshold` 都非 null：保持阈值、`attained` 及原有语义字段严格相等。非唯一坐标、基与多项式系数仍由数学定义核验，不逐基排序。
- 恰有一侧为 null：先对**两侧**调用 `verify_critical`；非空侧必须经过原始几何 LP 证书、Cramer 多项式恒等式和单侧 Sturm 延续核验。随后仅规范化 `exact_threshold`、`attained`、`threshold_certificate`、`threshold_proof_reason` 四字段。每实例记录证明侧、精确阈值、开闭、端点、受影响字段及合同核验标记。
- 端点、状态、二分停止原因、有效性条件、临界多项式列表存在及空非空合同均未全局忽略。双方非空的阈值与开闭不因该规则获豁免。
- 在整块阈值证书被规范化前，局部 `verify_threshold_certificate_contract` 核验 14 个必需字段，仅允许可选 `mechanism`；核 call/display/sensitivity/reason、根据接触冗余标记导出的 validity 条件，以及 OPTIMAL/UNBOUNDED 互斥附件。未知附加键不得被吞掉。证书数学值仍由前述独立数学核负责。
- 直接零闭阈不需要基延续，`threshold_proof` 与 `threshold_proof_reason` 均必须 null。一般延续证明 reason 必须为 `exact_basis_continuation`；分支角色和采样端点均绑定相应上下端点。

## 2. 新覆盖及来源

|族|精确参数或条目|查询数|
|---|---|---:|
|wide G1|3 取向 × 11 几何 × 10 个 μmax × steps 0..6|2310 critical|
|斜面 Farkas|坡度 1/4、1/3；steps 0..6、64|16 critical|
|二次根补充控制|2 种自由度；steps 3、48、64|6 critical|
|厚度|7 合法样本 + 18 厚度控制；25 来源条目、19 唯一模型|75 limit + 25 critical|

G1 的 μmax 为 `{1/8,1/4,3/8,1/2,3/4,1,3/2,2,3,4}`；11 组 `(t,h)` 明确写在 `wide_g1_specs()`。其中 t=1/3 的两组也逐个核原始顶点等 ABI 输入是否恰为 binary64，不将 1/3 本身作为 ABI 浮点输入。

两项 MAJOR 反例为 koureas 的 `(t,h,μmax,steps)=(3/32,1/16,3/4,4)` 与 `(3/8,1/4,3/8,1)`。闭式真阈值分别为 `2039/32768` 与 `119/512`，正常实现保守输出 null 阈值。它们作为具名查询纳入宽括号族。

斜面两例非零恒载导致下端 Farkas，数学开阈分别为 0、1/13；正常实现仍保守返回带证书括号，而非冒称精确阈值。二次根控制额外检查多项式 `μ²+2μ−1` 在括号两端异号，明确是本次补充控制，不冒称审阅原扫点的一部分。

历史 20 个合法增强实例由 `wide_enhancement_targets()` 持久保存参数与原始 ID：三个取向的零倾斜例各 6 个，另有 unreversed `(1/4,1/2)` 的 2 个。`acceptance_enrichment_inputs.json` 只作只读溯源投影并记录原始脚本及扫点 SHA；运行不读取审阅者 Temp。运行结束额外要求 20 个原始 ID 全部恰好出现、证明侧为 C++ 且逐例已核，不以总数替代身份追溯。

厚度生成器由 statics 子任务维护。harness 将模块与其 `SUMMARY` 指向的持久 tests/data 输入一并列入 source SHA 前后核；每条查询携带来源组、参数、输入指纹。6 份重复模型来自不同来源身份，不冒称 25 个互异几何。

## 3. 已执行证据及权威边界

- 定向宽族试运行完整执行 2332 critical，耗时约 407.97 秒；原始末行：`C3L3_DIFF limit=0 critical=2332 mismatch=0`。G1 三个取向各 770 个查询；历史 20 全部通过，扩大网格共 73 个非空侧为 C++ 的经数学核合法增强。
- 该试运行之后，内部只读复查指出被规范化阈值证书内的元字段可能被吞掉。本次已加局部合同门和零闭阈 proof 双 null 门。因此该宽族输出只标记为**定向试运行、非最终权威**。完整原 JSON 留在 ignored tmp，`wide_trial_summary.json` 留小摘要及 20 项处置。最终全族权威由主 agent 在最终源码冻结后执行，本子任务不重复宽族。
- 最终定向 pytest 原始末行：`45 passed in 4.38s`。原 21 个节点保留；新增合法双方向增强、缺上下延续、假 reason、双方非空严格比较、元合同损坏、零闭阈、覆盖计划及厚度域划分门。45 个 pytest 节点来自 28 个具名测试函数；覆盖计划测试只运行生成器，不重复 2310 次求解。
- 最终 AST 定向扫描：`C3L3_CHECKER_AST diagnostics=0`，不新增准入。最初 helper deepcopy 的诊断通过在测试内显式构造保守 wire 消除，没有搬移数值 oracle 来绕扫描。
- 源冻结 SHA：`tools/eab2_c3l3_diff.py` 为 `f9e66ec40e78107836f66b1e5368f465624975e08d1d42348559bb2d915f6649`；`tests/test_eab2_c3l3_harness.py` 为 `30d915573ecbff3cde817f8bb9f6479752bdca3d396415950585f94dfd75890d`。

内部真实 C++ continuation 变异 DLL 的定向红门由 critical 子任务负责；最终复查材料见同目录 `continuation_dll_red_gates.json` 与 `internal_checker_review.md`。这些均不是未经授权的第二路独立验收。

## 4. 文档编码订正

本文件首次写入时，PowerShell 到 Python 的文本管道把中文替换成了问号。修复前的字节核验为 UTF-8 可解码、无 BOM，但中文码点为 0、问号为 1161。此次仅以 UTF-8 安全补丁重写本证据文档；冻结的 tools、tests、fixture 均未修改。修后以实际 Unicode 码点检查中文内容，不能用显示效果替代字节核验。
