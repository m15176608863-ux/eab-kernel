# INT1 R6：最终报告、逐节点执行与交付边界独立终审

审查者：theory_docs 子代理；未编写主报告或 `int1_finalize_evidence.py`。本路线只读核对最终源码、原始执行 journal、报告及其他路线证据，不修改源码、不重跑或拼接测试。

**结论：限定范围内的交付一致性审查通过，0 critical、0 major、0 open minor；工单本身仍为 INT1_PARTIAL。** 第6条尚有19个历史独立变异 helper／249条有效准入及112个无逐站点准入的驱动插桩点未集中，不能因最终测试绿或本审查通过而写成完整工单／新里程碑 G6 通过。

机器证据：[review_delivery.json](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_delivery.json)。所审主报告 SHA256：`ce14528fe857982d6e56d3271f029325bdcd2f304fd05156c16c44bced2f4d9f`。

## 1. 直接读取原始执行记录，而非转录派发数

对有效基线 `baseline_suite_r2_postreboot` 与有效最终 `final_suite_r2_postreboot`，分别读取自己的全局 collection、4片派发清单、4片 execution.json 内实际 collected 和 call reports。每片及全局多重集合严格一致，全局无重复节点；全部记录 complete，未拼接旧运行。

- 基线 **13471 collected＝executed**：13469 call passed、2 call failed；所有 setup/teardown passed；0 skip。失败恰为 M5a2 重验证源码绑定与3103旧准入不可变合同两项，没有第三项。
- 从基线导出源再次逐文件计算：M4c 冻结摘要 **23/23** 绑定匹配；M5a2 的27文件闭包仅 global_entrance.py 一项不同。主报告没有按预期虚构 M4c 红项。
- 最终 **13558 collected＝executed**，三阶段各13558 passed、无其他 outcome；四片 exit_code 均0；静态 exit_code＝0。
- 直接读取8份 pytest shard 命令：均含 `-p no:cacheprovider`、显式 `--basetemp`，其目录均位于 INT1_evidence/tmp。

最终四片文本日志最后非空行与 summary、主报告逐字相同：

```text
3390 passed in 757.74s (0:12:37)
3390 passed in 916.95s (0:15:16)
3389 passed in 777.79s (0:12:57)
3389 passed in 1334.00s (0:22:14)
```

两套有效运行的静态日志最后一行均为：

```text
exact construction AST gate: 0 violation(s)
```

## 2. 节点差异与性能独立重算

从实际 call nodeid 集合重新作差：**新增87、删除0**，与 suite_delta.json 一致。由原 execution duration 重新求和并比对 performance.json：

| 项目 | 独立重算值 |
|---|---:|
| 基线 call 秒 | 3420.8343042000097 |
| 最终 call 秒 | 3532.7883834000213 |
| 新增节点 call 秒 | 2.96681099999887 |
| 新增节点／基线 | 0.0008672770254777608，即约0.086728% |
| 全部 call 比值 | 1.0327271271404632，即约+3.2727% |
| 整批 wall 比值 | 0.9606694047694803 |

主报告舍入值相符，并保留 `controlled_host=false` 的共享宿主局限，没有声称受控加速或严格整体性能定理。新增门的实测成本与本次全套 call 变化均低于约5%，但这不是不受宿主负载影响的上界保证。

## 3. 字节版本、编码与链接

- 独立逐项比较最终导出 manifest：实际执行副本与其清单零差异；非生成证据的当前文件与执行副本零差异、无漏项。未把 fresh byte export 冒称为 Git worktree。
- 恢复后的 `test_m5a2_static_runner.py` 全部235个换行为 CRLF，与原文件的 CRLF 风格一致；恢复后完整另名 r2 从头测试。之前完整绿的 r1 仅为 superseded 历史，不用于本次最终节点拼接。
- 主报告可正确解码为UTF-8且无BOM，**实际汉字4154个、ASCII问号0个**；这项检查专门排除了“问号乱码仍能合法解码UTF-8”的假阳性。
- 主报告中的本地文件链接全部核对存在；非tmp的本单证据没有超过1,000,000字节的文件。详细链接清单在 JSON。
- 初审的复跑示例顺序问题已修：先刷新两套回放，后建立 final_new，最后审计 final_new；并说明新 baseline_new 不自动替换 finalizer 固定的性能参考。

## 4. PARTIAL 与历史证据边界

从 static_work.json 的逐exec清单重新分类、计数：19个独立 helper 对应249条有效准入；112个 test-driver 编译点的逐站点准入为0；另13个故意动态／静态门程序与1个AST builder被正确分开，没有把全部exec都写成同一类缺陷。主报告开头、§5及最后一行均明确披露此未实施工作。

原始三角形／out.csv／次数证明由R2交叉审查，本次主报告沿用其边界：1.101舍入单位与2.8×10⁻⁶来自工单给定Claude验收，未冒称本次全数据高精度重建；1810步一般仿射首入等原遗留不被“集成已绿”覆盖。

## 5. 六路索引及发布顺序

| 路线 | 最终证据 |
|---|---|
| R1 真实重算／发布协议 | [review_replay.md](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_replay.md) |
| R2 仿射理论／冻结数据 | [review_theory.md](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_theory.md) |
| R3 静态／watchdog 最终CRLF字节复验 | [review_static_eol_r1.json](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_eol_r1.json) |
| R4 数值内部变异 | [review_semantic.md](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_semantic.md) |
| R5 不可变准入原对象 | [review_admission_contract.md](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_admission_contract.md) |
| R6 最终报告／执行证据 | [review_delivery.json](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_delivery.json) |

本审查文件冻结后，由主执行者再运行 finalizer 刷新最终 `delivery_audit.json` 与 `artifact_manifest.json`，把本审查文件也纳入清单；避免声称一个自引用哈希清单已经包含尚未生成的审查文件。该最后清单封存不改变源码、已完成运行或本审查所绑定主报告。

R6_SCOPED_DELIVERY_REVIEW_PASS_TASK_REMAINS_PARTIAL
