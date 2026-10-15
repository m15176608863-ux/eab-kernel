# M5b P2 数值合同清单

本清单覆盖 P2、现有 `algebraic.py` 的六次域扩展、稳健认证与端点/对账工具。生产几何的数值决定是有理/代数精确决定，非浮点阈值。下表 P2 公开有理输入拒绝 `float/bool/str`，二进制文件输入须由读入器明确转换成 `Fraction`；工具外部解码/观测重放的 binary64 边界另在后表明确登记。

| API / 量 | 输入及支持域 | 输出/合同 | 门 |
|---|---|---|---|
| `area_centroid` | int/Fraction，二维单简单非零面积环 | 精确有向面积形心，归一方向不改形心 | `test_area_centroid_is_area_weighted_and_frame_covariant` |
| `rational_half_angle` | `|theta|<=1`，整数精度位 `8..512` | 有理 Taylor 包围 `[lower,upper]`、dyadic `u1`、严格绝对误差上界；theta=0全零 | `test_half_angle_has_independent_taylor_enclosure_and_zero_exactness` |
| `HalfAngleApproximation` | 四个有理字段，区间有序，theta/u1在支持域 | 普通只读表示；直接构造**不自证**区间包含超越函数值 | 同上，证书来源仅限工厂函数 |
| `DDAAnchoredMotion` | `|u1|<=1`、二维有理 d/c、有理对称2×2 E | 显式P2模型，不从端点拟合E、不隐藏物理路径假设 | `test_p2_coordinates_match_independent_complex_product_oracle` |
| `.at/.endpoint` | 有理点、有理 `0<=s<=1` | 精确有理坐标；theta=0弦、E=0同中心SE2 | `test_zero_angle_is_p1_and_zero_strain_is_same_center_se2` |
| `.coordinate_polynomials` | 有理点 | 升幂系数 `((Nx,Ny),D)`，分子≤3次，正D≤2次 | `test_coordinate_polynomial_identity` |
| `.orientation_preserving_sufficient` | `E`如上 | 布尔 `2*||E||∞<1`；False是未知，不是反转 | `test_unsupported_p2_domains_fail_loudly_before_event_enumeration` |
| `dda_motion_from_z` | 单环、6个有理z、近似位数 | 面积形心、d=z前2项、E12=z6/2、严格半角近似 | `test_dda_z_mapping_uses_area_centroid_and_engineering_shear` |
| `p2_p3_bound` | 非空点、显式P2、`|theta|<=1` | 所有字典量Fraction；radius_l1、time_law_angle、parameter_angle、half_angle_error、position；position为全窗Euclidean及坐标上界 | `test_p2_p3_uniform_bound_contains_independent_interval_trigonometry` |
| `projected_sweep` | 非空点、显式P2、有理非零方向 | 两个Fraction，包含全窗所有多边形点投影；只作充分证书 | `test_projected_sweep_contains_all_independent_rational_probes` |
| `_line_polynomials` | 验证后环、两个特征索引 | F/G/H精确分子、正DA DB分母；D_B整除及≤6次均有运行时检查 | `test_sixth_degree_events_match_independent_seven_sample_oracle` |
| `dda_first_entrance` | 单简单环、显式P2、每块`2*||E||∞<1` | 复用`SE2Entrance2`协议；初态-1/0/1，status，精确time，全并列incidences/features，初始PD惰性 | `test_complete_first_contact_matches_independent_oracle` |
| `RealAlgebraic/roots_interval` | **平方自由化前**次数1..6、精确系数与隔离区间 | 原Sturm/gcd/区间精确判定不变；7次拒绝，无容差放宽 | `test_sixth_degree_root_isolation_has_independent_factor_and_bisection_oracles` |

## 浮点边界、静态准入、舍入

- 本模块不新增 `float()`、`math.*`、NumPy、隐式binary64构造或显示构造通道；`round(Fraction)` 只用于 dyadic 半角有理网格，不返回 binary64。
- `dataclass(frozen=True)` 的 `object.__setattr__` 只将已验证字段规范化为 Fraction/元组；不接受任意反射名称。静态逐站审查记录由 M5b INT1 延续审查落盘。
- `_event_times`、`_features`、`as_rational`、`QuadraticTime` 的调用是现有精确协议复用；显示 `.time` 仍经原 construction boundary，绝不反馈判定。
- 网格位数是用户指定的近似精度/资源域，不是接触阈值；其全部误差显式进入 P2/P3 上界。
- 新增API不保证任意大型输入的性能；全时程对账应冻结真实运行结果，不能把门的不足一秒运行时间外推成 64010 步—块对的性能承诺。

## 严格充分稳健证书：`src/eab/kernel2d/model_robustness.py`

各接口的坐标、系数、时间与半径要求 int/Fraction；布尔、字符串、float 数值输入被拒绝。结果中的量为 Fraction 或离散状态/标签，无新增 binary64 输出。`None` 表示充分条件未证，不表示实际模型敏感，更不表示无接触。误差半径为**每顶点坐标 L∞ 全窗界**，其语义只针对已规定连续管，不是未知真实路径。

| API / 量 | 输入及域 | 输出/判定合同 | 具名门 |
|---|---|---|---|
| `polynomial_range` | 非空精确多项式，`0<=lo<=hi<=1` | Bernstein 系数凸包得到精确有理包围；非精确极值 | `test_bernstein_independent_oracle` |
| `chord_paths` | 等长≥3顶点、有理两帧 | 每顶点 `(Nx,Ny,D)`；P1线性分子、D=1 | `test_single_cover_certificate_has_independent_closed_form_oracle` |
| `dda_paths` | 有理初始环、`DDAAnchoredMotion` | 使用P2精确坐标多项式，拒绝任意未审回调 | `test_replay_distinguishes_robust_first_cover_from_unproved_initial_exit` |
| `swept_axis_bounds` | ≥3条有理顶点路径、全窗分母严格正证书 | 每坐标整段上下包围，可缓存作批量充分证书；不把box距离叫精确几何间隙 | `test_no_contact_requires_strict_margin_and_covers_whole_window`；`test_replay_rounding_tube_is_charged_even_when_models_have_same_status` |
| `separation_certificate` | 上述路径、非负L∞半径、有理闭窗、正整数panels | 每闭子窗严格投影间隙/`||n||1` 大于两半径和才返回 `ROBUST_NO_CONTACT`；等号不通过 | `test_no_contact_requires_strict_margin_and_covers_whole_window` |
| `single_cover_certificate` | 同上、单个VE/EV、严格括区间；管内严格凸CCW环由全部非邻顶点余量验证 | 早期分离、边内投影、名义严格横截、两端异号、所有竞争事件排除均过才给单首盖身份；**不认证扰动后导数/唯一根/精确时间不变** | `test_single_cover_certificate_has_independent_closed_form_oracle`；`test_single_cover_rejects_endpoint_uncertainty_and_competing_tie` |

主 oracle 只用 Fraction、整数/阶乘或组合数、独立闭式菱形—墙事件；不复用生产几何、求根、Bernstein 算法来造期望。`tests/test_m5b_robustness.py` 收集 13 个节点，包含大平移/一般有理旋转/单位缩放门 `test_certificates_are_covariant_under_rotation_translation_and_units`，以及内部语义变异 `test_tube_margin_mutation_dies_on_semantics_not_hash`（严格不等号）和 `test_crossing_error_mutation_dies_on_semantics_not_hash`（两端误差）。文档证明见 `docs/m5b_robustness_theory.md`，不是用有限采样替代连续管证明。

## 对账接线：`tools/m5b_robust_replay.py`

| API / 量 | 口径及合同 | 具名门 |
|---|---|---|
| `prepare` | 从冻结有理初末帧与z构造P1/P2；`radius=P2_P3_bound+max|P2_endpoint-observed_endpoint|+radius_l1*parameter_angle`。新增末项覆盖P3自己的端点闭合残差；同一保守半径计入两模型 | `test_replay_rounding_tube_is_charged_even_when_models_have_same_status`；`test_p3_own_endpoint_closure_has_separate_parameter_error_budget` |
| `compare_pair` | P1/P2先比状态及完整首盖集合，随后两者均须有严格充分证书才进入稳健子集；比较时间证书单列；P3仅管内保证，不做超越首根；初始出口排序没有正误差余量证明则未证 | `test_replay_distinguishes_robust_first_cover_from_unproved_initial_exit` |
| `legacy_counts` | 只消费已有稳健分类与规范化**主参考primary**标签；逐阶段计数FIRST_COVER_MATCH/OTHER_REFERENCE、ROBUST_CONTACT_MISSING_PAIR、ROBUST_FIRST_COVER_NOT_SELECTED；最后一项只表示未选作**主参考**，不表示未选作次参考；未证参考不进入稳健分母 | 同上；标签分类是接线一致性，不冒充几何主oracle；`test_legacy_ledger_is_primary_only_even_if_secondary_matches_first_cover` |
| 半径接线变异 | 即使两个名义模型状态相同也必须支付正端点误差半径；把半径接成0或漏P3自身端点闭合额外项须在语义断言报红 | `test_replay_tube_wiring_mutation_is_killed_by_semantic_assertion`；`test_p3_endpoint_closure_budget_mutation_dies_on_wiring_assertion` |
| 冻结覆盖 | 15例、1810步、15220块帧；完整块对枚举64010；开始/结束绑定输入与源码、每5步进度、中断作废不拼接 | `test_frozen_input_counts_cover_fifteen_cases_and_15220_blocks`（计数门）；全时程真实运行另有摘要 |

`tests/test_m5b_replay.py` 共7个接线/冻结/口径门。这些门验证主oracle结果怎样进入证书与计数，**不是另一套独立几何 oracle**。次参考（legacy VV 的secondary VE）仍未对账，列PARTIAL；原始tuple7仍保留以便续做。观测到 P1/P2 差异与未通过充分证书必须分列；`MODEL_SENSITIVE_OR_UNPROVED` 不能当实际差异率。

## 端点与输入边界：`tools/m5b_endpoint_replay.py`

| API / 量 | 数值合同 | 具名门 / 限制 |
|---|---|---|
| `binary64_decimal` | 外部 `%.17g` 字符串先解码为binary64，再`Fraction(value)`冻结其精确值；拒绝非有限值和正值下溢为0；不把原十进制当精确坐标 | `test_z_rows_pair_by_step_block_not_csv_order_and_snapshot_is_start`；属于明确输入边界，不用于内核判据 |
| `exact_points` / `area_centroid` | 冻结有理字符串→Fraction；独立有向面积矩，无生产几何helper，零面积拒绝 | `test_area_centroid_matches_independent_triangle_integrals` |
| `sin_cos_intervals` | `|theta|<=1`、正整数terms，交错Taylor有理包围 | `test_trig_enclosures_match_independent_lagrange_oracle`；提供数学sin/cos严格界，不证明历史CRT位相同 |
| `endpoint_map` | 显式给定c计算所需顶点/z、显式sin/cos的精确有理值 | `test_endpoint_map_matches_independent_displacement_oracle`；公共映射 `M=[[cos+ex,-sin+gxy/2],[sin+gxy/2,cos+ey]]`，非矩阵乘法应变 |
| `dda_position_intervals` | 同z与面积形心，在一个有理s上P3的坐标Taylor区间 | 单时刻严格包围；不是整段采样证书；P2/P3整段界来自P2理论 |
| `rounding_unit` | `U=ulp(max(abs(coordinate)))`，最大值覆盖块初末帧两坐标；U为该正幅度上侧binary64间距，零为`2^-1074` | `test_rounding_unit_is_block_ulp_not_epsilon_coordinate`；不是unit roundoff，也不是coordinate×`2^-52` |
| `reconstruct` | Python binary64 sin/cos的精确Fraction值给M_DDA；与末帧残差严格有理计算；数学sin/cos误差、位置误差另用Taylor包围 | `test_frozen_endpoint_evidence_has_all_cases_and_recomputable_extrema`；**不保证未知历史C++ CRT逐位相同**，提供严格误差上界 |
| `grouped_binary64_replay` | 只读源语句分组的binary64算术重放，按调用方环序求和；物理lo..hi循环起点由`m5b_grouped_probe.physical_order`核对/恢复；统计精确数值相等，Fraction合并±0 | **仅佐证**。复用源算法分组，不能当独立主oracle；不是signed-zero逐位同一，也不能由输出相同反推内部形心/三角函数位唯一 |
| `freeze_inputs` | z行按(step,block)配`geom.step(k-1)→step(k)`；snapshot k是起点；terminal给最后终点；校验全部输入哈希、拓扑/别名/行数，无遗漏z | `test_z_rows_pair_by_step_block_not_csv_order_and_snapshot_is_start`；源只读复制到本树tmp，入库分片均≤1MB |

端点不变性门：`test_centroid_and_endpoint_rigid_motion_and_unit_invariance`（12格：3尺度×4平移，含一般有理旋转）；端点内部变异门：`test_internal_endpoint_mutants_fail_designated_semantics`；历史中点最大例的独立三乘三重建：`test_midpoint_minimal_example_has_independent_three_by_three_reconstruction`。二进制重放仅佐证的信任边界不得因误差小或逐位吻合而删除。

## INT1 补项：有理重建模筛选

`RealAlgebraic.as_rational` 的素数无根筛选必须枚举**包括余数0**的全部剩余类。`tests/test_m5b_int1_followup.py::test_as_rational_modular_filter_includes_the_zero_residue` 独立整数展开 `(x-p)(x²+p)`：模p只在0有根，但选中的真实根p非零。`test_residue_zero_guard_kills_the_internal_nonzero_residues_only_mutant` 把内部循环改为`range(1,prime)`，明确由有理重建语义断言杀死，不靠哈希。此项不改变 `as_rational` 算法，只补合同门。
