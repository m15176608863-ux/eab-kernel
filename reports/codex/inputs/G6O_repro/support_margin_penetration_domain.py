"""WO-G6O: penetration sentinel's ordinary margin_gap lacks final boundary.

Independent oracle: overlapping axis-aligned unit boxes have distance=0.
The documented accepted-contact margin gap is exactly -delta. For an exact
positive delta below the RN-zero midpoint, ordinary scalar construction
must reject or provide the explicitly required exact display certificate.
Neither occurs. No tested geometry operation computes the oracle.
"""
from pathlib import Path
from fractions import Fraction as F
import sys, math

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'));sys.dont_write_bytecode=True
from eab.kernel3d.geom3 import box
from eab.margin import margin_contacts, PENETRATING

# box defaults represent an ordinary [-.5,.5]^3 volume; identical copies
# overlap throughout their open interior, independently of any tolerance.
A=box();B=box()
delta=F(2)**-2000
assert delta > 0 and delta < F(2)**-1075
contact,=margin_contacts(A,B,delta=delta)
assert contact.label==(PENETRATING,)
assert contact.distance==0 and contact.margin_gap==0.0
assert contact.closed is True
assert contact._exact_closed is None and contact.exact_distance_squared is None
expected=-delta
assert expected!=0
print('identical ordinary unit boxes, delta=Fraction(2)**-2000')
print(f'documented exact margin_gap=-delta={expected}')
print(f'actual margin_gap={contact.margin_gap!r}, closed={contact.closed}, label={contact.label!r}')
print(f'exact_closed={contact._exact_closed!r}, exact_distance_squared={contact.exact_distance_squared!r}, exact_normal_direction={contact.exact_normal_direction!r}')
print('CONFIRMED: nonzero ordinary margin_gap becomes zero without domain exception or exact display certificate')
