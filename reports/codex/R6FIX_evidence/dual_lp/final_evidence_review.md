# R6FIX 交付证据复审（第二轮全套运行中）

日期：2026-10-12。范围：只读复核全仓修复证据、测试改写与交付脚本；经主执行者授权，仅修改两个 evidence 交付脚本及本说明。没有再改 `src/tests/docs/tools`，没有重跑完整测试或完整交付审计。

**边界：本代理是 G6F-07/11/12 及 frozen 同类修复的作者。本次是证据链复审，不是独立 G6 审查，也不替代用户要求的下一轮独立只读复核。**

## 1. 当前已证实及尚未证实

- 第一轮完整运行确实失败，原记录已另存：`6 failed, 8849 passed in 1312.89s (0:21:52)`，runner 墙钟 `1324.8708759 s`。不能把该记录标绿，也不能只报告后续快速专项门而隐藏全套失败。
- 首轮证据：[日志](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/full_suite_first.log)、[元数据](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/full_suite_first.json)、[启动文件哈希](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/verified_tree_first_start.json)。
- 第一轮六个失败的 BB52、盖构造、互锁 oracle 后续修复及原格复跑都有对应证据。现已读到最新专项元数据：`283 passed in 1.17s`，exit 0，runner 墙钟 `1.9282253999990644 s`；[记录](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/final_targeted_verified.json)。
- 一次错误文件名 `test_canon_map.py` 导致 exit 4/no tests ran，记录保留为 `final_targeted_second.*`；它不是修前红或变异红，不能算“门有牙”。随后改为实际存在的 `test_doc_pointers.py` 才得到上述 283 项绿。
- 本说明写入时第二轮完整运行尚未结束，**未声称最终全绿或交付完成**。完整通过后须将实际终行、runner 时间及大于 900 s 的原因写入主报告；并行进程重叠不能冒充隔离性能测量。

## 2. 12 条主项的红与变异证据核验

各修前日志都有对应测试的 `FAILED tests/...::test_*` 节点；变异穿过实际实现，未使用结果之后追加假值。以下为变异实际运行错误，而非仅在源代码摘录中搜到文字。

| 主项 | 变异对应的真实看护失败 |
|---|---|
| 01 | `source-membership-isolated`；同类拓扑返回隔离另有 `topology-result-isolated` |
| 02 | `convex-point-ignores-face-hints` |
| 03 | `exact-midpoint-concavity` |
| 04 | 二维及三维各自 `strict sample was skipped`，不是任一分类门碰巧红 |
| 05 | 微贯入 `first strict exit`，另有极端平方 `closed segment projection` |
| 06 | `representable signed gap`，实际 `-0.0` 对非零负 gap |
| 07 | 除法实际 `(inf, -inf, 0.0)` 对 `(1.0, -1.0, 0.0)`；atan2 实际 `-0.0` 对 `-5e-201` |
| 08 | `exact relative distance`，实际 `0.0` 对 `1e-9` |
| 09 | `exact-mixed-affine-translation`；nominal 同类 `exact-large-offset-escape blocked by nominal construction` |
| 10 | `stale pre-rounded margin difference claim`，文档陈述真实退回旧句 |
| 11 | 常数零次幂合法调用错误抛 `ZeroDivisionError`，正是删除 p==0 分支的缺陷，不是 collection 或环境错误 |
| 12 | `optimal result must carry exact_x`，真实返回 `None` |

追加扫描变异还包括乘积导数 `nan`、逆幂中间溢出、冻结 gap 的 `nan`、冻结法向导数中间溢出、精确范数、既有 near-parallel 门，以及 VV3 的 `round final norm, not its components`（`0 != 5e-324`）。

现机器检查覆盖 **24 条变异链**：8 条 g0/construction 独立 pytest 失败 + 8 条 dual/frozen 独立 pytest 失败 + 8 条 geom3 内部捕获失败。geom3 wrapper exit 0 是其正常验证模式，必须同时具有逐项实际 `AssertionError: <guard>`、结构化 `KILLED_BY_GUARDING_ASSERTION` 与终行 `8 internal mutants killed by the intended assertion`，不能仅把 wrapper 的 exit 0 当“变异报红”。

## 3. 已修交付脚本的三个缺口

### 3.1 全路径集合与输入边界

[audit_delivery.py](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/audit_delivery.py) 现在比较 `src/tests/docs/tools` 全部文件及 README/pyproject/AGENTS 的**新增、删除、修改**，不再只检查启动清单中已有的路径。只读核验时当前 168 个路径与第二轮启动冻结清单一致。

同时核对 fixtures 路径集合及起始哈希；已实际核验 **62 个 fixtures 全部一致**，未缺失。inputs 当前共 53 个文件，但起始 baseline 只记录了旧 `g6e_findings_raw.json`。新增 G6F 的 52 个文件没有起始哈希：脚本会明确记录此历史证据缺口，只给出当前观察哈希；**不能声称其当前哈希证明任务开始以来未改**。

全套审计也要求实际 exit 0、JSON 终行与 log 完全一致、全通过计数不小于原 8582，以及无选择性 pytest 参数。新旧测试一并扫描新增 skip/xfail 语法；原测试函数与参数化装饰器不能消失/改变。

### 3.2 变异 metadata 与实际失败匹配

[index_delivery.py](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/index_delivery.py) 对独立 pytest 变异要求 exit 1、JSON/log 终行一致、指定 `FAILED` 节点与运行时 `E ...` 中的目标错误同时存在；拒绝 unrelated FAILED、源码摘录里有 guard 但实际不报该错误、collection error。

内部 caught 变异单独核验 wrapper exit、8 项 JSON 唯一性、各自 traceback/断言与成功捕获标志。只有最终审计通过且其 full-log/full-JSON/freeze 哈希仍匹配时，才写 12 项 `FIXED_REGRESSION_GREEN_MUTATION_KILLED` 状态。现有 24 条记录已通过只读验证。

### 3.3 新增文件完整交付

旧 `git diff --binary` 不含 untracked 新源码和新测试，不能单独作为本单完整交付。现脚本将生成 `working_tree_delivery.zip`：纳入修改与新增的源码、测试、文档、主报告及 evidence 中的小型 Python 重放脚本和 Markdown 分项报告，排除用户 inputs、临时产物、证据数据、生成的 INDEX 及 ZIP 自身。

ZIP 内 `DELIVERY_MANIFEST.json` 给出每个文件 hash/大小及删除路径；生成后重开 ZIP 核对完整条目集和逐文件 hash。`working_changes.patch` 仍保留，但 INDEX 明确其仅为 tracked diff 辅助文件。完整证据数据另由外部 INDEX/manifest 链接和哈希覆盖，不混入代码包形成递归归档。

## 4. 测试改写复审与机器审计限制

只读 AST 对照起始 ZIP 后：原测试函数删除 0，原测试装饰器变化 0，已有测试新增 skip/xfail 调用 0。但 AST 清单**不能证明任意断言或间接生成网格都未放松**，必须结合人工台账与真实变异。

重点读了后续 BB52、互锁与 G2 oracle diff：

- BB52 保留原三个参数格、原出口与旧投票守护；给原旧浮点像重新完整跑 1260 格，无变异 `603/603`、真实缺 VE 变异 `584/603` 与 19 条严格正距离缺盖归因均保留。新精确仿射像 `603/603` 单独断言，不以换数据后改期望来掩盖旧门。
- 互锁原 18 格及其集合/候选/tied labels 断言未删，只对独立 oracle 的输入平移先 Fraction 化；另加该输入契约的真实旧 float 加法变异。
- G2 原网格和字典字段相等未改；将共享旧浮点舍入错误的 oracle gap 改成独立 Fraction/Decimal 最后开方，并新增极端尺度及工程坐标最小红门。

现主报告已有上述改写台账；它与 AST 检查互补，不应把“无删除/装饰器未变”写成形式化无放松证明。

## 5. 本次脚本验证与后续运行顺序

没有运行完整 delivery audit 或打包，因为第二轮全套尚在进行。本次只运行两个脚本的 `--self-test` 等价入口、无 pyc 的 `compile()`、现有变异证据校验。结果 exit 0：

```text
audit_delivery self-test: 8 checks passed; no full audit executed
index_delivery self-test: 12 checks passed; no final indexing or packaging executed
24 existing mutation chains validated
```

证据：[验证日志](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/dual_lp/delivery_script_checks.log)、[验证 metadata](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/dual_lp/delivery_script_checks.json)。

主执行者收到第二轮全套实际成功后，应先定稿主报告，再按以下顺序运行（工作代码继续冻结）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/R6FIX_evidence/audit_delivery.py
python -X utf8 reports/codex/R6FIX_evidence/index_delivery.py
```

若审计不通过，不能强制写 DONE；若之后修改了待交付文件，应重新生成对应 hash 清单与 ZIP。脚本不会替主执行者杜撰全套结果。
