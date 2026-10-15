# M5c A1–A4 语义补牙证据

## 结果与边界

- 完成 A1–A4：四类 R2 结构条件、r2、R1 L1 范数与 P1/P2 双盒、误差式各项、严格等号、近阈值、真实 oracle 核对。
- 收集 = 执行 = 49，0 skip；新内部变异 22 项全部由具名语义断言捕获。
- 变异执行未选任何源码哈希/冻结摘要测试（`hash_guards_selected=false`），没有在输出之后伪造数据。
- 全部生产算法保持不变。新增 oracle 仅导入 `fractions.Fraction`，不共享生产几何、求根、区间原语。
- 近阈值接受格端点余量/误差为 `1/199999`（约 5.000025e-6）。标签与括区均由独立平移事件 oracle 检查。
- 大平移及单位格新增 3 格 L1 对偶范数门；既有 R2 有理旋转/大平移/极端单位元门一并运行。
- 早期回返格确实签错首盖：正确 VE(3,0) 在 17/40，错误候选 VE(2,3) 在 3/5；独立闭式点为 (33/32,-2)。EV 删除格也确实签错首盖（正确 EV=.3，错误 VE=.5）。
- 严格凸性与竞争者等号格检查的是充分证书契约；保守界等号不必意味着真实凸性丢失或真实首盖改变。
- 误差删项门以独立展开值检查预算本身，而不是把任何预算降低都冒称找到了真实轨迹反例。

## 变异表

| 真实内部变异 | 结果 |
|---|---|
| `test_internal_structural_mutations_die_on_named_semantics[early_skip]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[early_half]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[omit_ev]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[omit_projection_g]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[omit_projection_h]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[omit_last_panel]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[competitor_nonstrict]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[convexity_nonstrict]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[norm_linf]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[omit_r2]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[p1_box_only]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[wrong_return_label]` | 语义 kill |
| `test_internal_structural_mutations_die_on_named_semantics[wrong_return_bracket]` | 语义 kill |
| `test_internal_event_error_term_deletion_dies_on_budget_semantics[w-0]` | 语义 kill |
| `test_internal_event_error_term_deletion_dies_on_budget_semantics[w-1]` | 语义 kill |
| `test_internal_event_error_term_deletion_dies_on_budget_semantics[w-2]` | 语义 kill |
| `test_internal_event_error_term_deletion_dies_on_budget_semantics[v-0]` | 语义 kill |
| `test_internal_event_error_term_deletion_dies_on_budget_semantics[v-1]` | 语义 kill |
| `test_internal_event_error_term_deletion_dies_on_budget_semantics[v-2]` | 语义 kill |
| `test_internal_convexity_error_term_deletion_dies_on_semantics[2*radius*_length1(u)+8*radius*radius]` | 语义 kill |
| `test_internal_convexity_error_term_deletion_dies_on_semantics[2*radius*_length1(v)+8*radius*radius]` | 语义 kill |
| `test_internal_convexity_error_term_deletion_dies_on_semantics[2*radius*(_length1(u)+_length1(v))]` | 语义 kill |

## 重跑

`python tools/m5c_mutation_evidence.py`。脚本显式配置本树 TEMP/TMP、`-p no:cacheprovider`、`--basetemp`。
完整 pytest 输出见同目录 `semantic_teeth_pytest.txt`；细目与当前源码哈希见 `semantic_teeth.json`。
先行证明与反例边界见 `docs/m5c_teeth_theory.md`；源码见 `tests/test_m5c_robustness.py` 与 `tests/m5c_teeth_oracle.py`。
