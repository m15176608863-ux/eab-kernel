# WO-R12FIX 修复报告

> 已完成本单，工作树未提交。静态门 0 违例；全套 11368 项全绿；包含收集/核对的运行跨度 569.37 秒（四进程，不是串行计时）。

## 1. 输入与执行合同

- 实际输入 [G6L findings](file:///D:/eab-wt/cx-e2/reports/codex/inputs/G6L_findings.json) 确认 **0 critical / 1 major / 0 minor**，唯一编号 **G6L-01**。工单中“6 条”“11 条”是遗留模板文字，不虚构另外的发现；下文分成 11 个证据组，仍只计一项修复。
- 起点：`codex-work`，HEAD `0ce65a44c9c26d99411cee68d7300e7b5521bb40`，已含 M4a；初始 tracked 工作树无修改，仅有未跟踪的本轮审查输入。
- 范围：只写本工作树。未修改生产数值实现、姊妹仓库、外部设计正本、fixtures；不运行姊妹 exe。未执行 commit / push / reset / checkout / stash / worktree。
- 成功标准：审查四形态修前确实漏报且数值错误；修后在真实植入行拒绝；未知形态默认拒绝；内部撤除关键检查能弄红看护断言；源码和独立 helper 全扫无未处置项；M4a 与全套通过；文档准确说明范围。
- 回退锚：HEAD 及 [原 scanner 字节备份](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/baseline/check_exact_construction.py.txt)。不通过 git 回退丢弃其他修改；本单不自动执行回退。
- 工单禁止新工作树，因此未执行新鲜 git worktree 门；本次工作树测试不冒称新的六路独立 G6 退出审查。M0 的所有者退出决定不变。

## 2. G6L-01：根因与治根修复

旧门在不认识普通调用、容器取出的 callable 或跨过程返回时，可能给出空的舍入/调用来源摘要；`map`、`iter`、`pop` 因而把真正的早舍入路径洗成“零违例”。继续补函数名不能闭合 Python 的隐式构造与反射表面。

保留 [原局部来源分析](file:///D:/eab-wt/cx-e2/tools/check_exact_construction.py)，新增 [正向子集准入](file:///D:/eab-wt/cx-e2/tools/exact_construction_subset.py) 和 [逐站点人工审查清单](file:///D:/eab-wt/cx-e2/tools/exact_construction_policy.json)：

1. **未证明即拒绝**：未知 AST、import/namespace member、普通调用摘要、callable 传递、动态调用、回调、装饰器、间接写入、未知属性读取及运行时反射均须报 `closed-*`；不再猜未知返回“安全”。
2. **数值子集同样封闭**：自动证明仅限纯整数字面量的精确算术闭包；`/`、负幂、变量/混合类型算术、`sum` 等无类型证明的路径默认拒绝。注解内调用、f-string、不能证明为纯整数的 `%` 不作为无损数值操作放行。没有把“不是任意 Python 证明”变成容许已知内建绕过的借口。
3. **人工例外不等于静态证明**：保留现有数值路径时，逐条记录 AST、限定函数、完整模块上下文及具体数值模型/用途理由；没有按函数名、属性名或整文件全面免检。全部 `src/tests/tools` Python 字节与路径集被依赖哈希锁定；任一变化使新增例外失效。扫描副本核副本的字节，而不是借主树背书。
4. 仍运行原有 `rounded-root` / `rounded-vector` / `direct-float` / `subtract-rounded` 等门。新准入不能替代或掩盖旧舍入断言。

**保证范围**：受支持内建标量/数据模型上的封闭子集静态检查，加明确人工例外、默认拒绝。不是任意 Python 的数值证明，也不证明任意算法意图、任意用户对象重载或外部运行时 monkeypatch。变量 Fraction 算法本身也不靠名字推断精确，须读对应人工理由。

## 3. 11 个证据组：修前红 → 修后绿

永久门：[test_r12fix_static_closed.py](file:///D:/eab-wt/cx-e2/tests/test_r12fix_static_closed.py)，新增 **112 个参数化格子**；没有缩减原网格。

| 组 | 被看护内容 | 修前/撤修失败证据与修后断言 |
|---|---|---|
| 1 | 真实 cone 的 `map(norm_rational, ...)` | 正确 `5e-324`，内部坏构造 `0.0`，旧门 `[]`；新门要求真实植入行有 `closed-*`。 |
| 2 | 真实 cone 的 `map(sqrt_rational, ...)` | 平方量先构造成零，再求根；旧门漏报，新门拒绝同一调用行。 |
| 3 | `next(iter([norm_rational]))` | callable 从迭代器取回后早舍入；旧门漏报，新门拒绝目标语句。 |
| 4 | `list.pop()` 返回 callable | 真实函数内部容器取出 root 后错误变零；新门拒绝，不向枚举结果追加假数据。 |
| 5 | 未见过的自定义 HOF、partial/lambda、动态属性/导入/容器 | 同时覆盖源码路径和独立 oracle helper 路径；自定义 HOF 即使实参尚未舍入也必须拒绝，证明不是靠旧坏表达式名单。 |
| 6 | 普通 helper 洗掉实参、隐藏自身舍入返回、把 root 藏到 callee | 保留已知实参舍入；无跨过程证明就拒绝调用，不以未知返回当成精确。 |
| 7 | intrinsic 同名遮蔽、未知 namespace/member、callback/解包 | `abs`、`tuple`、`get`、`Fraction` 等同名局部定义不能获得内建摘要；未知调用表面默认拒绝。 |
| 8 | 注解、`__annotations__`、globals/dict/defaults 等运行时元数据 | 实际运行均可把半次正规分量舍成零后取回；独立平方中点证书要求非零；注解内调用及运行时 `__annotations__` / dunder 反射默认拒绝，普通纯类型标注不因此拒绝。 |
| 9 | 非 dunder 的生成器帧与异常参数 | `gi_frame.f_locals`、`ValueError(...).args` 也能携带早舍入值；未知数据属性按站点审阅，不能仅补反射名字黑名单。 |
| 10 | `%g` / f-string，整数除法/负幂，Fraction×float，混合 `sum` | 均有运行 `0.0` 与独立中点要求 `5e-324` 的反例；无类型证明算术/归约/格式化默认拒绝。 |
| 11 | 内部撤除准入、真实全仓副本与依赖漂移 | 撤掉 scanner 的关键步骤，四个真实 cone 拒绝断言必须失败；副本植入要在植入行拒绝，修改源码/helper/tools 使旧例外失效。 |

四种真实 cone 的 oracle 独立采用 Fraction KKT 和平方中点：`q=2**-1074`，投影 `p=(-q/3,)*3`，平方范数 `q²/3`，严格处于 `(q/2)²` 与 `(3q/2)²` 之间，故最终 binary64 为 `q`。先把三个分量各舍入会全为零；这不是几何原语共用形成的自证。

修前原始日志（尾行原样）：

| 日志 | 尾行 |
|---|---|
| [四形态及动态形态](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_red.log) | `40 failed in 0.71s` |
| [helper 实参](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_helper_red.log) | `2 failed, 44 deselected in 0.08s` |
| [helper 返回](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_return_red.log) | `2 failed, 46 deselected in 0.09s` |
| [同名遮蔽](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_shadow_red.log) | `8 failed, 70 deselected in 0.29s` |
| [callee 内隐藏 root](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_argument_red.log) | `2 failed, 78 deselected in 0.13s` |
| [运行时注解/反射](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_annotation_red.log) | `8 failed, 80 deselected in 0.32s` |
| [默认参数反射](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_default_reflection_red.log) | `4 failed, 88 deselected in 0.20s` |
| [普通属性/格式化](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_attributes_format_red.log) | `8 failed, 92 deselected in 0.32s` |
| [隐式算术/归约](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/pre_fix_implicit_arithmetic_red.log) | `12 failed, 100 deselected in 0.44s` |

这些 `deselected` 仅是先红定向运行选择；最终全套不得有遗漏/缩网格。前四行真实问题由旧 scanner 先复现；后续边界是在修复过程的独立负向检查中先确认漏报再收紧，不误称都已在原审查报告中列为独立发现。

## 4. 变异不是碰巧报红

`test_l01_disabling_closed_pass_trips_real_cone_rejection_assertion` 在 scanner 源码内部撤掉正向准入及未证明普通调用拒绝，原局部来源分析保留。它捕获的必须是：

```text
G6L-01 closed-subset rejection assertion
```

且指向 `cone_intersection_margin` 的实际植入行。真实坏构造数值从 `5e-324` 变成 `0.0` 另有独立断言，不能靠全图哈希失效造成其他行报警充牙。完整记录见 [变异断言证据](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/mutation_teeth.json)。

## 5. 全仓同类扫描与人工例外

扫描对象为 `src/` 与 `tests/` 全部 **196 个 Python 文件**；依赖锁定另含 `tools/`，合计 **213 文件**。初次调用准入扫出 9392 个诊断；补齐属性与未定型算术后原始诊断为 **18630 个**，这是新规则对现有语法的保守拒绝数量，不是 18630 个已确认数值缺陷。相同函数内相同 AST 可能被多行使用，正式清单按完整键去重为 **16936 条**（src 7828、tests 9108），未审项 0；[验证汇总](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/verification_summary.json) 再核上下文、依赖和键唯一性。

- [最终原始扫描](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/final_raw_scan_v2.json) 保留未豁免结果。
- [源码新增准入审核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/src_positive_subset_review.json) 区分 Fraction/整数、过滤候选、给定模型、显示字段和旧近似报告；例如 LP 的浮点 `%1.0` 是候选扰动，不能谎称整数取模；浮点接触形心只选择参考点，后续精确力矩仍从原数据计算。
- [独立 oracle 新增审核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/test_oracle_positive_subset_review.json) 区分精确 Fraction 算法与 legacy 窗口/位模式兼容参考。
- 测试文件中的顶层独立 helper 同样审查。模块级 pytest/scaffold 与顶层 `test_*` 驱动的整个子树明确不属于新闭集前检保证；原舍入扫描仍运行。驱动内部局部 oracle 不能因零违例被称为已获此门保证。
- [测试文件独立 helper 新增审核](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/test_driver_helpers_positive_subset_review.json) 含 4727 个新增站点；其中 [723 个明确 legacy 豁免站点](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/test_driver_helpers_positive_subset_exemptions.json) 属于既有近似/残差/有限筛选模型，不是驱动豁免，也不属于机器精确证明。
- 旧浮点观察/残差/采样筛选明示为 scope exemption，不冒称独立精确几何 oracle。完整理由在正式 policy 和 evidence 的逐站点审核清单；历史实验扫描/候选不是最终授权清单。

正常 scanner 只读 policy，绝不自动扩充白名单。evidence 中的组装脚本是本次已审清单的封装工具，不是供未来改动自动盖章的刷新入口。全图锁定很保守：连注释/换行变化也需重新核对，这是安全与维护成本的明确取舍。

## 6. 测试改写台账（只加强，不放松）

| 文件/门 | 原断言与新断言 |
|---|---|
| R9 `test_checked_construction_calls_are_not_rejected_as_direct_casts` | 未定型 `a-b` 不再允许空诊断，必须且仅出现 `closed-unproved-arithmetic`，仍不得误报 direct-float；新增 `3-2` 确切整数正例；原直接 `sqrt_rational(q)` 正例保留。 |
| R10 `test_j01_fraction_on_unrounded_supplied_data_remains_allowed` | 简单形式仍为 `[]`；map/容器方法形式要求非空且仅 `closed-*`，仍不许虚构旧 rounding 违例。参数格子全保留。 |
| R10 `test_j01_self_expanding_attribute_alias_terminates` | 保留原 **2 秒**超时及进程成功断言；未知 `a.x` 现在必须且仅有指定闭集拒绝，不再期望 `[]`。 |
| R11 原 unrounded/overwritten 正例与 eager generator 正例 | 原先不应出现的 rounding 诊断仍禁止；同时要求未知 callable/容器表面默认拒绝。参数、执行顺序与网格不减。 |

未删除测试、未加 skip/xfail、未缩网格、未放宽容差/超时。源码和数值测试的正确答案未修改。

## 7. 全套、M4a 与文档验证

### 7.1 定向与静态门

| 验证 | 原始末行 |
|---|---|
| 静态 CLI | `exact construction AST gate: 0 violation(s)` |
| R9/R10/R11/R12 全部静态回归（含真实副本） | `280 passed in 93.96s (0:01:33)` |
| M4a 109 项 + 文档 15 项 | `124 passed in 9.07s` |

证据：[命令与耗时](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/targeted_verification.json)、[静态输出](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/static_gate.log)、[定向原日志](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/targeted_regression.log)。首次定向有一次 **环境错误**：basetemp 父目录不存在，结果为 `279 passed, 1 error in 65.92s (0:01:05)`；保留 [失败原日志](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/targeted_regression_environment_error.log)，创建本树父目录后重跑全绿。没有为此放宽断言、跳过测试或延长超时。

### 7.2 完整全套：11368 / 11368 通过

Python **3.12.10 / Windows x64**。运行 [标准 pytest 四分片脚本](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/run_full_suite.py)，没有安装 xdist；先完整 collect，再按完整测试文件分配四个普通 pytest 进程。每条命令仍是 `python -X utf8 -m pytest -q ...`，没有 `-k`、删格、skip/xfail。只记录节点的插件不改变选择。

**各 pytest 的最后一行原样如下**（四进程，因此不伪造一条串行 pytest 总结）：

```text
1367 passed in 426.60s (0:07:06)
2230 passed in 559.35s (0:09:19)
4876 passed in 398.18s (0:06:38)
2895 passed in 260.07s (0:04:20)
```

- 总数 **11368**，相对原 11256 增加 112；完整收集集、四片收集并集、执行并集逐 nodeid 精确一致且无重复。
- 四进程退出码全为 0，setup/call/teardown 无 failed 或 skipped；四分片是完整测试运行，不是定向结果拼成声称。
- 并发执行墙钟 **566.600559 s**；包含收集/前后核验的脚本 UTC 起止跨度 **569.374448 s < 900 s**。四个进程时间相加 1667.99 s 不是串行基准，不以此宣称性能提升。
- 运行前后核对 **220 文件**（代码、policy、相关文档、配置和记录插件/脚本），漂移清单为空。
- 另对 **3375 个 tracked 文件**计算实际 Git blob 与 SHA-256；只有本报告列出的 6 个既有文件修改，**219 个 src/fixtures 文件均与 HEAD 原字节相同**。新文件明确列在交付清单，不通过 git stat 缓存冒称来源未变。

证据：[完整全套汇总](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/full_suite/summary.json)、[各片原日志及逐项记录入口](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/ARTIFACT_INDEX.md)、[最终机读验收 PASS](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/verification_summary.json)。原三份既有静态测试文件的测试函数集合（含明确登记的一处改名）和参数装饰器另有 AST 等价核验，全通过。

M4a 三文件共 **109 项**，与 HEAD 原字节相同：[清单](file:///D:/eab-wt/cx-e2/reports/codex/R12FIX_evidence/m4_inventory.json)。未改 adapter/reader、未重捕获或删改 fixtures。它们须同时纳入最终全套。

文档同步：[README](file:///D:/eab-wt/cx-e2/README.md)、[canon_map §8](file:///D:/eab-wt/cx-e2/docs/canon_map.md) 增加 M4a 列并消除旧唯一键歧义；[本树设计同步](file:///D:/eab-wt/cx-e2/docs/r12fix_design_sync.md) 说明闭集、人工例外、测试豁免和真实保证范围。外部设计正本只读，不声称已回写。`fix_canon_ptrs.py --apply` 已运行，输出 `0 rewritten; 0 kept` / `applied`。

## 8. 可复跑与遗留

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/check_exact_construction.py
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r12fix_static_closed.py --basetemp=reports/codex/R12FIX_evidence/tmp/r12_rerun
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=reports/codex/R12FIX_evidence/tmp/serial_rerun
```

不要求重启、登录或安装依赖。本单没有尚未修完的确认项。保留边界：人工例外不是机器数值证明；测试驱动豁免区不是精确 oracle 保证；policy 的 AST/依赖快照绑定本次验证环境，变更源码或 Python AST 版本后须重新审阅，不能自动刷新后冒称仍然已证明；M4a 仍为冻结导出的静态离线对账，未扩展为运动首入/锁滑/在线替换验证；独立下一轮复审仍由审查线决定。

R12FIX_DONE
