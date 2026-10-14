# M4c runner 原子进度写入独立复核

2026-10-14；只读审查 `tools/m4c_run_gates.py`、`tests/test_m4c_runner.py`，未修改生产/测试，未启动全套。范围内 **0 critical、0 major、0 minor**；不是全仓 G6。

## 结论

- host `write_json` 与实际 `PLUGIN.progress` 都只重试 `Path.replace` 的 **PermissionError**。最多12次调用；前11次延迟 `min(.01*n,.1)`，总退避0.65秒；第12次仍失败即原异常抛出。其他异常不重试、不吞掉。待替换 payload 不被误当成功文件，旧目标在失败时保留。
- 组件门独立重跑：`6 passed in 0.09s`、0 skip；新测试 `scan_text` 0违例。[执行证据](review_probes/runner_test_run.json)。
- 另外用真实 pytest 子进程加载从当前 runner 导出的实际 PLUGIN，在 **Path.replace 内部**注入缺陷：[脚本](review_probes/check_runner_atomic.py)、[完整结果](review_probes/runner_atomic_probe.json)。三种场景完整运行，1.888秒：
  - 前两次 PermissionError：每次 progress 第三次成功，真实 collection/call/teardown/sessionfinish 都走过；实际收集1=实际执行1、0 skip、进程退出0。
  - 永久 PermissionError：collection 和 sessionfinish 各一次 progress，每次严格12次、11次退避后抛出；进程非零退出。
  - FileNotFoundError：每次 progress 仅1次调用、无退避；进程非零退出。
- 两种失败场景虽然 sessionfinish 写了 `complete=true`，但 pytest 记录 exitstatus=3、实际 call 节点为空、最终进程非零退出。因此 runner 的 **进程退出码0 AND execution_complete AND dispatch/actual-collection/actual-call 多重集合相等 AND skip=0** 联合条件不会误绿。静态门也必须退出0。

初次额外 probe 因 pytest 自动沿父目录选 rootdir，节点ID多了仓库相对前缀，触发探针自身断言；这是探针输入/预期错误，不是 runner 错误。已显式 `--rootdir`，改用全新 `tmp/review_runner_r2` 完整重跑全部三场景，不拼接旧运行。

## 最终全套节点复核

final_suite_r2 的 summary 已 `complete=true / GREEN` 后，独立执行仅标准库的 [check_final_suite_nodes.py](review_probes/check_final_suite_nodes.py)，重新读取4片真实 execution reports，而非照抄runner汇总结论。确认每片 dispatch=collection=call **含重数**相等、跨片无重复、全体实际执行12974=原收集12974、0 failed、0 skip；进程与记录exitstatus均为0。完整证据：[runner_final_nodes.json](review_probes/runner_final_nodes.json)。

四片日志最后一行逐字核对如下：

```text
3244 passed in 769.96s (0:12:49)
3244 passed in 761.16s (0:12:41)
3243 passed in 761.02s (0:12:41)
3243 passed in 1503.25s (0:25:03)
```

静态门退出0，原样末行 `exact construction AST gate: 0 violation(s)`；runner总墙钟1700.5836133秒。被作废的final_suite_r1未混入节点或统计。这里核验了最终新鲜字节副本的全套执行证据，仍不把它称为提交后Git worktree验证或完整六路G6。

## 被审哈希

| 文件 | SHA256 |
|---|---|
| `tools/m4c_run_gates.py` | `00cefefc2921f4e9b3a4952716096c7516f339be2cef5af9764c8f69dfdca845` |
| `tests/test_m4c_runner.py` | `e17c20ca6e5c98bcebe0004dae886fdc8f7d39834ea9525e805b179618144bfd` |

起止哈希相同；[机器结论与证据哈希](review_runner.json)。
