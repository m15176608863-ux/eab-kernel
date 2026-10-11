"""Run final entrance mutants in isolated module namespaces, never edit source."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
cases=[
    ('predecessor_float','return (previous + t) / 2','return float(t) - 2.0e-9',
     'test_exact_predecessor_selfcheck_never_rounds_back_to_the_event','bodies already touch at t = 1e+20'),
    ('coplane_tolerance','return dot(n, sub(a, b)) == 0','return abs(dot(n, sub(a, b))) <= Fraction(1, 10**9)',
     'test_degenerate_merge_never_coalesces_distinct_exact_planes','FF'),
    ('predecessor_float_midpoint','return (previous + t) / 2','return float((previous + t) / 2)',
     'test_preceding_event_probe_is_strictly_inside_the_exact_interval','assert'),
]
if len(sys.argv)>1:
    case=next(c for c in cases if c[0]==sys.argv[1])
    name,needle,replacement,test,marker=case
    sys.path.insert(0,str(ROOT/'src'))
    import eab.kernel3d.entrance3 as E
    source=Path(E.__file__).read_text(encoding='utf-8-sig')
    assert source.count(needle)==1
    exec(compile(source.replace(needle,replacement),E.__file__,'exec'),E.__dict__)
    import pytest
    raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','tests/test_entrance3_exact.py::'+test,
                                  '--basetemp',str(OUT/'tmp'/('final_mutant_'+name))]))
path=ROOT/'src/eab/kernel3d/entrance3.py'
before=hashlib.sha256(path.read_bytes()).hexdigest()
results=[]
for name,needle,replacement,test,marker in cases:
    start=time.perf_counter()
    p=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__)),name],cwd=ROOT,
                     env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8'),
                     text=True,encoding='utf8',errors='replace',capture_output=True)
    log=p.stdout+p.stderr
    (OUT/'entrance'/('final_mutant_'+name+'.log')).write_text(log,encoding='utf8')
    # A collection/import error is not a kill. Inspect target failure separately.
    killed=p.returncode==1 and ('FAILED tests/test_entrance3_exact.py::'+test) in log and marker in log
    results.append(dict(name=name,test=test,returncode=p.returncode,killed=killed,
                        target_marker=marker,seconds=time.perf_counter()-start))
    assert killed,log
after=hashlib.sha256(path.read_bytes()).hexdigest()
assert before==after
(OUT/'entrance'/'final_mutants.json').write_text(json.dumps(dict(source_sha256=before,
    source_unchanged=True,results=results),indent=2)+'\n',encoding='utf8')
print(json.dumps(results,indent=2))
