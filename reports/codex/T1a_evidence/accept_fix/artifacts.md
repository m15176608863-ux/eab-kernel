# WO-T1a 返修交付索引

当前工作树未提交；HEAD仍为Claude暂存的b0c1cbf。来源提交待Claude从fc9675c重建后登记。独立对抗复验与新鲜Git树验收由所有者安排，本轮不代称已合入。

## 关键文件

1. [中文报告](file:///D:/eab-wt/cx-e2/reports/codex/T1a_report.md)：模型边界、订正、两项批准偏离、P2退化、完整快档/全档原样末行。
2. [批准schema](file:///D:/eab-wt/cx-e2/docs/eab2_case_v1_tia2d.md)：tia2d-2，CLAUDE-APPROVED-TIA2D-2 / 2026-10-19。
3. [新语料目录](file:///D:/eab-wt/cx-e2/fixtures/eab2_cases/tia2d-2/formal_20261019_02/)；[批清单](file:///D:/eab-wt/cx-e2/fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64/manifest.json)；[gzip双SHA索引](file:///D:/eab-wt/cx-e2/fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64/gzip_index.json)。114角色、1086正式冷查询、165gzip分片；先解压再按原JSON字节SHA核验。
4. [加强回读](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_fix/readback.json)；[验证器版本和执行](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_fix/strict_readback_execution.json)。独立解码/点积核证书+复算生产查询，不是独立力学求解器。
5. [完整快档](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_fix_fast/summary.json)；[全档四分片](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_fix_final/summary.json)；[无Git副本](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_no_git/summary.json)。8689、14665、587项通过，不能混加为独立测试数。
6. [六个真实源码变异](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_critical_mutations_03/summary.json)；[曲率证据](file:///D:/eab-evidence/reports/codex/T1a_evidence/accept_fix/curvature_probe.json)；[图件](file:///D:/eab-wt/cx-e2/reports/codex/T1a_figures/)。
7. [卫生快照](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_fix/hygiene.json)；[门后源码核对](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_fix/post_gate_source_check.json)；[逐文件交付SHA](file:///D:/eab-wt/cx-e2/reports/codex/T1a_evidence/accept_fix/artifact_manifest.json)。这是交接快照，不作为当前源码必须等于历史证据哈希的回归测试。
8. [外归档台账](file:///D:/eab-wt/cx-e2/reports/EVIDENCE_ARCHIVE.md)；[批准外归档目录](file:///D:/eab-evidence/reports/codex/T1a_evidence/)。590文件177,844,383B按四份清单逐SHA保存；旧binary64批不留工作树，新原始JSON和Python-only也在外归档，fixtures仅保留新binary64gzip批。

## 读取与复跑

- `tools/tia2d_readback.py`可直接读取gzip批目录；不导入编码器或几何种子传播辅助函数。
- `tools/tia2d_no_git_check.py --name <新名称>`使用只读git archive并覆盖返修字节；明确不是新鲜Git工作树。
- `tools/tia2d_run_gates.py --name <新快档名>`；全档再加`--runslow`，固定四分片。
- 所有pytest均禁cacheprovider并显式basetemp；TEMP/TMP在本单evidence/tmp下。不得复用已完成或中断的运行目录。
- 报告末行所列非退化形貌族转T1b；lock UNPROVED与INVALID_INPUT自然正式角色仍标缺失；不把多边形零锥外推光滑曲面。
