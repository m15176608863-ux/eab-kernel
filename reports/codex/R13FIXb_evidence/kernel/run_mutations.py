import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path.cwd(); dest=ROOT/'reports/codex/R13FIXb_evidence/kernel'; tmp=ROOT/'reports/codex/R13FIXb_evidence/tmp'
cases={
'event_label_time_swap':'test_surface_event_label_time_binding_matches_independent_xy_elimination',
'raw_dot_early':'test_in_domain_raw_dot_cancellation_is_not_erased',
'oracle_scalar_early':'test_exact_public_vector_arithmetic_matches_inline_rational',
'projection_parameter_early':'test_2d_exact_oracle_quantities_match_independent_formulas',
'sampler_bounds_early':'test_random_coordinate_samplers_round_only_final_affine_value',
 'translated_coordinate_early':'test_exact_surface_constructions_and_intersections',
 'event_time_early':'test_surface_events_non_dyadic_exact_times',
 'area_coordinate_early':'test_exact_area_nondyadic_raw_values_match_shoelace',
 'support_check_removed':'test_random_polygon_named_support_domain_rejection',
}
results=[]
for name,test in cases.items():
 env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',TEMP=str(tmp),TMP=str(tmp),R13_KERNEL_MUTANT=name,PYTHONPATH=os.pathsep.join((str(ROOT/'src'),str(tmp))))
 cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','r13_kernel_mutants',f'tests/test_r13fixb_kernel_numeric.py::{test}','--tb=short']
 start=time.perf_counter();p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf8',errors='replace');elapsed=time.perf_counter()-start
 log=p.stdout+p.stderr;(dest/f'mutant_{name}.log').write_text(log,encoding='utf8')
 results.append(dict(mutant=name,test=test,returncode=p.returncode,killed=p.returncode==1,seconds=elapsed,tail=log.strip().splitlines()[-1],log=f'mutant_{name}.log'))
 print(name,p.returncode,results[-1]['tail'],flush=True)
(dest/'mutations.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if not all(r['killed'] for r in results):sys.exit(1)
