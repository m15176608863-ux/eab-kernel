"""Replay geometry findings from the frozen fifth-round raw JSON.
Indices are 0-based findings[] ordinals; not invented identifiers.
Only reproduction prefixes are used, never original in-memory repair sections.
"""
from pathlib import Path
import json, re, sys, subprocess, time
ROOT=Path(__file__).resolve().parents[2]
f=json.loads((ROOT/'reports/codex/inputs/g6e_findings_raw.json').read_text(encoding='utf-8-sig'))['findings']
indices=[6,25,26,27,28,29,30,33,36,37,39,40,41,42,43]
results=[]
for i in indices:
    raw=f[i]['how_to_reproduce'].replace('\\n','\n')
    code=None
    if "<<'EOF'\n" in raw:
        code=raw.split("<<'EOF'\n",1)[1].split('\nEOF',1)[0]
    elif '--- F' in raw:
        code=raw.split('.py ---\n',1)[1].split('\n--- output',1)[0]
    elif 'python -X utf8 -c "\n' in raw:
        code=raw.split('python -X utf8 -c "\n',1)[1].split('\n"',1)[0].replace("\\'", "'")
    if code is None:raise ValueError((i,raw[:80]))
    if i==39:code=code.split('facet_vote3(A,B,local_facets3',1)[0]+"print('facet_vote3', facet_vote3(A,B,local_facets3(A,B,1e-12),convex_hull_3d(d),d))\n"
    if i==40:code="""import sys;sys.path.insert(0,'src')
from eab.kernel2d.covers import convex_entrance_block,membership_convex
from eab.kernel2d.g0 import g0_convex
A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)]
def B(d,h):return [(0.,0.),(1.,0.),(1.,1.),(0.,1.),(0.,.5+h),(d,.5)]
P=B(.5e-6,1e-4)
try:convex_entrance_block(A,P,(0.,0.),1e-6);print('ERROR: accepted reflex polygon')
except ValueError as e:print('exact convex rejection:',e)
for d in [1e-5,1e-4]:print('fallback depth',d,'membership',membership_convex(A,P,(-.1+d,.2)))
"""
    if i==41:
        code=code.split('# aligned rulers',1)[0]
        code=code.replace('assert A.is_convex() and B.is_convex() and not A.manifold_issues() and not B.manifold_issues()',"print('supplied exact convexity',A.is_convex(),B.is_convex(),'explicit convex-model G0 follows')")
    if i==27:code=code.replace("'gap',facet_gap3(A,B,bad,x)","'bad-present',bad in F")
    if i==42:code=code.split('orig = g03._plane_from_points',1)[0]
    script=ROOT/f'review/repro/geometry_g6e_{i:02}.py'
    script.write_text('# Original raw finding index '+str(i)+'; current HEAD replay, no repair.\n'+code+'\n',encoding='utf-8')
    start=time.time()
    proc=subprocess.run([sys.executable,'-X','utf8',str(script)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    output=proc.stdout
    (ROOT/f'review/logs/geometry_g6e_{i:02}.txt').write_text(output,encoding='utf-8')
    row={'raw_index':i,'original_severity':f[i]['severity'],'original_file':f[i]['file'],'exit_code':proc.returncode,'seconds':round(time.time()-start,3),'script':str(script.relative_to(ROOT)),'log':f'review/logs/geometry_g6e_{i:02}.txt','verified_output':output}
    results.append(row)
    print('INDEX',i,'EXIT',proc.returncode,'SECONDS',row['seconds'],flush=True);print(output[-1600:],flush=True)
(ROOT/'review/evidence/geometry_g6e_replay.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
