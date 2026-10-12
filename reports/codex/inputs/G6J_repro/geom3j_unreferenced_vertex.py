"""Unconfirmed validity-boundary probe; not counted as a confirmed defect.
An isolated unreferenced vertex may violate the valid 2-manifold input premise.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import box,polyhedra_overlap,brute_feature_distance
from eab.kernel3d.g03_surface_oracle import separated_distance
from eab.margin import body_distance
A=box(center=(0,0,0),half=(1,1,1)); B=box(center=(4,0,0),half=(1,1,1))
A.verts.append((2.75,0,0))
print('unreferenced_index=8; face_set unchanged; Cartesian box surface distance=2')
print('manifold_issues diagnostic:',A.manifold_issues(0))
print('surface relation:',polyhedra_overlap(A,B))
print('brute/oracle distances:',brute_feature_distance(A,B),separated_distance(A.verts,A.faces,B.verts,B.faces))
try: print('body_distance:',body_distance(A,B))
except Exception as error: print(type(error).__name__+': '+str(error))
print('NOT_COUNTED: input valid-manifold interpretation requires clarification')
