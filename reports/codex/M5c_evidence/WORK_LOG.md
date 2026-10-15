# WO-M5c 执行合同与进度

## 合同（2026-10-16）

- Target：A1–A7 语义补牙和证据绑定完成；B/C 先证明再认证，未证保留 PARTIAL。
- Scope：仅 `D:/eab-wt/cx-e2`；姐妹库、其他工作树与设计正本只读。
- Non-goals：不更改姐妹求解器、不主张物理路径已知、不把未证当实证差异；不执行 Git 写操作。
- Success：指定内部变异红在目标语义断言；完整冻结摘要开始/结束闭包一致；真实重算；最终四进程全绿、收集=执行、0 skip；静态零违例与逐站反事实准入审计；中文报告逐项标状态。
- Verification：`python -X utf8 tools/m5c_run_gates.py --name final_suite`；专项 pytest 均 `-p no:cacheprovider --basetemp <本树M5c tmp子目录>`；真实回放使用新目录、进度落盘、中断整批作废。
- Rollback anchor：经只读核验，初态干净，HEAD=`efb0dfe514a1f60c44e6341b69cce77ff5c9ec17`；baseline_suite 使用只读 `git archive HEAD` 字节导出；所有修改保留 diff，不自动回滚。
- 临时目录：`reports/codex/M5c_evidence/tmp/`（ignored）；大日志/节点清单只存该目录。
- 新鲜验证：用户禁止 worktree/clone 等 Git 写操作，以新鲜字节导出验证，明确不冒称新 Git checkout。

## 计划

1. DONE 基线/理论/证据规则核对；基线四片在新鲜字节副本执行。
2. DONE A：代码、专项门、端点/稳健全量真实重算和联合发布已验证。
3. DONE B：68 对诊断、R3 证明/实现/独立对抗完成，2→19；C 理论复核完成但实现未完成，保留 PARTIAL。
4. DONE 真实重算、联合发布、最终四片、静态/准入与中文报告；最后独立交付复核收尾。

## 进度

- 基线 HEAD 与工作树已核验；memory registry 无本项目相关命中。
- 三路并行：A1–A4 语义补牙；A6–A7 绑定；B/C 研究。主代理负责 A5、回放集成、最终验证与报告。

- A1–A4：49专项/22内部变异绿；A6–A7当前固定13规则/4测试文件，政策零新增，端点29与稳健21运行时闭包。
- A5独立复核发现VE锁长提示m4误作第二参考；完整回放r1作废并终止所有worker，未发布/未拼接。修复区分VV第二参考与完整共边槽，283188行独立oracle零失配后从头r2。
- 端点真实重算15220块帧完成，全部精确极值未变，闭包29文件首尾一致。五个真实最小例另行重算发布。
- R3采用同时间相对有理包络+简单环保持；静态局部0违例，独立对抗复核已完成，68候选重新求解/扩证已完成，19获证、49未证；C边界特征存续未实现，保持PARTIAL。

## 最终验证

- 完整有效稳健 r2：1810 步 / 15220 块帧 / 64010 对，5014.223 秒；21 源首尾一致。研究 r4 对 68 候选重新求根扩证，19 通过。
- 联合发布 complete；实际产物专项 130 passed，0 skip/0 deselect；独立逐行重解码 283188 条参考，零失配。
- final_suite 新鲜字节副本：13781 收集 = 13781 执行，0 skip；全部 setup/call/teardown passed，静态 0。执行审计比对当前源码/测试/配置/fixture，无漂移。
- 基线/当前反事实逐站 3391/3391，净增0；新门 call 时间 10.817s，占基线 0.3203%。
- Git 差异校验用只读临时 cr-at-eol 选项识别仓库合法 CRLF（未规范化冻结字节）；无 whitespace 错误。
- A 完成，B 扩证完成并保留49未证；C仅严格条件定理，未实现，整体 M5c_PARTIAL。
- 结果见 [中文报告](file:///D:/eab-wt/cx-e2/reports/codex/M5c_report.md) 与 [交付清单](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/DELIVERY_INDEX.md)。
