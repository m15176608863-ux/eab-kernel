# M4c 重启中断与恢复记录

所有者报告：2026-10-14 约 08:53（Asia/Singapore）电脑重启，运行中的子进程被终止。

## 重启后检查

- HEAD 仍为 `870045c`，分支仍为 `codex-work`；没有 Git 状态变更操作。
- 新增设计稿、运动内核草稿和四分片工具文件在盘；Python 文件能 AST 解析，但解析通过不是实现验收。
- 原 `baseline_suite/` 有收集清单和导出 manifest；四个分片日志都是 0 字节，没有任何执行记录或最终 summary。
- 原基线运行整体标为 `INVALIDATED_INTERRUPTED`，不使用收集结果、分片片段或旧计时作为通过证据。
- `kinematics_audit.json` 是完整 JSON，但其中文 Markdown 在中断前曾因 PowerShell 输入编码写成问号。
  恢复后用原生 UTF-8 重写，并重新执行 15 例源数据复制、哈希及几何/时序审计；新旧完整输入哈希和计数一致。

机器检查及旧文件哈希：[interruption_audit.json](interruption_audit.json)。
旧运行废弃标识：[baseline_suite/INVALIDATED.json](baseline_suite/INVALIDATED.json)。

## 全新运行原则

基线在 `baseline_suite_r2/` 从只读 `git archive HEAD` 导出新的无.git字节副本，**从头**收集、四进程执行及静态扫描。
它不是新鲜 Git worktree；所有者禁止 worktree 操作，不能冒称满足提交后检查。
最终代码全套另用全新目录，旧日志不拼接。其他已中断或主动停止的探针只作问题定位，不能冻结成验收结果。

`tools/m4c_run_gates.py` 现在原子写入 `run_state.json`、各进程进度和每个测试节点的计数；
逐节点 journal 在忽略的 tmp 目录，最终执行清单另存。
只有完整 sessionfinish、退出码 0、实际收集=实际执行、0 skip 和静态门通过的 final summary 才是 GREEN。
回放工具同样逐步 flush 记录与进度，并将完整性、输入哈希、代码哈希写入最终摘要。
再次中断后保留原目录并新目录全量重跑，不将“进度落盘”误解为允许拼接半次运行。

## 第二次中断：09:16 会话终止，10:37 再次重启

所有者第二次续单说明：2026-10-14 约 09:16 启动本任务的上层会话结束，进程被终止；
从该时刻起无任务进程运行，约 10:37 电脑再次重启。恢复时未发现本单存活 Python 进程。
HEAD/分支仍为 `870045c / codex-work`，工作树保留未提交改动。

- `baseline_suite_r2/`：没有最终 summary，虽然有逐节点 journal 和进度，**整个运行作废**。
- `full_replay/`：没有完整批次 summary；其中个别案例已有 complete 审计，但它们不拼入下一批。
  该首批此前也因附属 CSV 额外步号别名 fail-closed 审查需要修复；整体作废，保留问题现场。
- 原内核组件门、PD 组件静态检查、运动学源审计和 `mutations_r2/` 存在完整文件；
  只在最终源码哈希吻合时使用，代码改变则重新运行对应组件，不从未完成日志推算结果。
- 重启/中断前未完成的独立探针、静态扫描不能作为完成证据。

旧目录文件哈希及完整性核查：[interruption_audit_2.json](interruption_audit_2.json)。
第二次作废标记：`baseline_suite_r2/INVALIDATED.json`、`full_replay/INVALIDATED.json`。

依第二次续单授权，**不再重跑起点基线全套**。引用 M3 报告中 870045c 之前树的四分片时间，
明确它“不是同字节基线、只作耗时参考”，不能据此宣称严格的前后性能百分比。
最终代码全套仍必须在实质工作和全时程回放完成后，从新目录完整跑成一次；不使用旧分片拼接。
优先级调整为：理论/内核/门完成并落盘 → 全 1810 区间与冻结 450 区间完整回放 → 最终四片全套。

## 最终全套 r1 验证失败，不作为通过证据

`final_suite_r1/` 从新鲜字节副本启动后，溯源完备性门发现两个新增 M4c 夹具尚未登记中央
`fixtures/PROVENANCE.json`；另一个分片的 pytest 进度钩子在 Windows `Path.replace` 时遇
短暂文件占用 `PermissionError [WinError 5]`，内部退出 3，虽末行写有 298 passed，实际只执行了该片的部分节点。
执行记录的 `node_sets_equal=false` 正确阻止该片算绿。

根代理确认命令行后只停止本次 runner 与仍运行的分片，PID/命令行清单留在 tmp。
整个 `final_suite_r1/` 标为 `INVALIDATED_VERIFICATION_FAILURE`；任何已通过节点与计时不拼入下一次运行。
补登两个夹具（旧 198 条登记逐项不变），并给进度原子替换增加有界 PermissionError 重试门。
修复后必须在新目录 `final_suite_r2/` 从头导出、收集、四片完整执行及静态扫描。

## full_replay_r2 主动作废：输入失败闭集与公开对象合同修复

第二次续单后启动的 `full_replay_r2` 不是重启遗留半次运行；它于源码审查中被主代理明确要求主动停止。
新发现的窄输入路径是 gzip 截断引发 EOFError：原工具虽非零退出，但不能持久化 audit RED。
同时公开 QuadraticTime 的非数值等同/hash 合同存在小缺陷，需要统一修复并重新绑定源码哈希。

核对命令行属于当前树 M4c 后，只停止回放父 PID 29996 和仍存活的子 PID 17420、32412。
该批次所有完成子例、进度与部分规范化记录均保留，但**整体作废，不复用，不拼接**。
修复后真实截断 gzip 红门及缺/坏 audit、非零子进程、启动异常的批次 RED/incomplete 门均已通过。

主代理正式宣布最后生产源码冻结后，从全新 `full_replay_r3/` 重跑全部1810区间，成功后串行执行
`frozen_replay/` 的完整450区间，然后生成持久摘要与最小复现。初始父 PID 8712，完整命令及子 PID
保存在 [replay_r3_process_start.json](replay_r3_process_start.json)；运行阶段与最终源哈希见
[WORK_STATUS.json](WORK_STATUS.json)。进程进度不是通过证据，仍必须等批次 complete=true。

## full_replay_r3 主动作废：统一最外层输入审计边界

在 r3 早期的最后输入审查中，确认复用读取器对 JSON 顶层标量/null 等坏形状会抛 TypeError，
仅把 EOFError 加到有限异常列表仍不足以封闭入口审计。主代理要求再次整体作废 r3，
不复用其中任何子例；停止范围仍只限核对命令行后的本树 M4c 父子进程。

最终修复把 `Exception` 统一捕获限定在 CLI 的**最外层审计包装**，保留异常类型/信息及非零退出，
没有增加几何 fallback，没有把失败改成结果；`KeyboardInterrupt` / `SystemExit` 属于 BaseException，仍传播。
审计输出自身失败只尝试一次并写 stderr，不无限重试。81 个针对门通过，涵盖真实CLI坏顶层/嵌套形状、
JSON/UTF8/gzip、endpoint schema、运行时异常和系统中断边界，详见 `replay_input_guard_final.log/xml`。

主代理确认 replay 最终哈希 `4d6689f52a084ee462f55c376050c5a93ec87541e14d54835d124f36452dcd7c` 后，
才启动全新 `full_replay_r4/` 的1810区间；其成功后串行完整执行 `frozen_replay/` 450区间。
最后运行启动进程见 [replay_r4_process_start.json](replay_r4_process_start.json)，没有拼接 r2/r3 完成子例。

## frozen_replay 整批作废：输出路径发布异常

full_replay_r4 全1810区间已经完整成功。随后 frozen_replay 的15个子例也都计算完450区间，
但驱动发布 expected.json 时把相对 --out 路径直接 relative_to(绝对ROOT)，导致 ValueError、CLI退出1。
这不是系统中断，也不是几何核失败；仍按主代理要求把整个冻结批次标 INVALIDATED_PUBLISH_FAILURE，
不复用其任何case结果。最小修复是驱动入口 out.resolve()；新增
`test_frozen_relative_output_path_publishes_expected_fixture` 精确复现原异常路径。
修后在全新 frozen_replay_r2 目录完整重跑450区间，原目录专门忽略，避免重复规范化数据进入交付。
full_replay_r4 的完整计算不受该发布问题影响，继续通过最终驱动的同批只读 verify-batch 重审。

## 最终闭环：完整批次与最终四片各自重新完成

最终有效批次为 `full_replay_r4`（15 例、1810 区间）与 `frozen_replay_r2`（15 例、450 区间）；
两者 final summary 完整，并由最终驱动对各自**同一完整批次**复核通过，未借用作废目录的任何片段。

`final_suite_r2` 在全新字节导出上完整结束，进程退出 0；四片末行为：

```text
3244 passed in 769.96s (0:12:49)
3244 passed in 761.16s (0:12:41)
3243 passed in 761.02s (0:12:41)
3243 passed in 1503.25s (0:25:03)
```

独立逐节点复核确认 12974 实际收集 = 12974 实际调用，跨片重复 0、failed 0、skip 0；
全仓静态 `exact construction AST gate: 0 violation(s)`，总墙钟 1700.583613 秒。
见 [最终 summary](final_suite_r2/summary.json)、[独立节点复核](review_probes/runner_final_nodes.json)。
恢复程序的工作已闭环，但算法/验收剩余范围仍按 [总报告](../M4c_report.md) 的 M4c_PARTIAL 处理；
完成一次新运行不使任何中断或失败批次重新有效，也不消除早期 TEMP 工作域偏差。
