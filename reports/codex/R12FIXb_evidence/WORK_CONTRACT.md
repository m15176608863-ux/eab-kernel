# WO-R12FIX-b 执行合同

- Target：重做静态构造门局部例外和数据流准入，保持原有牙及 11368 个测试节点。
- Scope：本工作树的工具、必要数值简单化、测试、文档及证据目录。
- Non-goals：不修改姊妹仓库、其他工作树、fixtures；不执行 commit/push/reset/checkout/stash/worktree；不宣称 G6 独立退出。
- Success：静态门 0；局部锁三门和全部原牙通过；例外不超过 200 条，否则如实报告数字和原因；完整测试集合包含原 11368 节点且全绿；执行 fix_canon_ptrs --apply。
- Verification：所有 Python 命令使用 PYTHONDONTWRITEBYTECODE=1 python -X utf8。入口为静态门、pytest 全套、文档指针工具。
- Rollback：baseline/ 保存执行前 218 个相关文件的原字节（扩展名加 .txt），baseline_inventory.json 保存 SHA-256。仅按文件手工回退，不自动覆盖已接受改动。
- 初始 HEAD：0ce65a44c9c26d99411cee68d7300e7b5521bb40。保留未提交 R12FIX 改动。

## 计划

1. [已完成] 盘点、字节备份、原 11368 节点清单。
2. [已完成，本轮有限范围] 数据流子集、局部锁、动态数值写法简单化及独立定向审查；最终重分类后仍有 16 条数值动态排除待改写。
3. [已完成逐站点核对] 安装 2365 条局部遗留排除；超过 200，未宣称安全证明或独立批准。
4. [已完成验证和交付] 最终 full_suite_release：11508 条全绿，原 11368 节点全保留，新增 140；墙钟 551.694103 秒；源码/policy/关键文档无漂移。静态 CLI 0；三道可维护性门与原牙通过。报告 135 个本地链接已核验。

最终验收状态：PARTIAL。2365 条局部排除仍超过 200；16 条数值动态规则记录待改写；642 条证明缺口与 467 条近似/名义范围排除未关闭。本计划的验证/报告工作已完成，不表示工单所有实现目标完成。

- [主报告](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_report.md)
- [机器可读状态](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/final_validation.json)
- [最终全套](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/full_suite_release/summary.json)

首轮最终验证失败：165 条清单节点错绑（168 个实际诊断）及 R10 裸 intrinsic sink 漏接线；另修正 39 条过时/错配理由。初版与红证据保留。修正不增加排除、不刷新作用域 hash，重新冻结跑全套。

## 已发现的执行偏差

早期一轮含 tmp_path 的定向 pytest 未显式指定 basetemp，生成了系统 TEMP 下的临时测试夹具。已只读核实并记录于 dynamic_temp_scope_deviation.json；未删除或修改这些外部文件。后续含临时路径的测试一律指定本工作树证据目录下的独立 basetemp。最终报告必须披露，不能声称全程零外写。
