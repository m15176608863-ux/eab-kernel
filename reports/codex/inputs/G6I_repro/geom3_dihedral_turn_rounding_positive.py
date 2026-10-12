"""Independent signed-angle oracle from the exact 2D cross-section.
For the edge from O=(0,0,0) to Z=(0,0,1), third vertices
C=(-M,M+1,0), D=(M-1,-M,0) give normals (M+1,M,0),(M,M-1,0).
Their cross product has z-component -1 and dot product 2*M*M. The first
face traverses the shared edge from Z to O, so t=-e_z and the signed
triple product (n1 x n2).t is +1. The true convex exterior dihedral angle
is atan(1/(2*M*M)); no production
geometric primitive or normal is used by this oracle. Every coordinate below
is supplied as binary64 and exactly represents its stated integer.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from eab.kernel3d.geom3 import tetra
rows=[]
for M in (10**6,10**7,10**8,10**9,10**12,2**50):
    assert F(float(M))==M and F(float(M+1))==M+1 and F(float(M-1))==M-1
    P=tetra((0.,0.,0.),(0.,0.,1.),(-float(M),float(M+1),0.),(float(M-1),-float(M),0.))
    assert P.manifold_issues()==[] and P.volume()==float(F(1,6)) and P.is_convex()
    expected=math.atan(float(F(1,2*M*M)))
    actual=P.dihedral_turn((0,1))
    assert expected>0 and P._exact_dihedral_orientation((0,1))==1
    rows.append(dict(M=M,expected_angle=expected,actual_angle=actual,
                     signed_volume=P.volume(),convex=P.is_convex(),
                     face_normals=(P.face_normal(0),P.face_normal(1)),issues=P.manifold_issues()))
    if M>=10**8:
        assert actual==expected,(actual,expected)
print(json.dumps(dict(result="FIXED",rows=rows),indent=2))
print("FIXED: finite binary64 valid tetrahedra preserve a representable positive signed dihedral angle")
