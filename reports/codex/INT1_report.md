# WO-INT1：M3 / M5 集成收口报告

日期：2026-10-15。起点及当前 HEAD：`f012d6a3a53b8f46a35e649843bbc1b8b2f93e0c`。

最终有效运行：`final_suite_r2_postreboot`，已在最终 CRLF 字节版本上整批从头完成。此前完整全绿的 r1 已标为 superseded，没有拼接任何分片。

## 结论与范围

**集成树真实重算及最终测试已绿；工单整体仍为 PARTIAL。** 第 1–5 条和第 6 条的本次 M3/M5 插桩集中、准入不扩张已处理；**第 6 条的全库历史插桩集中尚未完成**，具体剩余 19 个独立变异 helper／249 条有效准入，以及 112 个无逐站点准入的驱动插桩点，见 §5。这些是未实施的工作，不是环境阻塞，不能把本次局部整理写成全库完成。

最终新鲜字节副本共 **13,558 项收集＝派发＝各片实际收集＝实际执行，0 skip，所有 setup/call/teardown passed，静态 0 违例**。相对新基线净增 87 项、删除 0 项；新增节点耗时占基线约 **0.08673%**。机器交付核验 GREEN 只表示所列文件、来源及执行记录一致，不代表上述未完成卫生事项已完成。

仅写 `D:/eab-wt/cx-m4`；没有 commit、push、reset、checkout、stash、worktree、branch 操作。其他工作树及 b-DDA 只读；没有修改姊妹内核。新增工具使用标准库及本仓库已有模块，pytest 为现有测试依赖。未修改 `src/` 数值生产代码，主要改动为测试看护、静态检查、准入协议、真实重算后的证据绑定与理论文档。

关键交付：

- [最终四片摘要](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/final_suite_r2_postreboot/summary.json)
- [逐节点身份审计](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/node_identity_audit.json)
- [交付审计](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/delivery_audit.json)
- [完整文件及哈希清单](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/artifact_manifest.json)

## 0. 重启中断、作废与恢复

所有者报告 20:40 左右关机重启。22:09 恢复核查时，原 `baseline_suite` 仍为 `TESTING, complete=false`，**没有整批 final summary**，只有第 2、3 片已有终局文件。整批标为 `INVALIDATED_REBOOT`；这两片也不作为新运行的一部分使用，不拼接其余两片。重新从 HEAD 导出全新字节副本运行 `baseline_suite_r2_postreboot`。随后最终四片 r1 完整全绿，但字节卫生发现一个测试文件未保留原 CRLF；恢复行尾且确认 AST 完全一致后，另名 `final_suite_r2_postreboot` 再完整从头运行四片及静态门，以 r2 为最终证据。

- [中断与重用审计](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/interruption_audit.json)
- [原基线作废记录](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/baseline_suite/reboot_invalidation.json)

`motion_refresh_r2` 与 `se2_revalidation_r2` 在中断前已有完整认证。恢复后核对生产源码闭包、编排脚本、输入、已发布摘要／清单、15 个 worker 的完成标志／步数／源码绑定与规范化产物哈希，全部一致，故沿用两份完整认证。R1 另外独立解压深比较了两批共 900 帧。r1 是已完成但被加强编排校验后的 r2 取代的历史轮次，不与 r2 拼接。未完成的 R2/R3/R5 审查从头复做；旧 `static_scan2` 是完整但有 4 条违例的开发轮次，不充当最终扫描。

发现并修复两类交付编码问题：PowerShell 5.1 默认重定向产生的 12 个 UTF-16 驱动／专项日志，原字节保存在 ignored `tmp/encoding_originals/`，文本规范为 UTF-8 无 BOM；其默认 ASCII 管道还使主报告草稿及两份分报告中文变成问号，现已重写，并核对实际中文字及无 BOM。机器 JSON 和 policy 没有该问号污染；编码修复没有改数值结果或冻结源码。

行尾恢复仅涉及 `tests/test_m5a2_static_runner.py`，原／后 AST 严格相同；另做实际 R3 专项复验，不只换哈希。两套 450 帧的生产／回放闭包不含该测试文件，因此无需重算，最终依赖复核仍全部匹配。见[行尾修复记录](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/line_ending_repair.json)。

## 1. 全新基线：全部红项及原因

有效基线为 [baseline_suite_r2_postreboot](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/baseline_suite_r2_postreboot/summary.json)，来自只读 `git archive HEAD`，而非修改后的工作副本。13,471 项全部执行，**13,469 passed、2 failed、0 skip**，setup/teardown 均 passed。静态最后一行为 `exact construction AST gate: 0 violation(s)`。

| 实际红项 | 原因 | 处理 |
|---|---|---|
| `test_m5a_replay.py::test_frozen_family_products_are_distinct_and_bound_to_current_source` | M5a2 重验证清单中 `src/eab/kernel2d/global_entrance.py` 仍绑定 `59e7bf…`，合并树实际为 `a84477…` | 完整重跑 450 帧，比较后发布清单；未只改哈希 |
| `test_m5a2_static_runner.py::test_all_3103_legacy_and_117_m5a_admissions_remain_unchanged` | M3 线原地改写 23 条旧行，前 3220 行指纹由约定的 `1e513f…` 变成 `3b6f85…` | 恢复基线原行，续审并追加当前站点行 |

**与预期的差异也如实记录：** f012d6a 提交说明预计 M4c 源码绑定不符，但实际归档 HEAD 中该摘要的全部 23 个绑定文件均匹配，M4c 此项 pytest 没有报红。不能据预期虚构第三条失败；仍依工单在合并树完整重算了 450 帧，取得新的实际运行认证。准入冲突表现为不可变合同 pytest 红，**不是**旧 AST 扫描红。没有额外的文档指针行号失败。

完整失败节点及逐片末行见 [基线诊断](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/baseline_diagnosis.json)；源码实际绑定差异及 23 个旧行 ID 见 [绑定审计](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/baseline_source_binding_audit.json)。

## 2. 两套真实重算：比较通过才发布

| 有效运行 | 实算规模 | 比较规则与结果 | wall 秒 |
|---|---:|---|---:|
| `motion_refresh_r2` | 15×30＝450 帧 | 历史完整 JSON 帧逐值深比较；steps、分类、secondary counts、stats、输入、逐帧与整帧摘要均一致 | 161.16077659999428 |
| `se2_revalidation_r2` | 15×30＝450 帧 | 运行既有 M5a2 编排及 M5a 回放；逐历史 M5a 叶值比较；与上一轮 M5a2 的全部规范化产物哈希一致 | 64.22736220000661 |

M5a 历史时间证书与 M5a2 的表示差异仅限原协议已认可、经独立精确 oracle 证为相等的时间表示。本次逐算例表示变更清单与上一轮完全相同，**没有新增语义或规范化产物差异**。比较不通过即不发布候选，历史帧文件不覆盖。

M4c 摘要保留原 `m3c_refresh` 与 `m5a_revalidation` 两段溯源，新增 `int1_refresh`、完整编排哈希与此次实际计算指针。M5a2 先在 ignored tmp 生成候选，比较通过后才发布。`fixtures/PROVENANCE.json` 共 217 条，**仅 `m5a2/revalidation.json` 一条的 source、bytes、sha256 更新**，ingested/status 及其他 216 条逐值不变；其原有单空格缩进、CRLF、无末尾换行格式亦保持。

R1 在 r1 发现“原子发布”文字与直接写文件不一致、编排未纳入哈希两项 minor；改为目标文件原子 replace、纳入编排前后哈希后，两批全部另名 r2 重新计算，不沿用 r1 帧。M5a2 清单与 PROVENANCE 是各文件原子写入，不声称它们组成跨文件事务；回退副本及最终二者一致性检查保留。

- [M4c 完整认证](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/motion_refresh_r2_attestation.json)
- [M5a2 完整认证](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/se2_revalidation_r2_attestation.json)
- [M5a2 前后逐项比较](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/se2_revalidation_r2_comparison.json)
- [独立 900 帧及发布协议复核](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_replay.md)

## 3. 静态准入约定统一

采用 M5a2 的“旧行不改＋续审退休旧 pin＋新行钉当前节点”约定：

1. `3bf5e95` 已存在的 3103 行恢复其原 JSON 对象字节，23 条 M3 改写改为追加 `INT1-C0001..0023`。新行承接已验收 M3 的当前节点，而不是放宽匹配规则。
2. M5a 的 117 行、M5a2 的 170 行逐值及原对象字节不变；不可变 pytest 原指纹未改。
3. M3b 本线新增 39 行以 **6c014f5 已验收状态**冻结，包括经 M3c 续签的 `M3b-L0004..0007`。这些行在共同基线不存在，分支内部先前版本不是本次共同历史锚点，因此不退回尚未验收的旧 pin；今后改动同样走续审。涉及此次脚手架迁移的旧行保留原值并退休。
4. 共有 92 条续审，old_row 指纹全部匹配。续审只使旧 pin 不再被当作陈旧错误，**不会授予当前站点准入**；当前许可必须来自新 pin 或明确钉住源码的共享插桩域。

| 口径 | 转换前 | 转换后 |
|---|---:|---:|
| 历史 waiver 档案行数 | 3429 | 3452 |
| 仍有效的逐站点行数 | 3406 | 3360 |
| 共享插桩协议审查记录 | 0 | 1 |
| 有效行数＋共享审查记录 | 3406 | 3361 |

档案净增 **23 全为约定转换**；其他新增 waiver 为 0。旧插桩 46 条通过续审退休，未删除／改写历史；纳入一次共享域后有效许可净减 **45**，不是新增 23 项自由许可，也不是把历史档案行数虚报为减少。

[R5 独立原对象字节复核](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_admission_contract.md)与[机器不可变审计](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/immutability_audit.json)记录全部对账。

## 4. M5a2 缺失看护门与真实内部变异

相关生产路径原实现已有正确分支，本单未改数值源码；补上能够看住缺陷的常规 pytest。下表数值／几何／回放变异均先屏蔽源码及文件哈希回调，以原函数通过同一断言，再编译并注入实际内部函数缺陷，要求红在指定语义断言，而非哈希或碰巧失败。

| 要求／变异 | 新断言及观察 |
|---|---|
| **major：二次 as_rational 丢区间检查** | SE(2) 端到端正确首入 1/3；删除检查后实际变成 −1/2，命中 `quadratic SE2 entrance must be 1/3` |
| **major：swept radius 改 max 范数** | 任意非形心中心、u＝1/100、1/1000、1/10000，尺度 1、1e−6、1e6及大平移；独立有理坐标包含检查；变异将真实 contact 错判 no_contact，命中指定首入断言 |
| 模素数筛选漏掉整除首项系数的前提 | 构造 `(p x−1)(p x²＋1)`，p＝2/3/5；错误筛选丢掉真实有理根 1/p |
| 细化宽度 1/(2B²) | 两个大分母，初始中点严格越过 Farey 分界 gap/8，不处于平局；`1/(2B)` 和四倍宽阈值两种内部变异均失败 |
| δ_aff 的 L∞ 改 L1 | 双非零分量、正规方程正交残差，尺度 1e−100／1／1e6；正确 δ＝2s，而不是 3s |
| 聚焦 stats：已证分离而省略块对 | bb03 第1步 (1,3)；省略计数内部加2代替加1，命中完整 stats 守恒断言 |
| 聚焦 stats：初始接触复用 | bb05 第1步 (2,3)；内部漏计复用路径，命中初始接触完整 stats 断言 |
| 聚焦 stats：初始压入复用 | bb05 第1步 (1,2)；同类缺陷在 initial_overlap 分支独立失败 |
| 公共构造器闭区间上端点根 | `(3x−1)(x−2)` 在 [0,1/3] 精确表示上端根；破坏上端点收缩方向后命中端点语义断言；另拒绝两端同时含根区间 |
| 仿射拟合交叉项反号 | 进入常规 pytest，由独立未中心化 Cramer 正规方程断言杀死 |
| 正残差冒充精确证书 | 将 `δ==0` 改为 `δ<=2^-52`；命中正残差不得认证断言 |
| 逐顶点残差校正项反号 | 加号改减号；命中原快照终点必须精确闭合断言 |

以上共 **13 个内部变异**（宽度项包含两个），恢复后认证 13/13 KILLED；新语义文件 29 passed in 0.32s，相邻回归 116 passed in 1.59s。见[语义报告](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_work.md)、[恢复后认证](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_work_resume_r1.json)、[R4 独立逐变异复验](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_semantic.md)。

### 比较器站点与 watchdog

- 18 种高阶写法 × 普通／test-driver 两类路径，共 36 个控制格；覆盖 `self.compare`、map、getattr／反射、工厂返回、装饰器、继承并覆写 compare、变量及拼接名称、getattr 别名、字典／globals／vars、attrgetter、类型别名。对应 18 个检查器内部缺陷格移除该语义规则，必须红在 `higher-order comparator dispatch` 断言；注入文本不依赖源码哈希绊线。
- R3 初审实际找到 **1 major、10 种漏报**，保留原始 RED 证据；修复后 20 个双路径探针全拒绝。9 个共享域探针同时确认数值／舍入／比较器规则不被豁免，helper 字节或作用域变更会使审查失效。静态检查仍是保守有限子集检查，不声称任意 Python 程序证明。
- teardown 中真实等待 0.7 秒，0.25 秒 watchdog 必须以 124 终止且不能写完成 execution；内部把取消 timer 的 hook 从 logfinish 提前到 teardown 后，错误地返回 0，命中“teardown remains under watchdog”断言。正常及变异两格都纳入 pytest，不把 call 阶段通过当作整个测试完成。

见 [原 R3 独立复核](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static.md)、[CRLF 恢复后的完整 R3 重验](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_eol_r1.md)及[静态逐项清单](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/static_work.json)。新 R3 实际重跑 20 个高阶探针、共享域负向门、两个 teardown 子进程及 76 项专项（3.27 秒），不是只替换源码哈希。

## 5. 插桩卫生：已处理与明确未完成部分

[统一辅助模块](file:///D:/eab-wt/cx-m4/tests/mutation_support.py)集中源码提取、唯一锚点替换、复制模块 globals 后编译及返回／注入 callable。一次 `TEST_ONLY_SOURCE_MUTATION_PROTOCOL` 审查绑定 helper 整文件 SHA256 与 **9 个明确作用域 context**，不按函数名称无限豁免，不覆盖数值 oracle／结果断言，不豁免 rounded provenance、直接 float、数值算术或代数比较器准入。

活动准入类别的变化为：

| 类别 | 前 | 后 |
|---|---:|---:|
| M5A2_LOCAL_REVIEW | 170 | 143 |
| STRUCTURAL_DATA_OR_PROTOCOL_REVIEW | 299 | 280 |
| 其余原类别合计（逐类均不变） | 2937 | 2937 |
| 统一插桩协议域 | 0 | 1 |
| 合计 | 3406 | 3361 |

全部档案／活动类别及规则分布、46 个退休 ID、23 个转换 ID、9 个 scope 与逐函数遗留清单均见[静态报告](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/static_work.md)和[完整机器清单](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/static_work.json)。

**没有完成全库迁移。** exec AST 总数由 150 降至 146，其中中央 helper 占 1；其余 145 已分类，不能全部称为缺陷或待迁移变异：

- **19 个真正的历史独立变异 helper，承载 249 条当前有效准入**，涉及 R6/R7/R8/R9/R11/R13/R14/R15、G2、limit_multi、tf_reader、perf_contact_window；尚未集中。
- **112 个测试驱动／嵌套变异编译点**，现有逐站点准入为 0，仍存在重复仪器代码；尚未集中。
- 另 13 个故意动态程序／静态门测试和 1 个 AST 提取 builder，不属于应机械迁移的变异 helper。

这些历史迁移技术上可做，本次未实施，不以环境或工期冒充不可解阻塞。后续应按函数级、整模块级两组迁移，并逐变异核验，不得批量删除历史准入或扩大共享域以凑数量。因此本单最终标记 PARTIAL。

## 6. 仿射理论文档订正与证据边界

[docs/m5a2_affine_theory.md](file:///D:/eab-wt/cx-m4/docs/m5a2_affine_theory.md)已完成：

1. 撤回“未取得每步内部 d、θ、E”：out.csv 每步每块以 %.17g 记录 z 六分量。只读核对 15 份 out.csv，与 M4c 冻结哈希全相同，共 15,220 行；最大 |z3|≈0.0050105223。由 M 反解 θ、E 的唯一性明确限定小转角分支，而非声称 sin 全局唯一或逐位恢复原 z。
2. 明列顶点均值中心与 DDA 面积形心 `cent_prev` 不等价，给出换心平移关系；半角时间律、补偿应变与中心差异均保留。
3. 以 `Q_B^T Q_B=D_B²I`、`det Q_B=D_B²` 证明叉积及投影事件分子恒含正因子 `D_B=1+u_B²s²`；约消后一般次数≤6，刚体≤5，并单独处理 u_B＝0，避免“除常数硬减两次”。后续退出条件改为**六次实根隔离**；当前≤5次 API 未偷偷放宽。
4. 核对历史 r4 的 15 份逐块表哈希后重分层：500 个零残差**全部且恰为三角形块帧**，其余 14,720 个非三角形均正；表内单列三角形并给非三角形分布。
5. §7 改为实际 `affine_full_r4`、50.122772900009295 秒；保留 1810 步／15220 块帧／64010 块对帧的真实冻结口径。
6. ≤1.101 舍入单位端点重建和约 2.8×10⁻⁶ 步中点偏离，**明确引用工单所载 Claude 验收结果**。本次独立核了输入、分层及证明，不冒称重新完成那两项全数据高精度重建，不把中点值说成全时间上界，也不把描述性坐标尺度说成严格舍入误差定理。

历史 M5a2 报告中“八次”文字保留为历史记录，本次理论 §4/§9 和此报告明确订正为六次，未篡改旧认证。完整 1810 步一般仿射首入、正残差首盖证书、三模型因果分解仍是原 M5a2 遗留，不因 INT1 测试绿而声称已实现。

证据：[理论数据审计](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/theory_data_audit.json)、[独立精确多项式交叉检查](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/theory_polynomial_probe.json)、[R2 独立复核](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_theory.md)。

## 7. 最终四分片、静态、性能及交付核验

有效最终轮次仅 `final_suite_r2_postreboot`。四片最后一行按片号原样：

```text
3390 passed in 757.74s (0:12:37)
3390 passed in 916.95s (0:15:16)
3389 passed in 777.79s (0:12:57)
3389 passed in 1334.00s (0:22:14)
```

静态最后一行原样：

```text
exact construction AST gate: 0 violation(s)
```

全局收集、分片派发、各片实际收集、实际 call 的多重集合严格一致；13,558 个唯一节点，全部阶段 passed，0 skip。不是把派发清单当执行清单。[新增／删除节点清单](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/suite_delta.json)显示新增 87、删除 0。

| 性能口径 | 新基线 | 最终 | 解释 |
|---|---:|---:|---|
| call 累计秒 | 3420.8343042 | 3532.7883834 | 比值 1.03272713，约 +3.2727% |
| 整批 wall 秒 | 1552.4220074 | 1491.364（约） | 比值 0.96066940 |
| 新增 87 节点 call 秒 | — | 2.9668110 | 基线的 0.086728%，低于约5%预算 |

[性能原始数值](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/performance.json)注明 `controlled_host=false`：基线与最终运行部分并发、宿主有其他任务。新增门开销已测且很小，但不能把这些比值夸称为受控的整体性能认证或加速证明；长回放重算不塞进默认 pytest。

新鲜副本执行前后全部路径／字节无漂移；当前源码与实际执行副本无差异、无遗漏。此次遵守工单“不建 worktree”的禁令，使用**新鲜字节副本，不冒称新鲜 Git worktree**，证据中 `fresh_git_checkout=false`。全部 pytest 带 `-p no:cacheprovider` 与显式 `--basetemp`；TEMP/TMP 位于 INT1_evidence/tmp。超过1 MB的节点／执行清单及原始长产物只在 ignored tmp；提交候选证据的编码／大小异常为0。

六路交叉复核对应 R1 回放、R2 理论、R3 静态／watchdog、R4 数值变异、R5 准入历史、R6 最终报告与执行证据。其结论仅覆盖本次实际实现及披露范围；**第6条全库卫生未完成，不能据此宣称完整工单或新里程碑 G6 全量验收通过**。最终 R6 及索引见 [review_delivery.md](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_delivery.md)。

## 8. 复跑与回退锚点

```powershell
$env:TEMP = "$PWD/reports/codex/INT1_evidence/tmp"
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
python -X utf8 tools/int1_run_gates.py --name baseline_new --baseline-head
python -X utf8 tools/int1_refresh_motion.py --name motion_refresh_new
python -X utf8 tools/int1_revalidate_replay.py --name se2_revalidation_new
python -X utf8 tools/int1_run_gates.py --name final_new
python -X utf8 tools/int1_finalize_evidence.py final_new
```

名称必须全新；中断或依赖变化就整批作废重跑。finalize 以本次固定有效基线 `baseline_suite_r2_postreboot` 作为节点差异／性能参考，审计命令指定的完整最终轮次，不会自行拼接旧分片；示例中的 `baseline_new` 是另一次独立诊断，未自动替换该参考。再次发布新重算会改变绑定文件，故必须先重算、再做最终新鲜副本验证，不能只补哈希。

回退锚点为只读 Git 对象 f012d6a、`INT1_evidence/tmp/rollback/` 原字节副本、各次 `*_before.json`。未代为执行 Git 恢复或提交。原始 replay/节点大清单属于本机 ignored 证据；入库小摘要、认证、源码与冻结夹具足以重跑默认 pytest，但不声称新克隆自动拥有本机历史 1810 步全时程输入。

INT1_PARTIAL：第6条仍有19个历史独立变异helper／249条有效准入及112个无逐站点准入的驱动插桩点未集中；其余本单重算、准入约定、语义门、文档与最终全套验证已完成
