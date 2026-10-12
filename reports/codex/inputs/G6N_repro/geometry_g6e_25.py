# Original raw finding index 25; current HEAD replay, no repair.
import sys,math,random; sys.path.insert(0,'src')
from fractions import Fraction as F
from eab.kernel2d.covers import convex_entrance_block, membership_convex
from eab.kernel2d.geom import polygons_overlap, translate
from eab.kernel2d.g0 import g0_convex
# 例一：单位方块 + 1e-14 倒角，对正三角形
h=1e-14; B=[(0.0,0.0),(1.0-h,0.0),(1.0,h),(1.0,1.0),(0.0,1.0)]
Q=[(0.0,0.0),(0.25,0.25*math.sqrt(3)),(-0.25,0.25*math.sqrt(3))]; A=[(-p[0],-p[1]) for p in Q]
eb=convex_entrance_block(A,B); print(eb.facets)
x=(1.1,0.5); print('cover',membership_convex(A,B,x,0.0,eb),'brute',polygons_overlap(translate(A,x),B))   # cover -1, brute 1
r=g0_convex(A,B,samples=2000); print('g0 mismatches',len(r.mismatches))   # 132
# 例二：C=1e3，T 形短边 h=1e-8，A 边倾 1e-4
C=1e3; h=1e-8; B=[(C,C),(C+1-h,C),(C+1,C),(C+1,C+1),(C,C+1)]
Q=[(0.0,0.0),(0.5*math.cos(1e-4),0.5*math.sin(1e-4)),(0.25,0.4)]; A=[(-p[0],-p[1]) for p in Q]
eb=convex_entrance_block(A,B); print(eb.facets)   # 含 ('FF',0,1)
V1,V2=eb.vertices[1],eb.vertices[2]; x=((V1[0]+V2[0])/2,(V1[1]+V2[1])/2-1e-5)
print('cover',membership_convex(A,B,x,0.0,eb),'brute',polygons_overlap(translate(A,x),B,0.0))   # cover 1, brute -1
