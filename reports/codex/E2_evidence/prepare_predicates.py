"""WO-E2 scoped rewrite; apply only after the untouched baseline completes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = ROOT / 'tests/test_kernel2d_predicates.py'
with p.open(encoding='utf-8', newline='') as f:
    old = f.read()
nl = '\r\n' if '\r\n' in old else '\n'
s = old.replace('\r\n', '\n')
s = s.replace('from eab.kernel2d.g0 import g0_convex, random_convex_polygon',
'''from eab.kernel2d.g0 import g0_convex, random_convex_polygon
from eab.kernel2d.exact import convex_overlap_exact, polygons_overlap_exact''')

def replace_body(name, new):
    global s
    start = s.index('def ' + name + '(')
    end = s.find('\n\n\n', start)
    if end == -1:
        end = len(s)
    s = s[:start] + new.rstrip() + s[end:]

replace_body('test_membership_without_eb_agrees_with_brute_force_in_any_unit', '''def test_membership_without_eb_agrees_with_brute_force_in_any_unit(s):
    """旧门只核两侧非零的带外随机点；E2 用独立内联 Fraction SAT 核全部点（不舍入 A+x）。
    零容差逐点全等，另核调用方报告带只能把精确答案改成0，绝不能翻号；原有60×20点与尺度全部保留。"""
    rng = random.Random(21)
    nonzero = 0
    for _ in range(60):
        A0, B0 = random_convex_polygon(rng, rng.randint(3, 7)), random_convex_polygon(rng, rng.randint(3, 8))
        A, B, tol = _scaled(A0, s), _scaled(B0, s), 1e-3 * s
        for _ in range(20):
            x = (rng.uniform(-3.0, 3.0) * s, rng.uniform(-3.0, 3.0) * s)
            truth = convex_overlap_exact(A, B, x)
            assert membership_convex(A, B, x) == truth, (A0, B0, x)
            report = membership_convex(A, B, x, tol)
            assert report in (0, truth), (x, report, truth)
            nonzero += report != 0
    assert nonzero >= 600
''')

start = s.index('    # 两条长边夹 0.1 rad')
end = s.index('    rng = random.Random(1)', start)
s = s[:start] + '''    # 旧门豁免短倒角的错误合并；现在连短边也不豁免：本例没有任何精确反向平行边。
    assert not any(f[0] == "FF" for f in eb.facets), eb.facets
''' + s[end:]
s = s.replace('b = polygons_overlap(translate(TILTED_TRIANGLE, x), B, 0.0)\n        if m != 0 and b != 0:\n            n += 1\n            if m != b:\n                wrong.append((x, m, b))',
'''b = convex_overlap_exact(TILTED_TRIANGLE, B, x)
        n += 1
        if m != b:
            wrong.append((x, m, b))''')
s = s.replace('成员判定 16/2000 答反、g0 报红。"""', '成员判定 16/2000 答反、g0 报红。\n    E2 不再豁免短边合并或跳过0：全部1500点与独立 Fraction SAT 精确一致，比旧带外门更强。"""')

replace_body('test_a_t_vertex_one_ulp_above_the_lowest_edge_is_still_convex', '''def test_a_t_vertex_one_ulp_above_the_lowest_edge_uses_the_concave_path(quarter):
    """旧口径把一个ulp微凹吞成平直顶点并强制4FF；E2精确拒收，再走一般简单多边形路径。
    保留四朝向与300点，额外保留精确平直对照；全部答案对闭式矩形减三角缺口 oracle，零带内豁免。
    oracle只用内联 Fraction 区间/线性插值，与凸构造及凹相交的耳切/SAT零共用。"""
    C = 1e5
    bump = math.nextafter(C, math.inf)
    P = [(C, C), (C + 1.0, bump), (C + 2.0, C), (C + 2.0, C + 1.0), (C, C + 1.0)]
    flat = [(C, C), (C + 1.0, C), (C + 2.0, C), (C + 2.0, C + 1.0), (C, C + 1.0)]
    for _ in range(quarter):
        P = [(-y, x) for x, y in P]
        flat = [(-y, x) for x, y in flat]
    for tol in (0.0, 1e-9, 1.0):
        with pytest.raises(ValueError, match="reflex"):
            convex_entrance_block(SQUARE, P, tol=tol)
    eb = convex_entrance_block(SQUARE, flat)
    assert sorted(f[0] for f in eb.facets) == ["FF", "FF", "FF", "FF", "VE"]
    assert all(math.dist(eb.vertices[i], eb.vertices[(i + 1) % len(eb.vertices)]) > 0.5 for i in range(len(eb.vertices)))
    rng = random.Random(quarter)
    cx, cy = (sum(p[0] for p in P) / 5, sum(p[1] for p in P) / 5)
    xs = [(cx + rng.uniform(-2, 2), cy + rng.uniform(-2, 2)) for _ in range(300)]
    # 先在原坐标精确加x，再逆90度旋转，得到轴对齐方块的区间。
    for x in xs:
        points = [(Fraction(a) + Fraction(x[0]), Fraction(b) + Fraction(x[1])) for a, b in SQUARE]
        for _ in range(quarter):
            points = [(b, -a) for a, b in points]
        lo, hi = max(Fraction(C), min(p[0] for p in points)), min(Fraction(C + 2), max(p[0] for p in points))
        low_y, high_y = min(p[1] for p in points), max(p[1] for p in points)
        if lo > hi or low_y > C + 1:
            want = -1
        else:
            h = Fraction(bump) - Fraction(C)
            bottom = lambda z: Fraction(C) + h * min(z - C, C + 2 - z)
            floor = min(bottom(lo), bottom(hi))
            want = -1 if high_y < floor else (0 if lo == hi or high_y == floor or low_y == C + 1 else 1)
        assert membership_convex(SQUARE, P, x) == want, (quarter, x, want)
''')

replace_body('test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation', '''def test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation(seed):
    """旧门无视输入舍入强制4FF；E2以独立内联 Fraction 反平行边对为oracle，逐标签相等而非放松计数。
    原种子/尺度/平移全保留，精确G0三票不跳样本，tiny折点不再豁免。"""
    RECT = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1.0), (0.0, 1.0)]
    rng = random.Random(seed)
    s, tm = 1e-3, 1e3
    th, phi = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)
    c, sn = math.cos(th), math.sin(th)
    f = lambda P: [(s * (c * p[0] - sn * p[1]) + tm * math.cos(phi), s * (sn * p[0] + c * p[1]) + tm * math.sin(phi)) for p in P]
    A, B = f(SQUARE), f(RECT)
    eb = convex_entrance_block(A, B)
    expected = set()
    for i in range(4):
        ax, ay = (Fraction(A[(i + 1) % 4][k]) - Fraction(A[i][k]) for k in (0, 1))
        for j in range(4):
            bx, by = (Fraction(B[(j + 1) % 4][k]) - Fraction(B[j][k]) for k in (0, 1))
            if ax * by == ay * bx and ax * bx + ay * by < 0:
                expected.add(("FF", i, j))
    assert {l for l in eb.facets if l[0] == "FF"} == expected
    assert len(eb.facets) == 8 - len(expected)
    rep = g0_convex(A, B, samples=100, seed=1)
    assert rep.passed, (rep.mismatches[:2], rep.facet_symmetric_diff, rep.hull_vertex_mismatch)
    assert rep.band_skipped == rep.hull_vertex_ambiguous == 0
    assert rep.samples == 100 + rep.boundary_probes
''')

s = s.replace('半个容差：夹平即可', '半个旧容差：仍必须拒收')
s = s.replace('    assert len(convex_entrance_block(SQUARE, P2).facets) >= 4',
'''    with pytest.raises(ValueError, match="reflex"):
        convex_entrance_block(SQUARE, P2)''')
s = s.replace('深 50·t 的微凹必须拒收（阈值放宽 100 倍就会被当平直顶点吞掉）。',
'''旧门深50t拒收、半t接收；E2二者均精确拒收，t不再作为凸性豁免。
    保留两个原样本并收紧旧接受分支；精确平直可接受另由96格门守护。''')
replace_body('test_the_length_tolerance_is_the_slack_for_the_long_edge_rotation', '''def test_length_tolerance_never_changes_exact_parallel_merging(C):
    """旧门 δ=tol/2合并、2tol不并；E2非零精确叉积一律不并，tol只兼容参数。
    保留原两倾角，新增δ=0边界与tol=0/1e-7/1，要求标签与顶点都不依tol变化，三组几何产物必须互异。"""
    tol = 1e-7
    products = []
    for d, n_ff in ((0.0, 4), (0.5 * tol, 3), (2.0 * tol, 3)):
        big = [(C, C), (C + 1.0, C + d), (C + 1.0, C + 1.0), (C, C + 1.0)]
        ref = convex_entrance_block(SQUARE, big)
        for window in (0.0, tol, 1.0):
            got = convex_entrance_block(SQUARE, big, tol=window)
            assert got == ref
            assert sum(f[0] == "FF" for f in got.facets) == n_ff, (C, d, got.facets)
        products.append(tuple(ref.vertices))
    assert len(set(products)) == 3
''')
with p.open('w', encoding='utf-8', newline='') as f:
    f.write(s.replace('\n', nl))
