"""Review-copy mutation audit: production byte edits only inside review/copies/."""
from pathlib import Path
import shutil, subprocess, os, hashlib, json
ROOT=Path(__file__).resolve().parents[2]
COPY=ROOT/'review/copies/gates_docs_mutations'
COPY.mkdir(parents=True,exist_ok=True)
for name in ('src','tests','tools','fixtures'):
    shutil.copytree(ROOT/name,COPY/name,dirs_exist_ok=True)
shutil.copy2(ROOT/'pyproject.toml',COPY/'pyproject.toml')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
cases=[
 ('2d_boundary_to_inside','src/eab/kernel2d/exact.py','worst = min(worst, s)','worst = 1',
  ['tests/test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip']),
 ('hull_retains_nonextreme','src/eab/kernel3d/geom3.py','used=sorted({i for f in rings for i in f})','used=list(range(len(pts)))',
  ['tests/test_hull_robustness.py::test_sliver_fallback_removes_the_middle_of_three_collinear_vertices']),
 ('edge_boundary_strict','src/eab/kernel3d/covers3.py','s1 > 0 and s2 > 0 and axial == 0','s1 >= 0 and s2 >= 0 and axial == 0',
  ['tests/test_kernel3d_covers.py::test_edge_arc_of_box_edge']),
 ('merge_distinct_microplanes','src/eab/kernel3d/entrance3.py','return dot(n, sub(a, b)) == 0','return abs(dot(n, sub(a, b))) <= Fraction(1,10**9)',
  ['tests/test_entrance3_concave.py::test_degenerate_merge_keeps_parallel_planes_at_different_heights_apart',
   'tests/test_entrance3_exact.py::test_degenerate_merge_never_coalesces_distinct_exact_planes']),
]
result=[]
def run(label,nodes):
    command=[os.sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',
             '--basetemp='+str(COPY/'tmp'/label),'--tb=short',*nodes]
    process=subprocess.run(command,cwd=COPY,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output=process.stdout.decode('utf-8',errors='replace')
    (ROOT/'review/logs'/f'gates_mutation_{label}.log').write_text(output,encoding='utf-8')
    return process.returncode,output
for label,file,old,new,nodes in cases:
    path=COPY/file;before=path.read_bytes();checksum=hashlib.sha256(before).hexdigest()
    baseline_code,baseline_out=run(label+'_baseline',nodes)
    assert baseline_code==0,baseline_out
    text=before.decode('utf-8');assert text.count(old)==1,(label,text.count(old))
    try:
        path.write_bytes(text.replace(old,new).encode('utf-8'))
        code,out=run(label+'_mutant',nodes)
    finally:
        path.write_bytes(before)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==checksum
    assert code==1,(label,out)
    row={'id':label,'file':file,'source_edit':[old,new],'nodes':nodes,
         'baseline_returncode':baseline_code,'mutation_returncode':code,'restored_sha256':checksum,
         'verified_output':out}
    result.append(row)
    print(label,baseline_out.strip().splitlines()[-1],'->',out.strip().splitlines()[-1],flush=True)
(ROOT/'review/notes/gates_docs_mutations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
