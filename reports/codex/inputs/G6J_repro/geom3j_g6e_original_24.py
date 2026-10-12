import sys, math
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import box, Polyhedron, brute_feature_distance
from eab.kernel3d.covers3 import cone_intersection_margin
from eab.margin import body_distance
B = box()
for psi in (1e-11, 1e-10, 1e-9, 3e-9):
    g = 0.1; cs, sn = math.cos(psi), math.sin(psi)
    rc = (cs*-1.0 - sn*1.0, sn*-1.0 + cs*1.0, -1.0)
    corner = (1.0 + g, 1.0 + psi*g/2, 1.0 + g)
    c = tuple(corner[i] - rc[i] for i in range(3))
    A = Polyhedron([(c[0] + cs*x - sn*y, c[1] + sn*x + cs*y, c[2] + z) for x, y, z in box().verts], list(box().faces))
    ia = min(range(8), key=lambda i: math.dist(A.verts[i], corner))
    try: res = body_distance(A, B)
    except Exception as e: res = repr(e)[:110]
    print(psi, cone_intersection_margin(A, ia, B, 6), brute_feature_distance(A, B), res)