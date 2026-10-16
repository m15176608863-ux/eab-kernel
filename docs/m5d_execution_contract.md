# WO-M5d 执行合同

## 范围与回退锚

- Target：补齐 A 的具名语义门与内部变异证据，完成 B 口径订正；C1 先证明后实现，未完成的研究项明确 PARTIAL。
- Scope：仅 `D:/eab-wt/cx-e2`；姊妹仓库、其他工作树、设计正本只读。
- Non-goals：不切换姊妹求解器，不外推未认证子集，不做 Git 写操作，不以测试全绿替代所有者 G6 验收。
- Baseline / rollback anchor：初始工作树干净，HEAD `5b73cc8dfc1ad4f257412392111927d5a7171640`；只读 `git archive HEAD` 生成基线字节快照存本树 ignored tmp，保留原始字节，不自动恢复。
- Success：A 每类真实内部变异红在具名语义断言；独立 oracle 零失配；B 精确计数与源码行号；C1 只发布证明覆盖的证书；四片收集=执行、0 skip；静态 0 违例；反事实逐站准入审计；绑定闭包发生变化则真实重算。

## 验证与执行纪律

统一 `TEMP=TMP=reports/codex/M5d_evidence/tmp` 的绝对路径，pytest 均 `-p no:cacheprovider --basetemp <本树 tmp 下独立目录>`。
全套：`python -X utf8 tools/m5d_run_gates.py --name baseline_suite --baseline-head`，最终执行另用新目录。
基线和最终均四进程完整执行；禁止工作树操作，因此使用全新字节导出，明确 `fresh_git_checkout=false`。
长跑进度落盘，不复用中断批次；超过 1 MB 的日志、逐节点清单留 ignored tmp。
只新增标准库实现；现有 pytest 是测试运行器，不新增依赖。

## 计划

1. 检查基线与冻结规则，导出并启动基线四片。
2. 分工 A1/A4（R3），A2/A3（回放 R1 / 温和 R2），B（结构与 raw 语义），C1（证明与实现）；先文后码。
3. 独立复核，运行语义变异与全时程证据，检查绑定重算与静态/准入。
4. 新鲜字节导出最终四片，汇总中文报告、交付清单与遗留。

当前阶段：4 已完成（基线与最终四片全绿；最终 13877 收集=执行、0 skip，静态 0 违例；A/B/C1 语义门、独立交叉复核、受影响闭包真实重算与七文件发布、逐站准入净增 0 已完成）。
本单交付状态为 M5d_DONE；所有者六路 G6 独立退出验收不由本执行合同代签。最终报告及 evidence/run_state 保存实际证据。
