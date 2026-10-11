"""WO-E3E4 six assigned covers/hull findings; --baseline reloads e1fbbd4 source read-only."""
from pathlib import Path
import json, math, subprocess, sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
import eab.kernel2d.covers as cv
import eab.kernel2d.geom as gm
baseline='--baseline' in sys.argv
if baseline:
    for mod, path in [(gm,'src/eab/kernel2d/geom.py'),(cv,'src/eab/kernel2d/covers.py')]:
        exec(compile(subprocess.check_output(['git','show','e1fbbd4:'+path],cwd=ROOT).decode('utf-8'),path,'exec'),mod.__dict__)
from eab.kernel2d.g0 import g0_convex
A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)]
results={}
B=[(0.,0.),(1.,0.),(1.,1.),(0.,1.),(0.,.5001),(5e-7,.5)]
try:
    cv.convex_entrance_block(A,B,tol=1e-6); rejection=None
except ValueError as e:
    rejection=str(e)
results['src/eab/kernel2d/covers.py:117']={'rejection':rejection,'memberships':[cv.membership_convex(A,B,(-.1+d,.2),tol=1e-6) for d in (1e-5,1e-4)]}
results['src/eab/kernel2d/covers.py:360']={'vertex_counts':[len(cv.convex_entrance_block(A,[(0.,0.),(1-h,0.),(1.,0.),(.5,.2)]).vertices) for h in (1e-14,2e-14,3e-14,1e-13)]}
rows=[]
for C in (0.,1e3,1e4):
 for d in (1.05e-9,1.25e-9):
    P=[(C,C*.3),(C+1,C*.3),(C+1,C*.3+1),(C,C*.3+1)]
    Q=[(C+math.cos(d)*u-math.sin(d)*v,C*.3+math.sin(d)*u+math.cos(d)*v) for u,v in [(0.,0.),(1000.,0.),(1000.,1.),(0.,1.)]]
    rows.append({'C':C,'d':d,'AB_passed':g0_convex(P,Q,samples=100).passed,'BA_passed':g0_convex(Q,P,samples=100).passed})
results['src/eab/kernel2d/covers.py:453']={'grid':rows}
h=1e-14;P=[(0.,0.),(1-h,0.),(1.,h),(1.,1.),(0.,1.)]
Q=[(0.,0.),(-.25,-.25*math.sqrt(3)),(.25,-.25*math.sqrt(3))]
results['src/eab/kernel2d/covers.py:501']={'membership':cv.membership_convex(Q,P,(1.1,.5)),'g0_passed':g0_convex(Q,P,samples=2000).passed}
pts=[(0.,0.),(1e-15,-1e-3),(1e-15,1.),(1e-3,-1e-3),(2.,-1e-3),(2.,1.)]
H=gm.convex_hull(pts)
results['src/eab/kernel2d/geom.py:434']={'hull':H,'true_extreme_missing':(1e-15,-1e-3) not in H}
g=1e-6;C=1e5;theta=math.radians(-5)
P=[(C+u+g*math.cos(theta),C+v+g*math.sin(theta)) for u,v in [(0,0),(1,0),(1,1),(0,1)]]
Q=[(C+u,C+v) for u,v in [(0,0),(-1,1),(-1,-1)]]
record={'strict':cv.vv_cover(P,0,Q,0).strict,'labels':[c.label() for c in cv.enumerate_covers(P,Q,window=1e-3)]}
if baseline:
    src=subprocess.check_output(['git','show','e1fbbd4:src/eab/kernel2d/covers.py'],cwd=ROOT).decode('utf-8')
    needle='du = round_floor(max(abs(a[0]), abs(a[1]), abs(b[0]), abs(b[1]))) / dist'
    assert src.count(needle)==1
    exec(compile(src.replace(needle,needle+' * 100'),'<baseline_internal_du_x100>','exec'),cv.__dict__)
    record['internal_du_x100_strict']=cv.vv_cover(P,0,Q,0).strict
    record['internal_du_x100_labels']=[c.label() for c in cv.enumerate_covers(P,Q,window=1e-3)]
else:
    record['noise_du_path_removed']=not hasattr(cv,'_angle_tols')
results['src/eab/kernel2d/covers.py:238']=record
print(json.dumps({'baseline':baseline,'source':'e1fbbd4' if baseline else 'working-tree','findings':results},ensure_ascii=False,indent=2))
