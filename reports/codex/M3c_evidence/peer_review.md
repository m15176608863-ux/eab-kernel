# WO-M3c 定向同伴复核

审查者：`interval_gates` 子代理，只读复核四片执行器、450 帧重算执行器与三维独立 oracle/变异门。本文由根代理依照审查者消息及机器记录恢复中文，修正原 Markdown 写入时的编码替换；不改变审查结论。

## 结论与范围

审查范围内 **0 critical、0 major**。这是工单内定向复核，**不是六路 G6，也不替代 Claude 的独立验收**。

- 四片执行器逐片核 dispatch、实际 collection、setup/call/teardown 的 Counter，所有报告必须 passed 且完整；重复、漏执行或 skip 都不能满足 GREEN。
- 原始大记录、导出和 TEMP/TMP 留在 `M3c_evidence/tmp`；只使用只读 `git archive`/`git ls-files`，不操作姊妹库。新鲜字节副本不等于新 Git worktree。
- 重算器真实启动 15 个回放进程，每个调用 `frame_result` 遍历 30 帧；独立重读 normalized 450 帧与原记录逐值比较，并核输入、分类聚合、每帧散列和生产源码前后不变。
- 三维 oracle 仅导入 Fraction/product，以手工声明的笛卡尔凸盒并、完整支撑事件、网格暴露矩形和钳位距离计算期望，不消费生产分解/SAT/hull/clip/距离结果。
- 有理旋转矩阵精确正交，转置反变换和距离平方缩放正确。
- 来源平面变异发生在 `explicit_boundary` 内部，分别穿过邻胞、完整覆盖、最短出口检查。
- closed-only EE 的交叉长条样本位于解析盒差边界面内部、VF/FV 条带之外；独立面法向检查确认是锥边缘，不是严格有效。
- 退化片审计先检查点数、非零叉积和共面性，再做重心计算，避免空片除零伪装成语义红。

## 小项及后续处置

审查初版指出：`expected_fixture_unchanged=True` 当时仅由无夹具写入行为支持，缺少并发期间前后散列核验。根代理已加入 expected.json 与全部 normalized 夹具的前后散列守卫，并整批重算 r2，450 帧全部一致；具体计算证据见 [r2 认证](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/motion_refresh_r2_attestation.json)。审查原记录保留，不追改其被审版本哈希。

本审查本身不声称执行了最终四片；运行结论以根代理最终审计为准。结构化五族与刚体变换也不是随机实体穷尽证明。

[原始机器审查记录及被审文件散列](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/interval_peer_review.json)
