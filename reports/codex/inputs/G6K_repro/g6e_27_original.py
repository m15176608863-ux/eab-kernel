import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import sys; sys.path.insert(0,'src')
from eab.kernel2d.covers import convex_entrance_block
from eab.kernel2d.geom import is_convex
A=[(0.0,0.0),(0.1,0.0),(0.1,0.1),(0.0,0.1)]
for h in (1e-14,2e-14,3e-14,1e-13):
    B=[(0.0,0.0),(1.0-h,0.0),(1.0,0.0),(0.5,0.2)]
    try: convex_entrance_block(A,B); r='ok'
    except ValueError as e: r=str(e)
    print(h,is_convex(B),r)        # 前三个报 folds back，1e-13 ok
C=1e5
for h,ap in ((3e-9,0.2),(1e-8,0.05)):
    B=[(C,C),(C+1.0-h,C),(C+1.0,C),(C+0.5,C+ap)]
    try: convex_entrance_block(A,B); print('ok')
    except ValueError as e: print(h,ap,e)
d=2**-52; B=[(0.0,0.0),(1.0,0.0),(1.0,1.0),(1.0+d,1.0-d),(0.0,1.0)]
try: convex_entrance_block(A,B)
except ValueError as e: print(e)   # total turning angle -0.000000 ... winds more than once