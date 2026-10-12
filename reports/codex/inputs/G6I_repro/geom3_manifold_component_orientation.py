"""Diagnostic promise: an empty issues list is claimed to certify outwardness.
Independent cube-volume oracle uses side-length products only; negative winding
of the disconnected small component is constructed explicitly by reversing every
ring. No production volume/normal/topology primitive enters the truth.
"""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def cube(center,half):
 x,y,z=center;h=half
 return [(x-h,y-h,z-h),(x+h,y-h,z-h),(x+h,y+h,z-h),(x-h,y+h,z-h),
         (x-h,y-h,z+h),(x+h,y-h,z+h),(x+h,y+h,z+h),(x-h,y+h,z+h)]
a=cube((0,0,0),2);b=cube((10,0,0),1)
# Interval products [-2,2]^3 and [9,11]x[-1,1]^2 are strictly disjoint.
# They are two separate boundary components, not a nested cavity shell.
assert max(p[0] for p in a)<min(p[0] for p in b)
small_faces=[tuple(reversed(f)) for f in faces]
P=Polyhedron(a+b,faces+[tuple(8+i for i in f) for f in small_faces])
issues=P.manifold_issues(tol=0)
actual_volume=P.volume()
expected_volumes=(4**3,-2**3)
assert actual_volume==sum(expected_volumes)==56
assert issues==[],issues
small=Polyhedron(b,small_faces)
assert small.volume()==expected_volumes[1]
assert any('orientation is inward' in item for item in small.manifold_issues(tol=0))
print(json.dumps(dict(result='CONFIRMED',expected_component_signed_volumes=expected_volumes,
 total_volume=actual_volume,whole_issues=issues,small_component_issues=small.manifold_issues(tol=0),
 failure='larger outward component masks disconnected inward component under advertised empty-list certificate',
 scope='diagnostic/documentation only; invalid orientation excluded from core surface API domain'),indent=2))
