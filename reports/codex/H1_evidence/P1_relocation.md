# H1 P1 去域化搬家记录

## 结果

- 134 个函数/类定义逐项核对：60 搬、74 留；134/134 的完整函数/类源码字串未变（含嵌套方法，不含模块顶层 import）。
- `kernel3d/interlock.py` 整体移到 `adapters/tia3d.py`；`kernel2d/dda_motion.py` 整体移到 `adapters/bdda2d_motion.py`；不留兼容转发。
- `DDAAffineMotion` 单独移到 `adapters/bdda2d_affine.py`；`model_robustness.dda_paths` 移到 `adapters/bdda2d_motion.py`。
- `bdda2d_affine` 同时向外提供核心原对象 `AffineFit/fit_affine`，使 INT1 变异仪器只改顶层 import、全部 10 个函数源码保持原样；这是 adapter → core 的合法组合，不是内核兼容转发。
- DDA 模型私有的校验、构造与事件胶合随模型搬；通用多项式算术/根隔离仍在 `kernel2d/algebraic.py`，通用事件器仍在 `kernel2d/se2.py`，通用路径证书仍在 `model_robustness.py`、`m5c_certificates.py`、`m5d_exit_certificate.py`。
- `contact_record.py` 的 6 张映射表分别移到 `adapters/bdda2d.py`、新建 `bdda3d.py`、新建 `tf.py`。保留原表项，根包不再转导出域映射。
- 通用文本数值解码器从 `readers/numeric_decode.py` 移到 `eab/numeric_decode.py`，切断 `eab.__init__ → contact_record → readers` 的传递依赖；所有调用方改新路径。
- 唯一非搬家生产文案：`kernel3d/geom3.py::Polyhedron.edge_dir` 的零长边异常仍为 ValueError、条件未变，仅把提示中的 `readers.bdda_geom.strip_duplicate_vertices` 换成通用 input boundary。
- 当前文档/工具/测试路径补扫 399 个文本文件：机械更新文档 1 文件 1 处（`docs/plan_20260921.md:97`）；完整旧路径剩余 0。历史计划中 2 处裸 `interlock.py` 叙事保留，不改历史报告、夹具或 provenance 值；明细见 `p1_current_path_references.json`。

## 纯度门与牙

`tools/h1_kernel_purity.py` 对用户指定内核集合做 AST 检查：标识符按下划线/驼峰/数字族切词，非 docstring 字符串同查；起始词表全部保留，另加入“岩石/节理”。仅真实模块/类/函数 docstring 豁免。
导入图解析绝对导入、相对导入、from-package 子模块、隐式父包 `__init__` 和字面量动态导入，传递闭包不得进入 adapters/readers。

`tests/test_kernel_purity.py` 共 6 个节点：真实仓库纯度；两种副本注入（adapter import / mtype）各一个；传递导入；词法；真 docstring 豁免。
两种注入都写入复制的 `geom.py` 后执行真实 CLI，要求退出码 1 且对应规则文本出现；不是在审计结果之后追加假条目。
静态准入扫描 `scan_text(tests/test_kernel_purity.py) == []`，未新增准入，未修改扫描域；AST 审计工具与既有 tools 工具一样不属 src/tests 数值构造预检域。

## 局部验证

- 所有 `src/eab` 模块逐个导入成功。
- 原样末行：`237 passed in 35.28s`（纯度、记录、数值解码、仿射/P2、路径证书/R3）。
- 原样末行：`210 passed in 29.79s`（纯度 CLI 牙、INT1、TF/读取器、逃逸精确路径）；见 `p1_targeted_verification.log`。
- 机器对应表：`p1_function_relocation.json`；开工源码锚：`p1_sources_before.json`。这些是一次搬家说明，不是当前源码哈希绊线门。

## 逐定义留/搬理由

表含类及其方法，方便静态准入键的机械对应。`same` 全为 true。

| 原模块与定义 | 新位置 | 决定 | 理由 | same |
|---|---|---|---|---|
| `src/eab/kernel3d/interlock.py::escape_height_brute` | `src/eab/adapters/tia3d.py::escape_height_brute` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::EscapeSolution` | `src/eab/adapters/tia3d.py::EscapeSolution` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_normal_noise` | `src/eab/adapters/tia3d.py::_normal_noise` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_cover_escape_z` | `src/eab/adapters/tia3d.py::_cover_escape_z` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_cover_at` | `src/eab/adapters/tia3d.py::_cover_at` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_CandidateSnapshot` | `src/eab/adapters/tia3d.py::_CandidateSnapshot` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_candidates` | `src/eab/adapters/tia3d.py::_candidates` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_candidates_cached` | `src/eab/adapters/tia3d.py::_candidates_cached` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_candidates_uncached` | `src/eab/adapters/tia3d.py::_candidates_uncached` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::escape_candidates` | `src/eab/adapters/tia3d.py::escape_candidates` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_nonpenetrating_at` | `src/eab/adapters/tia3d.py::_nonpenetrating_at` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_escape_sections` | `src/eab/adapters/tia3d.py::_escape_sections` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_prior_intervals` | `src/eab/adapters/tia3d.py::_prior_intervals` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_exact_escape` | `src/eab/adapters/tia3d.py::_exact_escape` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_exact_escape_cached` | `src/eab/adapters/tia3d.py::_exact_escape_cached` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::escape_height_covers` | `src/eab/adapters/tia3d.py::escape_height_covers` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::_escape_solution` | `src/eab/adapters/tia3d.py::_escape_solution` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::escape_height_from_frozen_cover` | `src/eab/adapters/tia3d.py::escape_height_from_frozen_cover` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel3d/interlock.py::dilatancy_profile` | `src/eab/adapters/tia3d.py::dilatancy_profile` | 搬 | TIA 逃逸高度/剪胀域 API 及其私有实现 | true |
| `src/eab/kernel2d/dda_motion.py::_q` | `src/eab/adapters/bdda2d_motion.py::_q` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_point` | `src/eab/adapters/bdda2d_motion.py::_point` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_matrix` | `src/eab/adapters/bdda2d_motion.py::_matrix` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_apply` | `src/eab/adapters/bdda2d_motion.py::_apply` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::area_centroid` | `src/eab/adapters/bdda2d_motion.py::area_centroid` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_trig_bounds` | `src/eab/adapters/bdda2d_motion.py::_trig_bounds` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::HalfAngleApproximation` | `src/eab/adapters/bdda2d_motion.py::HalfAngleApproximation` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::HalfAngleApproximation.__post_init__` | `src/eab/adapters/bdda2d_motion.py::HalfAngleApproximation.__post_init__` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::HalfAngleApproximation.error` | `src/eab/adapters/bdda2d_motion.py::HalfAngleApproximation.error` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::rational_half_angle` | `src/eab/adapters/bdda2d_motion.py::rational_half_angle` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::DDAAnchoredMotion` | `src/eab/adapters/bdda2d_motion.py::DDAAnchoredMotion` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::DDAAnchoredMotion.__post_init__` | `src/eab/adapters/bdda2d_motion.py::DDAAnchoredMotion.__post_init__` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::DDAAnchoredMotion.orientation_preserving_sufficient` | `src/eab/adapters/bdda2d_motion.py::DDAAnchoredMotion.orientation_preserving_sufficient` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::DDAAnchoredMotion.at` | `src/eab/adapters/bdda2d_motion.py::DDAAnchoredMotion.at` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::DDAAnchoredMotion.endpoint` | `src/eab/adapters/bdda2d_motion.py::DDAAnchoredMotion.endpoint` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::DDAAnchoredMotion.coordinate_polynomials` | `src/eab/adapters/bdda2d_motion.py::DDAAnchoredMotion.coordinate_polynomials` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::dda_motion_from_z` | `src/eab/adapters/bdda2d_motion.py::dda_motion_from_z` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::p2_p3_bound` | `src/eab/adapters/bdda2d_motion.py::p2_p3_bound` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_local_numerators` | `src/eab/adapters/bdda2d_motion.py::_local_numerators` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_pcross` | `src/eab/adapters/bdda2d_motion.py::_pcross` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_pdot` | `src/eab/adapters/bdda2d_motion.py::_pdot` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_DDARing` | `src/eab/adapters/bdda2d_motion.py::_DDARing` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_validated_ring` | `src/eab/adapters/bdda2d_motion.py::_validated_ring` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_divide_positive_factor` | `src/eab/adapters/bdda2d_motion.py::_divide_positive_factor` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::_line_polynomials` | `src/eab/adapters/bdda2d_motion.py::_line_polynomials` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::projected_sweep` | `src/eab/adapters/bdda2d_motion.py::projected_sweep` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/dda_motion.py::dda_first_entrance` | `src/eab/adapters/bdda2d_motion.py::dda_first_entrance` | 搬 | DDA 锚定 P2 模型及其精确构造/事件胶合；通用算术仍在内核 | true |
| `src/eab/kernel2d/affine_motion.py::_q` | `src/eab/kernel2d/affine_motion.py::_q` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::_point` | `src/eab/kernel2d/affine_motion.py::_point` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::_matrix` | `src/eab/kernel2d/affine_motion.py::_matrix` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::_apply` | `src/eab/kernel2d/affine_motion.py::_apply` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::AffineFit` | `src/eab/kernel2d/affine_motion.py::AffineFit` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::AffineFit.__post_init__` | `src/eab/kernel2d/affine_motion.py::AffineFit.__post_init__` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::AffineFit.delta` | `src/eab/kernel2d/affine_motion.py::AffineFit.delta` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::AffineFit.endpoint_certificate` | `src/eab/kernel2d/affine_motion.py::AffineFit.endpoint_certificate` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::AffineFit.endpoint` | `src/eab/kernel2d/affine_motion.py::AffineFit.endpoint` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::fit_affine` | `src/eab/kernel2d/affine_motion.py::fit_affine` | 留 | 通用精确仿射拟合与输入校验 | true |
| `src/eab/kernel2d/affine_motion.py::DDAAffineMotion` | `src/eab/adapters/bdda2d_affine.py::DDAAffineMotion` | 搬 | DDA 端点形状路径类 | true |
| `src/eab/kernel2d/affine_motion.py::DDAAffineMotion.__post_init__` | `src/eab/adapters/bdda2d_affine.py::DDAAffineMotion.__post_init__` | 搬 | DDA 端点形状路径类 | true |
| `src/eab/kernel2d/affine_motion.py::DDAAffineMotion.correction` | `src/eab/adapters/bdda2d_affine.py::DDAAffineMotion.correction` | 搬 | DDA 端点形状路径类 | true |
| `src/eab/kernel2d/affine_motion.py::DDAAffineMotion.orientation_preserving_sufficient` | `src/eab/adapters/bdda2d_affine.py::DDAAffineMotion.orientation_preserving_sufficient` | 搬 | DDA 端点形状路径类 | true |
| `src/eab/kernel2d/affine_motion.py::DDAAffineMotion.at` | `src/eab/adapters/bdda2d_affine.py::DDAAffineMotion.at` | 搬 | DDA 端点形状路径类 | true |
| `src/eab/kernel2d/affine_motion.py::DDAAffineMotion.endpoint` | `src/eab/adapters/bdda2d_affine.py::DDAAffineMotion.endpoint` | 搬 | DDA 端点形状路径类 | true |
| `src/eab/kernel2d/affine_motion.py::DDAAffineMotion.corrected_at` | `src/eab/adapters/bdda2d_affine.py::DDAAffineMotion.corrected_at` | 搬 | DDA 端点形状路径类 | true |
| `src/eab/kernel2d/model_robustness.py::_q` | `src/eab/kernel2d/model_robustness.py::_q` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_window` | `src/eab/kernel2d/model_robustness.py::_window` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_add` | `src/eab/kernel2d/model_robustness.py::_add` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_scale` | `src/eab/kernel2d/model_robustness.py::_scale` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::polynomial_range` | `src/eab/kernel2d/model_robustness.py::polynomial_range` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::chord_paths` | `src/eab/kernel2d/model_robustness.py::chord_paths` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::dda_paths` | `src/eab/adapters/bdda2d_motion.py::dda_paths` | 搬 | DDA 路径类型到有理坐标路径的适配 | true |
| `src/eab/kernel2d/model_robustness.py::_validate` | `src/eab/kernel2d/model_robustness.py::_validate` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_quotient` | `src/eab/kernel2d/model_robustness.py::_quotient` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_projection` | `src/eab/kernel2d/model_robustness.py::_projection` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_value` | `src/eab/kernel2d/model_robustness.py::_value` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_panels` | `src/eab/kernel2d/model_robustness.py::_panels` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_normals` | `src/eab/kernel2d/model_robustness.py::_normals` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_radii` | `src/eab/kernel2d/model_robustness.py::_radii` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::separation_certificate` | `src/eab/kernel2d/model_robustness.py::separation_certificate` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_minus` | `src/eab/kernel2d/model_robustness.py::_minus` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_times` | `src/eab/kernel2d/model_robustness.py::_times` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_plus` | `src/eab/kernel2d/model_robustness.py::_plus` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_cross` | `src/eab/kernel2d/model_robustness.py::_cross` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_dot` | `src/eab/kernel2d/model_robustness.py::_dot` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_boxes` | `src/eab/kernel2d/model_robustness.py::_boxes` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_diff` | `src/eab/kernel2d/model_robustness.py::_diff` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_length1` | `src/eab/kernel2d/model_robustness.py::_length1` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_event` | `src/eab/kernel2d/model_robustness.py::_event` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_strict_convex` | `src/eab/kernel2d/model_robustness.py::_strict_convex` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::swept_axis_bounds` | `src/eab/kernel2d/model_robustness.py::swept_axis_bounds` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_mul_poly` | `src/eab/kernel2d/model_robustness.py::_mul_poly` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_derivative` | `src/eab/kernel2d/model_robustness.py::_derivative` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::_event_derivative` | `src/eab/kernel2d/model_robustness.py::_event_derivative` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/kernel2d/model_robustness.py::single_cover_certificate` | `src/eab/kernel2d/model_robustness.py::single_cover_certificate` | 留 | 通用路径/顶点管证书代数，无 legacy 槽位 | true |
| `src/eab/contact_record.py::CoverType` | `src/eab/contact_record.py::CoverType` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::Mode` | `src/eab/contact_record.py::Mode` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::Feature` | `src/eab/contact_record.py::Feature` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::Feature.as_tuple` | `src/eab/contact_record.py::Feature.as_tuple` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::ContactRecord` | `src/eab/contact_record.py::ContactRecord` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::ContactRecord.canonical_key` | `src/eab/contact_record.py::ContactRecord.canonical_key` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::ContactRecord.to_dict` | `src/eab/contact_record.py::ContactRecord.to_dict` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::ContactRecord.from_dict` | `src/eab/contact_record.py::ContactRecord.from_dict` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::_encode` | `src/eab/contact_record.py::_encode` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::_decode` | `src/eab/contact_record.py::_decode` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::validate` | `src/eab/contact_record.py::validate` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::records_to_json` | `src/eab/contact_record.py::records_to_json` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/contact_record.py::records_from_json` | `src/eab/contact_record.py::records_from_json` | 留 | 域无关的记录结构/枚举与序列化 | true |
| `src/eab/readers/numeric_decode.py::_decimal` | `src/eab/numeric_decode.py::_decimal` | 搬 | 通用精确数值文本边界，去除传递 reader 依赖 | true |
| `src/eab/readers/numeric_decode.py::scalar` | `src/eab/numeric_decode.py::scalar` | 搬 | 通用精确数值文本边界，去除传递 reader 依赖 | true |
| `src/eab/readers/numeric_decode.py::_nonfinite` | `src/eab/numeric_decode.py::_nonfinite` | 搬 | 通用精确数值文本边界，去除传递 reader 依赖 | true |
| `src/eab/readers/numeric_decode.py::loads` | `src/eab/numeric_decode.py::loads` | 搬 | 通用精确数值文本边界，去除传递 reader 依赖 | true |
| `src/eab/readers/numeric_decode.py::integer` | `src/eab/numeric_decode.py::integer` | 搬 | 通用精确数值文本边界，去除传递 reader 依赖 | true |
| `src/eab/readers/numeric_decode.py::decode_tree` | `src/eab/numeric_decode.py::decode_tree` | 搬 | 通用精确数值文本边界，去除传递 reader 依赖 | true |
| `src/eab/kernel2d/m5c_certificates.py::_relative` | `src/eab/kernel2d/m5c_certificates.py::_relative` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::_bilinear` | `src/eab/kernel2d/m5c_certificates.py::_bilinear` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::_length1` | `src/eab/kernel2d/m5c_certificates.py::_length1` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::_event` | `src/eab/kernel2d/m5c_certificates.py::_event` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::_normals` | `src/eab/kernel2d/m5c_certificates.py::_normals` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::_separation` | `src/eab/kernel2d/m5c_certificates.py::_separation` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::relative_separation_certificate` | `src/eab/kernel2d/m5c_certificates.py::relative_separation_certificate` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::_simple` | `src/eab/kernel2d/m5c_certificates.py::_simple` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::diagnose_single_cover` | `src/eab/kernel2d/m5c_certificates.py::diagnose_single_cover` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5c_certificates.py::single_cover_certificate` | `src/eab/kernel2d/m5c_certificates.py::single_cover_certificate` | 留 | 通用相对路径与简单环单首盖证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_exact` | `src/eab/kernel2d/m5d_exit_certificate.py::_exact` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_ring` | `src/eab/kernel2d/m5d_exit_certificate.py::_ring` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_sub` | `src/eab/kernel2d/m5d_exit_certificate.py::_sub` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_cross` | `src/eab/kernel2d/m5d_exit_certificate.py::_cross` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_l1` | `src/eab/kernel2d/m5d_exit_certificate.py::_l1` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_convex_guard` | `src/eab/kernel2d/m5d_exit_certificate.py::_convex_guard` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_cross_guard` | `src/eab/kernel2d/m5d_exit_certificate.py::_cross_guard` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_boundary` | `src/eab/kernel2d/m5d_exit_certificate.py::_boundary` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_distance2` | `src/eab/kernel2d/m5d_exit_certificate.py::_distance2` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::_rank_guard` | `src/eab/kernel2d/m5d_exit_certificate.py::_rank_guard` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::exit_order_certificate` | `src/eab/kernel2d/m5d_exit_certificate.py::exit_order_certificate` | 留 | 通用凸环最短出口排序证书 | true |
| `src/eab/kernel2d/m5d_exit_certificate.py::exit_order_certificate.refused` | `src/eab/kernel2d/m5d_exit_certificate.py::exit_order_certificate.refused` | 留 | 通用凸环最短出口排序证书 | true |
