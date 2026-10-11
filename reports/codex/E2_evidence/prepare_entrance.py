"""Apply the WO-E2 convex-only ray predicate repair after the baseline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = ROOT / 'src/eab/kernel2d/entrance.py'
with p.open(encoding='utf-8', newline='') as f:
    original = f.read()
nl = '\r\n' if '\r\n' in original else '\n'
s = original.replace('\r\n', '\n')
s = s.replace('from dataclasses import dataclass', 'from dataclasses import dataclass\nfrom fractions import Fraction')
s = s.replace('from .exact import convexity_violation', 'from .exact import convexity_violation, entrance_block_exact, membership_exact')
s = s.replace('dot, edge, is_convex, neg,', 'dot, edge, neg,')
s = s.replace('    if polygons_overlap(translate(A, x0), B, ctol) == 1:\n        return shortest_exit(A, B, x0, tol=tol)\n    if convexity_violation(A) is None and convexity_violation(B) is None:      # 精确凸才走凸路径（E2）\n        return _first_entrance_convex(A, B, x0, d, ctol, r, t_max)',
'''    if convexity_violation(A) is None and convexity_violation(B) is None:      # 精确凸才走凸路径（E2）
        if membership_exact(A, B, x0) == 1:
            return shortest_exit(A, B, x0, tol=tol)
        return _first_entrance_convex(A, B, x0, d, ctol, r, t_max)
    if polygons_overlap(translate(A, x0), B, ctol) == 1:
        return shortest_exit(A, B, x0, tol=tol)''')
start = s.index('def _first_entrance_convex(')
end = s.index('\n\ndef _cover_at(', start)
s = s[:start] + '''def _first_entrance_convex(A: Poly, B: Poly, x0: Point, d: Point, ctol: float, r: float, t_max: float) -> Entrance2:
    """精确有理数半空间射线裁剪；facet_gap 只在最后输出构造量，不参与去留/时刻分支。
    tol/r 仅为并列标签报告窗，不能把错过 E 或超过 t_max 的射线变成命中。
    门：test_convex_ray_decisions_do_not_use_constructed_facet_gaps / test_convex_ray_resolves_tiny_slopes_and_misses。
    """
    eb = entrance_block_exact(A, B)
    X, D = tuple(map(Fraction, x0)), tuple(map(Fraction, d))
    enter = []
    active = []
    t_out = None

    def none():
        return Entrance2("none", 0.0, None, None, None, None, None, 0.0, (), len(enter))

    for f in eb.facets:
        ex, ey = f.direction
        # h >= 0 是 E 的内半空间；不用单位法向或浮点差分求斜率。
        h = ex * (X[1] - f.start[1]) - ey * (X[0] - f.start[0])
        slope = ex * D[1] - ey * D[0]
        if h == 0:
            active.append(f)
        if slope > 0:
            enter.append((-h / slope, slope, f))
        elif slope < 0:
            bound = -h / slope
            t_out = bound if t_out is None else min(t_out, bound)
        elif h < 0:
            return none()
    t_in = max([Fraction(0)] + [t for t, _, _ in enter])
    if (t_out is not None and t_in > t_out) or (t_max != float("inf") and t_in > Fraction(t_max)):
        return none()
    best = max(enter, key=lambda q: q[0]) if enter else None
    if t_in == 0 and active:
        # 已恰好接触：定义 min{t>=0:x(t)∈E}=0，包括沿边或背离运动。
        fbest = next((f for t, _, f in enter if t == 0), active[0])
    elif best is not None and best[0] == t_in:
        fbest = best[2]
    else:
        return none()
    band2 = Fraction(ctol + r) ** 2
    tied = []
    for t, slope, f in enter:
        ex, ey = f.direction
        if ((t - t_in) * slope) ** 2 <= band2 * (ex * ex + ey * ey):
            tied.append(f.label)
    if fbest.label not in tied:
        tied.insert(0, fbest.label)
    tied.sort(key=lambda lab: 0 if lab == fbest.label else 1)
    lab = fbest.label
    x = (float(X[0] + D[0] * t_in), float(X[1] + D[1] * t_in))
    pa, pb = _facet_points(A, B, lab, x)
    return Entrance2("entrance", float(t_in), x, lab, _facet_normal(A, B, lab), pa, pb,
                     facet_gap(A, B, lab, x), tuple(tied), len(enter))
''' + s[end:]
s = s.replace('"""沿 x(t) = x0 + t·d 的首入（见模块文档）。A、B 均 CCW；tol 为长度容差（并列与谓词的带，抬到舍入地板）。"""',
'''"""沿 x(t) = x0 + t·d 的首入。凸路径选路、初态与射线裁剪精确；tol只影响并列报告。
    凹路径及已侵入后的 shortest_exit 保持既有长度带/舍入地板口径（E3待做）。"""''')
s = s.replace('容差（纪律 F）：谓词与并列按长度地板 c·eps·C 加调用方 tol；facet 法向沿用 `facet_gap` 的口径（噪声内共线链里最长边的法向）。',
'''E2：凸选路、凸初态、半空间射线裁剪均用精确有理数；facet_gap/法向/接触点只作浮点输出，法向取 facet 自己的边。
并列标签报告仍按调用方 tol 与舍入量级；凹首入、已侵入后的最短出口保持既有容差路径，不属于凸谓词精确化声明。''')
with p.open('w', encoding='utf-8', newline='') as f:
    f.write(s.replace('\n', nl))
