# WO-M5c A6–A7 源码闭包与共享审查绑定工作记录

## 合同与边界

- 目标：共享审查追加不得扩大既定规则/路径域；端点与稳健回放绑定实际运行时完整仓内 Python 导入闭包，开始/结束各核查一次。
- 范围：本工作树 `tools/exact_construction_subset.py`、`tools/m5c_source_binding.py`、两条回放与最小例的绑定区域、对应 pytest 门。
- 非目标：不修改 JSON 准入政策、不改历史审查记录、不借哈希改写替代真实回放；不把源码完整性门作为几何正确性证据。
- 回滚锚：收到工单时 `efb0dfe` 的文件内容；未执行任何修改型 git 操作。

## A6 处置

1. 生产 `mutation_review_domain_is_bounded()` 固定 13 条脚手架规则；任何新增数值规则令整个活动审查失效，而不只是忽略新增条目。
2. 路径限制为已审查的 4 个真实变异模块：`tests/mutation_support.py`、`tests/test_int1_semantics.py`、`tests/test_m3b_construction3d.py`、`tests/test_m5a2_exact.py`。不按 `tests/` 字符串前缀放行；普通数值测试、生产路径、`tests/../src/...` 均拒绝。
3. 当前生效审查指纹单独固定为 `cb2f1e7fe51137a61fcf9126f756af55fce22875beac487cedc27ec5e7b78cdc`。历史前缀不变仍不够；追加更宽审查会触发这条当前指纹断言。
4. 数值规则、生产路径、未审查测试路径、父目录穿越共 4 个真实生产 guard 内部变异：改坏前拒绝，删去相应内部边界后都红在 `M5c an appended broader review must not discharge any diagnostic`，没有借助当前审查指纹门。变异在内存生产函数内部；源码文件字节没有改变，源码哈希绊线不可能成为报红原因。
5. `tools/exact_construction_policy.json` 零修改、0 条新增审查/续审/准入；当前已审查调用方和作用域的原有字节/函数指纹仍全部生效。

## A7 处置

- 新 helper `runtime_source_hashes()` 从实际 `sys.modules` 读取仓内 `src/eab/**/*.py` 与 `tools/*.py` 的已加载模块，另明确计入入口与绑定 helper；不再只列直接依赖，也不把无关的整个生产包当作导入闭包。
- 端点回放开始前预载其 midpoint 的原 lazy imports，再采集闭包。当前干净解释器端点闭包 29 文件（原 28 文件 + 绑定 helper），稳健闭包 21 文件。
- 开始写 `source_hashes`，结束重新采集 `source_hashes_end`，要求路径集合与每项字节哈希完全相同；迟加载模块、被删文件或中途源码变化均作废，不可续接。稳健 worker 也记录并核对自己的首尾闭包。
- 端点 manifest 独立存 `input_hashes.manifest`，不再混入源码哈希字段；原冻结 shard 重读检查保留。
- pytest 在干净子进程中独立采集对应入口闭包，与摘要比较全部条目及结束条目；避免 pytest 已导入大量其他模块导致闭包污染。
- 每个端点/稳健传递依赖均复制至 pytest scratch，逐文件真实追加变异字节，验证 production `assert_current_sources()` 拒绝。共 29 + 21 个文件探针；只改 scratch，没有改真实运行源码。
- 额外门拒绝开始后出现新 runtime import，以及即使内容哈希匹配的非规范路径穿越。
- 最小例 `verify()` 按冻结闭包逐文件核验，而不把 pytest 的额外模块误认为回放依赖；`freeze()` 同样首尾绑定。最小例仍须实际重新计算。

## 独立 oracle / import 清单

新政策/绑定门的独立期望只用 `copy`、`hashlib`、`json`、`pathlib`、`subprocess`、`sys` 以及字面审查域；`pytest` 为驱动，`mutation_support` 仅构造内部变异；被测代码为 `check_exact_construction._subset` 与 `m5c_source_binding`。未使用几何原语；本组只声称政策与来源绑定完整性，不声称数值正确性。新增 helper 不含几何数值构造，不增加数值合同或数值准入。

## 已执行验证

命令（均在本工作树，TEMP/TMP 指向 `reports/codex/M5c_evidence/tmp/`）：

```powershell
python -m pytest -q -p no:cacheprovider --basetemp reports/codex/M5c_evidence/tmp/binding_unit_r2 tests/test_m5b_policy_history.py tests/test_m5c_policy_binding.py tests/test_m5b_int1_followup.py -k 'not frozen_summaries'
```

最后一行原样：`34 passed, 2 deselected in 1.43s`。

这里明确剔除的是 **待真实重算发布后才运行的 2 个摘要绑定门**，不是完整套件的 0 skip / 收集=执行证明。完整套件与重算由主代理最终记录，不可把本条作为整单通过结论。

对本工作新增/改动的 3 个测试文件逐文件调用生产 `scan_text()`：均 **0 违例**（`test_m5c_policy_binding.py`、`test_m5b_policy_history.py`、`test_m5b_endpoint.py`）；尚不替代主代理整树静态门。

## 早期待办记录（最终核验见末节）

1. 实际重算端点 15220 块帧与稳健 1810 步，发布新摘要及最小例，禁止只改哈希。
2. 运行 2 条冻结摘要闭包门，再完整四分片验证收集=执行、0 skip。
3. 把本记录的局部结果纳入最终 `M5c_report.md`，闭包数如最终新增生产 imports 应以真实回放为准。

## 真实重算发布后的最终核验

完整 R2 已实际完成并发布（1810 步、15220 块帧、64010 对），15 个 worker 的 21 项源码首尾映射与父进程完全一致；旧 r1 作废且未拼接。冻结 publisher 实际执行成功并发布 `combined_summary.json`：逐对重核旧/新 64010 个 P1/P2 精确状态、特征、时间，68 个研究候选齐全，单首盖由 2 增至 19（净增 17）。所有绑定/联合及对应会计门含真实冻结产物全绿：`130 passed in 5.48s`，0 skip、0 deselect。

端点 29 项、稳健 21 项完整闭包门及最小例重算门均已执行，不再保留早期待发布剔除项。初态贯入 16676 对每阶段参考计数为主参考 81209、正式 VV 二参 2001、共边候选槽 19785；仍为 0 个出口排序证书，计数不代表出口命中结论。完整四分片收集=执行与静态总门由主代理最后发布。

可核验记录：`combined_publication_verification.json`、`combined_publisher_freeze.json`、`binding_combined_actual_r1.log`。
