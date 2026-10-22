"""Certificate-driven planar translation in the complement of open overlap.

Search uses GlobalEntrance2 convex cells, not the convex hull of their union.
An open-cell overlap graph proposes winding barriers; the free arrangement
visibility graph proposes escape paths, including zero-width contact seams.
Every accepted status passes a separate input-polygon certificate verifier.
Finite resource limits return UNPROVED, never a topological guess.
Gates: tests/test_tia2d_t1b_translation.py (independent paths and barriers).
"""
from dataclasses import dataclass
from fractions import Fraction as Q

from .global_entrance import (GlobalEntrance2, _ring, _point, _edges, _sub,
    _cross, _at, _cell_state, _split_segments, _area2)
from .translation_certificates import (verify_escape_certificate,
    verify_trapping_certificate, verify_wobble_bounds, translation_segment_strictly_blocked)


@dataclass(frozen=True)
class TranslationComponent2:
    status: str
    reason: str
    path: tuple = ()
    verification: object = None
    area_bounds: tuple | None = None
    diameter_squared_bounds: tuple | None = None
    inner_square_radius: Q | None = None
    bounds_verification: object = None
    source: str = "exact_open_obstacle_cells_and_independent_verifier"
    observable: str = "origin_translation_component"


def _clip(poly, a, b):
    result = []
    for p, q in _edges(poly):
        hp = _cross(_sub(b, a), _sub(p, a))
        hq = _cross(_sub(b, a), _sub(q, a))
        if hp >= 0:
            result.append(p)
        if (hp < 0 < hq) or (hq < 0 < hp):
            result.append(_at(p, _sub(q, p), hp / (hp-hq)))
    return tuple(dict.fromkeys(result))


def _intersection(a, b):
    result = a
    for p, q in _edges(b):
        if len(result) < 3:
            return ()
        result = _clip(result, p, q)
    return result if len(result) >= 3 and _area2(result) > 0 else ()


def _center(poly):
    return tuple(sum((p[k] for p in poly), Q(0))/len(poly) for k in (0, 1))


def _crossing(a, b):
    z = _cross(a, b)
    return (1 if a[1] <= 0 < b[1] and z > 0 else
            -1 if b[1] <= 0 < a[1] and z < 0 else 0)


def _barrier(cells):
    centers = tuple(_center(p) for p in cells)
    graph = [[] for _ in cells]
    for i, a in enumerate(cells):
        for j in range(i+1, len(cells)):
            common = _intersection(a, cells[j])
            if common:
                point = _center(common)
                graph[i].append((j, point))
                graph[j].append((i, point))
    paths, winding = {}, {}
    for root in range(len(cells)):
        if root in paths:
            continue
        paths[root], winding[root] = (centers[root],), 0
        queue = [root]
        while queue:
            i = queue.pop(0)
            for j, point in graph[i]:
                increment = _crossing(centers[i], point)+_crossing(point, centers[j])
                if j not in paths:
                    paths[j] = paths[i]+(point, centers[j])
                    winding[j] = winding[i]+increment
                    queue.append(j)
                elif winding[i]+increment-winding[j]:
                    raw = paths[i]+(point,)+tuple(reversed(paths[j]))
                    return tuple(p for k, p in enumerate(raw) if not k or p != raw[k-1])
    return ()


def _segment_hits_open(cell, a, b):
    """Intersect strict affine half-plane constraints with closed [0,1]."""
    lo, hi = Q(0), Q(1)
    for p, q in _edges(cell):
        h = _cross(_sub(q, p), _sub(a, p))
        d = _cross(_sub(q, p), _sub(b, a))
        if not d:
            if h <= 0:
                return False
            continue
        bound = -h/d
        if d > 0:
            lo = max(lo, bound)
        else:
            hi = min(hi, bound)
    if lo < hi:
        return True
    return lo == hi and 0 <= lo <= 1 and _cell_state(cell, _at(a, _sub(b, a), lo)) == 1


def _free_segment(cells, a, b):
    return not any(_segment_hits_open(c, a, b) for c in cells)


def _escape(cells, max_vertices):
    magnitude = max((abs(v) for c in cells for p in c for v in p), default=Q(0))
    reach = 4*magnitude+1
    targets = tuple((reach*x, reach*y) for x, y in
                    ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)))
    zero = (Q(0), Q(0))
    for target in targets:
        if _free_segment(cells, zero, target):
            return (zero, target), "direct_free_path"
    segments = tuple(sorted({tuple(sorted((p, q))) for c in cells for p, q in _edges(c)}))
    if len(segments) > max_vertices:
        return (), "arrangement_resource_limit"
    vertices = sorted({p for edge in _split_segments(segments) for p in edge
                       if not any(_cell_state(c, p) == 1 for c in cells)})
    if len(vertices) > max_vertices:
        return (), "visibility_resource_limit"
    vertices = [zero]+[p for p in vertices if p != zero]+list(targets)
    target_start = len(vertices)-len(targets)
    previous, queue = {0: None}, [0]
    while queue:
        i = queue.pop(0)
        for j, p in enumerate(vertices):
            if j in previous or not _free_segment(cells, vertices[i], p):
                continue
            previous[j] = i
            if j >= target_start:
                path = []
                while j is not None:
                    path.append(vertices[j])
                    j = previous[j]
                return tuple(reversed(path)), "arrangement_free_path"
            queue.append(j)
    return (), "no_verified_path_or_barrier"


def _refine(moving, obstacles, path):
    result = [path[0]]
    pending = [(a, b, 0) for a, b in reversed(tuple(zip(path, path[1:])))]
    while pending:
        a, b, depth = pending.pop()
        if translation_segment_strictly_blocked(moving, obstacles, a, b):
            result.append(b)
        elif depth < 64:
            middle = ((a[0]+b[0])/2, (a[1]+b[1])/2)
            pending.extend(((middle, b, depth+1), (a, middle, depth+1)))
        else:
            return ()
    return tuple(result)


def _inner_radius(cells):
    radii = []
    for cell in cells:
        if _cell_state(cell, (Q(0), Q(0))) >= 0:
            return Q(0)
        for a, b in _edges(cell):
            values = [a, b]
            for sign in (-1, 1):
                h, d = a[0]+sign*a[1], b[0]-a[0]+sign*(b[1]-a[1])
                if d and 0 <= -h/d <= 1:
                    values.append(_at(a, _sub(b, a), -h/d))
            radii.extend(max(abs(p[0]), abs(p[1])) for p in values)
    return min(radii)


def translation_component(moving, obstacles, *, max_cells=512, max_vertices=2000):
    """Return only independently verified TRAPPED/ESCAPABLE, else UNPROVED.

    Area/diameter bounds, not an exact component reconstruction, accompany a
    barrier. Diameter is encoded squared to keep bounds rational. The upper
    rectangle follows from winding invariance on the free component. The
    lower square uses exact minimum L-infinity distance to every convex cell.
    """
    moving, obstacles = _ring(moving), tuple(_ring(p) for p in obstacles)
    models = tuple(GlobalEntrance2(moving, p, merge_convex=True) for p in obstacles)
    if any(model.membership((0, 0)) == 1 for model in models):
        return TranslationComponent2("UNPROVED", "origin_in_open_obstacle")
    cells = tuple(dict.fromkeys(c for model in models for c in model.cells))
    if len(cells) > max_cells:
        return TranslationComponent2("UNPROVED", "cell_resource_limit")
    # Direct escape is cheap, including exact contact seams.
    path, reason = _escape(cells, 0)
    if path:
        check = verify_escape_certificate(moving, obstacles, path)
        if check.valid:
            return TranslationComponent2("ESCAPABLE_TRANSLATION", reason, path, check)
    path = _barrier(cells)
    if path:
        path = _refine(moving, obstacles, path)
        if path:
            check = verify_trapping_certificate(moving, obstacles, path)
            if check.valid:
                r = _inner_radius(cells)
                bounds = verify_wobble_bounds(moving, obstacles, path, r)
                if bounds.valid:
                    return TranslationComponent2("TRAPPED_TRANSLATION", "strict_winding_barrier", path, check,
                        (bounds.area_lower, bounds.area_upper),
                        (bounds.diameter_squared_lower, bounds.diameter_squared_upper), r, bounds)
                return TranslationComponent2("UNPROVED", "independent_bounds_verification_failed:"+bounds.reason)
    path, reason = _escape(cells, max_vertices)
    if path:
        check = verify_escape_certificate(moving, obstacles, path)
        if check.valid:
            return TranslationComponent2("ESCAPABLE_TRANSLATION", reason, path, check)
        reason = "independent_escape_verification_failed:"+check.reason
    return TranslationComponent2("UNPROVED", reason)


def tolerance_component(moving, obstacles, delta, *, element="square", erode_obstacles=True,
                        max_cells=512, max_vertices=2000):
    """Erode one moving ring and optionally all fixed rings before searching."""
    from .erosion import erode_polygon_exact
    if not isinstance(element, str):
        element = _ring(element)
    result = erode_polygon_exact(moving, delta, element)
    if result.status != "ACCEPTED":
        return TranslationComponent2("UNPROVED", "moving_erosion_rejected:"+str(result.reason))
    fixed = []
    for p in obstacles:
        item = erode_polygon_exact(p, delta if erode_obstacles else 0, element)
        if item.status != "ACCEPTED":
            return TranslationComponent2("UNPROVED", "obstacle_erosion_rejected:"+str(item.reason))
        fixed.append(item.polygon)
    return translation_component(result.polygon, fixed, max_cells=max_cells, max_vertices=max_vertices)


def critical_tolerance(moving, obstacles, low, high, *, iterations=12, element="square",
                       erode_obstacles=True, max_cells=512, max_vertices=2000):
    """Dyadic bisection with verified opposite statuses, no guessed attainment.

    Rejected erosions and unknown queries interrupt with an explicit reason.
    The function does not extend the domain past accepted simple rings.
    """
    moving, obstacles = _ring(moving), tuple(_ring(p) for p in obstacles)
    if not isinstance(element, str):
        element = _ring(element)
    low, high = Q(low), Q(high)
    if not 0 <= low < high or iterations < 0:
        raise ValueError("need 0 <= low < high and nonnegative iterations")
    a = tolerance_component(moving, obstacles, low, element=element, erode_obstacles=erode_obstacles,
                            max_cells=max_cells, max_vertices=max_vertices)
    b = tolerance_component(moving, obstacles, high, element=element, erode_obstacles=erode_obstacles,
                            max_cells=max_cells, max_vertices=max_vertices)
    if a.status != "TRAPPED_TRANSLATION" or b.status != "ESCAPABLE_TRANSLATION":
        return dict(status="UNPROVED", reason="endpoints_not_opposite", low=low, high=high,
                    low_result=a, high_result=b, attained=None)
    for _ in range(iterations):
        middle = (low+high)/2
        result = tolerance_component(moving, obstacles, middle, element=element, erode_obstacles=erode_obstacles,
                                     max_cells=max_cells, max_vertices=max_vertices)
        if result.status == "TRAPPED_TRANSLATION":
            low, a = middle, result
        elif result.status == "ESCAPABLE_TRANSLATION":
            high, b = middle, result
        else:
            return dict(status="UNPROVED", reason=result.reason, low=low, high=high,
                        low_result=a, high_result=b, attained=None)
    return dict(status="CERTIFIED_BRACKET", reason="monotone_erosion", low=low, high=high,
                low_result=a, high_result=b, attained=None)
