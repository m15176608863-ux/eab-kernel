"""Replay G6E gate gaps through current production paths in an isolated copy."""
from pathlib import Path
import shutil,subprocess,os,json,hashlib,sys
ROOT=Path(__file__).resolve().parents[2]
COPY=ROOT/'review/copies/docs_more_mutations'
COPY.mkdir(parents=True,exist_ok=True)
for name in ('src','tests','tools','fixtures'):
    shutil.copytree(ROOT/name,COPY/name,dirs_exist_ok=True)
shutil.copy2(ROOT/'pyproject.toml',COPY/'pyproject.toml')
cases=[
 ('g6e08_remove_extent',8,'src/eab/kernel3d/interlock.py','if c is not None and c.in_extent:', 'if c is not None:',
  ['tests/test_interlock_candidates_contract.py::test_every_public_candidate_is_a_real_contact_at_its_own_height']),
 ('g6e35_zero_public_extent',35,'src/eab/kernel3d/interlock.py','return [(z, lab) for z, lab, _, _ in _candidates(A, B, offset, tol, gtol)[0]]',
  'return [(z, lab) for z, lab, _, _ in _candidates(A, B, offset, tol, 0.0)[0]]',
  ['tests/test_interlock_candidates_contract.py::test_public_candidates_keep_both_branches_inside_the_predicate_band']),
 ('g6e46_weaken_supporting_certificate',46,'src/eab/kernel3d/geom3.py',
  'if not any(n) or any(_eg.dot(n,_eg.sub(_eg.vector(q),a)) > 0 for q in pts):',
  'if not any(n) or any(_eg.dot(n,_eg.sub(_eg.vector(q),a)) > Fraction(1,10**9) for q in pts):',
  ['tests/test_hull_robustness.py::test_exact_convexity_oracle_catches_a_point_the_build_was_made_to_ignore']),
 ('g6e49_allow_exact_outside_vv',49,'src/eab/kernel2d/covers.py',
  'active = _open_cone(alo, ahi, d) and _open_cone(blo, bhi, d)', 'active = True',
  ['tests/test_kernel2d_covers_e3.py::test_vv_active_exact_support_not_a_roundoff_band']),
]
result=[]
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
def run(label,nodes):
    cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',
         '--basetemp='+str(COPY/'tmp'/label),'--tb=short',*nodes]
    p=subprocess.run(cmd,cwd=COPY,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    out=p.stdout+p.stderr
    (ROOT/'review/logs'/('docs_'+label+'.log')).write_text(out,encoding='utf-8')
    return p.returncode,out,cmd
for label,id,file,old,new,nodes in cases:
    path=COPY/file;before=path.read_bytes();checksum=hashlib.sha256(before).hexdigest()
    baseline,baseline_out,_=run(label+'_baseline',nodes)
    assert baseline==0,baseline_out
    text=before.decode('utf-8');assert text.count(old)==1,(label,text.count(old))
    try:
        path.write_bytes(text.replace(old,new).encode('utf-8'))
        code,out,cmd=run(label+'_mutant',nodes)
    finally: path.write_bytes(before)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==checksum
    row={'id':label,'g6e_id':id,'file':file,'source_edit':[old,new],'nodes':nodes,'command':cmd,
         'baseline_returncode':baseline,'mutation_returncode':code,'restored_sha256':checksum,'verified_output':out}
    result.append(row)
    print(label,baseline_out.strip().splitlines()[-1],'->',out.strip().splitlines()[-1],flush=True)
    assert code==1,(label,out)
(ROOT/'review/notes/docs_more_mutations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
