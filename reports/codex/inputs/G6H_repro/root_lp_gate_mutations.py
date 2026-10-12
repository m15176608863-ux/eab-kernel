"""G6E23/47 migrated gates: physical copied-tree mutants, original tree untouched."""
from pathlib import Path
import sys,shutil,subprocess,os,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
copy=ROOT/'review/copies/root_lp_gates'
copy.mkdir(parents=True,exist_ok=True)
for folder in ('src','tests'):
    shutil.copytree(ROOT/folder,copy/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
for name in ('pyproject.toml','conftest.py'):
    if (ROOT/name).exists():shutil.copy2(ROOT/name,copy/name)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
cases=[
 dict(id='G6E23-unbounded-screen-off',file='src/eab/limit_multi.py',
      old='if rmin.status == OPTIMAL and rmin.x[ia] > 0.0:',new='if False:',
      nodes=['tests/test_limit_exact_selfcheck.py::test_multi_unbounded_screen_covers_both_rejection_branches_and_nonzero_body']),
 dict(id='G6E47-scale-based-power-acceptance-all-target-gates',file='src/eab/limit.py',
      old='admissible = all(p >= 0 for p in power) and all(v >= 0 for v in yr) and drive >= 1',
      new='admissible = all(p >= -Fraction(1,10**7)*max([Fraction(1)]+[abs(t) for t in y]) for p in power) and all(v >= 0 for v in yr) and drive >= 1',
      nodes=['tests/test_limit_exact_selfcheck.py::test_exact_admissibility_has_no_tall_body_or_other_body_speed_tolerance',
             'tests/test_limit_multi.py::test_a_far_body_does_not_loosen_the_self_check',
             'tests/test_limit_exact_selfcheck.py::test_multi_exact_duality_rejects_statically_feasible_suboptimal_interpolation'])
]
out=[]
for c in cases:
    path=copy/c['file']; data=path.read_bytes(); text=data.decode('utf8')
    assert text.count(c['old'])==1,(c['id'],text.count(c['old']))
    def run(mode):
        cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*c['nodes'],
             '--basetemp='+str(ROOT/'review/tmp_root_gate'/c['id']/mode)]
        r=subprocess.run(cmd,cwd=copy,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8')
        (ROOT/'review/logs'/f"{c['id']}_{mode}.log").write_text(r.stdout,encoding='utf8')
        return dict(exit_code=r.returncode,output=r.stdout,command=cmd)
    baseline=run('baseline')
    try:
        path.write_bytes(text.replace(c['old'],c['new']).encode('utf8'))
        mutant=run('mutant')
    finally:path.write_bytes(data)
    restored=hashlib.sha256(path.read_bytes()).hexdigest()==hashlib.sha256(data).hexdigest()
    out.append(dict(**c,baseline=baseline,mutant=mutant,restored_sha256=restored))
    print(c['id'],'baseline=',baseline['exit_code'],'mutant=',mutant['exit_code'],'restored=',restored)
    print(mutant['output'][-1800:])
(ROOT/'review/notes/root_lp_gate_mutations.json').write_text(json.dumps(out,indent=2),encoding='utf8')
