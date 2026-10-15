# M5b：INT1 遗留项及准入逐站审计

状态：本分工的 INT1 小项已完成；这不替代全时程对账、四片执行或 G6。

## 1．余数零语义与内部变异

`tests/test_m5b_int1_followup.py` 以 `(x-p)(x²+p)`、`p∈{2,3,5,7}` 构造独立期望：模 p 后是 `x³`，唯一根为余数 0；唯一实根 p 位于非退化有理括区间中，不能被“无根”筛删除。oracle 仅用 `fractions.Fraction`、整数展开与枚举，未调用生产多项式原语来生成期望。

将真实 `RealAlgebraic.as_rational` 函数体中的 `range(prime)` 改为 `range(1, prime)`，再执行同一断言，红在 `M5b residue-zero modular root must survive the no-root filter`。这条路径不读取任何源码/冻结文件哈希，未在输出后追加假根。生产 `as_rational` 无需修复。

## 2．共享域收紧与调用方绑定

- 原 `mutation_instrumentation_review` 对象原值保留；新增只追加数组 `mutation_instrumentation_reviews`，首条后继明确绑定原记录 SHA256。
- `semantic_guard` 断言分派和 `mask_source_hashes` 非变异脚手架移入原有 `test_internal_int1_mutants_fail_the_designated_semantic_assertion` 驱动；没有新增共享范围，也没有把数值 oracle 移入该域。
- 活动共享域由 9 个 scope 减为 7 个。每个 scope 除函数源 pin 外增加调用方模块非定义语句的 `module_context`，最终另钉**完整调用方模块源码**的 `module_source_sha256`，绑定 import 来源、模块级别名重绑定及直接 def/class 遮蔽。保留 helper 整文件字节 pin。
- 负门分别替换 `from mutation_support ...` 的导入来源、增加同名 helper 的模块级重绑定；被测函数源 pin 保持不变，新绑定必须失效。内部变异仅移除模块 pin 比较，红在 `M5b caller helper import resolution must invalidate the shared review`，不是碰巧的 helper 哈希不符。
- 活动策略 `proof_domain` 明写：通过反射取得 `float`（例如 getattr/globals/间接 callable）**不在豁免保证内**。13 条规则是有限静态脚手架规则，不构成任意 Python、反射数值流或数值 exactness 证明。

独立审查真实找到并修复 **1 major**：仅钉非定义语句时，在模块末尾添加同名 `def mutated_function` / `class mutated_function` 可以覆盖导入，原两个 pin 却不变。没有用反射域外声明搪塞这个直接遮蔽缺陷；保留首条 M5b 审查记录不改，追加 `M5b-INSTRUMENTATION-2` 绑定完整调用方源码。新增 def/class 两格及“只移除整模块 pin”的内部变异，红在 `M5b direct def/class shadowing cannot inherit imported helper authorization`。当前逐站审计的 enabled 分支直接调用真实 checker，避免审计模拟遗漏新绑定规则。

## 3．不可变 / 只追加门

`tests/test_m5b_policy_history.py` 对以下已接受状态冻结规范 JSON 值摘要；允许尾部追加，但拒绝改写、删除、前插：

| 范围 | 固定长度 |
|---|---:|
| M3b 新增行 | 39 |
| INT1-C 行 | 23 |
| df4f6f1 全部旧 waiver 前缀 | 3452 |
| 旧续审记录前缀 | 92 |
| M5b 首条后继共享审查记录 | 1 |
| 独立审查修复后的共享记录前缀 | 2 |

原 INT1 共享审查对象单独不可变，首条后继的 `supersedes_sha256` 必须指向它。历史数据缺陷与数值内部变异分别报告：前者本来就是历史指纹合同，不冒充数值语义变异。

## 4．逐规则 × AST 站点口径

审计脚本：[m5b_audit_admissions.py](file:///D:/eab-wt/cx-e2/tools/m5b_audit_admissions.py)。机器清单：[admission_rule_sites.json](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/admission_rule_sites.json)。同一行同样文本出现两次，按 AST 列位置计两个站点；有专门 pytest 防止把它们折为一行准入。每个活动 pin 都定位其作用域内 AST；仅四条已存在的历史空 pin 另列，不计入站点。

| 口径 | df4f6f1 | 当前 | 差值 |
|---|---:|---:|---:|
| 归档 waiver 行 | 3452 | 3522 | +70 |
| 源上下文仍匹配的行 | 3360 | 3416 | +56 |
| 真有本 scope AST 站点的行 | 3356 | 3412 | +56 |
| 逐站准入的规则 × AST occurrence | 3558 | 3618 | +60 |
| 共享域实际免除的规则 × AST occurrence | 104 | 77 | −27 |
| 上两项合计 | 3662 | 3695 | **+33** |

**不得把一条共享审查说成一个准入站点。** 此前按诊断 `(line,source)` 去重得到的 101/74 也会漏掉同行重复 AST；最终口径是 104/77。共享减少 27 是断言分派及 hash masking 迁入既有 test-driver 排除域，**不代表全仓总豁免真的减少 27**，更不声称全库历史插桩迁移已完成。

新增 70 行中，14 行只是 `algebraic.py` 六次扩展对原 14 个 pin 的逐站续审；旧行逐值保留、追加 14 条续审，新旧对应 AST 相同，不增加活动站点。其余 56 行对应 60 个新规则站点：`dda_motion.py` 32，`model_robustness.py` 3，独立 oracle 25。每条节点、规则、作用域、解释与具名门见 [new_admission_review.json](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/new_admission_review.json)。未扩大全局 imports/members，也未把独立数值 oracle 改名为 test driver 来凑净零。

四条历史空 pin 为 `R12b-L0534/L0536/L0539/L0691`：函数上下文仍匹配，但对应 AST 只在其他函数出现，旧 stale 检查按全文件找节点，故不报错；这些行不会授权当前本 scope 站点。保留历史不改，本单审计明确扣除。不得把它们当作新增风险、有效许可或数值失配。

## 5．验证及变异表

| 项目 | 结果 |
|---|---|
| 新 INT1/历史门 | 20 个，含四个余数零参数格及 def/class 遮蔽格 |
| 新旧相关专项 | 125 项全绿，精确末行见 int1_tests.json，0 skip |
| 余数零内部缺陷 | 指定数值语义断言 KILLED |
| 忽略调用方 import 绑定内部缺陷 | 指定授权判定断言 KILLED |
| 忽略完整调用方源码 pin 内部缺陷 | def/class 遮蔽语义断言 KILLED |
| 历史删除 / 改写 / 前插 | 6 组逐项拒绝，尾部追加保留绿 |
| 全库静态 r3 | `exact construction AST gate: 0 violation(s)` |

专项执行记录：[int1_tests.json](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/int1_tests.json)；静态执行记录：[static_admissions_r3.json](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/static_admissions_r3.json)。r1 的 27 条全为新端点/回放测试驱动脚手架；经移入真实 test 驱动或把 map 改为直接生成器后，未增加相应准入。r2 曾为全绿，但独立审查随后找到上述 major；修复后完整重跑 r3，不拼接旧扫描结果。

命令均使用 `TEMP/TMP=reports/codex/M5b_evidence/tmp`、`-p no:cacheprovider` 和显式 `--basetemp`；无 Git 写操作、无姊妹仓库写入。`exact_construction_subset.py` 曾误转换换行，后经只读 `git show HEAD` 确认原为 LF，已仅恢复原 LF，规范化文本/AST 未变。新文件均 UTF-8 无 BOM。

完整四片与全局耗时增量由主报告给出。本分工不以专项绿代替它们，也不宣称 G6 已完成。

INT1_M5b_FOLLOWUP_DONE
