# WO-C3L1：精确 LP 核与 L1 接触裁判 C++ 移植

## 0. 结论与信任边界

**WO-C3L1 收口返修完成：P0/P1 已实现并验证，P2 已报告，退出状态 C3L1_DONE。**

Claude 提供的 **84d514e 原轮**新鲜工作树复现与两名非作者对抗核查均通过（0 critical / 0 major）。本次返修按验收意见修改后，在本树固定字节重新完整构建、四层差分与 Python 快/全档；H1 使用字节导出，不冒称对返修未提交字节又做了一次新鲜 Git 树或独立核查。
**§1–10 保留原实现合同与历史验证；§11 是本次验收返修的唯一当前证据入口。**
横切 LP 20 族 **745/745**、L1 三族 **776** 查询、C1 **657/657** 块对均 0 数学语义失配。
L1 不是逐字全相同：19 个一阶查询存在 **495 项非唯一证书字段表示差异**（9 项 exact_x、486 项零锥乘子）；全部保留；本次逐个以工具从原始几何和实际 masks/anchors 重建的有理矩阵复核。
状态串、生成元集合、矩阵、半径界及 assembly/lock 字段没有此类差异。不能把 `mismatch=0` 写成 `strict_fields=0`。

开工全档 14938 项；本次返修快档 8951 项、全档 15035 项，全部 0 failed / 0 skipped，执行节点多重集合等于收集节点、模块实际执行完整。最终 CTest 9/9。原轮8944/15028结果作为历史保留。
有限测试不是全输入域证明；一阶/平移结果不是完整有限运动或 L3 承载力结论。

- [逐项机器清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/requirements.json)；[验证摘要](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/verification_summary.json)；[全部交付文件与链接](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/deliverables.md)。
- 所有者退出门已由 Claude 提供：见 [验收原文](file:///D:/eab-evidence/reports/codex/C3L1_evidence/acceptance_review/C3L1_acceptance.md)；其结论针对 84d514e。本代理不将其改称对本次未提交返修字节的另一次独立审查。

## 1. 范围、来源与回滚锚

- 工作树 `D:/eab-wt/cx-c0`；基线 `eab2-c3 @ 7540cdec5f4ca06a709deca3673435a091961941`，开工干净。原轮代码已由 Claude 暂存为 84d514e，本次返修是在该提交上的未提交工作区产物；文件哈希见 [build_repair.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/build_repair.json)、[artifact_manifest.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/artifact_manifest.json)。
- 设计 [eab2_design.md](file:///D:/eab-wt/cx-c0/docs/eab2_design.md) SHA-256 `6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac` 未变。
- 原轮只写本树；本轮另获准写 C3L1 专属外归档。未安装、下载或执行 Git 写操作；未改 `src/eab` 数学源码、静态构造准入及外部只读仓库。vendor 71 文件审计通过。
- 回滚由所有者以基线和逐文件修改清单决定，不使用 reset/checkout 丢弃未知修改。PROVENANCE 修改前字节另存 [provenance_before_C3L1.json](file:///D:/eab-evidence/reports/codex/C3L1_evidence/provenance_before_C3L1.json)。
- Python 3.12 H1 监测实际模块执行；pytest 全部禁 cacheprovider、显式 basetemp；原轮有效最终运行 TEMP/TMP 在本单 `tmp` 根下；本次H1仍遵此规则，build脚本按M4改用被忽略的中性 `eab2/build/tmp`。工单开工基线一次，后续各次收尾均按 Claude 续单独立全跑；旧收尾全档被 capacity 中断，整次作废保留，不拼接，依 Claude 续单从头重跑。中间不重算全量冻结证据。
- 最终报告/索引在验证结束后生成；被测 C++/Python/工具/夹具源码以 H1、构建和差分哈希为准，报告更新不冒充另一次新鲜树验证。[基线只读文件与本次受测源码核对](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/source_integrity_acceptance.json)。
- 原轮包装边界审计见 [历史 boundary_audit.json](file:///D:/eab-evidence/reports/codex/C3L1_evidence/_pre_acceptance/boundary_audit.json)：PROVENANCE 沿用原有统一 CRLF，当时默认diff把新增CR报为行尾空白。本次该文件相对84d514e未改，普通 `git diff --check` 为0；相对7540cde的命令局部 `cr-at-eol` 检查也为0，未改配置或已测文件字节，见 [本次 boundary_audit.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/boundary_audit.json)。

## 2. P0-1：横切精确 LP 核

实现 [opt.hpp](file:///D:/eab-wt/cx-c0/eab2/src/opt.hpp) / [opt.cpp](file:///D:/eab-wt/cx-c0/eab2/src/opt.cpp)，命名空间 `eab2::opt` 仅依赖 exact 数值层，不依赖 contact/statics。
标准型 `min cᵀx, Ax=b, x≥0`，两阶段精确单纯形；Dantzig 遇退化/循环转 Bland。
可选候选基只给索引，精确重建并对原始数据核验；默认全有理冷启动，**未启用浮点候选生成加速或浮点过滤器**。

| 状态 | 必须核验的原始模型等式/不等式 |
|---|---|
| OPTIMAL / min | `Ax=b, x≥0, Aᵀy≤c, cᵀx=bᵀy` |
| OPTIMAL / max | 正确翻转目标及对偶；`Aᵀy≥c` 且零对偶间隙 |
| INFEASIBLE | `Aᵀy≤0, bᵀy>0` 的 Farkas 证书 |
| UNBOUNDED | 精确 `x₀≥0, Ax₀=b` **及** `r≥0, Ar=0`，归一化 `cᵀr=-1`（min）或 `+1`（max）；不能只给射线 |
| 齐次/归一化 | 精确等式标准化及归一化可行性，用于一阶与 twist 冗余 |

无界可行点和改进射线由辅助精确 LP 构造后再核；主元预算包含辅助 LP、Phase I/II 和清人工列。预算/整数范围耗尽为 RESOURCE_LIMIT，无数学答案；意外不变量失败为 INTERNAL_ERROR。
LP 不消费几何 max_work_units。位长仅是已观测存储有理数的整数高水位，不是所有临时 limb 或内存峰值。

门：[test_opt.cpp](file:///D:/eab-wt/cx-c0/eab2/tests/test_opt.cpp) 的 `candidate_reconstruction_rejects_lies / three_statuses_and_signs / exact_scale_and_resolution / asymmetric_scale_grid / cycling_terminates_and_budget_fails_loud / normalization_and_invalid_inputs`；独立 Python [eab2_opt_diff.py](file:///D:/eab-wt/cx-c0/tools/eab2_opt_diff.py)、[test_eab2_opt_harness.py](file:///D:/eab-wt/cx-c0/tests/test_eab2_opt_harness.py)。
差分来源包括既有 `test_lp_certificates.py / test_lp_scale.py / test_lp_fail_loud.py` 的模型族；**只移植 LP 模型/证书，不宣称移植这些族的完整 L3 物理政策**。

[20 族完整差分](file:///D:/eab-evidence/reports/codex/C3L1_evidence/opt_diff_repair.json)：688 optimal、7 infeasible、50 unbounded。

| 族 | 例数 |
|---|---:|
| `certificate_farkas` | 5 |
| `certificate_reverify3` | 4 |
| `basic_random` | 12 |
| `certificate_huge_step` | 18 |
| `certificate_near_parallel` | 6 |
| `certificate_cycling` | 3 |
| `certificate_redundant` | 200 |
| `certificate_exact_edges` | 13 |
| `certificate_max_sign` | 13 |
| `scale_rhs` | 32 |
| `scale_rows` | 32 |
| `scale_binary_rhs` | 24 |
| `scale_zero_rhs` | 4 |
| `scale_columns` | 36 |
| `certificate_si_worst` | 11 |
| `certificate_old_scale` | 48 |
| `fail_loud_cohesive` | 8 |
| `fail_loud_si` | 30 |
| `fail_loud_fine_cone` | 6 |
| `fail_loud_site` | 240 |

## 3. P0-2/3/4：装配、锁定与一阶可动性

实现 [l1.hpp](file:///D:/eab-wt/cx-c0/eab2/src/l1.hpp) / [l1.cpp](file:///D:/eab-wt/cx-c0/eab2/src/l1.cpp)，按设计 §5.1 使用 `eab2::contact`（文件名 l1 保持）；命名空间机械对齐证明见 [namespace_alignment.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/namespace_alignment.json)。

- **逐点装配**：由 C1 零点局部查询取得来源；在每个接触点构造 `F_p`，只保留边界半平面；去重不抹掉作用反作用与来源；极大共线段的内部平坦顶点不出约束但保留来源。真 VV 在完整 twist 空间（包含实际参考点/锚点的转动列）作精确可达/不可达判定，无证明则 MECHANICAL_UNRESOLVED；不靠“同块对有线接触”忽略 VV。
- **平移锁定**：四状态与 NOT_SEPARABLE 的 SEAM_SLIDING / TRANSLATION_IMMOBILE 细化；全部局部锥覆盖及严格有理半径/排除边界证据，REMOVABLE 有精确分离射线；OVERLAP 拒签（不伪造四状态）。与 Python 一样用未凸合并耳切积胞，不改变胞/弧/半径语义。
- **一阶**：只用法向约束；满列秩且归一化精确 LP 值为零才签零锥；否则精确双描述生成元，线性空间双向保留；零锥给非负法向旋量组合 `Gᵀλ=±e_j`。单体、多体、FIXED_BODY、dof_mask、dof_anchor 均覆盖。未解析真 VV 不枚举模态；完整性未知保留 UNPROVED。
- **获批合同沿用**：dof_anchor、极大共线段内部平坦顶点规则，以及 profile1 中已证冗余真 VV 不进入 L3 力贡献。本单没有实现 L3 力学，不能宣称已验证承载力。

具名门：[test_l1.cpp](file:///D:/eab-wt/cx-c0/eab2/tests/test_l1.cpp) 的 `six_regressions / provenance_and_flat / mobility_cases / lock_cases / dd_oracle / exact_metamorphic / resource_guards`；Python 门 [test_eab2_c3l1.py](file:///D:/eab-wt/cx-c0/tests/test_eab2_c3l1.py)。

## 4. P0-5：正式语料、六个回归及独立比较

期望侧只使用 Python 生产裁判、stdlib Fraction 和独立 JSON/有理数解析；不导入或调用 C++ helper/DLL 计算期望。
ctypes 模块只传送 C++ 实际结果，解析拒绝重复 JSON 键、非规范有理串等歧义。独立核对原始 LP/旋量等式，不能仅以“目标值相同”接受坏证书。
冻结语料先严格复核；没有用改哈希代替实际小集/全差分重放。

| 来源 | 输入数 | assembly | first_order | lock | 合计 |
|---|---:|---:|---:|---:|---:|
| tia2d-2 `formal_20261019_02` | 114 | 114 | 114 | 350 | 578 |
| T1b 冻结诊断档案的 L1 投影（非 tia2d-2 正式批次） | 36 | 36 | 36 | 0 | 72 |
| 精确变换补充 | 36 | 36 | 36 | 54 | 126 |
| 总计 | 186 | 186 | 186 | 404 | 776 |

T1b 入库 [36 例来源与逐文件哈希清单](file:///D:/eab-wt/cx-c0/fixtures/eab2_cases/t1b_l1/manifest.json)；投影冻结 Body 输入及 first_order 证书；原档是诊断 schema，未生成新 tia2d-2 正式批次。完整 assembly 期望由独立 Python 重算，并核原档 contact_status / constraint_count；原档并无完整 ContactSet2。顶点与参考坐标可无损表示为 binary64，不重算 L3，不依赖外部档案继续回归。
总来源登记新增 37 条（manifest+36 gzip），原 386 条及所有数据字节不变，[追加证明](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/provenance_append_audit.json)。

### 六个具名回归（d 有两个 μ 版本，共 7 例 / 27 个 L1 查询）

| 回归 | 守护的 L1 事实 | 结果 |
|---|---|---|
| a 锯齿 | 4 个端点约束，尖点两个边界而非任意原始 cover | RESOLVED；NONZERO_CONE |
| b 裸真 VV | 无伪半平面，有精确可达见证 | 装配/一阶均 MECHANICAL_UNRESOLVED |
| c 冗余 VV | twist 不可达证书保留转动自由度 | RESOLVED；一个 REDUNDANT_PROVED 证书 |
| d 平齐 μ=0 / 1/4 | 正式装配 8 约束，所有点 F_p=CONVEX，边界仅 `(-1,0)` | 两版均通过；不核承载力数值 |
| e 同块对线接触+真 VV | 线段的 2 约束不使另一 VV 自动冗余 | MECHANICAL_UNRESOLVED |
| f 凸尖入凹口 | F_p=CONVEX，两个真实边界 | RESOLVED；2 约束 |

上述 27 查询严格字段差异也是 0。C++ 单测使用小构型和解析法向另核，不能把其单接口 d 的 2 约束与正式多接口 d 的 8 约束混为一个算例。

正式 114 例状态分布（不是全部变换/T1b 混计）：
- `assembly`：`MECHANICAL_UNRESOLVED` 2；`OVERLAP` 1；`RESOLVED` 111。
- `first_order`：`MECHANICAL_UNRESOLVED` 2；`NONZERO_CONE` 74；`OVERLAP` 1；`UNPROVED` 1；`ZERO_CONE` 36。
- `lock`：`NOT_CONTACT` 2；`NOT_SEPARABLE_TRANSLATION` 276；`OVERLAP` 1；`REMOVABLE_TRANSLATION` 71。

唯一 UNPROVED 来自未知候选完整性，不是被隐瞒的迭代预算失败。
495 项表示差异仅在 19 个正式 first_order 查询：所有非唯一 primal/乘子均按原始模型精确复核；生成元按集合规范比较，排序不构成数学差异。完整每项差异见 [diff_repair.json](file:///D:/eab-evidence/reports/codex/C3L1_evidence/diff_repair.json)，不丢弃到“前十项”。

```text
OPT_DIFF selected=745 completed=745 mismatches=0
C3L1_DIFF assembly=186 first_order=186 lock=404 mismatch=0 strict_fields=495
C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086
EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS
```

## 5. P0-6 与 P1-7：ABI 增量及 C1 小项

工作 ABI，非 C3 全阶段发布稳定 ABI；完整签名和限制见 [c_api.h](file:///D:/eab-wt/cx-c0/eab2/include/eab2/c_api.h)、[testing.h](file:///D:/eab-wt/cx-c0/eab2/include/eab2/testing.h)、[ABI_CONTRACT.md](file:///D:/eab-wt/cx-c0/eab2/ABI_CONTRACT.md)。

- 新增 get_c3l1_abi_info；Assembly2 创建/释放、ContactSet2 装配/精确导出/释放、query_lock、first_order_mobility；opt_solve_exact 仅测试 DLL。
- 正式能力 ASSEMBLY2=512、CONTACTSET2=1024、LOCK2=2048、MOBILITY2=4096；TEST_OPT=8192 仅测试；LP2 仍预留 L3。数学状态 MECHANICAL_UNRESOLVED=7，不与调用失败混淆。
- 输入显式参考点/锚点、固定边界与 mask；contact set 持有独立快照。锁定查询显式 moving/neighbor 索引，每个指定邻体当次固定，不从 mask 推断遗漏邻体。
- 保持 C0/C1 结构尺寸、generation/owner/type 句柄防错、失败输出与库内释放；资源拒签不输出数学结论。

| C1 遗留项 | 处置与证据 |
|---|---|
| 坏 FP 下清理/读 limits | body/entrance/result/C3 destroy 与 get_limits2 跳过 FP 自检；`release_bad_fp` 实测 FTZ/DAZ、3 舍入模式、6 屏蔽位及宿主状态不变 |
| 跨 context 并行 | 全局锁仅注册表解析/共享所有权固定，计算用 context 锁；`concurrent_contexts` 在真实计算锁内双线程会合证明重叠；测试钩子不进正式 DLL |
| exterior/CONTACT 层比较 | `verify_contact_layers/compare_exports` 核 exterior_state、CONTACT 边区间并集及端点/孤立点等于规范骨架；657 例、100086 双向层查询 0 失配 |
| numeric_batch 工作范围 | 原轮采用文档方案；验收返修 M1 已增加逐项 IntegerLimitScope 与 RESOURCE_LIMIT 映射，见新增 numeric_compute_budget_matrix；最终完整验证另列 |
| LIMITS2/README | ABI 文档列出 LIMITS2；README 说明两 DLL 均含运行时派发 AVX2 STL，不误称受控 TU 用 AVX；移除硬编码运行路径/过期入口 |
| 生产 C 头与 NO_COMPACT | C 头对生产 DLL/静态库均调用 C1；NO_COMPACT 在 README/ABI 明示仅诊断 |

本轮 C1 与 LP/L1 均从头在同一最终字节固定 DLL 上重新执行，C1 的657例与100086双向层查询不借用 build03 结果。早期 build03 差分仅作历史证据保留。最终 DLL 另已从头跑全部 C++ 单测、CTest、C 头与 C0 数值差分；统一来源哈希与逐阶段记录见 [closeout_repair_run.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_repair_run.json)。

## 6. P1-8：元门与门的牙齿

- C++ `exact_metamorphic`：4 个 90° 旋转×2 反射×3 dyadic 缩放 = 24 组；非原点非对称实际参考点/锚点，平移 `(100000+3/8,-1000+5/16)`；明确按旋转/反射/尺度变换比较生成元集合，反射翻转角速度；同时 48 个缝滑/四面笼锁定查询及严格半径检查。
- Python/DLL 补充：6 个构型×6 种精确变换 =36 输入，含大二进平移至 131072；assembly/first_order/lock 共126查询。不是浮点旋转后假定拓扑不变。
- LP 内部源代码变异 5/5 被指定语义断言击杀；L1 内部变异 5/5（F_p 法向、实际转动列、开锥严格性、平坦点、误凸合并）被指定语义断言击杀。均实际修改被测代码副本、成功编译后由数学语义报红，不是向输出追加假数据或靠源码哈希报红。
- 证据：[opt_mutations.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/opt_mutations.json)、[l1_mutations_final_strict.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/l1_mutations_final_strict.json)。早期 L1 变异产物位置不符合指定 tmp 根，已验证路径后完整迁入并严格重跑；旧证据不删，映射见 [l1_mutations_path_migration.json](file:///D:/eab-evidence/reports/codex/C3L1_evidence/l1_mutations_path_migration.json)。

```text
OPT_MUTATIONS total=5 killed=5 survived=0
EAB2_L1_MUTATIONS mutants=5 semantic_red=5 failed=0
```

## 7. P2：原轮规模与冷调用耗时（历史快照，不设门）

LP 745 例最大 12 行、2053 列、69 主元、1374 存储整数位。累计 C++ 27.146455s / Python 5.979633s，约 4.540 倍；C++ 默认精确冷启动、Python 有浮点候选加精确核验，不能据此宣称同算法性能退化。
下表每个查询状态仅一次冷调用，非新进程冷启动；不含输入解码及 DLL 启动。一阶两侧都预装配接触集。C++ 含 ABI/ctypes/JSON 解码；Python 总列含 query+dataclass/JSON，核列仅生产函数。机器并行负载未控制，无统计加速比或工程基准结论。

| 来源 | 族 | 数量 | C++总秒 | Python查询+JSON秒 | Python核秒 |
|---|---|---:|---:|---:|---:|
| T1b_frozen_projection | assembly | 36 | 0.783536 | 0.926826 | 0.885369 |
| T1b_frozen_projection | first_order | 36 | 50.667509 | 97.931634 | 97.884772 |
| exact_transform | assembly | 36 | 0.046950 | 0.080219 | 0.072095 |
| exact_transform | first_order | 36 | 0.037417 | 0.070695 | 0.067236 |
| exact_transform | lock | 54 | 0.110226 | 0.147085 | 0.124329 |
| tia2d-2_formal | assembly | 114 | 3.961465 | 4.307853 | 4.162018 |
| tia2d-2_formal | first_order | 114 | 16.170277 | 25.513439 | 25.435759 |
| tia2d-2_formal | lock | 350 | 15.015477 | 23.076034 | 19.828864 |

逐查询数值见 [diff_repair.json](file:///D:/eab-evidence/reports/codex/C3L1_evidence/diff_repair.json)；分组/中位/最大见 [p2_repair.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/p2_repair.json) 与 [p2_repair.md](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/p2_repair.md)；LP/C1 补充 [p2_extra_repair.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/p2_extra_repair.json)。

### C1 旧“约慢 1.5 倍”的解释与改进方向

旧数值来自 [C1E §6](file:///D:/eab-wt/cx-c0/reports/codex/C1E_report.md) 的 20×40 合成 55 邻接：C++ 全局导出中位5.796427s，Python E+subdivision中位3.833166s，约1.51倍。不是正式605块对或本次L1计时。
**可确认的口径差异**：C++ 导出含更完整来源/covers/JSON及 Python 解析，旧合成 Python 只到 E+subdivision；因此这不是等工作量内核比。C1 精确路径的大量排布拆段、约分与重复规范化/序列化，以及保守位长检查是从代码可见的成本来源，但本单未作分阶段 profiler，不能声称已经定量归因。
本次657例的 C++ 构造累计2.290900s、导出33.223696s，Python对应裁判43.022949s；与旧合成规模/口径不同，不推导“已解决1.5倍”。
后续可先分阶段剖析并对齐同一输出口径，再评估不可变拓扑/规范键缓存、减少有理临时量与重复 gcd、预留容器、流式 JSON、隔离诊断导出；本单未实现这些优化，不引入浮点过滤或削弱精确证书。

## 8. 原轮验证原始末行（历史快照）

### 开工全档四分片

```text
3735 passed in 912.24s (0:15:12)
3735 passed in 793.19s (0:13:13)
3734 passed in 1251.75s (0:20:51)
3734 passed in 719.74s (0:11:59)
exact construction AST gate: 0 violation(s)
```

### 收尾快档

```text
8944 passed in 329.06s (0:05:29)
```

### 收尾全档四分片

```text
3757 passed in 1484.14s (0:24:44)
3757 passed in 772.33s (0:12:52)
3757 passed in 1090.35s (0:18:10)
3757 passed in 987.53s (0:16:27)
exact construction AST gate: 0 violation(s)
```

各次 `export_changed=[] / live_tree_changed=[]`；`fresh_git_checkout=false`。模块覆盖和四分片明细分别见 [summary.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/baseline_full/summary.json)、[summary.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_repair_fast/summary.json)、[summary.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_repair_full/summary.json)。
本轮快档实际耗时按上述原始末行披露；“约5分钟”是成本目标，未为追求时间删测试或放宽门槛，不把单次墙钟当隔离性能基准。
原始逐分片日志无损 gzip 与未压缩哈希见 [raw_log_archive.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/raw_log_archive.json)。静态构造零诊断不等于数值全域证明；纯度/大文件/来源门包含在 Python 全档，未扩准入。

### 最终 C++ 构建 / 单测

```text
EAB2_NUMERIC_TESTS checks=558 failed=0
FP_ENVIRONMENT: FTZ=reject DAZ=reject ROUND_MODES=3_reject MASK_BITS_7_12=6_reject HOST_STATE=unchanged
ABI_TESTS: 764 assertions, 0 failures
C_HEADER_PRODUCTION_DLL checks=31 failures=0
C_HEADER_STATIC checks=31 failures=0
EAB2_GEOMETRY2_TESTS checks=700 failed=0
EAB2_LOCAL_TESTS checks=233 failed=0
EAB2_OPT_TESTS checks=5894 failed=0
EAB2_L1_TESTS checks=8144 failed=0
EAB2_C3L1_ABI checks=134 failed=0
100% tests passed, 0 tests failed out of 9

Total Test time (real) =   0.49 sec
EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS
EAB2_DELIVERY_AUDIT status=PASS findings=0 vendor_files=71 compiler_commands=18
```

[构建原始日志](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_repair_build.log)；[构建源码与 DLL 哈希](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/build_repair.json)；[closeout_repair_ctest.log](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_repair_ctest.log)；[delivery_audit_repair.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/delivery_audit_repair.json)。
最终测试 DLL SHA-256 `52feb6f87150ef49bcc31ffafb0d36bfd7f238f3aa0d0d17e83e9fa81e0be9e1`；编译产物仅在忽略目录，不入库。

### 失败记录与最小修复

1. 初次 L1 回归：误用 `merge_convex=true`，7具名例的13个锁定查询胞/弧/半径不一致。以 Python 为裁判改回 false；不放宽比较，补内部变异与锁定胞结构语义门。[失败记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/diff_regressions.json) / [修复后记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/diff_regressions_fixed.json)。
2. 初次收尾快档：新增37夹具未进入总PROVENANCE，`1 failed, 8906 passed in 282.86s (0:04:42)`；非数学失败。只追加真实数据来源/哈希，原条目逐字节可还原，定向 `428 passed in 0.41s`，再全快档重跑；该失败快档后没有接着运行全档。后来启动的 final_full 因 capacity 中断、无最终 summary，已整次作废；本轮 closeout_repair_full 从零执行。[失败快档](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/final_fast/summary.json) / [provenance_targeted.log](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/provenance_targeted.log)。
3. 一次直接 CMake 调用未初始化 MSVC 环境而缺 stdint.h，按环境错误改用原固定 build_eab2.bat；另一次新增 ABI 测试误用大写 OPTIMAL，修正测试对既有小写 JSON 状态的预期。均不修改 Python 数学合同。
4. 首轮完整续单全档 `closeout_restart_full` 实际完成但 RED：新增测试的 `float(x)` 命中1个冻结静态站点，两个守护测试各失败1项，独立AST末行 `exact construction AST gate: 1 violation(s)`。仅把该测试改为已受审 `scalar_rational(x)`，仍用 Fraction 回环的精确相等断言；没有放宽断言、改数据或新增准入，src/eab/C++数学源码未变。定向20项与全仓静态门先绿，再将C++、三族差分、快档及四分片全档全部重跑到本轮 closeout_repair；不用上一轮任一成功分片补拼。修复及不增准入证明见 [static_repair.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/static_repair.json)，定向记录 [static_repair_preflight.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/static_repair_preflight.json)，失败全档 [summary.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_restart_full/summary.json)。
5. 早期变异临时目录及个别 PowerShell UTF-16 日志已整理；变异在规定 tmp 根重跑，日志只转编码且末行不变；未把旧失败证据删掉或改为成功。

## 9. 复跑命令与差异清单

先设置环境，所有输出用新名字；不对既有证据覆盖，不执行 Git 写操作：

```powershell
$env:TEMP = "$PWD/reports/codex/C3L1_evidence/tmp"
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
cmd /c eab2\build_eab2.bat
& "C:/Program Files/Microsoft Visual Studio/2022/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe" --test-dir eab2/build --output-on-failure
python tools/eab2_opt_diff.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C3L1_evidence/tmp/opt_recheck.json --source-commit BASELINE_PLUS_UNCOMMITTED
python tools/eab2_c3l1_diff.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C3L1_evidence/tmp/l1_recheck.json
python tools/eab2_diff_c1.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C3L1_evidence/tmp/c1_recheck.json --metamorphic --source-commit BASELINE_PLUS_UNCOMMITTED
python tools/h1_run_gates.py --name owner_fast_NEW --evidence-root reports/codex/C3L1_evidence
python tools/h1_run_gates.py --name owner_full_NEW --runslow --evidence-root reports/codex/C3L1_evidence
```

`--source-commit` 仅来源标签，复跑时应填写实际基线与未提交状态，不能把本轮基线当新代码产生提交；以源码/DLL SHA-256 为准。实际 CTest 绝对路径和命令保存在 [ctest_repair.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/ctest_repair.json)。复跑仍需本地既有 MSVC/CMake/Boost/Python环境，不触发安装或下载。

| 项目 | 本单处理 / 边界 |
|---|---|
| 与设计数学冲突 | 本单未发现必须停工的新冲突；以 Python 裁判修正 C++ 合并胞缺陷 |
| 已批准设计外项 | dof_anchor、平坦内部顶点、profile1 冗余 VV 沿 T1a |
| LP 浮点候选 | 默认未实现候选生成加速；可选候选精确重建，纯有理结果符合合同 |
| 非唯一证书 | 495 严格字段差异公开，不强行追随 Python 基序；数学等式独立验证通过，供 Claude 验收审查 |
| 工作 ABI | C3-L1 增量非整个 C3 稳定发布；opt 仅测试入口，L3 LP2 未宣称实现 |
| P2 归因 | 有口径分析与代码级成本假设，无因果 profiler 或性能门 |
| 新鲜树/独立核查 | 工单禁止 Git 写，未自行建树；没有冒称独立核查通过 |

## 10. 容量中断续单的历史收尾状态

旧 `final_full` 容量中断作废，见 [closeout_restart_invalidation.json](file:///D:/eab-evidence/reports/codex/C3L1_evidence/closeout_restart_invalidation.json)；随后 `closeout_restart_full` 完整运行但静态门失败，亦不计入通过验收，见 [closeout_repair_invalidation.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_repair_invalidation.json)。原日志均保留。本轮仅使用修复后独立完整重跑的记录。本轮固定源码后，C++ 增量构建/全部单测、CTest、LP/L1/C1全部差分、Python快档和全档四分片均独立从头重跑；不是清洁克隆或清洁重编。阶段顺序、原始末行、耗时、逐阶段源码前后相等及无拼接声明见 [closeout_repair_run.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/closeout_repair_run.json)。
本轮统一源码清单 [closeout_repair_source_manifest.json](file:///D:/eab-evidence/reports/codex/C3L1_evidence/closeout_repair_source_manifest.json)；全部差分 DLL 哈希与最终构建一致。本轮只修复一个新增测试的构造边界调用；未改数学源码，未 commit 或执行任何 Git 写操作。

## 11. 收尾状态（Claude 验收返修，本次当前结果）

### 11.1 验收输入、返修与复现边界

- 起点为干净的 `eab2-c3 @ 84d514ebd7e820a6ea7e5f58f4113d8e2bd32e24`；未 commit / push / reset / checkout / stash / branch / worktree，未安装下载，未结束非自己启动的进程。回退锚是该提交及逐文件归档原字节，不自动覆盖恢复。
- Claude 两路非作者报告原文已保存：[完整验收报告](file:///D:/eab-evidence/reports/codex/C3L1_evidence/acceptance_review/C3L1_acceptance.md)；[来源SHA与工单合同](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/intake.json)。原报告 0 critical / 0 major，已审查并认可495项非唯一证书；有限测试不等于全输入域证明。
- **M1 计算预算**：每项 evaluate 建立 `IntegerLimitScope(state->limits.max_integer_bits)`，并专门捕获 ResourceLimit 映射逐项 RESOURCE_LIMIT；批次仍 OK、失败不改bits、相邻合法项正常、异常作用域复位。原生 `numeric_compute_budget_matrix` 先红后绿，ABI断言由764增至776。
- 原对手 NORM 脚本逐字节复制到获准归档后重跑，未写用户Temp：k=250合法；k=500/1000/2000/4000/65536全部逐项RESOURCE_LIMIT。k=65536本轮 API **0.161 s**、自启动子进程墙钟 **0.327 s**；每个自启动子进程60s上限，均未超时。此为位长限额响应，不声称任意算法统一墙钟/内存上界。[原始对手结果](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/numeric_budget_adversarial.json)。
- **L1 m1**：工具从原始多边形CCW标签边重建法向，从实际 dof_mask / dof_anchor 重建作用反作用与转动列，从局部环重建VV forbidden facets，再构造 normalized LP、VV H/rhs、zero-cone Gᵀλ=±e_k后核证；不信 C++ 导出矩阵，也不调用 C++ helper。接触约束集合仍由 Python 裁判确定。新增7项回归包含非原点非对称anchor与mask，及在生产行/法向/切向构造内部注入自洽错误，连期望/实际两边同时错误仍拒绝。
- m1定向末行 `27 passed in 0.78s`，正式冻结114个assembly和114个first_order证书轻量回读0失配。首次定向出现公开无序constraints与证书构造序混淆，仅修工具排序契约后通过；未留存该次原始控制台日志，不能冒称有原始日志。返修定向与归档证明见 [preflight_summary.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/preflight_summary.json)、[preflight_archive.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/preflight_archive.json)。
- **M4**：build_eab2.bat 的 TEMP/TMP 改为 `eab2/build/tmp/`；README复跑输出在该被忽略中性目录，不再污染已提交里程碑证据。本轮H1的TEMP/basetemp仍在规定C3L1 ignored tmp。
- **M5 / L1 m3**：ABI明确同一context调用被串行化、result/context销毁使data指针失效；借用data读取须与销毁自行协调。C1 local_origin默认合并胞，不能代替query_lock的未合并胞/严格半径证书。
- **L1 m2 选择**：未增加 `/Brepro`；明确DLL字节不承诺跨树复现。复现以受测源码SHA、实际编译器/选项和语义门为锚；本树DLL SHA只标识该次受测产物。[源码与本次DLL哈希](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/build_acceptance.json)。
- 未改 `src/eab`、设计SHA、静态准入、fixtures数据或既有数学合同；无新增设计偏离。L3/L4、浮点候选生成加速和性能优化仍为原非目标。

### 11.2 证据归档与净增

旧219文件按验收清单处理：81个小摘要留仓；136个原文件（11,949,974 B）外移；fixture_formal_replay两文件gzip−9、mtime=0；10份报告/索引另保存改写前原字节。旧三个repair差分外存，新差分各只留一份权威gzip；过期测试副本已外移。复制→目标SHA/字节核验→再核源→单文件unlink，无递归删除或不等字节覆写。
[旧逐文件映射/SHA](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/archive_manifest.json)；[220原文件独立归档审计](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/archive_initial_audit.json)；[本轮最终日志/执行集/双SHA压缩映射](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/final_archive.json)；[归档台账](file:///D:/eab-wt/cx-c0/reports/EVIDENCE_ARCHIVE.md)。所有大日志、H1原执行记录和执行/包装脚本在获准C3L1外目录，相对7540cde的拟交付逻辑字节净增不足 **1.75 MB**（目标2 MB内），精确字节及单文件卫生最终值见 [hygiene.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/hygiene.json)。工作字节瘦身不消除旧提交blob，本代理未重写Git历史；外归档是本地副本而非远端备份。

### 11.3 固定字节完整重跑与原始末行

先运行CMake声明产物的clean目标，再完整build（不是仅用旧DLL），随后CTest、审计、C0、NORM预算、LP、L1、C1、P2摘要、Python快档、全档四分片；12阶段顺序完成。所有阶段源码前后相等，不重用/拼接旧运行。[完整逐阶段流水账](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/acceptance_final_run.json)；受测字节清单 [source_manifest.json.gz](file:///D:/eab-evidence/reports/codex/C3L1_evidence/acceptance_runs/acceptance_full/source_manifest.json.gz)。

```text
EAB2_NUMERIC_TESTS checks=558 failed=0
FP_ENVIRONMENT: FTZ=reject DAZ=reject ROUND_MODES=3_reject MASK_BITS_7_12=6_reject HOST_STATE=unchanged
ABI_TESTS: 776 assertions, 0 failures
C_HEADER_PRODUCTION_DLL checks=31 failures=0
C_HEADER_STATIC checks=31 failures=0
EAB2_GEOMETRY2_TESTS checks=700 failed=0
EAB2_LOCAL_TESTS checks=233 failed=0
EAB2_OPT_TESTS checks=5894 failed=0
EAB2_L1_TESTS checks=8144 failed=0
EAB2_C3L1_ABI checks=134 failed=0
9/9 Test #9: c3l1_abi_dll .....................   Passed    0.01 sec

100% tests passed, 0 tests failed out of 9

Total Test time (real) =   0.49 sec
EAB2_DELIVERY_AUDIT status=PASS findings=0 vendor_files=71 compiler_commands=18
EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS
NUMERIC_COMPUTE_BUDGET adversarial=6 k65536=RESOURCE_LIMIT status=PASS
OPT_DIFF selected=745 completed=745 mismatches=0
C3L1_DIFF assembly=186 first_order=186 lock=404 mismatch=0 strict_fields=495
C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086
```

Python快档原始末行：
```text
8951 passed in 332.80s (0:05:32)
```

Python全档四分片及独立静态门原始末行：
```text
3759 passed in 816.94s (0:13:36)
3759 passed in 1081.65s (0:18:01)
3759 passed in 964.39s (0:16:04)
3758 passed in 1540.07s (0:25:40)
exact construction AST gate: 0 violation(s)
```

快档8951、全档15035（原轮各新增7个回归节点），0 failed / 0 skipped；执行多重集、模块实际执行完整；export_changed / live_tree_changed 均空。[快档summary](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fast/summary.json)；[全档summary](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_full/summary.json)。这次H1 fresh_git_checkout=false，明确是返修字节导出；不混同Claude提供的84d514e原轮新鲜树。

当前权威差分：[C0 4483样本](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/numeric_diff_acceptance.json)；[C1 657对](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/c1_diff_acceptance.json.gz)；[LP 745例](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/opt_diff_acceptance.json.gz)；[L1 776查询](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/diff_acceptance.json.gz)。L1 assembly=186 / first_order=186 / lock=404；0语义失配，495非唯一证书字段差异完整保留且在几何重建矩阵上核验，六个具名回归27查询仍严格差异0。
本轮仅计时报告不设门：[p2_acceptance.md](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/p2_acceptance.md) / [p2_acceptance.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/p2_acceptance.json)；§7是旧轮历史时序，未假称与当前测量等同，未重算冻结数据。

### 11.4 退出

验收要求M1–M5与L1 m1–m3均已处置；完整收尾门通过，无本单待办。Claude原轮新鲜树与独立核查的来源边界如上，未冒称返修后又获独立签字。交付仅本地未提交工作字节，等待所有者合入操作；这不是功能/验证未完成项。

C3L1_DONE
