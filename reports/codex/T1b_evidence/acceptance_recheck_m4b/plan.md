# T1b m4b 第二轮复验返修计划

目标：同一凹障碍不同凸片的端点式变异必须被语义门杀死；原版正确拒绝伪困住闭路并判可逃逸；两处措辞准确；最终快档与四分片全档全部通过。

范围：仅本工作树及 D:/eab-evidence/reports/codex/T1b_evidence/。非目标：不改生产代码/数学合同/静态准入/冻结数据，不改图名、不重新计算B，不做Git写操作。

回滚锚：初始干净的773b760；三份待改文件原字节及验收输入SHA见intake.json。不得用回滚覆盖所有者后续更改。

1. **完成**：核对反例，补同障碍语义门与源码内变异门，原版绿/变异红；定向静态检查。
2. **完成**：仅订正报告的两处措辞及本轮状态，冻结待测字节。
3. **完成**：完整快档（约5分钟）及全档四分片（约24分钟）；H1正常模式验证当前树字节导出，并核当前树前后不变。pytest禁cacheprovider、显式basetemp，TEMP/TMP均在本单tmp。
4. **完成**：记录两类端点变异边界、原样门末行、哈希/链接/净增审计，依实测决定DONE或PARTIAL。

验证命令：`python -X utf8 tools/tia2d_t1b_run_gates.py --name m4b_fast`；`python -X utf8 tools/tia2d_t1b_run_gates.py --name m4b_full --runslow`。不覆盖既有acceptance_fast/full证据。

实测结果：定向35 passed；独立源码m4b变异原版1 passed/变异1 failed并命中语义断言；完整快档8853、四片全档14937，0失败/跳过，静态0违例，66/66执行见证。报告末行T1b_DONE；最终字节/归档/卫生见各JSON，不把旧绿灯冒作本次验证。
