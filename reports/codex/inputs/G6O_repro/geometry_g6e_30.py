# Original raw finding index 30; current HEAD replay, no repair.
import sys, math; sys.path.insert(0,'src'); sys.path.insert(0,'tests')
from test_near_parallel_edges import exact_seg_seg, _quat, _move
from eab.kernel3d.geom3 import tetra, _seg_seg_distance
from eab.margin import body_distance, rounding_floor
theta, half, x0, gap = 1.5e-6, 0.3, 0.95, 4.5793919600798964e-09
B = tetra((-1.0,0.0,0.0),(1.0,0.0,0.0),(0.0,-0.8,-1.5),(0.0,0.9,-1.4))
c, s = math.cos(theta), math.sin(theta)
A = tetra((x0-half*c,-half*s,gap),(x0+half*c,half*s,gap),(x0-0.1,-0.7,1.3+gap),(x0+0.2,0.8,1.2+gap))
R=_quat(5); A,B=_move(A,R),_move(B,R)
print('exact',exact_seg_seg(A.verts[0],A.verts[1],B.verts[0],B.verts[1]),'oracle',_seg_seg_distance(A.verts[0],A.verts[1],B.verts[0],B.verts[1]),'4*rnd',4*rounding_floor(A,B))
print(body_distance(A,B))
