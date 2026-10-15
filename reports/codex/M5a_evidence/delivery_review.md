# M5a 交付独立复核

状态：**FINAL_ACTUAL_GREEN_PENDING_LAST_MANIFEST_REFRESH**。只读审阅源码、测试与运行证据；本复核未修改被审工具或数值源码。最后仅需主执行者在报告、本文和 JSON 全部落盘后刷新 artifact 清单，复核者再只读核清单，不回写本文以免哈希循环。

## 实际四片与静态门

独立直接读取 collection、四份分发清单、执行 JSON 和日志，不导入被审审计脚本：**13254 唯一收集 = 分发 = 实际收集 = call 执行，0 skip**。每个节点恰好一条 setup、call、teardown，共 39762 条记录均 passed。以下为日志原样末行，已与 summary 逐字核对：

```text
3314 passed in 739.15s (0:12:19)
3314 passed in 714.95s (0:11:54)
3313 passed in 737.78s (0:12:17)
3313 passed in 1426.50s (0:23:46)
```

静态门实际日志末行：`exact construction AST gate: 0 violation(s)`，退出码 0。

baseline 同样独立核实 **13110 收集 = 13110 call 执行，0 skip**，全部阶段 passed。baseline 节点全部保留、0 删除；新增 **144 = 回放 49 + SE2 38 + 代数 26 + 独立 oracle 15 + 夹具溯源 16**，无未解释新增。

## 源码与交付文件新鲜性

- 实际执行 export 清单 **5549** 个互异文件，全部重新计算 SHA-256：0 缺失、0 字节差异；独立枚举 export 目录：0 清单外文件。
- 当前受保护输入 **5466** 个，全部与执行 export 一致，0 遗漏新增输入。当前比较仅排除 `reports/codex/M5a_evidence/**` 和本单主报告；这两类生成交付物另做清单与编码核验。
- runner 的 pre/post export 完整性记录均空差异。当前两份被审工具、实际 export 副本和导出清单 SHA 一致；具体 SHA 见配套 JSON。
- 本次复核时 **159** 个改动候选的文本均 UTF-8 无 BOM；提交候选中无超过 1,000,000 字节的本单运行产物。
- 最终 collection 日志、export 清单及四片执行 JSON 共 **6** 个超过该阈值的大文件，逐一用 `git check-ignore` 核实均被忽略，保留作本地证据而非提交候选。

## 脚本复审发现的闭合

- **DEL-01 已闭合**：runner 在实际执行前后核验清单全部文件；运行后差异直接令结果非 GREEN。finalizer 复核实际 export，并比较当前全部非生成输入，含文档、配置、历史报告和遗漏新增文件。实际证据也已独立通过上述检查。
- **DEL-02 已闭合**：finalizer 先生成节点、性能、环境文件；生成 delivery 审计后重新枚举候选供 artifact 清单使用；生成清单后再次校验编码与大小。最后刷新仍须在所有报告落盘后执行。
- **DEL-03 本次范围已核实，但不宣称普遍环境免疫**：runner 仍继承 PYTEST_ADDOPTS 等。本次环境无 PYTEST_* 选择项；全部 baseline 节点保留，新增节点均已解释，未观察到选择污染。
- **DEL-04 已闭合**：未只信 summary；四片日志原样末行、全部实际阶段记录均直接复核。

## 性能与边界

独立按记录的每个 binary64 duration 转为 Fraction 求和；与发布聚合值之差均在顺序浮点累加误差界内。

- 最终 / baseline 总墙钟比：**0.9420509763221585**。
- 最终 / baseline call 阶段合计比：**0.903895159160933**。
- 名称属于新 M5a 门的 call 合计 **11.012201599936816 秒**，占 baseline call 合计 **0.2974418887527642%**，精确比值小于 5%。

这些是共享主机上的描述性计时，`controlled_environment=false`；不得据较快的最终运行宣称受控加速或严格总回归上界。call_seconds 是并行各 call 阶段墙钟之和，不是 CPU 时间，不含 setup、teardown；按 test_m5a 名称计算的新增门占比不含旧门间接开销与新增 16 条溯源参数行。总墙钟从导出完成后开始，含收集、四片、末尾静态门及完整性检查。

本次是全新字节导出，不是新鲜已提交 Git 工作树；不能替代常驻纪律 D 或独立六路 G6。本文仅确认所列交付执行与证据合同，不提升研究模型的认证范围，不改变主报告的 PARTIAL 结论。

## 最后待办

主执行者刷新 artifact_manifest 后，由本复核者只读核候选集合、逐文件 SHA/大小、本文及 JSON 和主报告的新哈希，再以消息确认。配套机器证据：[delivery_review.json](file:///D:/eab-wt/cx-e2/reports/codex/M5a_evidence/delivery_review.json)。
