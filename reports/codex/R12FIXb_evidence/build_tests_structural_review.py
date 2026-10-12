"""Round-4 source-backed structural triage.  This is NOT policy approval."""
import ast
from collections import Counter
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy

BASE = Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):
    numerical = runpy.run_path(str(BASE / "build_tests_numerical_review.py"))
scopes = dict(numerical["scopes"])
rows = json.loads((BASE / "raw_scan_round4.json").read_text(encoding="utf-8"))
NUMERIC = {"closed-rounded-construction", "closed-unproved-arithmetic", "closed-reduction", "closed-rounded-call"}
selected = [r for r in rows if r["path"].startswith("tests/test_")
            and not r["path"].startswith("tests/test_perf_") and r["rule"] not in NUMERIC]


def add(file, names, kind, reason, action=None):
    for name in names.split():
        scopes["tests/" + file + ".py", name] = (kind, reason, action)


P = "SOURCE_PROOF_GAP"
I = "SUPPLIED_INPUT"
D = "DYNAMIC_NUMERIC_REWRITE"
M = "METADATA_OR_IO"
H = "MUTATION_HARNESS"
A = "LEGACY_APPROX"
T = "TEST_ASSERTION_PROTOCOL"

add("test_bb52_g1", "result", T, "pytest.fixture(scope=module) 缓存固定 seed/样本数的 BB52 审计报告；fixture 装饰器不转换数值标量，analyze 返回被断言的报告。")
add("test_bb52_g1", "_drop_vv _drop_cone_boundary _drop_ev _drop_ve_subset", H, "monkeypatch 在盖/法锥被测入口中故意丢盖或改边界符号；lambda/orig 动态调用是变异装置，错误实现应被现有牙检出，不能描述成安全构造。")
add("test_contact_record", "_rec", M, "base 是明确列出字段的 ContactRecord 夹具字典，kw 只覆盖给定字段；**base 是记录装包，不由显示几何量计算新距离。应精确建模 unpack 或改显式字段，而非放开任意 unpack。")
add("test_covers3_g0_vote2", "_random_pair _random_pair.rnd_hull", I, "固定 RNG 在 [-s,s] 采样顶点并求其 hull，s 也为给定随机尺度；只造给定试验输入，不将随机函数当精确数值 oracle。")
add("test_covers3_membership", "_pairs", I, "固定盒/四面体与 seed=11 的随机点 hull 组成试验块对，调用仅构造被测输入，不计算正确舍入 expected 距离。")
add("test_covers3_membership", "_assert_exact_facet_counts _assert_exact_rotated_vote_counts", T, "raw_support_classification/独立 Gordan ray oracle 给 expected；exact_convex_view 仅解码实际标签，最终比较整数集合/计数，不把显示法向回作期望构造。")
add("test_doc_pointers", "_files _resolve", M, "Path.rglob/parents/as_posix 和 dict setdefault/get 只检索文档引用文件名；返回路径或 None，不构造任何几何标量。")
add("test_e5a2_integer_arithmetic", "_fraction_membership", D, "point 用 map(F,point) 转有理，后续平面与 closest-hull 比较在 Fraction 域；确切已知 F 不是先舍入。但数值 map callable 应改显式 comprehension，不能为任意 map 开洞。")
add("test_e5a2_surface", "placed placed.transform", D, "transform 先 map(F,p)，随后给定 Fraction s/t 的 3-4-5 有理旋转与平移；应把已知 F 数值 map 改 comprehension，保留有理构造而非动态豁免。")
add("test_e5b_polyhedron_cache", "_noncanonical_translation_check", T, "显式改 verts 并检查 exact_convex_view 对象缓存失效和点成员性；这是被测 cache/invalidation 调用，修改后的坐标是实际输入，不是复用舍入输出作 oracle。")
add("test_e5b_triangle_boolean", "_feasible", D, "map(F,p) 后以有理 Gaussian 消元枚举共同重心可行性，未先舍入；已知数值 map 应直接化，不能宽泛豁免高阶数值函数。")
add("test_e5b_triangle_boolean", "_pairs _pairs.make", I, "rng.randrange 生成有理三角点，E.cross 仅 generator-only 拒绝共线输入（源码明确不定 expected）；yield 测试输入，后续 _feasible 独立判真值。")
add("test_e5b_triangle_boolean", "_endpoint_check", D, "map(E.vector,固定整数点) 将端点试验有理化，_feasible 给独立精确真值；map 数值 callable 可直接 comprehension 化，不该成为动态例外。")
add("test_edge_arc_per_side", "_chamfered_on_box", I, "移去角点/加入倒角，再用 yaw 生成实际给定几何；convex_hull/merge_coplanar 是夹具构造，非精确期望长度的重建。")
add("test_filtered_predicates", "test_orient3d_filter_has_a_real_fast_path", T, "ctor 仅遍历 (float,F)，输入只有0/1整数，转 float 精确；目的是确认相同单纯形两种给定类型走 filter 快路，并 monkeypatch Fraction fallback 为必错。仍应把两种构造写显式分支，不把任意 callable 转换放行。")
add("test_fixture_provenance", "_sha256 _check _fixture_files", M, "Path/文件 read/stat 与 hashlib update/hexdigest 核对夹具原字节；iter(lambda:fh.read(1<<20),b'') 是字节流迭代，无数值几何 callable 或开方数据流。")
add("test_frozen_lowdim", "_separated_draws", I, "rng.uniform 生成给定位移，用 polyhedra_overlap 仅筛选 separated 试验样本，返回坐标列表而非几何真值/构造 oracle。")
add("test_g03_two_rulers", "_chamfered_box _truncated_cube", I, "删除一个给定盒顶点，增加三组 e 偏移端点，再对实际点集 hull/merge；生成薄棱输入以压测门，不给出正确舍入距离 expected。")
add("test_g2_bdda3d", "_assert_g2_gate", T, "仅对 G2 报告的标签/计数/窗口字段做断言；G2_BAND 是长度常数而非 callable，closed-callable-value 为绑定类型误报，不应锁整个函数。")
add("test_g2_bdda3d", "_fake_case", H, "JSON 夹具经传入 mutate 做指定故障或单位变换后写到 tmp_path，供重新运行 G2；这是受控测试变异协议，不能当正常数值 callback 证明。")
add("test_g2_bdda3d", "_inject _vf _low_dim", H, "故意构造不存在的盖并包装枚举器，用于特定 compare/window 断言的牙；返回 make/lambda 是显式故障装置。该追加型牙不能替代穿过真实枚举器的内部变异主证据。")
add("test_g2_bdda3d", "_box_vf_oracle", A, "V.items 字典遍历遍历已知轴对齐顶点，计算 VF/FV 符号与容差级gap；此 oracle 使用 float 中点/差与1e-9比较，非正确舍入构造证明，方法调用本身仅取容器项。")
add("test_g2_bdda3d", "_scaled _moved", I, "d['verts'].items 遍历 JSON 顶点，按给定尺度或 R3/平移形成实际输入图像；不把这些 float 变换称为精确 oracle，items 自身不调用数值函数。")
add("test_g2_bdda3d", "_dup_append_moving _dup_host_face", I, "复制给定顶点并改整数 legacy 引用，append/list 只做 alias/topology 夹具，不求几何派生标量。")
add("test_geom3_e5a", "_map _placed", D, "map(F,p) 后全部有理 3/5、4/5、5/13、12/13 旋转及给定有理 scale/translation，精确保共面；把已知 F 数值 map 直接化即可，不能批准未知 callable。")
add("test_geom3_face_polygon", "Frame.poly", D, "self(p) 为 Frame.__call__ 的采样姿态变换，再包装 Polyhedron；当前对象 callable 协议超出可证明一阶形式，应改为显式 pt 方法/参数调用，不凭类名信任任意 self callable。")
add("test_geom3_merge", "_call_with_timeout _call_with_timeout.run", H, "fn(*args) 放入 daemon Thread，box_传值/异常并设置20秒死循环牙；这是通用超时测试执行协议，无法以源码静态证明任意 fn 数值安全。若保留需明确极小 harness 边界，不作数值豁免理由。")
add("test_hull_robustness", "_fr_orient", P, "F=Fraction 是固定类别名，四点逐分量有理化后 determinant 全有理；不是函数参数/callable容器。可直接写 Fraction 让绑定证明更透明。")
add("test_hull_robustness", "_assert_exact_hull", P, "set.issubset 核对输出顶点来自输入，_fr_orient 和有理法向行列式独立检查支持性/极点；容器方法与 combinations 不作浮点几何构造。")
add("test_hull_robustness", "_ridge_pair", I, "固定 roof 与三角针顶点定义实际试验输入，convex_hull_3d 在这些坐标上构造块体；不回收显示距离/法向。")
add("test_interlock_exact", "_wall", I, "W.random.Random 与 _place/_key/_prism_xz 生成固定seed、给定舍入扰动墙体；earliest_wall_escape 真值另从最终坐标有理求解。")
add("test_interlock_walls", "_place", I, "rng.randint 选整数ULP扰动叠加到旋转后给定坐标；这是故意生成末位差别输入，不能称其精确 affine，也不是距离 expected 构造。")
add("test_invariance_2d", "_T _floor_in_reference_units", D, "_T 返回捕获旋转/尺度/位移的 pt/vec/poly callable；floor 再从 tuple 取 poly 调用得到坐标噪声尺度。需改显式变换参数/一阶helper，不能用普通float采样理由豁免新的高阶形态。")
add("test_invariance_2d", "_g0_exact_affine _g0_exact_affine.vec _g0_exact_affine.poly", D, "系数先转 Fraction 后有理 affine，数值本身不先舍入；但返回 vec/poly callable 且 map(vec,P)/map(Fraction,p) 属高阶写法，应改一阶显式helper与comprehension。")
add("test_invariance_2d", "_reflex_truth", D, "map(Fraction,q) 转原始坐标，再以有理叉积和给定sin/cos阈值独立判 reflex；应直接化已知转换map，不批准任意 callable 流。")
add("test_invariance_geom", "_pair_generic _pair_ve3_wedge _pair_ridge_needle", I, "显式固定/RNG 点集生成一般位置、楔形与针棱输入，convex_hull/merge 只是实际给定形状构建，距离真值另算。")
add("test_invariance_geom", "_raw_coordinate_views", T, "canonical_view 从原始 verts/faces 独立算 expected，再 assert_raw_coordinate_view 比较被测 exact_convex_view；站点不是显示几何值再构造。")
add("test_invariance_interlock", "_ilock", I, "KW 是明确的 interlocking_pair 参数表，**KW 只传已知输入几何参数；后续 rigid 为给定位姿。应建模固定字典/改显式kwargs，不宽放任意 unpack。")
add("test_kernel2d_convex_ray_exact", "_sat_ray", D, "map(F,x/d) 后各 SAT 投影/速度/区间界全部 Fraction，已知 F 并无舍入；map 改显式 comprehension，保留精确射线 oracle。")
add("test_kernel2d_entrance_e3", "_sat_ray", D, "顶点、X和D有理化后求完整 SAT ray 区间，界值精确；结构拒绝来自 map(F,...) 应直接化，而非给数值高阶例外。")
add("test_kernel2d_covers_e3", "independent_cover_oracle.scan", P, "scan 用上层有理点集、独立 displacement/product/cone公式，out.add 只记录kind/i/j/strict标签；math.isinf 仅判window哨兵，无先舍入构造。")
add("test_kernel2d_entrance", "_random_convex", I, "rng.uniform 取样实际坐标再 convex_hull 构成测试输入，非正确舍入预期真值。")
add("test_kernel2d_predicates", "_grid_truth", D, "corners lambda 只生成整数格点集合，集合交决定精确polyomino真值；可直接改 def/comprehension，虽整数算术安全也不需动态例外。")
add("test_kernel2d_predicates", "_polyomino_pairs", I, "rng.randint 采样整数格点数量/平移；translate 输入由 scalar_exact(integer) 最终显示，整数格拓扑独立保留，不从显示差分求真值。")
add("test_kernel2d_review", "_random_simple_polygon", I, "rng.uniform 只生成给定点，Fraction副本用独立proper-cross筛掉自交；reversed 切片是点顺序置换，不数值舍入。")
add("test_kernel3d_covers", "_canon_pairs", I, "固定四面体/盒与seed=21随机hull形成试验输入，不作为正确舍入构造oracle。")
add("test_kernel3d_geom", "_placed_exact", P, "F=Fraction 固定类别名，每个 t/s/R/p 在乘加前 F 转换，完整 affine 有理；应修固定别名绑定或写 Fraction，而非动态函数许可。")
add("test_limit_exact_selfcheck", "q", D, "getattr(v,'exact',F(v)) 专门读取 exact-witness 扩展，存在即保留有理证书，否则有理化原始值；非数值反射调用，但可改明确类型/字段分支，不能泛化任意 getattr 安全。")
add("test_limit_exact_selfcheck", "test_exact_witness_is_preserved_by_copy_not_by_float_arithmetic", H, "float(r.alpha) 故意剥离 exact witness，测试明确要求后续 check_duality static_ok=False；这是正确性破坏牙，不是正常数值安全站点。")
add("test_limit_fuzz", "_exact_status_alpha", P, "_exact_limit_lp 按给定原始模型有理重建，_exact_max 独立精确求状态/目标，scalar_exact 仅最终显示obj；静态导入/参数传播缺口，不宜豁免。")
add("test_limit_fuzz", "_genuinely_unresolvable", A, "float范数仅定义输入扰动尺度，rng.choice扰动live后重新用独立精确LP判状态/目标变化；是敏感性/分辨率诊断，不能把float尺度当exact构造。")
add("test_limit_multi", "_mutant_module", H, "read_text/ModuleType/sys.modules/compile/exec 复制并内部替换被测 limit_multi 模块，保留package定位；这是真故障注入基础设施，不能当正常数值反射安全证明。")
add("test_lp", "test_weak_and_strong_duality", A, "red=c[j]-sum(y*A) 只作 reduced-cost >= -1e-7 最终容差断言；可能舍入但不再送入root/norm/unit/几何差分构造，不承担有理LP证书。")
add("test_lp_certificates", "_block", D, "mv/P lambda 捕获 R/off 生成给定接触/载荷位姿；确有float构造，闭式对照是历史容差试验。应改直接一阶helper，不能以测试身份豁免动态数值。")
add("test_lp_certificates", "_exact_limit_lp.shift", D, "X 是上层 lambda v:Fraction(v)，shift 将原荷载及给定参考原点有理化后独立叉积平移；数值精确但lambda别名应改Fraction直接调用。")
add("test_m4_bdda_adapter", "_window", M, "Bdda2DWindow 包装固定step与F(1,8)窗口，kwargs是明确测试参数覆盖；无先舍入几何派生，宜固定字段/建模已知解包，非任意kwargs例外。")
add("test_m4_bdda_adapter", "_key_from_label", M, "EV->VE交换递归只规范kind/block/vidx整数标签，返回身份key；不做数值几何构造。")
add("test_m4_bdda_shadow", "_digest _assert_baseline", M, "JSON规范序列化与SHA256核对差异报告，或比较整数计数/分类窗口字段；对象方法不计算新数值几何真值。")
add("test_m4_bdda_vv_reader", "_bb52_gate", T, "load_records 读取导出后筛VV并断言整数corner identity/raw_p2，非距离/法向构造。")
add("test_margin", "_true_normal", D, "_TRUE_INFLATED_NORMAL 是保存的被测函数别名，用字典缓存正常法向供Lipschitz故障对照；不能凭别名任意信任callback，应固定导入/直接helper或明确有限注入protocol。")
add("test_margin_resolution", "_needle _blunt_needle", I, "给定tip/r/H/e与固定角度只构造输入needle点集再hull，独立距离expected另算；不声称采样三角函数精确。")
add("test_r10_initial_boundary", "_pose", D, "map(F,v) 后3/5、4/5有理旋转与Fraction scale/shift精确保接触边界；map已知转换应直接化而非动态豁免。")
add("test_r10_initial_boundary", "_box _pair", P, "中心、符号顶点、交区间边界都先Fraction，pair独立数出退化维数；Polyhedron只包装有理坐标，不先舍入。")
add("test_r11fix_numeric_types", "_review_cases _mixed_bilinear_cases", I, "yield 只枚举明确int/float/Fraction原始类型与指数边界输入；ldexp/ulp给定可表示binary64值，不构造期望几何量，生成器语法可建模有限yield或改列表。")
add("test_r11fix_static_flow", "_assert_cone_rejected", H, "scan 参数是原scanner或内部变异scanner，在源码文本上运行并断言精确cone行的 rounded-vector 牙；是静态门自测协议而非数值callback。")
add("test_r12fix_static_closed", "_assert_closed_rejection", H, "scan 对植入源码返回诊断记录，此helper断言目标行/function/rule；处理的是源码与元数据，不执行未知数值构造。")
add("test_r6fix_construction", "_assert_current_margin_description", M, "splitlines/startswith 从文档抽状态行并核对测试指针/历史声称，纯文本无数值构造。")
add("test_r6fix_construction", "test_g6f06_gap_magnitude_gate_has_teeth", H, "lambda sqrt(float(value)) 刻意回滚到先舍入root，要求 representable signed gap 断言报红；保留牙，绝不能写为正常安全例外。")
add("test_r6fix_g2_oracle", "test_g2_oracle_early_square_rounding_mutation_is_caught", H, "monkeypatch distance_display 为 sqrt(float(squared)) 的显式错误，必须由最终距离正确舍入证书捕获。")
add("test_r6fix_dual_lp", "_mutant_function", H, "inspect.getsource/dedent/compile/exec 只生成内部缺陷函数供牙运行；function.__code__/__name__是定位元数据，非许可正常反射数值实现。")
add("test_r6fix_geom3", "_prism", D, "顶点先在Fraction affine域生成；floating分支map(scalar_exact,p)最后转成指定浮点输入图像以测精度边界。已知数值map应改comprehension，不扩大动态例外。")
add("test_r6fix_geom3", "_assert_returned_view_isolation _assert_face_hints_do_not_change_convex_membership _assert_exact_concavity", T, "对缓存隔离/face hints变化/有理凹性分别运行被测几何接口并断言；输入修改是测试协议，不以已显示距离建立expected。")
add("test_r7fix_docs", "_assert_current_status _assert_no_priority_advice", M, "splitlines/startswith只核对README/canon当前状态与撤回优先性用语，纯文本无数值构造。")
add("test_r8fix_gate_teeth", "convex_view_mutant reject_z_inside_cone_filter all_branch_convex_view_mutant", H, "获取被测源码、精确锚点替换并monkeypatch：丢顶点/改缓存标签/滤掉z轴等内部缺陷。反射/模块字典是变异安装协议，不能当正常数值安全豁免。")
add("test_r8fix_frozen", "test_contact_margin_postround_subtraction_mutant_is_caught.premature_round", H, "故意先sqrt_rational显示root、再减scalar_exact(offset)，重现margin末端差分提前舍入；这是明确植入的错误实现，必须由目标midpoint/cancellation牙报红，不能视为正常安全构造。")
add("test_r8fix_margin_gap_gate", "_arithmetic_fault_inside_margin_contacts", H, "把被测margin_contacts内部normalized_difference换成w-delta/漏delta/反号等错误；compile/exec与setattr为牙安装，保证这些先舍入/符号缺陷被目标断言检出。")
add("test_r8fix_wrench", "_oracle", D, "r逐坐标Fraction差，map(F,force)后叉积全有理；独立精确旋量oracle本身安全，但数值map要直接化，不给未知callable例外。")
add("test_r9fix_construction_rounding", "_certificate", P, "struct.pack/unpack只取得binary64末位奇偶，nextafter给相邻浮点，Fraction中点平方/幂精确验证最终舍入格；不是先舍入平方再开方。")
add("test_r9fix_cover_parameters", "_assert_parameters", D, "map(F,p) 后Gram determinant与EE/VE参数全有理；dot lambda只是已知精确乘积和，应改显式def，保留参数证书而不是许可新高阶形态。")
add("test_r9fix_docs", "_assert_route_is_explicit_history", M, "text.split 只截出路线标题区并核对历史状态免责声明，纯文本检查。")
add("test_r9fix_entrance_domain", "_finite_contact", D, "B的map(F,p)有理化与A有理平移后，on以精确叉积及区间比较判有限接触；数值map可直接化，不需豁免。")
add("test_r9fix_entrance_domain", "_assert_contact_labels", T, "独立_finite_contact逐标签核验被测tied_labels并要求见证重合；调用断言不把显示派生量流回新构造。")
add("test_r9fix_oracle_candidate", "_fresh_oracle_candidate_cache", M, "pytest autouse fixture在yield前后清 oracle LRU缓存，强制每条测试新鲜执行候选路径；cache_clear/fixture/yield不转数值。")
add("test_r9fix_solid_cones", "_roof _roof.transform", D, "map(F,p)之后给定Fraction scale/shift及3-4-5旋转有理；数值转换map应直接化，Polyhedron只装有理顶点。")
add("test_r9fix_topology", "_folded_roof _folded_roof.transform", D, "先用Fraction roof midpoint证明确凹性，map(F,p)后有理affine保持其结构；应直接化转换map，不依赖动态数值例外。")
add("test_readers_roundtrip", "_gate", T, "parse_again callback只复读夹具，JSON往返/validate/canonical_key/hash检测记录确定性和交换对称性；这是I/O/身份测试协议，不构造几何量。")
add("test_readers_roundtrip", "_assert_step_keys_unique _primary_unique_records", M, "canonical_key/dict.set_default分组整数身份标签并核对导出重复项，不算距离/法向，也不调用容器内的数值函数。")
add("test_readers_roundtrip", "_key_constant _key_ignores_features _key_not_swap_symmetric", H, "返回故意错误canonical_key lambda，分别制造常量碰撞/忽略feature/交换不对称；只用于身份牙，不是数值构造许可。")
add("test_readers_roundtrip", "_raw_contacts", M, "read/decode/replace/split独立读取CSV；int/scalar_exact仅把导出的标记字段转原始输入类型，最终比较整数身份，不重建几何派生量。")
add("test_tf_reader", "_raw_table _load _synthetic_probe", M, "TSV字节读写、split/join与reader加载供记录字段逐项核对；都是原始输入/文本协议，不是先舍入再开方等构造。")
add("test_tf_reader", "_mutant_reader", H, "复制reader到临时ModuleType并编译内部错误，再monkeypatch读取接口供字段牙；__file__/__dict__/模块反射是明确变异安装，非正常数值实现。")

# The same helper may have both a Lambda node and calls through that lambda.
# Classify the entire numerical helper honestly, not just the Lambda diagnostic.
for file, names in {
    "test_frozen_ee_sign": "_ridge_pair _wedge_pair",
    "test_interlocking": "_scaled_pair",
    "test_invariance_geom": "_base",
    "test_invariance_interlock": "_margin_ref",
    "test_invariance_limit": "_map_back",
    "test_lp_certificates": "_lock_case _si_case _exact_limit_lp _floor",
    "test_margin": "_lipschitz_worst _lipschitz_verdict",
    "test_margin_resolution": "_small_pair",
}.items():
    for name in names.split():
        key = "tests/" + file + ".py", name
        _, reason, _ = scopes[key]
        scopes[key] = (D, "源码仍包含数值lambda、传入callback或从注册表取出的数值构造器，需直接化而不是例外。" + reason, None)

# Certain structural findings have a narrower explanation than their containing
# numeric scope.  These overrides are based on the inspected syntax and body.
noncallable_constants = {"G2_BAND", "FACET_KINDS", "REL_GEOM_TOL", "OPTIMAL", "PENETRATING", "INSIDE", "OUTSIDE"}
actions = {
    P: "FIX_ANALYSIS_NO_WAIVER", I: "REVIEW_EXPLICIT_SUPPLIED_INPUT_BOUNDARY",
    D: "REWRITE_DYNAMIC_NUMERIC_NO_WAIVER", M: "REVIEW_NONNUMERIC_PROTOCOL_ONLY",
    H: "RETAIN_TARGETED_MUTATION_TOOTH_REVIEW_HARNESS_BOUNDARY",
    A: "REWRITE_OR_DOCUMENT_NONEXACT_DIAGNOSTIC", T: "FIX_ANALYSIS_OR_REVIEW_TEST_PROTOCOL_ONLY",
    "ACTUAL_BAD": "RETAIN_TARGETED_MUTATION_TOOTH_REVIEW_HARNESS_BOUNDARY",
}
out, seen, missing = [], set(), set()
for row in selected:
    key = tuple(row[k] for k in ("path", "function", "rule", "node"))
    if key in seen:
        continue
    seen.add(key)
    scope = row["path"], row["function"]
    if scope not in scopes:
        missing.add(scope)
        kind, reason, action = "UNRESOLVED", "该scope尚未完成逐站点审查，不批准任何例外。", "REVIEW_REQUIRED_NO_WAIVER"
    else:
        kind, reason, action = scopes[scope]
    if kind == "ACTUAL_BAD":
        kind = H
    source = row["source"]
    if row["rule"] == "closed-callable-value" and source in noncallable_constants:
        kind, action = P, None
        reason = "源码导入/定义的 " + source + " 是标量常数、枚举状态或标签集合，并未在该站点被调用；应修值类别误判，不为未知callable开洞。所在scope用途：" + reason
    elif row["rule"] == "closed-syntax" and row["node"].startswith("JoinedStr("):
        kind, action = M, None
        reason = "该f-string只生成接触label身份（例如c/l/r加整数i），未把格式化值转回数值；" + reason
    elif row["rule"] == "closed-modulo":
        kind, action = P, None
        reason = "(i+1)%n 的i来自range(n)、n来自len(section)，仅循环整数面索引，不是浮点取模；" + reason
    elif ("map(" in source or row["rule"] == "closed-callable-value" and source in {"F", "scalar_exact", "_fv", "vec", "pt", "poly", "P"}) and kind not in {M, H, T}:
        kind, action = D, None
        reason = "该数值callable/map/闭包传递应改直接调用或comprehension；不能为当前可理解对象扩成未知callable例外。" + reason
    elif row["rule"] == "closed-syntax" and row["node"].startswith("Lambda(") and kind not in {M, H}:
        kind, action = D, None
        reason = "数值lambda可改显式一阶def并传参，不应进例外；" + reason
    elif row["rule"] == "closed-unpacked-call" and kind not in {M, H}:
        action = "SIMPLIFY_OR_PROVE_FINITE_KEYWORD_UNPACK_NO_WAIVER"
        reason = "该调用仍需逐键证明实际kwargs或改显式参数；不因callee已知而自动认可任意unpack。" + reason
    out.append({**row, "disposition": kind, "reason": "站点 `" + source.replace("\n", " ") + "`：" + reason,
                "recommended_action": action or actions.get(kind, "REVIEW_REQUIRED_NO_WAIVER"), "waiver_approved": False})
assert not missing, sorted(missing)
payload = {
    "review_kind": "independent structural source review; NOT waiver approval",
    "input": "raw_scan_round4.json", "input_sha256": hashlib.sha256((BASE / "raw_scan_round4.json").read_bytes()).hexdigest(),
    "input_rows": len(selected), "unique_reviewed_sites": len(out),
    "category_counts": dict(Counter(r["disposition"] for r in out)),
    "action_counts": dict(Counter(r["recommended_action"] for r in out)),
    "limits": ["每站点都未自动批准waiver，最后必须交叉校验node/context与最新源码。",
               "已知Fraction/规范模块调用的证明缺口应修分析，而非用本表替代证明。",
               "数值map/lambda/高阶callable/unpack必须直接化或新增有限可证分析；不自动例外。",
               "显式变异harness与旧近似诊断各自单列；不是无先舍入的数值保证。"],
    "sites": out,
}
(BASE / "tests_structural_local_review.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in payload.items() if k != "sites"}, ensure_ascii=False, indent=2))
