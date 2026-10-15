# R6：四片执行与最终发布证据独立复核

**PASS_PUBLICATION_CONSISTENCY_WITH_DECLARED_PARTIAL；本域 critical 0、major 0。**

本结论接受明示 PARTIAL 的发布，不是完整工单完成或总体 G6 退出。只读 src/tests/tools/fixtures/policy、鲜副本、原始执行和回放记录，仅更新这两份 review_execution 文件。

## 1. 实际执行，不拿派发代替执行

- baseline_r1：13,558 节点，40,674 阶段；全局收集＝四片派发＝各片实际收集＝实际 call（按多重集合），每节点 setup/call/teardown 恰好一次、全部 passed；逐片 JSONL 与最终执行报告相同；0 skip/timeout/错误标记。
- final_r1：**13,656** 节点、**40,968** 阶段，同样逐节点三阶段各一次且全 passed。四片无重叠，0 skip/timeout/错误标记；静态末行是 exact construction AST gate: 0 violation(s)。
- 两轮新鲜字节副本完整文件集合及 SHA256 重算匹配 manifest，runner 前后漂移差分为空。final 共 6,621 个导出文件；其中 src/tests/tools/fixtures 的 571 条路径与当前树的完整路径集合/哈希相同，增删改均为 0。fresh_git_checkout=false，不冒称新鲜 Git 检出。
- wrapper 委托既有 runner；pytest 禁 cache、显式 basetemp，TEMP/TMP 在本树 tmp；stderr 合并日志，watchdog 覆盖到 logfinish（含 teardown），非零退出/未完成/超时/skip 不给 GREEN。
- finalizer 一般漂移循环只检查 manifest 中已列路径，不检查新增路径。本复核额外比较当前完整路径集合，对本次快照无遗漏；未修改已执行工具来绕过绑定。
- finalizer 内存记录负探针：漏 call、重复 call、skip、teardown failed、非零 exitstatus、complete=false 六类均拒绝；未修改真实日志或生产源码。

四片最后一行原样：

```text
3414 passed in 729.01s (0:12:09)
3414 passed in 1249.87s (0:20:49)
3414 passed in 735.89s (0:12:15)
3414 passed in 826.19s (0:13:46)
```

## 2. 最终报告及全量账本核对

主报告：[M5b_report.md](file:///D:/eab-wt/cx-e2/reports/codex/M5b_report.md)  
SHA256：152c83e155893855b3975cfec95f8e3d5d5c592e755d90d47f27b9b4662a14d2

- 重新从 15 个 pairs.jsonl.gz 逐条计数全部 **64010** 对：无重复、每步块对组合齐全、连续 1810 步、15220 块帧；逐例与全局 Counter 均与摘要一致。所有 raw 哈希匹配，发布摘要与运行摘要逐字节相同；52 个源码与 91 个输入哈希逐项无漂移。
- 主报告 15 行分布及合计完全一致：稳健无接触 38681、稳健单首盖 2、未证 25327（初始出口未证 16676、其它无证 8651）；P1/P2 状态/首盖身份不同 0。核验独立全批审计绑定当前摘要与五个最小例。本域没有重复几何求根，不以账本一致替代独立数值证明。
- 主参考表逐项对应账本：raw_df05 匹配/其它 1/3，post_df06 2/2；缺块对均 0；未选为主参考 1/0；稳健无接触参考各 11443。报告明确 primary-only、各 7768 次参考未分类，未扩张“漏检”含义。
- 四片末行与静态末行在主报告中各原样出现一次。execution_audit、performance、suite_delta 与原始执行逐值相符。新增节点 98、移除 0；新增门 call 2.944788900023923 s，占基线 call 的 **0.084130915869%**。报告舍入正确并注明 controlled_host=false；不是整个系统性能的受控对比。
- 准入按 AST occurrence：3558+104=3662 → 3618+77=3695，净 +33；3522 档案行、3416 active context 行、4 ghost pin 口径明确。这里只核对既有逐站清单与发布，不把本人编写的静态准入逻辑称独立数学 oracle。
- 端点五个数值显示与摘要一致；315760/315760 只称精确数值一致、不声称 signed-zero 全位相同，314252 旧计数保留。报告已明示端点摘要仅直接依赖绑定、传递闭包硬化待办，并保留外部 2.8e-6 口径遗留。
- 450 帧真实重算 attestation 为 GREEN，旧归一化结果/夹具字节/旧来源记录保持、当前哈希一致。全部 26 个主报告本地链接存在，主报告 UTF-8 无 BOM。

## 3. 明示 PARTIAL 的边界

报告末行保留：M5b_PARTIAL：已贯入正扰动最短出口排序；legacy次参考；敏感子集P3首入与完整三模型比例；外部2.8e-6口径对齐；完整G6退出

上述五项未完成；端点传递源码闭包硬化也未因本域通过而完成。P3 只由严格管证明稳健子集，未证不等于实测模型不同；不保证首时刻/扰动导数/根唯一性；初态同几何不冒称正管下出口排序稳定；新鲜字节副本不等于新鲜 Git worktree。报告实际表述与证据一致。

机器结果：[review_execution.json](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_execution.json)。本状态只绑定上述主报告 SHA256，后续编辑须重新核对。

R6_PASS_PUBLICATION_CONSISTENCY_WITH_DECLARED_PARTIAL
