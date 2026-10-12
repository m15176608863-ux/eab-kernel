import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import sys; sys.path.insert(0, 'src')
from eab.kernel2d.covers import convex_entrance_block, membership_convex
from eab.kernel2d.geom import polygons_overlap, translate
from eab.kernel2d.g0 import g0_convex
A = [(0.0, 0.0), (0.1, 0.0), (0.1, 0.1), (0.0, 0.1)]
def B(dent, h):
    return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.5 + h), (dent, 0.5)]
tol = 1e-6; P = B(0.5e-6, 1e-4)
try:
 convex_entrance_block(A,P,(0.0,0.0),tol)
 raise AssertionError('micro-reflex convex input accepted')
except ValueError as e:
 print('convex API rejected',e)
for d in (1e-5,1e-4):
 x=(-0.1+d,0.2)
 m=membership_convex(A,P,x,tol)
 print('depth',d,'exact general membership',m)
 assert m==1
