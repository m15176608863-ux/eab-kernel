"""Independent exact area and nearest-subnormal rounding witness."""
from pathlib import Path
from fractions import Fraction as F
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron
u=F(1,2**1074)
p=Polyhedron([(0,0,0),(1,0,0),(1,F(29,10)*u,0)],[(0,1,2)])
# Triangle base1, perpendicular height29u/10 => exact area29u/20.
# Area lies below the midpoint(3u/2) between subnormals u and 2u.
area=F(29,20)*u
assert u<area<F(3,2)*u
expected=float(u);actual=p.face_area(0)
print(json.dumps(dict(exact_area_in_smallest_subnormal_units=str(area/u),expected_area=expected,reported_area=actual,ratio=actual/expected),indent=2))
assert actual==2*expected and actual!=expected
p.verts[2]=(1,u,0)
print('unrepresentable exact area=u/2, face_area=',p.face_area(0),'(no exception)')
assert p.face_area(0)==0
print('CONFIRMED face_area rounds Newell norm before halving, doubles a representable area and silently underflows an unrepresentable one')

# Same early-rounding pattern left in two public facet/support constructions.
from eab.kernel3d.covers3 import facet_gap3,support_gaps3
T=Polyhedron([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
x=(F(1)+F(51,20)*u,0,0)
q=F(51,20)**2/3
assert 1<q<F(3,2)**2  # exact squared gap in units u**2 lies below midpoint
g=facet_gap3(T,T,('VF',('vertex',0),('face',3)),x)
all_gaps=support_gaps3(T,T,x)
print('facet_gap3 exact midpoint oracle:',expected,'actual:',g)
print('support_gaps3 same supporting facet:',all_gaps[3])
assert g==all_gaps[3]==2*expected
print('CONFIRMED facet_gap3/support_gaps3 round numerator before normal-length division; same doubled representable final gap')
