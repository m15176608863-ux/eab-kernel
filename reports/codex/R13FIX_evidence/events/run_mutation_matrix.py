import inspect,json,sys,time,traceback
from pathlib import Path
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import eab.kernel2d.entrance as E2
import eab.kernel3d.entrance3 as E3
import test_kernel2d_entrance as T2
import test_entrance3 as T3
rows=[]
def run(label,fn,count):
 t=time.perf_counter(); failures=[]
 for seed in range(count):
  try:fn(seed)
  except AssertionError as exc:failures.append(dict(seed=seed,message=str(exc),traceback=traceback.format_exc()))
 row=dict(stage=label,passed=count-len(failures),failed=len(failures),seconds=time.perf_counter()-t,failures=failures)
 rows.append(row);print(label, row['passed'],row['failed'],flush=True)
source=inspect.getsource(E3.first_entrance3);needle='tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x)'
namespace=dict(vars(E3));exec(compile(source.replace(needle,'tuple(scalar_rational(_mapped_value) for _mapped_value in x0)'),'<r13-3d-mutant>','exec'),namespace)
T3.first_entrance3=namespace['first_entrance3'];run('post_fix_3d_mutant',T3.test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs,24)
source=inspect.getsource(E2._first_entrance_convex);namespace=dict(vars(E2));exec(compile(source.replace('x = vector_rational(exact_x)','x = vector_rational(x0)'),'<r13-2d-mutant>','exec'),namespace)
E2._first_entrance_convex=namespace['_first_entrance_convex']
fn=T2.test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs
legacy=inspect.getsource(fn)
legacy='\n'.join(line for line in legacy.splitlines() if not any(marker in line for marker in ('from r13_event_oracle','interval = convex_ray_interval_2d','assert interval is None','assert interval is not None','assert_event_binding(')))
namespace=dict(vars(T2));exec(compile(legacy,'<r13-preserved-pre-fix-2d-gate>','exec'),namespace)
run('pre_fix_2d_equivalent_gate_mutant',namespace[fn.__name__],30)
run('post_fix_2d_mutant',fn,30)
(ROOT/'reports/codex/R13FIX_evidence/events/mutation_matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
assert rows[0]['failed']==23 and rows[0]['passed']==1
assert rows[1]['failed']==0 and rows[1]['passed']==30
assert rows[2]['failed']>0
assert all(f['message']=='event position midpoint binding' for row in (rows[0],rows[2]) for f in row['failures'])
