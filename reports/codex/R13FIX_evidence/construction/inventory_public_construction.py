"""Rebuild the explicitly reviewed API/field census, never infer coverage by grep."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
maps = {}


def cover(module, names, filename, tests, scales, note="独立有理公式逐值核对；有限构造族，不等于全输入域证明", status="新增差分门"):
    for name in names.split():
        maps["eab."+module+"."+name] = dict(status=status, tests=[filename+"::"+test for test in tests.split()], scales=scales, note=note)


geo="tests/test_r13fix_geometry_differential.py"
for mod in ("kernel2d.geom", "kernel3d.geom3"):
    cover(mod,"dot cross",geo,"test_public_dot_cross_round_after_cancellation test_public_dot_cross_reject_unrepresentable_nonzero","输入2^-538/1/2^1020；最终minsub/0/普通；只改全float路径")
    cover(mod,"norm unit",geo,"test_public_norm_normal_and_edge_components_match_rational_reference","2^[-1070,-600,0,600,1018]")
    cover(mod,"add sub",geo,"test_public_float_coordinate_operations_match_independent_components test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs","2^[-1074,-600,0,600,1021]；max范围外","仅all-float最终坐标范围检查；Fraction/Dual/混合类型保留原代数合同")
cover("kernel2d.geom","translate",geo,"test_public_float_coordinate_operations_match_independent_components test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs","2^[-1074,-600,0,600,1021]；max范围外","all-float路径；混合类型未做全范围保证")
cover("kernel3d.geom3","mul box Polyhedron.translated",geo,"test_public_float_coordinate_operations_match_independent_components test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs","2^[-1074,-600,0,600,1021]；max范围外","all-float路径；translated的既有mixed Fraction精确保留合同不变")
cover("kernel2d.geom","outward_normal",geo,"test_public_norm_normal_and_edge_components_match_rational_reference","2^[-1070,-600,0,600,1018]")
cover("kernel2d.covers","normal_cone",geo,"test_public_norm_normal_and_edge_components_match_rational_reference","2^[-1070,-600,0,600,1018]")
cover("kernel2d.geom","signed_area vertex_turn point_side centroid",geo,"test_public_area_turn_side_match_exact_shoelace","2^[-537,-530,0,500,509]")
cover("kernel3d.geom3","Polyhedron.face_normal Polyhedron.edge_dir Polyhedron.vertex_edge_dirs",geo,"test_public_norm_normal_and_edge_components_match_rational_reference","2^[-1070,-600,0,600,1018]")
cover("kernel3d.geom3","Polyhedron.face_area",geo,"test_public_area_turn_side_match_exact_shoelace test_public_face_area_at_overflow_edge_rounds_final_area","2^[-537,-530,0,500,509]；area=2^1023")
cover("kernel3d.geom3","Polyhedron.volume Polyhedron.centroid",geo,"test_public_volume_and_centroid_match_independent_tetrahedral_moments","2^[-359,-350,0,330,338]")
cover("kernel2d.covers","ve_cover ev_cover vv_cover enumerate_covers facet_gap",geo,"test_public_2d_cover_fields_match_exact_projection_and_gap","2^[-1070,0,1018]")
cover("kernel2d.g0","brute_polygon_distance",geo,"test_public_2d_cover_fields_match_exact_projection_and_gap","2^[-1070,0,1018]")
cover("kernel3d.covers3","closest_point_of_convex_hull_to_origin cone_relint_direction",geo,"test_public_3d_closest_point_and_distance_constructions","2^[-1070,0,1018]")
cover("kernel3d.exact_geom","point_segment_distance_squared point_triangle_distance_squared segment_distance_squared",geo,"test_public_3d_closest_point_and_distance_constructions","2^[-1070,0,1018]，Fraction平方输出")
cover("kernel3d.geom3","brute_feature_distance",geo,"test_public_3d_closest_point_and_distance_constructions","2^[-1070,0,1018]")
cover("kernel3d.covers3","facet_plane3 facet_normal3 facet_gap3 support_gaps3",geo,"test_public_facet_normal_and_support_gap_are_independently_derived","2^[-1070,0,1018]","逐gap和方向核对；facet支持恒等式以生产方向为候选，未独立证明全部方向枚举")
cover("kernel3d.covers3","vf_cover fv_cover ee_cover ve3_cover ev3_cover vv3_cover",geo,"test_all_six_public_3d_cover_constructors_compare_every_numeric_field","2^[-1070,-537,0,509,1018]，各向异性保持面面积可表达")
cover("kernel3d.geom3","Polyhedron.edge_noise Polyhedron.face_noise Polyhedron.dihedral_noise Polyhedron.vertex_edges",geo,"test_relative_noise_diagnostics_do_not_round_away_scale_before_ratio","2^[-1070,-600,0,600,1018]","面噪声模型使用逐边已舍入长度的有理和；不是多根式正确舍入承诺")
cover("kernel2d.geom","round_floor",geo,"test_absolute_noise_diagnostic_rejects_unrepresentable_nonzero","minsub输入不可表达非零输出必须拒绝",status="新增范围门；差分网格待补")
cover("kernel3d.geom3","noise_floor",geo,"test_absolute_noise_diagnostic_rejects_unrepresentable_nonzero","minsub输入不可表达非零输出必须拒绝",status="新增范围门；差分网格待补")
for mod,names in (("kernel2d.geom","turn_angle interior_point convex_hull"),("kernel2d.covers","cone_width"),("kernel3d.geom3","angle_between Polyhedron.dihedral_turn convex_hull_3d convex_hull_3d_eps exact_convex_view exact_surface merge_coplanar")):
    cover(mod,names,geo,"test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates","2^[-1070,0,1018]","角度只验正交解析值；拓扑API只验坐标保真，不覆盖全部拓扑结果",status="新增有限差分门；完整网格待补")

mech="tests/test_r13fix_mechanics_differential.py"
cover("limit","wrench mechanism_power",mech,"test_public_wrench_and_power_each_value_matches_rational_reference","2^[-1074,-600,0,600,1022]")
cover("rational3","dot cross",mech,"test_public_rational3_polynomials_do_not_use_a_display_as_input","2^[-1074,-600,0,600,1022]；精确有理多项式")
cover("limit","friction_generators",mech,"test_public_friction_generators_round_complete_component test_public_3d_friction_generators_follow_exact_given_coefficient_model","mu=minsub/0.5/nextafter(1,0)/2^1022；3D两k×四mu","二维完整分量公式；三维按给定libm系数模型逐棱分量，不承诺真超越函数正确舍入")
cover("construction","vector_rational",mech,"test_public_vector_constructor_has_independent_extreme_cells_and_distinct_outputs","minsub/2^-600/1/3/2^600/max+2^969；产物互异；正负输出范围拒绝")
cover("dual","atan2 sqrt",mech,"test_public_dual_angular_and_sqrt_derivatives_are_value_bound","2^[-1074,-600,0,600,1022]","导数有理参考；非代数primal不承诺全域正确舍入")
cover("dual","sin cos",mech,"test_public_trig_derivative_follows_declared_coefficient_model","2^[-1074,-600,0,600,1022]","libm系数已给定的导数积模型，非真超越函数全域舍入证明")
cover("lp","solve maximize",mech,"test_public_lp_views_are_bound_to_independent_exact_solution","2^[-1075,-1074,-600,0,600,1023,1024]","非对称唯一2x2原始/对偶，每个显示字段与精确解绑定")
cover("limit","limit_load",mech,"test_public_limit_single_and_multi_match_analytic_sliding_capacity","2^[-1073,-600,0,600,1021]","独立解析滑移承载族，不覆盖所有活跃集")
cover("limit_multi","limit_load_multi",mech,"test_public_limit_single_and_multi_match_analytic_sliding_capacity","2^[-1073,-600,0,600,1021]","独立解析滑移承载族，不覆盖所有多体活跃集")

frozen="tests/test_r13fix_frozen_margin_differential.py"
cover("kernel3d.frozen","frozen_gap frozen_normal",frozen,"test_frozen_public_gap_normal_and_jets_match_rational_values","2^[-1074,-600,0,600,1018]；6kind值与导数")
cover("kernel3d.frozen","face_normal_generic ee_normal_generic frozen_lift",frozen,"test_face_edge_normals_and_frozen_lift_have_independent_extreme_jets","2^[-1074,-600,0,600,1018]；非零方向导数")
cover("margin","body_distance margin_contacts nearest_point_on_convex_entrance distance_to_convex_entrance inflated_normal margin_gap_from_frozen_cover",frozen,"test_margin_public_distance_projection_normal_and_gap_are_value_bound","2^[-1074,-600,0,600,1018]","闭盒保单位面积；点凸包3-4-5独立投影")

event="tests/test_r13fix_event_bindings.py"
cover("kernel2d.entrance","first_entrance shortest_exit",event,"test_public_2d_event_fields_have_independent_extreme_scale_references test_public_entrance_times_are_rounded_once_at_extreme_scales","2^[-1070,0,1018]；t/exact_t/x/normal/gap/witness")
cover("kernel3d.entrance3","first_entrance3",event,"test_public_3d_entrance_fields_have_independent_extreme_scale_references test_public_entrance_times_are_rounded_once_at_extreme_scales","2^[-1070,0,1018]；各向异性面积可表达")
cover("kernel3d.entrance3","shortest_exit3",event,"test_public_3d_exit_fields_have_independent_extreme_scale_references","2^[-1070,0,508]")
cover("kernel3d.interlock","escape_height_covers escape_height_from_frozen_cover escape_height_brute",event,"test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots","2^[-1070,0,1018]乘3/4与1/3")
cover("kernel3d.interlock","escape_candidates dilatancy_profile",event,"test_nominal_candidates_and_profile_have_valuewise_extreme_scale_references","2^[-1070,0,1018]","profile仅平坦导数0；nominal候选容许抑制，非完整保证",status="新增有限差分门；完整网格待补")

old="tests/test_r9fix_construction_rounding.py"
cover("construction","scalar_rational ratio_rational",old,"test_r9_scalar_ratio_are_certified_at_binary64_midpoints","0/minsub/minnormal/2^-600/1/3/7/2^600/max及中点两侧",status="已有独立差分门")
cover("construction","sqrt_rational",old,"test_r9_exact_sqrt_is_certified_at_binary64_midpoints test_r9_exact_sqrt_non_square_subnormal_certificates","全binary64关键舍入cell与24非平方次正规cell",status="已有独立差分门")
cover("construction","norm_rational unit_rational",old,"test_r9_norm_and_unit_round_exact_final_components","次正规/普通/上溢边缘及大有理数归一化",status="已有独立差分门")
cover("construction","normalized_difference_rational","tests/test_r9fix_compound_construction.py","test_compound_constructor_rounds_values_between_max_and_overflow_midpoint test_compound_range_and_cancellation_are_not_decided_by_intermediate_displays","max与overflow中点之间/2^1100相消/minsub以下",status="已有独立差分门")

predicate_names=set("is_ccw zero_length_edges is_convex reflex_vertices orient2d point_in_polygon segments_properly_cross polygons_overlap in_cone membership_convex local_facets ambiguous_facets convexity_violation is_convex_exact strict_vertices membership_exact convex_overlap_exact vertex_side_exact ve_side_exact ev_side_exact polygons_overlap_exact entrance_membership_exact vertex_cone_contains edge_arc_contains cones_intersect_relint local_facets3 membership_convex3 frozen_ee_sign orient2 polygon_locate polygon_locate_fraction triangle_locate point_in_surface segment_crosses surface_overlap face_polygon_locate point_in_face_polygon point_in_polyhedron segment_crosses_face polyhedra_overlap exact_point_in_polyhedron exact_segment_crosses_face exact_point_in_convex_polyhedron exact_convex_overlap is_exact_zero fraction_vectors cross2_sign dot2_sign orient3d orient3d_fraction mechanism_is_admissible check_duality check_duality_multi mechanism_is_admissible_multi validate closed passed".split())
data_names=set("as_tuple canonical_key to_dict from_dict records_to_json records_from_json label metadata cone_tol edges vertex_faces edge_faces edge_traversals aabb vertex_block vertex_pos canon width val grad const seed lift seeded ensure_ccw edge triangulate vertex_edges manifold_issues reflex_edges".split())
report_names=set("coord_scale round_floor eff_tol angle_floor turn_floor noise_floor edge_noise face_noise dihedral_noise metrics characteristic_length coordinate_magnitude rounding_floor effective_geom_tol contact_resolution boundary_band central_difference convergence_order".split())
selector_names=set("convex_hull convex_hull_3d convex_hull_3d_eps merge_coplanar exact_convex_view exact_surface hull_exact hull_exact_fr strict_vertices triangulate".split())
rows=[]


def add_row(path,node,qual,public=True,kind="callable",annotation=""):
    module="eab."+".".join(path.relative_to(ROOT/"src/eab").with_suffix("").parts)
    api=module+"."+qual
    leaf=qual.rsplit(".",1)[-1]
    if not public: category="非public私有实现"
    elif kind=="field": category="公开数据字段/返回记录契约"
    elif "/readers/" in path.as_posix(): category="读取/契约转换（数值字段仍需单独差分）"
    elif "oracle" in module or module.endswith(("g03_exact","g0","g03")): category="参考/验证API（非生产主构造）"
    elif leaf in predicate_names: category="判据/离散标签"
    elif leaf in report_names: category="数值诊断/近似报告构造"
    elif leaf in selector_names: category="坐标/拓扑选择器"
    elif leaf in data_names: category="数据访问/结构变换"
    else: category="数值构造/混合输出（需有独立逐值门）"
    info=maps.get(api)
    if info is None:
        if not public: status="不在公开API范围"
        elif kind=="field": status="随所属构造返回逐字段审查；不得由字段名推定覆盖"
        elif category in ("判据/离散标签","数据访问/结构变换","坐标/拓扑选择器"): status="非浮点主构造；已有契约/拓扑门另审"
        else: status="未确认完整独立极尺度差分门（缺口/待逐项审查）"
        info=dict(status=status,tests=[],scales="未确认",note="本普查不把名称匹配或测试全绿当作该API的差分覆盖证明")
    rows.append(dict(api=api,path=path.relative_to(ROOT).as_posix(),line=node.lineno,public=public,kind=kind,
                     category=category,annotation=annotation,**info))


for path in sorted((ROOT/"src/eab").rglob("*.py")):
    tree=ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            add_row(path,node,node.name,not node.name.startswith("_"),annotation=ast.unparse(node.returns) if node.returns else "")
        elif isinstance(node,ast.ClassDef):
            for item in node.body:
                if isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    special=item.name in ("__init__","__add__","__sub__","__mul__","__truediv__","__pow__","__neg__","__radd__","__rsub__","__rmul__","__rtruediv__")
                    public=not node.name.startswith("_") and (not item.name.startswith("_") or special)
                    add_row(path,item,node.name+"."+item.name,public,annotation=ast.unparse(item.returns) if item.returns else "")
                elif isinstance(item,ast.AnnAssign) and isinstance(item.target,ast.Name):
                    add_row(path,item,node.name+"."+item.target.id,not node.name.startswith("_") and not item.target.id.startswith("_"),"field",ast.unparse(item.annotation))

for row in rows:
    for nodeid in row["tests"]:
        path,name=nodeid.split("::")
        tree=ast.parse((ROOT/path).read_text(encoding="utf-8-sig"))
        assert any(isinstance(n,ast.FunctionDef) and n.name==name for n in ast.walk(tree)),nodeid
HERE.mkdir(parents=True,exist_ok=True)
(HERE/"public_api_inventory.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
public=[r for r in rows if r["public"]]
summary={"all_symbols_including_private":len(rows),"public_callables":sum(r["kind"]=="callable" for r in public),
         "public_fields":sum(r["kind"]=="field" for r in public),"explicitly_mapped_callables":sum(bool(r["tests"]) for r in public),
         "unconfirmed_numeric_callables":sum(r["kind"]=="callable" and r["status"].startswith("未确认") for r in public)}
(HERE/"inventory_counts.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
lines=["# R13FIX 公开构造 API 差分门普查","","**结论：补齐了一批明确缺口，但没有完成全部公开构造 API 的极尺度独立逐值门；不得据此声称全覆盖。**","",
       "## 范围与判定办法","","- AST 遍历全部 `src/eab/**/*.py` 的顶层函数、类方法和注解字段；私有类/私有函数保留在 JSON，明确非 public。特殊算术方法作为 public 纳入。",
       "- public 是源码命名暴露面的保守上界，不仅是 `__init__.py` 的再导出；oracle/读取/判据/诊断也列清。数据记录字段不能因所属类型受测就自动当作全部字段已测。",
       "- 表内 nodeid 为人工按公式与断言对象核对的映射。扫描只验证 nodeid 存在，绝不以 grep、函数名出现或全套绿推断独立性或覆盖。",
       "- 每行新增门只证明列明的构造族/尺度；角度、诊断多根式、随机/名义候选和普通 Dual 快路均保留限制。静态子集门是辅助检查，不是此处运行时主保证的替代。","",
       "## 统计","", "```json",json.dumps(summary,ensure_ascii=False,indent=2),"```","",
       "## 已知遗留（R13FIX_PARTIAL 的实质项）","",
       "1. `geom/geom3` 的 all-float add/sub/mul/translate/box 与 dot/cross 已补范围/逐值门；混合类型及泛型其它代数路径仍未建立完整范围保证，未泛改 Fraction/Dual 语义。",
       "2. 所有角度的完整非正交及极小角族、随机样本构造、坐标选择器全部返回字段、部分精确工具 API 仍需逐项补门。",
       "3. `noise_floor/round_floor` 新增的是不可表达非零响亮拒绝门；外围 policy estimates（margin 等）、metrics、泛化噪声网格未全部补齐。face_noise 的逐边长度若自身不可表达仍可能拒绝最终可表达比例。",
       "4. 普通 Dual 算术快路/一般幂/超越函数不保证全域正确舍入；新门严格区分 libm 系数模型与真超越函数。",
       "5. readers/adapters/contacts转换的各公开数值字段与机械一般活跃集未有此次完整极尺度逐值证明；3D摩擦生成器已新增两k×四mu的给定系数模型门，不是全输入域保证；M4a既有门必须另行回归。",
       "6. nominal escape候选容许抑制、dilatancy只新增平坦零导数族，不能等同完整差分保证。","",
       "## 每个公开调用点/字段台账","","完整私有/公开机器表见 `reports/codex/R13FIX_evidence/construction/public_api_inventory.json`。"]
module=None
for r in public:
    if r["path"]!=module:
        module=r["path"];lines += ["", "### `"+module+"`", "", "| API / 字段 | 分类与状态 | 差分门 / 尺度 / 限制 |", "|---|---|---|"]
    test="<br>".join("`"+v+"`" for v in r["tests"]) or "—"
    lines.append("| `"+r["api"].removeprefix("eab.")+"` | "+r["category"]+"；"+r["status"]+" | "+test+"<br>"+r["scales"]+"<br>"+r["note"]+" |")
(ROOT/"docs/r13fix_construction_inventory.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False))
