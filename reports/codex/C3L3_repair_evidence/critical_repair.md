# WO-C3L3 验收返修：临界参数具名门与七项内部变异

## 范围

返修入口 HEAD：`c8718bb0850328defd8f0cc16fb4f3a09e922975`。已只读核对 Claude 验收材料中的 MAJOR-1 及 `critical/scripts/mutate.py`、`m_compare.py`、`m1_probe.py`。

本分工仅修改：

- [test_critical.cpp](file:///D:/eab-wt/cx-c0/eab2/tests/test_critical.cpp)
- [eab2_c3l3_critical_mutations.py](file:///D:/eab-wt/cx-c0/tools/eab2_c3l3_critical_mutations.py)

没有修改生产算法，没有 commit 或其他 Git 写操作，没有正式 CMake/DLL 构建，没有 Python 全档运行。验证为隔离目录内从源码重编的 C++ 单测、变异可执行文件，以及随后获准添加的两份隔离变异 DLL 定向红门；不是独立对抗复审。入口全档证据由主代理另行汇总，本分工没有重跑或重新认领该结果。

## 两个新具名 Koureas 回归

均位于 `threshold_contracts()`。真值由手工代入 `t-(h/2)(1+t*t)` 给出，不从被测二分候选或被测 LP 读取。

| 具名回归 | t | h | μ_max | steps | 报告括号 | 独立真值 | 门要求 |
|---|---|---|---|---|---|---|---|
| `koureas_wide_four_steps` | 3/32 | 1/16 | 3/4 | 4 | [3/64, 3/32] | 2039/32768 | 真值严格位于括号内；exact_threshold/attained 为 null，且无 threshold_certificate/proof/proof_reason |
| `koureas_wide_one_step` | 3/8 | 1/4 | 3/8 | 1 | [3/16, 3/8] | 119/512 | 同上 |

两例都核验端点原始 LP 证书。上端已经无界，不代表它是首个无界阈值；删掉下侧延拓条件时，新门必须拒绝错误的精确闭阈声明。

既有 unreversed 开阈低预算例保留，其语义断言显式命名为 `unreversed_open_requires_above`，用于定位缺少上侧射线延拓的内部缺陷。

## 七项源内部变异

原五项保持：分子 Sturm、分母 Sturm、末步分辨率原因、binary64 域上界、私有整数作用域。新增两项直接替换 `critical.cpp` 内部判定，而非在输出后追加假字段：

1. `closed_no_lower_continuation`：删掉 `(candidate == 0 || below.has_value())`。
2. `open_no_upper_ray`：删掉开阈条件中的 `above`。

隔离工具先执行无变异基线；每项变异独立编译，且必须以退出码 1 和**指定语义断言**同时匹配才算捕获。编译失败、其他断言失败或仅哈希差异都不算通过。

实际新增变异原始末行：

```text
C3L3_CRITICAL_FAIL checks=143 reason=koureas_wide_four_steps_requires_below: unbounded endpoint is not a closed threshold
C3L3_CRITICAL_FAIL checks=131 reason=unreversed_open_requires_above: endpoint states cannot certify an open threshold
```

七项 C++ 变异可执行文件的唯一完整隔离运行命令：

```powershell
python -X utf8 tools/eab2_c3l3_critical_mutations.py --root D:/eab-wt/cx-c0 --output D:/eab-wt/cx-c0/eab2/build/tmp/c3l3_repair_critical_mutations_20261023_r1
```

实际基线及整体末行：

```text
C3L3_CRITICAL_OK checks=346
C3L3_CRITICAL_MUTATIONS_OK caught=7 escaped=0
```

退出码 0。所有临时源码、编译产物及 TEMP/TMP 均位于 ignored 构建区；没有结束任何非本任务启动的进程。

## 附加定向 DLL 红门

根据主代理后续指令，将本次隔离运行新生成的 core/statics 对象与只读正式 `c_api.cpp` 的新编对象链接，分别加入上述两个内部变异的 `critical.obj`；不使用正式 build 的任何 obj/lib 或 generated 头。构建标识从源码模板及本次编译器版本生成并追加 `repair-mutant`。两份 DLL 各有 29 个生产导出、无 test-only 导出。原始 C API 源码 SHA 前后相同。

待差分代理冻结修订的 `compare()` 后，直接调用两个 DLL，保存未经修改的原生 ABI JSON，再送入修订后的比较器。其非唯一证明差异规则必须先通过原几何、LP、多项式和单侧延拓核验，才能规范化字段。

| 内部变异 / 定向输入 | DLL 实际假声明 | 比较器必须抛出的原始语义异常 | 结果 |
|---|---|---|---|
| `closed_no_lower_continuation`；Koureas t=3/32、h=1/16、μ_max=3/4、steps=4 | `exact_threshold=3/32, attained=true` | `closed threshold needs bounded continuation` | ValueError，拒绝 |
| `open_no_upper_ray`；unreversed t=3/16、h=1、μ_max=1、steps=1 | `exact_threshold=0/1, attained=false` | `open threshold needs feasible point and improving continuation` | ValueError，拒绝 |

两次比较的 `dispositions` 均为空，证明假证书没有被非唯一基证明增益规则接纳。实际完整定向运行末行：

```text
C3L3_CONTINUATION_DLL_RED_GATES_OK rejected=2 admitted=0
```

第一次定向脚本使用了错误的异常类捕获（AssertionError，而检查器抛 ValueError）；仅修正 ignored 执行脚本的异常处理后完整重跑两例。生产算法、比较器与两份假证输出均未因该脚本修正而改动。

详见 [DLL 定向红门摘要](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_repair_evidence/continuation_dll_red_gates.json)。两份原生假证的 SHA-256：

- 闭阈：`a7f6c6a9e754f7f974cbe63ac36d2f3cdc80bfe20fa2f134fa6ce616ce8decbf`
- 开阈：`51788cf91d453eddd75fd0a413fea9777df9aa560bcafbfe25e9946f9fb5fd55`

原始 JSON、两份 DLL 与构建/执行脚本均在 ignored 目录。供主代理按 H1 归档的 [逐文件清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_repair_evidence/continuation_dll_archive_queue.json) 已记录字节数和 SHA；本分工未擅自写入外部归档目录，归档完成状态由主代理另行记录。

## 生产源码不变与证据

[critical_repair.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_repair_evidence/critical_repair.json) 保存验收输入 SHA、两例参数及括号、修改文件 SHA、实际命令和末行，并对 `eab2/src` 的九个生产 `.cpp` 逐文件比较当前 SHA 与 HEAD 字节，全部相等。`git diff --exit-code -- eab2/src` 为 0；两个修改文件的 `git diff --check` 通过，UTF-8 无 BOM、LF 合同已核。

[critical_mutations.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_repair_evidence/critical_mutations.json) 是本次变异运行的权威摘要，含原/变体 SHA、逐项替换、编译与执行命令、目标断言、基线以及 `sources_unchanged=true`。ignored 目录中的同名运行原件不是另一份入库权威结果。

边界：本素材只关闭本分工的 C++ 具名门和七项变异要求；不代替主代理负责的宽括号/Farkas 差分、非唯一证明比较规则订正、正式收尾门或 Claude 再验收。

## 比较器最终冻结后的两例重核

比较器增加阈值元数据互斥检查后，沿用原两份 DLL（不重编译）完整重跑两例；最终比较器 SHA-256 为 `f9e66ec40e78107836f66b1e5368f465624975e08d1d42348559bb2d915f6649`。两例原生假证 JSON 与 DLL SHA 均与前次相同，仍由原指定数学断言拒绝，`dispositions=[]`。

```text
C3L3_CONTINUATION_DLL_RED_GATES_OK rejected=2 admitted=0
```

前一比较器 SHA `afbe425b17061c8fc59d4149492c64f9de59a7c7bd744f9cc0f9561be43ed40c` 的摘要、原 JSON、旧归档队列及已有构建日志在 [previous_checker](file:///D:/eab-wt/cx-c0/eab2/build/tmp/c3l3_repair_critical_dll_r1/previous_checker/) 原字节保存，并加入本轮归档队列；未覆盖旧 SHA。此前拒绝运行的 stdout 仅为工具输出，没有独立磁盘日志；本次另存 [rejection_final.log](file:///D:/eab-wt/cx-c0/eab2/build/tmp/c3l3_repair_critical_dll_r1/rejection_final.log)。这仍是执行者红门复现，不是 Claude 复验。
