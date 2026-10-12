# R13FIXb 交付生成/验证逻辑只读审查

范围：`finalize_report.py` 与 `verify_artifacts.py`，辅读全套 runner 的快照/集合定义、首轮失败回执及现有统计/日志。不是内核重新审查，也不是 G6。未执行两个交付脚本、未修改源代码、测试、工具、政策、文档或 runner；只新建本审查证据。

## 结论

**报告模板的 PARTIAL 口径与现有证据一致；初审发现的两处交付验证逻辑弱点已由主代理修复，本代理复读确认闭合。** 审阅时最终四片仍在运行，`full_suite_verified/summary.json` 与最终报告尚未生成；本审查绝不提前宣布全套绿。

## 核实通过的事项

1. **136 项并未被夸大为全域已证明**：模板分别称 107 项独立三档逐值门、29 项非构造证明，列出原 138 项内的 2 个 gap；另明列 adapter `cone_tol/metadata` 两个平台有限门。明确“不能据此声称全公开 API 都已满足合同”及全仓近似入口仍未闭合，末行是 PARTIAL 而非 DONE。清单集合为 138 唯一 API，原 915 行、额外 31 行、原 11723 节点的数字均与本地 JSON 一致。
2. **生成不能凭空绿**：finalizer 要求已存在的最终 summary 为 PASS 且全部 checks 为真；当前缺 summary 就不能生成。分片末行与耗时取自回执，不是硬编码绿色字符串。更新后的 finalizer 还直接核 `root/static_release.log` 末行为 `exact construction AST gate: 0 violation(s)`，兼容现有 UTF-16 日志。
3. **首轮 FAIL 保留**：`full_suite_final/summary.json` 当前仍为 FAIL，完整收集/执行 11994 节点、5 个失败报告，墙钟 600.330339 秒，漂移列表为空。模板如实区分真实次正规报告回归与旧变异工具失配，链接失败证据而非覆盖旧记录。
4. **硬编码事实抽核未发现不实**：`435 passed in 12.45s`、指针首次 `22 rewritten; 0 kept`、后续 `11 rewritten; 0 kept`、最终 `0 rewritten; 0 kept`、静态 0 违例均与现有 UTF-16 日志一致。各组变异 JSON 均能提供表格所需名称与失败字段，没有 `None` 占位。硬编码叙述适合本次冻结回执，不是自动适配未来新工单的通用生成器。
5. **相对链接解析正确**：从实际未来报告位置 `reports/codex/` 解析 30 个模板本地链接，从 inventory 文档解析 5 个本地链接；全部位于本树。当前缺失的仅为预期尚未生成的 `policy_delta_final.json`、最终 summary、artifact verification 和报告本身，没有发现 `../` 层级错指。链接门只核目标存在，不核 Markdown fragment 是否存在；这不应称完整链接内容验证。
6. **冻结哈希现状无漂移**：本次另外按 runner 的完整规则重建路径集合，用旧/新 keys 并集比较，250 个冻结路径当前完全一致，包括 src/tests/tools、政策、README/docs、runner/plugin；未发现真实新增/删除/修改。

## 发现与建议

### DEL-01：最终 verifier 的漂移检查漏掉新增路径

初审 `verify_artifacts.py` 的 `drift = [p for p,h in before.items() ...]` 只遍历旧快照键。因此会抓住已冻结路径的修改与删除，但最终全套完成后新增一个 `src/tests/tools/*.py` 不会进入此列表；PASS 字段 `source_test_policy_doc_drift=[]` 可能掩盖这类新增。

建议：按 runner 同样规则重建当前快照，然后比较 `before.keys() | after.keys()`。本次独立并集比较结果是空漂移，因此这是验证器完备性缺陷，不是声称当前真的发生了源码漂移。

### DEL-02：PASS 文件早于最终 Git 检查落盘

初审 verifier 在核 branch/head 及 `git diff --check` **之前**写 `artifact_verification.json` 的 `status=PASS`。若这些后续检查失败，程序虽然非零退出，却可能留下本轮看似成功的核验文件。

建议：先做 branch/head、diff 与 manifest 路径检查，全部成功后再写 PASS 回执；manifest 应仍收录最终 artifact 回执的哈希。不能仅把写回执移到 manifest 哈希生成之后而让 manifest 继续引用旧回执。

## 主代理修订后的闭合复核

- **DEL-01 已关闭**：verifier 通过 importlib 装载冻结 runner，仅调用其只读 `snapshot()`；`main()` 不会被 import 触发。当前快照与冻结快照通过 keys 并集逐项比较，新增、修改和删除均会入 drift。无需复制并可能漏更新另一套路径规则。
- **DEL-02 已关闭**：branch/head、`git diff --check`、所有 manifest 路径约束和哈希读取已移至 PASS 发布前；未来回执先编码为 `receipt_bytes`，manifest 针对这批确切字节计算哈希，最后才调用 `write_bytes(receipt_bytes)` 发布 PASS。没有残留“manifest 引用旧回执”的顺序错误。
- 本轮复核仅源码阅读和 AST 解析，不运行 finalizer/verifier，也没有修改冻结路径。最终生产 PASS 仍须由主代理等待全套结束、按顺序执行生成器与核验器后取得。

## 审查边界

- 本审查没有验证最终尚未完成的全套 PASS，也不替主代理执行 finalizer/verifier。
- 最终 verifier 基于冻结 summary 的 checks，而非再次重新跑 pytest；这是正常回执核验，不应宣传为第二次独立全套。
- nodeid 存在门会剥掉参数化后缀，只能证明基础测试函数被收集，不能独立证明特定参数或 oracle 数学独立性。模板已经明确机器门不伪造独立性，此项是边界而非新增缺口。
- `deliverables.json` 列全部 Git 可见、非 ignored 的改动/未跟踪文件，并排除自身哈希；不是对任意忽略文件的全面归档保证。
