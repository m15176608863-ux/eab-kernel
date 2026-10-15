# INT1 静态约定、仪器卫生与语义门

## 结论

- 合并基线的静态扫描本来就是 0 违例；冲突是 pytest 中的历史行不可变约定，不能误称为初始 AST 扫描红。
- 恢复 3bf5e95 的 3103 条旧行。23 条 M3 原地改写改为「旧行 + 续审退休 + INT1-C 新行」。M5a/M5a2 的 287 条行全部保持原值。
- M3b 新增 39 条按 6c014f5 已验收快照冻结。共同基线没有这些行，因此不回滚为本线已被取代的中间实现。包括 M3c 曾原地续签的 4 条：不声称它们在本线历史上从未改变，此后统一采用不可变与追加续审。
- 旧重复仪器准入 46 条只退休、不删除，合并成一个准确钉住源码和作用域的测试仪器审查。
- 修复行尾前的完整历史静态门：`exact construction AST gate: 0 violation(s)`，耗时 136.929 s。该记录证明当时的源码字节，不直接证明后来的 CRLF 字节。
- 修复行尾前的完整历史定向组合：`229 passed in 8.82s`；当时独立 R3 复核：`76 passed in 3.25s`，0 critical、0 major。原日志和原 `source_hashes` 均保留，不以换哈希冒充重跑。

## 行尾恢复与最终字节的重验证

最终字节审查发现 `tests/test_m5a2_static_runner.py` 在编辑时从原有 CRLF 变成 LF。root 已恢复原 CRLF；[行尾修复记录](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/line_ending_repair.json) 确认 AST 相同、235 处 CRLF、生产重算依赖未变。即使 AST 相同，旧字节上的全绿也不冒充最终字节证据。

旧的 `final_suite_r1_postreboot` 全套完整结果已经被标为 superseded。最终有效字节由新的 R3 实测记录 `review_static_eol_r1`（76 passed in 3.27s，全部独立探针通过）及从头完整执行的 [final_suite_r2_postreboot](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/final_suite_r2_postreboot/) 证明：13,558 项全部通过，收集＝执行、0 skip、静态 0 违例，两份记录均已完整完成。`static_work.json` 的 `line_ending_revalidation` 保存完成状态和证据哈希，原 `source_hashes`、旧静态结果与旧定向结果保持为历史证据，不以哈希替换冒充重跑。

## 计数口径

| 指标 | 变更前 | 变更后 |
|---|---:|---:|
| 历史 waiver 档案总数 | 3429 | 3452 |
| 当前作用域有效的逐站准入 | 3406 | 3360 |
| 另计统一仪器审查 | 0 | 1 |
| 当前有效准入含仪器审查 | 3406 | 3361 |

历史增加 23 条完全来自用户要求的约定转换，不是新增无关豁免；有效准入净减 45。退休的 46 条包括 M5A2_LOCAL_REVIEW 27 条和 STRUCTURAL_DATA_OR_PROTOCOL_REVIEW 19 条。旧行保持不变优先于物理删除历史准入，因此不能用档案总行数衡量当前授权规模。

### 当前有效类别分布

| 类别 | 变更前 | 变更后 |
|---|---:|---:|
| APPROXIMATE_OR_NOMINAL_SCOPE_EXCLUSION | 422 | 422 |
| INPUT_MODEL_OR_OUTPUT_BOUNDARY | 620 | 620 |
| LOCAL_NUMERIC_OR_PROTOCOL_REVIEW | 214 | 214 |
| M5A2_LOCAL_REVIEW | 170 | 143 |
| M5A_CLOSED_FORM_TEST_REVIEW | 5 | 5 |
| M5A_DISCRETE_SET_REVIEW | 2 | 2 |
| M5A_EXACT_RATIONAL_REVIEW | 29 | 29 |
| M5A_EXACT_RECORD_REVIEW | 2 | 2 |
| M5A_FINAL_DISPLAY_REVIEW | 17 | 17 |
| M5A_FROZEN_COMPARISON_REVIEW | 2 | 2 |
| M5A_FROZEN_INITIALIZATION | 14 | 14 |
| M5A_INDEPENDENT_ORACLE_REVIEW | 23 | 23 |
| PROOF_GAP_MANUAL_EXCLUSION | 640 | 640 |
| PUBLIC_DIAGNOSTIC_CALLBACK | 5 | 5 |
| R13_EXPLICIT_APPROXIMATE_INPUT_OR_DIAGNOSTIC | 98 | 98 |
| R13_LOCAL_STRUCTURAL_OR_ANALYZER_PROOF_GAP | 10 | 10 |
| RUNTIME_TEST_ORACLE_REVIEW | 498 | 498 |
| STRUCTURAL_DATA_OR_PROTOCOL_REVIEW | 299 | 280 |
| TEST_EXECUTION_OR_INTENTIONAL_DEFECT | 320 | 320 |
| UNFINISHED_NUMERICAL_DYNAMIC_REWRITE | 16 | 16 |
| TEST_ONLY_SOURCE_MUTATION_PROTOCOL（单独审查） | 0 | 1 |

## 一次仪器审查的准确证明域

中央 `tests/mutation_support.py` 只执行：读取显式函数体、唯一字面替换、复制模块 namespace、编译真实变异、返回 callable 或安装 monkeypatch。不写生产文件，也不制造后置假输出。审查钉住中央 helper 整文件 SHA256，并钉住以下 9 个作用域的源码 context。

- `tests/mutation_support.py::<module>`
- `tests/mutation_support.py::mutated_function`
- `tests/mutation_support.py::mutated_callable`
- `tests/mutation_support.py::replace_module_callable`
- `tests/test_m5a2_exact.py::exact_mutation`
- `tests/test_m3b_construction3d.py::_mutate`
- `tests/test_int1_semantics.py::semantic_guard`
- `tests/test_int1_semantics.py::mask_source_hashes`
- `tests/test_int1_semantics.py::inject_semantic_mutation`

作用域之外不因函数名或测试路径获准。闭子集调用、属性、反射等规则可以在这些精确已审代码上消解；算术、舍入来源、直接 float、代数比较器站点规则均不消解。`closed-syntax` 仅对应已钉住 mask_source_hashes 的 4 个字面 hash-disable lambda，不能外延到数值 oracle。独立审查检验了源 scope 变化、未知 helper/oracle、helper 任意字节变化时准入失效，以及 8 类数值规则不可豁免。

## 高阶比较器与 watchdog 牙齿

- 共 18 个高阶源程序，每个在普通路径与 test-driver 路径检查，共 36 格；另有 18 个 checker 内部规则失效变异，必须红在指定 `higher-order comparator dispatch` 语义断言，不靠源码哈希。
- 覆盖 self 方法、map、getattr、变量或字符串拼接属性名、getattr 别名、__dict__/globals/vars 下标、operator.attrgetter 及导入别名、工厂返回、装饰器、直接或间接或别名基类覆写 compare。
- R3 曾找到 10 个实际绕过，均保留原始复现程序并补进 pytest；复核 10 × 2 路径均命中 `algebraic-comparator-site`。这是有限 AST/别名域的辅助拒绝规则，不是任意 Python 反射的完备证明。
- watchdog 先证明 teardown 内 0.7 s 阻塞被 0.25 s timer 终止；再把真实 PLUGIN 的取消 hook 从 logfinish 错移到 teardown 开始，结果子进程完整退出 0，从而原「teardown 仍受 watchdog」断言必红。变异不是伪造 timeout 记录，也不使用永不结束的外部进程。

## 卫生剩余的精确边界

本单 M3/M5 涉及的重复编译已集中，当前有效准入净减；没有声称全库历史脚手架都已重构。历史迁移在技术上可做，但本次没有实施：这不是环境阻塞，也不应因数量较多而称为不可做。用户要求全库集中，因此总报告必须将该部分明确列为未完成。

全库 exec AST 调用由 150 减到 146，其中 1 个为中央 helper。其余 145 个分为：

- 19 个历史独立变异 helper，仍承载 249 条当前有效逐站准入，属于真正可进一步集中但本单未完成的遗留。
- 112 个 test-driver 或其嵌套变异编译点，当前逐站准入为 0，属于原框架的测试驱动豁免。它们仍有代码重复，但不是新增准入膨胀。
- 13 个故意动态程序或静态门自身运行案例，及 1 个用于 AST 提取展示函数的 builder。它们不是可机械删除的变异脚手架，不计为迁移未完成项。

### 仍有有效准入的真实历史变异 helper

| 路径和函数 | 有效准入 |
|---|---:|
| `tests/test_g2_bdda3d.py::_mutant_g2` | 10 |
| `tests/test_limit_multi.py::_mutant_module` | 12 |
| `tests/test_perf_contact_window.py::_mutant` | 6 |
| `tests/test_r11fix_static_flow.py::_mutant_scan` | 6 |
| `tests/test_r13fixb_dual_margin.py::_internal_mutant` | 16 |
| `tests/test_r13fixb_kernel_numeric.py::_install_internal_expression_fault` | 14 |
| `tests/test_r13fixb_readers_oracles.py::_mutate` | 20 |
| `tests/test_r14_dual.py::_mutated_function` | 13 |
| `tests/test_r14_readers.py::_internal_mutant` | 11 |
| `tests/test_r15fix_geometry.py::_mutate` | 15 |
| `tests/test_r15fix_numeric_decode.py::_internal_mutant` | 11 |
| `tests/test_r6fix_dual_lp.py::_mutant_function` | 12 |
| `tests/test_r7fix_geom3.py::_inject` | 16 |
| `tests/test_r8fix_gate_teeth.py::convex_view_mutant` | 13 |
| `tests/test_r8fix_gate_teeth.py::reject_z_inside_cone_filter` | 13 |
| `tests/test_r8fix_gate_teeth.py::all_branch_convex_view_mutant` | 17 |
| `tests/test_r8fix_margin_gap_gate.py::_arithmetic_fault_inside_margin_contacts` | 13 |
| `tests/test_r9fix_g03_construction.py::_bad_witness_report` | 14 |
| `tests/test_tf_reader.py::_mutant_reader` | 17 |

以上保留源文件与准入细目在 `static_work.json`，没有为了赶绿把其整文件或整函数自动豁免。本执行者此后只修订交付证据；root 在字节审查中所作的 CRLF 恢复已单独记录，并触发新的 R3 与完整四片重跑，不能沿用旧字节的全绿作为最终证明。

## 证据文件

- `static_work.json`：完整类别和规则分布、旧新仪器库存、23 条转换行、46 条退休行、9 个 scope 的审查域、源码哈希。
- `static_postreboot_state.json` 和 `static_postreboot.txt`：重启后完整静态门，未拼接旧日志。
- `static_ready.txt`：定向 229 个测试的最后行。
- `review_static.json`：另一执行者的 R3 复核。
- `review_semantic.json` 和 `review_semantic.md`：本执行者对 13 个新数值、轨迹及统计变异的独立 R4 复核，全部在指定语义断言处报红。

静态与准入约定部分完成；全库历史仪器集中仍有上述精确遗留，须在总报告中披露。
