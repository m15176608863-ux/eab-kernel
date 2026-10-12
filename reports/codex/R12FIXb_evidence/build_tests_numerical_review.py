"""Emit the independently source-reviewed round-2 triage, NOT a waiver manifest.

The scope-specific explanations below were written after reading their bodies and
call sites.  AST/source fields come from the frozen raw scan only for matching.
No review entry automatically approves a policy exception.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
rows = json.loads((BASE / "raw_scan_round2.json").read_text(encoding="utf-8"))
rules = {"closed-rounded-construction", "closed-unproved-arithmetic", "closed-reduction", "closed-rounded-call"}
selected = [r for r in rows if r["path"].startswith("tests/") and r["rule"] in rules]
scopes = {}


def add(file, names, disposition, reason, action=None):
    for name in names.split():
        key = ("tests/" + file + ".py", name)
        assert key not in scopes, key
        scopes[key] = (disposition, reason, action)


PROOF = "SOURCE_PROOF_GAP"
INPUT = "SUPPLIED_INPUT"
APPROX = "LEGACY_APPROX"
BAD = "ACTUAL_BAD"

# Exact scalar provenance: fix the analyzer, do not grant source-wide approval.
for f in ("e5a_cover_oracle", "perf_cover_oracle_reference"):
    add(f, "witness_distance", PROOF, "witness_points(..., exact=True) 返回有理数见证点；d 的分量是两个 Fraction 的差，norm_exact 才进行最后构造。不是先 float 差分再构造。")
for f in ("e5a_escape_oracle", "perf_escape_oracle_reference"):
    add(f, "_signed_gap", PROOF, "n 与 numerator 来自 q/model 有理几何；numerator²/dot(n,n) 保持 Fraction，sqrt_exact 是完整比值的最终显示。")
    add(f, "face_band", PROOF, "有理方向 d、偏移 w 和夹紧后的 Fraction 参数 t 构成 r=w-d*t；dot(r,r) 与 Fraction(extent)² 比较，不把浮点投影送入构造。")
    add(f, "facet", PROOF, "model 先有理化顶点；面投影或 EE Gram 参数 s,t 及 pa,pb 保持 Fraction；单位方向/显示 gap 与 exact_coefficients、extent_only 分支分离。列出的 scale/sub/dot 站点没有显示 float 回流。")
    add(f, "direction_noise", PROOF, "total=Fraction(ae)+Fraction(be)，方向平方与 nn 来自有理模型；整个 total²*|da|²*|db|²/nn 在 Fraction 域完成，sqrt_exact 最后显示噪声上界。")
    add(f, "_candidates", INPUT, "z 由 scalar_exact 最终取为一个可表示候选位移，再在该给定位置重建 model 并仅检查 facet extent；不声称候选二进制坐标等于未舍入的精确根，也不从舍入 gap 重建距离。")
add("e5a_g2_oracle", "construction", PROOF, "model 给出 Fraction 顶点；Gram 投影、s/t 和差向量均有理，distance_squared 保持精确；normal 与最终距离显示是独立末端分支，列出的 scale/add/sub/dot 不吃显示值。")
add("e5b_frozen_oracle", "_surface", PROOF, "顶点先转 Fraction；Newell normal、点与 origin 差以及标量积均有理，这里只是精确面平面证书。")
add("e5b_frozen_oracle", "distance_squared", PROOF, "_surface 提供 Fraction 三角面；_edge_edge_sq 使用有理段参数/平方差，min 保留精确平方距离，不在开方前转 float。")
add("perf_witness_reference", "reference_witness", PROOF, "方向键 key 是整数规范方向，a 为有理 cell 顶点；dot(key,a) 是精确切平面常数，不是显示见证点的差分。")
add("test_e5a2_integer_arithmetic", "_fraction_rows", PROOF, "q 顶点和 Fraction 叉积形成方向 n；axes.add(n) 只把有理/整数方向放入集合，容器操作不产生舍入。")
add("test_e5a2_integer_arithmetic", "_eager_ee", PROOF, "qvectors、c.mul/add/sub 和 Gram s/t 都在 Fraction 域；gap2 精确到 sqrt_exact 最终开方。Cover3 同时保存显示字段与独立 gap2/candidate/(s,t) 精确字段，构造记录并不对显示字段再开方。")
add("test_frozen_ee_sign", "_line_parameters_and_gap", PROOF, "independent.q 有理化线端点，叉积/Gram/有向分子均有理；sqrt_exact(numerator²/dot(n,n)) 是最后且唯一距离舍入。")
add("test_frozen_surface_diagonal", "_pair.move", PROOF, "调用参数 scale、translation 为 Fraction；每个原坐标先 F 转换，3/5、4/5 的正交变换也用 Fraction，直到 Polyhedron 顶点均精确。")
add("test_frozen_surface_diagonal", "_check", PROOF, "期望值由 scale*(F(1.7)-F(1.5)) 经 scalar_exact 最后显示；其余列出站点调用被测 API 或 pytest.approx 做最终核对，没有把比较结果流入新几何构造。")
add("test_geom3_merge", "_assert_exact_merge", PROOF, "Counter 站点统计整数顶点标签/有向边重数；切片拼接、重数相减不是几何标量舍入。几何平面/面积核验另用 Fraction。")
add("test_hull_robustness", "_exact_worst_outside", PROOF, "顶点显式 Fraction，面叉积 nn 与外点有向积 top 都是有理数；sqrt_exact(top*top/nn) 才输出距离，不先舍入分子或分母。")
add("test_invariance_2d", "_min_near_parallel_sin", PROOF, "_seg_dist 只筛选附近边对；入选边的分量重新逐坐标转 Fraction，叉积 c 及两模方都是有理，sqrt_exact 完整比值后才取 min 显示值。筛选器近似不污染比值。")
add("test_invariance_2d", "_support_labels_exact _sat_gap_exact", PROOF, "输入顶点/轴先 Fraction 化，支持投影差和法向模平方在有理域；最终 sqrt_exact 只显示完整 gap²/norm²，不重构已舍入差分。")
add("test_invariance_geom", "_support_gap_oracle", PROOF, "exact_oracle.qpoint 先有理化顶点，支持差、wedge/dot 与符号判定精确；sqrt_exact 对完整有理距离平方作最后显示。map 等动态形式须另按动态规则简化。")
add("test_limit_arch", "Arch.hinge_mechanisms", PROOF, "关节点逐坐标 Fraction，_solve4 有理解线性方程，tw/vel 中乘加和虚功全有理；这些 vel 调用不使用先舍入机构，alpha 是精确功率比。")
add("test_near_parallel_edges", "exact_seg_seg", PROOF, "_fv 先有理化两段，端点及内点 Gram 候选的平方距离都是 Fraction；min 的 best 仍是 Fraction，sqrt_exact(best) 是最终显示。")
add("test_perf_contact_window", "_box", PROOF, "中心与半宽逐个 F 转换，s[k] 为整数正负号；F(center)+s*F(half) 是有理坐标。")
add("test_perf_contact_window", "_pose", PROOF, "origin/p 坐标 F 转换，调用的 scale 与 frame 项为整数或 Fraction（含 3/5、4/5）；仿射变换全过程有理。")
add("test_perf_contact_window", "_assert_axis_certificate", PROOF, "scale 为有理测试参数、sign 仅 ±1，-sign*F(7,4) 与 scale/4 均有理；最后直接调用被测 inflated_membership 验证证书，非显示量回流。")
add("test_perf_contact_window", "_bilateral", PROOF, "overlap 由 Fraction 窗宽派生；左右盒中心/半宽 Fraction 算术，i+8 仅整数面索引偏移，Polyhedron 拼接保留有理顶点。")
add("test_perf_contact_window", "_assert_thick_bilateral_overlap_rejected", PROOF, "w=F(1,64)，3*w/2 为有理精确厚度；inflated_membership 是被测调用，不是从显示值重建预期。")
add("test_perf_integer_geometry", "sat_cases", PROOF, "box 输入 (F(0),)*3 与 (F(1),)*3；tuple 重复不做浮点乘法，提供精确 SAT 给定数据。")
add("test_perf_interlock", "_cases _cases.move", PROOF, "t 为整数，scale/delta 为整数或 Fraction，p 逐坐标 F 转换；move 的全部仿射坐标有理，Polyhedron 不造成先舍入。")
add("test_r8fix_margin_gap_gate", "_large_gap_gate", PROOF, "M=F(10**20)、excess=F(1)，M+excess+1 为有理精确间隙；margin_contacts 直接测给定输入并用独立证书判错。")
add("test_r9fix_topology", "_cube", PROOF, "center 各坐标 map(F,...) 且 h=F(half)，x±h/y±h/z±h 全有理；map(F) 的动态写法须另外简化，不能据此豁免未知 callable。", "REWRITE_DYNAMIC_AND_FIX_ANALYSIS")
add("test_r9fix_topology", "_assert_disconnected_inward_detected", PROOF, "scale 默认及测试实参为 Fraction，2*scale、10*scale 均精确；两有理 cube 的连通性测试不构造舍入距离。")
add("test_r9fix_topology", "_join", PROOF, "仅拼接既有 vertices 与整数偏移后的面索引，不求平方根/单位向量，也不改变顶点标量。")

# Pure sequence / identity operations misclassified as scalar arithmetic.
add("test_entrance3_concave", "_prism", PROOF, "两个已有坐标 tuple 列表相加只是棱柱顶点拼接；Polyhedron 包装原始给定坐标，面 reversed 只改变整数索引朝向。")
add("test_g03_two_rulers", "_prism", PROOF, "两截面顶点列表拼接是序列运算，Polyhedron 及 reversed 面只包装输入与索引，不产生浮点几何派生量。")
add("test_limit_duality", "_assert_duality", PROOF, "(0.0,)*dim 是零原点 tuple 重复，不是标量乘法；check_duality 核对已有求解结果，不将报告显示量作为构造输入。")
add("test_perf_edge_frame", "_queries", PROOF, "dict.fromkeys 去重三组整数边标签，len//2 是整数中间索引；没有数值几何数据流。")
add("test_kernel2d_predicates", "_polyomino", PROOF, "rng.choice 选整数网格单元，边界由格点拓扑构成；选择操作不把舍入派生标量输入构造。")

# Random rotations generate represented fixture inputs, not certified exact poses.
rotation_scopes = {
    "test_covers3_g0_vote2": "_quat_rotation", "test_covers3_membership": "_g6_rotation",
    "test_covers3_strict_lowdim": "_rot", "test_entrance3": "_quat", "test_frozen_ee_sign": "_rot3",
    "test_g03_two_rulers": "_quat", "test_g2_bdda3d": "_rot3", "test_geom3_face_polygon": "_rotation",
    "test_geom3_merge": "_rotation", "test_geom3_overlap_witness": "_rotation _qrot _Rq",
    "test_hull_robustness": "_rot", "test_invariance_geom": "_rotation", "test_invariance_interlock": "_rot3",
    "test_invariance_limit": "_rot3", "test_lp_certificates": "_rot _si_case.rot3",
    "test_margin_resolution": "_rotq", "test_near_parallel_edges": "_quat",
}
for f, ns in rotation_scopes.items():
    add(f, ns, INPUT, "seeded RNG 给出 binary64 四元数（部分另含三维方向），平方和/开方/单位化确有中间舍入；结果只生成变换后实际给定的姿态/坐标，不是精确期望距离或单位向量 oracle。不能称这些算术没有先舍入，需规范构造改写或明确采样输入边界。")

input_details = {
    "test_bb52_g1": ("_rounded_distance_audit", "函数明确保留原 21×60 rounded coordinate image 作为实际给定输入，再以零额外位移跑独立精确距离审计；不把该图像冒充精确仿射坐标。"),
    "test_covers3_g0_vote2": ("_non_facet_ee_labels", "法向/夹角只选明显非 facet 的 EE 标签（阈值 1e-3）以测 local_only；不是拿近似夹角作为精确几何边界 oracle。"),
    "test_covers3_strict_lowdim": ("_ridge_and_spike", "_rot 只给生成 ridge/spike 测试坐标的采样姿态，实际坐标交给下游几何谓词核验。"),
    "test_e5a2_bilinear_integer": ("operand_pairs", "rng.randrange 的 ±10**9 是整数采样界，用于构造随机有理数分子/分母；没有浮点中间舍入。"),
    "test_e5a2_integer_arithmetic": ("_cases", "rng.randrange 的 ±10**8 为整数界，只产生测试有理数输入，不构造几何预期答案。"),
    "test_e5a2_interlock_bridge": ("_pair", "amp/lx/ly/lz 缩放与整体 translation 定义实际输入的块体；下游对该给定坐标作精确判定，不承诺未舍入仿射像。"),
    "test_end_to_end_cb2": ("_scaled _capacity", "几何尺度、W*load_scale、施力方向/高度是给定试验模型的坐标/载荷；enumerate/limit 是被测执行，独立守恒/承载门针对这些实际给定数据，不将 float 变换称为精确派生证书。"),
    "test_frozen_ee_sign": ("_stack _ridge_pair _wedge_pair", "旋转、ridge 位置/镜像仅生成 EE 符号试验的给定坐标；独立 q/Fraction oracle 随后从这些实际坐标算真值。局部 lambda/callable 若仍存在应改为直接 helper，不能借采样理由豁免动态未知流。"),
    "test_g03_two_rulers": ("_ridge_pair", "_prism 包装指定 ridge 横截面构成给定块体；没有显示距离/法向流回精确 oracle。"),
    "test_g2_bdda3d": ("_near_dup_moving", "对给定顶点加入 1e-10 扰动并 append，专门生成近重合顶点的 alias/topology 夹具；append 是输入容器操作。"),
    "test_geom3_e5a": ("_g6e_distance_case", "已归档小间隙夹具经 _quat/_move 生成实际给定坐标；距离真值从最终坐标另算，不把姿态变换当精确距离证书。"),
    "test_geom3_face_polygon": ("Frame.__init__", "Frame 保存 _rotation(seed) 的采样旋转与给定位移，供生成实际输入；旋转本身不充当被测法向的精确 expected。"),
    "test_geom3_merge": ("_place _float_place _unplace_y _pocketed_slab", "_place 在采样旋转后以 Fraction 做 affine 以保共面；_float_place 明确测 rounded float 图像；_unplace_y 仅区域筛选；pocket 顶点为整数网格加可精确表示的 0.5。均为输入/区域选择，不重建显示距离。"),
    "test_geom3_overlap_witness": ("_place _l_block _box _x_pair", "_rotation/_qrot 经仿射变换生成给定 L/盒/cross 块体；下游见证/精确谓词针对实际坐标，不声称浮点变换保留理想实数几何。"),
    "test_interlock_sensitivity": ("_steep_H _steep_check", "缩放 amp/phase 和指定高度是敏感性试验输入；结果与近似解析/容差检查比，不输出精确构造 oracle。"),
    "test_interlocking": ("_scaled_pair", "scale 仅定义给定几何输入；函数中若保留数值 lambda，应直接化改写，不是可批准的动态数值例外。"),
    "test_invariance_2d": ("_star _ring", "随机角/半径只采样多边形实际输入；后续精确谓词独立有理化这些坐标。"),
    "test_invariance_geom": ("Motion.__init__", "Motion 记录采样旋转、尺度和位移供生成实际几何输入，不作为距离/单位法向精确 oracle。"),
    "test_invariance_interlock": ("_app _vec _rigid _tia_geom _tia_kink_offset _tia", "仿射坐标/向量及 0.5*s kink 偏移定义不变性试验的给定输入；rigid/tia 执行被测路径，实际给定坐标与理想变换的舍入区别由既有容差/精确分支处理，不能称采样运算本身精确。"),
    "test_invariance_limit": ("_matvec _w _cases _transform _transform.P _wrench_sum _c", "采样旋转/缩放的接触位置、单位法向、合力/力矩作为 LP 的实际给定模型输入；独立 residual 是另外的近似一致性核查，不是对未舍入理想变换的精确证书。此函数中的浮点乘加不能被描述为无舍入。"),
    "test_kernel2d_exact": ("_rand_convex _probe_points", "随机 hull 与 min/max 包围框±0.2 只决定附加测试平移采样；期望谓词从最终给定坐标算，不用这些 RNG 界作精确几何派生量。"),
    "test_kernel2d_g0": ("_star _ring", "rng 半径/角度是多边形夹具输入生成，真值独立于该采样算法；不宣称正则形状参数精确保持。"),
    "test_limit": ("_flat_block_ratio", "W、几何尺度和施力点定义平块加载试验；解析承载比用容差核对。给定模型允许 binary64 坐标/载荷，不将缩放过程当 exact 派生证书。"),
    "test_limit_contacts": ("_box _hovering_block", "盒体中心/半宽、H+gap 与 W 缩放、施力点/旋量均用于指定实际输入模型；enumerate/limit 是被测调用，不是先舍入的独立精确预期。"),
    "test_limit_fuzz": ("_case", "rng.uniform(0,2*pi) 只选随机角度以生成试验接触/载荷；不输出精确期望法向。"),
    "test_limit_scale": ("_scaled", "g*x 生成测试的给定坐标图像；Polyhedron 接收实际坐标，尺度不变性用独立证据核查而非宣称 affine 本身精确。"),
    "test_limit_selfcheck": ("_box", "T 平移、宽高、W 与施力点用于给定 LP 模型并打破形心对称；精确自校验针对这些实际输入，float fixture 构造不冒充 exact derived geometry。"),
    "test_lp_certificates": ("_si_case _lock_case _floor", "随机位置/载荷/旋转定义给定 LP 测试输入；r2/Rm 等数值 lambda/callable 若仍在应直接化，不能以采样输入为由许可未知动态构造。"),
    "test_margin_exact": ("_pair", "1+gap 为给定端点；本文件传入受控可表示 dyadic gap，并另用 Fraction 原坐标精确验证 signed gap，不能对任意 float gap 泛化无舍入。"),
    "test_margin_penetration": ("_tetra _box _convex_case _check_monotone_contact_resolution", "尺度半宽/坐标及 0.4-p 生成指定穿透输入；contact_resolution/body_distance 等是被测执行；half-abs(p) 只诊断深度，正确性另由原始坐标 Fraction 符号证据核验。"),
    "test_margin_resolution": ("_roof _roof_with_tiny_corner _small_pair", "大平移/小 e 棱角有意生成可表示的实际坐标图像以测舍入与分辨率；不声称理想 affine 精确保留。数值 sc lambda 须改直接 helper，不宜作为动态例外。"),
    "test_r7fix_geom2": ("_vv", "dx+size/dy+size 只指定二盒实际端点，测试另按原坐标精确差分核验 vv_cover；输入精度损失不被当作正确距离预期。"),
}
for f, (ns, reason) in input_details.items():
    add(f, ns, INPUT, reason)

# Older approximate diagnostics: explicitly NOT exact-construction proofs.
approx_details = {
    "test_bb52_g1": ("_retired_vote", "显式 retired vote 仅作历史浮点符号票的误判对照，current 真值来自独立精确门；不得称其精确 oracle。"),
    "test_frozen_lowdim": ("_brute_grad _check_one", "中心差分 (distance(x+h)-distance(x-h))/(2h) 与梯度 e 的 sqrt(sum(e²)) 是容差级导数/单位长度诊断，确有中间舍入；不提供精确导数或正确舍入距离构造保证。"),
    "test_geom3_face_polygon": ("_box_box_distance _dist_box_to_L", "轴对齐盒/L 解析式以 float 差、平方和及 sqrt 计算容差级对照，确是近似 oracle 而非正确舍入构造；应改 exact 公式或明确限定旧诊断边界，不可写无先舍入。"),
    "test_geom3_overlap_witness": ("_sat_sigma _sat_sigma.dot _sat_sigma.cross", "独立 OBB SAT 容差诊断采用 float 点/叉积与 n>1e-9 轴筛选、单位化，确有先舍入；仅在普通夹具上作近似分离深度对照，非精确 SAT 决定 oracle。"),
    "test_invariance_2d": ("_cover_predicate_margin _cover_predicate_margin.delta _seg_dist _seg_dist.pd", "前者计算保守可分辨性诊断而非判定真值；后者仅按近似段距离筛选附近边对。float 差/平方/开方确有舍入，最终几何真值由独立 Fraction 分支核验，不应升级为 exact 保证。"),
    "test_invariance_geom": ("_base", "math.dist 对已显示见证点仅找参考距离 d0 附近的并列标签；真实距离由独立闭式/brute 证据给出，不把显示见证点之差宣称精确距离。"),
    "test_invariance_interlock": ("_nz_min _escape _margin_ref", "nz/三角斜率是条件或不确定度报告；hypot 用于改变参数化、显示见证点差的 norm 只选近距离并列标签。均为容差诊断，不能当精确逃逸高度或距离构造。"),
    "test_invariance_limit": ("_cross _dot _norm _unit _generators _dual_residuals", "这些独立 float 代数/单位化用于给定接触模型及最差相对功率 residual；它们确有中间舍入，属于近似双对偶一致性检查而非 Fraction LP 证书。规范构造改写优先于例外。"),
    "test_lp_certificates": ("_old_formulation", "函数刻意保留旧浮点 _build_columns LP 作尺度错误对照；不作为新的精确证书，不能用它证明先舍入安全。"),
    "test_margin": ("_lipschitz_probe_points _legacy_global_pairs", "center/R/norm 决定局部与全局采样环和非重合点筛选，包含 float 几何舍入；这是近似 Lipschitz 实验点生成，不是正确舍入几何 oracle，旧 global-only 门的局限已在源码标明。"),
}
for f, (ns, reason) in approx_details.items():
    add(f, ns, APPROX, reason)
add("test_margin", "_lipschitz_setup", PROOF, "(E,)+probe_points+(global_pairs,) 是容器记录拼接，不是 scalar 算术；调用到的采样诊断需各自审核，不能因拼接误报而给整个函数数值豁免。")
add("test_margin", "_lipschitz_worst _lipschitz_verdict", APPROX, "normal_fn 是故障注入/正常法向的高阶参数，norm(normal_fn(x)-normal_fn(y))/norm(x-y) 是近似 Lipschitz 判据。数值动态调用必须改成显式已知分支/直接 helper；此审核不批准 callback 例外。", "REWRITE_DYNAMIC_NO_WAIVER")
add("test_invariance_limit", "_map_back", APPROX, "P 为传入位置变换 callable，用于把求解机构换回参考系并做近似功率残差；虽非 exact oracle，动态数值 P 仍须改传显式 R/s/t 或直接 helper，不能豁免未知 callable。", "REWRITE_DYNAMIC_NO_WAIVER")
add("test_interlock_sensitivity", "_steep_two_branches_in_report_band", INPUT, "gap/nz 来自 branch 显示报告，z=-gap/nz 仅选择严格落在报告 band 内的实际采样点以测试两个分支；不是把这个舍入高度冒充 exact 边界 oracle。如仍有精确边界声称须改写/收紧文档。")
add("test_lp_certificates", "_exact_limit_lp", PROOF, "oc 的 float 平均仅选择任意参考原点；所有力矩 (p-F(oc))×g 与荷载平移均在 Fraction 域且使用同一给定 oc，精确 LP 对参考点平移不变。_build_columns 只提供模型定义的锥棱方向，其浮点力矩被丢弃后独立精确重算。X=lambda F 形式仍应直接化。", "REWRITE_DYNAMIC_AND_FIX_ANALYSIS")

# Calls under test, final comparisons, and nonnumeric operations are not sinks.
api_details = {
    "e5b_margin_oracle": "check_exact_margin",
    "test_frozen_ee_sign": "_check_ee_exact _frozen_gap_of_chosen_label",
    "test_interlock_escape": "_check_escape", "test_interlock_exact": "_assert_exact_wall",
    "test_invariance_2d": "_covers", "test_invariance_geom": "body_distance margin_contacts inflated_membership _cell",
    "test_invariance_interlock": "body_distance margin_contacts inflated_membership _escape_ref _resolution",
    "test_invariance_limit": "_reference _solve", "test_limit": "_interlock_capacity",
    "test_limit_contacts": "_cb2_covers", "test_limit_scale": "_interlock_covers _capacity_ratio",
    "test_limit_selfcheck": "_utm_block", "test_lp_certificates": "_assert_same_exact_limit_result _exact_alpha",
    "test_m4_bdda_adapter": "_assert_matches_independent_oracle", "test_margin_resolution": "_expected _assert_distance _assert_margin_consistent",
    "test_perf_interlock": "_assert_cache_does_not_cross_offsets", "test_r10_resolution": "_unbounded",
    "test_r8fix_initial_state": "_assert_tight_seam_exit", "test_r8fix_margin_gap_gate": "_ordinary_gap_gate",
}
for f, ns in api_details.items():
    add(f, ns, PROOF, "此 helper 的列出站点执行被测公开 API/缓存与非缓存对照，或把其返回值交给最终断言；没有在站点先算一个显示几何派生量再作为精确 oracle 构造。应修区分被测调用和有害参数 provenance，不能因 callee 内有构造而全标红。")
add("test_margin_exact", "_assert_window_contract _assert_default_contract", PROOF, "2.**-24 / 2.**-35 是可精确表示的 dyadic；本文件 ratio/w 组合另通过 Fraction 原坐标 signed-gap 等式验证。其余站点直接调用被测 margin API，非显示量回流；不可泛化任意 float 幂均精确。")
add("test_r8fix_margin_gap_gate", "_ordinary_binary64_midpoint_gap_gate", PROOF, "2.**-53 精确可表示；给定二进制端点专为 midpoint tooth，margin_gap 由独立 Fraction midpoint-cell 证书检查，不把 float 预差当真值。")
add("test_kernel3d_covers", "_position_independence_violations", PROOF, "got^base 是标签 set 的对称差，t+x 是给定位姿输入，g1-g2 只写入失败诊断；不是数值 xor 或以差分显示值构造 oracle。应分类型/用途消除误报，不给整个函数统一数值许可。")
add("test_fixture_provenance", "_sha256", PROOF, "fh.read(1<<20) 的数值是整数读取块大小，返回 bytes 供 SHA256；无数值几何构造。")
add("test_fixture_provenance", "_fixture_files", PROOF, "p.relative_to(FIX) 只计算夹具路径清单，不对几何标量求差。")
add("test_g4_multistep", "_df22_last", PROOF, "chr(13)+chr(10) 是 CRLF 文本拼接，replace 规范日志换行；无数值几何构造。")
add("test_invariance_2d", "_bb52_blocks", PROOF, "sys.path.insert 等只设置 fixtures/tool 的读取路径；不是数值构造输入转换。")
add("test_kernel2d_review", "_load_both", PROOF, "sys.path/模块加载仅载入两份读取结果供对照，不计算几何派生标量。")
add("test_lp_scale", "_certify", PROOF, "pytest.approx(primal,...) 是最终证书数值比较器；其返回比较对象不流入任何几何构造。")
add("test_m4_bdda_shadow", "_gate_case", PROOF, "shadow.compare_fixture(path) 消费夹具路径并返回差异报告供断言；不是 float 派生标量构造。")
add("test_m4_bdda_vv_reader", "_write_case", PROOF, "map(str)/join/write_text 序列化 CSV 测试输入；返回字符/写入长度，不是数值 callable 构造。")
add("test_tf_reader", "_assert_rows_agree", PROOF, "getattr(r,k) 仅读取已知字段表用于最终相等断言，不调用容器取出的函数，也不构造新几何；若项目统一禁止此数值字段反射应改显式字段核对，不能宽泛放开 getattr。")

# Purposeful wrong code must remain an exercised tooth, never be described safe.
add("test_r9fix_construction", "_premature_sqrt_mutant", BAD, "故意错误实现 sqrt(float(value))，确实先舍入并用于 monkeypatch 被测 sqrt 路径；测试必须因其错误结果报红。这不是安全数值例外。", "INTENTIONAL_DEFECT_KEEP_MUTATION_TOOTH")
add("test_g2_bdda3d", "_mutant_g2", BAD, "compile/exec 将文本变异植入被测 G2 模块后运行门；目的就是重引缺陷验证红，不能用语义安全理由批准动态数值代码。", "INTENTIONAL_DEFECT_KEEP_MUTATION_TOOTH")
add("test_r11fix_static_flow", "_cone_implant _mutant_scan", BAD, "source.replace/compile/exec 在被测 scanner/cone 内部植入遗漏或坏算术；这是牙的测试基础设施，故障代码必须保持被门拒绝，不声称其数值安全。", "INTENTIONAL_DEFECT_KEEP_MUTATION_TOOTH")
add("test_r7fix_geom3", "_inject", BAD, "compile/exec 专门把错误体注入被测几何函数，随后由针对断言验证红；属于显式变异基础设施而非正常数值实现许可。", "INTENTIONAL_DEFECT_KEEP_MUTATION_TOOTH")
add("test_r9fix_g03_construction", "_bad_witness_report", BAD, "此 helper 安装错误 witness 枚举逻辑后执行 G0 报告以证明构造牙；被测 API 调用不是正常 oracle，必须保留故障断言，不将故障实现说成无先舍入。", "INTENTIONAL_DEFECT_KEEP_MUTATION_TOOTH")

default_actions = {
    PROOF: "FIX_ANALYSIS_NO_WAIVER",
    INPUT: "REWRITE_OR_REVIEW_EXPLICIT_SUPPLIED_INPUT_BOUNDARY",
    APPROX: "REWRITE_OR_REVIEW_EXPLICIT_NONEXACT_DIAGNOSTIC_BOUNDARY",
    BAD: "INVESTIGATE_DEFECT_NO_WAIVER",
}
out = []
seen = set()
missing = set()
for row in selected:
    key = (row["path"], row["function"], row["rule"], row["node"])
    if key in seen:
        continue
    seen.add(key)
    scope = (row["path"], row["function"])
    if row["function"].split(".")[0].startswith("test_"):
        disposition, reason, action = PROOF, "这是已约定边界外的 test_* driver（含其嵌套测试变异体），本轮 closed-* 新规则扫描到了 driver。应恢复原 driver 范围而不是新增例外；本条不主张函数内所有数值写法精确。", "RESTORE_EXISTING_TEST_DRIVER_BOUNDARY_NO_WAIVER"
    elif scope in scopes:
        disposition, reason, action = scopes[scope]
    else:
        missing.add(scope)
        disposition, reason, action = PROOF, "尚未完成该站点源码人工审查，不批准豁免。", "REVIEW_REQUIRED_NO_WAIVER"
    out.append({**row, "disposition": disposition, "reason": "站点 `" + row["source"].replace("\n", " ") + "`：" + reason,
                "recommended_action": action or default_actions[disposition], "waiver_approved": False})
assert not missing, sorted(missing)
payload = {
    "review_kind": "independent numerical-site triage; NOT a waiver manifest",
    "input": "raw_scan_round2.json",
    "input_sha256": hashlib.sha256((BASE / "raw_scan_round2.json").read_bytes()).hexdigest(),
    "input_rows": len(selected), "unique_reviewed_sites": len(out),
    "dedup_key": ["path", "function", "rule", "node"],
    "category_counts": dict(Counter(r["disposition"] for r in out)),
    "action_counts": dict(Counter(r["recommended_action"] for r in out)),
    "limits": ["SOURCE_PROOF_GAP 不是豁免批准；应修数据流/类型规则并保留对抗牙。",
               "SUPPLIED_INPUT / LEGACY_APPROX 承认某些源码有 float 先舍入，绝不等同正确舍入构造证明。",
               "ACTUAL_BAD 条目均为本轮识别的显式内部故障注入，不是新发现的非故意生产缺陷。",
               "动态数值 lambda/callback/map 等仍须另改简单源码；本审核不授权豁免。",
               "必须与最终扫描的 path/function/rule/node/context 交叉过滤；此快照不能自动变成新 manifest。"],
    "sites": out,
}
(BASE / "tests_numerical_review.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
summary = json.dumps({k: v for k, v in payload.items() if k != "sites"}, ensure_ascii=False, indent=2)
(BASE / "tests_numerical_review_summary.json").write_text(summary + "\n", encoding="utf-8")
print(summary)
