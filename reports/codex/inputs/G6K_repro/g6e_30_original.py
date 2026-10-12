import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import sys, math; sys.path.insert(0,'src')
from eab.kernel2d.covers import ambiguous_facets, convex_entrance_block, local_facets
from eab.kernel2d.g0 import char_length, g0_convex
SQ=[(0.0,0.0),(1.0,0.0),(1.0,1.0),(0.0,1.0)]; RECT=[(0.0,0.0),(1000.0,0.0),(1000.0,1.0),(0.0,1.0)]
def rot(P,th,t):
    c,s=math.cos(th),math.sin(th); return [((c*p[0]-s*p[1])+t[0],(s*p[0]+c*p[1])+t[1]) for p in P]
for C in (0.0,1e3,1e4):
  for d in (1.05e-9,1.25e-9):
    T=(C,0.3*C); A=rot(SQ,0.0,T); B=rot(RECT,d,T); tol=1e-12*char_length(A,B)
    eb=convex_entrance_block(A,B,(0.0,0.0),tol)
    print(C,d,'FF',sorted(l for l in eb.facets if l[0]=='FF'),'amb',sorted(ambiguous_facets(A,B,tol)),'strict',len(local_facets(A,B,tol)),'g0',g0_convex(A,B,samples=100).passed,g0_convex(B,A,samples=100).passed)