from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()/'src'))
from fractions import Fraction as F
from eab.kernel3d.geom3 import Polyhedron
from eab.margin import body_distance,margin_contacts
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
av=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,0),(1,-1,1),(1,1,0),(-1,1,1)]
bv=[(1,-1,2),(1,1,1),(-1,1,2),(-1,-1,1),(1,-1,4),(1,1,4),(-1,1,4),(-1,-1,4)]
g=F(1,10**9);T=F(10**8)
a=Polyhedron([tuple(F(x)+T for x in p) for p in av],faces)
b=Polyhedron([tuple(F(x)+T+(g if k==2 else 0) for k,x in enumerate(p)) for p in bv],faces)
print('bodydistance',body_distance(a,b,tol=0))
for c in margin_contacts(a,b,delta=2*g,tol=0): print(c)
