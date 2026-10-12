import sys,json,subprocess,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
# Original 50-entry JSON has no IDs: indices below are zero-based.
items=[
(23,'geom3 transverse plane-noise omission','tests/test_e5a2_surface.py::test_legacy_surface_membership_and_crossing_are_exact'),
(24,'VV3 cone threshold erases real E vertices','tests/test_geom3_e5a.py::test_exact_thin_hull_facet_is_not_reported_as_zero_area_by_float_cancellation'),
(27,'edge arc symmetric noise grants wrong side','tests/test_edge_arc_per_side.py'),
(28,'G03 hull-face normal thickness two-rulers','tests/test_g03_e5a.py::test_fifth_round_ratio_yaw_inputs_have_zero_exemptions'),
(30,'near-parallel segment distance inconsistent witnesses','tests/test_geom3_e5a.py::test_g6e_near_parallel_oracle_uses_consistent_exact_distance'),
(35,'EE finite extent ignores line conditioning','tests/test_near_parallel_edges.py'),
(38,'G03 extra vertices excused by low_e','tests/test_g03_e5a.py::test_g0_vote_three_rejects_false_local_vertices_instead_of_low_e_exemption'),
(39,'facet_vote3 default undefined L','tests/test_g03_e5a.py::test_default_facet_vote_has_no_undefined_resolution_scale'),
(41,'G03 exact ridge hidden by support bands','tests/test_g03_e5a.py::test_fifth_round_original_roof_input_is_not_flattened_by_support_bands'),
(42,'G03 noncoplanar seeds fitted as support plane','tests/test_g03_e5a.py::test_fifth_round_original_chamfer_has_no_fitted_nonplanar_support'),
(43,'Gordan barycentric absolute threshold drops real cone','tests/test_covers3_g0_vote2.py'),
(45,'hull noise-scale mutation escapes old selfcheck','tests/test_hull_robustness.py::test_noise_floor_in_the_hull_has_teeth'),
(49,'G03 widening unresolved bands has no tooth','tests/test_g03_e5a.py::test_true_ridges_are_checked_not_hidden_below_a_resolution_threshold'),
]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
outputs=[]
for index,scenario,node in items:
 cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',node,'--basetemp='+str(ROOT/'review/tmp_geom3_history'/str(index))]
 t=time.perf_counter();r=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
 (ROOT/f'review/logs/geom3j_history_{index:02}.log').write_text(r.stdout,encoding='utf-8')
 row={'raw_index':index,'source_summary':scenario,'equivalent_replay':node,'returncode':r.returncode,'wall_s':time.perf_counter()-t,'verified_output':r.stdout[-1600:]}
 outputs.append(row);print(index,r.returncode,r.stdout.strip().splitlines()[-1],flush=True)
(ROOT/'review/logs/geom3j_historical_replay.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(row['returncode']==0 for row in outputs)
