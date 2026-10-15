# INT1 R3：恢复 CRLF 后的全新独立复核

结论：**限定范围通过，0 critical、0 major、0 minor。**

本轮不是只换哈希：在 `tests/test_m5a2_static_runner.py` 恢复原 CRLF 后，以全新临时目录从头执行比较器、准入域、独立 teardown 探针和完整 76 项专项。旧 `review_static.md/json` 原样保留为历史，本文件及同名 JSON 承担最终字节绑定。

被测文件 SHA256：

```text
0c529b472d61621a66f3ea708e5511c1fe432741a012a258dca8864afc4eeaa9
```

独立读取确认 235 个 CRLF、0 个裸 LF。源码/测试/policy 均未由本审查修改。

## 从头执行的检查

| 范围 | 本轮结果 |
|---|---|
| 初审十种高阶绕过，普通与测试驱动两种路径 | 20/20 命中指定 `algebraic-comparator-site`，原 major 保持关闭 |
| 统一插桩的精确 scope | 9/9 合法插桩域可识别；八类数值/比较器规则均不被该域豁免 |
| 域篡改 | 改 scope、未知 oracle、临时副本中改变 helper 字节均使准入失效 |
| 数值 oracle 隔离 | 二次式首入与 L∞ 残差数值门不在插桩准入域内 |
| 独立 teardown 控制组 | 新写 fixture 的 teardown 休眠 2 秒，watchdog 0.5 秒；真实进程以 124 退出，记录对应节点且不发布完成清单 |
| 独立 teardown 内部变异 | 把真实插件取消定时器的 `pytest_runtest_logfinish` 改成 `pytest_runtest_teardown`；变异进程错误地以 0 完成，指定断言 `independent teardown must remain under watchdog` 报红 |
| 完整静态/runner 专项 | `76 passed in 3.27s`，退出码 0 |
| 前后源码绑定 | 静态门、subset、policy、helper、测试文件、runner 六份文件执行前后 SHA256 全一致 |

独立 teardown 探针不调用源码哈希门；缺陷注入在实际插件钩子内部，不通过伪造超时产物制造红灯。

## 命令与证据

专项实际命令包含 `-p no:cacheprovider`、全新 `--basetemp=.../tmp/review_static_pytest_eol_r1`；两个独立 teardown 子进程也各有新目录与显式基目录。全部 `TEMP/TMP` 均指向 INT1 专用 tmp；日志由 Python 显式 UTF-8 写出。

- [完整机器复核](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_eol_r1.json)
- [76 项完整日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_pytest_eol_r1.txt)
- [独立 teardown 控制日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_teardown_eol_r1_control.txt)
- [独立 teardown 变异日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_teardown_eol_r1_early_cancel.txt)
- [完整运行进度](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_static_eol_r1_progress.json)

仍保留有限正子集边界：本门不是任意 Python 反射的完备证明；76 项专项也不替代另行全新执行的最终四片门。其他数值语义与理论证据未受本次换行修复影响，本轮没有无故重写它们。

R3_EOL_PASS_SCOPED_REVIEW
