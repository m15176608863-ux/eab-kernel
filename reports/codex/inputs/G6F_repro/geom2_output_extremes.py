from pathlib import Path
import sys,json,math
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import entrance as E,g0,covers as C
s=2.**-600
B=[(0.,0.),(s,0.),(s,s),(0.,s)];A=[(x+s*1.5,y+s*.5) for x,y in B]
truth=s*.5
out={}
out['distance']={'true':truth,'got':g0.brute_polygon_distance(A,B)[0]}
r=g0.g0_distance_completeness(A,B,[(0.,0.)])
out['distance_gate']={'passed':r.passed,'samples':r.samples,'worst':r.worst_abs_error,'failures':r.failures}
r=E.shortest_exit(B,B,(s*.5,0.))
out['gap']={'true':-truth,'got':r.gap,'label':r.label}
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/notes/geom2_output_extremes.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
