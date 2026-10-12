"""Axis-product volume/centroid oracle; no production geometric primitive.

All faces are planar, outward oriented; every supplied coordinate is binary64.
The box oracle follows integration over a product of intervals, not triangulation.
"""
from pathlib import Path
import sys,json,math
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron
s=math.ldexp(1.,-600);h=math.ldexp(1.,600)
verts=[(-s,-s,-h),(s,-s,-h),(s,s,-h),(-s,s,-h),(-s,-s,h),(s,-s,h),(s,s,h),(-s,s,h)]
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
expected_volume=float(8*F(s)*F(s)*F(h))
expected_centroid=(0.,0.,0.)
p=Polyhedron(verts,faces)
got_volume=p.volume();got_centroid=p.centroid()
assert expected_volume!=0 and math.isfinite(expected_volume)
assert got_volume!=expected_volume and got_centroid!=expected_centroid
assert got_volume==float(F(expected_volume)*F(2,3))
print(json.dumps(dict(box=dict(half_width_x=s,half_width_y=s,half_height=h,
                              got_volume=got_volume,expected_volume=expected_volume,
                              ratio=got_volume/expected_volume,got_centroid=got_centroid,
                              expected_centroid=expected_centroid)),indent=2))
# A tetrahedron is unchanged when a face ring is cyclically shifted.
tv=[(0.,0.,0.),(0.,0.,h),(s,0.,0.),(0.,s,0.)]
tf=[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
tetra=Polyhedron(tv,tf)
first=tetra.volume()
tetra.faces=[(0,2,1),(0,1,3),(0,3,2),(2,3,1)]
second=tetra.volume()
truth=float(F(s)*F(s)*F(h)/6)
assert first==0 and second==truth and truth>0
print(json.dumps(dict(tetra=dict(expected_volume=truth,original_face_ring_volume=first,
                                cyclically_shifted_face_ring_volume=second)),indent=2))
print('CONFIRMED valid finite planar-face geometry: intermediate range loss changes volume and centroid')
