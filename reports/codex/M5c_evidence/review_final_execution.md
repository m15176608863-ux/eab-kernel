# M5c 最终执行与报告独立复核

**结论 GREEN；未发现新的交付/统计 critical 或 major。** 此为独立原始证据审计，不替代 Claude 最终独立验收，也不把C尚未实现改写为完成。

## 原始执行

不调用 `m5c_finalize_evidence.py` 的审计函数，而以标准库独立读取 collection.txt、4份派发节点清单、4份 execution.json 和对应逐阶段 execution.jsonl、4份原日志与静态原日志。

- 收集=唯一执行=**13781**；0skip，分片无重叠，41343条setup/call/teardown记录全部passed。
- 每个节点三阶段恰各一次；每片journal与最终execution JSON逐条相同；每片派发顺序严格等于完整收集清单的对应四分片。
- 四片进程exit=0且无timeout；报告和执行摘要中的末行均与原日志逐字一致：

```text
3446 passed in 895.75s (0:14:55)
3445 passed in 738.35s (0:12:18)
3445 passed in 1295.12s (0:21:35)
3445 passed in 692.89s (0:11:32)
```

静态原末行：

```text
exact construction AST gate: 0 violation(s)
```

## 执行同一性

- Fresh export的**6749**个文件集合与manifest完全相等，逐文件SHA均相同；运行前后export_integrity为空差异且complete。
- 当前工作树的**597**个源码/测试/工具/fixture/根配置文件，双向文件集合及字节均与实际执行export相同，新增未执行文件也在核查域内。
- 已审计真实产物的**134**项公开绑定输入在实际执行export中逐字一致；**34**项ignored tmp原始流/进度再次核当前SHA一致。没有把运行后变动的冻结summary当作已测版本。
- `fresh_git_checkout=false`：遵守禁worktree约束的全新字节导出，不冒称新Git检出。

## 数字、性能与报告

从原始call记录重算：基线13656节点，新增125、移除0；新增节点累计10.817297s / 基线3377.440944s = **0.3203%**，低于5%。报告明确这是新增call成本，不把并发宿主墙钟当受控基准。

报告总分母、64010三分类、14079实际比较、68候选、19稳健子集、逐算例分布、raw formal/shared分列和C参考数均与先前独立原始会计一致。C出口认证仍0，49/68仍未证；138非刚体探针只核状态/身份、90名义D=1边界已明确。未发现需修改的报告文本。

18个本地Markdown链接全部存在（父代理已生成交付清单）；报告UTF-8无BOM、LF，最后一行准确为：

```text
M5c_PARTIAL：C 的正误差管出口特征存续、排序实现及稳健子集命中结论未完成；49/68 新接触仍未证且不外推
```

## 文件与后续

- [机器证据](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_final_execution.json)
- [中文报告](file:///D:/eab-wt/cx-e2/reports/codex/M5c_report.md)
- [真实全时程会计复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_final_artifacts.md)

本轮仅写审查文档和ignored tmp探针；源码、测试、已发布summary均未修改。父代理只需最后再生成交付manifest/index以收录本审查；不得再改源码/测试后沿用本次执行结论。Claude验收、C实现与未证49对保持原边界。
