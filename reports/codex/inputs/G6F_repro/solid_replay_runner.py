from pathlib import Path
import json,re,subprocess,os,sys,time
root=Path(__file__).resolve().parents[2]
raw=json.loads((root/'reports/codex/inputs/g6e_findings_raw.json').read_text(encoding='utf-8'))['findings']
ids=[7,24,25,28,29,31,34,37,40,42,43,44]
results=[]
for i in ids:
    text=raw[i-1]['how_to_reproduce']
    if "<<'EOF'" in text:
        code=text.split("<<'EOF'",1)[1].split('\nEOF',1)[0].lstrip('\n')
    elif i in (42,43,44):
        name={42:'F2.py',43:'F3.py',44:'F4.py'}[i]
        code=text.split('--- '+name+' ---',1)[1].split('--- output ---',1)[0].strip()
        if i==42: code=code.split('# aligned rulers',1)[0]
        if i==43: code=code.split('orig = g03._plane_from_points',1)[0]
    elif i==40:
        code='''from eab.kernel3d.geom3 import box, convex_hull_3d, sub
from eab.kernel3d.covers3 import local_facets3
from eab.kernel3d.g03 import facet_vote3
A=box(half=(1,1,1)); B=box(center=(0.3,0.2,3),half=(2,1.5,0.7))
d=[sub(b,a) for a in A.verts for b in B.verts]
print(facet_vote3(A,B,local_facets3(A,B,1e-12),convex_hull_3d(d),d))'''
    else: raise RuntimeError(i)
    # Every process imports only the reviewed tree, independent from old paths.
    code="import sys\nsys.path[:0]=['src','tests']\n"+code
    path=root/f'review/repro/solid_g6e_{i:02d}.py'
    path.write_text(code,encoding='utf-8')
    start=time.monotonic()
    p=subprocess.run([sys.executable,'-X','utf8',str(path)],cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,encoding='utf-8',errors='replace')
    output=p.stdout+p.stderr
    log=root/f'review/logs/solid_g6e_{i:02d}.log';log.write_text(output,encoding='utf-8')
    row={'g6e_id':i,'kind':'original-input replay','exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'script':str(path.relative_to(root)),'log':str(log.relative_to(root)),'verified_output':output}
    results.append(row)
    print('REPLAY',i,'exit',p.returncode,'seconds',round(row['elapsed_seconds'],2));print(output[:3500],flush=True)
(root/'review/notes/solid_replay_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
