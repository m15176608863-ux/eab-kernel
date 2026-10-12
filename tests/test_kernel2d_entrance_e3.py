"""E3 入口精确门：主 oracle 为闭式矩形/台阶以及测试内联 Fraction SAT。

不以生产 polygons_overlap_exact、法锥、Minkowski 或候选生成器作主 oracle。
注入门修改真实候选生成路径；同实现精确谓词 brute 仅作辅助检查。
"""
from construction_oracle import scalar_exact
import math
from fractions import Fraction as F

import pytest

from eab.kernel2d.entrance import first_entrance, first_entrance_brute, shortest_exit

SQ = [(0., 0.), (1., 0.), (1., 1.), (0., 1.)]
STEP = [(0., 0.), (2., 0.), (2., .5), (1., .5), (1., 1.), (0., 1.)]


def shifted(P, x, y):
    return [(a + x, b + y) for a, b in P]


@pytest.mark.parametrize('offset', [0., 1e3, 1e6])
@pytest.mark.parametrize('scale', [2.**-10, 1., 2.**10])
def test_concave_first_entrance_keeps_sub_roundoff_translation_and_tiny_velocity(offset, scale):
    """竖板闭式 t=δ/speed；平移必须先 Fraction，再谓词，不能吞掉 δ。"""
    A = [(offset + scale * (x + 1), offset + scale * (y + .75)) for x,y in SQ]
    B = [(offset + scale * x, offset + scale * y) for x,y in STEP]
    delta, speed = scale * 2.**-45, scale * 2.**-50
    e = first_entrance(A, B, (delta, 0.), (-speed, 0.), t_max=64.)
    assert e.kind == 'entrance' and e.t == 32., (e.kind, e.t)
    for tol in (0., scale):
        short = first_entrance(A, B, (delta, 0.), (-speed, 0.), t_max=math.nextafter(32., 0.), tol=tol)
        assert short.kind == 'none', (short.kind, short.t)


def test_concave_initial_overlap_is_exact_even_below_coordinate_roundoff():
    A, B = shifted(SQ, 1e6 + 1., 1e6 + .75), shifted(STEP, 1e6, 1e6)
    got = first_entrance(A, B, (-2.**-45, 0.), (-1., 0.))
    assert got.kind == 'exit' and got.gap == -2.**-45, (got.kind, got.gap)


@pytest.mark.parametrize('direction', [(1., 0.), (0., 1.), (-1., 0.)])
def test_concave_touching_start_has_closed_set_time_zero(direction):
    A = shifted(SQ, 1., .75)
    e = first_entrance(A, STEP, (0., 0.), direction)
    assert e.kind == 'entrance' and e.t == 0.


def test_concave_fraction_time_is_not_replaced_by_rounded_float_candidate():
    A = shifted(SQ, 1.4, .9)
    e = first_entrance(A, STEP, (0., 0.), (-.7, -.1), t_max=2.)
    want = (F(1.4) - 1) / F(.7)
    assert e.kind == 'entrance' and e.t == scalar_exact(want), (e.kind, e.t, want)
    assert e.t_exact == want


def test_concave_near_times_are_not_exact_ties_even_with_a_report_window():
    A = shifted(SQ, 1.5, 1.5)
    # top and bottom corners have nonidentical y after shear; exact lower corner wins.
    A[1] = (A[1][0], A[1][1] + 2.**-40)
    e = first_entrance(A, STEP, (0., 0.), (0., -1.), tol=.01, t_max=3.)
    assert e.kind == 'entrance' and e.t == 1.
    assert ('VE', 1, 2) not in e.tied_labels
    assert ('VE', 0, 2) in e.tied_labels


def test_shortest_exit_compares_exact_signed_distance_not_rounded_gap():
    A, B = shifted(SQ, 1e6 + 1., 1e6 + .75), shifted(STEP, 1e6, 1e6)
    e = shortest_exit(A, B, (-2.**-45, 0.))
    assert e.normal == (1., 0.) and e.gap == -2.**-45, (e.normal, e.gap)
    e = shortest_exit(shifted(SQ, .2, -.125), [(-2.,-1.),(2.,-1.),(2.,0.),(-2.,0.)], (0.,0.))
    assert e.normal == (0., 1.) and e.gap == -.125


def test_brute_uses_exact_translation_not_noise_band():
    A, B = shifted(SQ, 1e6 + 1., 1e6 + .75), shifted(STEP, 1e6, 1e6)
    got = first_entrance_brute(A, B, (2.**-45, 0.), (-2.**-50, 0.), t_max=64., steps=8)
    assert got == 32.


def test_missing_earlier_concave_contact_is_caught_by_exact_selfcheck(monkeypatch):
    from eab.kernel2d import entrance as E
    A = shifted(SQ, 1.4, .9)
    real = E.enumerate_covers
    def dropped(A, B, **kwargs):
        return [c for c in real(A, B, **kwargs) if not (
            (c.kind == 'VE' and c.b_index == 3) or
            (c.kind == 'EV' and B[c.b_index][0] == 1.))]
    monkeypatch.setattr(E, 'enumerate_covers', dropped)
    with pytest.raises(RuntimeError, match='missed an earlier entrance'):
        first_entrance(A, STEP, (0.,0.), (-1.,-.5), t_max=3.)

def _sat_ray(A, B, x, d):
    """独立内联 Fraction 全投影 SAT；无生产几何原语。返回凸片首次闭集相交时刻。"""
    A, B = [[(F(u), F(v)) for u,v in P] for P in (A,B)]
    X, D = tuple(map(F,x)), tuple(map(F,d))
    low, high = F(0), None
    for P in (A,B):
        for i,p in enumerate(P):
            q = P[(i+1)%len(P)]
            nx,ny = q[1]-p[1], p[0]-q[0]
            aa = [nx*(a[0]+X[0])+ny*(a[1]+X[1]) for a in A]
            bb = [nx*b[0]+ny*b[1] for b in B]
            speed = nx*D[0]+ny*D[1]
            lower, upper = min(bb)-max(aa), max(bb)-min(aa)
            if speed == 0:
                if lower > 0 or upper < 0:
                    return None
                continue
            lo,hi = sorted((lower/speed,upper/speed))
            low = max(low,lo)
            high = hi if high is None else min(high,hi)
    return None if high is not None and low > high else low


@pytest.mark.parametrize('seed', range(8))
@pytest.mark.parametrize('offset', [0.,1e3,1e6])
@pytest.mark.parametrize('scale', [2.**-10,1.,2.**10])
def test_concave_rotated_translated_and_scaled_ray_matches_independent_piecewise_sat(seed, offset, scale):
    """STEP 用已知四个三角凸片分解（仅输入顶点，不调用耳切）；每格答对实际舍入数据。"""
    import random
    theta = random.Random(914+seed).uniform(.1,6.)
    c,s = math.cos(theta), math.sin(theta)
    def transform(P):
        return [(offset+scale*(c*x-s*y), -.7*offset+scale*(s*x+c*y)) for x,y in P]
    A = transform(shifted(SQ,1.4,.9))
    B = transform(STEP)
    d = (scale*(-c+.5*s),scale*(-s-.5*c))
    times = [_sat_ray(A,[B[i] for i in tri],(0.,0.),d)
             for tri in ((0,1,2),(0,2,3),(0,3,4),(0,4,5))]
    want = min(t for t in times if t is not None)
    e = first_entrance(A,B,(0.,0.),d,t_max=3.)
    assert e.kind == 'entrance' and e.t_exact == want and e.t == scalar_exact(want)


def test_exact_selfcheck_catches_an_earlier_narrow_contact_interval_not_just_the_last_step(monkeypatch):
    """U 的左壁先碰后离；删掉左壁候选后右壁前一步分离，但全前事件仍必须报漏首入。"""
    from eab.kernel2d import entrance as E
    B = [(0.,0.),(4.,0.),(4.,3.),(3.,3.),(3.,1.),(1.,1.),(1.,3.),(0.,3.)]
    A = [(-2.,2.),(-1.875,2.),(-1.875,2.125),(-2.,2.125)]
    real = E.enumerate_covers
    def right_only(A,B,**kwargs):
        return [c for c in real(A,B,**kwargs) if (
            c.kind == 'VE' and B[c.b_index][0] >= 3. and B[(c.b_index+1)%len(B)][0] >= 3.) or (
            c.kind == 'EV' and B[c.b_index][0] >= 3.)]
    monkeypatch.setattr(E,'enumerate_covers',right_only)
    with pytest.raises(RuntimeError,match='missed an earlier entrance'):
        first_entrance(A,B,(0.,0.),(1.,0.),t_max=7.)

def test_exact_ties_do_not_include_a_distinct_nearby_tread_contact():
    delta=2.**-40
    B=[(0.,0.),(2.,0.),(2.,.5),(1.,.5),(1.,.5+delta),(0.,.5+delta)]
    A=shifted(SQ,.5,1.)
    e=first_entrance(A,B,(0.,0.),(0.,-1.),tol=.01,t_max=2.)
    assert e.kind=='entrance' and e.t==.5-delta
    assert ('VE',0,4) in e.tied_labels
    assert ('VE',1,2) not in e.tied_labels
    assert ('VE',1,2) in e.near_labels


def test_convex_ties_are_exact_and_near_labels_remain_only_a_report():
    delta=2.**-40
    e=first_entrance(SQ,SQ,(2.,2.+delta),(-1.,-1.),tol=.01)
    assert e.t==1.+delta
    assert set(e.tied_labels)=={('FF',0,2)}
    assert set(e.near_labels)=={('FF',0,2),('FF',3,1)}
