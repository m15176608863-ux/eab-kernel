# R15FIX 冻结后的只读复核

范围：tools/exact_construction_policy.json 相对 HEAD 的差分；R15FIX_evidence/static_review.py 与 static_review.json；README 新增段落及 docs/r15fix_design_sync.md。复核期间源码、tests、tools、docs 均未写入，只新增本证据文件。此复核由 O04 分工代理完成，**不是新的独立模型 G6 六路审查，也不是新鲜 worktree 验收**。

## 1. 结论

当前冻结版本未发现分析器放宽、整函数/整路径免检、原测试修改，或 README/本树设计同步新引入的全域正确/G6 已通过声称。当前新增数值构造准入与局部代码、测试目的相符。静态零诊断仍只表示当前有限检查器没有发现问题，不是数学证明。

## 2. policy 差分的机器核对

直接用 git show HEAD:tools/exact_construction_policy.json 的 JSON 与当前文件比较：

| 项目 | 结果 |
|---|---|
| schema / review_contract / imports / members | 全部逐值相同；没有扩大导入或成员白名单 |
| 原 waiver 数量 | 3035 |
| 当前 waiver 数量 | 3102 |
| 新增具体节点 | 76 |
| 原节点局部源码续签 | 79 |
| 删除已不存在节点 | 9 |
| 79 条续签变化键 | 仅 context、reason、review_evidence |
| 79 条续签未变部分 | path、function、rule、node、category、id |
| static_review.json 条目 | 155，正好等于新增 76 + 续签 79 |
| review 与最终 policy | 155 条对象逐项完全相同 |
| 当前源码 pin 核对 | 155 条 context 与当前 site_contexts 一致；具体 AST node 都存在 |
| 具体范围 | 25 个具名作用域，10 个文件；没有 path/function 通配符 |

9 条删除项均来自已移除的旧表达式：dilatancy 的三个浮点 d*direction；单体/多体合力路径各三个旧范数/显示相关节点。没有通过删除仍在使用的诊断规则来放行新实现。

新增生产路径共 16 条：

- R15-L0001：escape_height_brute 的具名域异常构造；裸 float 接口拒绝无法携带的 overflow 证书。
- R15-L0002/L0003：dilatancy 的两个 Fraction 差。源是 exact_height 与给定 delta 的精确 Fraction 编码，不是显示 h；手工准入有真实代数依据。
- R15-L0004/L0005：margin 早返回之前 exact_input(delta/band)，有限性验证，不是提前舍入。
- R15-L0006～L0016：bdda3d 字段 integer 分派与最终 extra tree。整数调用仅做 exact_input + 分母一检查；known continuous 的 schema 边界已独立受检，不把未知动态执行变成安全操作。

其它 60 条新增位于新测试：生产 API 的调用驱动、独立 Fraction 期望值最终 float、真实内部变异的 inspect/compile/exec 或故意早舍入。它们固定在这些测试的确切 AST 和 context；不授予生产代码反射/任意 callback 权限。

## 3. 静态审查脚本的使用边界

static_review.py 的 REVIEWS 是本轮人工审阅说明的作用域索引，不是运行时分析器白名单。脚本 approve 模式把 static_pending 的每一条诊断固化为具体 path/function/rule/node/context；最终扫描器仍按五元组逐项匹配。未在扫描时自动生成 waiver，也未添加整个 scope 的跳过分支。

**维护注意：这个证据脚本不是可无人审阅重复执行的未来自动批准器。** 因为 approve 会读取待处理诊断并沿既有 REVIEWS 索引生成新 pin，今后源码改动后不得仅因函数名还在 REVIEWS 中就重跑 approve 当成复核完成。当前冻结的 155 条已在本次逐类/逐项核对，未来新增节点仍需重新审阅。

## 4. 原门与分析器未改的字节证据

除 git diff --name-only HEAD -- tests 为空外，又用 R15FIX_evidence/tracked_before.json 中 SHA256 与实际当前文件字节比较，避免只依赖 git stat 缓存：

- 183 个原已跟踪 tests 文件：全部哈希相同。
- tools/check_exact_construction.py：哈希相同。
- tools/exact_construction_flow.py：哈希相同。
- tools/exact_construction_subset.py：哈希相同。

没有删门、放松断言、缩参数网格、增加 skip/xfail。新门是四个未跟踪的 test_r15fix_*.py 文件。static_local_final.log 为 `issues 0`；本复核不冒充仍在进行的最终全套结果。

## 5. 文档声明审查

README 新段落明确“工作树修复，待独立复审”，保留 M4a，不重宣 M0，不把本树绿称为 G6/新鲜树验收。设计同步明确：

- O01 合力为按 tol 筛选后的最终显示，不替代完整 LP 证书。
- O02 私有完整 jet 代数不改变一般 Dual 逐操作合同；sin callback 的 unit-seed 协议公开写明；libm/采样仍是声明的近似模型。
- O03 下溢允许必须由 exact_distance_squared 和 exact_closed 支撑；非有限/上溢拒答。
- O04 字段 schema 决定整数/连续域，没有放松连续量拒收。
- O05 height infinity 是显式显示例外，不是物理无界；裸包装拒答，profile 传递证书并对精确根差最终舍入。
- 外部设计正本按只读限制未写回；本树设计同步不是偷偷修改姊妹仓库。

未发现这些新声明超出本轮具体实现/门所承诺的范围。旧 README 内容未在本次全面重审，不能把本复核扩大成整仓所有历史科学声明均已获证。

## 6. 旧 reason 与 R15 renewal 的历史文字

部分续签 reason 保留旧 R12 说明，再追加明确标记 `R15 local renewal:` 的当前说明。例如旧 dilatancy 句称 d*direction 是浮点采样，当前 R15 尾注则明确 exact supplied delta*direction。当前源码和 docs/r15fix_design_sync.md 已一致指向后者。

这属于历史附记阅读歧义，不改变 gate 的 AST/context 收口，不构成运行时或测试放宽。本次不要求打破冻结去改 policy。**最终交付报告应明确：本轮 R15 local renewal 与本树 R15 设计合同优先；其中旧浮点采样描述是历史理由，不再描述当前 dilatancy 实现。** 未来整理历史台账时可独立消除这种叙述冗余，但不应把整理伪装成新的数值证明。

复核结论：当前冻结改动的上述静态准入与声明检查通过；最终全套结果由主执行报告另行给出。


---

## 7. 第二次冻结后的追加复核（保留首次记录）

本节针对第一次全套暴露的两个回归之后的最新冻结版本；前文首次复核的 3102/155 数量是当时事实，不覆盖、不回写。仍只读源码/tests/tools/docs，仅向本证据文件追加文字；第二完整套尚在执行，本节不预报其结果，不是独立 G6。

### 7.1 回归与 O01 的合同修正

读取第一次 full_suite_runner.log：最后行为 `R15FIX_FULL_SUITE FAIL: 12586 calls; wall=572.010s; failures_or_skips=2; source_drift=0`。其中原 `test_public_limit_single_and_multi_match_analytic_sliding_capacity[-1073]` 暴露仅因接触合力显示下溢而阻断原本成功的精确容量问题；另一个为 canon 文档关键词门。没有把这两个红隐藏成通过。

最新单/多体路径仍在 Fraction 上完成选列与合力和，新增：

- `exact_contact_forces`：保留同一 tol 选列后的完整 Fraction 分量元组。
- `contact_force_display_underflow`：对上述精确分量和最终 float 显示逐项比较，当且仅当存在非零精确分量显示为零时为 True。
- 最终 scalar_rational 使用 allow_underflow=True，并保留有符号零；上溢仍具名拒绝。

这不是把非零悄悄当零，也不把“按 tol 选列的显示”改称完整平衡证书。精确合力/显式标记保留了信息，lambdas 仍是完整静力证书；原有可表达容量域不因附带显示量缩小。成功域修复范围与 docs/r15fix_design_sync.md §1 相符，非最优结果的新增字段默认空/False，不伪造力证书。

新增 underflow 门含零、正负 2^-1100、正负 RN 临界 2^-1075、可表达 2^-1074，断言精确字段、flag 充要条件、完整显示值和符号位；另外保留最终 overflow 具名报错门。missing_certificate/silent_underflow 变异分别触发对应断言。此次替换的是本轮自己新加的“下溢只可拒答”门，不是删除/放松任何原仓库门；新合同是证书化显示例外，而非无证书容许零。交付测试改写台账应如实记这一调整。

可读回归日志：final_regression_repair2.log 为 `174 passed in 0.72s`；o01_final_verified.log 为 `48 passed in 0.15s`。前一个中间运行曾因参数化 tiny 同时有默认值导致 collection error，final_regression_repair.log 已保留；这不是数值失败，后续已修正测试声明。

### 7.2 最新 policy 再核对

相对 HEAD 的当前数量为 **3035 → 3103 = 新增 77 + 续签 79 - 删除 9**；非 waiver 顶层键仍全部逐值相同。79 条续签变化键仍仅 context/reason/review_evidence；不存在新增 scope/path wildcard 或整函数免检。

新增第 77 项为 R15-L0077，唯一 AST 为新测试 `test_contact_force_nonzero_final_underflow_has_explicit_exact_certificate` 的 `float(-tiny)`；它只构造独立精确期望值的最终显示，同时测试另行断言精确证书与 flag，符合 test oracle 的最终 RN 边界，不是批准生产代码中间转 float。

static_review.json 现为 **156 条**，逐项等于当前 policy 中本轮新增/续签差分；重新验证全部 156 条当前 context 与 AST 存在性均成功。O01 生产函数的新上下文已重新 pin，分析器逻辑没有变化。前述“证据生成脚本不能当成未来无人审阅批准器”限制仍适用。

### 7.3 原测试与分析器再次逐字节核对

再次读取 tracked_before.json 并对现存文件计算 SHA256：**原已跟踪 183 个 tests 文件零变化**；check_exact_construction.py、exact_construction_flow.py、exact_construction_subset.py 三个分析器源码仍全部等于最初哈希。此次并未通过修改原 -1073 成功断言或 canon 文档门来修复回归。

canon 顶部增加“静态工具仍是辅助检查，不是安全保证；局部 AST／源码 pin 与 Fraction 数据流合同不变”，与现有真实门一致，不构成新的静态证明声明。

### 7.4 schema 词法收紧撤回的边界

O04 只撤回 **字段分派之前一律套连续 binary64 输出域** 的词法限制；十进制 token 本身仍精确保留为 Fraction，负零和非标准 NaN/Infinity 拒绝合同保持。整数身份的分母一检查仍在；真正由 schema 消费的连续字段仍经过 scalar_rational 的非零/有限边界。因此已知连续量的拒收没有放松，不应误读成所有 JSON token 必须在解析阶段就拒绝大/小数。

未消费字段及未知 metadata 不因本轮文本自动获得新的物理单位、连续量含义或完整 schema 保证。这与当前设计同步“已知连续字段”和“未知 extra 保留既有树模型”的限定一致。O01 的有证书下溢显示例外属于力结果输出，与读取器连续字段的严格读入域分开，文档没有把两者混为一谈。

追加结论：最新 O01 证书化显示、静态 pin、canon 补句及 schema 边界未见上述范围内的新阻断；保留原测试/分析器字节边界通过。最终全套是否全绿及耗时仍以主执行报告和第二轮完整日志为准。
