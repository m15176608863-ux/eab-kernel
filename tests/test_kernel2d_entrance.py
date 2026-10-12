"""二维首入（命题 7 的二维版，按运动方向定义）的门：闭式（凸对的 H 表示）、凹块对不经盖的 oracle、随机凸对、刚体运动不变（纪律 F）、
最短出口、以及 bb52 真几何上的 legacy 对账（每条 legacy 顶点-边接触都能作为沿该边法向逼近的首入被引擎选中）。"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

from eab.kernel2d.covers import ve_cover
from eab.kernel2d.entrance import first_entrance, first_entrance_brute, shortest_exit
from eab.kernel2d.geom import outward_normal, polygons_overlap, translate

ROOT = Path(__file__).resolve().parents[1]
SQ = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
SLAB = [(-2.0, -1.0), (2.0, -1.0), (2.0, 0.0), (-2.0, 0.0)]            # 顶边 y = 0


def _rot(P, th, T=(0.0, 0.0)):
    c, s = math.cos(th), math.sin(th)
    return [(T[0] + c * x - s * y, T[1] + s * x + c * y) for x, y in P]


def _rotv(v, th):
    c, s = math.cos(th), math.sin(th)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])


# ---------------------------------------------------------------- 闭式

@pytest.mark.parametrize("speed", [1.0, 0.5, 3.0])
def test_square_dropping_onto_a_slab_is_a_parallel_edge_entrance(speed):
    """单位方块（底边 y = 0.3）沿 −y 落到板上：t* = 0.3/speed，法向 +y，facet 是平行边 FF（两条边里长的那条的法向）。"""
    A = translate(SQ, (0.2, 0.3))
    e = first_entrance(A, SLAB, (0.0, 0.0), (0.0, -speed))
    assert e.kind == "entrance" and e.t == pytest.approx(0.3 / speed, abs=1e-12), (e.kind, e.t, e.label)
    assert e.normal == pytest.approx((0.0, 1.0), abs=1e-12) and e.label[0] == "FF", e.label
    assert e.point_b[1] == pytest.approx(0.0, abs=1e-12) and abs(e.gap) <= 1e-12
    bt = first_entrance_brute(A, SLAB, (0.0, 0.0), (0.0, -speed), t_max=2.0 / speed)
    assert bt == pytest.approx(e.t, abs=1e-9)


def test_rotated_square_lands_on_its_lowest_corner():
    """方块转 0.3 rad 再落：最低的顶点先着地（VE：A 的顶点对板的顶边），t* = (最低点 y − 0)/|d_y|。"""
    A = _rot(SQ, 0.3, (0.1, 0.5))
    ymin = min(p[1] for p in A)
    d = (0.1, -1.0)
    e = first_entrance(A, SLAB, (0.0, 0.0), d)
    assert e.kind == "entrance" and e.t == pytest.approx(ymin / 1.0, abs=1e-12)
    assert e.label[0] == "VE" and e.normal == pytest.approx((0.0, 1.0), abs=1e-12), e.label
    assert e.point_a[1] == pytest.approx(0.0, abs=1e-12)
    assert first_entrance_brute(A, SLAB, (0.0, 0.0), d, t_max=2.0) == pytest.approx(e.t, abs=1e-9)


def test_corner_onto_corner_is_a_set_valued_point():
    """方块的左下角正落到板的右上角上：VE（A 顶点, 板顶边）与 EV（A 底边, 板顶点）同时被触及——并列集两条，代表按枚举序。"""
    A = translate(SQ, (2.0, 0.4))
    e = first_entrance(A, SLAB, (0.0, 0.0), (0.0, -1.0))
    assert e.kind == "entrance" and e.t == pytest.approx(0.4, abs=1e-12)
    kinds = {lab[0] for lab in e.tied_labels}
    assert {"VE", "EV"} <= kinds or "FF" in kinds, e.tied_labels


def test_ray_that_misses_or_stops_short_gives_none():
    A = translate(SQ, (0.2, 0.3))
    assert first_entrance(A, SLAB, (0.0, 0.0), (0.0, 1.0)).kind == "none"
    assert first_entrance(A, SLAB, (0.0, 0.0), (0.0, -1.0), t_max=0.2).kind == "none"
    assert first_entrance(A, SLAB, (0.0, 0.0), (0.0, -1.0), t_max=0.3).kind == "entrance"
    assert first_entrance(translate(SQ, (5.0, 0.3)), SLAB, (0.0, 0.0), (0.0, -1.0)).kind == "none"   # 落在板外


# ---------------------------------------------------------------- 已侵入：最短出口

def test_penetrating_start_takes_the_shallowest_exit():
    A = translate(SQ, (0.2, -0.1))                        # 压进板 0.1
    e = first_entrance(A, SLAB, (0.0, 0.0), (1.0, 0.0))
    assert e.kind == "exit" and e.normal == pytest.approx((0.0, 1.0), abs=1e-12) and e.gap == pytest.approx(-0.1, abs=1e-12)
    assert polygons_overlap(translate(A, (0.0, 0.1)), SLAB) <= 0 and polygons_overlap(translate(A, (0.0, 0.05)), SLAB) == 1
    assert shortest_exit(A, SLAB, (0.0, 0.0)).label == e.label


# ---------------------------------------------------------------- 凹块：L 形台阶

STEP = [(0.0, 0.0), (2.0, 0.0), (2.0, 0.5), (1.0, 0.5), (1.0, 1.0), (0.0, 1.0)]     # 下踏面 y=0.5 (x∈[1,2])，竖板 x=1，上踏面 y=1


def test_square_sliding_into_a_concave_step_first_touches_the_riser():
    """方块从右上方沿 (−1, −0.5) 滑入：前缘左下角 (1.4, 0.9) 在 t = 0.4 到达竖板 x = 1（y = 0.7 ∈ [0.5, 1]）。
    凹体没有全局 E，候选来自局部盖、谓词裁决；首入 facet 是 A 的左边对竖板（FF 平行边：两个顶点-边盖的退化族，这里报 VE/FF 之一）。"""
    A = translate(SQ, (1.4, 0.9))
    d = (-1.0, -0.5)
    e = first_entrance(A, STEP, (0.0, 0.0), d, t_max=3.0)
    assert e.kind == "entrance" and e.t == pytest.approx(0.4, abs=1e-12), (e.kind, e.t, e.label)
    assert e.normal == pytest.approx((1.0, 0.0), abs=1e-12), e.normal
    bt = first_entrance_brute(A, STEP, (0.0, 0.0), d, t_max=3.0, steps=600)
    assert bt == pytest.approx(e.t, abs=1e-9)


def test_missed_candidate_on_the_concave_step_is_detected(monkeypatch):
    """把 B 侧特征落在竖板 x = 1 上的盖全部从枚举里删掉：剩下最早的在程候选是上踏面（t = 1.8），但那时两体早已相交——必须抛错。"""
    import eab.kernel2d.entrance as E
    A = translate(SQ, (1.4, 0.9))
    real = E.enumerate_covers

    def on_riser(c, B):
        if c.kind == "VE":
            b0, b1 = B[c.b_index], B[(c.b_index + 1) % len(B)]
            return abs(b0[0] - 1.0) < 1e-12 and abs(b1[0] - 1.0) < 1e-12
        if c.kind == "EV":
            return abs(B[c.b_index][0] - 1.0) < 1e-12
        return False

    def dropped(At, B, **kw):
        return [c for c in real(At, B, **kw) if not on_riser(c, B)]
    monkeypatch.setattr(E, "enumerate_covers", dropped)
    with pytest.raises(RuntimeError, match="missed an earlier entrance"):
        first_entrance(A, STEP, (0.0, 0.0), (-1.0, -0.5), t_max=3.0)


# ---------------------------------------------------------------- 随机凸对 × 随机射线：对不经盖的 oracle

def _random_convex(rng, n=7, scale=1.0, center=(0.0, 0.0)):
    from eab.kernel2d.geom import convex_hull
    pts = [(center[0] + scale * rng.uniform(-1, 1), center[1] + scale * rng.uniform(-1, 1)) for _ in range(n)]
    return convex_hull(pts)


@pytest.mark.parametrize("seed", range(30))
def test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs(seed):
    rng = random.Random(700 + seed)
    A = _random_convex(rng)
    B = _random_convex(rng, center=(3.0 * rng.uniform(0.7, 1.3), 0.3 * rng.uniform(-1, 1)))
    x0 = (rng.uniform(-0.5, 0.5) - 3.0, rng.uniform(-0.5, 0.5) + 2.5)
    d = (3.0 - x0[0] + 0.3 * rng.gauss(0, 1), -x0[1] + 0.3 * rng.gauss(0, 1))
    e = first_entrance(A, B, x0, d, t_max=4.0)
    bt = first_entrance_brute(A, B, x0, d, t_max=4.0, steps=800)
    from r13_event_oracle import assert_event_binding, convex_ray_interval_2d
    interval = convex_ray_interval_2d(A, B, x0, d, 4)
    if bt is None:
        assert interval is None
        assert e.kind == "none", (e.kind, e.t, e.label)
        return
    assert e.kind == "entrance", (bt, e.kind)
    assert e.t == pytest.approx(bt, abs=5e-9), (e.t, bt, e.label)
    from fractions import Fraction as F
    assert e.t_exact is not None
    assert interval is not None
    assert_event_binding(e.t, e.t_exact, e.x, x0, d, interval[0])
    exact_x=tuple(F(x0[i])+e.t_exact*F(d[i]) for i in range(2))
    assert _independent_overlap(A,B,exact_x)==0
    rounded=translate(A,e.x)
    assert polygons_overlap(rounded,B)==_independent_overlap(rounded,B)
    assert abs(e.gap) <= 1e-9
    assert e.normal[0] * d[0] + e.normal[1] * d[1] < 0.0


# ---------------------------------------------------------------- 纪律 F：刚体运动不变

@pytest.mark.parametrize("th,tmag", [(0.0, 1e3), (0.7, 0.0), (0.7, 1e3), (2.1, 1e5), (4.0, 1e6)])
def test_first_entrance_is_invariant_under_rigid_motion(th, tmag):
    A0 = _rot(SQ, 0.3, (0.1, 0.5))
    d0 = (0.1, -1.0)
    e0 = first_entrance(A0, SLAB, (0.0, 0.0), d0)
    T = (0.6 * tmag, -0.8 * tmag)
    A, B = _rot(A0, th, T), _rot(SLAB, th, T)
    d = _rotv(d0, th)
    e = first_entrance(A, B, (0.0, 0.0), d)
    assert e.kind == e0.kind == "entrance"
    assert abs(e.t - e0.t) <= 1e-9 * (1.0 + tmag * 1e-3), (e.t, e0.t)
    assert e.label == e0.label, (e.label, e0.label)
    assert e.normal == pytest.approx(_rotv(e0.normal, th), abs=1e-9)


# ---------------------------------------------------------------- bb52 真几何：legacy 的每条顶点-边接触都能作为首入被选中

FIX = ROOT / "fixtures" / "bdda_df" / "studio_20260712"


def _independent_overlap(A, B, x=(0., 0.)):
    """独立 Fraction 边交 + winding oracle；不调用生产的相交、耳切、法锥、SAT 或其原语。
    正面积交来自严格包含、真交叉或同向共线边的正长度交；其余闭集接触记 0。"""
    from fractions import Fraction as F
    A = [(F(a)+F(x[0]), F(b)+F(x[1])) for a,b in A]
    B = [(F(a),F(b)) for a,b in B]
    def orient(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def on(a,b,p):
        return orient(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
    def inside(p,P):
        winding=0
        for i,a in enumerate(P):
            b=P[(i+1)%len(P)]
            if on(a,b,p): return 0
            if a[1]<=p[1]<b[1] and orient(a,b,p)>0: winding+=1
            if b[1]<=p[1]<a[1] and orient(a,b,p)<0: winding-=1
        return 1 if winding else -1
    touch=False
    for P,Q in ((A,B),(B,A)):
        for i,a in enumerate(P):
            b=P[(i+1)%len(P)]
            for p in (a,((a[0]+b[0])/2,(a[1]+b[1])/2)):
                state=inside(p,Q)
                if state==1: return 1
                touch |= state==0
    for i,a in enumerate(A):
        b=A[(i+1)%len(A)]
        for j,c in enumerate(B):
            d=B[(j+1)%len(B)]
            oa,ob,oc,od=orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
            if oa*ob<0 and oc*od<0: return 1
            if oa==ob==oc==od==0:
                axis=0 if a[0]!=b[0] else 1
                overlap=min(max(a[axis],b[axis]),max(c[axis],d[axis]))-max(min(a[axis],b[axis]),min(c[axis],d[axis]))
                if overlap>0 and (b[0]-a[0])*(d[0]-c[0])+(b[1]-a[1])*(d[1]-c[1])>0: return 1
                touch |= overlap>=0
            touch |= on(a,b,c) or on(a,b,d) or on(c,d,a) or on(c,d,b)
    return 0 if touch else -1


def _independent_exit_labels(A, B):
    """原始边代数的独立局部支撑/投影/平方距离；不调用任何生产法锥或 cover。"""
    from fractions import Fraction as F
    A,B=[[(F(x),F(y)) for x,y in P] for P in (A,B)]
    candidates=[]
    for kind,P,Q in (("VE",A,B),("EV",B,A)):
        for i,p in enumerate(P):
            prev,nxt=P[i-1],P[(i+1)%len(P)]
            u=(p[0]-prev[0],p[1]-prev[1]); v=(nxt[0]-p[0],nxt[1]-p[1])
            turn=u[0]*v[1]-u[1]*v[0]
            if turn<0 or (turn==0 and u[0]*v[0]+u[1]*v[1]<=0): continue
            for j,q in enumerate(Q):
                r=Q[(j+1)%len(Q)]; ex,ey=r[0]-q[0],r[1]-q[1]
                if ex*u[1]-ey*u[0]<0 or v[0]*ey-v[1]*ex<0: continue
                if turn==0 and ex*u[0]+ey*u[1]>=0: continue
                dx,dy=p[0]-q[0],p[1]-q[1]
                g=ey*dx-ex*dy; proj=ex*dx+ey*dy; length2=ex*ex+ey*ey
                if g<=0 and 0<=proj<=length2:
                    label=(kind,i,j) if kind=="VE" else (kind,j,i)
                    candidates.append((g*g/length2,label))
    best=min(distance for distance,_ in candidates)
    return {label for distance,label in candidates if distance==best}


@pytest.mark.skipif(not (FIX / "bdda_debug_verts.csv").exists(), reason="bb52 fixture missing")
def test_every_legacy_vertex_edge_contact_of_bb52_is_a_first_entrance_along_its_edge_normal():
    """53 条 legacy 盖仍在 sin(3°)/FIT 窗口全量对账；所有输入另核精确初态，不跳过微贯入。
    微贯入必须返回独立精确最浅盖集合；真正未侵入的首入才与 legacy 贴合窗比较。
    oracle 为本文件内联 Fraction 边交/winding 与独立支撑列，不共用生产几何原语。"""
    sys.path.insert(0, str(ROOT / "tools"))
    import bb52_g0
    blocks, alias = bb52_g0.load_blocks(step=1)
    v2b = {v: b for b, dct in blocks.items() for v in dct["vidx"]}
    loc = {v: i for b, dct in blocks.items() for i, v in enumerate(dct["vidx"])}
    misses = []
    n = n_pen = 0
    for mtype, p1, p2, p3, _, _ in bb52_g0.legacy_contacts(step=1):
        if mtype != 0:
            continue
        p1, p2, p3 = (alias.get(v, v) for v in (p1, p2, p3))
        ba, bb = v2b[p1], v2b[p2]
        assert v2b[p3] == bb
        A, B = blocks[ba]["poly"], blocks[bb]["poly"]
        ia = loc[p1]
        i2, i3 = loc[p2], loc[p3]
        nb = len(B)
        jb = i2 if (i2 + 1) % nb == i3 else i3
        assert {jb, (jb + 1) % nb} == {i2, i3}
        FIT = 1e-6                                      # 夹具初始位形的贴合精度（G1 门：matched_gap_max_abs < 1e-6）
        CONE = math.sin(math.radians(3.0))              # legacy 的 h1 = 3° 法锥角容差（G1 门复现 53/53 用的就是它）
        n += 1
        # (1) legacy 的这条 v-e 在 legacy 自己的精度下是引擎的有效盖、间隙在贴合精度内
        c = ve_cover(A, ia, B, jb, FIT, cone_tol=CONE)
        if c is None or abs(c.gap) > FIT:
            misses.append((ba, bb, p1, (p3, p2), "legacy v-e not a cover at 3deg/1e-6", None if c is None else c.gap))
            continue
        nB = outward_normal(B, jb)
        d = tuple(-x for x in nB)
        n_pen += polygons_overlap(A, B, FIT) == 1       # 原 legacy 带内计数约束保留，但不再跳过这些输入
        initial = _independent_overlap(A, B)
        # (2) 引擎沿该边内法向逼近的首入：同一条盖、或同一顶点的集值邻支、或接触点就是这个顶点、或落在同一条接触线上
        #     （平行边贴合的退化族：legacy 记 A 顶点对 B 边，引擎可能记 B 顶点对 A 边，法向相同）
        e = first_entrance(A, B, (0.0, 0.0), d, tol=FIT, t_max=1.0)
        if initial == 1:
            assert e.kind == "exit", (ba, bb, p1, initial, e)
            want = _independent_exit_labels(A, B)
            assert e.label in want and set(e.tied_labels) == want, (ba, bb, p1, e.tied_labels, want)
            continue
        assert e.kind == "entrance", (ba, bb, p1, initial, e)
        assert e.t_exact is not None
        from fractions import Fraction as F
        exact_x = (e.t_exact * F(d[0]), e.t_exact * F(d[1]))
        assert _independent_overlap(A, B, exact_x) == 0, (ba, bb, p1, e.t_exact)
        if initial == 0:
            assert e.t == 0.0
        labels = e.tied_labels
        same_label = ("VE", ia, jb) in labels or any(lab[0] == "VE" and lab[1] == ia for lab in labels)
        same_point = any(p is not None and math.dist(p, A[ia]) <= FIT for p in (e.point_a, e.point_b))
        same_plane = e.normal is not None and abs(e.normal[0] * nB[1] - e.normal[1] * nB[0]) <= 1e-6 and e.t <= FIT
        same_time = e.kind == "entrance" and abs(e.t - c.gap) <= FIT          # legacy 那条在贴合精度内与首入同时被触及
        if not (same_label or same_point or same_plane or same_time):
            misses.append((ba, bb, p1, (p3, p2), e.kind, e.label, e.t, labels[:3]))
    assert n == 53 and n_pen <= 20, (n, n_pen)
    assert not misses, (len(misses), misses[:5])


def test_an_earlier_out_of_segment_candidate_is_skipped_on_the_concave_step():
    """方块在竖板右侧正上方（x ∈ [1.5, 2.5]）竖直下落：上踏面 y = 1 的候选时刻更早（t = 0.5）但投影落在它的段外（x > 1），
    真首入是下踏面 y = 0.5（t = 1.0）。候选不在各自时刻重验边内、又不用谓词核验，就会把 t = 0.5 当首入（两处互为冗余，同时撤回才错）。"""
    A = translate(SQ, (1.5, 1.5))
    e = first_entrance(A, STEP, (0.0, 0.0), (0.0, -1.0), t_max=3.0)
    assert e.kind == "entrance" and e.t == pytest.approx(1.0, abs=1e-12), (e.kind, e.t, e.label)
    assert e.normal == pytest.approx((0.0, 1.0), abs=1e-12)
    assert first_entrance_brute(A, STEP, (0.0, 0.0), (0.0, -1.0), t_max=3.0) == pytest.approx(1.0, abs=1e-9)


def test_an_empty_candidate_set_is_not_answered_as_none_when_the_bodies_touch(monkeypatch):
    """把凹对的盖枚举整个掏空：引擎不许答"不触及"——谓词探针在候选时刻（这里没有）之外还得有一道，所以探针按候选时刻走不到时
    仍要抛错：这里用台阶对上一条用例的位形，枚举掏空后候选为空，必须以 RuntimeError 报"漏了首入"而不是返回 none。"""
    import eab.kernel2d.entrance as E
    A = translate(SQ, (1.4, 0.9))
    monkeypatch.setattr(E, "enumerate_covers", lambda At, B, **kw: [])
    with pytest.raises(RuntimeError, match="missed an earlier entrance"):
        first_entrance(A, STEP, (0.0, 0.0), (-1.0, -0.5), t_max=3.0)
