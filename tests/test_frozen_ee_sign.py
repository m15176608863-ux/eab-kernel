"""冻结 EE 朝向与精确棱内判定（G6 第五轮输入，WO-E5a 契约更新）。

保留全部原运动/工程坐标格子，但分支答案针对运动后给定的二进制数据：
法锥用独立 Fraction 循环 Newell/Gram oracle，交点参数用独立 Fraction Gram 解；
不把舍入输入通过噪声带伪装成理想刚体运动。一般面环盖与凸包 facet 各自完整
对账，不混用二者的几何/编号。距离误差限只约束浮点构造，不参与任何分支。
冻结路径仅适配 primal EE；Dual 正常非退化值/导数另有一致门，微交叉留 WO-E5b。
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel3d.covers3 import ee_cover, facet_normal3, local_facets3  # noqa: E402
from eab.kernel3d.frozen import ee_normal_generic, frozen_ee_sign  # noqa: E402
from eab.kernel3d.geom3 import Polyhedron, box, dot, exact_convex_view  # noqa: E402
from eab.margin import body_distance, contact_resolution, inflated_membership, margin_gap_from_frozen_cover, OUTSIDE  # noqa: E402
import e5a_cover_oracle as independent  # noqa: E402
import e5b_frozen_oracle as surface_oracle  # noqa: E402


def _ee_exact(A, ea, B, eb, tol=1e-9):
    """Independent cyclic-Newell/Gram oracle; no production geometric primitive."""
    a, b = independent._model(A), independent._model(B)
    u = independent.sub(a[0][ea[1]], a[0][ea[0]])
    v = independent.sub(b[0][eb[1]], b[0][eb[0]])
    uu, uv, vv = independent.dot(u,u), independent.dot(u,v), independent.dot(v,v)
    determinant = uu*vv-uv*uv
    if determinant == 0:
        return None
    w = independent.sub(b[0][eb[0]], a[0][ea[0]])
    uw, vw = independent.dot(u,w), independent.dot(v,w)
    s, t = (vv*uw-uv*vw)/determinant, (uv*uw-uu*vw)/determinant
    n = independent.cross(v,u)
    for direction in (n, independent.scale(n,-1)):
        sb = independent.arc(b,eb,direction,tol)
        sa = independent.arc(a,ea,independent.scale(direction,-1),tol)
        if sa >= 0 and sb >= 0:
            scaled = [float(c/max(map(abs,direction))) for c in direction]
            length = math.hypot(*scaled)
            unit = tuple(c/length for c in scaled)
            return unit,(s,t),sa == sb == 1,0 <= s <= 1 and 0 <= t <= 1
    return None


def _line_parameters_and_gap(A,ea,B,eb):
    """Gram line solve independent of whether either local normal arc accepts."""
    a,b=independent.q(A.verts[ea[0]]),independent.q(B.verts[eb[0]])
    u=independent.sub(independent.q(A.verts[ea[1]]),a)
    v=independent.sub(independent.q(B.verts[eb[1]]),b)
    w=independent.sub(b,a)
    uu,uv,vv=independent.dot(u,u),independent.dot(u,v),independent.dot(v,v)
    uw,vw=independent.dot(u,w),independent.dot(v,w)
    den=uu*vv-uv*uv
    assert den > 0
    params=((vv*uw-uv*vw)/den,(uv*uw-uu*vw)/den)
    n=independent.cross(v,u)
    scaled=[float(x/max(map(abs,n))) for x in n]
    unit=[x/math.hypot(*scaled) for x in scaled]
    gap=sum(unit[i]*float(a[i]-b[i]) for i in range(3))
    return params,gap


def _check_ee_exact(A, ea, B, eb, tol=1e-9):
    truth = _ee_exact(A,ea,B,eb,tol)
    got = ee_cover(A,ea,B,eb,tol)
    assert (got is not None) == (truth is not None), (ea,eb,truth,got)
    if truth is not None:
        normal,params,strict,inside = truth
        assert got.params == tuple(map(float,params)), (ea,eb,got.params,params)
        assert got.strict == strict and got.in_extent == inside, (ea,eb,params)
        assert sum(x*y for x,y in zip(got.normal,normal)) > 1-1e-12
    return got,truth


def _rot_z(th):
    c, s = math.cos(th), math.sin(th)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def _rot3(seed):
    rng = random.Random(seed)
    q = [rng.gauss(0, 1) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _app(R, v):
    return tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))


def _xf(P, R, t, s=1.0):
    return Polyhedron([tuple(a + b for a, b in zip(_app(R, tuple(s * c for c in p)), t)) for p in P.verts], list(P.faces))


def _stack(yaw, gap, seed, t, s=1.0):
    """偏航 yaw 的单位方块叠在单位方块上方 gap，整对做种子 seed 的一般旋转、按 s 缩放、平移到 |t|（方向 (0.6, −0.48, 0.64)）。"""
    tv = (t * 0.6, -t * 0.48, t * 0.64)
    top = _xf(box(center=(0.0, 0.0, 1.0 + gap), half=(0.5, 0.5, 0.5)), _rot_z(yaw), (0.0, 0.0, 0.0))
    A = _xf(top, _rot3(seed), tv, s)
    B = _xf(box(half=(0.5, 0.5, 0.5)), _rot3(seed), tv, s)
    return A, B


GRID = [(yaw, gap, seed, t) for yaw in (1e-4, 1e-5) for gap in (1e-3, 1e-6) for seed in (4, 6, 9) for t in (0.0, 1e3, 1e5, 1e6)]


@pytest.mark.parametrize("yaw,gap,seed,t", GRID)
def test_frozen_gap_on_the_label_body_distance_chose_is_the_distance(yaw, gap, seed, t):
    """文档工作流：body_distance 选标签 → frozen_ee_sign 定朝向 → margin_gap_from_frozen_cover。分离的一对，冻结间隙必须是 +d
    （修前 96 个 EE 位形里 19 个给 −d：分离判成闭合），δ = 0.5d 时冻结间隙 0.5d 且 inflated_membership 答 OUTSIDE。"""
    A, B = _stack(yaw, gap, seed, t)
    d, lab = body_distance(A, B)
    if lab[0] != "EE":
        pytest.skip(f"nearest label is {lab[0]}, not EE")
    ea, eb = (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])
    sgn = frozen_ee_sign(A, B, ea, eb)
    tol = 1e-9 * max(1.0, d) + 4096 * 2.220446049250313e-16 * max(1.0, t)
    g = margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), 0.0, ee_sign=sgn)
    assert abs(g - d) <= tol, (d, g, sgn)
    g5 = margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), 0.5 * d, ee_sign=sgn)
    assert abs(g5 - 0.5 * d) <= tol, (d, g5)
    assert inflated_membership(A, B, delta=0.5 * d) == OUTSIDE


@pytest.mark.parametrize("yaw,seed,t", [(y, sd, t) for y in (1e-3, 1e-5) for sd in (4, 6) for t in (0.0, 1e3, 1e6)])
def test_frozen_ee_orientation_agrees_with_ee_cover_and_facet_normal3_on_every_ee_pair(yaw, seed, t):
    """原面环的通用盖与凸包的严格 facet 分别核独立 oracle，不混用两套编号/几何。"""
    A, B = _stack(yaw, 1e-3, seed, t)
    n_cov = 0
    for ea in A.edges():
        for eb in B.edges():
            cov,truth = _check_ee_exact(A,ea,B,eb)
            if cov is None:
                continue
            n_cov += 1
            nf = ee_normal_generic(A, ea, B, eb, frozen_ee_sign(A, B, ea, eb))
            assert dot(cov.normal, nf) > 0.5, (ea, eb, cov.normal, nf)
            assert sum(x*y for x,y in zip(nf,truth[0])) > 0.5
    assert n_cov >= 8
    # facet_normal3 is defined on canonical convex views and strict local labels.
    # Check that complete label set as well, rather than deleting the facet gate.
    from e5a_convex_oracle import canonical_view, assert_raw_coordinate_view
    expected_a=canonical_view(tuple(A.verts),tuple(A.faces))
    expected_b=canonical_view(tuple(B.verts),tuple(B.faces))
    ca,cb=exact_convex_view(A),exact_convex_view(B)
    assert_raw_coordinate_view(ca,expected_a)
    assert_raw_coordinate_view(cb,expected_b)
    def oracle_edges(view):
        return sorted({tuple(sorted((i,j))) for face in view.faces for i,j in zip(face,face[1:]+face[:1])})
    expected=set()
    for ea in oracle_edges(expected_a):
        for eb in oracle_edges(expected_b):
            truth=_ee_exact(expected_a,ea,expected_b,eb,0.0)
            if truth is not None and truth[2]:
                lab=("EE",("edge",*ea),("edge",*eb))
                expected.add(lab)
                assert sum(x*y for x,y in zip(facet_normal3(ca,cb,lab),truth[0])) > 1-1e-12
    assert {lab for lab in local_facets3(ca,cb) if lab[0]=='EE'} == expected
    assert expected


@pytest.mark.parametrize("seed", (4, 6))
@pytest.mark.parametrize("t,s", [(1e5, 1e-3), (1e6, 1e-2), (1e3, 1.0)])
def test_near_parallel_crossing_edges_stay_in_extent_in_engineering_coordinates(seed, t, s):
    """全部原运动格逐对核精确 Gram 参数/在程；舍入后的数据不被噪声带伪装成理想八重并列。"""
    A0, B0 = _stack(1e-5, 0.06, seed, 0.0)
    A, B = _stack(1e-5, 0.06, seed, t, s)
    near,expected_near,actual_near = [],set(),set()
    for ea in A.edges():
        for eb in B.edges():
            c0,truth0 = _check_ee_exact(A0,ea,B0,eb)
            c,truth = _check_ee_exact(A,ea,B,eb)
            if truth is not None and truth[3]:
                expected_near.add((ea,eb))
            if c is not None and c.in_extent:
                actual_near.add((ea,eb))
            if c0 is not None and c0.in_extent and abs(c0.gap-0.06) <= 1e-9:
                near.append((ea,eb))
                if c is not None:
                    assert abs(c.gap-0.06*s) <= 1e-9*s+4096*2.220446049250313e-16*t
    assert actual_near == expected_near and near
    # A rounded input can legitimately choose a different label. It must still
    # choose an independently valid in-extent label, with the physical gap and
    # frozen signed distance checked on both original and transformed inputs.
    for P,Q,scale,offset in ((A0,B0,1.0,0.0),(A,B,s,t)):
        distance,label=body_distance(P,Q,contact_window=contact_resolution(P,Q))
        assert label in {lab for lab,_ in independent.cover_labels(P,Q)}
        assert abs(distance-.06*scale) <= 1e-9*scale+4096*2.220446049250313e-16*offset
        sign=frozen_ee_sign(P,Q,label[1][1:],label[2][1:]) if label[0]=='EE' else 1.0
        frozen=margin_gap_from_frozen_cover(P,Q,label,(0.,0.,0.),0.,ee_sign=sign)
        assert abs(frozen-distance) <= 1e-9*scale+4096*2.220446049250313e-16*offset

        # Default exact surface mode has a different oracle domain: a rounded
        # nonplanar ring is ear-cut, including its real diagonal edges.  The
        # independent ear cut/Gram distance oracle imports no production
        # predicate, normal, triangulation, hull, or distance routine.
        from eab.margin import _witnesses
        oracle_labels = surface_oracle.cover_labels(P,Q)
        actual_labels = {(c.label(),c.strict) for c,_,_ in _witnesses(P,Q,1e-9,exact_surface=True)}
        assert actual_labels == oracle_labels, 'complete exact-surface cover set'
        exact_distance,exact_label=body_distance(P,Q)
        distance_squared=surface_oracle.distance_squared(P,Q)
        oracle_distance=math.sqrt(float(distance_squared))
        assert exact_label in {lab for lab,_ in oracle_labels}, 'exact-surface chosen label'
        assert abs(exact_distance-oracle_distance) <= 4*math.ulp(oracle_distance), 'independent exact surface distance'
        exact_sign=frozen_ee_sign(P,Q,exact_label[1][1:],exact_label[2][1:]) if exact_label[0]=='EE' else 1.0
        exact_frozen=margin_gap_from_frozen_cover(P,Q,exact_label,(0.,0.,0.),0.,ee_sign=exact_sign)
        assert abs(exact_frozen-oracle_distance) <= 8*math.ulp(oracle_distance), 'exact-surface frozen signed distance'
        if exact_label[0]=='EE':
            surface_p,_=surface_oracle.surface(P)
            surface_q,_=surface_oracle.surface(Q)
            ea,eb=exact_label[1][1:],exact_label[2][1:]
            truth=_ee_exact(surface_p,ea,surface_q,eb)
            assert truth is not None and truth[3], 'independent diagonal EE extent'
            frozen_normal=ee_normal_generic(P,ea,Q,eb,exact_sign)
            assert sum(x*y for x,y in zip(frozen_normal,truth[0])) > 1-1e-12, 'independent exact-surface EE orientation'



def test_exact_surface_cover_gate_kills_internal_source_ring_only_mutation(monkeypatch):
    """The full label-set gate sees a real internal triangulation-branch loss."""
    import inspect
    import eab.margin as margin
    source=inspect.getsource(margin._witnesses)
    assert source.count('if exact_surface:') == 2
    namespace=dict(vars(margin))
    exec(compile(source.replace('if exact_surface:', 'if False:'),
                 '<mutant: folded surface expansion removed>', 'exec'),namespace)
    monkeypatch.setattr(margin,'_witnesses',namespace['_witnesses'])
    with pytest.raises(AssertionError,match='complete exact-surface cover set'):
        test_near_parallel_crossing_edges_stay_in_extent_in_engineering_coordinates(4,1e5,1e-3)


def test_unrounded_yaw_stack_retains_the_analytic_eight_crossing_edge_pairs():
    a=_xf(box(center=(0.,0.,1.06),half=(.5,.5,.5)),_rot_z(1e-5),(0.,0.,0.))
    b=box(half=(.5,.5,.5))
    near=[]
    for ea in a.edges():
        for eb in b.edges():
            c,_=_check_ee_exact(a,ea,b,eb)
            if c is not None and c.in_extent and abs(c.gap-.06)<1e-12:
                near.append((ea,eb))
    assert len(near)==8


@pytest.mark.parametrize('yaw,seed',[(.2,4),(.2,6),(.7,4),(.7,6)])
def test_frozen_primal_adapter_matches_the_unchanged_dual_formula_off_degeneracy(yaw,seed):
    """Ordinary nonparallel cases retain both primal value and a live derivative."""
    from eab.dual import Dual
    a,b=_stack(yaw,.06,seed,0.)
    ea,eb=(0,1),(4,5)
    sign=frozen_ee_sign(a,b,ea,eb)
    value=ee_normal_generic(a,ea,b,eb,sign)
    va=[[Dual.const(c,1) for c in p] for p in a.verts]
    vb=[[Dual.const(c,1) for c in p] for p in b.verts]
    va[0][0]=Dual.seed(a.verts[0][0],1,0)
    da,db=Polyhedron([tuple(p) for p in va],a.faces),Polyhedron([tuple(p) for p in vb],b.faces)
    actual=ee_normal_generic(da,ea,db,eb,sign)
    assert [v.v for v in actual] == pytest.approx(value,abs=1e-13,rel=1e-13)
    h=1e-6
    probes=[]
    for step in (-h,h):
        vertices=list(a.verts)
        vertices[0]=(vertices[0][0]+step,*vertices[0][1:])
        probes.append(ee_normal_generic(Polyhedron(vertices,a.faces),ea,b,eb,sign))
    derivative=[(v-u)/(2*h) for u,v in zip(*probes)]
    assert [v.e[0] for v in actual] == pytest.approx(derivative,abs=1e-7,rel=1e-7)
    assert max(abs(v.e[0]) for v in actual) > .01


def _corner_pair(yaw, gap, x0=0.3):
    """单位方块 A 的角点 (x0, −0.5) 绕过该点的竖轴偏航 yaw，坐在单位方块 B 上方 gap：A 的底棱 (0, 1) 与 B 的顶棱 (4, 5)
    夹角 yaw、交点恰在 A 棱的端点（s = 1）、B 棱的 0.8 处——近平行、相触（gap = 0）、端点上的边界态。"""
    top = box(center=(x0 - 0.5, 0.0, 1.0 + gap), half=(0.5, 0.5, 0.5))
    c, s = math.cos(yaw), math.sin(yaw)
    V = [(x0 + c * (x - x0) - s * (y + 0.5), -0.5 + s * (x - x0) + c * (y + 0.5), z) for x, y, z in top.verts]
    return Polyhedron(V, list(top.faces)), box(half=(0.5, 0.5, 0.5))


@pytest.mark.parametrize("seed", (4, 6, 9, 11, 13, 17))
@pytest.mark.parametrize("t,s", [(1e4, 1e-3), (1e5, 1e-3), (1e6, 1e-2)])
def test_touching_near_parallel_edges_crossing_at_an_endpoint_stay_in_extent(seed, t, s):
    """原端点闭式条件保留；全部舍入运动格按独立精确参数分类，不以噪声窗口改成在程。"""
    A0, B0 = _corner_pair(1e-5, 0.0)
    c0,truth0 = _check_ee_exact(A0,(0,1),B0,(4,5))
    assert c0 is not None and c0.in_extent and abs(c0.gap) < 1e-12
    assert abs(c0.params[0] - 1.0) < 1e-9 and abs(c0.params[1] - 0.8) < 1e-9
    tv = (t * 0.6, -t * 0.48, t * 0.64)
    A, B = _xf(A0, _rot3(seed), tv, s), _xf(B0, _rot3(seed), tv, s)
    c,truth = _check_ee_exact(A,(0,1),B,(4,5))
    params,gap=_line_parameters_and_gap(A,(0,1),B,(4,5))
    assert abs(gap) <= 4096 * 2.220446049250313e-16 * t
    if c is not None:
        assert c.in_extent == (0 <= params[0] <= 1 and 0 <= params[1] <= 1)
        assert c.params == tuple(map(float,params))
        assert abs(c.gap) <= 4096 * 2.220446049250313e-16 * t
    else:
        # This is an exact arc rejection, not an exemption from the extent gate.
        assert truth is None


# ---------------------------------------------------------------- 第五轮另两路审查者的 critical 位形（同一缺陷，换了几何）

sys.path.insert(0, str(ROOT / "tests"))


def _ridge_pair(theta, g, y0=0.5):
    """四面体的水平脊棱悬在方块顶角上方 g，与一条顶棱近平行（夹角 θ）、与另一条交叉。"""
    from eab.kernel3d.geom3 import tetra
    B = box(half=(1.0, 1.0, 1.0))
    c, s = math.cos(theta), math.sin(theta)
    at = lambda u: (1.0 - u * s, y0 + u * c, 1.0 + g)                  # noqa: E731
    P0, P1 = at(-1.5), at(1.5 / c)
    mid = at(0.5 * (-1.5 + 1.5 / c))
    perp = (c, s, 0.0)
    Q0 = (mid[0] + 0.5 * perp[0], mid[1] + 0.5 * perp[1], mid[2] + 1.0)
    Q1 = (mid[0] - 0.5 * perp[0], mid[1] - 0.5 * perp[1], mid[2] + 1.0)
    return tetra(P0, P1, Q0, Q1), B


def _wedge_pair(k, g=0.1):
    """楔形（凸包）的底棱悬在方块上方 g、与方块顶棱夹角 2^-k·1.5 量级，镜像后编号让 EE 成为 body_distance 的标签。"""
    from eab.kernel3d.geom3 import convex_hull_3d
    d = 2.0 ** -k
    p0 = (-1.5, -1 - 1.5 * d, 0.5 + g)
    p1 = (1.5, -1 + 1.5 * d, 0.5 + g)
    u = (-d * 0.3, 0.3, 0.0)
    pts = [p0, p1] + [(p[0] + sg * u[0], p[1] + sg * u[1], p[2] + 1.0) for p in (p0, p1) for sg in (1, -1)]
    mirror = lambda P: Polyhedron([(-v[0], v[1], v[2]) for v in P.verts], [tuple(reversed(f)) for f in P.faces])  # noqa: E731
    return mirror(convex_hull_3d(pts)), mirror(box(half=(1.0, 1.0, 0.5)))


def _frozen_gap_of_chosen_label(A, B):
    d, lab = body_distance(A, B)
    sgn = frozen_ee_sign(A, B, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])) if lab[0] == "EE" else 1.0
    return d, lab, float(margin_gap_from_frozen_cover(A, B, lab, (0.0, 0.0, 0.0), 0.0, ee_sign=sgn))


@pytest.mark.parametrize("theta", (1e-3, 1e-4))
@pytest.mark.parametrize("t", (1e3, 1e5, 1e6))
def test_frozen_gap_on_a_ridge_nearly_parallel_to_a_top_edge(theta, t):
    """审查者位形一：脊棱与顶棱近平行（θ = 1e-3 / 1e-4），20 个姿态 × 工程坐标；修前 θ = 1e-4、|t| = 1e5 时 8/20 给 −d。"""
    from test_invariance_geom import Motion
    for r in range(1, 21):
        M = Motion(r, t, 1.0)
        A, B = (M.poly(P) for P in _ridge_pair(theta, 0.01))
        d, lab, g = _frozen_gap_of_chosen_label(A, B)
        assert abs(g - d) <= 1e-6, (r, lab, d, g)


@pytest.mark.parametrize("rot,t", [(7, 1e6), (10, 1e5), (15, 1e5)])
def test_frozen_gap_on_a_nearly_parallel_wedge(rot, t):
    """审查者位形二：楔形底棱与顶棱近平行（2^-10），修前三格都给 −0.1。"""
    from test_invariance_geom import Motion
    A0, B0 = _wedge_pair(10)
    M = Motion(rot, t, 1.0)
    d, lab, g = _frozen_gap_of_chosen_label(M.poly(A0), M.poly(B0))
    assert lab[0] == "EE" and abs(d - 0.1) <= 1e-9 and abs(g - d) <= 1e-9, (lab, d, g)
