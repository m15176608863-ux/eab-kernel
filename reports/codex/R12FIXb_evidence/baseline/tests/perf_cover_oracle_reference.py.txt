"""Independent rational oracle for the general local-cover interface.

No production geometry primitive is imported. This checks the current supplied
face-ring/Newell interface, including rounded nonplanar faces; it does NOT claim
that a Newell plane is the exact triangulated nonplanar surface. Convex theorem
tests instead use the explicit vertex-hull view and the separate G0 oracle.

Compared with the implementation: face vectors use the cyclic-coordinate
Newell identity; arcs use Gram coefficients; line parameters use a Gram solve;
cone intersections use Gordan extreme rays, not a closest-simplex algorithm.
"""

from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
import math
from construction_oracle import norm_exact, vector_exact


def q(p):
    return tuple(F(x) for x in p)


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def scale(a, k):
    return tuple(x*k for x in a)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


@lru_cache(maxsize=256)
def model(vertices, faces):
    v = tuple(map(q, vertices))
    normals = []
    edge_faces = {}
    neighbors = [set() for _ in v]
    for fi, face in enumerate(faces):
        n = [F(0), F(0), F(0)]
        for i, j in zip(face, face[1:] + face[:1]):
            a, b = v[i], v[j]
            for k in range(3):
                u, w = (k+1) % 3, (k+2) % 3
                n[k] += (a[u]-b[u])*(a[w]+b[w])
            edge_faces.setdefault(tuple(sorted((i, j))), []).append((fi, i, j))
            neighbors[i].add(j)
            neighbors[j].add(i)
        normals.append(tuple(n))
    directions = tuple(tuple(sub(v[j], v[i]) for j in sorted(js)) for i, js in enumerate(neighbors))
    return v, faces, tuple(normals), edge_faces, directions


def _model(P):
    return model(tuple(P.verts), tuple(P.faces))


def outside(value, norm2, tol):
    return value > 0 and (tol <= 0 or value*value > F(tol)**2*norm2)


def vertex(m, vi, d, tol):
    values = [dot(d, e) for e in m[4][vi]]
    if not values:
        return -1
    for value, e in zip(values, m[4][vi]):
        if outside(value, dot(d, d)*dot(e, e), tol):
            return -1
    return int(all(value < 0 for value in values))


def arc(m, edge, d, tol):
    adj = m[3].get(tuple(sorted(edge)), ())
    if len(adj) != 2:
        return -1
    (f1, i, j), (f2, _, _) = adj
    v, _, normals, _, _ = m
    t, n1, n2 = sub(v[j], v[i]), normals[f1], normals[f2]
    tt = dot(t, t)
    turn = dot(t, cross(n1, n2))
    if turn <= 0 or outside(abs(dot(d, t)), dot(d, d)*tt, tol):
        return -1
    # Project both generators into the exact edge-normal plane and solve their
    # Gram system. Scaling avoids division and remains positive.
    a = sub(scale(n1, tt), scale(t, dot(n1, t)))
    b = sub(scale(n2, tt), scale(t, dot(n2, t)))
    aa, ab, bb = dot(a, a), dot(a, b), dot(b, b)
    da, db = dot(d, a), dot(d, b)
    alpha, beta = bb*da-ab*db, aa*db-ab*da
    # Domain-band distances to each bounding ray are independently squared.
    sa = dot(t, cross(n1, d))
    sb = dot(t, cross(d, n2))
    if outside(-sa, (tt*dot(n1, n1)-dot(t, n1)**2)*dot(d, d), tol):
        return -1
    if outside(-sb, (tt*dot(n2, n2)-dot(t, n2)**2)*dot(d, d), tol):
        return -1
    return int(alpha > 0 and beta > 0 and dot(d, t) == 0)


def face_extent(m, fi, p):
    v, faces, normals, _, _ = m
    f, normal = faces[fi], normals[fi]
    drop = max(range(3), key=lambda i: abs(normal[i]))
    u, w = [i for i in range(3) if i != drop]
    parity = False
    for i, j in zip(f, f[1:] + f[:1]):
        a, b = v[i], v[j]
        z = (b[u]-a[u])*(p[w]-a[w])-(b[w]-a[w])*(p[u]-a[u])
        if z == 0 and min(a[u], b[u]) <= p[u] <= max(a[u], b[u]) and min(a[w], b[w]) <= p[w] <= max(a[w], b[w]):
            return True
        if (a[w] > p[w]) != (b[w] > p[w]):
            x = a[u] + (p[w]-a[w])*(b[u]-a[u])/(b[w]-a[w])
            if x > p[u]:
                parity = not parity
    return parity


@lru_cache(maxsize=8192)
def strict_cone(constraints):
    """Gordan: positive feasible rays span a strict direction iff one exists."""
    if not constraints:
        return False
    normalized = tuple(scale(g, 1/max(map(abs, g))) for g in constraints)
    values = set(normalized)
    if any(scale(g, -1) in values for g in values):
        return False
    candidate = scale(tuple(sum(g[i] for g in normalized) for i in range(3)), -1)
    if all(dot(candidate, g) < 0 for g in normalized):
        return True
    acc = (F(0),)*3
    for a, b in combinations(normalized, 2):
        r = cross(a, b)
        if not any(r):
            continue
        for d in (r, scale(r, -1)):
            if all(dot(d, g) <= 0 for g in normalized):
                acc = add(acc, scale(d, 1/max(map(abs, d))))
                if all(dot(acc, g) < 0 for g in normalized):
                    return True
    return False


def cover_labels(A, B, tol=1e-9):
    """Complete (label, exact strictness) set for infinite window, extent_tol=0."""
    return _cover_labels_cached(tuple(A.verts), tuple(A.faces), tuple(B.verts), tuple(B.faces), tol)


@lru_cache(maxsize=2048)
def _cover_labels_cached(av_raw, af_raw, bv_raw, bf_raw, tol):
    a, b = model(av_raw, af_raw), model(bv_raw, bf_raw)
    av, af, an, ae, ad = a
    bv, bf, bn, be, bd = b
    out = set()
    for ia, p in enumerate(av):
        for fb, face in enumerate(bf):
            n = bn[fb]
            state = vertex(a, ia, scale(n, -1), tol)
            if state >= 0:
                projection = sub(p, scale(n, dot(n, sub(p, bv[face[0]]))/dot(n, n)))
                if face_extent(b, fb, projection):
                    out.add((("VF", ("vertex", ia), ("face", fb)), state == 1))
    for fa, face in enumerate(af):
        n = an[fa]
        for ib, p in enumerate(bv):
            state = vertex(b, ib, scale(n, -1), tol)
            if state >= 0:
                projection = sub(p, scale(n, dot(n, sub(p, av[face[0]]))/dot(n, n)))
                if face_extent(a, fa, projection):
                    out.add((("FV", ("face", fa), ("vertex", ib)), state == 1))
    for ea in ae:
        da = sub(av[ea[1]], av[ea[0]])
        for eb in be:
            db = sub(bv[eb[1]], bv[eb[0]])
            aa, ab, bb = dot(da, da), dot(da, db), dot(db, db)
            den = aa*bb-ab*ab
            if not den:
                continue
            w = sub(bv[eb[0]], av[ea[0]])
            aw, bw = dot(da, w), dot(db, w)
            s, t = (bb*aw-ab*bw)/den, (ab*aw-aa*bw)/den
            if not (0 <= s <= 1 and 0 <= t <= 1):
                continue
            n = cross(db, da)
            for d in (n, scale(n, -1)):
                sb, sa = arc(b, eb, d, tol), arc(a, ea, scale(d, -1), tol)
                if sb >= 0 and sa >= 0:
                    out.add((("EE", ("edge", *ea), ("edge", *eb)), sb == sa == 1))
                    break
    for X, Y, kind, swap in ((a, b, "VE3", False), (b, a, "EV3", True)):
        xv, _, _, _, _ = X
        yv, _, _, ye, _ = Y
        for i, p in enumerate(xv):
            for edge in ye:
                d = sub(yv[edge[1]], yv[edge[0]])
                w = sub(p, yv[edge[0]])
                s = dot(w, d)/dot(d, d)
                if not 0 <= s <= 1:
                    continue
                n = sub(w, scale(d, s))
                if not any(n):
                    continue
                sx, sy = vertex(X, i, scale(n, -1), tol), arc(Y, edge, n, tol)
                if sx >= 0 and sy >= 0:
                    features = (("edge", *edge), ("vertex", i)) if swap else (("vertex", i), ("edge", *edge))
                    out.add(((kind, *features), sx == sy == 1))
    for ia, pa in enumerate(av):
        for ib, pb in enumerate(bv):
            d = sub(pa, pb)
            if any(d) and (vertex(b, ib, d, tol) < 0 or vertex(a, ia, scale(d, -1), tol) < 0):
                continue
            if strict_cone((*bd[ib], *(scale(g, -1) for g in ad[ia]))):
                out.add((("VV3", ("vertex", ia), ("vertex", ib)), True))
    return frozenset(out)


def witness_points(A, B, label, *, exact=False):
    """Independent exact witnesses for an in-extent local cover.

    Gram solves, not production projection/line helpers, determine both points.
    R9 retains the pre-optimisation geometric reference, but shares the test-only
    certified final construction boundary. Distance uses exact=True witnesses.
    """
    kind, fa, fb = label
    am, bm = _model(A), _model(B)
    av, bv = am[0], bm[0]
    if kind == "VF":
        p = av[fa[1]]
        origin, normal = bv[bm[1][fb[1]][0]], bm[2][fb[1]]
        a, b = p, sub(p, scale(normal, dot(normal, sub(p, origin))/dot(normal, normal)))
    elif kind == "FV":
        b, a = witness_points(B, A, ("VF", fb, fa), exact=exact)
        return a, b
    elif kind == "EE":
        a0, b0 = av[fa[1]], bv[fb[1]]
        da, db = sub(av[fa[2]], a0), sub(bv[fb[2]], b0)
        aa, ab, bb = dot(da, da), dot(da, db), dot(db, db)
        w = sub(b0, a0)
        wa, wb = dot(w, da), dot(w, db)
        denominator = aa*bb-ab*ab
        s, t = (wa*bb-wb*ab)/denominator, (wa*ab-wb*aa)/denominator
        a, b = add(a0, scale(da, s)), add(b0, scale(db, t))
    elif kind == "VE3":
        a, p = av[fa[1]], bv[fb[1]]
        d = sub(bv[fb[2]], p)
        t = dot(sub(a, p), d)/dot(d, d)
        b = add(p, scale(d, t))
    elif kind == "EV3":
        b, a = witness_points(B, A, ("VE3", fb, fa), exact=exact)
        return a, b
    elif kind == "VV3":
        a, b = av[fa[1]], bv[fb[1]]
    else:
        raise ValueError(label)
    if exact:
        return a, b
    return vector_exact(a), vector_exact(b)


def witness_distance(A, B, label):
    a, b = witness_points(A, B, label, exact=True)
    d = tuple(x-y for x, y in zip(a, b))
    return norm_exact(d)


def margin_selection(A, B, delta, *, touching=False, tol=1e-9):
    """Independent margin selection for the separated/touching test families.

    The pre-existing margin convention is independently evaluated here:
    ctol=max(1e-9*L, 1e-12*AABB_diagonal, 64*eps*max(C,L))
    +64*eps*max(C,L); contact witnesses are clamped to zero; include iff
    distance<=delta. No margin.py or cover implementation is called.
    """
    lengths, diagonals = [], []
    for P in (A, B):
        lengths.append(max(norm_exact(F(v[k])-F(P.verts[0][k]) for k in range(3)) for v in P.verts))
        lo = tuple(min(v[k] for v in P.verts) for k in range(3))
        hi = tuple(max(v[k] for v in P.verts) for k in range(3))
        diagonals.append(norm_exact(F(hi[k])-F(lo[k]) for k in range(3)))
    length = min(lengths)
    coordinate = max(abs(x) for P in (A, B) for v in P.verts for x in v)
    rounding = 64*2.220446049250313e-16*max(coordinate, length)
    ctol = max(1e-9*length, 1e-12*max(diagonals), rounding)+rounding
    distances = {label: witness_distance(A, B, label) for label, _ in cover_labels(A, B, tol)}
    contact = touching or min(distances.values(), default=float("inf")) <= ctol
    result = {}
    for label, distance in distances.items():
        if contact and distance <= ctol:
            distance = 0.
        if distance <= delta:
            result[label] = distance
    return result
