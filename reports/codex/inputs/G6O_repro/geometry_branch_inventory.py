from pathlib import Path
import json,re
root=Path.cwd();allrows=json.loads((root/'review/evidence/all_source_comparisons.json').read_text(encoding='utf-8'))
rows=[r for r in allrows if r['file'].startswith(('src/eab/kernel2d/','src/eab/kernel3d/')) or r['file'] in {'src/eab/predicates.py','src/eab/margin.py'}]
legacy={'_inward_vertex_direction','_edge_edge_contacts','_active_normals','_gordan_direction','_min_norm_on_simplex','_contact_cone_witness','_ray_directions','_sliver_middle_vertex','_tri_axes'}
report={'_normal_noise','_cover_escape_z','_candidates_uncached','_escape_solution','escape_height_covers','_construction_error_exceeds','_minimum_witness_distance','g0_distance_completeness','g0_exit_completeness','_display_witness_distance','g0_distance_completeness3','Polyhedron.manifold_issues','Polyhedron._find_interior_point','first_entrance_brute'}
filters={'orient2d','orient3d','cross2_sign','dot2_sign','_iv','_ia','_is','_im','_edge_window_filter','polygon_locate'}
window={'_cross_ge_window','_cone_accepts','_cone_nonreflex','normal_cone','in_cone','_angle_window2','_ve_side_directions','_in_segment_exact','_feature_in_gap_window','enumerate_covers','membership_convex','_outside_dot_band','_qvertex_state_cached','_qedge_contains','_qparameter_in_extent','_cover_in_window','enumerate_covers3','membership_convex3','reflex_vertices','point_in_polygon','_point_in_polygon','segments_properly_cross','_triangles_overlap','_interiors_overlap','polygons_overlap','polygon_locate_fraction','point_in_surface','segment_crosses','_triangles_near','surface_overlap','_in_exact_boundary_band'}
for r in rows:
    scope=r['scope'];file=r['file'];cat='exact_rational_or_integer_or_discrete_branch'
    reason='Core source uses rational/integer supplied-coordinate data before truth branches; comparison against 0.0 does not imply a floating operand. This row belongs to a reviewed function family, not a new exhaustive numeric proof.'
    if scope in legacy and file.endswith(('geom3.py','geom.py')):
        cat='inactive_private_legacy';reason='src call search has only private internal/declaration references; no public overlap, membership or hull answer consumes this noise chain. It is not certified by a rational fallback.'
    elif scope in filters:
        cat='certified_float_filter_or_interval_bound';reason='Finite separated sign/interval may return early; all inconclusive/nonfinite bounds take exact Fraction path. Independent stress plus filtered-predicate targeted gate passed.'
    elif scope in report:
        cat='construction_diagnostic_or_nominal_report';reason='Affects displayed witness error, nominal cover labels/ties, sampled corroboration or candidate search. Physical membership/event root uses exact solver; a reported interior candidate is independently exact-tested.'
    elif scope in window:
        cat='explicit_caller_window_with_exact_comparison';reason='tol, extent_tol, cone_tol or window is caller data; squared/rational comparisons do not add coordinate noise to default truth. Nonconvex bands have documented incompleteness.'
    if scope.startswith('Polyhedron.') and scope.split('.')[-1] in {'edge_noise','face_noise','dihedral_noise','metrics','vertex_edges','vertex_edge_dirs','dihedral_turn','face_normal','face_area','volume','centroid'}:
        cat='construction_or_diagnostic_result';reason='Magnitude/angle reporting; zero and sign choices use exact raw quantities. Final expression/declared support range is a separate construction obligation covered by domain team.'
    if scope in {'first_entrance','_first_entrance_convex','_first_entrance_concave','shortest_exit'} and any(re.search(r'\b'+k+r'\b',r['comparison']) for k in ('band','band2','ctol','tol','r')):
        cat='event_answer_exact_near_labels_reporting';reason='Exact event roots and minimum squared depths select the answer. near_labels uses explicit/reporting window separately.'
    if file=='src/eab/margin.py':
        cat='exact_relation_distance_or_explicit_window'
        reason='Source squared-distance certificates control default relation, contact, delta and band branches. Final witness displays do not select these states.'
        if scope in {'_tie_groups','cover_witness','_repair_folded_construction','characteristic_length','rounding_floor','_effective_geom_tol_exact','boundary_band','contact_resolution'}:
            cat='construction_diagnostic_or_window_report'
            reason='Distance display, fixed geometric witness construction, coordinate roundoff estimate or explicitly requested nominal/tie report. No implicit band changes the default relation.'
        if scope=='_resolve' and 'abs(dmin - truth)' in r['comparison']:
            cat='construction_selfcheck_rejection_not_truth_band'
            reason='Exact minimum squared distance is independently required equal to truth2 in this same if; the 4*rnd bound separately rejects malformed floating witnesses, not physical classification.'
        if scope=='MarginContact.closed':
            cat='exact_certificate_or_user_constructed_record_view'
            reason='Production separated reports retain _exact_closed; manually constructed record without a certificate uses its caller supplied float model. Penetrating sentinel tiny delta final-boundary concern is delegated to support audit.'
    if file.endswith('interlock.py') and scope=='escape_height_covers' and 'F(display)' in r['comparison']:
        cat='CONFIRMED_G6O_GEOM_01_output_range_hole'
        reason='The following nextafter(max_binary64,+inf) publishes infinity for a finite rational root in the RN-finite cell. No finite check follows; six-case grid confirms three silent nonfinite displays. Exact root/state are unaffected.'
    r['geometry_audit_class']=cat;r['rationale']=reason
(root/'review/evidence/geometry_branch_inventory.json').write_text(json.dumps({'scope':'Geometry, margin and predicates only; root inventory supplies other modules. Function-family manual classification guided by inspected source, not claim that every dynamic path or every numerical input was proved.','comparison_rows':len(rows),'legacy_reader_policy':'readers/bdda_geom.strip_duplicate_vertices performs documented legacy preprocessing with dup_tol/rounding_floor. This changes the input model before exact geometry and is separately indexed by root; it is not counted as a hidden predicate defect.','limitations':'Nominal interlock labels, general transcendental construction and all user-defined scalar protocols are not full-domain theorems. No current geometry truth noise-band counterexample was found.','rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
from collections import Counter
print(len(rows),dict(Counter(r['geometry_audit_class'] for r in rows)))
