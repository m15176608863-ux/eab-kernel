"""WO-E2 staging only: build reviewable drafts without touching tested sources."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def read(path):
    with (ROOT / path).open(encoding="utf-8", newline="") as f:
        return f.read()


def draft(path, old, new):
    assert old != new
    nl = "\r\n" if "\r\n" in old else "\n"
    new = new.replace("\r\n", "\n").replace("\n", nl)
    with (OUT / (Path(path).name + ".draft")).open("w", encoding="utf-8", newline="") as f:
        f.write(new)


path = "src/eab/kernel2d/exact.py"
old = read(path)
start = old.index("def convex_overlap_exact(")
end = old.index("# ---------------------------------------------------------------- 法锥", start)
replacement = '''def convex_overlap_exact(A: Poly, B: Poly, x: Point = (0.0, 0.0)) -> int:
    """凸 CCW 对的独立精确 SAT oracle：1 内部相交 / 0 恰相触 / -1 分离。

    纪律 A：只用 Fraction 构造、内联坐标差与投影；不调用本模块的 _fr / _sub / _cross / _dot、
    Minkowski、法锥或 geom 的任何几何原语。平移同样在 Fraction 上做，不先形成舍入后的 A+x。
    门：tests/test_kernel2d_exact.py::test_sat_oracle_uses_no_kernel_geometry_primitive。
    """
    xx, xy = Fraction(x[0]), Fraction(x[1])
    FA = [(Fraction(a[0]) + xx, Fraction(a[1]) + xy) for a in A]
    FB = [(Fraction(b[0]), Fraction(b[1])) for b in B]
    touch = False
    for P, Q in ((FA, FB), (FB, FA)):
        for k in range(len(P)):
            p, q = P[k], P[(k + 1) % len(P)]
            nx, ny = q[1] - p[1], p[0] - q[0]
            if nx == 0 and ny == 0:
                continue
            pmax = nx * p[0] + ny * p[1]
            qmin = min(nx * v[0] + ny * v[1] for v in Q)
            if qmin > pmax:
                return -1
            if qmin == pmax:
                touch = True
    return 0 if touch else 1


'''
draft(path, old, old[:start] + replacement + old[end:])

path = "src/eab/kernel2d/g0.py"
old = read(path)
new = old.replace("from .exact import entrance_block_exact, hull_exact_fr, polygons_overlap_exact, strict_vertices",
                  "from .exact import convex_overlap_exact, entrance_block_exact, strict_vertices")
new = new.replace("票一  成员（精确 E 的 facet 符号）== 暴力谓词（两份精确耳切逐对三角形的精确分离轴，`exact.polygons_overlap_exact`），",
                  "票一  成员（精确 E 的 facet 符号）== 独立内联 Fraction 分离轴（`exact.convex_overlap_exact`），")
new = new.replace("票二  局部法锥规则的严格集（精确符号）== 全局 Minkowski 的非 FF facet 集；",
                  "票二  局部法锥严格/边界集 == 独立全顶点投影支持集；walk 的严格 VE/EV == 唯一支持标签集；\n        平直链的非 FF 余段须属于精确边界集，不再错误地算作严格 facet，也不豁免任何标签；")
new = new.replace("票三  E 的严格凸顶点集 == conv{b − a} 的精确凸包顶点集（差点 b − a 在 Fraction 上算，不舍入）。",
                  "票三  E 的严格凸顶点集 == 独立内联 Fraction gift-wrap 的 conv{b − a} 顶点集（差点不舍入）。")
new = new.replace("容差（纪律 F，M0.2）：本模块内部不再有绝对阈值。", "以下容差口径只适用于凹块距离/出口完备性，凸 G0 不使用容差：")
anchor = "def g0_convex("
pos = new.index(anchor)
helpers = '''def _support_labels_independent(A: Poly, B: Poly) -> tuple[set[tuple], set[tuple]]:
    """独立票二 oracle：全顶点投影的最小支持集；只用内联 Fraction 算术，零法锥/极角/Minkowski 原语。

    唯一支持顶点给严格标签；多点并列给边界标签（包括平直顶点），不使用几何容差。
    """
    FA = [(Fraction(p[0]), Fraction(p[1])) for p in A]
    FB = [(Fraction(p[0]), Fraction(p[1])) for p in B]
    strict, boundary = set(), set()
    for target, edges, kind in ((FA, FB, "VE"), (FB, FA, "EV")):
        for k in range(len(edges)):
            p, q = edges[k], edges[(k + 1) % len(edges)]
            nx, ny = q[1] - p[1], p[0] - q[0]
            projections = [nx * v[0] + ny * v[1] for v in target]
            bottom = min(projections)
            support = [i for i, z in enumerate(projections) if z == bottom]
            labels = {(kind, i, k) if kind == "VE" else (kind, k, i) for i in support}
            (strict if len(support) == 1 else boundary).update(labels)
    return strict, boundary


def _difference_hull_independent(A: Poly, B: Poly) -> set[tuple[Fraction, Fraction]]:
    """独立票三 oracle：Jarvis gift-wrap，内联 Fraction 差/行列式/距离；不共用 exact 的单调链或任何几何原语。"""
    points = sorted({(Fraction(b[0]) - Fraction(a[0]), Fraction(b[1]) - Fraction(a[1]))
                     for a in A for b in B})
    if len(points) < 3:
        return set(points)
    start = current = points[0]
    hull = set()
    while True:
        hull.add(current)
        candidate = next(p for p in points if p != current)
        for p in points:
            ux, uy = candidate[0] - current[0], candidate[1] - current[1]
            vx, vy = p[0] - current[0], p[1] - current[1]
            determinant = ux * vy - uy * vx
            if determinant < 0 or (determinant == 0 and vx * vx + vy * vy > ux * ux + uy * uy):
                candidate = p
        current = candidate
        if current == start:
            return hull


'''
new = new[:pos] + helpers + new[pos:]
start = new.index('    glob = {f.label', new.index('def g0_convex('))
end = new.index('    E = {ex.vertices', start)
new = new[:start] + '''    walk = {f.label for f in ex.facets if f.label[0] != "FF"}
    truth_strict, truth_boundary = _support_labels_independent(A, B)
    glob = walk - truth_boundary
    loc, amb = local_facets(A, B), ambiguous_facets(A, B)
    rep.facet_local, rep.facet_global, rep.facet_ambiguous = len(loc), len(glob), len(amb)
    # 全集等式而非 ambiguous 豁免：平直链余段也必须通过独立闭包支持检查。
    rep.facet_symmetric_diff = sorted((loc ^ truth_strict) | (amb ^ truth_boundary)
                                      | (glob ^ truth_strict) | (walk - truth_strict - truth_boundary))
    H = _difference_hull_independent(A, B)
''' + new[end:]
new = new.replace("        brute = polygons_overlap_exact(A, B, x)", "        brute = convex_overlap_exact(A, B, x)")
draft(path, old, new)

path = "tests/test_kernel2d_exact.py"
old = read(path)
new = old.replace('    if not (is_convex_exact(A) and is_convex_exact(B)):\n        pytest.skip("rounding made a vertex reflex")',
                  '    # 原门遇舍入微凹就跳过；新门覆盖每个固定样本，生成器的严格凸余量必须保持可分辨。\n    assert is_convex_exact(A) and is_convex_exact(B), "fixed strict-convex sample lost its margin"')
new = new.replace('    if not (is_convex_exact(A) and is_convex_exact(B)):\r\n        pytest.skip("rounding made a vertex reflex")',
                  '    # 原门遇舍入微凹就跳过；新门覆盖每个固定样本，生成器的严格凸余量必须保持可分辨。\r\n    assert is_convex_exact(A) and is_convex_exact(B), "fixed strict-convex sample lost its margin"')
new = new.replace('def test_exact_membership_equals_exact_separating_axis_oracle(seed, t):',
                  'def test_exact_membership_equals_exact_separating_axis_oracle(seed, t):\n    """独立内联 Fraction SAT 对照：旧门可 skip 舍入样本；新门每个固定样本必测，边界探针不豁免。"""', 1)
new += (OUT / "exact_test_additions.txt").read_text(encoding="utf-8")
draft(path, old, new)
print("Prepared exact.py.draft, g0.py.draft, test_kernel2d_exact.py.draft; no tested source modified.")
