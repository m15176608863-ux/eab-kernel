# C3-L4 当前接口与实现参数对账（64b499f）

日期：2026-10-24；范围：WO-C3L4-fix-close 续单，只读核查生产源码并修正文档。当前 HEAD 为 `64b499f8bf2d5e889d0ac0c65a3eab37ef743629`；未改 `src/eab`、`eab2/src`、`eab2/include` 或设计正本。以下“相符”指源码与文字对账，不等于本记录亲自执行对应运行门。

## 搜索预算与诊断

| 项目 | 当前实现 / 源码位置 | 文档对账 |
|---|---|---|
| 候选上限 | 每方向至多 64 个不同有理斜率；Python `src/eab/kernel2d/branch_certificate.py:17,374-408`；C++ `eab2/src/branch.cpp:287-289` | 相符；不宣称候选完备 |
| 重试基数 | `RETRY_LIMIT=6`；Python `:18,454-469`；C++ `:673-695`；基须再核 K 与记录 probe | 相符；基选择不代替证明 |
| 筛选探测 | 固定 ε=`2^-24`、η=`2^-8`；Python `:20,427-433`；C++ `:526-543` | 下端可为原问题不可行而具有齐次对偶见证；仍须完整 K 认证 |
| 提升探测网格 | ε∈`{2^-8,2^-16,2^-24,2^-32}`，η∈`{2^-4,2^-8,2^-12,2^-16}`，每候选至多 16 对，另有筛选一对；Python `:22-23,434-440`；C++ `:545-547` | 相符；不按种子幅值缩放，不以次数上限冒充墙钟或内存上限 |
| 探测几何阈值候选 | 仅固定 ε=`2^-24`，56 次二分；Python `:21,342-370,513-519`；C++ `:454-474`；仅内部阈值且顶点派生候选耗尽后追加一次 | 相符；探测候选仍不构成导数认证 |
| 齐次对偶见证 | 原问题 INFEASIBLE 时解 `max cᵀx, Ax=0, x≥0`，取其精确对偶；Python `:283-296`；C++ `probe_dual` | 相符 |
| 定向顶点 | Python `_negative_components` / `_probe_targeted`（`:298-333,470-494`）；C++ `:593-657`；在筛选点最大化失败分量，每次 point/ray 调用最多 8 个 | 仅产生候选基，仍核 K 与当前探测点；不是完整性证明 |
| 探测一致性 | Python `_probe_consistent`（`:243`）由 `_vector`（`:178`）调用；C++ 复用路径 `probe_primal_ok` / `probe_dual_ok`（`:659-695`） | 带 ε/η 的见证提升中，K 正而记录 probe 负也拒收；无探测记录的奇异候选元数据不作有限点检查 |
| 形状不变量 | Python `sensitivity.py:410-415`；C++ `branch.cpp:805-808` | 缺下端对偶/上端点/射线，转 unresolved / internal_certificate_shape |
| 生产诊断 | 两后端生产模块均无逐探测点环境变量诊断；诊断在工具层对照证书候选与探测记录 | 与设计澄清相符 |

具名语义门：`eab2/tests/test_sensitivity.cpp::branch_pure_load_jet_corpus_regression`、`branch_infeasible_lower_dual_with_load_jet`、`ordered_field_and_raw_path_guards`、`original_search_domain_boundary_certificate`。另有 `tests/test_threshold_branch.py::test_certified_direction_without_witnesses_is_never_a_value` 与 C++ `branch_face2_regression` 的 JSON 无空证书断言守护形状。定向顶点的全族能力改善等待所有者分片结果，此处不新增已证命题。它们守护各例的结果/证据语义；这里没有宣称每个预算数值都另有独立直接断言门，也没有从有限实例推出全域分支完备性。

本轮 minor 具名门：
- `tests/test_eab2_branch_verify.py`：`test_archive_caller_domain_forgery_is_rejected_by_independent_checker`、`test_certificate_archive_writer_binds_the_original_caller_request`、`test_certified_null_witness_has_explicit_need_message_not_typeerror`；工具档案从原调用请求绑定 `mu_max_binary64`，不采信返回域补值，null 见证明确拒绝。
- `tests/test_threshold_branch.py`：`test_rational_roots_repeated_zero_does_not_hide_seven_over_128`、`test_probe_threshold_candidates_uses_original_domain_not_narrowed_mu_hi`、`test_reused_basis_positive_in_k_but_negative_at_probe_is_skipped`。
- `tools/eab2_branch_probe_reuse.py::verify_reused_basis_records`：C++ 当前原片段白盒实跑、独立 Fraction 核 JSON，内部删除有限点 guard 变异被杀；不是全求解器端到端证明。实测见收尾报告。

## 测试入口与非对称差分

- `eab2/tests/test_sensitivity.cpp:285-337,634-670`：默认入口保留轻量 `branch_faces_and_independent_beams`；`--branch-sweep` 才执行两厚度、全部单面、开/闭双梁和三种权重的完整扫描。README 已区分两者；本记录未运行扫描。
- `branch_pure_load_jet_corpus_regression`（`:375-396`）已进入默认具名列表（`:656`），核两种厚度纯恒/活载种子的双侧认证零导数；“存在门”不等于本记录另行运行门。
- `tools/eab2_c3l4_asymmetric.py:147-201`：精确阈值源保留 6 个阈值通道；具有精确有限 `limit` 的源另加 `asym_limit_dead_live`，目标为 limit 而非 critical。输入接线门为 `tests/test_eab2_c3l4_asymmetric.py::test_asymmetric_case_preparation_does_not_claim_a_referee_or_certified_slope`（`:67-89`）。
- `tools/eab2_c3l4_diff.py:469-477`：证明能力 floor 的 `ValueError` 转为当前查询的 `proof_capability_floor` 差异与 exception 记录，不整例中止；数值或认证能力退化仍是 mismatch，不放宽比较合同。

## ABI 与历史证据边界

- `eab2/ABI_CONTRACT.md` 冻结 JSON 实读计数为 **31 导出、28 结构、64 整数常量、31 返回类型**。生产能力位 **581501**，其中 `EAB2_CAP_SENSITIVITY2=524288`；`eab2/src/c_api.cpp:105-113` 与公共头对应，测试能力仅在测试构建追加。
- `eab2/include/eab2/c_api.h` 当前 SHA-256：`e6419195dd20800004a1452e5fc1efc6fa1079e6cef28701f395f2048476d3e4`。ABI 具名门为 `tests/test_eab2_release_abi.py::test_release_frozen_contract_matches_public_header_and_all_struct_fields`；本次只读复核现有顶层 DLL 实测 `EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0`，见 [JSON](close_release_abi.json)；不声称该 DLL 与新鲜树字节相同。
- 设计正本 `docs/eab2_design.md` 实读 SHA-256：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`，未改。`eab2/ABI_CONTRACT.md` 补形状失败诊断及工具档案请求绑定文字；冻结机器表保持原字节。
- [abi_minor_results.md](abi_minor_results.md) 保留历史原文及 47691cc 尾节，另加本轮索引；[EVIDENCE_ARCHIVE.md](../../EVIDENCE_ARCHIVE.md) 的历史归档、SHA 与验收边界不改写。本记录未改外部归档，也不访问或改动所有者新鲜树。
- 运行证据与最终接受决定见 [收尾报告](../C3L4_fix_close_report.md) / [修复轮报告](../C3L4_fix_report.md)；所有者新鲜树与非作者核查仍由 Claude 负责，不能由本次静态对账代替。
