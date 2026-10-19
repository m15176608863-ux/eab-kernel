# WO-T1a 验收返修执行合同

- 目标：落实 Claude 验收裁定 A–D，形成可核验的 tia2d-2 小体积语料与诚实的 PARTIAL 报告。
- 写域：当前工作树；另仅 `D:/eab-evidence/reports/codex/T1a_evidence/` 获准外归档。验收 scratch、其他树只读。
- 非目标：不 commit / push / reset / checkout / stash / worktree / branch；不修改钉版设计；不新增静态构造准入；不将多边形结论外推光滑曲面。
- 回退锚点：开工干净 HEAD `b0c1cbf8043e48b02070f814d121ffa987a62f09`，归档保留原字节并核 SHA。Git 重建由 Claude 执行。
- 成功检查：六个阈值/回收变异由语义门检出；schema 精确字段与独立读取通过；无 git 的 archive 加返修字节副本 TIA 测试零失败；gzip 固定时间戳且双 SHA；快档及全档四分片零失败、零跳过、静态零准入变化。
- 批准：`CLAUDE-APPROVED-TIA2D-2 / 2026-10-19`；设计偏离仅 dof_anchor 与极大共线段内部平坦顶点不出约束。

## 执行顺序（单一集成阶段在途）

1. 完成：阅读验收输入，核心、schema、几何三线返修；150 项集成定向门、50 项形貌含慢档门通过，新增/改动静态 0，六个真内部变异被语义门检出。
2. 完成：114 binary64角色、1086冷查询及2个Python-only角色导出；完整加强回读通过。导出时源码清单真实保留，后续只加强读取器并另记验证器SHA，没有改变冻结数据。此前并行修改触发预检来源守卫，已作废，不拼接成成功批。
3. 完成：165 gzip分片（4,581,793 B）、169个fixture文件登记，394项fixture/来源门通过；590个原始/历史证据文件逐SHA外归档；报告和图已订正。
4. 完成：无git archive字节副本587项通过；完整快档8689项与全档四分片14665项通过。两档模块执行63/63、0失败/跳过、节点多重集合一致、冻结字节未变；全库静态0违例。最终报告填原样末行，卫生/交付索引另存本目录。

## 重跑入口

所有 pytest 使用 `-p no:cacheprovider --basetemp <独立证据 tmp>`；TEMP/TMP 指向本单 tmp。
最终：`python -X utf8 tools/tia2d_run_gates.py --name accept_fix_fast`；`python -X utf8 tools/tia2d_run_gates.py --name accept_fix_final --runslow`。
中断运行作废，另起全新运行名，不拼日志。不把验收方的独立求解器结果冒充本轮自产证据。

## 工期估计

定向修改与集成耗时依门而定；冻结后的新语料约 8–12 分钟、读取约 2 分钟、快档约 5 分钟、全档四分片约 28 分钟；不为改文重复全量计算。
