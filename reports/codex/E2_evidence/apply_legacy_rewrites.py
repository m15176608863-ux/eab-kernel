"""WO-E2 legacy-test rewrites, staged until the untouched baseline has ended."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def replace_span(path, start, end, new):
    p = ROOT / path
    with p.open(encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    a = text.index(start)
    b = text.index(end, a) if end else len(text)
    out = text[:a] + new.replace("\n", nl) + text[b:]
    with p.open("w", encoding="utf-8", newline="") as f:
        f.write(out)


REVIEW_R7 = '''def test_r7_third_vote_hull_vertices_match_and_catch_sign_flip(monkeypatch):
    """旧门把 outward_normal 反号，期望 G0 成员/凸包票红；E2 中法向只构造、不再决定成员。
    新门保留随机对三票和法向反号的构造量看护，并在实际 membership_exact 函数内部把边界吞成内部。
    强度：原来的法向错误仍被独立边法向公式识别；新成员门零容差、边界样本不跳过，明确要求 0→1 的目标断言红。
    oracle：法向用测试内联 hypot / 点乘；成员用 G0 的独立耳切-SAT，不调用 Minkowski 的几何原语。
    """
    import inspect
    import math
    import eab.kernel2d.covers as cv
    import eab.kernel2d.exact as ex

    rng = random.Random(11)
    A = random_convex_polygon(rng, 7)
    B = random_convex_polygon(rng, 6)
    rep = g0_convex(A, B, samples=300, seed=2)
    assert rep.passed and rep.hull_vertex_mismatch == 0

    # 原来的反法向缺陷现在只影响构造；以独立公式看护，不能要求精确谓词受它污染。
    x = (2.0, -3.0)
    expected = []
    for label in cv.convex_entrance_block(A, B).facets:
        kind, ai, bj = label
        assert kind in ("VE", "EV")       # 随机一般位置，无 FF
        P, k, sign = (B, bj, 1.0) if kind == "VE" else (A, ai, -1.0)
        u, v = P[k], P[(k + 1) % len(P)]
        dx, dy = v[0] - u[0], v[1] - u[1]
        h = math.hypot(dx, dy)
        nx, ny = sign * dy / h, -sign * dx / h
        px, py = B[bj][0] - A[ai][0], B[bj][1] - A[ai][1]
        want = nx * (x[0] - px) + ny * (x[1] - py)
        assert cv.facet_gap(A, B, label, x) == pytest.approx(want, abs=1e-14)
        expected.append((label, want))
    orig = cv.outward_normal
    with monkeypatch.context() as m:
        m.setattr(cv, "outward_normal", lambda poly, i: tuple(-v for v in orig(poly, i)))
        assert all(cv.facet_gap(A, B, lab, x) == pytest.approx(-want, abs=1e-14) for lab, want in expected)
        assert any(abs(cv.facet_gap(A, B, lab, x) - want) > 1.0 for lab, want in expected)

    # 牙穿过实际被测函数内部，不能在结果后追加伪造的失配。
    src = inspect.getsource(ex.membership_exact)
    assert "worst = min(worst, s)" in src
    namespace = dict(ex.__dict__)
    exec(src.replace("worst = min(worst, s)", "worst = 1"), namespace)
    monkeypatch.setattr(cv, "membership_exact", namespace["membership_exact"])
    bad = g0_convex(SQ, SQ, samples=20, seed=2)
    assert not bad.passed
    assert bad.mismatches and all(brute == 0 and cover == 1 for _, brute, cover in bad.mismatches)
    assert len(bad.mismatches) == bad.boundary_probes == 16


'''

REVIEW_DEPTH = '''@pytest.mark.parametrize("depth_over_t", [2.0, 0.5])
def test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start(depth_over_t):
    """旧门接受深度 0.5·tol 的微凹、拒绝 2·tol，并允许 2000 个样本在带内失配（最多 200 个）。
    E2 凸性对给定数据精确，两种非零凹深都必须拒收；同一批 2000 个平移和三个精确边界邻点交由通用成员路径。
    新断言更强：不再吞微凹、不跳过边界、每个答案对独立闭式 oracle 零错，且三种状态都必须实际出现。
    oracle 零共用：此顶边 V 口的两端高度为 1；|x_x|<1、x_y≈−1 时至少一个端点落在方块底边内部，
    因而相交状态恰为 sign(1+x_y)，只用 Fraction 加法/比较，不调用被测路径的耳切、SAT、法锥或凸包。
    """
    from fractions import Fraction
    import math
    from eab.kernel2d.covers import convex_entrance_block, membership_convex
    tol = 1e-9
    A = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0 - depth_over_t * tol), (0.0, 1.0)]
    for report_tol in (0.0, tol, 100.0 * tol):
        with pytest.raises(ValueError, match="reflex vertex"):
            convex_entrance_block(A, SQ, tol=report_tol)
    rng = random.Random(3)
    probes = [(rng.uniform(-0.9, 0.9), -1.0 + rng.uniform(-50.0, 50.0) * tol) for _ in range(2000)]
    probes += [(0.25, y) for y in (-1.0, math.nextafter(-1.0, -math.inf), math.nextafter(-1.0, math.inf))]
    states = set()
    for x in probes:
        height = Fraction(x[1]) + 1
        want = (height > 0) - (height < 0)
        got = membership_convex(A, SQ, x, 0.0)
        assert got == want, (depth_over_t, x, got, want)
        states.add(got)
    assert states == {-1, 0, 1}
'''

G0_PARALLEL = '''def test_degenerate_parallel_edges_membership_still_exact():
    """旧门在成员或暴力票为 0 时跳过；新门对同样 500 个样本加 8 个边界点逐一精确核对。
    oracle 用 Fraction 分离轴（convex_overlap_exact），不经 Minkowski 构造/角排序/成员 facet 路径；
    tol=0 消除报告带，要求三态都出现，因此强于原来的仅带外符号相符。
    """
    from eab.kernel2d.exact import convex_overlap_exact
    rng = random.Random(7)
    eb = convex_entrance_block(SQUARE, SQUARE, tol=1e-12)
    probes = [(rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5)) for _ in range(500)]
    probes += [(-1.0, -1.0), (-1.0, 1.0), (1.0, -1.0), (1.0, 1.0),
               (-1.0, 0.0), (1.0, 0.0), (0.0, -1.0), (0.0, 1.0)]
    states = set()
    for x in probes:
        m = membership_convex(SQUARE, SQUARE, x, 0.0, eb)
        b = convex_overlap_exact(SQUARE, SQUARE, x)
        assert m == b, (x, m, b)
        states.add(m)
    assert states == {-1, 0, 1}


'''

G0_KINK = '''def test_vote_three_keeps_exact_kinks_without_ambiguous_exemptions(C, Ls, d):
    """旧门允许短边微折点落在凸包弦距容差内时从票三两侧删掉（hull_vertex_ambiguous≤2）。
    E2 新口径：同一 24 格必须保留全部 5 个严格顶点，零说不清、零跳样；参数仍覆盖工程坐标/短边/小倾角。
    oracle：测试独立内联 Fraction 单调链，差点先精确相减，不调用 Minkowski、法锥或库凸包函数。
    新断言不更弱：原来的整门通过保留，另要求以前允许豁免的微折点也确实参与，并钉住全部边界探针计数。
    """
    from fractions import Fraction as F
    A = [(C, C), (C + 1.0, C), (C + 1.0, C + 1.0), (C, C + 1.0)]
    B = [(0.0, 0.0), (Ls, Ls * d), (Ls, Ls), (0.0, Ls)]
    pts = sorted({(F(b[0]) - F(a[0]), F(b[1]) - F(a[1])) for a in A for b in B})
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    hull = set(half(pts)[:-1] + half(list(reversed(pts)))[:-1])
    assert len(hull) == 5
    r = g0_convex(A, B, samples=400, seed=1)
    assert r.passed, (C, Ls, d, r.hull_vertex_mismatch, r.facet_symmetric_diff, r.mismatches[:2])
    assert r.hull_vertex_mismatch == r.hull_vertex_ambiguous == r.band_skipped == 0
    assert r.boundary_probes == 20 and r.samples == 420
    assert r.facet_local == r.facet_global == 2
'''

INVARIANCE = '''def _facet_set(A, B):
    return set(convex_entrance_block(A, B, (0.0, 0.0), 0.0).facets)


def _support_labels_exact(A, B):
    """独立 Fraction 支撑投影 oracle（本组输入无平直顶点）：不调库法锥/角序/凸包原语。
    B 边的外法向上，A 唯一最小顶点给 VE，两端同为最小的一条 A 边给 FF；交换得到 EV。
    同时返回所有严格支撑点的最小投影距离余量，以及是否存在精确平行边界。
    """
    FA = [(Fraction(x), Fraction(y)) for x, y in A]
    FB = [(Fraction(x), Fraction(y)) for x, y in B]
    labels, strict_margins, boundary = set(), [], False
    for P, Q, kind in ((FA, FB, "VE"), (FB, FA, "EV")):
        for j, q in enumerate(Q):
            q1 = Q[(j + 1) % len(Q)]
            nx, ny = q1[1] - q[1], q[0] - q1[0]
            projs = [nx * p[0] + ny * p[1] for p in P]
            lo = min(projs)
            mins = [i for i, v in enumerate(projs) if v == lo]
            if len(mins) == 1:
                i = mins[0]
                labels.add((kind, i, j) if kind == "VE" else (kind, j, i))
                gap = min(v - lo for v in projs if v > lo)
                strict_margins.append(float(gap) / math.hypot(float(nx), float(ny)))
            else:
                boundary = True
                assert len(mins) == 2
                i = next(i for i in mins if (i + 1) % len(P) in mins)
                labels.add(("FF", i, j) if kind == "VE" else ("FF", j, i))
    return labels, min(strict_margins, default=math.inf), boundary


def _sat_gap_exact(A, B, x):
    """独立内联 Fraction 分离轴最大有符号间隙（外正内负），仅作为带外不变性的舍入余量筛选。
    平移先 Fraction 相加；不调用被测 Minkowski/法锥/归并函数。
    """
    X = (Fraction(x[0]), Fraction(x[1]))
    FA = [(Fraction(a) + X[0], Fraction(b) + X[1]) for a, b in A]
    FB = [(Fraction(a), Fraction(b)) for a, b in B]
    gaps = []
    for P, Q in ((FA, FB), (FB, FA)):
        for j, p in enumerate(P):
            q = P[(j + 1) % len(P)]
            nx, ny = q[1] - p[1], p[0] - q[0]
            gap = min(nx * v[0] + ny * v[1] for v in Q) - nx * p[0] - ny * p[1]
            gaps.append(float(gap) / math.hypot(float(nx), float(ny)))
    return max(gaps)


@pytest.mark.parametrize("motion", MOTIONS, ids=MOTION_IDS)
@pytest.mark.parametrize("case", CONVEX_CASES, ids=[c[0] for c in CONVEX_CASES])
def test_convex_g0_is_invariant(case, motion):
    """旧门强迫理想平行对刚体运动后仍有原来的 FF 标签（由噪声窗吞微倾）。
    E2 新门先逐格对独立 Fraction 支撑投影 oracle 核对全部标签、对精确 SAT 核对每个成员答案，
    再在支撑投影/成员间隙余量超过坐标舍入界时守不变；精确平行/相触属于数据边界，允许随舍入改变但绝不跳过 oracle。
    强度：旧带内标签同一性换成每格零错，原来带外不变仍保留；G0 三票还钉住零跳样、零顶点豁免、全部边界探针。
    oracle 与被测零共用：投影和 SAT 不经 Minkowski 极角归并/法锥，投影辅助函数全在测试内独立实现。
    """
    from eab.kernel2d.covers import membership_convex
    from eab.kernel2d.exact import convex_overlap_exact
    name, A, B = case
    _, theta, s, tm = motion
    ref = g0_convex(A, B, samples=300, seed=3)
    assert ref.passed, name
    pt, vec, poly = _T(theta, s, tm)
    At, Bt = poly(A), poly(B)
    ref_labels, margin, has_boundary = _support_labels_exact(A, B)
    want, _, _ = _support_labels_exact(At, Bt)
    assert _facet_set(A, B) == ref_labels
    assert _facet_set(At, Bt) == want, (name, motion[0], _facet_set(At, Bt) ^ want)
    # 16 个舍入预算覆盖两端坐标、旋转、点积、参考平移传播；纯相对，无绝对地板。
    noise = 16.0 * _floor_in_reference_units(A, B, motion)
    if not has_boundary and margin > noise:
        assert want == ref_labels, (name, motion[0])
    rep = g0_convex(At, Bt, samples=300, seed=3)
    assert rep.passed, (name, rep.mismatches[:2], rep.facet_symmetric_diff, rep.hull_vertex_mismatch)
    assert rep.band_skipped == rep.hull_vertex_ambiguous == 0
    assert rep.boundary_probes == 4 * len(want)
    assert rep.samples == 300 + rep.boundary_probes
    assert rep.facet_local == rep.facet_global == sum(lab[0] != "FF" for lab in want)
    probes = [(0.0, 0.0), (0.4, 0.25), (1.0, 0.0), (1.0, 1.0), (3.0, 2.0), (-3.0, -2.0)]
    stable = 0
    for x in probes:
        truth = convex_overlap_exact(A, B, x)
        moved = convex_overlap_exact(At, Bt, vec(x))
        assert membership_convex(A, B, x, 0.0) == truth
        assert membership_convex(At, Bt, vec(x), 0.0) == moved
        if abs(_sat_gap_exact(A, B, x)) > noise:
            assert moved == truth, (name, motion[0], x, truth, moved)
            stable += 1
    assert stable >= 2       # 不变性分支必须真正执行，不因全落边界而空过。


'''


if __name__ == "__main__":
    import sys
    if sys.argv[1:] != ["--apply"]:
        raise SystemExit("Pass --apply only after the unchanged full baseline has ended.")
    replace_span("tests/test_kernel2d_review.py", "def test_r7_third_vote", "def test_gap0_sign", REVIEW_R7)
    replace_span("tests/test_kernel2d_review.py", '@pytest.mark.parametrize("depth_over_t,accepted"', None, REVIEW_DEPTH)
    replace_span("tests/test_kernel2d_g0.py", "def test_degenerate_parallel_edges_membership_still_exact", "def test_gate_has_teeth_wrong_orientation", G0_PARALLEL)
    replace_span("tests/test_kernel2d_g0.py", "def test_vote_three_treats_kinks", None, G0_KINK)
    replace_span("tests/test_invariance_2d.py", "def _facet_set(A, B):", "# ---------------------------------------------------------------- 凸性 / 反射顶点", INVARIANCE)
    replace_span("tests/test_invariance_2d.py", "  · 凸块 G0：", "  · 凸性 / 反射顶点", "  · 凸块 G0（E2）：每格成员/标签对独立精确 oracle 零错；只在判定余量超过舍入界时要求刚体不变，边界数据变化不豁免 oracle；\n")
    print("Applied E2 exact-semantics rewrites to three test files.")
