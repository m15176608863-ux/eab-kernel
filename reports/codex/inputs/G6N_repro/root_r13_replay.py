"""WO-G6N: replay G6M-01/02/03 against current HEAD, no source writes."""
from pathlib import Path
from fractions import Fraction as F
import hashlib, importlib.util, json, math, os, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tools'), str(ROOT/'tests')]
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
spec = importlib.util.spec_from_file_location('g6n_gate', ROOT/'tools/check_exact_construction.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
# Extract literal sources from the read-only previous review, without executing
# its file-writing/old-assertion part.
previous = Path('D:/eab-wt/g6m/review/repro/static_lifecycle_bypass.py').read_text(encoding='utf-8')
ns = {}
exec(previous[previous.index("PREFIX="):previous.index('q=F(1,2**1075)')], ns)
rows = []
for name, source in ns['SOURCES'].items():
    path = 'src/eab/g6m_'+name+'_new.py'
    issues = gate.scan_text(source, path)
    rows.append({'prior_id':'G6M-01','case':name,'diagnostics':issues,
                 'closed':bool(issues),'legacy_exclusions':len(gate._subset.approved_sites(source,path))})
    assert issues and not gate._subset.approved_sites(source,path)

# The actual random gate must fail specifically on the returned position,
# not a static stale-waiver diagnostic or an unrelated chosen witness.
import inspect
import test_entrance3 as original
from eab.kernel3d import entrance3 as E3
original.test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs(0)
source = inspect.getsource(E3.first_entrance3)
needle = 'tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x)'
assert source.count(needle) == 1
environment = dict(vars(E3))
exec(compile(source.replace(needle, 'tuple(scalar_rational(_mapped_value) for _mapped_value in x0)'),
             '<g6n-r13-real-entrance-return-mutant>', 'exec'), environment)
saved = original.first_entrance3
original.first_entrance3 = environment['first_entrance3']
try:
    try:
        original.test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs(0)
    except AssertionError as error:
        assert 'event position midpoint binding' in str(error), str(error)
        rows.append({'prior_id':'G6M-02','closed':True,'target_assertion':str(error),
                     'baseline_seed0':'passed','mutation':'inside first_entrance3 x -> x0'})
    else:
        raise AssertionError('old defect escaped current numerical gate')
finally:
    original.first_entrance3 = saved

canon = (ROOT/'docs/canon_map.md').read_text(encoding='utf-8-sig').splitlines()[2]
assert '不再锁全库依赖' in canon and '已知 int/Fraction' in canon and '辅助代码检查' in canon
rows.append({'prior_id':'G6M-03','closed':True,'current_intro':canon})
out={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
     'results':rows,'all_three_prior_findings_closed':True,
     'tracked_source_written':False}
(ROOT/'review/evidence/r13_replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
