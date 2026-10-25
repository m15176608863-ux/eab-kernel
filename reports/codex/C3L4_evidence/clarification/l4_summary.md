# C3-L4 裁定后完整差分摘要

只读复核：本摘要只解析本次正常完成的 L4 JSON，不调用 DLL、Python 裁判、LP 求解或 pytest。此前在 thickness/control/08 中断的运行未拼接；本次从头完成全部查询。最终 H1、真实使用者及发布验收状态由主报告另述。

- 原始末行：**`C3L4_DIFF sensitivity=402 mismatch=0`**。
- 175 模型、402 查询、0 失配，耗时 **171.109 秒**；运行前后源码一致，记录的 30 项源码 SHA-256 与当前文件全部一致。
- 阈值隐函数 **70 查询 / 140 侧**独立核证；基依赖标签差异 **32 查询 / 16 模型**逐项登记，不是静默删除字段。
- 斜率 proof floor：**393 个非空字段**、0 exceptions；不是 393 个独立参数查询。
- **32 条非 binary64 精确输入**逐条登记为 `ABI_INPUT_DOMAIN_EXCLUSION`，不计失配，也不因此标记 PARTIAL；未将其舍入后冒充原输入执行。

[本次完整结果 gzip](../differential/l4.json.gz) · [紧凑审计 JSON](l4_summary.json)。压缩件已逐字节解压回验；以本摘要的原始数据 SHA-256 识别运行，不能因旧同名文件被更新而混用结果。

- L4 JSON SHA-256: `286dc40618edc56ab99ad4e94a97614f1513350cea4eb1ae43b3192a305e416d`.
- Release DLL SHA-256: `b08c5558572831b52f17a60253e2ce1ede450a31eed800d8a5b3b053124c75df`.

## 1. 逐族计数

| 家族 | 模型 | 查询 | smooth | one_sided | singular | unresolved | 失配 | 标签登记 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| formal/TIA-G1 | 27 | 75 | 14 | 0 | 8 | 53 | 0 | 0 |
| formal/TIA-G5 | 27 | 69 | 55 | 2 | 10 | 2 | 0 | 0 |
| formal/named_regression | 7 | 11 | 3 | 0 | 5 | 3 | 0 | 0 |
| formal/TIA-G2 | 15 | 39 | 0 | 0 | 3 | 36 | 0 | 0 |
| formal/TIA-G3 | 15 | 39 | 0 | 0 | 3 | 36 | 0 | 0 |
| formal/TIA-G4 | 15 | 39 | 0 | 0 | 3 | 36 | 0 | 0 |
| formal/contract_coverage | 8 | 8 | 1 | 0 | 4 | 3 | 0 | 0 |
| t1b | 36 | 72 | 54 | 0 | 0 | 18 | 0 | 32 |
| thickness | 25 | 50 | 2 | 0 | 0 | 48 | 0 | 0 |

## 2. 标签裁定范围与逐查询登记

只有阈值 `implicit_certificate` 的跨后端标签集合不要求相等；导数、D+/D−、可微性、quality、reason、有效条件、attained 和精确阈值仍严格相等。非阈值 ties 仍严格比较。

每侧先由原始几何独立核其临界 LP 证书、多项式恒等式及单侧 Sturm，核所选基在阈值处仍可行、所选端连续有效，并逐真实越零分量核 `−phi_p/phi_mu`。公开 ABI/Python 的 caller 标签并集合同不变；本轮冻结隐函数库存的 caller 声明全部为空，入口要求这一条件，故本轮结果标签恰为该侧全部真实越零标签。

本次只读复核额外检查了完整 32 条登记：每条 `semantic_fields_equal=true`；两侧均保留 selected_piece、完整 ties、implicit_components 和 piece_jacobians；标签无重复，标签集合恰等所有分量标签；分量序号唯一；每个 phi_mu 非零且有理算术 `−phi_p/phi_mu` 等于所报斜率；两侧分量斜率均与该查询 D+、D− 符号一致。此处是已执行证据的一致性复核，不冒充重新进行 LP/Sturm 求解。

下表“标签/分量”给出 Python 与 C++ 各自计数；所有行都已通过上述检查，完整两侧标签与分量保存在原始 JSON 的 `threshold_label_comparison.dispositions`。

| case | query | 参数 | Python 标签/分量 | C++ 标签/分量 | 共同 D+ |
|---|---:|---|---:|---:|---|
| `t1b/00` | 0 | amplitude | 3/3 | 3/3 | `534254080/16785409` |
| `t1b/00` | 1 | tilt | 3/3 | 3/3 | `4071/4097` |
| `t1b/04` | 0 | amplitude | 2/2 | 2/2 | `-2145254336/67125249` |
| `t1b/04` | 1 | tilt | 2/2 | 2/2 | `8183/8193` |
| `t1b/07` | 0 | amplitude | 2/2 | 1/1 | `-536575776/16785409` |
| `t1b/07` | 1 | tilt | 2/2 | 1/1 | `4093/4097` |
| `t1b/09` | 0 | amplitude | 2/2 | 3/3 | `534515488/16785409` |
| `t1b/09` | 1 | tilt | 2/2 | 3/3 | `4073/4097` |
| `t1b/13` | 0 | amplitude | 2/2 | 2/2 | `-2145516664/67125249` |
| `t1b/13` | 1 | tilt | 2/2 | 2/2 | `2728/2731` |
| `t1b/16` | 0 | amplitude | 2/2 | 1/1 | `-536641358/16785409` |
| `t1b/16` | 1 | tilt | 2/2 | 1/1 | `8187/8194` |
| `t1b/18` | 0 | amplitude | 4/4 | 4/4 | `-267486016/4190209` |
| `t1b/18` | 1 | tilt | 4/4 | 4/4 | `2041/2047` |
| `t1b/20` | 0 | amplitude | 2/2 | 2/2 | `-1071252544/16769025` |
| `t1b/20` | 1 | tilt | 2/2 | 2/2 | `4087/4095` |
| `t1b/21` | 0 | amplitude | 5/5 | 4/4 | `-106945488/836405` |
| `t1b/21` | 1 | tilt | 5/5 | 4/4 | `4083/4090` |
| `t1b/23` | 0 | amplitude | 2/2 | 2/2 | `-2140086080/16736281` |
| `t1b/23` | 1 | tilt | 2/2 | 2/2 | `4085/4091` |
| `t1b/24` | 0 | amplitude | 5/5 | 4/4 | `-85/4` |
| `t1b/24` | 1 | tilt | 5/5 | 4/4 | `255/256` |
| `t1b/26` | 0 | amplitude | 3/3 | 3/3 | `2135434208/67125249` |
| `t1b/26` | 1 | tilt | 3/3 | 3/3 | `8141/8193` |
| `t1b/27` | 0 | amplitude | 3/3 | 3/3 | `533727456/16785409` |
| `t1b/27` | 1 | tilt | 3/3 | 3/3 | `4069/4097` |
| `t1b/30` | 0 | amplitude | 5/5 | 4/4 | `-2721/128` |
| `t1b/30` | 1 | tilt | 5/5 | 4/4 | `8163/8192` |
| `t1b/32` | 0 | amplitude | 3/3 | 3/3 | `2136481312/67125249` |
| `t1b/32` | 1 | tilt | 3/3 | 3/3 | `2715/2731` |
| `t1b/33` | 0 | amplitude | 3/3 | 3/3 | `533989232/16785409` |
| `t1b/33` | 1 | tilt | 3/3 | 3/3 | `4071/4097` |

## 3. 完整 32 条 ABI 输入域外条目

来源为 `tests/data/eab2_c3l3_thickness_summary.json`（原始来源 `reports/codex/T1b_evidence/acceptance_fix/thickness_summary.json`）。全部 reason=`non_binary64_exact_input`。表中列出原始具体文件名、ratio、失败标量字段总数以及证据记录的**首个失败字段和精确值**；不把首个字段冒称完整失败字段清单。每行原样结构化数据亦在紧凑 JSON 中保留。

| 源样本 | ratio | 失败字段数 | 首个失败字段 | 原始精确值 |
|---|---|---:|---|---|
| `thickness_00_00.json.gz` | `392183/4231168` | 42 | `block_1.vertices[1][0]` | `-405015579/135397376` |
| `thickness_00_01.json.gz` | `96/1033` | 42 | `block_1.vertices[1][0]` | `-3090/1033` |
| `thickness_00_02.json.gz` | `26768/265481` | 42 | `block_1.vertices[1][0]` | `-1587867/530962` |
| `thickness_00_03.json.gz` | `28864/265481` | 42 | `block_1.vertices[1][0]` | `-793737/265481` |
| `thickness_00_04.json.gz` | `30960/265481` | 42 | `block_1.vertices[1][0]` | `-1587081/530962` |
| `thickness_00_05.json.gz` | `32/257` | 42 | `block_1.vertices[1][0]` | `-768/257` |
| `thickness_00_06.json.gz` | `131329/1052672` | 42 | `block_1.vertices[1][0]` | `-100662525/33685504` |
| `thickness_01_00.json.gz` | `392183/4231168` | 42 | `block_1.vertices[1][0]` | `-405015579/135397376` |
| `thickness_01_01.json.gz` | `96/1033` | 42 | `block_1.vertices[1][0]` | `-3090/1033` |
| `thickness_01_02.json.gz` | `14572/149785` | 42 | `block_1.vertices[1][0]` | `-3583911/1198280` |
| `thickness_01_03.json.gz` | `15224/149785` | 42 | `block_1.vertices[1][0]` | `-1791711/599140` |
| `thickness_01_04.json.gz` | `15876/149785` | 42 | `block_1.vertices[1][0]` | `-3582933/1198280` |
| `thickness_01_05.json.gz` | `16/145` | 42 | `block_1.vertices[1][0]` | `-867/290` |
| `thickness_01_06.json.gz` | `65681/593920` | 42 | `block_1.vertices[1][0]` | `-56819277/19005440` |
| `thickness_02_00.json.gz` | `392183/4231168` | 66 | `block_1.vertices[1][0]` | `-405015579/135397376` |
| `thickness_02_01.json.gz` | `96/1033` | 66 | `block_1.vertices[1][0]` | `-3090/1033` |
| `thickness_02_02.json.gz` | `1221416/12781309` | 66 | `block_1.vertices[1][0]` | `-152917677/51125236` |
| `thickness_02_03.json.gz` | `1255024/12781309` | 66 | `block_1.vertices[1][0]` | `-76452537/25562618` |
| `thickness_02_04.json.gz` | `1288632/12781309` | 66 | `block_1.vertices[1][0]` | `-152892471/51125236` |
| `thickness_02_05.json.gz` | `1280/12373` | 66 | `block_1.vertices[1][0]` | `-36999/12373` |
| `thickness_02_06.json.gz` | `5255253/50679808` | 66 | `block_1.vertices[1][0]` | `-4849495809/1621753856` |
| `thickness_03_00.json.gz` | `392183/4231168` | 66 | `block_1.vertices[1][0]` | `-405015579/135397376` |
| `thickness_03_01.json.gz` | `96/1033` | 66 | `block_1.vertices[1][0]` | `-3090/1033` |
| `thickness_03_02.json.gz` | `65272/699341` | 66 | `block_1.vertices[1][0]` | `-8367615/2797364` |
| `thickness_03_03.json.gz` | `65552/699341` | 66 | `block_1.vertices[1][0]` | `-4183755/1398682` |
| `thickness_03_04.json.gz` | `65832/699341` | 66 | `block_1.vertices[1][0]` | `-8367405/2797364` |
| `thickness_03_05.json.gz` | `64/677` | 66 | `block_1.vertices[1][0]` | `-2025/677` |
| `thickness_03_06.json.gz` | `262821/2772992` | 66 | `block_1.vertices[1][0]` | `-265418769/88735744` |
| `thickness_04_00.json.gz` | `96/1033` | 66 | `block_1.vertices[1][0]` | `-3090/1033` |
| `thickness_04_01.json.gz` | `4635/33056` | 66 | `block_1.vertices[1][0]` | `-3159471/1057792` |
| `thickness_05_00.json.gz` | `96/1033` | 66 | `block_1.vertices[1][0]` | `-3090/1033` |
| `thickness_05_01.json.gz` | `4635/33056` | 66 | `block_1.vertices[1][0]` | `-3159471/1057792` |

## 4. 已有负门证据与源码一致性

- [定向测试记录](harness_tests.json)：`81 passed in 12.32s`，退出码 0；记录的测试与 checker 源码 SHA-256 均仍匹配当前文件。
- [checker 内部变异](certificate_mutations.json)：`C3L4_CERTIFICATE_MUTATIONS_OK baseline=2 rejected=8 semantic_failures=9`；两次 baseline 各 10 节点通过，8 个真实 checker 源内变异产生 9 个目标语义红，全部 `semantic_outcome_verified=true`，记录的 8 项源码 SHA-256 均与当前文件一致。
- 未重跑上述测试或变异；仅复核已有记录。此项是独立 checker 的牙，不混称为生产 C++ 六类数学变异。

**本次 L4 结论：完整正常运行，402 查询、0 失配；32 条标签差异经逐侧核证登记，32 条非 binary64 样本按明确 ABI 输入域排除。**
