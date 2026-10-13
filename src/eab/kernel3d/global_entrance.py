"""M3 exact convex-union entrance object, independent of surface predicates.

The representation is a finite union of full-dimensional convex parts.  For
each pair, closed SAT slabs describe E_ij and their strict versions describe
O_ij.  Therefore E is the closed union and O the union of the open interiors,
NOT the interior of E.  All returned constructions are Fraction certificates;
this module makes no binary64 constructions.  See m3_global_entrance_design.md
and tests/test_m3_global3d.py for the contract and its executable checks.

Input: consistently outward oriented, closed, embedded triangulated surfaces
(possibly with inward oriented cavity shells). Nonplanar rings have the same
deterministic projected-ear interpretation as the existing surface API, but
neither its triangulator nor any overlap/cover primitive is imported here.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from itertools import count
from math import gcd, lcm

def _number(value):
    try:
        return F(value)
    except (ValueError, OverflowError, TypeError):
        raise ValueError('global3d coordinate: nonfinite or unsupported scalar input') from None


def _point(p):
    if len(p) != 3:
        raise ValueError('global3d requires three coordinates')
    return tuple(_number(x) for x in p)


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _mean(points):
    return tuple(sum(p[k] for p in points)/len(points) for k in range(3))


def _normal(poly):
    origin = poly[0]
    crosses = [_cross(_sub(a, origin), _sub(b, origin))
               for a, b in zip(poly, poly[1:] + poly[:1])]
    return tuple(sum(n[k] for n in crosses) for k in range(3))


def _turn(vertices, u, v, i, j, k):
    a, b, c = vertices[i], vertices[j], vertices[k]
    return (b[u]-a[u])*(c[v]-a[v])-(b[v]-a[v])*(c[u]-a[u])


def _triangulate(vertices, faces):
    """Independently implemented deterministic supplied-ring interpretation."""
    triangles = []
    for face in faces:
        if len(face) < 3 or len(set(face)) != len(face):
            raise ValueError('global3d requires simple nondegenerate face rings')
        if any(not isinstance(i, int) or i < 0 or i >= len(vertices) for i in face):
            raise ValueError('global3d invalid face vertex index')
        polygon = tuple(vertices[i] for i in face)
        normal = _normal(polygon)
        if not any(normal):
            raise ValueError('global3d zero-area source face')
        drop = max(range(3), key=lambda k: abs(normal[k]))
        u, v = (drop+1) % 3, (drop+2) % 3
        signed = sum(vertices[i][u]*vertices[j][v]-vertices[j][u]*vertices[i][v]
                     for i, j in zip(face, face[1:] + face[:1]))
        sign = 1 if signed > 0 else -1
        ring = list(face)
        while len(ring) > 3:
            for k, middle in enumerate(ring):
                before, after = ring[k-1], ring[(k+1) % len(ring)]
                if sign*_turn(vertices, u, v, before, middle, after) <= 0:
                    continue
                if any(all(sign*_turn(vertices, u, v, i, j, q) >= 0 for i, j in
                           ((before, middle), (middle, after), (after, before)))
                       for q in ring if q not in (before, middle, after)):
                    continue
                triangles.append(tuple(vertices[i] for i in (before, middle, after)))
                del ring[k]
                break
            else:
                removable = next((k for k, j in enumerate(ring)
                                  if _turn(vertices, u, v, ring[k-1], j, ring[(k+1) % len(ring)]) == 0), None)
                if removable is None:
                    raise ValueError('global3d face projection is not a simple polygon')
                tri = tuple(vertices[i] for i in
                            (ring[removable-1], ring[removable], ring[(removable+1) % len(ring)]))
                if any(_cross(_sub(tri[1], tri[0]), _sub(tri[2], tri[0]))):
                    triangles.append(tri)
                del ring[removable]
        tri = tuple(vertices[i] for i in ring)
        if not any(_cross(_sub(tri[1], tri[0]), _sub(tri[2], tri[0]))):
            raise ValueError('global3d zero-area source triangle')
        triangles.append(tri)
    return tuple(triangles)


def _inside(p, triangles):
    """Exact parity for BSP leaf interior points; no production oracle call."""
    for k in count(1):
        direction = (1, k, k*k+k+1)
        hits = 0
        bad = False
        for a, b, c in triangles:
            first, second, delta = _sub(b, a), _sub(c, a), _sub(p, a)
            h = _cross(direction, second)
            determinant = _dot(first, h)
            if not determinant:
                # A parallel ray in a face plane is not generic.
                if not _dot(_cross(first, second), delta):
                    bad = True
                    break
                continue
            q = _cross(delta, first)
            u = _dot(delta, h)/determinant
            v = _dot(direction, q)/determinant
            t = _dot(second, q)/determinant
            if t <= 0 or u < 0 or v < 0 or u+v > 1:
                continue
            if u == 0 or v == 0 or u+v == 1:
                bad = True
                break
            hits += 1
        if not bad:
            return hits % 2 == 1


@dataclass(frozen=True)
class ConvexPart3D:
    """Exact closed convex cell and a strictly interior rational certificate."""
    vertices: tuple
    faces: tuple
    interior: tuple


def _part(faces):
    faces = tuple(tuple(face) for face in faces)
    vertices = tuple(sorted({p for face in faces for p in face}))
    centre = _mean(vertices)
    if len(vertices) < 4:
        raise ValueError('global3d degenerate convex cell')
    oriented = []
    for face in faces:
        n = _normal(face)
        height = _dot(n, _sub(centre, face[0]))
        if not height:
            raise ValueError('global3d cell has no strict interior certificate')
        if height > 0:
            face = tuple(reversed(face))
            n = tuple(-x for x in n)
        if any(_dot(n, _sub(p, face[0])) > 0 for p in vertices):
            raise ValueError('global3d nonconvex part')
        oriented.append(face)
    return ConvexPart3D(vertices, tuple(oriented), centre)


def _clip_polygon(polygon, normal, height, positive=False):
    signed = [_dot(normal, p)-height for p in polygon]
    if positive:
        signed = [-x for x in signed]
    out = []
    for i, a in enumerate(polygon):
        b = polygon[(i+1) % len(polygon)]
        da, db = signed[i], signed[(i+1) % len(polygon)]
        if da <= 0:
            out.append(a)
        if da*db < 0:
            t = da/(da-db)
            out.append(tuple(a[j]+t*(b[j]-a[j]) for j in range(3)))
    out = tuple(dict.fromkeys(out))
    return out if len(out) >= 3 and any(_normal(out)) else ()


def _cap_order(points, normal):
    centre = _mean(points)
    drop = max(range(3), key=lambda k: abs(normal[k]))
    x, y = (drop+1) % 3, (drop+2) % 3
    ranked = []
    for p in points:
        dx, dy = p[x]-centre[x], p[y]-centre[y]
        if dx > 0 and dy >= 0:
            key = (0, dy/dx)
        elif dy > 0 and dx <= 0:
            key = (1, -dx/dy)
        elif dx < 0 and dy <= 0:
            key = (2, dy/dx)
        else:
            key = (3, -dx/dy)
        ranked.append((key, p))
    return tuple(p for _, p in sorted(ranked))


def _split_cell(cell, normal, height):
    minus, plus = [], []
    cap = set()
    for face in cell.faces:
        left = _clip_polygon(face, normal, height)
        right = _clip_polygon(face, normal, height, True)
        if left:
            minus.append(left)
        if right:
            plus.append(right)
        for poly in (left, right):
            cap.update(p for p in poly if _dot(normal, p) == height)
    face = _cap_order(tuple(cap), normal)
    minus.append(face)
    plus.append(tuple(reversed(face)))
    return _part(minus), _part(plus)


def _box_part(vertices):
    low = tuple(min(p[k] for p in vertices) for k in range(3))
    high = tuple(max(p[k] for p in vertices) for k in range(3))
    if any(a == b for a, b in zip(low, high)):
        raise ValueError('global3d requires positive-volume solids')
    corners = tuple((x, y, z) for x in (low[0], high[0])
                    for y in (low[1], high[1]) for z in (low[2], high[2]))
    faces = []
    for axis in range(3):
        normal = tuple(1 if k == axis else 0 for k in range(3))
        for bound in (low[axis], high[axis]):
            face = tuple(p for p in corners if p[axis] == bound)
            faces.append(_cap_order(face, normal))
    return _part(faces)


def _bsp_parts(vertices, triangles):
    stack = [(_box_part(vertices), triangles)]
    result = []
    while stack:
        cell, boundary = stack.pop()
        for polygon in boundary:
            normal = _normal(polygon)
            height = _dot(normal, polygon[0])
            values = [_dot(normal, p)-height for p in cell.vertices]
            if min(values) < 0 < max(values):
                break
        else:
            if _inside(cell.interior, triangles):
                result.append(cell)
            continue
        left, right = _split_cell(cell, normal, height)
        lb, rb = [], []
        for polygon in boundary:
            if all(_dot(normal, p) == height for p in polygon):
                continue
            a = _clip_polygon(polygon, normal, height)
            b = _clip_polygon(polygon, normal, height, True)
            if a:
                lb.append(a)
            if b:
                rb.append(b)
        stack.append((right, tuple(rb)))
        stack.append((left, tuple(lb)))
    return tuple(result)


def _volume_six(triangles):
    origin = triangles[0][0]
    return sum(_dot(_sub(a, origin), _cross(_sub(b, origin), _sub(c, origin)))
               for a, b, c in triangles)


def _merge_parts(parts):
    """Merge full-face neighbours only when every remaining face supports both.

    This does not convexify a concave union: a shared full facet is removed,
    and every retained oriented facet must contain the entire union behind it.
    The final exact volume certificate is checked again by the caller.
    """
    parts = list(parts)
    changed = True
    while changed:
        changed = False
        for i, a in enumerate(parts):
            aset = {frozenset(face) for face in a.faces}
            for j in range(i+1, len(parts)):
                b = parts[j]
                shared = aset & {frozenset(face) for face in b.faces}
                if not shared:
                    continue
                faces = tuple(face for face in a.faces+b.faces if frozenset(face) not in shared)
                vertices = a.vertices+b.vertices
                planes = tuple((_normal(face), face[0]) for face in faces)
                if any(_dot(n, _sub(p, q)) > 0 for n, q in planes for p in vertices):
                    continue
                parts[i] = _part(faces)
                del parts[j]
                changed = True
                break
            if changed:
                break
    return tuple(parts)


def convex_decomposition(polyhedron):
    """Reproducible exact convex decomposition, using Steiner BSP if necessary.

    Gates: test_convex_decomposition_covers_nonstar_pocket_and_cavity and
    test_global3d_support_domain_errors_are_loud. Local manifold checks do not
    purport to certify absence of arbitrary self-intersections in an input mesh.
    """
    vertices = tuple(_point(p) for p in polyhedron.verts)
    faces = tuple(tuple(face) for face in polyhedron.faces)
    if not vertices:
        raise ValueError('global3d requires a closed positive-volume surface')
    anchor = vertices[0]
    local = tuple(_sub(p, anchor) for p in vertices)
    return _translated_parts(_decompose(local, faces, _bsp_parts), anchor)


def _shift_part(part, offset):
    vertices = tuple(tuple(p[k]+offset[k] for k in range(3)) for p in part.vertices)
    faces = tuple(tuple(tuple(p[k]+offset[k] for k in range(3)) for p in face) for face in part.faces)
    interior = tuple(part.interior[k]+offset[k] for k in range(3))
    return ConvexPart3D(vertices, faces, interior)


@lru_cache(maxsize=512)
def _translated_parts(parts, offset):
    return tuple(_shift_part(part, offset) for part in parts)


@lru_cache(maxsize=2048)
def _local_part(part):
    anchor = part.vertices[0]
    return _shift_part(part, tuple(-x for x in anchor)), anchor


@lru_cache(maxsize=128)
def _decompose(vertices, faces, bsp_implementation):
    if len(vertices) < 4 or len(faces) < 4:
        raise ValueError('global3d requires a closed positive-volume surface')
    incidence = {}
    for face in faces:
        for i, j in zip(face, face[1:] + face[:1]):
            incidence.setdefault(tuple(sorted((i, j))), []).append((i, j))
    if any(len(rows) != 2 or rows[0] != tuple(reversed(rows[1]))
           for rows in incidence.values()):
        raise ValueError('global3d requires a closed consistently oriented manifold')
    triangles = _triangulate(vertices, faces)
    volume = _volume_six(triangles)
    if volume <= 0:
        raise ValueError('global3d requires positive oriented volume')
    planes = [(_cross(_sub(b, a), _sub(c, a)), a) for a, b, c in triangles]
    if all(_dot(n, _sub(p, a)) <= 0 for n, a in planes for p in vertices):
        return (_part(triangles),)
    # A bounded-face BSP is used even for star solids. A centre-to-all-faces
    # fan is valid but generates many unnecessary tetrahedral pairs on the
    # TIA prisms; the exact BSP/merge path has fewer parts without special
    # assumptions about a star kernel or Steiner-free tetrahedralization.
    parts = _bsp_parts(vertices, triangles)
    parts = _merge_parts(parts)
    achieved = sum(_volume_six(tuple((face[0], face[k], face[k+1])
                                    for face in part.faces for k in range(1, len(face)-1)))
                   for part in parts)
    if achieved != volume:
        raise ValueError('global3d decomposition volume certificate failed')
    return parts


def _axis(vector):
    denominator = lcm(*(F(x).denominator for x in vector))
    integers = tuple(F(x).numerator*(denominator//F(x).denominator) for x in vector)
    divisor = gcd(*integers)
    if not divisor:
        return None
    sign = 1 if next(x for x in integers if x) > 0 else -1
    return tuple(x//divisor*sign for x in integers)


@lru_cache(maxsize=8192)
def _part_features(part):
    normals = {_axis(_normal(face)) for face in part.faces}
    edges = {_axis(_sub(b, a)) for face in part.faces
             for a, b in zip(face, face[1:] + face[:1])}
    return tuple(sorted(normals-{None})), tuple(sorted(edges-{None}))


@lru_cache(maxsize=8192)
def _pair_slabs(a, b):
    la, ao = _local_part(a)
    lb, bo = _local_part(b)
    displacement = _sub(bo, ao)
    return tuple((n, lo+_dot(n, displacement), hi+_dot(n, displacement))
                 for n, lo, hi in _local_pair_slabs(la, lb))


@lru_cache(maxsize=8192)
def _local_pair_slabs(a, b):
    an, ae = _part_features(a)
    bn, be = _part_features(b)
    axes = set(an + bn)
    axes.update(_axis(_cross(u, v)) for u in ae for v in be)
    axes.discard(None)
    denominator = lcm(*(x.denominator for p in a.vertices+b.vertices for x in p))
    aa = tuple(tuple(x.numerator*(denominator//x.denominator) for x in p) for p in a.vertices)
    bb = tuple(tuple(x.numerator*(denominator//x.denominator) for x in p) for p in b.vertices)
    rows = []
    for axis in sorted(axes):
        pa = [_dot(axis, p) for p in aa]
        pb = [_dot(axis, p) for p in bb]
        rows.append((axis, F(min(pb)-max(pa), denominator), F(max(pb)-min(pa), denominator)))
    return tuple(rows)


def _slab_interval(slabs, start, direction, strict):
    lower = upper = None
    for normal, lo, hi in slabs:
        offset = _dot(normal, start)
        velocity = _dot(normal, direction)
        if not velocity:
            if (offset <= lo or offset >= hi) if strict else (offset < lo or offset > hi):
                return None
            continue
        a, b = (lo-offset)/velocity, (hi-offset)/velocity
        a, b = min(a, b), max(a, b)
        lower = a if lower is None else max(lower, a)
        upper = b if upper is None else min(upper, b)
        if lower > upper or (strict and lower == upper):
            return None
    if lower is None or upper is None:
        raise ValueError('global3d line direction must be nonzero')
    return lower, upper


def _merge(intervals, strict):
    result = []
    for lo, hi in sorted(intervals):
        if result and (lo < result[-1][1] if strict else lo <= result[-1][1]):
            result[-1] = (result[-1][0], max(hi, result[-1][1]))
        else:
            result.append((lo, hi))
    return tuple(result)


@dataclass(frozen=True)
class LineSections3D:
    """E closed intervals and O open intervals; touching O endpoints stay split."""
    closed: tuple
    opened: tuple

    def classify(self, parameter):
        q = _number(parameter)
        if any(lo < q < hi for lo, hi in self.opened):
            return 1
        return 0 if any(lo <= q <= hi for lo, hi in self.closed) else -1

    def first_nonpenetrating(self, parameter=0):
        q = _number(parameter)
        return next((hi for lo, hi in self.opened if lo < q < hi), q)


@dataclass(frozen=True)
class GlobalEntrance3D:
    """Lazy exact E/O convex-pair union, without an explicit boundary mesh."""
    parts_a: tuple
    parts_b: tuple

    def classify(self, translation=(0, 0, 0)):
        """Physical state -1 separated / 0 touching / 1 interior intersection."""
        translation = _point(translation)
        touching = False
        for a in self.parts_a:
            for b in self.parts_b:
                values = [(_dot(n, translation), lo, hi) for n, lo, hi in _pair_slabs(a, b)]
                if all(lo < value < hi for value, lo, hi in values):
                    return 1
                touching |= all(lo <= value <= hi for value, lo, hi in values)
        return 0 if touching else -1

    def line_sections(self, start=(0, 0, 0), direction=(0, 0, 1)):
        """Exact affine line intersection with E and O, including all endpoints."""
        start, direction = _point(start), _point(direction)
        if not any(direction):
            raise ValueError('global3d line direction must be nonzero')
        return _line_sections(self, start, direction, _slab_interval, _merge)


@lru_cache(maxsize=512)
def _line_sections(model, start, direction, interval_implementation, merge_implementation):
    closed, opened = [], []
    for a in model.parts_a:
        for b in model.parts_b:
            # Exact coordinate slabs reject pairs before expensive feature SAT.
            if any(not direction[k] and
                   (max(p[k] for p in a.vertices)+start[k] < min(p[k] for p in b.vertices)
                    or max(p[k] for p in b.vertices) < min(p[k] for p in a.vertices)+start[k])
                   for k in range(3)):
                continue
            slabs = _pair_slabs(a, b)
            interval = _slab_interval(slabs, start, direction, False)
            if interval is not None:
                closed.append(interval)
            interval = _slab_interval(slabs, start, direction, True)
            if interval is not None:
                opened.append(interval)
    return LineSections3D(_merge(closed, False), _merge(opened, True))


def global_entrance(A, B):
    """Construct the exact closed/open convex union for translations of A vs B."""
    return GlobalEntrance3D(convex_decomposition(A), convex_decomposition(B))
