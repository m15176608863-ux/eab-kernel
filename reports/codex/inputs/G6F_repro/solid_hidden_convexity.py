import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from fractions import Fraction as F
from eab.kernel3d.geom3 import Polyhedron
# CCW x-z ring; extrude y. Determine outward faces by explicit volume order.
def prism(eps,t=F(0)):
    ring=[(F(0),F(0)),(F(2),F(0)),(F(2),F(1)),(F(1),F(1)-eps),(F(0),F(1))]
    n=len(ring)
    verts=[(x+t,y,z) for y in (F(-1),F(1)) for x,z in ring]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces +=[(i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n)]
    return Polyhedron(verts,faces)
for eps,t in [(F(1,2**50),F(0)),(F(1,2**24),F(10**8))]:
    P=prism(eps,t)
    # Midpoint of two surface peaks is outside: roof at x=t+1 is 1-eps.
    print('epsilon',eps,'translation',t)
    print('independent concavity determinant',-2*eps)
    print('roof at peak midpoint',1-eps,'midpoint height',F(1))
    print('is_convex(tol=0)',P.is_convex(tol=0))
    print('reflex_edges(tol=0)',P.reflex_edges(tol=0))
    print('min_dihedral_turn',min(P.dihedral_turn(e) for e in P.edges()))
    print('manifold_issues',P.manifold_issues())
    assert not P.manifold_issues()
    assert P.is_convex(tol=0) and P.reflex_edges(tol=0)==[]
    # Independent witness: two roof peaks belong to the surface but their
    # midpoint lies strictly above the piecewise-linear roof => not convex.
    assert 1-eps < 1
    print('CONFIRMED exact midpoint concavity witness; API returned convex/no reflex')
P=prism(F(1,2**50));P=Polyhedron([tuple(map(float,v)) for v in P.verts],P.faces)
print('binary64-only valid input:',not P.manifold_issues(),'is_convex(tol=0)',P.is_convex(tol=0),'reflex_edges(tol=0)',P.reflex_edges(tol=0))
assert not P.manifold_issues() and P.is_convex(tol=0) and not P.reflex_edges(tol=0)
