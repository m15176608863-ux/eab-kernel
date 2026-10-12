"""Post-freeze same-family scan: public contact display subtraction."""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"src"))
from eab.kernel3d.geom3 import box
from eab.margin import margin_contacts
M=F(10**20)
A=box((M+10001,F(0),F(0)),(F(1),F(1),F(1)))
B=box((F(-1),F(0),F(0)),(F(1),F(2),F(2)))
rows=margin_contacts(A,B,delta=M,band=20000,tol=0)
assert rows
result=rows[0]
print(json.dumps({"expected_distance_squared":str((M+10000)**2),
 "exact_distance_squared":str(result.exact_distance_squared),
 "expected_margin_gap":10000.,"actual_margin_gap":result.margin_gap,
 "closed":result.closed,"label":result.label},indent=2))
assert result.exact_distance_squared == (M+10000)**2
assert result.margin_gap == 10000., "contact margin was subtracted after distance rounding"
