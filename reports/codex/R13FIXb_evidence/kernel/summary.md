# R13FIX-b kernel 分组证据

## 处置结论

旧 `public_api_inventory.json` 中，本组不含 `kernel2d/geom.py` 和 `kernel3d/geom3.py` 的未确认 callable 共 **77 项**：

- **57 项**有新公开调用、独立有理/解析参考、低/普通/高三档逐值门。
- **20 项**逐项审阅返回语句，证明只输出 bool、离散分类、源索引标签或组合计数，不产生数值构造量。
- 本组 callable 缺口 **0**。机读逐项证据见 [coverage.json](coverage.json)，不是按函数名称推断覆盖。

新门共 **64 格**，最后一次 `64 passed in 0.84s`。全仓四片由主代理单独收集；本文件不冒充全仓/G6结果。

## 支持域

1. 精确有理构造和纯组合判定保持原全有限域，不人为限制 ±400。
2. `exact_geom.sub/add/mul/dot/cross` 对含 builtin float 的 int/float/Fraction 表达式只在最终结果调用统一 `scalar_rational`；纯有理/整数和 Dual 原类型协议保留。实际精确表面算法公开入口 `normal/triangle_locate/point_segment_distance_squared/segment_triangle` 先转原坐标的 Fraction，不把舍入构造反馈判据。
3. `g0.random_convex_polygon` 采用主代理集中模块 `numeric_domain.check_input(scale,"random_convex_polygon.scale")`；正数尺度在 `[2^-400,2^400]`，每个随机坐标按给定 RNG binary64 draw 的精确仿射模型最终 RN。零/负尺度和点数少于 3 是输入错误，不是域外数值。
4. `g0.sample_translations` / `g03.sample_translations3` 对给定 RNG draw 用有理 bbox、padding、仿射表达式，最终一次 RN；不因 bbox 的浮点中间值拒绝可表达最终结果。
5. `g03_surface_oracle.model` 是显式的清分母 **integer payload** 入口；三档为 integer 1 / 7 / 2^397。其下游公开包装 `separated_distance` 另以 2^-400 / 1 / 2^397 的有理坐标测清分母与距离。
6. `first_entrance_brute` 是共享生产重叠谓词的抽样佐证，不是独立 oracle。3D 修为精确有理平移、零隐式厚度、直到上下界 float 显示相同或相邻的有理二分；在扫描已分辨首个相交区间前提下返回至多一个 ulp 的上界。孤立切触或比采样步长窄的穿越仍可能漏，不改变原“采样佐证”的限制。

## 域内真错及最小修复

| 问题 | 修复 | 红/绿证据 |
|---|---|---|
| `exact_geom.segment_triangle` raw float 在 2^-400 和 2^397 真交点返回 None，普通档 t=1/3 被提前舍入 | 入口转原坐标 Fraction；相关精确入口同族补强 | before.log / final_numeric.log |
| 2D G0 的 turn/segment_square、3D G0 的 minus/scalar/wedge/cross raw float 路径提前舍入，整数原语被原始浮点污染 | 仅 raw float lift；保留整型内部路径，segment_square 在除法前精确化 | before.log / final_numeric.log |
| 2D/3D bbox 随机采样中间界与仿射表达式早舍入 | 精确 bbox 与 padding，RNG 值转 Fraction，仅最终 RN | before.log / mutation_sampler_bounds_early.log |
| 3D brute entrance 真 t=3，低/普给 2.999999996…（隐式加厚），高档给 3.5（长度L误作时间终止尺度） | 全有理位形、无隐式加厚、binary64相邻区间终止 | brute_before.log / final_numeric.log |
| 公共 raw dot 的可表达相消残差可被早乘舍入成0 | exact_geom builtin float/mixed 单表达式最终RN | mutant_raw_dot_early.log |

普通 raw float 数值语义依旧兼容旧门，未放宽 `test_e5a2_integer_arithmetic.py`：与新门合跑 `55 passed in 1.28s`（当时新门30格）。

## 实际变异与红断言审阅

全部变异只在隔离 pytest 子进程中重编译目标函数，不改生产文件；不是构造输出后追加伪数据。表内每项对应三档失败。

| 变异 | 内部位置 | 实际红断言原因 |
|---|---|---|
| raw_dot_early | `exact_geom.dot` 恢复原始float乘法后才包Fraction | `actual == float(exact_reference)`：0 对精确可表达正残差 |
| oracle_scalar_early | `g03_exact.scalar` 将有理内积经float重包 | 逐值 Fraction 内积不等，非容差/择顶点断言 |
| projection_parameter_early | `g0_oracle.segment_square` 先float(t)再算足点 | 精确有理 t 和平方距离均不等；修正门使 t 不恰巧二进制可表达 |
| sampler_bounds_early | `g0.sample_translations` 恢复rng.uniform(float(bounds)) | 独立有理仿射坐标差 1 ulp |
| translated_coordinate_early | `exact_sweep.translate_exact` 位移后先float | 每个精确坐标不等 |
| event_time_early | `_events_cached` 写入 SurfaceEvent 前float(t) | {2/21,11/21,20/21} 精确时刻集合不等 |
| area_coordinate_early | `exact.signed_area2` 先舍入P坐标 | 双面积与独立shoelace有理值不等 |
| support_check_removed | `g0.random_convex_polygon` 删除集中check_input | 两个正域外格在应抛异常的断言上 `DID NOT RAISE`；负域外格失去专门异常而进入普通输入拒绝 |

详情：[mutations.json](mutations.json)、[run_mutations.py](run_mutations.py)。**8 / 8 杀死，0 存活**。

## 文件范围

生产改动仅：
- `src/eab/kernel2d/g0.py`
- `src/eab/kernel2d/g0_oracle.py`
- `src/eab/kernel3d/entrance3.py`
- `src/eab/kernel3d/exact_geom.py`
- `src/eab/kernel3d/g03.py`
- `src/eab/kernel3d/g03_exact.py`
- `src/eab/kernel3d/g03_surface_oracle.py`

新增门：`tests/test_r13fixb_kernel_numeric.py`。未改中央模块、静态政策或两份 geom 文件（由主代理负责）。未访问姊妹仓库写路径，未做 git 写操作。

## 信任边界/遗留

- 这些是有限、明确解析输入族的逐值门，不是所有几何形状的数学完备证明。
- G0 报告门核对完整正常返回字段；facet_vote3 另覆盖可独立推导的异常 plane payload，未冒充一般随机失效报告全覆盖。
- 3D 单盒枚举族覆盖5种非空返回类型；VV3 的公共构造已有 R13FIX 独立门。本组对原未确认 `enumerate_covers3` 已核对全部返回盖的每个数值/证书；不声称该盒族覆盖所有拓扑。
- 支持域检查/专门异常在中央模块与共享构造器的完整收口、静态0违例、全套4片和canon指针由主代理汇总。

## 冻结后定向回归

`python -X utf8 -m pytest -q tests/test_r13fixb_kernel_numeric.py tests/test_e5a2_integer_arithmetic.py tests/test_kernel2d_g0.py tests/test_entrance3_exact.py --tb=short`

末行：`251 passed in 54.40s`。见 [regression.log](regression.log)。首次回归命令曾误写不存在的 `test_kernel2d_g0_exact.py`，属命令输入错误；确认实际文件名后以上命令重跑成功，未修改测试放宽门。

## 交叉审查追加（取代前述 64 格与 8 变异计数）

审查者正确指出：正常报告全0/空failure不能证明非零diagnostics数值；事件时刻集合不能证明label→time绑定。现只新增测试和证据，生产文件未改。

- `test_2d_g0_nonzero_diagnostics_and_failure_payload_are_independent`：内部 `_project` 的足点表达式减 s，**在 Cover 构造和真实枚举之前注入**，不篡改报告输出。解析内嵌矩形给distance truth=3s、got=4s、worst_abs_error=s，非空failure中x、got、truth及精确投影1/3显示全部逐值；exit给t=1、worst_witness=s和完整非空failure逐值。三档2^-400/1/2^397。
- `test_3d_g0_nonzero_diagnostics_and_failure_payload_are_independent`：内部 `_float_vector` 表达式x减s，嵌套yz盒保证最近精确候选仍是VF、平方9s²；报告got=4s、truth=3s、worst=s，非空 `failures` 与 `construction_failures` 每字段逐值；`completeness_failures`应为空。三档2^-400/1/2^395，使所有输入坐标 <=24s<2^400。
- `test_surface_event_label_time_binding_matches_independent_xy_elimination`：不用被测几何原语，固定源盒环及其确定性三角索引，内联xy 2x2有理解及平行投影的端点事件，构建完整(label,time)集合并严格相等，不能跨标签互换时刻蒙混。
- 追加 `event_label_time_swap` 内部变异：在 `_events_cached` 写入SurfaceEvent前交换2/21和11/21；原时刻集合保持不变，法向不变；新绑定门三档全红（`assert actual==expected`），见 `mutant_event_label_time_swap.log`。

最终：**73 passed in 0.94s**，见 `cross_review_strengthening.log`；**9 / 9 内部变异杀死**，见更新后的 `mutations.json`。更新的 `coverage.json` 为上述4项逐条加入对应门和限制；57 differential / 20 nonconstructive / 0 gap。主代理可以基于最新冻结测试收集全仓节点。

### 交叉复核第二补强：非空 completeness_failures

新增三档 `test_3d_g0_nonempty_completeness_payload_matches_omitted_nearest_face`：在真实 `enumerate_covers3` 内 `vf_cover` 调用位置漏掉最近的face3，不在枚举输出后追加/删改记录，保留其它生产真实盖。独立Cartesian参考：真最近距离3s；漏最近面后，远面距离5s，最近边的(3s,4s)分量也给5s。因此完整逐值核对 `completeness_failures=[(x,25s²,9s²)]`，以及 `worst_abs_error=2s`、非空`failures`与`construction_failures`的(x,5s,3s)元组。三档2^-400/1/2^395，输入全在工程域内。

最新冻结结果：**76 passed in 0.98s**，`cross_review_strengthening.log`。`coverage.json` 中3D G0 API已追加具体新门引用与非空payload证据，覆盖计数仍57/20/0。

## 全套后旧内部变异工具迁移（R6/R7/R9）

主代理在首轮全套结束后授权，只修改3个旧test文件，先逐文件复制到 `kernel/before/`；不改生产、不改policy、不改原测试节点、参数尺度、主数值断言或预期AssertionError文本。

1. R6 `test_r6fix_mutation_rounding_squared_norm_is_caught`：旧注入 `math.sqrt(G.dot(a,a))` 中 G.dot 已升级为检查式精确构造，会在早平方2^-1200处响亮失败、遮挡原数值断言。改注入真正旧表达式 `math.sqrt(sum(x*x for x in a))`；实质仍是**在被测norm入口内部恢复早平方浮点下溢**。原 `representable-norm` 断言精准杀死它。
2. R7 `test_g6g08_internal_mutation_rounding_before_cross_product_is_caught`：原先仅把relative改float，后来调用新exact_geom.cross/mul守卫会先报域外，遮挡原轴积体积断言。改在 `_mass_properties` 的weight表达式内恢复每分量原始float乘/减的叉积；随后以Fraction封装**已经损坏**的中间值交给精确dot/moments。这不恢复丢失的信息，亦不产生伪记录；原`axis-product-volume`非零体积断言、-600尺度和异常期待完整保留。
3. R9 `test_normalized_difference_float_nn_mutant_hits_target_assertion`：生产已从 `Fraction(nn)` 迁为具名 `exact_input(nn,"normalized difference square")`，旧注入仅是字符串锚失效。锚改为当前该唯一call，替换为raw `nn`，实质仍是删除nn的精确化。原`normalized difference preserves representable root from float nn`数值断言精准杀死早舍入。

静态节点说明：R6新lambda中的`sum(x*x...)`是刻意坏实现，限于pytest猴补注入，不能列为获准生产构造；R7新增原始乘法仅位于注入源码字符串，不是生产执行路径；R9仅更新唯一精确化call的源码匹配字符串。原工具形态均已有，无需新增静态形态或扩张生产白名单。

三份**完整文件**验证：`98 passed in 0.95s`，见 `legacy_mutations_migrated.log`。AST审计确认所有原test函数名与参数化decorator不变，before/after SHA256见 `legacy_mutations_migration.json`。
