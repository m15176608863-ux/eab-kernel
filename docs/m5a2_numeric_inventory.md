# M5a2 数值合同增量

本文件只登记 M5a2 增量，不改写 M3/M4c/M5a 历史验证范围。

静态门是维护辅助，不是任意 Python 回调精确性的证明。新增 `algebraic-comparator-site`
要求 `scalar_algebraic` 的每个回调站点逐点准入（包括别名调用），未知形参或属性不自动获准。
仅现有 `RealAlgebraic.time` 的精确比较器与构造器内部符号反转递归两站点获准；
逐条理由及源码指纹见 [静态准入](../reports/codex/M5a2_evidence/static_admissions.json)。

原 3103 + M5a 117 条准入保留原值。修改作用域的旧指纹由单独、绑定原条目哈希和新作用域哈希的续审记录归档；
续审记录本身不给当前代码任何豁免，当前站点另有追加准入。

| API / 公开量 | 处置 | 具名门与边界 |
|---|---|---|
| `RealAlgebraic.as_rational()` | differential | `test_m5a2_exact.py::test_rational_reconstruction_recognizes_nondyadic_roots`：独立因式展开含非 dyadic 大分母；无理根排除、隔离区间外另一有理根的反例。整数本原多项式分母界、精确二分及代入，不通过 float 重构。 |
| `se2_first_entrance(...).exact_time` 的有理出口 | differential | `test_rational_lever_time_has_one_container_mixed_equality_hash_and_sorting`：L=5,h=3 的首时刻 1/3 统一为 `QuadraticTime`，混合 Fraction/旧时刻的排序、等值和 hash。一般 `RealAlgebraic` 仍不可哈希，不声称所有代数容器互通。 |
| `RigidFit.certificate`；独立 oracle 输入域；闭区间下端点根 | nonconstructive / differential | `test_every_exact_positive_residual_stays_uncertified` 含 2^-1074、10^-100；`test_independent_oracle_rejects_nonexact_inputs_at_first_contact`；`test_public_algebraic_constructor_retains_closed_lower_endpoint_root`。 |
| `AffineFit.center/translation/matrix/residuals/delta/endpoint`，`fit_affine` | differential | `test_m5a2_affine.py::test_fit_matches_independent_three_point_and_normal_equation_oracles`：独立未中心化 3x3 Cramer 解，不共享拟合原语。刚体坐标/单位门逐残差向量核对，含 2^-400 / 1 / 2^397、随机有理旋转及大平移。delta 是坐标 L-infinity 上界，不宣称其数值在任意旋转下不变。 |
| `DDAAffineMotion.at/endpoint/correction/corrected_at` | differential | `test_additive_trajectory_matches_independent_component_oracle`；`test_zero_strain_is_se2_and_zero_rotation_is_m4c_vertex_chord`；`test_linear_residual_correction_closes_data_without_certification`。精确轨迹构造不是一般首入求解器；无新增 binary64 显示出口。 |
| `AffineFit.endpoint_certificate`；`DDAAffineMotion.orientation_preserving_sufficient` | nonconstructive | 前者只声明端点仿射闭合，绝非物理轨迹或首盖证书；后者为 Neumann 充分条件，返回 false 仅为未知。`test_orientation_sufficient_bound_and_degenerate_counterexample` 与正残差/未知内点偏移门。 |
| 回放分类、序列化、`same_time`、扫掠界 | differential / nonconstructive | `test_m5a2_replay.py` 直接调用被接线的生产几何内核，由测试内独立分类得到账本期望：这是回放接线 oracle，不冒称独立几何 oracle。小转角包含主 oracle 独立展开有理坐标，无共享 bound/polynomial 原语。 |

B 的一般仿射事件求解、正残差首盖稳定认证及完整三模型首盖对账尚未实现，
不能由以上构造门、端点状态或轨迹偏差上界推出。证明状态见 [仿射理论](m5a2_affine_theory.md)。
