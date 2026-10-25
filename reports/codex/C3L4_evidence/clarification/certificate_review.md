# C3-L4 阈值证书比较：独立复核

## 范围与结论口径

本记录由 sensitivity 子任务独立审阅比较器形成，不改 Python/C++ 数学实现，不复跑全量语料；它不是 Claude 的里程碑对抗核查。检查对象是 `tools/eab2_c3l4_diff.py` 的 `compare_sensitivity`、`verify_sensitivity`、`verify_implicit`，以及其调用的 C3-L3 原始几何、LP、多项式和单侧 Sturm 验证器。

最新裁定允许**所选临界基不同导致的阈值派生标签差异**，不允许漏验某一侧、不允许把共同错误当一致、不允许丢失实际越零分量，也不豁免有限承载力等其他族的标签。

## 独立算术链及信任边界

1. `rebuilt_problem` 从已验收 L1 接触标签选择原始多边形边，重新形成 T、N、摩擦两列及其作用在两物体上的相反广义力；力矩使用 `(p-dof_anchor)×g`。恒载进入负 RHS，活载进入 A 的 alpha 列，参考点荷载先转到锚点。它不使用导出的 A、T/N 当数值裁判，也不调用生产投影器。
2. `rebuilt_seed` 从按原始顶点 ID 给定的 Fraction jets 独立微分；核同坐标共享顶点的种子一致，包含 `d[(p-a)×g]`、锚点变化及活载列导数。导出的 `dA/db/dc` 只是待核对象，不是重建输入。
3. `verify_limit` 用上述矩阵核原/对偶可行与精确目标等式，或核可行点加归一化改进射线/Farkas。`verify_critical` 分别核两端、精确阈值原始 LP、开放/闭合状态和临界基多项式。
4. `verify_branch` 的恒等式核验不是少量近似采样：A 对 μ 仿射；det 次数不超过 m，分子次数不超过 m+1；在 m+2 个不同且 det 非零的精确点，用独立 Fraction 消元重算 det 和所有 Cramer 比值。次数界加精确样本足以证明对应多项式恒等式。奇异样本不计数且总扫描点数足够，所有分子数量、标签与基下标均有形状/身份检查。
5. `branch_signs` 先用精确多项式除法剥离区间两端根，再对剩余多项式建立有理 Sturm 链，排除开区间内的根，最后检查比值符号。中点只在无内部根已被证明之后取符号，不以中点正值代替无根证明。导出 signs 必须与独立计算逐项相等。

接触集合的选择/完备性仍来自已验收的 L1 裁判和本次整链差分；本检查不声称自己又独立实现了一套接触枚举器。Python 生产求解器用于产生待比较一侧，核证算术没有复用其 LP、敏感性、几何 seed 或多项式 helper。

## 全部 crossing 与每个 slope

- 闭阈选择仍成立的 upper/improving-ray 基；开阈选择 lower/mechanism 基。除完整 `verify_critical` 外，敏感性检查显式要求所选侧 continuation signs 非 null；非零区间的 signs 不可为空；阈值处 det 非零且全部分量非负；至少存在一个声明有效的方向。
- 分支再次按 **threshold_certificate.problem 的列标签顺序** 运行 `verify_branch`，不能把另一端的列下标错解释为阈值 LP 的列。
- 对所选基所有分子逐一检查阈值精确零和失效侧第一个非零 Taylor 系数，独立构造完整 crossing 列表。然后分别解基变分，逐分量核 `phi_p`、`phi_mu`、`-phi_p/phi_mu`、对应 k 及标签。
- `implicit_components` 要求与这张完整列表精确相等；`piece_jacobians` 与完整逐分量斜率一致；`selected_piece` 绑定 kind/basis/entering。因此 component extra/missing/duplicate、错误 slope/phi 不会被集合去重掩盖。
- 标签集合比较前先检查实际 `tied_labels` 没有重复。通用 ABI 的 caller 字符串标签保持原合同，与完整派生 crossing 标签合法合并；**不能**把 caller 字符串强制当作派生 ColumnLabel。
- 本次正式运行另在语料准入核实所选 implicit 查询没有 caller 声明标签，并在库存中记录。因此本轮双方实际标签恰好是各自基的全部真实 crossing；这只是已选语料域，不是缩窄公共 ABI。
- 斜率相同才允许 smooth/有效单侧导数；多个不同斜率必须 tie、无标量斜率。两侧精确阈值、attained、导数值、方向符号、differentiability/quality/reason/validity_conditions 继续严格比较。

## 比较器入口与窄豁免

`compare_sensitivity` 自己完成 Python 和 C++ 两侧的 `verify_critical` 与 `verify_sensitivity`，不再依赖外层 runner 恰好提前验过 Python。随后只有 `target=critical` 且两侧 `method=implicit_certificate` 时，才将基依赖的 `tied_labels` 从跨后端相等比较中移出。每侧完整性检查已先完成，差异条目保存双方 selected piece、标签和每个 crossing 的 phi/斜率。非阈值标签仍严格比较。

这不是直接忽略所有 ties，也不是因为数值斜率恰好相等就跳过证书。双方同时伪造相同标签/斜率仍必须在各自原始几何核验中失败。

## 复核中发现并处理的问题

1. 原入口主要依赖外层核 Python；已将双侧核证收进比较器自身。
2. 原标签 set 会吞重复；已先拒重复再核精确成员。
3. 原导数验证缺所选侧 continuation/端点可行性/有效方向 guards；已按 Python 数学合同补齐。
4. 原分支下标可能由端点列序解释到另一个阈值列序；已绑定阈值原始问题再验多项式。
5. 中间曾提出 `declared_tied_labels` 必须属于真实 crossing 的过严建议。独立审阅用 `c_api.h` 的“caller strings / derived structured labels”及 Python `_threshold_sensitivity2` 的合法 union 指出冲突；主代理明确撤回。未交付此规则，也未修改 ABI/Python 合同。恢复合法 caller union，并将“本轮查询 caller 为空”放在语料准入而不是通用验证器。把可信 query 输入也改掉后称双方输出伪造的中间负门一并撤回。

## 负输入门与源内变异门

负输入门分别覆盖 Python、C++、两侧共同错误：标签 extra/missing/duplicate，component extra/missing/duplicate/wrong slope，标量 wrong slope；两侧完整 critical polynomial/Sturm 也有独立篡改负门；另有合法不同临界基及合法 caller 标签正门、非阈值标签仍严格的门。

负输入门本身不冒称 AGENTS 的“内部变异”。另由 `tools/eab2_c3l4_certificate_mutations.py` 在全新子进程中加载真实比较器的隔离源码副本，分别删去/弱化源码内验证，再调用这些具名门。真实源文件不被编辑，runner 不改返回结果；每个缺陷须引发指定 `DID NOT RAISE` 或非阈值标签语义断言失败。语法错误、导入失败、哈希红不能算杀死变异。

8 个内部缺陷：跳过 Python sensitivity 核证、跳过 C++ sensitivity 核证、用 set 吞重复 crossing、漏 crossing 标签精确成员核验、漏 component/phi/slope 等式、跳过 Python critical 核证、跳过 C++ critical 核证、把豁免扩大到非阈值。

### 最终 r2 实测

命令：

```text
python tools/eab2_c3l4_certificate_mutations.py --output eab2/build/tmp/c3l4_certificate_mutations_r2
```

每个 child 的 pytest 命令均带 `-p no:cacheprovider` 和该 child 独立的显式 `--basetemp`；TEMP/TMP 均在本次 ignored build 目录。重复执行必须给新输出目录，不能复用旧进度。

| 源内缺陷 | 被杀死的具名门后缀 | 实测红 |
|---|---|---:|
| `skip_python_sensitivity_certificate` | `each_threshold_side_rejects_false_labels_and_slopes[component_slope-python]` | 1 |
| `skip_cpp_sensitivity_certificate` | 同族 `[component_slope-cpp]` | 1 |
| `set_dedup_hides_duplicate_crossing` | 同族 `[duplicate-cpp]` | 1 |
| `omit_crossing_label_exactness` | 同族 `[extra-cpp]`、`[missing-cpp]` | 2 |
| `omit_component_slope_equations` | 同族 `[component_slope-cpp]` | 1 |
| `skip_python_critical_certificate` | `each_threshold_side_rechecks_full_critical_proof[polynomial-python]` | 1 |
| `skip_cpp_critical_certificate` | 同族 `[sturm-cpp]` | 1 |
| `ignore_non_threshold_tied_labels` | `non_threshold_tied_labels_remain_strict` | 1 |

前后 baseline 各运行 10 个具名节点，包含合法非唯一基和合法 caller 标签正门，原始末行分别为：

```text
10 passed in 2.19s
10 passed in 2.20s
C3L4_CERTIFICATE_MUTATIONS_OK baseline=2 rejected=8 semantic_failures=9
```

总耗时 11.187 秒。8 个 mutant SHA-256 均不同；所有 `semantic_outcome_verified=true`，全部监视源文件前后 SHA-256 一致；真实 Python 数学文件未改。详细命令、精确替换前后片段、源指纹、目标语义红和各 child 日志路径均在 [summary.json](file:///D:/eab-wt/cx-c0/eab2/build/tmp/c3l4_certificate_mutations_r2/summary.json)，汇总原始输出在 [run.log](file:///D:/eab-wt/cx-c0/eab2/build/tmp/c3l4_certificate_mutations_r2/run.log)。

最终受审比较器 SHA-256：`d434800c8c83da5608461223745262544060e6c9117e08b92276da8cab90d9c7`；测试文件：`710a9c0b278b2a1722a74cf7150a62bf822aecad745bdbfbe6951f6d4a6b0e6b`；内部变异 runner：`1928ffa2d637e7a83d6e91e6da3df91b6fa04eb86d29aaf52fb46e3889ed528c`。

中间 r1 已被 r2 取代，不作为最终源码证据。复核结论：本次限定比较规则未发现剩余上述核证缺口，caller 合同保留，基依赖标签差异只有双侧完整证书验证后才进入差异台账。本结论不代替完整语料执行或全输入正确性证明；根代理负责全量六层、fresh build、快档与四分片全档。
