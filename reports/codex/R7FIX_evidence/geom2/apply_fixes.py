from pathlib import Path

def edit(path, fn):
    p=Path(path)
    with p.open(encoding='utf-8',newline='') as f: s=f.read()
    nl='\r\n' if '\r\n' in s else '\n'
    s=fn(s.replace('\r\n','\n'))
    with p.open('w',encoding='utf-8',newline='') as f:f.write(s.replace('\n',nl))

def oracle(s):
    s=s.replace('from math import lcm','from math import lcm\nfrom functools import cmp_to_key')
    marker='\ndef ray_exit(A,B,u):'
    helper='''
def boundary_has_exterior(A, B):
    """Exact local complement certificate, independent of production primitives.

    Vertex/supporting-edge lines partition translation space into cells where
    intersection is constant. At a contact event, inspect one rational point in
    every open angular sector of its incident lines. The step is smaller than
    every nonincident line crossing. An exterior sector means true boundary E;
    a tight-fit seam with no exterior sector is interior E, not an exit.
    """
    lines = set()
    rays = set()
    for P, Q, sign in ((A, B, 1), (B, A, -1)):
        for p in P:
            for a, b in zip(Q, Q[1:]+Q[:1]):
                ex, ey = b[0]-a[0], b[1]-a[1]
                if ex == ey == 0:
                    continue
                h = turn(a, b, p)
                lines.add((sign*-ey, sign*ex, h))
                if h == 0:
                    length = abs(ex)+abs(ey)
                    ray = (ex/length, ey/length)
                    rays.update((ray, (-ray[0], -ray[1])))
    def half(v):
        return 0 if v[1] > 0 or (v[1] == 0 and v[0] > 0) else 1
    def compare(u, v):
        if half(u) != half(v):
            return half(u)-half(v)
        determinant = u[0]*v[1]-u[1]*v[0]
        return -1 if determinant > 0 else (1 if determinant < 0 else 0)
    ordered = sorted(rays, key=cmp_to_key(compare))
    for a, b in zip(ordered, ordered[1:]+ordered[:1]):
        dx, dy = a[0]+b[0], a[1]+b[1]
        if dx == dy == 0:
            dx, dy = -a[1], a[0]
        step = F(1)
        for nx, ny, h in lines:
            slope = nx*dx+ny*dy
            if h and slope:
                step = min(step, abs(h/slope)/2)
        if overlap(translate(A, (step*dx, step*dy)), B) == -1:
            return True
    return False

'''
    s=s.replace(marker,'\n'+helper+marker)
    s=s.replace('"""First exact boundary event, with exact interval membership and no band."""', '''"""First exit from topological int E, including isolated boundary events.

    Strict body overlap implies int E, but the converse fails at tight-fit
    seams. Non-overlap events/intervals therefore require a local exterior
    sector certificate; merely inspecting adjacent ray intervals is unsound.
    """''')
    s=s.replace('''        if overlap(translate(A,(mid*ux,mid*uy)),B)!=1:return lo
        lo=hi''','''        Am = translate(A, (mid*ux, mid*uy))
        state = overlap(Am, B)
        if state == -1 or (state == 0 and boundary_has_exterior(Am, B)):
            return lo
        Ah = translate(A, (hi*ux, hi*uy))
        if overlap(Ah, B) == 0 and boundary_has_exterior(Ah, B):
            return hi
        lo=hi''')
    return s
edit('src/eab/kernel2d/g0_oracle.py',oracle)

def geom(s):
    s=s.replace('from math import hypot','from math import hypot\n\nfrom ..construction import sqrt_rational')
    s=s.replace('''    return hypot(a[0], a[1])''','''    """One final checked square root of the exact supplied vector square."""
    x, y = map(Fraction, a)
    return sqrt_rational(x*x+y*y)''',1)
    s=s.replace('''    n = norm(a)
    if n == 0.0:
        raise ZeroDivisionError("unit of zero vector")
    return (a[0] / n, a[1] / n)''','''    """Normalize exact component ratios, never divide by the rounded norm."""
    x, y = map(Fraction, a)
    square = x*x+y*y
    if not square:
        raise ZeroDivisionError("unit of zero vector")
    return tuple(((v > 0)-(v < 0))*sqrt_rational(v*v/square) for v in (x, y))''')
    s=s.replace('''    e_prev = sub(poly[i % n], poly[(i - 1) % n])
    e_next = sub(poly[(i + 1) % n], poly[i % n])
    return cross(e_prev, e_next)''','''    a, b, c = (tuple(map(Fraction, poly[k % n])) for k in (i-1, i, i+1))
    return _display_fraction(cross(sub(b, a), sub(c, b)))''')
    s=s.replace('''    e_prev = sub(poly[i % n], poly[(i - 1) % n])
    e_next = sub(poly[(i + 1) % n], poly[i % n])
    from math import atan2
    return atan2(cross(e_prev, e_next), dot(e_prev, e_next))''','''    a, b, c = (tuple(map(Fraction, poly[k % n])) for k in (i-1, i, i+1))
    u, v = sub(b, a), sub(c, b)
    determinant, scalar = cross(u, v), dot(u, v)
    scale = max(abs(determinant), abs(scalar))
    if not scale:
        raise ValueError("turn angle at zero-length edge")
    from math import atan2
    return atan2(_display_fraction(determinant/scale), _display_fraction(scalar/scale))''')
    return s
edit('src/eab/kernel2d/geom.py',geom)

def cov(s):
    s=s.replace('''    df = (float(d[0]), float(d[1]))
    return Cover("VV", ia, jb, unit(df), norm(df), None, a, active, a, b, expanded)''','''    return Cover("VV", ia, jb, unit(d), norm(d), None, a, active, a, b, expanded)''')
    s=s.replace('''def _in_gap_window(c, A, B, window):
    if window < 0:''','''def _in_gap_window(c, A, B, window):
    return _feature_in_gap_window(c.kind, c.a_index, c.b_index, A, B, window)


def _feature_in_gap_window(kind, ai, bj, A, B, window):
    """Exact window check before potentially unrepresentable construction."""
    if window < 0:''')
    s=s.replace('''    if c.kind == "VV":
        d = _vsub(_fr(A[c.a_index]), _fr(B[c.b_index]))''','''    if kind == "VV":
        d = _vsub(_fr(A[ai]), _fr(B[bj]))''')
    s=s.replace('''    P, E, i, j = (A, B, c.a_index, c.b_index) if c.kind == "VE" else (B, A, c.b_index, c.a_index)''','''    P, E, i, j = (A, B, ai, bj) if kind == "VE" else (B, A, bj, ai)''')
    s=s.replace('''            c = ve_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and _in_gap_window(c, A, B, window) and (''','''            if not _feature_in_gap_window("VE", ia, jb, A, B, window):
                continue
            c = ve_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and (''')
    s=s.replace('''            c = ev_cover(A, ka, B, ib, tol, cone_tol)
            if c is not None and _in_gap_window(c, A, B, window) and (''','''            if not _feature_in_gap_window("EV", ka, ib, A, B, window):
                continue
            c = ev_cover(A, ka, B, ib, tol, cone_tol)
            if c is not None and (''')
    s=s.replace('''            c = vv_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and (c.strict or c.window_active) and _in_gap_window(c, A, B, window):''','''            if not _feature_in_gap_window("VV", ia, jb, A, B, window):
                continue
            c = vv_cover(A, ia, B, jb, tol, cone_tol)
            if c is not None and (c.strict or c.window_active):''')
    s=s.replace('''    n = outward_normal(B, bj) if norm(sub(b1, b0)) >= norm(sub(a1, a0)) else neg(outward_normal(A, ai))''','''    da, db = _vsub(_fr(a1), _fr(a0)), _vsub(_fr(b1), _fr(b0))
    n = outward_normal(B, bj) if dot(db, db) >= dot(da, da) else neg(outward_normal(A, ai))''')
    return s
edit('src/eab/kernel2d/covers.py',cov)

def gates(s):
    start=s.index('def char_length(');end=s.index('\ndef sample_translations',start)
    s=s[:start]+'''def _char_length_squared(*polys):
    """Exact squared diameter: a large finite input must not create inf tolerance."""
    return max(((Fraction(x1)-Fraction(x0))**2+(Fraction(y1)-Fraction(y0))**2
                for x0, x1, y0, y1 in map(_bbox, polys)), default=Fraction(0))


def char_length(*polys: Poly) -> float:
    """Checked display of maximal bbox diagonal; gates use its exact square."""
    return independent.sqrt_display(_char_length_squared(*polys))


def _construction_error_exceeds(error, length2, truth, atol, *polys):
    """Finite errors only; compare the exact bound without constructing sqrt(L²).

    error > atol*max(L,truth)+64*eps*C is squared after removing the exact
    roundoff term. Neither a huge diameter nor a tiny coefficient can overflow
    or silently underflow the acceptance threshold.
    """
    if not math.isfinite(error) or not math.isfinite(truth):
        return True
    if not math.isfinite(atol) or atol < 0:
        raise ValueError("atol must be finite and nonnegative")
    scale = max((abs(Fraction(v)) for P in polys for p in P for v in p), default=Fraction(0))
    excess = Fraction(error)-Fraction(64*math.ulp(1.0))*scale
    return excess > 0 and excess*excess > Fraction(atol)**2*max(length2, Fraction(truth)**2)

''' + s[end:]
    s=s.replace('L = char_length(A, B)','L2 = _char_length_squared(A, B)')
    s=s.replace('covs = enumerate_covers(At, B, window=inf)','''# Search only the independently certified nearest-distance window. The
        # outward-rounded bound includes the exact root and avoids constructing
        # unrelated distances beyond binary64 range.
        covs = enumerate_covers(At, B, window=math.nextafter(truth, inf))''')
    s=s.replace('''if err > atol * max(L, truth) + round_floor(coord_scale(At, B)):''','''if _construction_error_exceeds(err, L2, truth, atol, At, B):''')
    s=s.replace('covs = enumerate_covers(Az, B, window=inf)','covs = enumerate_covers(Az, B, window=0.0)')
    s=s.replace('''if got > atol * L + round_floor(coord_scale(Az, B)):''','''if _construction_error_exceeds(got, L2, 0.0, atol, Az, B):''')
    s=s.replace('''the ray; independent integer winding checks each interval without a noise
    band. The Fraction result preserves the exact event for gate construction.''','''the ray; independent integer winding checks intervals and events without a
    noise band. Local rational line-arrangement sectors distinguish true boundary
    events from tight-fit seams inside E. The Fraction result preserves the exact
    event for gate construction.''')
    return s
edit('src/eab/kernel2d/g0.py',gates)
