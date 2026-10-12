# WO-R10FIX 修复报告

日期：2026-10-12。执行树：`D:/eab-wt/cx-e2`；分支：`codex-work`；修前/交付 HEAD：`0e9ef93f67656b0bfeafd487ff12bde44360ab25`。
工作树交付，不提交。**不是下一轮独立 G6，不宣称 M0 退出。**

**交付结论**：五条及本次确认的同类问题已修；新增 209 格，既有测试不改。
完整串行回归 **10813 passed in 1185.22s (0:19:45)**；墙钟 1194.19 秒。
超过 900 秒目标；原因与慢项见第6节。关键成果及全部证据见 [交付索引](R10FIX_DELIVERY_INDEX.md)。

## 1. 输入数量对账与工作合同

输入 [G6J_findings.json](inputs/G6J_findings.json) 实际 `findings` 为 **5 条：0 critical / 4 major / 1 minor**，
对应 G6J-J01～J05。工单“6 条确认发现”“与这 6 条同类”“报告 11 条”与实际新发现数不一致。
本报告按 **5 条本轮修复 + 6 条上一轮修复保留性回放 = 11 个对账项**列明，不虚构 J06～J11。
后六项当前已经修复，不把旧轮红灯冒称为本轮修前红。

- **目标**：五条均有当前代码修前红、修后绿、内部变异报红；扫描同类并处置；完整测试全绿。
- **范围**：只写本树；姊妹仓库、其他工作树及外部正本均只读。未执行 commit/push/reset/checkout/stash/worktree。
- **非目标**：不改变姊妹内核；不运行姊妹 exe；不删 fixture、不缩网格、不改工程验证/优先性口径。
- **回退锚**：[逐文件修前副本](R10FIX_evidence/baseline/) 与 [修前 SHA-256 清单](R10FIX_evidence/baseline_manifest.json)。
  恢复必须由所有者按文件选择，不用 Git 批量丢弃后续修改。
- **验证**：新增独立解析/有理数门、源内变异、原 148 个测试文件保留、全套 pytest、静态门、canon 指针、fixture/input 哈希及范围审计。
- **执行约束**：Python 均用 `PYTHONDONTWRITEBYTECODE=1 python -X utf8`；pytest 临时目录置于本树 evidence/tmp。

## 2. 五条修复：逐条红 → 绿 → 变异

### 01 · G6J-J01：静态门关键字与伪去污（major）

**根因**：只读 `Call.args`，漏关键字及 `**kwargs`；`Fraction`/`map(Fraction)` 清掉已知舍入来源；
局部循环、增量赋值、容器和分支缺少来源传播。

**修法**：位置/关键字/星号参数共用入口；Fraction 只精确表示现有值，不恢复已丢位数；
跟踪普通、注解、解包、海象、增量、属性/下标/容器赋值，以及循环、推导式、with、match、try 的本地可见数据流。
callable 别名按可能分支合流，别名图按首节点判环，防止 `a=a.x` 无限展开。
仍明确不是任意动态 Python 的跨过程完备证明。

**修前红**：[首跑](R10FIX_evidence/J01_red.log) `30 failed, 11 passed in 0.33s`；
最终七原型和七个真实 cone 路径变异在保存的修前 scanner 上重放：
[日志](R10FIX_evidence/J01_final_baseline_red.log) `14 failed in 0.26s`。
目标断言要求指定函数/规则存在，旧门给 `[]`。

七种语法逐项：`sqrt(value=...)`、`norm(values=...)`、`Fraction(rounded)`、`map(Fraction,rounded)`、
局部 for 累加、局部 append、`a -= b`。每种都植入真实 `cone_intersection_margin`，独立 KKT 与平方中点证书给正确输出 u，
原内核 u、变异内核 0，再检查指定 AST 规则。不是“产出后追加假数据”。

**修后绿**：[新 65 + 旧 25 门](R10FIX_evidence/J01_green.log) `90 passed in 1.28s`；全仓 AST 0 违例。
**回退变异**：只删 scanner 的 keyword 遍历，真实 cone 关键字变异的数值断言先通过，随后
`assert any(row[2:4] == ("cone_intersection_margin", "rounded-vector") ...)` 报红，实际 `[]`：
[1 failed](R10FIX_evidence/J01_mutation_red.log)。

额外四个交叉复核反例（海象外层绑定、别名无限展开、try/match callable 合流）先
[4 failed, 61 passed](R10FIX_evidence/J01_peer_red.log)，修后原探针再次独立运行全部通过：
[复核](R10FIX_evidence/static_peer_recheck.log)。完整 [J01 分报告](R10FIX_evidence/J01_notes.md) 列出五个窄例外及理由。

### 02 · G6J-J02：普通三维边界初态闭集首入（major）

**根因**：只单独处理 `int(E)` 初态；普通边界初态进入“向内运动”的候选过滤，切向/背离候选被丢掉。
**修法**：`initial==0` 分支按当前位形独立收集精确零间隙、有限特征域盖，方向无关返回
`entrance / exact_t=0`。保留紧配内缝 `int(E)` 的局部出口合同，统一显示见证构造。

**修前红**：[日志](R10FIX_evidence/J02_red.log) `16 failed, 16 passed in 1.02s`。
原复审 12 格仍 9 格错：6 格 `none`、3 格背离 RuntimeError；另有 Fraction/float 见证显示不一致。
目标断言：`got.kind == 'entrance'`，实际 `'none'`；信息为
`closed initial face boundary must not be discarded by motion`。

**修后绿**：[39 门](R10FIX_evidence/J02_green.log) `39 passed in 1.11s`；
[旧相关回归](R10FIX_evidence/J02_targeted.log) `318 passed in 31.03s`（该次新门为 38 格，随后追加非零 x0 门）。
覆盖面/棱/点初接触、凸/凹体、零/短 t_max、进入/背离/切向、1e-9/1/1e8 尺度、1e8 平移、有理旋转。

**变异**：源内 `if initial == 0` 改 false，在上述 kind 断言红；去掉 `c.in_extent`，在
`initial tied label left its finite source domain` 红（实际 `5/4 <= 1` 不成立）。
证据和二维、zero-margin、互锁、brute/shortest_exit 路径扫描详见 [J02 分报告](R10FIX_evidence/J02_notes.md)。

### 03 · G6J-J03：微反射法锥反方向误标严格内部（major）

**根因**：两侧叉积正不足以证明两条射线构成正向凸锥；微反射的反向薄扇区也满足原条件。
**修法**：先核合法凸/显式微反射域，strict 再要求精确正转角；微反射同向窗口最多返回 0，反向 -1。
大反射/对向边界射线不在此凸法锥域，返回 -1；零射线明确拒收。

**修前红**：[日志](R10FIX_evidence/J03_J05_red_corrected.log) 三姿态均在
`opposite thin sector is exterior` 断言 `1 == -1` 报红，另含大反射、反向射线和零射线格。
**修后绿**：新门连同 J05 和旧 R9 solid-cones 的 [扫描回归](R10FIX_evidence/J03_J05_scan.log)
`81 passed in 0.21s`。
**变异**：在内存恢复原 `in_cone` 函数体，三个原姿态再次在同一方向断言红：
[3 failed](R10FIX_evidence/J03_mutation_red.log)。

同类读取二维全部 cone helper/VE/VV 前置条件与三维顶点、棱弧、锥交依赖；新增三维微反射屋脊门。
另一路独立快审实际执行 720 个有理反射方向格，未确认新缺陷：
[复核报告](R10FIX_evidence/root_peer_review.md)。这不是任意无效输入/任意曲面的完整证明。

### 04 · G6J-J04：Dual.sqrt 完整导数提前舍入（major）

**根因**：先将 sqrt(v) 舍为 1，再算 `(0.5/s)*seed`。v=nextafter(1,+inf)、seed=3u 时得到 2u，正确结果 u。
范围外导数还会静默 0/Inf。
**修法**：完整导数平方 `seed²/(4v)` 在 Fraction 中求出，统一 `sqrt_rational` 一次舍入后施符号；范围外响亮失败。

**修前红**：[主日志](R10FIX_evidence/J04_red.log) `26 failed, 6 passed, 3 deselected in 0.23s`；
其中中点真值断言 `complete sqrt derivative final rounding` 报错，范围格 `DID NOT RAISE`。
**修后绿**：[新旧子集](R10FIX_evidence/J04_green.log) `1099 passed in 0.66s`，保留原 R7 的 876 格。
**变异**：恢复 `(0.5/s)*a` 后同一完整导数断言红；其余五种同类源内变异也各自命中目标断言：
[六项变异日志](R10FIX_evidence/J04_mutations.log)。

同类实际修复：sin/cos 非零导数乘积下溢；half-integer pow 的 Decimal80 精确 tie 错舍（4.5u 应偶舍 4u，原5u）；
atan2 ordinary 快径一 ULP 错舍；pow 零 seed 时 primal 静默下溢。
half-power/atan2 追加 [修前红](R10FIX_evidence/J04_scan_red.log) `13 failed, 35 deselected in 0.17s`。
一般超越/非半整数幂的近似合同没有冒称全域 RN-even；完整说明见 [J04 分报告](R10FIX_evidence/J04_notes.md)。

### 05 · G6J-J05：uncertainty=NaN 被标 resolved（minor）

**根因**：精确 LP 机构先显示 Inf、误差预算先显示零，`Inf*0` 成 NaN；`NaN > threshold` 为假留下 resolved。
**修法**：保留精确机构、移轴活荷载、有理预算尺度；完整比值与邻域重解相对变化最后才显示；
最优/无界、单/多体四分支均显式把非有限 U 标 unresolved。不改承载状态与精确 alpha。

**修前红**：[日志](R10FIX_evidence/J03_J05_red_corrected.log) 原例
`math.isfinite(result.uncertainty)` 为 false；NaN/Inf 诊断注入也在状态断言红。
**修后绿**：[22 门](R10FIX_evidence/J05_optimal_scan.log) `22 passed in 0.08s`；
加旧 limit fuzz/multi/selfcheck 的 [定向回归](R10FIX_evidence/J03_J05_green.log) `186 passed in 10.15s`。
**变异**：真实 `_wrench_rounding` 恢复旧函数体，次正规预算归零，单/多体 U=0，在独立下界
`4*2**-53 <= uncertainty` 红：[2 failed, 6 passed](R10FIX_evidence/J05_mutation_red.log)。

**对审查材料的必要订正**：该退化对偶面上的 U 不唯一；机构约束给 `u <= U <= 3u`，而非固定 u。
当前所选机构为 `(0,1/s,-1/s)`，U=2u。新增测试最初写固定 u 的错误已在生产修改前订正，
两个修前日志均保留；这不是旧测试弱化。
独立快审还验证单/多体三个 alpha 显示全 Inf 的邻域重解，精确变化率仍为
`0.0008297438213806996`、状态 unresolved：[探针](R10FIX_evidence/root_peer_probes.log)。

## 3. 第 06～11 项：上一轮六修复的保留性回放

运行审查方已提供的六个 `r9_positive_*.py`，只在内存适配 ROOT/import 路径，输入原件不改。
输入 SHA-256、退出码、耗时和日志见 [机读六项结果](R10FIX_evidence/previous_six_replay.json)，
完整命令见复跑脚本 [replay_previous_six.py](R10FIX_evidence/replay_previous_six.py)。全部 exit 0。

| 对账项 | 上轮缺陷/本轮保留断言 | 结果与证据 |
|---|---|---|
| 06 · G6I-01 | 2D 平直链有限特征：t=1、仅 VE(0,3)、见证重合；边界 FF t=0 | [FIXED](R10FIX_evidence/r9_positive_geom2_convex_flat_facet_domain.log) |
| 07 · G6I-02 | 声明折面屋脊：24 输入格，同时核源/声明表面凸性 false、凹棱(5,7)、中点 exterior | [FIXED](R10FIX_evidence/r9_positive_geom3_folded_reflex_hidden.log) |
| 08 · G6I-03 | 精确锥交 margin 次正规 24 格，独立 KKT 与完整平方中点 | [FIXED，0 wrong](R10FIX_evidence/r9_positive_geom3_cone_margin_subnormal.log) |
| 09 · G6I-04 | margin/oracle 先舍平方错误：三尺度真距；实际 body_distance/margin_contacts 源内回退仍被抓 | [FIXED + MUTATION REJECTED](R10FIX_evidence/r9_positive_docs_margin_oracle_range.log) |
| 10 · G6I-05 | 分离壳方向：总56=64-8 不得遮住小内向壳；明确 component 1 inward | [FIXED](R10FIX_evidence/r9_positive_geom3_manifold_component_orientation.log) |
| 11 · G6I-06 | README/canon 三处现行陈述不得恢复过时合同 | [FIXED](R10FIX_evidence/r9_positive_docs_stale_current_contracts.log) |

这六项没有在本轮假装重新修复、重新造修前缺陷；其历史红→绿/修法见输入 G6J 的六项确认及既有 R9FIX 报告。

## 4. 同类扫描结论与剩余边界

| 类别 | 本次覆盖/新增处置 | 边界 |
|---|---|---|
| 初态边界 | 2D/3D 首入、brute、局部出口、零裕度、互锁 covers/brute；普通凸/凹接触和内缝区分 | brute 共用生产成员只能佐证；局部出口非全局凹体 PD |
| 法锥 | 公共2D helper/局部VE/VV与3D声明表面顶点、棱弧、锥交；微反射三尺度+方向格 | 有限输入族，不认证任意畸形表面或非有限 tol |
| Dual 初等函数 | sqrt、sin、cos、pow、atan2，以及 frozen 自有 Fraction jet 的读取核查 | libm/一般非半整数系数仍近似；普通四则精度未重定义 |
| 静态调用/赋值 | 七真实路径原型、65新增格，含四个交叉检查遗漏后的返修 | 未知反射/用户函数跨过程不属形式证明；五个窄例外保留并逐项说明 |
| 报告派生量 | 单/多体 U、噪声预算、扰动、邻域 alpha 差比；NaN/Inf 不得 resolved | U 只是所选机构的估计；非所有最优面的稳定性保证 |

没有修改姊妹仓库，没有将相同错误移到输出包装层去隐藏。两次内部交叉审查的范围和结果均留证，
**它们不是仓库要求的新鲜只读树六路 G6**。

## 5. 测试改写、范围和文档台账

- 148 个既有测试文件与修前 SHA-256 **逐字节相同**；0 删除、0 放松、0 skip/xfail、0 参数网格缩减。
- 新增五个 `tests/test_r10_*.py`，共209格（65静态、39初态、26法锥、57对偶、22分辨性）。新门开发订正：J05 的不唯一 U 改用正确解析范围；J01 local_append 的
  最终算子与目标规则对齐，并在修前 scanner 对最终七原型重跑红。J04 期望转换换成独立 oracle，未加新测试白名单。
- 62 个既有 fixture 文件逐字节相同；复审指定的六份复现脚本 SHA-256 与 findings 中提供值全部相符。
- 修改范围：5 个生产模块、1 个工具模块、4 个既有文档；新增本树设计同步、五个测试和证据。
- README/canon/两份本树设计已链接 [R10FIX 设计同步](../../docs/r10fix_design_sync.md)。
  外部 `D:/E(A, B)/07 ...md` 只读，待所有者纳入；没有把本树补充说成外部正本已回写。
- 定义行移动后已运行 `tools/fix_canon_ptrs.py --apply`：15 rewritten、0 kept；[日志](R10FIX_evidence/canon_apply.log)。
- 原 scanner CRLF 保留。`git diff --check` 默认把 CR 误报 trailing whitespace，故审计使用命令局部
  `git -c core.whitespace=cr-at-eol diff --check`，没有修改任何 Git 配置。
- 可复跑 [范围/fixture/测试/输入审计](R10FIX_evidence/verify_delivery.py)；结果 [delivery_audit.json](R10FIX_evidence/delivery_audit.json)。

## 6. 最终全套与耗时

最终串行运行命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
New-Item -ItemType Directory -Force reports/codex/R10FIX_evidence/tmp | Out-Null
python -X utf8 -m pytest -q --durations=20 --basetemp=reports/codex/R10FIX_evidence/tmp/full_suite
python -X utf8 tools/check_exact_construction.py
python -X utf8 tools/fix_canon_ptrs.py
python -X utf8 reports/codex/R10FIX_evidence/verify_delivery.py
```

全套由 [run_full_suite.py](R10FIX_evidence/run_full_suite.py) 保存 stdout/stderr、退出码和墙钟。
一次初始全套因交叉检查发现静态门遗漏而主动停止，保留
[中断日志](R10FIX_evidence/full_suite_interrupted_static_peer.log)，不计作通过或最终耗时。
第二次运行在使用 tmp_path 时遇到 setup 环境错误：指定 basetemp 的父目录不存在，
pytest 只创建末级目录，产生 `FileNotFoundError [WinError 3]`。保留
[第二次中断日志](R10FIX_evidence/full_suite_interrupted_missing_tmp_parent.log)。
创建本树父目录并在复跑脚本中加入 `mkdir(parents=True, exist_ok=True)` 后，原 fixture/provenance 门
`66 passed in 0.11s`；没有为此改生产代码或测试断言。
随后在全部源码/测试冻结、临时环境确认后重新运行，完整日志最后一行原样为：

```text
10813 passed in 1185.22s (0:19:45)
```

- [完整日志](R10FIX_evidence/full_suite.log)；[命令/退出码/耗时 JSON](R10FIX_evidence/full_suite.json)。退出码 **0**，
  无 failed/error/skipped/xfail 汇总；相较修前10604项，净增209项。
- pytest 1185.22 秒，进程墙钟 **1194.1882582999824 秒**，**未达到 ≤900 秒目标**。
  最慢20项均是既有门，主要为 bb52/G0 完备性及内部变异、frozen 特征枚举、互锁逃逸。
  例如 `test_g0_exit_completeness_has_teeth[drop_VE_subset]` 55.43s、`[no_EV_covers]` 42.66s、
  `[strict_cone_only]` 28.34s、bb52 几何 fixture setup 26.87s。
  没有为速度删格或放松断言；新209格+canon+fixture 的独立定向集成仅
  [276 passed in 1.57s](R10FIX_evidence/integration_final.log)，但这不是新增代码对旧门间接耗时影响的隔离基准。
  输入 G6J 在同 HEAD 的全套记录为1299.11s；环境/运行方式未受控，不能据此声称性能提升。
- 最终 AST：[0 violation(s)](R10FIX_evidence/static_gate_final.log)。
- canon 再核：[0 rewritten; 0 kept](R10FIX_evidence/canon_final.log)。
- 最终运行中201个源码/测试/工具文件 SHA-256 无变化：
  [快照](R10FIX_evidence/final_run_code_snapshot.json)、[稳定性结果](R10FIX_evidence/final_run_code_stability.json)。
- 全套之后重跑范围审计：148旧测试不变、62fixture不变、0删除、0越界修改、6份审查复现哈希吻合、
  HEAD/分支不变、diff whitespace 检查通过：[审计](R10FIX_evidence/delivery_audit.json)。

上述全套计时只含最终一次完整运行，不包含两次中断、逐条红绿、变异和交叉审查的额外时间。

## 7. 遗留与交付边界

本单不执行 Git 写操作，未创建新工作树，也没有权限范围内的外部设计正本回写。
下一轮独立 fresh-tree 六路审查仍须由所有者安排；“本轮全绿”不能代替 0 critical / 0 major 的 G6 退出结论。
静态分析与超越近似、局部出口和 U 估计的边界见第4节，不将有限测试包装成全域数学证明。

五条本轮修复无待处理已确认项。耗时目标未达是如实报告的性能限制，不通过缩减测试掩盖。
文件索引及可复跑脚本见 [R10FIX_DELIVERY_INDEX.md](R10FIX_DELIVERY_INDEX.md)；
精确交付文件哈希见 [delivery_manifest.json](R10FIX_evidence/delivery_manifest.json)。

R10FIX_DONE
