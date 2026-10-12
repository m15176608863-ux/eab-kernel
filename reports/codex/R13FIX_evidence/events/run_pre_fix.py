import sys,inspect,json,time,traceback
from pathlib import Path
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import eab.kernel3d.entrance3 as E
import test_entrance3 as T
needle='tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x)'
source=inspect.getsource(E.first_entrance3)
assert source.count(needle)==1
namespace=dict(vars(E));exec(compile(source.replace(needle,'tuple(scalar_rational(_mapped_value) for _mapped_value in x0)'),'<r13-return-start-mutant>','exec'),namespace)
T.first_entrance3=namespace['first_entrance3']
start=time.perf_counter();rows=[]
for seed in range(24):
    try:T.test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs(seed)
    except Exception as exc:rows.append(dict(seed=seed,status='red',error=repr(exc),traceback=traceback.format_exc()))
    else:rows.append(dict(seed=seed,status='green'))
result=dict(stage='pre_fix_existing_gate_real_internal_x_to_x0_mutation',rows=rows,passed=sum(r['status']=='green' for r in rows),failed=sum(r['status']=='red' for r in rows),seconds=time.perf_counter()-start)
print(json.dumps(result,ensure_ascii=False,indent=2));(ROOT/'reports/codex/R13FIX_evidence/events/pre_fix_existing_mutant.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
