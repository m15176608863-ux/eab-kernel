"""Rerun four E5b interlock internal mutations; restore each live function."""
import json
import sys
import time
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools'),str(ROOT/'tests')]
from eab.kernel3d import interlock as I
import test_interlock_exact as T
import test_interlock_sensitivity as H

rows=[]
A,B=T._wall()
def run(name,attr,replacement,check):
    original=getattr(I,attr);setattr(I,attr,replacement)
    started=time.perf_counter()
    try:
        check()
    except (AssertionError,ValueError) as exc:
        rows.append(dict(mutation=name,internal_symbol=attr,killed=True,exception=type(exc).__name__,message=str(exc),seconds=time.perf_counter()-started))
    else:
        rows.append(dict(mutation=name,killed=False))
    finally:
        setattr(I,attr,original)

original=I.surface_events
run('omit near-vertical exact surface events','surface_events',lambda *a,**k:tuple(e for e in original(*a,**k) if abs(e.normal[2])>F(1,10**8)*max(map(abs,e.normal))),lambda:T._assert_exact_wall(A,B))
original_predicate=I._nonpenetrating_at
run('omit returned-root exact nonpenetration certificate','_nonpenetrating_at',lambda a,b,off,h:0 if h>0 and h in {e.time for e in I.surface_events(a,b,start=off)} else original_predicate(a,b,off,h),lambda:T._assert_exact_wall(A,B))
original_intervals=I._prior_intervals
run('omit first previous candidate interval proof','_prior_intervals',lambda *args:iter(list(original_intervals(*args))[1:]),lambda:T._assert_interval_proof(I.escape_height_covers(A,B,(0,0,0))))
def vertical(z,nz,cands,gtol,r):
    pos=[c for c in cands if c[0]>0];lab=next(c[1] for c in pos if c[0]==z)
    tied=tuple(c[1] for c in pos if abs(c[0]-z)<=1e-9*max(1.,abs(z)) and c[1]!=lab)
    return I.EscapeSolution(z,lab,len(cands),(lab,)+tied)
run('steep nominal vertical tie-window internal mutation','_escape_solution',vertical,lambda:H._steep_check(1.,0.))
assert all(r['killed'] for r in rows)
Path(__file__).with_name('mutations.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False,indent=2))
