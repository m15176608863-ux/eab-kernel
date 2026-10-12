# R13FIX 公开构造 API 差分门普查

**结论：补齐了一批明确缺口，但没有完成全部公开构造 API 的极尺度独立逐值门；不得据此声称全覆盖。**

## 范围与判定办法

- AST 遍历全部 `src/eab/**/*.py` 的顶层函数、类方法和注解字段；私有类/私有函数保留在 JSON，明确非 public。特殊算术方法作为 public 纳入。
- public 是源码命名暴露面的保守上界，不仅是 `__init__.py` 的再导出；oracle/读取/判据/诊断也列清。数据记录字段不能因所属类型受测就自动当作全部字段已测。
- 表内 nodeid 为人工按公式与断言对象核对的映射。扫描只验证 nodeid 存在，绝不以 grep、函数名出现或全套绿推断独立性或覆盖。
- 每行新增门只证明列明的构造族/尺度；角度、诊断多根式、随机/名义候选和普通 Dual 快路均保留限制。静态子集门是辅助检查，不是此处运行时主保证的替代。

## 统计

```json
{
  "all_symbols_including_private": 915,
  "public_callables": 333,
  "public_fields": 249,
  "explicitly_mapped_callables": 107,
  "unconfirmed_numeric_callables": 138
}
```

## 已知遗留（R13FIX_PARTIAL 的实质项）

1. `geom/geom3` 的 all-float add/sub/mul/translate/box 与 dot/cross 已补范围/逐值门；混合类型及泛型其它代数路径仍未建立完整范围保证，未泛改 Fraction/Dual 语义。
2. 所有角度的完整非正交及极小角族、随机样本构造、坐标选择器全部返回字段、部分精确工具 API 仍需逐项补门。
3. `noise_floor/round_floor` 新增的是不可表达非零响亮拒绝门；外围 policy estimates（margin 等）、metrics、泛化噪声网格未全部补齐。face_noise 的逐边长度若自身不可表达仍可能拒绝最终可表达比例。
4. 普通 Dual 算术快路/一般幂/超越函数不保证全域正确舍入；新门严格区分 libm 系数模型与真超越函数。
5. readers/adapters/contacts转换的各公开数值字段与机械一般活跃集未有此次完整极尺度逐值证明；3D摩擦生成器已新增两k×四mu的给定系数模型门，不是全输入域保证；M4a既有门必须另行回归。
6. nominal escape候选容许抑制、dilatancy只新增平坦零导数族，不能等同完整差分保证。

## 每个公开调用点/字段台账

完整私有/公开机器表见 `reports/codex/R13FIX_evidence/construction/public_api_inventory.json`。

### `src/eab/adapters/bdda2d.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `adapters.bdda2d.Bdda2DWindow.step` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.d0` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.h1_degrees` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.seg_tol` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.fit_tol` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.source` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.fallback_fields` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.raw_parameters` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.cone_tol` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.Bdda2DWindow.metadata` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.load_window` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `adapters.bdda2d.detect_step` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/construction.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `construction.scalar_rational` | 数值构造/混合输出（需有独立逐值门）；已有独立差分门 | `tests/test_r9fix_construction_rounding.py::test_r9_scalar_ratio_are_certified_at_binary64_midpoints`<br>0/minsub/minnormal/2^-600/1/3/7/2^600/max及中点两侧<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `construction.ratio_rational` | 数值构造/混合输出（需有独立逐值门）；已有独立差分门 | `tests/test_r9fix_construction_rounding.py::test_r9_scalar_ratio_are_certified_at_binary64_midpoints`<br>0/minsub/minnormal/2^-600/1/3/7/2^600/max及中点两侧<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `construction.vector_rational` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_vector_constructor_has_independent_extreme_cells_and_distinct_outputs`<br>minsub/2^-600/1/3/2^600/max+2^969；产物互异；正负输出范围拒绝<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `construction.sqrt_rational` | 数值构造/混合输出（需有独立逐值门）；已有独立差分门 | `tests/test_r9fix_construction_rounding.py::test_r9_exact_sqrt_is_certified_at_binary64_midpoints`<br>`tests/test_r9fix_construction_rounding.py::test_r9_exact_sqrt_non_square_subnormal_certificates`<br>全binary64关键舍入cell与24非平方次正规cell<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `construction.norm_rational` | 数值构造/混合输出（需有独立逐值门）；已有独立差分门 | `tests/test_r9fix_construction_rounding.py::test_r9_norm_and_unit_round_exact_final_components`<br>次正规/普通/上溢边缘及大有理数归一化<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `construction.unit_rational` | 数值构造/混合输出（需有独立逐值门）；已有独立差分门 | `tests/test_r9fix_construction_rounding.py::test_r9_norm_and_unit_round_exact_final_components`<br>次正规/普通/上溢边缘及大有理数归一化<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `construction.normalized_difference_rational` | 数值构造/混合输出（需有独立逐值门）；已有独立差分门 | `tests/test_r9fix_compound_construction.py::test_compound_constructor_rounds_values_between_max_and_overflow_midpoint`<br>`tests/test_r9fix_compound_construction.py::test_compound_range_and_cancellation_are_not_decided_by_intermediate_displays`<br>max与overflow中点之间/2^1100相消/minsub以下<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |

### `src/eab/contact_record.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `contact_record.Feature.block` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.Feature.kind` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.Feature.index` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.Feature.verts` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.Feature.as_tuple` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.source` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.step` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.contact_index` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.block_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.block_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.cover` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.raw_cover` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.feature_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.feature_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.joint_material` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.ref_points` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.length_or_area` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.params` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.mode` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.raw_mode` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.mode_prev` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.raw_mode_prev` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.entrance_index` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.gap` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.shear` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.normal_force` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.mode_init` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.raw_mode_init` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.gap_ref` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.slip_ref` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.bond_flag` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.lock_position` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.extra` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.canonical_key` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.to_dict` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.ContactRecord.from_dict` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.validate` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.records_to_json` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `contact_record.records_from_json` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/dual.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `dual.Dual.v` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.e` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.const` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.seed` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.width` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.is_exact_zero` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__add__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__neg__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__sub__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__rsub__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__mul__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__truediv__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__rtruediv__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.Dual.__pow__` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.val` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.grad` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.is_exact_zero` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.sqrt` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_dual_angular_and_sqrt_derivatives_are_value_bound`<br>2^[-1074,-600,0,600,1022]<br>导数有理参考；非代数primal不承诺全域正确舍入 |
| `dual.sin` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_trig_derivative_follows_declared_coefficient_model`<br>2^[-1074,-600,0,600,1022]<br>libm系数已给定的导数积模型，非真超越函数全域舍入证明 |
| `dual.cos` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_trig_derivative_follows_declared_coefficient_model`<br>2^[-1074,-600,0,600,1022]<br>libm系数已给定的导数积模型，非真超越函数全域舍入证明 |
| `dual.atan2` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_dual_angular_and_sqrt_derivatives_are_value_bound`<br>2^[-1074,-600,0,600,1022]<br>导数有理参考；非代数primal不承诺全域正确舍入 |
| `dual.lift` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.seeded` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.central_difference` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `dual.convergence_order` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel2d/covers.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel2d.covers.Cover.kind` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.a_index` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.b_index` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.gap` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.param` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.point` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.strict` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.point_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.point_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.window_active` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.Cover.label` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.normal_cone` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.covers.cone_width` | 数值构造/混合输出（需有独立逐值门）；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel2d.covers.in_cone` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.ve_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_2d_cover_fields_match_exact_projection_and_gap`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.covers.ev_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_2d_cover_fields_match_exact_projection_and_gap`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.covers.vv_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_2d_cover_fields_match_exact_projection_and_gap`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.covers.enumerate_covers` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_2d_cover_fields_match_exact_projection_and_gap`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.covers.first_entrance_for_vertex` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.EntranceBlock.vertices` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.EntranceBlock.facets` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.EntranceBlock.vv` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.convex_entrance_block` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.facet_gap` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_2d_cover_fields_match_exact_projection_and_gap`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.covers.membership_convex` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.local_facets` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.covers.ambiguous_facets` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel2d/entrance.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel2d.entrance.Entrance2.kind` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.t` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.x` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.point_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.point_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.gap` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.tied_labels` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.n_candidates` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.near_labels` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.Entrance2.t_exact` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.entrance.first_entrance` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_event_bindings.py::test_public_2d_event_fields_have_independent_extreme_scale_references`<br>`tests/test_r13fix_event_bindings.py::test_public_entrance_times_are_rounded_once_at_extreme_scales`<br>2^[-1070,0,1018]；t/exact_t/x/normal/gap/witness<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.entrance.shortest_exit` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_event_bindings.py::test_public_2d_event_fields_have_independent_extreme_scale_references`<br>`tests/test_r13fix_event_bindings.py::test_public_entrance_times_are_rounded_once_at_extreme_scales`<br>2^[-1070,0,1018]；t/exact_t/x/normal/gap/witness<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.entrance.first_entrance_brute` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel2d/exact.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel2d.exact.signed_area2` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.convexity_violation` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.is_convex_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ExactFacet.label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ExactFacet.start` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ExactFacet.direction` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ExactEntranceBlock.vertices` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ExactEntranceBlock.facets` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ExactEntranceBlock.pairs` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.entrance_block_exact` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.strict_vertices` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.hull_exact` | 坐标/拓扑选择器；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.hull_exact_fr` | 坐标/拓扑选择器；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.membership_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.convex_overlap_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.vertex_side_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ve_side_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.ev_side_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.polygons_overlap_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.exact.entrance_membership_exact` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel2d/g0.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel2d.g0.G0Report.samples` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.band_skipped` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.mismatches` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.facet_local` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.facet_global` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.facet_symmetric_diff` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.facet_ambiguous` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.hull_vertex_mismatch` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.hull_vertex_ambiguous` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.boundary_probes` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.G0Report.passed` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.char_length` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.sample_translations` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.g0_convex` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.brute_polygon_distance` | 参考/验证API（非生产主构造）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_2d_cover_fields_match_exact_projection_and_gap`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.g0.DistanceReport.draws` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.DistanceReport.overlapping` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.DistanceReport.touching` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.DistanceReport.samples` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.DistanceReport.worst_abs_error` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.DistanceReport.failures` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.DistanceReport.passed` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.g0_distance_completeness` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.brute_ray_exit` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.ExitReport.draws` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.ExitReport.separated` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.ExitReport.touching` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.ExitReport.samples` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.ExitReport.worst_witness` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.ExitReport.failures` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.ExitReport.passed` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.g0_exit_completeness` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0.random_convex_polygon` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel2d/g0_oracle.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel2d.g0_oracle.sqrt_display` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.points` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.translate` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.turn` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.on_segment` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.inside` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.overlap` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.segment_square` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.distance` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.boundary_has_exterior` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.g0_oracle.ray_exit` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel2d/geom.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel2d.geom.coord_scale` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.round_floor` | 数值诊断/近似报告构造；新增范围门；差分网格待补 | `tests/test_r13fix_geometry_differential.py::test_absolute_noise_diagnostic_rejects_unrepresentable_nonzero`<br>minsub输入不可表达非零输出必须拒绝<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.eff_tol` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.angle_floor` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.sub` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>仅all-float最终坐标范围检查；Fraction/Dual/混合类型保留原代数合同 |
| `kernel2d.geom.add` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>仅all-float最终坐标范围检查；Fraction/Dual/混合类型保留原代数合同 |
| `kernel2d.geom.neg` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.dot` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_dot_cross_round_after_cancellation`<br>`tests/test_r13fix_geometry_differential.py::test_public_dot_cross_reject_unrepresentable_nonzero`<br>输入2^-538/1/2^1020；最终minsub/0/普通；只改全float路径<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.cross` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_dot_cross_round_after_cancellation`<br>`tests/test_r13fix_geometry_differential.py::test_public_dot_cross_reject_unrepresentable_nonzero`<br>输入2^-538/1/2^1020；最终minsub/0/普通；只改全float路径<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.norm` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.unit` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.signed_area` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_area_turn_side_match_exact_shoelace`<br>2^[-537,-530,0,500,509]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.is_ccw` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.ensure_ccw` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.edge` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.outward_normal` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.zero_length_edges` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.vertex_turn` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_area_turn_side_match_exact_shoelace`<br>2^[-537,-530,0,500,509]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.turn_angle` | 数值构造/混合输出（需有独立逐值门）；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel2d.geom.turn_floor` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.is_convex` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.reflex_vertices` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.point_side` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_area_turn_side_match_exact_shoelace`<br>2^[-537,-530,0,500,509]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.point_in_polygon` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.segments_properly_cross` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.centroid` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_area_turn_side_match_exact_shoelace`<br>2^[-537,-530,0,500,509]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel2d.geom.orient2d` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.interior_point` | 数值构造/混合输出（需有独立逐值门）；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel2d.geom.triangulate` | 坐标/拓扑选择器；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.polygons_overlap` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.translate` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>all-float路径；混合类型未做全范围保证 |
| `kernel2d.geom.reflect` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel2d.geom.convex_hull` | 坐标/拓扑选择器；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |

### `src/eab/kernel3d/covers3.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.covers3.Cover3.kind` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.a_feature` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.b_feature` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.gap` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.point_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.point_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.params` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.area` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.strict` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.in_extent` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.exact_gap_squared` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.exact_gap_sign` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.exact_area_squared` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.exact_normal_direction` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.exact_params` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.Cover3.label` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.vertex_cone_contains` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.edge_arc_contains` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.cone_constraints` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.closest_point_of_convex_hull_to_origin` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_3d_closest_point_and_distance_constructions`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.cone_relint_direction` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_3d_closest_point_and_distance_constructions`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.cone_intersection_margin` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.cones_intersect_relint` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.vf_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_all_six_public_3d_cover_constructors_compare_every_numeric_field`<br>2^[-1070,-537,0,509,1018]，各向异性保持面面积可表达<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.fv_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_all_six_public_3d_cover_constructors_compare_every_numeric_field`<br>2^[-1070,-537,0,509,1018]，各向异性保持面面积可表达<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.ee_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_all_six_public_3d_cover_constructors_compare_every_numeric_field`<br>2^[-1070,-537,0,509,1018]，各向异性保持面面积可表达<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.ve3_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_all_six_public_3d_cover_constructors_compare_every_numeric_field`<br>2^[-1070,-537,0,509,1018]，各向异性保持面面积可表达<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.ev3_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_all_six_public_3d_cover_constructors_compare_every_numeric_field`<br>2^[-1070,-537,0,509,1018]，各向异性保持面面积可表达<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.vv3_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_all_six_public_3d_cover_constructors_compare_every_numeric_field`<br>2^[-1070,-537,0,509,1018]，各向异性保持面面积可表达<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.covers3.enumerate_covers3` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.local_facets3` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.covers3.facet_plane3` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_facet_normal_and_support_gap_are_independently_derived`<br>2^[-1070,0,1018]<br>逐gap和方向核对；facet支持恒等式以生产方向为候选，未独立证明全部方向枚举 |
| `kernel3d.covers3.facet_normal3` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_facet_normal_and_support_gap_are_independently_derived`<br>2^[-1070,0,1018]<br>逐gap和方向核对；facet支持恒等式以生产方向为候选，未独立证明全部方向枚举 |
| `kernel3d.covers3.facet_gap3` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_facet_normal_and_support_gap_are_independently_derived`<br>2^[-1070,0,1018]<br>逐gap和方向核对；facet支持恒等式以生产方向为候选，未独立证明全部方向枚举 |
| `kernel3d.covers3.support_gaps3` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_facet_normal_and_support_gap_are_independently_derived`<br>2^[-1070,0,1018]<br>逐gap和方向核对；facet支持恒等式以生产方向为候选，未独立证明全部方向枚举 |
| `kernel3d.covers3.membership_convex3` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/entrance3.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.entrance3.Entrance3.kind` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.t` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.x` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.point_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.point_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.gap` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.tied_labels` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.members` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.n_candidates` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.exact_t` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.surface_label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.Entrance3.surface_members` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.merge_degenerate` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.entrance3.first_entrance3` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_event_bindings.py::test_public_3d_entrance_fields_have_independent_extreme_scale_references`<br>`tests/test_r13fix_event_bindings.py::test_public_entrance_times_are_rounded_once_at_extreme_scales`<br>2^[-1070,0,1018]；各向异性面积可表达<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.entrance3.shortest_exit3` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_event_bindings.py::test_public_3d_exit_fields_have_independent_extreme_scale_references`<br>2^[-1070,0,508]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.entrance3.first_entrance_brute` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/entrance_topology.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.entrance_topology.entrance_membership3` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/exact_geom.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.exact_geom.vector` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.sub` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.add` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.mul` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.dot` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.cross` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.normal` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.orient2` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.polygon_locate` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.polygon_locate_fraction` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.triangle_locate` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.triangulate` | 坐标/拓扑选择器；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.triangles` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.segment_triangle` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.point_in_surface` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.segment_crosses` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.segment_distance_squared` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_3d_closest_point_and_distance_constructions`<br>2^[-1070,0,1018]，Fraction平方输出<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.exact_geom.triangle_intersection` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_geom.point_segment_distance_squared` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_3d_closest_point_and_distance_constructions`<br>2^[-1070,0,1018]，Fraction平方输出<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.exact_geom.point_triangle_distance_squared` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_3d_closest_point_and_distance_constructions`<br>2^[-1070,0,1018]，Fraction平方输出<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.exact_geom.surface_overlap` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/exact_sweep.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.exact_sweep.SurfaceEvent.time` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_sweep.SurfaceEvent.label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_sweep.SurfaceEvent.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_sweep.translate_exact` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_sweep.surface_events` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_sweep.star_core` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.exact_sweep.contact_models` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/frozen.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.frozen.face_normal_generic` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_face_edge_normals_and_frozen_lift_have_independent_extreme_jets`<br>2^[-1074,-600,0,600,1018]；非零方向导数<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.frozen.ee_normal_generic` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_face_edge_normals_and_frozen_lift_have_independent_extreme_jets`<br>2^[-1074,-600,0,600,1018]；非零方向导数<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.frozen.frozen_ee_sign` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.frozen.frozen_normal` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_frozen_public_gap_normal_and_jets_match_rational_values`<br>2^[-1074,-600,0,600,1018]；6kind值与导数<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.frozen.frozen_gap` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_frozen_public_gap_normal_and_jets_match_rational_values`<br>2^[-1074,-600,0,600,1018]；6kind值与导数<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.frozen.frozen_lift` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_face_edge_normals_and_frozen_lift_have_independent_extreme_jets`<br>2^[-1074,-600,0,600,1018]；非零方向导数<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |

### `src/eab/kernel3d/g03.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.g03.G0Report3.samples` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.band_skipped` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.mismatches` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.facet_local` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.facet_global` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.facet_degenerate` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.facet_ambiguous` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.facet_local_dropped` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.facet_symmetric_diff` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.hull_vertex_mismatch` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.hull_vertices` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.e_vertices` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.e_vertices_ambiguous` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.boundary_probes` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.boundary_checked` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.boundary_kinds` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.G0Report3.passed` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.facet_vote3` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.sample_translations3` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.g0_convex3` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.DistanceReport3.samples` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.DistanceReport3.skipped_intersecting` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.DistanceReport3.worst_abs_error` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.DistanceReport3.failures` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.DistanceReport3.completeness_failures` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.DistanceReport3.construction_failures` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.DistanceReport3.passed` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03.g0_distance_completeness3` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/g03_exact.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.g03_exact.qpoint` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.minus` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.scalar` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.wedge` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.volume` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.dimension` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.plane_key` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.planar_ring` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.hull` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.difference_hull` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.sat_model` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.overlap` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.boundary_probes` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_exact.support_labels` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/g03_surface_oracle.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.g03_surface_oracle.minus` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.dot` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.cross` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.bounds` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.boxes_disjoint` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.face_pieces` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.model` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.in_face` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.contains` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.segment_face_hits` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.g03_surface_oracle.separated_distance` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/geom3.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.geom3.noise_floor` | 数值诊断/近似报告构造；新增范围门；差分网格待补 | `tests/test_r13fix_geometry_differential.py::test_absolute_noise_diagnostic_rejects_unrepresentable_nonzero`<br>minsub输入不可表达非零输出必须拒绝<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.coord_scale` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.sub` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>仅all-float最终坐标范围检查；Fraction/Dual/混合类型保留原代数合同 |
| `kernel3d.geom3.add` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>仅all-float最终坐标范围检查；Fraction/Dual/混合类型保留原代数合同 |
| `kernel3d.geom3.neg` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.mul` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>all-float路径；translated的既有mixed Fraction精确保留合同不变 |
| `kernel3d.geom3.dot` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_dot_cross_round_after_cancellation`<br>`tests/test_r13fix_geometry_differential.py::test_public_dot_cross_reject_unrepresentable_nonzero`<br>输入2^-538/1/2^1020；最终minsub/0/普通；只改全float路径<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.cross` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_dot_cross_round_after_cancellation`<br>`tests/test_r13fix_geometry_differential.py::test_public_dot_cross_reject_unrepresentable_nonzero`<br>输入2^-538/1/2^1020；最终minsub/0/普通；只改全float路径<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.norm` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.unit` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.angle_between` | 数值构造/混合输出（需有独立逐值门）；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel3d.geom3.Polyhedron.verts` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.faces` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.source_vertices` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.source_faces` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.metrics` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.edge_noise` | 数值诊断/近似报告构造；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_relative_noise_diagnostics_do_not_round_away_scale_before_ratio`<br>2^[-1070,-600,0,600,1018]<br>面噪声模型使用逐边已舍入长度的有理和；不是多根式正确舍入承诺 |
| `kernel3d.geom3.Polyhedron.face_noise` | 数值诊断/近似报告构造；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_relative_noise_diagnostics_do_not_round_away_scale_before_ratio`<br>2^[-1070,-600,0,600,1018]<br>面噪声模型使用逐边已舍入长度的有理和；不是多根式正确舍入承诺 |
| `kernel3d.geom3.Polyhedron.dihedral_noise` | 数值诊断/近似报告构造；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_relative_noise_diagnostics_do_not_round_away_scale_before_ratio`<br>2^[-1070,-600,0,600,1018]<br>面噪声模型使用逐边已舍入长度的有理和；不是多根式正确舍入承诺 |
| `kernel3d.geom3.Polyhedron.face_normal` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.Polyhedron.face_area` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_area_turn_side_match_exact_shoelace`<br>`tests/test_r13fix_geometry_differential.py::test_public_face_area_at_overflow_edge_rounds_final_area`<br>2^[-537,-530,0,500,509]；area=2^1023<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.Polyhedron.edges` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.vertex_faces` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.edge_faces` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.edge_traversals` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.vertex_edge_dirs` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.Polyhedron.vertex_edges` | 数据访问/结构变换；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_relative_noise_diagnostics_do_not_round_away_scale_before_ratio`<br>2^[-1070,-600,0,600,1018]<br>面噪声模型使用逐边已舍入长度的有理和；不是多根式正确舍入承诺 |
| `kernel3d.geom3.Polyhedron.edge_dir` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_norm_normal_and_edge_components_match_rational_reference`<br>2^[-1070,-600,0,600,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.Polyhedron.dihedral_turn` | 数值构造/混合输出（需有独立逐值门）；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel3d.geom3.Polyhedron.volume` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_volume_and_centroid_match_independent_tetrahedral_moments`<br>2^[-359,-350,0,330,338]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.Polyhedron.centroid` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_volume_and_centroid_match_independent_tetrahedral_moments`<br>2^[-359,-350,0,330,338]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.Polyhedron.interior_point` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.aabb` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.translated` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>all-float路径；translated的既有mixed Fraction精确保留合同不变 |
| `kernel3d.geom3.Polyhedron.reflected` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.manifold_issues` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.is_convex` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.Polyhedron.reflex_edges` | 数据访问/结构变换；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.face_polygon_locate` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.point_in_face_polygon` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.point_in_polyhedron` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.segment_crosses_face` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.polyhedra_overlap` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.brute_feature_distance` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_3d_closest_point_and_distance_constructions`<br>2^[-1070,0,1018]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.geom3.box` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_match_independent_components`<br>`tests/test_r13fix_geometry_differential.py::test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs`<br>2^[-1074,-600,0,600,1021]；max范围外<br>all-float路径；translated的既有mixed Fraction精确保留合同不变 |
| `kernel3d.geom3.tetra` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.convex_hull_3d` | 坐标/拓扑选择器；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel3d.geom3.convex_hull_3d_eps` | 坐标/拓扑选择器；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel3d.geom3.merge_coplanar` | 坐标/拓扑选择器；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel3d.geom3.exact_vector` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.exact_edge_vector` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.exact_face_normal` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.exact_surface` | 坐标/拓扑选择器；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel3d.geom3.exact_convex_view` | 坐标/拓扑选择器；新增有限差分门；完整网格待补 | `tests/test_r13fix_geometry_differential.py::test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates`<br>2^[-1070,0,1018]<br>角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果 |
| `kernel3d.geom3.exact_point_in_polyhedron` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.exact_segment_crosses_face` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.exact_point_in_convex_polyhedron` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.exact_convex_overlap` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.geom3.exact_triangle_intersection` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/kernel3d/interlock.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `kernel3d.interlock.escape_height_brute` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_event_bindings.py::test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots`<br>2^[-1070,0,1018]乘3/4与1/3<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.interlock.EscapeSolution.height` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.cover_label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.n_candidates` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.tied_labels` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.exact_height` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.exact_offset` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.interval_certificate` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.nonpenetrating_state` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.window_core` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.exact_contact_label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.EscapeSolution.exact_contact_normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `kernel3d.interlock.escape_candidates` | 数值构造/混合输出（需有独立逐值门）；新增有限差分门；完整网格待补 | `tests/test_r13fix_event_bindings.py::test_nominal_candidates_and_profile_have_valuewise_extreme_scale_references`<br>2^[-1070,0,1018]<br>profile仅平坦导数0；nominal候选容许抑制，非完整保证 |
| `kernel3d.interlock.escape_height_covers` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_event_bindings.py::test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots`<br>2^[-1070,0,1018]乘3/4与1/3<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.interlock.escape_height_from_frozen_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_event_bindings.py::test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots`<br>2^[-1070,0,1018]乘3/4与1/3<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `kernel3d.interlock.dilatancy_profile` | 数值构造/混合输出（需有独立逐值门）；新增有限差分门；完整网格待补 | `tests/test_r13fix_event_bindings.py::test_nominal_candidates_and_profile_have_valuewise_extreme_scale_references`<br>2^[-1070,0,1018]<br>profile仅平坦导数0；nominal候选容许抑制，非完整保证 |

### `src/eab/limit.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `limit.wrench` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_wrench_and_power_each_value_matches_rational_reference`<br>2^[-1074,-600,0,600,1022]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `limit.friction_generators` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_friction_generators_round_complete_component`<br>`tests/test_r13fix_mechanics_differential.py::test_public_3d_friction_generators_follow_exact_given_coefficient_model`<br>mu=minsub/0.5/nextafter(1,0)/2^1022；3D两k×四mu<br>二维完整分量公式；三维按给定libm系数模型逐棱分量，不承诺真超越函数正确舍入 |
| `limit.LimitContact.point` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitContact.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitContact.mu` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitContact.cohesion` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitContact.area` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitContact.label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitContact.tangent` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.contacts_from_covers` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.status` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.alpha` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.lambdas` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.mechanism` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.contact_forces` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.active` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.iterations` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.row_duals` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.uncertainty` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.resolvability` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.LimitResult.resolvability_statuses` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.limit_load` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_limit_single_and_multi_match_analytic_sliding_capacity`<br>2^[-1073,-600,0,600,1021]<br>独立解析滑移承载族，不覆盖所有活跃集 |
| `limit.mechanism_power` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_wrench_and_power_each_value_matches_rational_reference`<br>2^[-1074,-600,0,600,1022]<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `limit.mechanism_is_admissible` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit.check_duality` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/limit_multi.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `limit_multi.LimitBody.dead` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.LimitBody.live` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.LimitBody.label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.BodyContact.contact` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.BodyContact.body_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.BodyContact.body_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.status` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.alpha` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.lambdas` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.mechanisms` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.contact_forces` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.active` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.iterations` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.row_duals` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.uncertainty` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.resolvability` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.MultiLimitResult.resolvability_statuses` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.contacts_from_covers_multi` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.limit_load_multi` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_limit_single_and_multi_match_analytic_sliding_capacity`<br>2^[-1073,-600,0,600,1021]<br>独立解析滑移承载族，不覆盖所有多体活跃集 |
| `limit_multi.check_duality_multi` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `limit_multi.mechanism_is_admissible_multi` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/lp.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `lp.LPResult.status` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.x` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.obj` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.y` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.iterations` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.basis` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.ray` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.exact_x` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.LPResult.exact_y` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `lp.solve` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_lp_views_are_bound_to_independent_exact_solution`<br>2^[-1075,-1074,-600,0,600,1023,1024]<br>非对称唯一2x2原始/对偶，每个显示字段与精确解绑定 |
| `lp.maximize` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_lp_views_are_bound_to_independent_exact_solution`<br>2^[-1075,-1074,-600,0,600,1023,1024]<br>非对称唯一2x2原始/对偶，每个显示字段与精确解绑定 |

### `src/eab/margin.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `margin.characteristic_length` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.coordinate_magnitude` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.rounding_floor` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.effective_geom_tol` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.cover_witness` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.contact_resolution` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.body_distance` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_margin_public_distance_projection_normal_and_gap_are_value_bound`<br>2^[-1074,-600,0,600,1018]<br>闭盒保单位面积；点凸包3-4-5独立投影 |
| `margin.MarginContact.label` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.distance` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.margin_gap` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.normal` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.point_a` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.point_b` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.exact_distance_squared` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.exact_normal_direction` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.MarginContact.closed` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.margin_contacts` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_margin_public_distance_projection_normal_and_gap_are_value_bound`<br>2^[-1074,-600,0,600,1018]<br>闭盒保单位面积；点凸包3-4-5独立投影 |
| `margin.boundary_band` | 数值诊断/近似报告构造；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.inflated_membership` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.entrance_block_convex` | 数值构造/混合输出（需有独立逐值门）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `margin.nearest_point_on_convex_entrance` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_margin_public_distance_projection_normal_and_gap_are_value_bound`<br>2^[-1074,-600,0,600,1018]<br>闭盒保单位面积；点凸包3-4-5独立投影 |
| `margin.distance_to_convex_entrance` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_margin_public_distance_projection_normal_and_gap_are_value_bound`<br>2^[-1074,-600,0,600,1018]<br>闭盒保单位面积；点凸包3-4-5独立投影 |
| `margin.inflated_normal` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_margin_public_distance_projection_normal_and_gap_are_value_bound`<br>2^[-1074,-600,0,600,1018]<br>闭盒保单位面积；点凸包3-4-5独立投影 |
| `margin.margin_gap_from_frozen_cover` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_frozen_margin_differential.py::test_margin_public_distance_projection_normal_and_gap_are_value_bound`<br>2^[-1074,-600,0,600,1018]<br>闭盒保单位面积；点凸包3-4-5独立投影 |

### `src/eab/oracle_construction.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `oracle_construction.scalar_exact` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `oracle_construction.ratio_exact` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `oracle_construction.vector_exact` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `oracle_construction.sqrt_exact` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `oracle_construction.norm_exact` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `oracle_construction.unit_exact` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `oracle_construction.assert_sqrt_rounding` | 参考/验证API（非生产主构造）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/predicates.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `predicates.cross2_sign` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `predicates.dot2_sign` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `predicates.orient3d_fraction` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `predicates.orient3d` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/rational3.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `rational3.fraction_vectors` | 判据/离散标签；非浮点主构造；已有契约/拓扑门另审 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `rational3.dot` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_rational3_polynomials_do_not_use_a_display_as_input`<br>2^[-1074,-600,0,600,1022]；精确有理多项式<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |
| `rational3.cross` | 数值构造/混合输出（需有独立逐值门）；新增差分门 | `tests/test_r13fix_mechanics_differential.py::test_public_rational3_polynomials_do_not_use_a_display_as_input`<br>2^[-1074,-600,0,600,1022]；精确有理多项式<br>独立有理公式逐值核对；有限构造族，不等于全输入域证明 |

### `src/eab/readers/bdda3d.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `readers.bdda3d.record_from_entrance` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda3d.load_records` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/readers/bdda_df.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `readers.bdda_df.Df22Judgment.step` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.oc_iter` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.contact` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.mtype` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.m0_0` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.m0_prev` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.m0_new` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.o3` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.o4` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.t3` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.Df22Judgment.w0` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.read_contacts_csv` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.read_df18_csv` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.read_df22_csv` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.last_oc_judgments` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.read_verts_csv` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_df.load_records` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/readers/bdda_geom.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `readers.bdda_geom.BlockGeom.block` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.BlockGeom.poly` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.BlockGeom.vidx` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.BlockGeom.flipped` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.StepGeometry.step` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.StepGeometry.blocks` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.StepGeometry.alias` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.StepGeometry.canon` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.StepGeometry.vertex_block` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.StepGeometry.vertex_pos` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.strip_duplicate_vertices` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.bdda_geom.load_step_geometries` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |

### `src/eab/readers/tf_probe.py`

| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |
|---|---|---|
| `readers.tf_probe.PairStageRow.step` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.time` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.block_i` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.block_j` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.contact_start` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.contact_end` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.total_contacts` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.nn_count` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.ne_count` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.np_count` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.ee_count` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.PairStageRow.load_bucket` | 公开数据字段/返回记录契约；随所属构造返回逐字段审查；不得由字段名推定覆盖 | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.read_pair_stage` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
| `readers.tf_probe.load_records` | 读取/契约转换（数值字段仍需单独差分）；未确认完整独立极尺度差分门（缺口/待逐项审查） | —<br>未确认<br>本普查不把名称匹配或测试全绿当作该API的差分覆盖证明 |
