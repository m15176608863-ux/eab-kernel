from pathlib import Path
import ast, json, collections, re
root = Path('.')
sources = sorted((root / 'src/eab').rglob('*.py'))
rows = []
candidates = []
seeds = {'tol', 'atol', 'band', 'window', 'noise', 'floor', 'eps', 'ctol', 'gtol', 'ztol', 'threshold', 'dup_tol', 'geom_tol', 'contact_window', '_U', '_TINY', 'EPS', 'ROUND_C', 'REL_GEOM_TOL', 'REL_BOUNDARY_TOL', '_O3D_ERR', '_BILINEAR_ERR', '_FEAS', '_INFEAS', '_PIV_STABLE', '_PIV_NOISE', '_PIV_NOISE_GLOBAL', '_DUAL_CHECK', '_RAY_CHECK', '_NOISE_FLOOR', '_U_ENTRY', '_UNCERTAIN', '_SELF_CHECK', '_PERTURB', '_FLIP', 'bound', 'round_floor', 'rounding_floor', 'noise_floor', 'eff_tol', 'effective_geom_tol', 'face_noise', 'dihedral_noise', 'angle_floor', 'turn_floor'}
legacy2 = {'eff_tol', 'angle_floor', 'turn_floor', 'is_convex', 'reflex_vertices', 'point_in_polygon', '_point_in_polygon', 'segments_properly_cross', '_triangles_overlap', '_interiors_overlap', 'polygons_overlap'}
legacy3 = {'manifold_issues', 'is_convex', 'reflex_edges', '_segment_closest_points', '_edge_edge_contacts', '_active_normals', '_gordan_direction', '_min_norm_on_simplex', '_interior_contact_probe', 'cone_relint_direction', '_inward_at_vertex'}

def classify(path, fn, line):
    base = Path(path).name
    if base == 'predicates.py':
        return ('speed_filter_exact_fallback', '本文件cross/dot/orient的浮点比较只接受保守界外符号；其余Fraction兜底；二维20,000独立对拍已完成，非全域证明。')
    if path.endswith('kernel2d/geom.py'):
        if fn == 'orient2d':
            return ('speed_filter_exact_fallback', 'det>bound接受；界内/溢出回Fraction；上次20,000跨指数对拍已完成。')
        if fn in legacy2:
            return ('legacy_answer_changing_noise', '文档明确旧对照/统计API，不能作为生产exact；G0仍使用polygons_overlap，此活用处确认缺陷。')
        return ('float_construction_or_exact_helper', '法向/面积/点构造仍浮点；triangulate朝向与orient精确，convex_hull转调exact。')
    if path.endswith('kernel2d/g0.py'):
        if fn in {'g0_distance_completeness', 'g0_exit_completeness', 'brute_ray_exit'}:
            return ('confirmed_g0_answer_changing_noise', 'G2D-01/02已复现：固定1e-12*L + floor跳过严格样本/错误首出口；不是调用方显式窗口。')
        if fn == '_point_segment_distance':
            return ('confirmed_float_underflow_oracle', 'G2D-03已复现：e^2下溢为0使线段投影退成端点，错距。')
        return ('exact_or_sampling_metadata', '凸三票有理数，不跳样；采样/计数或独立支持/凸包。')
    if path.endswith('kernel2d/covers.py'):
        if fn in {'_facet_normal_own', 'facet_gap'}:
            return ('float_construction_report', '只选同向facet的浮点法向构造，不决定成员/首入。')
        return ('explicit_domain_window_or_exact', '法锥/长度/角窗与成员tol是显式调用方政策，转换Fraction后比较；默认零，不抬floor；无窗口分支精确。')
    if path.endswith('kernel2d/entrance.py'):
        if fn in {'_first_entrance_convex', '_first_entrance_concave', 'shortest_exit'}:
            return ('exact_decision_resolvability_only', '时刻/标签/选择有理数；band只near_labels。_contact_report平方先转float下溢另为确认G2D-04。')
        if fn == 'first_entrance_brute':
            return ('sampling_corroboration_not_oracle', '扫描可漏孤立切触，文档已降为佐证；二分输出float分辨率，不改精确state。')
        return ('exact_or_float_construction', '_feature_data等在Fraction；_facet_points为浮点见证构造；覆盖零方向/输入合法性检查。')
    if path.endswith('kernel2d/exact.py'):
        return ('exact_predicate', '本模块比较操作数来自Fraction/int，未发现噪声量判分支。')
    if base in {'rational3.py', 'exact_geom.py', 'exact_sweep.py', 'g03_exact.py'}:
        return ('exact_predicate_static', '有理/整数层；正tol是显式欧氏带。非二维范围：已静态分类，全部调用路径动态证明由三维镜头负责。')
    if base == 'lp.py':
        if fn == 'reduced_sign':
            return ('speed_filter_exact_fallback', 'E界外接受符号，界内/inf/nan退rational；该过滤界本子任务未独立动态证明。')
        if line < 491:
            return ('heuristic_with_exact_candidate_certification', '浮点层候选/阈值不应决定最终答案；solve经_Exact.certify失败有理数simplex兜底。root LP镜头负责真兜底检查。')
        return ('exact_certificate_or_metadata', '有理数证书/精确simplex；浮点显示数值、循环计数，非二维范围未全路径动态证实。')
    if base in {'limit.py', 'limit_multi.py'}:
        return ('resolution_or_explicit_force_display', 'U阈值只resolvability邻域报告；tol*fmax只forces/active截断展示，模块文档明确不当证书；模型/自校验root独审。')
    if base == 'margin.py':
        if fn in {'nearest_point_on_convex_entrance', 'distance_to_convex_entrance', 'inflated_normal'}:
            return ('root_confirmed_public_projection_cancellation', 'See ASCII semantic classification supplied by repair_inventory_encoding.py.')
        if fn in {'_contact_window', '_penetration_within_window', 'inflated_membership', 'margin_contacts', '_witness_squared'}:
            return ('explicit_domain_window_or_exact', '原始坐标有理平方距/显式window、delta与atol；exact_closed保护浮点gap显示；窗口可靠性另镜头。')
        if fn in {'_repair_folded_construction', '_resolve', 'body_distance'}:
            return ('construction_fail_closed_or_window_report', '浮点差界只修复构造/审核selfcheck，state和最小平方距另在精确层；未证明每种构造都相容。')
        return ('explicit_report_policy', 'rounding_floor/effective_geom_tol仅输出可由用户显式选择政策，_tie_groups只窗口模式旧展示次序。')
    if base == 'covers3.py':
        return ('exact_domain_window_static', '_q有理原语/精确整数范数比较，tol/extent/window显式；其他浮点只构造或元数据。三维逐路径动态证明由三维镜头。')
    if base == 'g03.py':
        if fn == 'g0_distance_completeness3':
            return ('confirmed_g0_answer_changing_noise', 'G2D-01同型3D补证：1e-12*L预筛跳真实正间隙，内部法锥毁坏仍pass。')
        return ('exact_convex_g0_static', '三票转独立整数/有理oracle、精确被测convex view；三维镜头负责完整独立性。')
    if base == 'geom3.py':
        if fn in legacy3:
            return ('legacy_diagnostic_or_dormant_noise_static', '旧浮点凸性统计/拓扑诊断/被新精确重叠替代的内部helper；是否其它调用仍活用需完整调用图核验，未全证实。')
        if fn == '_seg_seg_distance':
            return ('construction_heuristic_exact_fallback', '角小nn<=1e-8*a*c或非有限/下溢到有理segment距离；一般支路浮点构造，未单独穷尽对拍。')
        if fn == '_point_face_distance':
            return ('legacy_float_oracle_shared_primitives', 'brute_feature_distance仍浮点投影/精确面内对舍入投影判定；不是默认距离的最终精确选择，活用于审核，未全动态证明。')
        return ('exact_forward_or_construction_static', 'polyhedra_overlap→surface_overlap, hull/merge→精确层；其余float几何构造/工作排序，需看函数上下文。')
    if base == 'interlock.py':
        return ('nominal_report_resolution_or_exact_event', 'nz噪声压制只候选报告/兼容label；exact escape另surface_events根决定；r/gtol聚类只兼容labels，不是exact_height。')
    if base == 'entrance3.py':
        if fn == 'first_entrance_brute':
            return ('sampling_legacy_band_corroboration', '浮点平移+effective_geom_tol+ztol仍旧扫描佐证，doc明确非独立主oracle，不给准确孤立事件保证。')
        return ('exact_event_or_float_report_static', 'roots/labels/merge精确；tol显式角窗。本二维镜头不确认三维每个路径。')
    if base == 'frozen.py':
        return ('primal_branch_analytic_dual_path_static', '冻结片内解析/朝向分支，与显式domain tol；没有本子任务动态验证，root/三维镜头负责。')
    if path.endswith('readers/bdda_geom.py'):
        return ('legacy_adapter_simplification', 'dup_tol=max(requested,floor)删近邻顶点，输入归一化有文档；dup_tol=0非原数据保真，对核心exact不能混淆。')
    if '/readers/' in path or base == 'contact_record.py':
        return ('parsing_contract_or_adapter', '字段类型/长度/映射/显式legacy adapter，不在本子任务几何正确性动态验证。')
    if base == 'dual.py':
        return ('scalar_branch_no_tolerance', 'primal择支/通道合法性/定义域；未发现噪声带。')
    return ('static_unverified', '静态提取但未逐路径动态验证。')
for p in sources:
    path = p.as_posix()
    s = p.read_text(encoding='utf-8-sig')
    t = ast.parse(s)
    parent = {c: n for n in ast.walk(t) for c in ast.iter_child_nodes(n)}
    for n in ast.walk(t):
        if not isinstance(n, ast.Compare):
            continue
        current = n
        fn = '<module>'
        qual = []
        while current in parent:
            current = parent[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)) and fn == '<module>':
                fn = current.name
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qual.append(current.name)
        expression = ast.get_source_segment(s, n)
        names = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)}
        constants = [x.value for x in ast.walk(n) if isinstance(x, ast.Constant) and isinstance(x.value, float)]
        target = bool(names & seeds) or any((k in expression for k in ('tol', 'band', 'floor', 'noise', 'bound', '1e-', '_PIV', '_FEAS', 'window', 'threshold', '_UNCERTAIN', '_DUAL', '_RAY', '_INFEAS', '_PERTURB')))
        category, reason = classify(path, fn, n.lineno)
        row = {'file': path, 'line': n.lineno, 'function': '.'.join(reversed(qual)), 'comparison': expression, 'tolerance_syntax_candidate': target, 'float_literal_candidate': bool(constants), 'category': category, 'classification_basis': reason, 'verification_scope': 'enclosing function classification; not a proof of each dynamically typed operand'}
        rows.append(row)
        if target:
            candidates.append(row)
call_sites = []
for p in sources:
    s = p.read_text(encoding='utf-8-sig')
    t = ast.parse(s)
    for n in ast.walk(t):
        if isinstance(n, ast.Call):
            name = n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else ''
            if name in {'polygons_overlap', 'point_in_polygon', 'segments_properly_cross', 'polyhedra_overlap', 'eff_tol', 'effective_geom_tol', 'round_floor', 'rounding_floor', 'noise_floor', '_cover_escape_z'}:
                call_sites.append({'file': p.as_posix(), 'line': n.lineno, 'callee': name, 'call': ast.get_source_segment(s, n)})
out = {'scope': 'all src/eab/**/*.py; AST exhaustive Compare inventory, extra noise-policy call-site inventory', 'limitations': ['所有Compare都提取；动态Python不能从AST精确推断float类型，分类是函数级语义审阅，不冒充每一处分支都独立动态证明。', '本子任务深入kernel2d、predicates、margin；3D/LP/limit的静态分类须与其他镜头的独立动态证据合并。', '无过滤安全形式化全域证明，既有随机对拍不能当无反例证明。'], 'modules': len(sources), 'total_comparisons': len(rows), 'tolerance_syntax_candidates': len(candidates), 'category_counts': dict(collections.Counter((r['category'] for r in rows))), 'comparisons': rows, 'tolerance_candidates': candidates, 'noise_policy_call_sites': call_sites}
(root / 'review/notes/tolerance_inventory.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps({k: out[k] for k in ('modules', 'total_comparisons', 'tolerance_syntax_candidates', 'category_counts')}, ensure_ascii=False, indent=2))
import runpy
runpy.run_path(str(Path(__file__).with_name("repair_inventory_encoding.py")))
