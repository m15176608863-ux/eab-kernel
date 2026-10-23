# C3-L3 返修：单侧阈值证明豁免的作者团队内部复查

## 1. 身份、范围和结论

本记录由实现团队的 `statics` 协作者完成，属于**作者团队内部复查，不是 Claude 安排的独立对抗验收**。只读核查 [差分检查器](../../../tools/eab2_c3l3_diff.py) 的 `verify_limit`、`verify_branch`、`branch_signs`、`verify_critical`、`semantic`、`compare`，以及 [检查器单测](../../../tests/test_eab2_c3l3_harness.py)。复查者未修改这两个文件、C++ 生产代码或 `src/eab`；补强由 `harness` 协作者实施，本文件是复查者本轮唯一写入。

**最终结论：在本次核查范围内未发现剩余阻断。** 单侧 `exact_threshold=null` 的放行，确实在两侧数学核证完成之后才发生；发现并补上了被整体归一的阈值证书元合同及互斥附件检查，以及零闭阈直接分支的伪延续证明检查。这里修的是返修检查器自己的门，不是发现了 C++ 生产数学缺陷，也不替代最终全档、权威差分或外部验收。

本轮只读取正式冻结语料并调用检查器：**0 次生产求解器调用、0 次 DLL 调用、未运行全档、未重跑数值差分**。对比探针修改的是内存中的证书副本，属于检查器单元负例；它不是生产代码内部缺陷注入，不据此声称生产 mutation 门有牙。

## 2. 数学核证在归一之前

最终快照中的执行次序如下：

1. `compare` 先分别调用 `verify_critical(expected)` 和 `verify_critical(actual)`，不是先把字段抹平再核证。
2. 括号必须有合法顺序、可精确表示为 binary64 的端点，导出的 bits 与有理值一致；上端为 `UNBOUNDED`，有宽度时下端为 `OPTIMAL` 或 `INFEASIBLE`。端点及阈值的 LP 证书通过 `verify_limit` 核验。
3. `rebuilt_problem` 从原始顶点、已验收 L1 接触标签、实际自由度/锚点及荷载重新构造 `A,b,c`；不把 C++ 导出矩阵直接当 oracle。这里仍以 L1 标签确定接触，不声称重新独立发现全部接触拓扑。
4. `verify_branch` 由上述几何重建 `A(0),A(1)`；用独立 `Fraction` 消元在足够多的不同非奇异参数点核 determinant/Cramer 多项式恒等式，并验证维数、次数、标签、基列、进入列和采样值。它不只是核一个导出采样点。
5. 延续分支角色和采样参数绑定相应端点。`branch_signs` 仅剥离区间端点根，再用有理 Sturm 链排除内部根并核符号。闭阈非零时必须有下侧有界延续；开阈必须有上侧改进延续、阈值严格低于上端且恒载为零，以保证全上侧可用的精确可行点。
6. 无阈值一侧必须同时保持 `attained`、`threshold_certificate`、`threshold_proof`、`threshold_proof_reason` 为 null；有阈值一侧须先通过数学核证及新增证书合同核验，才归一四个明确字段并追加 disposition。

四个新增归一字段仅为 `exact_threshold`、`attained`、`threshold_certificate`、`threshold_proof_reason`。它不是对状态、括号、二分终止原因或其他顶层字段的整体豁免。

需要准确表述既有比较边界：`semantic` 本来就不逐字节比较非唯一 `basis`、`queries`、`problem`、`threshold_proof`、`mechanism`；原/对偶等 witness 经数学核验后只保留是否存在；`critical_polynomials` 比较是否非空而非基选择或多项式字面值；端点按精确值比较。问题、机构和多项式的数学意义由前置核证守护。因此报告不应将本比较描述为“除四字段外所有 JSON 字段逐字节相等”。

## 3. 本次发现和最小补强

### 3.1 整体归一的阈值证书可能掩盖非数学合同错误

原逻辑的 `verify_limit` 能核精确最优/无界证书，但不单独核成功结果的全部元字段和无关状态附件。将整个 `threshold_certificate` 归一后，内存副本中的四个错误曾得到以下结果；语料为 `coverage_resolution_bracket`：

```text
THRESHOLD_CERT_FIELD call_status strict_differences 1 enrichment_differences 0 dispositions 1
THRESHOLD_CERT_FIELD display_status strict_differences 1 enrichment_differences 0 dispositions 1
THRESHOLD_CERT_FIELD exact_y strict_differences 1 enrichment_differences 0 dispositions 1
THRESHOLD_CERT_FIELD validity_conditions strict_differences 1 enrichment_differences 0 dispositions 1
```

错误分别为 `INVALID_INPUT`、`INVALID_DISPLAY`、无界阈值证书中额外的 `exact_y=['123/1']`、虚构有效性条件。它们没有破坏既有正确的可行点/射线，所以仅做数学检查不足以拒绝。

新增 `verify_threshold_certificate_contract` 只在拟进行单侧豁免时调用，并位于任何归一和 disposition 追加之前：固定 14 个必需字段，仅允许额外 `mechanism`；核成功 call/display、`ideal_exact_2d`、null reason、由接触记录 `REDUNDANT_PROVED` 导出的有效性条件、非空问题；拒绝未知键和 OPTIMAL/UNBOUNDED 的互斥附件。精确值、点/射线、原/对偶及可选机构仍由先执行的数学核证负责，不新增基相等要求。

### 3.2 零闭阈早退未核延续字段

正式语料 `g1_koureas_h0_t1` 是直接零闭阈。原早退允许虚构 `threshold_proof_reason` 被单侧豁免吞掉；虚构 `threshold_proof` 则连原来的严格路径也会因 `semantic` 忽略该字段而放过：

```text
ZERO_THRESHOLD_FIELD threshold_proof_reason strict_differences 1 enrichment_differences 0 dispositions 1
ZERO_THRESHOLD_FIELD threshold_proof strict_differences 0 enrichment_differences 0 dispositions 1
```

最终 `verify_critical` 在 `lo=hi=threshold=0` 且闭阈的早退前，要求 `threshold_proof` 和 `threshold_proof_reason` 同为 null，符合 Python 的直接零阈分支；该检查覆盖双方，并不只作用于豁免路径。

## 4. 修复后独立于生产求解的复测

复查者按同一四个错误，在“Python 有证明”和“C++ 有证明”两个方向各测一次；零闭阈两个错误也按两个方向各测一次。错误必须触发下表指定语义断言，且 `dispositions` 必须仍为空；不是只接受任意异常。合法有证明/无证明配对两个方向仍通过，并记录 `threshold_certificate_contract_verified=true`。

| 探针 | 两向次数 | 指定拒绝原因 |
|---|---:|---|
| 阈值证书 call_status | 2 | `threshold certificate contract: call_status` |
| 阈值证书 display_status | 2 | `threshold certificate contract: display_status` |
| 无界阈值证书多出 exact_y | 2 | `threshold certificate contract: exclusive payload` |
| 虚构 validity_conditions | 2 | `threshold certificate contract: validity_conditions` |
| 零闭阈伪造 threshold_proof_reason | 2 | `direct closed zero must not invent a continuation proof` |
| 零闭阈伪造 threshold_proof | 2 | 同上 |

本次直接探针原始末行：

```text
C3L3_INTERNAL_CHECKER_REVIEW_OK valid_enrichment=2 contract_rejections=8 zero_proof_rejections=4 solver_calls=0 dll_calls=0 source_unchanged=true
```

持久具名门包括：

- `test_c3l3_nonunique_threshold_enrichment_requires_independent_proof`
- `test_c3l3_threshold_enrichment_rejects_missing_required_continuation`
- `test_c3l3_threshold_enrichment_cannot_waive_false_proof_reason`
- `test_c3l3_threshold_enrichment_cannot_hide_certificate_contract_corruption`
- `test_c3l3_open_threshold_enrichment_cannot_carry_an_unbounded_payload`
- `test_c3l3_direct_closed_zero_cannot_invent_a_continuation_proof`

上述门可用以下定向命令复跑；这里只给复跑方式，不将它冒充复查者本轮执行过的 pytest 命令。`harness` 协作者另报本文件全部门 `45 passed in 4.38s`，原始 pytest 日志由主报告引用。

```powershell
$env:TEMP=(Resolve-Path eab2/build/tmp).Path
$env:TMP=$env:TEMP
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider --basetemp eab2/build/tmp/c3l3_internal_checker_repeat tests/test_eab2_c3l3_harness.py -k 'threshold_enrichment or direct_closed_zero'
```

## 5. 快照和边界

| 文件 | 修补前复查快照 SHA-256 | 最终复查快照 SHA-256 |
|---|---|---|
| `tools/eab2_c3l3_diff.py` | `afbe425b17061c8fc59d4149492c64f9de59a7c7bd744f9cc0f9561be43ed40c` | `f9e66ec40e78107836f66b1e5368f465624975e08d1d42348559bb2d915f6649` |
| `tests/test_eab2_c3l3_harness.py` | `5e51ec30400ab52df4f9e7b02c507d8bb1bfc6af042f669fe65e97ec1227194f` | `30d915573ecbff3cde817f8bb9f6479752bdca3d396415950585f94dfd75890d` |

最终直接探针前后重新计算两个文件 SHA-256，均保持一致。这些哈希只标识本次已读快照，不把冻结数学数据绑定到当前源码，也不替代语义测试。

有限探针与代码阅读未证明检查器对任意未来 schema、所有输入域或所有错误都完备；没有据此宣称外部验收已经关闭。生产内部 mutation、完整权威差分与 Python 收尾全档仍分别以对应执行者的原始证据为准。
