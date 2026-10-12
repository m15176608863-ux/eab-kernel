import sys,math
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,'src')
from eab.readers.bdda_geom import strip_duplicate_vertices
from eab.kernel2d.exact import polygons_overlap_exact
T=1e8;u=math.ulp(T)
A=[(T,0),(T+u,u),(T+1,0),(T+1,-1),(T,-1)]
B=[(T-u,F(u)*3/4),(T+4*u,F(u)*3/4),(T+4*u,1),(T-u,1)]
vid,p,aliases=strip_duplicate_vertices(list(range(1,6)),A,dup_tol=0)
print('ulp',u,'A',A,'B',B,'cleaned',p,'aliases',aliases)
print('original=',polygons_overlap_exact(A,B),'cleaned=',polygons_overlap_exact(p,B))
