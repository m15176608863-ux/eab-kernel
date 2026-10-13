"""Audit runners only; no tracked edits. Logs contain the actual assertions."""
from pathlib import Path
import subprocess,json,time,os
ROOT=Path(__file__).resolve().parents[2]
nodes=[
'tests/test_kernel2d_exact.py::test_sat_oracle_uses_no_kernel_geometry_primitive',
'tests/test_kernel2d_exact.py::test_g0_support_and_hull_oracles_use_no_tested_geometry_primitive',
'tests/test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip',
'tests/test_kernel3d_covers.py::test_g0_gate_has_teeth_flipped_normals_are_caught',
'tests/test_kernel3d_covers.py::test_position_independence_gate_has_teeth_absolute_edge_direction',
'tests/test_g03_e5a.py::test_g0_oracle_has_no_tested_geometric_primitive_import',
'tests/test_g03_e5a.py::test_g0_oracle_keeps_original_points_before_a_defective_convex_view',
'tests/test_hull_robustness.py::test_sliver_fallback_removes_the_middle_of_three_collinear_vertices',
'tests/test_hull_robustness.py::test_exact_convexity_oracle_catches_a_point_the_build_was_made_to_ignore',
'tests/test_margin_penetration.py::test_contact_resolution_gate_has_teeth',
'tests/test_margin.py::test_theorem_two_gate_has_teeth_shrinking_the_nearest_point_is_caught',
'tests/test_margin.py::test_lipschitz_gate_has_teeth',
'tests/test_margin.py::test_lipschitz_gate_global_pairs_have_their_own_teeth',
'tests/test_r14_domain.py::test_shape_complete_coordinate_rounding_has_an_internal_mutation_tooth',
'tests/test_r14_dual.py',
'tests/test_r14_cone.py',
'tests/test_r14_claims.py',
'tests/test_r14_readers.py',
'tests/test_doc_pointers.py',
]
cmd=['python','-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*nodes,'--basetemp='+str(ROOT/'review/tmp_root_teeth')]
t=time.monotonic()
with (ROOT/'review/logs/root_selected_teeth.log').open('w',encoding='utf-8') as f:
 f.write('COMMAND: '+subprocess.list2cmdline(cmd)+'\n');f.flush();result=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'})
summary={'nodes':nodes,'command':cmd,'seconds':time.monotonic()-t,'exit_code':result.returncode,'scope':'selected independent-oracle, genuine internal mutation and R14 targeted gates; not all rewritten gates'}
(ROOT/'review/evidence/root_selected_teeth.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
