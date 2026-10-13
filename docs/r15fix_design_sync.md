# R15FIX：精确量汇总与显示边界补齐

2026-10-13。对应 G6O-O01～O05（0 critical / 3 major / 2 minor）；实现与证据留在本工作树，待独立复审。
本文同步本树设计合同，优先订正 R14 文本中与下列内容不一致的表述。
外部设计正本 `D:/E(A, B)/07 程序设计·统一接触内核方案.md` 按工单只读，**未回写**。
M0 所有者退出决定、M4a 离线影子边界保持不变；不宣称新鲜 worktree 或独立 G6 通过。

## 1. 合力是完整精确汇总的最终显示

`limit_load` / `limit_load_multi` 对每列先计算精确 `lambda * Fraction(direction)`，再按接触、分量从 `Fraction(0)` 累加。
只有完成全部选中列的和后，才用 `scalar_rational(..., quantity="contact force")` 构造普通 float。
不允许先构造列力、从 float 零开始累加，或以未经检查且无证书的 float 转换把非零最终合力变为零。
返回 `exact_contact_forces` 保存同一 tol 选列后的完整有理合力；`contact_force_display_underflow` 当且仅当有非零精确分量最终显示为零时为 True。
这是明确标记、保留符号的下溢显示例外：例如 -2^-1075 显示 -0.0，精确字段仍为 -2^-1075；普通零和可表达次正规数不误标。
最终上溢仍具名拒答。这样不因某个接触力显示下溢而拒绝容量仍可表达的正确 LP；完整静力证书仍为 lambdas，不能用选列后的字段替代。

选列政策仍是忽略 `|f_j| <= tol * max|f|`；非负有限 tol 时用精确平方比较落实，不构造仅用于比较的列力范数。
这样，中间相消列即使超出 binary64，仍能产生域内最终合力。`tol=0` 不得删除任何非零列。
`contact_forces` 仍是按 tol 筛选的显示量，不替代 `lambdas` 的完整静力证书；LP 模型、容量及证书求解器不改。

门：`tests/test_r15fix_force_reports.py` 中
`test_contact_force_report_rounds_complete_exact_sum`、
`test_contact_force_nonzero_final_underflow_has_explicit_exact_certificate`、
`test_contact_force_final_overflow_still_has_named_error`、
`test_contact_force_selection_boundary_and_outputs_differ`、
`test_force_selection_does_not_round_overflowing_intermediate_columns`。
预期值来自独立单接触静力/力矩方程，不调用生产几何或 LP 列生成器求答案。

## 2. 骨形工具的完整坐标与 jet

仅 `tools/osteomorphic.py` 的具名生成器使用私有有理一阶代数 `_ShapeJet`：坐标 primal 和每个导数通道完成完整表达式后分别最终舍入。
不改变全局 `Dual` 的逐操作语义，不承诺任意用户 Dual 复合表达式只舍入一次。
配对上块的 `center_z + lz` 亦保留精确中间量；sin 的局部导数先取系数，再用有理数结合原 seed、amp 及其余坐标项。
最终不可表达的非零坐标/jet 仍抛具名 `ConstructionDomainError`。

造型物理输入仍遵守已声明 D400；采样角度与 libm 系数模型不改，不声称理想曲面或超越函数全域正确舍入。
自定义 `sin_fn` 的公开 Dual 回调协议明确为收到宽度 1、seed `(1.0,)` 的 Dual，返回同宽 Dual 以报告局部一阶导数；
依赖调用方原通道宽度/seed 内容而非一般链式法则的回调不兼容此协议。
门：`tests/test_r15fix_shape.py` 的完整坐标、完整 jet、配对中心、相位 seed 极端量级及一般位置逐顶点门。

## 3. 贯入早返回的下溢证书

`margin_contacts` 的贯入 sentinel：`distance=0`、`normal=None`、精确 `margin_gap=-delta`。
delta/band 在所有早返回前经 `exact_input` 检查有限性；gap 的最终浮点显示允许下溢，**但同时附带**
`exact_distance_squared=Fraction(0)` 与 `_exact_closed=(delta >= 0)`。
结合调用参数 delta，这两字段与通常分支具有相同精确显示依据；负极小 gap 可显示为负零，closed 不能由这个零重判。
非有限输入或最终上溢仍具名拒答。负 delta 的穿透 sentinel 不声称 closed。
门：`test_r15_o03_penetration_early_return_has_exact_display_certificate`、
`test_r15_o03_penetration_early_return_rejects_nonfinite_or_overflow_gap`。

## 4. JSON 先保留数值，后由 schema 分派支持域

JSON `parse_float` 只把有限十进制实数字面量保留为精确 Fraction，并保留实数语法的负零；不提前套连续输出域。
整数身份按分母等于 1 保留任意精度，因此 `1e400` 与整数 token `10**400` 等值时行为一致。
已知连续字段在自己的 schema 内检查 RN-even 有限、非零范围；NaN/Infinity 仍拒绝。
这订正 R14 把十进制 token 整体先过连续域的实现，不放松任何连续量的输出检查。

bdda3d 的 `nsign/owner` 明确进入整数分派；`t1/t2/d1/fa/coh/tens` 各自进入连续分派，
不能靠整数字面量或只提供一个切向参数绕过检查。未知 extra 元数据保留既有树解码模型，不新造字段语义。
门：`tests/test_r15fix_numeric_decode.py`，涵盖 ContactRecord、Feature、实际 bdda3d 文件与工具 document 入口，及原 M4a 门。

## 5. 向上高度显示的专属 infinity 例外

设最大有限 binary64 为 M。`escape_height_covers` 的 `exact_height` 始终是权威有限根；`height` 是向上 binary64 显示。
当根 `M < H < M+2^970` 时，其 RN-even 显示仍为有限 M，但向上不存在有限表示，故返回 `height=+inf`，
并明确返回 **`height_display_overflow=True`**。其它正常有限显示标记 False；这不是物理无界或状态哨兵。
RN-even 自身已溢出的端点及更大输入仍 `ConstructionDomainError`，不以 M 冒充向上界。

裸 float 的 `escape_height_brute` 无法携带该例外证书，遇标记 True 时具名拒答；需要此域的调用方用完整 EscapeSolution。
`dilatancy_profile` 每行保留 `exact_height`、`height_display_overflow`；位移按精确 delta×direction 构造，
中心差分 `(H_next-H_prev)/(delta_next-delta_prev)` 在有理数上完成后才最终舍入。
采样中心差分不是连续曲线导数的全域证明；不能用两个高度显示值相减代替精确根差。
门：`tests/test_r15fix_geometry.py` 的 O05 边界、裸包装拒答、profile 证书、倾斜平面斜率与精确 offset 门。

## 6. 验证边界

详见 [执行报告](../reports/codex/R15FIX_report.md) 与 [证据目录](../reports/codex/R15FIX_evidence/)。
全部原测试保留；新增门的内部变异改写真正被测函数，而非事后伪造结果。
静态站点准入只更新受影响的已审阅 AST/局部源码 pin，不改变分析器或降低原门；零诊断不是数学证明。
本轮扫描和有限回归不证明任意 Python API／任意有效几何的全域正确性，已有近似模型缺口不因此自动关闭。
