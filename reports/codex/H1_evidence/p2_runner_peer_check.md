# H1 快慢档执行记录核对

本检查是执行方内部代码核对，不是 Claude 安排的一路独立对抗核查。未另跑全档。

## 已核对

- `h1_run_gates.py` 的派发、收集和实际 call 记录以 Counter 相等核对；跳过、失败、非零退出码或不完整执行均不能 GREEN。
- runner 传入快照 cwd 和 `H1_EXECUTION` / `H1_PROGRESS`；plugin 的 source root 严格限于该 cwd 的 `src/eab`，不是任意路径含 `src/eab` 即计数。
- `audit_module_coverage(source, records)` 的 `complete` 已加入 runner 的 GREEN 合取。清点为 48 个含函数模块、7 个无函数模块。前者要实际函数帧，后者要实际 `<module>` 帧；collection 导入不计执行。
- 函数帧需 `CO_NEWLOCALS` 且不是尖括号代码名；类定义体、推导式和 lambda 不冒充 def 调用。各 witness 的 nodeid 必须属于该 journal 中实际 passed 的 call。
- Python 无 `sys.monitoring` 时 runner CLI / plugin configure 均明确拒绝，不生成无覆盖的 GREEN。
- 每测试 logstart 立即写当前 node 和 `started_epoch` / `last_event_epoch`，teardown 更新；Windows atomic replace 失败最多重试 12 次。计数是 O(1) 更新，避免每节点重扫全部报告。
- runner 用 `as_completed` 消费四片；测试超时/无节点进展/异常中断时清理自身进程树并标 INVALIDATED。快档整档 900 秒，全档每片 10800 秒，节点无进展 900 秒。

## 局部实证

- 新门 `tests/test_h1_module_execution.py::test_declarative_modules_execute_in_fast_test`：`1 passed in 0.05s`；新文件 `scan_text=[]`，没有新增准入。
- 真实 plugin 记录证明 7/7 无函数模块在该测试期间执行；0/48 函数模块被误计。此局部运行覆盖审计正确返回 False，不冒充全模块覆盖。
- 微型独立源码树实际启动 pytest：仅 collection 导入 → False；测试期间 reload 类定义体但不调方法 → False；实际方法调用及模块 reload → True。
- 删除运行时的 `sys.monitoring` 后实际调用 configure 会抛错；journal 缺能力标志也不能通过审计。细节见 `p2_coverage_teeth.json`。

## 重跑

```powershell
$env:PYTHONPATH = "$PWD/src;$PWD/tools"
$env:TEMP = "$PWD/reports/codex/H1_evidence/tmp"
$env:TMP = $env:TEMP
$env:H1_EXECUTION = "$PWD/reports/codex/H1_evidence/module_smoke_execution.json"
$env:H1_PROGRESS = "$PWD/reports/codex/H1_evidence/module_smoke_progress.json"
python -m pytest -q -p no:cacheprovider -p h1_execution_plugin --basetemp reports/codex/H1_evidence/tmp/module_reload_recheck tests/test_h1_module_execution.py
```

快照验证边界：最终版本还比较 live 树文件集与逐文件 SHA256，`live_tree_changed` 非空也不能 GREEN；因此核对时刻 live 树须与被测快照完全相同。仍应冻结编辑后运行，避免中途变动使长跑作废，且不把检查之后的新编辑视为已验证。collection/static 阶段使用阶段超时而非测试节点 watchdog。
