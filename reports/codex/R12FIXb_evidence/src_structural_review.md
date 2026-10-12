# R12FIXb：src structural 逐站点只读复核

- 输入：`raw_scan_round4.json`；非 numerical `closed-*` 共 **396** 项 / **30** 个源码文件。
- 每项包含实际 path/function/rule/node/source、局部理由与 disposition；**正式例外批准数为 0**。
- 未读取旧 16936 豁免作为审批依据；不是独立 G6（本审查者此前负责机械简单化）。
- 文件哈希仅是当时核证证据，不作 policy 依赖快照；函数/节点改变后须重新对照审查，不连带锁定无关文件。
- 当前 AST 不再存在：0 项（若并行已改写，详见 JSON，不能移植旧节点理由）。

## 分类计数

| 分类 | 数量 |
|---|---:|
| APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL | 21 |
| CACHE_IDENTITY_NOT_DISPATCH | 37 |
| CANDIDATE_CERTIFIED_BY_EXACT_INPUT | 11 |
| CANDIDATE_CHECKED_PREDICATE_ONLY | 4 |
| DATA_COLLECTION_OR_LABELING | 54 |
| DATA_CONTAINER_FACTORY | 3 |
| DATA_SERIALIZATION_REFLECTION | 15 |
| DECLARATION_OR_TYPE_DATA | 53 |
| IEEE_BITCAST_CONSTRUCTION_BOUNDARY | 14 |
| IMMUTABLE_WITNESS_PROTOCOL | 8 |
| TUPLE_DISPLAY_JET_PROTOCOL | 4 |
| PROOF_CONTROL_FLOW_GAP | 4 |
| PUBLIC_OPTION_FORWARDING | 1 |
| REMAINING_NUMERIC_CALLBACK_REWRITE_REQUIRED | 11 |
| REMAINING_SIMPLE_NUMERIC_DYNAMIC_REWRITE_REQUIRED | 2 |
| REQUIRED_PUBLIC_DIAGNOSTIC_CALLBACK | 5 |
| SCALAR_PROTOCOL_DECLARATION | 2 |
| SOURCE_PROOF_GAP_EXACT_FLOW | 131 |
| TYPE_GUARDED_FIELD_DATA | 12 |
| VALIDATION_ERROR_PATH | 4 |

## 未完成的必要边界

- SOURCE_PROOF_GAP：已沿源追踪的 Fraction/int、类型守卫、迭代器/递归摘要缺口应修分析器，不以成批 waiver 代替。
- 三处 cmp_to_key 数值角序比较、geom3._quickhull_once 的 off_line key、Dual.__rsub__ dunder 直接访问均可继续机械简单化；此轮只读没有改数学算法。
- central_difference 的外部 f 是公开 G3 诊断 API；不能证明任意 f 内部无禁止模式，必要边界不得叙述成全程序保证。
- Dual 一般非半整数 power 使用 Decimal80 近似，与 oracle_construction 的候选+原输入 exact midpoint certificate 不同；不得合并为“Decimal 安全”。
- legacy/随机采样/首入 brute 只批准其诊断或候选身份，没有精确构造/搜索完备性批准。
- 缓存 implementation 函数身份已核查不被执行；新插入容器 callable 调度仍须红。

## 可复核文件

- `src_structural_review.json`：每节点完整记录。
- `write_src_structural_review.py`：固定的逐范围人工分类映射 + AST 存在性核查；**不是生成允许策略的工具**。
- 主报告与最终 static policy 是否采用/拒绝记录由根代理负责。


## 后续授权机械改写的对照（不是豁免批准）

原复核完成后，根代理授权将所列 5 个剩余数值动态站点改为直接运算/显式 key/稳定局部比较。原 JSON 的源码哈希与 `current_ast_node_present` 保留**改写前审核时点**；当前复核有 9 个旧 AST 报告节点已不存在，对照见 `src_structural_review_post_rewrite.json`。另有 4 个相同 Name AST 只作为直接 Call.func 留存，原高阶值使用已消除；原 `REMAINING_*` 间接形态当前剩余数为 0；不得把已消除旧节点搬进新 policy。定向 `538 passed in 29.20s`，以及实际排序循环 150 次稳定身份序等价检查通过。所有正式例外仍待根代理逐站点审定，本文件无批准授权。


## round5 措辞收窄

`_FrozenNormal.__new__` 四项改归 `TUPLE_DISPLAY_JET_PROTOCOL`：tuple 显示值虽不可原地改动，raw/derivatives 附加属性可重绑定，不能称 immutable witness。当前 src 只有构造器写这些字段；任意外部修改不在本局部源码证明范围。`_ExactFloat` 则有普通 __setattr__ 拦截。此更正不修改源代码或正式批准状态。
