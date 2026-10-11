"""Source mutations in isolated package copies; the live tree is never patched."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
source=ROOT/'src/eab/kernel3d/g03.py'
original=source.read_bytes()
mutants=[
 ('G01_skip_boundary','        brute=oracle.overlap(source_av,source_bv,x)',
  '        if cov == 0:\n            continue\n        brute=oracle.overlap(source_av,source_bv,x)',
  'tests/test_g03_e5a.py::test_g0_vote_one_checks_all_exact_vertices_edge_midpoints_and_face_centers',
  ['assert r.boundary_probes==r.boundary_checked==26']),
 ('G02_drop_comparison_label','    for lab in sorted(facets):','    for lab in sorted(facets)[1:]:',
  'tests/test_covers3_g0_vote2.py::test_vote2_local_facets_equal_hull_facets_on_random_pairs',
  ['assert rep.facet_symmetric_diff == []']),
]
records=[]
for mid,old,new,test,assertions in mutants:
    dest=OUT/'tmp'/mid
    shutil.copytree(ROOT/'src/eab',dest/'eab',dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    text=original.decode('utf-8')
    assert text.count(old)==1,(mid,text.count(old))
    target=dest/'eab/kernel3d/g03.py'
    with target.open('w',encoding='utf-8',newline='') as stream:stream.write(text.replace(old,new))
    cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',
         '-o',f'pythonpath={dest.as_posix()}',f'--basetemp={dest/"pytest"}',test,'--tb=short',f'--junitxml={OUT/mid}.xml']
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['TEMP']=env['TMP']=str(OUT/'tmp')
    result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    output=result.stdout+result.stderr
    (OUT/f'{mid}.log').write_text(output,encoding='utf-8')
    killed=result.returncode==1 and all(a in output for a in assertions)
    record=dict(id=mid,killed=killed,returncode=result.returncode,old=old,new=new,test=test,
                failure_assertions=assertions,source_sha256=hashlib.sha256(original).hexdigest(),
                mutant_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    records.append(record);print(mid,killed,result.stdout[-300:])
assert source.read_bytes()==original
(OUT/'g03_mutations.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
assert all(r['killed'] for r in records)
