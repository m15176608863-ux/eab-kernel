"""Exact local topology of E at a body-contact configuration.

Body interiors being disjoint does not imply boundary E: a tight-fit seam can
lie inside E. All triangle VF/FV and EE configuration planes contain the true
boundary of E. Their central arrangement therefore partitions a neighbourhood
into open chambers of constant intersection state. Exact representatives of
every chamber, with certified steps before every noncentral plane, decide
whether an exterior chamber exists. No geometric tolerance or epsilon guess is
used. This production implementation does not call an independent G0 oracle.

Gate: tests/test_r8fix_initial_state3.py (Cartesian interval-union oracle).
"""
from fractions import Fraction as F
from itertools import combinations

from . import exact_geom as G
from .geom3 import Polyhedron, polyhedra_overlap


def _canonical(direction):
    pivot = next(v for v in direction if v)
    return tuple(v / pivot for v in direction)


def _configuration_planes(A, B):
    """Central normals and the closest noncentral parallel-plane offsets.

    Artificial triangulation edges only subdivide chambers; retaining all of
    them avoids assumptions about convexity or a source polygon's planarity.
    A plane is h+n.delta=0, where delta translates A from its supplied pose.
    """
    central, noncentral = set(), {}

    def put(n, a, b):
        if not any(n):
            return
        n = _canonical(n)
        h = abs(G.dot(n, G.sub(a, b)))
        if not h:
            central.add(n)
        elif n not in noncentral or h < noncentral[n]:
            noncentral[n] = h

    def surface(P):
        vertices = tuple(G.vector(_mapped_value) for _mapped_value in P.verts)
        faces, edges = set(), set()
        for _, tri in G.triangles(P):
            n = G.cross(G.sub(tri[1],tri[0]),G.sub(tri[2],tri[0]))
            if not any(n):
                continue
            n = _canonical(n)
            faces.add((n, tri[0]))
            for a,b in zip(tri,tri[1:]+tri[:1]):
                if a != b:
                    edges.add(tuple(sorted((a,b))))
        return vertices, faces, edges

    av, af, ae = surface(A)
    bv, bf, be = surface(B)
    for n,b in bf:
        for a in av:
            put(n,a,b)
    for n,a in af:
        for b in bv:
            put(n,a,b)
    for a,a1 in ae:
        u = G.sub(a1,a)
        for b,b1 in be:
            put(G.cross(u,G.sub(b1,b)),a,b)
    return tuple(sorted(central)), tuple(sorted(noncentral.items()))


def _angular_compare(u,v):
    def half(p):
        return 0 if p[1] > 0 or (p[1] == 0 and p[0] > 0) else 1
    if half(u) != half(v):
        return half(u)-half(v)
    determinant = u[0]*v[1]-u[1]*v[0]
    return -1 if determinant > 0 else (1 if determinant < 0 else 0)


def _chamber_directions(normals):
    """One rational interior direction per central-arrangement sign chamber.

    With >=2 distinct planes each spherical chamber has an intersection ray
    in its closure (also true for rank-2 spherical lunes). Around each such ray
    every transverse angular sector is sampled. The perturbation is strictly
    smaller than every crossing of a plane not incident to that ray. All planes
    incident to the ray take their sign from the transverse sector itself.
    """
    if not normals:
        raise ArithmeticError('body contact has no incident configuration plane')
    if len(normals) == 1:
        yield normals[0]
        yield G.mul(normals[0],-1)
        return
    rays = set()
    for n,m in combinations(normals,2):
        ray = G.cross(n,m)
        if any(ray):
            ray = _canonical(ray)
            rays.update((ray,G.mul(ray,-1)))
    seen = set()
    for ray in sorted(rays):
        axis = min(range(3), key=lambda i: abs(ray[i]))
        coordinate = tuple(F(i == axis) for i in range(3))
        u = G.cross(ray,coordinate)
        v = G.cross(ray,u)
        uu,vv = G.dot(u,u),G.dot(v,v)
        values = [G.dot(n,ray) for n in normals]
        lines = set()
        for n,h in zip(normals,values):
            if h:
                continue
            line = G.cross(ray,n)
            a,b = G.dot(line,u)/uu,G.dot(line,v)/vv
            size = abs(a)+abs(b)
            tangent = (a/size,b/size)
            lines.update((tangent,(-tangent[0],-tangent[1])))
        ordered = []
        for line in lines:
            at = len(ordered)
            while at and _angular_compare(ordered[at-1], line) > 0:
                at -= 1
            ordered.insert(at, line)
        for a,b in zip(ordered,ordered[1:]+ordered[:1]):
            tangent = (a[0]+b[0],a[1]+b[1])
            if tangent == (0,0):
                tangent = (-a[1],a[0])
            q = G.add(G.mul(u,tangent[0]),G.mul(v,tangent[1]))
            step = F(1)
            for n,h in zip(normals,values):
                slope = G.dot(n,q)
                if h and slope:
                    step = min(step,abs(h/slope)/2)
            direction = G.add(ray,G.mul(q,step))
            products = tuple(G.dot(n,direction) for n in normals)
            if any(value == 0 for value in products):
                raise ArithmeticError('angular chamber representative lies on a plane')
            signs = tuple(1 if value > 0 else -1 for value in products)
            if signs not in seen:
                seen.add(signs)
                yield direction


def entrance_membership3(A, B):
    """1 in topological int(E), 0 on boundary E, -1 outside E.

    A and B are supplied in their current poses. Closed-surface body overlap
    keeps its separate physical contract; only its contact state needs the
    local configuration-space classification here.
    """
    state = polyhedra_overlap(A,B,0)
    if state != 0:
        return state
    central, limits = _configuration_planes(A,B)
    vertices = tuple(G.vector(_mapped_value) for _mapped_value in A.verts)
    for direction in _chamber_directions(central):
        step = F(1)
        for n,h in limits:
            slope = G.dot(n,direction)
            if slope:
                step = min(step,h/(2*abs(slope)))
        shift = G.mul(direction,step)
        probe = Polyhedron([G.add(p,shift) for p in vertices],list(A.faces))
        relation = polyhedra_overlap(probe,B,0)
        if relation == -1:
            return 0
        if relation == 0:
            raise ArithmeticError('off-plane chamber probe still has body contact')
    return 1
