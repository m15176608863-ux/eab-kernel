"""Human-reviewed G6M geometry candidate classification, not a safety proof.
The input is root's conservative keyword AST inventory. Explicit categories
are selected by file/function or line-specific inspected dataflow.
"""
from pathlib import Path
import json,collections,ast,hashlib
ROOT=Path(__file__).resolve().parents[2]
raw=json.loads((ROOT/'review/evidence/branch_inventory_raw.json').read_text(encoding='utf-8'))
# Keyword candidates missed symbolic bound names in predicates.py. Add every
# live filter's actual branch, rather than claiming the parent inventory is full.
existing={(r['file'],r['line'],r['kind']) for r in raw}
for file,names in [('src/eab/predicates.py',None),('src/eab/kernel3d/exact_geom.py',{'_iv','_im','_edge_window_filter','polygon_locate'})]:
    tree=ast.parse((ROOT/file).read_text(encoding='utf-8-sig'))
    for fn in tree.body:
        if not isinstance(fn,ast.FunctionDef) or names is not None and fn.name not in names:continue
        for node in ast.walk(fn):
            if not isinstance(node,(ast.If,ast.IfExp)):continue
            key=(file,node.lineno,type(node).__name__)
            if key not in existing:
                raw.append(dict(file=file,line=node.lineno,function=fn.name,kind=type(node).__name__,condition=ast.unparse(node.test)))
                existing.add(key)
out=[]
legacy={'_inward_vertex_direction','_edge_edge_contacts','_active_normals','_gordan_direction','_min_norm_on_simplex','_contact_cone_witness','_tri_axes'}
report={'angle_floor','turn_floor','metrics','edge_noise','face_noise','vertex_edges','manifold_issues','_normal_noise','_cover_escape_z','_candidates_uncached','_escape_solution','_tie_groups','effective_geom_tol','boundary_band','contact_resolution'}
geometry_files={'src/eab/predicates.py','src/eab/margin.py'}
for r in raw:
    file,fn,line=r['file'],r['function'],r['line']
    if not (file in geometry_files or '/kernel2d/' in file or '/kernel3d/' in file):continue
    category='精确有理判定或参数/离散分支（字面浮点不表示浮点被测量）';note='逐路径读取显示几何量先Fraction/整数化；词法命中不等于噪声比较。'
    if fn in legacy:
        category='遗留近似私有helper，生产新入口未调用';note='已查当前polyhedra_overlap→exact_geom.surface_overlap等调用链；不可作为独立oracle或泛化为任意外部私有调用正确。'
    elif fn in report:
        category='报告/构造/诊断或nominal标签';note='不改变默认精确成员、精确距离或exact_height；窗口nominal排序如实保留旧报告语义。'
    elif file.endswith('predicates.py') or fn=='orient2d' or fn in {'_iv','_im','_edge_window_filter','polygon_locate'}:
        category='保守浮点过滤，未认证则精确兜底';note='符号/interval结论须越过误差界；未通过走Fraction/整数路径；G6M独立78600比较及fallback计数。'
    elif 'g0' in file:
        category='审计门构造误差/抽样，不变更被测精确真值';note='精确完整性直接等式，构造量另用报告误差界。原浮点构造检查不是几何主oracle。'
    elif fn in {'first_entrance_brute','escape_height_brute'}:
        category='声明的佐证/兼容入口';note='二维/三维first_entrance_brute为有限采样，不是独立oracle；escape_height_brute现走精确事件。'
    elif file.endswith('/entrance.py') and fn in {'_first_entrance_convex','_first_entrance_concave','shortest_exit'}:
        category='near_labels可分辨性报告';note='候选时刻/并列/胜出先在Fraction比较；band只收near_labels。'
    elif file.endswith('/interlock.py') and fn=='escape_height_covers':
        category='显式窗口模型/nominal标签报告';note='contact_models仅显式w；root/event/proof独立完整精确枚举；nominal差值仅选label。'
    elif file.endswith('/margin.py') and fn=='_resolve' and line==362:
        category='精确完整性+浮点显示自检';note='minimum2!=truth2直接拒收；abs(dmin-truth)比较只验显示点，不能接受精确平方距离不等。'
    elif file.endswith('/margin.py') and fn=='closed':
        category='用户手工构造兼容浮点closed/生产精确closed';note='生产margin_contacts设_exact_closed；None时手工实例按给定margin_gap≤0，不有隐式窗口。'
    elif fn in {'normal_cone','_angle_window2','_ve_side_directions','_in_segment_exact','_feature_in_gap_window','enumerate_covers','first_entrance_for_vertex','membership_convex','reflex_vertices','point_in_polygon','_point_in_polygon','segments_properly_cross','_triangles_overlap','_interiors_overlap','polygons_overlap','_outside_dot_band','_qvertex_state_cached','_qedge_contains','_face_witness','_qparameter_in_extent','vv3_cover','_cover_in_window','enumerate_covers3','membership_convex3','_in_convex_boundary_band','face_polygon_locate','point_in_face_polygon','point_in_surface','segment_crosses','surface_overlap','_contact_window','_penetration_within_window','margin_contacts','inflated_membership'}:
        category='调用方显式域窗/边界报告，内部仍精确平方或符号';note='tol/extent/window/atol由调用方选择；默认数学状态不加坐标噪声地板。'
    out.append(dict(r,classification=category,rationale=note,confirmed_answer_changing_noise=False))
summary=collections.Counter(r['classification'] for r in out)
result=dict(head='fabe303b9d574891094b0b9e86b171343e469bfc',scope='几何候选逐站点人工分类；不把候选清单当全仓穷尽证明',candidates=len(out),summary=dict(summary),sites=out)
(ROOT/'review/geometry_branch_classification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(candidates=len(out),summary=dict(summary)),ensure_ascii=False,indent=2))
