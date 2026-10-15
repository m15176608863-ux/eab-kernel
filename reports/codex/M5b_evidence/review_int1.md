# M5b INT1 遗留独立审查（端点代理）

## 结论

修复后限定范围内 **0 critical、0 major、0 minor**。发现并修复 1 项 major 的记录保留如下；有限静态域不等于任意 Python 安全性证明。本审查不是完整六路 G6。

范围：`tools/exact_construction_subset.py` 共享域绑定、`tools/exact_construction_policy.json` 历史/后继记录、`tools/m5b_audit_admissions.py` 逐站统计、`tests/test_m5b_int1_followup.py` 与 `test_m5b_policy_history.py`；并重跑旧 INT1 语义与 M5a2 静态回归。

## 发现的 major：模块定义遮蔽原先可绕过新导入绑定

初版新绑定只加入 `site_contexts(text)["<module>"]`，此值按既有定义排除所有顶层 FunctionDef/ClassDef。审查者现场构造：

```python
# 追加到原 tests/test_int1_semantics.py 源码文本末尾（不改磁盘源文件）
def mutated_function(*args, **kwargs):
    return 1
```

Python 将此定义绑定到原导入 helper 名；原 `inject_semantic_mutation` 函数 pin 与非定义模块 pin 均不变，初版 `instrumentation_scope` 仍返回 True。另一 `class mutated_function: pass` 有同样问题。这是普通名字解析，不是已排除的运行时反射。

责任代理现已**追加** `M5b-INSTRUMENTATION-2`（未重写原记录），每个共享 scope 进一步绑定规范化换行后的整个调用方文件 `module_source_sha256`。它覆盖定义、装饰器和默认表达式；任何未审调用方源码变化都会失效。原导入+赋值测试保留，新增 def/class 两格与仅移除整模块 pin 的内部变异。

审查者对原两条遮蔽输入再次现场执行：**两者均 False**；同名换导入来源、直接赋值、函数/class 遮蔽现在都被拒绝。当前整模块绑定比较保守，会让不相关调用方改动也要求续审；这比漏放同名 helper 更安全，不把它叫完整 Python 名称解析器。

## 模素数“余数 0”门

独立多项式 `(x-p)(x²+p)=x³-px²+px-p²`，模 p 仅在余数 0 有根，而隔离实根 p 本身非零，可排除特殊零根捷径。p=2/3/5/7 四格由纯整数/Fraction 展开计算 oracle，不借用生产多项式原语。

`as_rational` 内部 `range(prime)` 改 `range(1,prime)`，在实际模块过滤路径返回错误 None；红必须命中 `M5b residue-zero modular root must survive the no-root filter`，不是文件/源码 hash 绊线。原函数先通过同一语义门。

## 历史合同与不可变性

审查者使用本树只读 `git show df4f6f1:tools/exact_construction_policy.json` 独立核对：

| 组 | 接受态数量 | 当前前缀 |
|---|---:|---|
| M3b 新增行 | 39 | 字段值不变，独立 SHA256 与测试常量一致 |
| INT1-C 行 | 23 | 字段值不变，独立 SHA256 与测试常量一致 |
| 全部历史 waiver | 3452 | 与 df4f6f1 原前缀完全相同 |
| 历史 renewal | 92 | 与 df4f6f1 原前缀完全相同 |
| 原 INT1 共享对象 | 1 | 原值相同，后继以 supersedes 指纹关联 |

测试对删除、重写首行、前插记录分别验证会红；追加新行允许。这里 hash 本身就是历史数据合同，并未把它拿去冒充数值变异的语义牙齿。两条本单共享后继现均纳入只追加前缀门：原前 1 条门保留，另加前 2 条 literal SHA256 `a8e5b80d4d395de140382609a78c5a83f243c968709c13bd335538838974c466`。

## 共享域与逐站统计

- `semantic_guard`、`mask_source_hashes` 已不在 active scopes，迁到真正测试驱动中；未为这些断言/掩码脚手架扩大共享域。
- 保留 13 条规则，不等于只有 13 个站点、更不等于“一个共享批准计一站”。当前逐 AST occurrence、规则、路径、函数、行/列口径为：**原 104 站 / 9 scopes → 当前 77 站 / 7 scopes，净减 27 站**。相同一行的两个相同 AST 表达式分别计数的门已覆盖。
- 全体准入逐站合并净增的当前快照为 **+33**，不是 0；新增来源与解释须由主报告及 `admission_rule_sites.json` 逐条披露。没有用共享域净减来隐藏总体净增。
- 审计工具 current 分支已改成调用真实 `instrumentation_scope`，不再用一个漏验 helper hash/新整模块 pin 的近似替身；historical 分支才显式重建旧反事实策略。
- `proof_domain` 明写经 getattr/globals/间接调用得到 reflected float 的情形 **NOT covered**。数字来源、算术、代数比较器的其他看护没有被这 13 条脚手架规则抹掉；但这仍非任意反射/运行时命名空间变异的保证。

## 独立执行与残余限制

```text
python -m pytest tests/test_m5b_int1_followup.py tests/test_m5b_policy_history.py tests/test_int1_semantics.py tests/test_m5a2_static_runner.py -q -p no:cacheprovider --basetemp reports/codex/M5b_evidence/tmp/pytest_int1_review_endpoint_r1
125 passed in 4.00s
```

TEMP/TMP 均在本树 M5b ignored tmp；0 skip。该次执行包括过滤余数变异、两种绑定内部变异、历史合同反例与旧 INT1 语义。完整审查文件 hash 与现场探针结果见 [review_int1.json](review_int1.json)。

未执行全套四分片或独立六路 G6；没有对所有 Python 动态行为做形式证明；新增路径的全局数值性能与全部 15 例结论不在本项审查范围。上述计数只是当前证据快照，最终收口以主报告冻结的逐站审计为准。
