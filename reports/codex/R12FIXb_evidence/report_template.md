# WO-R12FIX-b 交付报告

日期：2026-10-13（Asia/Singapore）。工作树：D:/eab-wt/cx-e2。HEAD：0ce65a44c9c26d99411cee68d7300e7b5521bb40，未提交。

## 1. 结论与逐项验收

**本轮为 PARTIAL，不是工单验收完成。** 局部锁、数据流准入和新增牙已落地；最终静态门 **0 违例**，完整 **11508** 节点全绿，原 **11368** 节点全部保留，新增 140。

例外从 16936 减为 **2365 条局部规则站点排除**，仍超过 200：1755 个不同 AST 站点、557 个作用域，src 771 条、tests 1594 条。
**0 诊断与全套绿是在这些排除生效后取得，不表示所有站点已证明不存在先舍入再构造。**
642 条证明缺口未关闭；467 条近似／名义范围涉及实际舍入；16 条数值动态规则记录仍待改写。
过渡清单是 root 显式记录的遗留排除决定，**不是机器推导或独立 G6 批准**；任务审阅者批准的数值 waiver 数为 0。

| 要求 | 结果 | 证据与边界 |
|---|---|---|
| 1. 站点及本地作用域锁，不锁整库 | 通过 | 真实清单局部失效、无关编辑门通过 |
| 2. 扩大安全子集、≤200、逐条安全说明 | 部分完成 | 已扩大子集；2365>200，近似范围不能冒充“为何无提前舍入”的证明 |
| 3. 数值动态写法改写 | 部分完成 | 已直接化的路径见 §4；16 条规则记录和公开诊断边界仍保留 |
| 4. 默认拒绝及原有牙 | 所列门通过 | 四种真实 cone 植入、新高阶形态及关闭拒绝层的反向牙保留 |
| 5. 三道可维护性门 | 通过 | 仓库副本注释绿；本函数失效红；新增禁止函数红 |
| 6. 全套、节点、指针、文档 | 通过 | 11508 唯一节点，收集／执行集合精确一致，指针工具已 apply |

## 2. 局部机制与保证范围

实现：[主扫描器](file:///D:/eab-wt/cx-e2/tools/check_exact_construction.py)、[源码流分析](file:///D:/eab-wt/cx-e2/tools/exact_construction_flow.py)、[闭集与局部 pin](file:///D:/eab-wt/cx-e2/tools/exact_construction_subset.py)、[当前 policy](file:///D:/eab-wt/cx-e2/tools/exact_construction_policy.json)。

- 每条记录 id、path、function、rule、node、context、category、reason、review_evidence。node 是不含行号的完整 AST 指纹，context 是所在函数／最小封闭作用域源码 SHA-256。
- 函数 hash 包含签名、装饰器、体内及尾部缩进注释；统一 LF/CRLF 后计算。模块／类的兄弟定义分别锁定，外层函数包含嵌套定义。
- 条件分支中同一限定绑定的多个定义锁为本地候选源码组，不能由最后一个覆盖；不混入无关函数。
- 删除整库 dependency snapshot 及旧无 hash 的函数级 EXCEPTIONS。imports/members 是有限结构词汇，不是全库源码依赖锁；新本地模块 import 不要求重建全库清单。
- 无关文件、同文件另一独立函数修改不失效。本函数源码变化、删站点／函数或 AST 不匹配报告 closed-stale-waiver；改写已安全也须明确清理陈旧记录。
- scanner 只读清单，不生成或续签例外。证据中的初次安装／纠正脚本仅是固定输入、有限 ID 的迁移记录，**不是后续重建全库豁免的工作流**。

自动准入包括：已知 int/Fraction 算术比较，统一构造调用，不流向开方／范数／单位化／几何差分的普通 float 运算，已知类型纯函数，有限源码直调／记录字段，固定 struct 格式及 int count 等。
浮点输入模型与算术派生浮点区分，Fraction(已舍入值) 不清除来源；非整数幂和 math.pow 也按潜在根构造追踪。
未知高阶、反射、运行时协议等，不靠“名字看起来可信”放行。

**这不是任意 Python 的证明，也不是算法数学正确性证明。**
沿用 R12 的测试边界：顶层 test_* 驱动及模块 scaffold 不在新增闭集前检保证内，仍受旧舍入检查；独立 helper/oracle 继续受检。
源码准入不能替代独立几何 oracle。
局部 pin 只防本节点／作用域变化静默续用，**不证明将来被调依赖的语义**；callee 原位重扫，人工排除路径仍受人工假设限制。
整份文件删除后的残留记录还需清单盘点，不能把按现存源码扫描称为完整文件删除审计。

[现行设计同步](file:///D:/eab-wt/cx-e2/docs/r12fix_design_sync.md) · [最终安装机制复核（非 G6）](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_installed_manifest_review.md)。

## 3. 例外条数、分类与代表

| 类别 | 条数 | 代表及真实边界 |
|---|---:|---|
| 结构、标签、数据协议 | 276 | L0001 canonical_key 只排标签；L0249/L0252 的 c.label() 是标识，不是排序 lambda |
| 给定输入模型／最终输出边界 | 639 | L0004 CSV 到 binary64 建模不声称十进制无损；L0611 以显示法向／点作为新接触模型，不恢复原 exact 见证 |
| 尚未关闭的证明缺口 | 642 | L0003 对象字段／参数摘要；L0037 整数幂分支的 Fraction 导数链，人工说明不等于机器已证 |
| 近似／名义报告范围排除 | 467 | L0028 普通 Dual 导数浮点快路径；L0476/L0514 名义候选与报告窗口，存在实际舍入 |
| 公开诊断 callable 边界 | 5 | central_difference 的 f(tp)/f(tm) 及诊断链；不证明任意外部 f |
| 测试执行／故意缺陷装置 | 320 | L0848 读取被测 API；compile/exec 变异体是重引缺陷，不是安全数值算法 |
| 数值动态改写遗留 | 16 | Frame.poly、_T、_g0_exact_affine、_map_back/_transform，及 q 的 getattr 字段反射 |
| **合计** | **2365** | **不是 2365 条机器安全证明** |

[最终逐站点决定账本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/local_review_decisions_release.json) · [分类统计及代表](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/local_manifest_statistics_release.json)。
每条关联表达式、限定作用域、理由及审核证据。39 条 metadata 已按当前源码更正或细化；并非每条旧理由都失实。
不能诚实说明“不存在提前舍入”的条目保留为证明缺口或范围排除，不编造理由；这是要求 2 未完成的实质。

未压到 200 的原因：有限摘要对对象字段、别名、分支类型、参数敏感流向和独立 oracle 包装仍不足；此外确有近似诊断和故意缺陷测试。
这不是“无法进一步实现”的结论，而是本轮尚未关闭的工作；没有用扩大可信函数名单或函数级白名单强行压数字。

当前 policy SHA-256：**@@POLICY_SHA@@**。
初次迁移后的新增排除数 **0**，作用域 hash 续签数 **0**；历史清单及所有明确纠正 delta 保留。

## 4. 已改写哪些动态形式

- 数值源码批涉及 22 个 src 文件：108 处已知数值 map 改显式生成式（src 90、独立 helper 18）；26 处 callable 形参／容器／alias 执行改命名直调。
- 16 处 numerical-key callback 改先算 key，再以数值 key 和唯一序号选择对象；min/max 保留首个平局获胜。LP 私有 ray callback 改数据元组／None，未改公开 API。
- 三处 exact comparator 的 cmp_to_key 改局部稳定插入循环，比较器 AST 不变，不让生产与 oracle 共用几何原语。150 次 ×128 个 Fraction 方向对照，值序、同角对象身份序一致。
- geom3 缓存字段 setattr、margin Cover3 反射打包、LimitContact 字段读取改显式字段。实现身份仍作缓存 key 数据，但不从身份参数调用数值函数，保留 monkeypatch 牙。
- tests 另直接化 25 处数值 map、17 处数值 lambda、两组 factory 表执行及 margin 采样 helper；四个 PERF helper 文件也直接化。既有名称和参数网格保留。
- r6/r7 两个源码变异锚点只同步新表达式拼写，缺陷与目标守护断言不变；提前舍入仍被原断言抓到，实测 0.0 != 1e-09。

[数值改写明细](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/dynamic_rewrites.md) · [test helper 变更](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/test_helper_rewrite_changes.json) · [factory／采样等价](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/test_factory_data_equivalence.json) · [PERF helper](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/flow_structure_and_perf_rewrite.md)。
各批文件可能重叠，**不简单相加**。最终逐文件变更和前后 SHA 见 [CHANGE_INDEX](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/CHANGE_INDEX.md)。

残留风险：稳定插入排序从 O(n log n) 变为 O(n²)；现有测试通过不等于大扇区性能验收。

## 5. 可维护性三门：真实清单红／绿

1. **无关文件注释绿**：在 evidence 的真实仓库副本先扫描零违例，给 src/eab/__init__.py 加注释，再扫仍零违例；policy 不更新。对应 test_unrelated_source_comment_keeps_real_repository_gate_green。
2. **仅本函数失效红**：最终真实 policy 中，给同文件的 _pair_generic 函数体插注释，恰 6 条已登记排除记录失效，其他 2359 条 context 不变；9 条诊断只属该函数。
   给 _pair_ve3_wedge 插注释则恰 12 条失效，其他 2353 条不变；15 条诊断只属该函数。不是以全库 hash 变化冒充局部红。
3. **新禁止函数红**：新增 math.sqrt(value*value) 的内存函数，出现 2 条目标拒绝，既有 approved/context 全不变；另有 norm(vector_rational(...))、getattr 和新 HOF 门。

[最终真实清单探针 JSON](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/real_policy_locality_probe.json) · [可重跑脚本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/real_policy_locality_probe.py)。
仓库副本注释门也在最终全套执行并通过。另测了兄弟方法、嵌套作用域、注释 hash、删除／安全改写后的陈旧记录、伪 AST、同名分支定义 pin。

## 6. 默认拒绝的牙与实际红绿

- 四种真实 cone_intersection_margin 内部植入保留：map_norm、map_sqrt、iter_callable、pop_callable。运行结果由最小 subnormal 变成 0；独立 Fraction 中点平方证书给真值。
- 自造 never_seen_before_731、新嵌套 dispatch、partial、lambda、容器、反射、未知成员等拒绝格子保留，src 和独立 helper 两路径覆盖。
- test_l01_disabling_closed_pass_trips_real_cone_rejection_assertion 在 scanner 内撤掉拒绝层，红在 **G6L-01 closed-subset rejection assertion**，不是添加假诊断或脆弱顶点断言。
- 新增 140 节点：safe 27、adversarial 50、maintenance 9、structure 23、final-mechanism 31；最终全部执行。

原节点全部保留，但不是所有历史断言逐字冻结：R9 的终端 scalar_rational(a-b)、R10 的直接 Fraction 列表累积、
R11 的明确不同列表重绑定按新安全子集改为准入；对应 map、高阶和其他不安全路径仍拒绝。
R12 历史 changed_dependency 节点名保留，断言从“全库依赖改变就失效”改为本工单要求的局部性。
这些是合同更新，不是删除格子；R10 自展开属性别名的目标拒绝断言则原样保留。

| 真正红证据 | 缺陷与目标 | 修复后 |
|---|---|---|
| final_mechanism_red.log：9 failed | 8 个幂根 CFG 状态漏传 + 同名 pin 未失效 | 永久门与全套通过 |
| final_augpower_red.log：4 failed, 9 passed | 增强幂赋值未接入同一 sink | 永久门与全套通过 |
| final_mechanism_call_return_probe.json：12 格空诊断 | callee 返回污染在摘要／CFG 边界丢失 | 对应 12 格永久门通过 |
| final_nested_exit_red.log：4 failed | 不可达赋值清洗嵌套退出状态 | 最近循环转移快照修复后通过 |
| final_with_prefix_red.log：2 failed | 被抑制异常前的污染丢失 | With 前缀合并后通过 |
| 首轮全套 R10 属性别名断言红 | 裸 sqrt_rational 未被新 flow 当 sink，非超时 | 原断言不变，alias_intrinsic_green.log 为 132 passed |

[机制复核与红绿说明](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_mechanism_review.md) · [裸构造接线复核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_bare_construction_wiring_review.json)。
历史 final_call_return_red.log 实际是绿日志，不按文件名冒称红；其修前证据是实际空诊断 JSON。
所有上述针对性任务复核 **均不是六路独立 G6**。

## 7. 最终全套、原样最后一行与耗时

[完整汇总](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/full_suite_release/summary.json)。
采用 **4 个普通 pytest 进程按完整文件分片**，不是局部子集，也不伪装成单进程输出。
收集集合 = 分片收集并集 = 执行并集，11508 个唯一节点，原 11368 全包含；
所有 setup/call/teardown 均 passed，0 skip/xfail。src/tests/tools、policy、关键文档和 runner 前后 SHA 无漂移。

四个进程最后一行，逐字原样：

@@PYTEST_LINES@@

完整分片墙钟 **@@WALL@@ 秒**；收集另用 @@COLLECT@@ 秒；四进程耗时之和 @@SUM@@ 秒。
没有杜撰不存在的单进程 pytest 最后一行。

最终静态 CLI 最后一行：

    exact construction AST gate: 0 violation(s)

exit 0，墙钟 @@STATIC_WALL@@ 秒。[日志](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/static_gate_release.log)。
fix_canon_ptrs.py --apply 初轮改正 13 个指针；最终复跑原样：

    0 rewritten; 0 kept
    applied

[最终指针日志](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/canon_apply_release.log)。

### 未隐藏的失败及约束偏差

- 首次安装后为 **168 违例**：提取器以行号和源码反找 AST，165 条 Call/Yield 误绑到外层 Expr（168 实际位置）。门保持拒绝，没有扩大匹配来接受错指纹。
  更正逐项核对相同 path/function/rule/source/line/context 及直接 AST 父子关系；0 作用域 hash 刷新、0 新排除。
- 首轮完整测试为 **3 failed、11505 passed**：两个真实静态基线门及 R10 sink 接线门；进行中的 docstring 修改也被前后快照捕获。
  首轮不算绿，证据完整保留；最终重新冻结、重新全套，不只补跑失败节点。
- 原 34 条动态类别逐项复核，18 条重分类；另 5 条 src 理由错配，共 39 条 metadata 更正。
  其中 5 条中文一度被 PowerShell ASCII 管道损坏，已用 UTF-8 直接文件修复并查 codepoint；最终对应问号串／替换字符为 0。
- **一次违反只写本树的偏差**：早期定向 pytest 未指定 basetemp，在系统 TEMP 的 pytest-1059 建立 42 个临时 CSV 夹具。
  已只读核查，未清理／改动外部文件。后续用本树 basetemp/no-cacheprovider；最终 runner 还把进程 TEMP/TMP/TMPDIR 指向本树。
  不能声称全程零外写。[越界证据](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/dynamic_temp_scope_deviation.json)。

## 8. 遗留与后续

1. **2365>200**。进一步关闭字段／类型／参数摘要缺口，明确隔离真实近似范围，不能靠批量续签完成。
2. 数值动态遗留 **16 条规则记录、8 个作用域、4 个文件**，不是“不可改写”的结论：

@@PENDING@@

3. 公开诊断 callback 的 5 条边界需维护；642 条证明缺口及 467 条近似／名义排除没有变成自动证明。
4. 插入排序大规模性能、任意 Python 协议、人工排除 callee 的将来语义不在保证内。
5. 工单禁止 worktree 操作，未建新鲜 worktree／克隆，也未完成六路 G6。全绿只对应此冻结工作树，不作里程碑 G6 退出声称。
6. 未 commit/push/reset/checkout/stash/worktree，未代改姊妹仓库或其他工作树。已披露 TEMP 约束偏差。

后续：先跑门 → 仅核被改作用域的陈旧记录 → 删除例外／改简单写法／补有限证明 → 逐项手审 → 重跑三门、牙、全套。
**不要运行历史初装器来重建清单，不要统一刷新 context。**

重跑（每次选未使用的运行名）：

    $env:PYTHONDONTWRITEBYTECODE='1'
    python -X utf8 tools/check_exact_construction.py
    python -X utf8 reports/codex/R12FIXb_evidence/real_policy_locality_probe.py
    $env:R12B_RUN_NAME='manual_recheck_01'
    python -X utf8 reports/codex/R12FIXb_evidence/run_full_suite.py
    python -X utf8 tools/fix_canon_ptrs.py --apply

恢复锚点为 [执行前字节副本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/baseline/)，须逐文件核对，不用 git reset 覆盖原已接受改动。
[交付与历史证据索引](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/DELIVERY_INDEX.md)。

R12FIXb_PARTIAL：2365 条局部排除超过 200；16 条数值动态规则记录待改写；证明缺口及旧近似范围未关闭
