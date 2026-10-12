"""Valid exact input rejected solely by equivalent zero-offset scalar types."""
from fractions import Fraction as F
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.interlock import escape_height_covers

FACES=((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))
SIGNS=((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
size=F(1,10**9);origin=F(10**8)
def make(center,half):
    return Polyhedron([tuple(origin+size*(center[k]+s[k]*half[k]) for k in range(3)) for s in SIGNS],list(FACES))
A=make((F(0),F(0),F(0)),(F(1,2),)*3)
B=make((F(0),F(0),F(3,4)),(F(1,2),)*3)
# Product-interval oracle: upper face of B is 5/4, lower face of A is -1/2;
# lifting A upward first separates at (5/4)-(-1/2) = 7/4 model units.
expected=F(7,4)*size
integer_zero=escape_height_covers(A,B,(0,0,0))
print('independent exact product-interval earliest root',expected)
print('offset integer zero exact_height',integer_zero.exact_height)
assert integer_zero.exact_height==expected
assert all(tuple(F(x) for x in p)==p for p in A.verts+B.verts)
try:
    float_zero=escape_height_covers(A,B,(0.,0.,0.))
except ValueError as error:
    print('equivalent offset float zero rejected:',type(error).__name__,str(error))
    assert 'zero-length edge' in str(error)
else:
    raise AssertionError('expected reproduction failed: float zero unexpectedly succeeded')
print('CONFIRMED nominal-report float translation fails before exact authoritative solver')
