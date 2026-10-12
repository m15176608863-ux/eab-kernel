"""Exact supplied-data wall roots and explicit local contact-window migration.

The original four groups by twenty seeds remain unchanged. Exact default roots
are checked by independent integer swept triangle SAT and rational ray parity.
The original nominal 0.2 / frozen-height assertions remain under an explicit
legacy-sized window. Additional ideal rational and 1e-6-clearance cases preserve
the original physical intent without silently discarding near-vertical events.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel3d.geom3 import Polyhedron, box  # noqa: E402
from eab.kernel3d.interlock import (escape_height_brute, escape_height_covers, escape_height_from_frozen_cover,  # noqa: E402
                                    frozen_ee_sign)

U_PROF = [(-2, -1), (2, -1), (2, 1), (1, 1), (1, 0), (-1, 0), (-1, 1), (-2, 1)]   # 槽底 z = 0（|x| < 1），竖墙 x = ±1 到 z = 1
DIR = (0.6, -0.48, 0.64)


def _prism_xz(prof, y0, y1):
    n = len(prof)
    v = [(float(x), float(y0), float(z)) for x, z in prof] + [(float(x), float(y1), float(z)) for x, z in prof]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    P = Polyhedron(v, faces)
    return P if P.volume() > 0 else Polyhedron(v, [tuple(reversed(f)) for f in faces])


def _key(clearance=0.0):
    A0 = box(center=(0.0, 0.0, 0.3), half=(1.0-clearance, 0.5, 0.5))                   # 贴两墙、压进槽底 0.2
    return Polyhedron([(-p[0], p[1], p[2]) for p in A0.verts], [tuple(reversed(f)) for f in A0.faces])   # 顶点 0 在 x = +1 侧


def _place(P, th, t, rng, ulps):
    """绕 z 转 th、平移到 |t|，每个坐标再加 ±ulps 个 ulp 的独立舍入（DDA 更新或导出的顶点就是这样）。"""
    c, s = math.cos(th), math.sin(th)
    return Polyhedron([tuple(x + rng.randint(-ulps, ulps) * math.ulp(x) for x in
                             (c * p[0] - s * p[1] + t * DIR[0], s * p[0] + c * p[1] + t * DIR[1], p[2] + t * DIR[2]))
                       for p in P.verts], list(P.faces))


from e5b_wall_oracle import earliest_wall_escape
from eab.margin import effective_geom_tol


@pytest.mark.parametrize("t,ulps", [(1e5, 4), (1e4, 1), (1e3, 4), (0.0, 0)])
def test_vertical_walls_do_not_hijack_the_escape_height(t, ulps):
    """All original 80 raw inputs: exact answer against independent SAT/ray oracle.

    Oracle primitives are test-only integer triangle SAT intervals and parity
    rays. No production event, geometric predicate, normal or triangulator is used.
    The original nominal 0.2 assertions remain verbatim in explicit window mode.
    """
    L0, Am = _prism_xz(U_PROF, -1.0, 1.0), _key()
    for seed in range(20):
        rng = random.Random(seed)
        A, L = _place(Am, 0.7, t, rng, ulps), _place(L0, 0.7, t, rng, ulps)
        sol = escape_height_covers(A, L, (0.0, 0.0, 0.0))
        truth=earliest_wall_escape(A,L)
        assert sol.exact_height == truth, (seed, sol.exact_height, truth, "exact earliest root")
        assert sol.nonpenetrating_state != 1
        window=effective_geom_tol(A,L,None)
        sol = escape_height_covers(A, L, (0.0, 0.0, 0.0), contact_window=window)
        assert abs(sol.height - 0.2) <= 1e-6, (seed, sol.height, sol.cover_label)
        lab = sol.cover_label
        assert lab[0] in ("VF", "FV", "EE")
        sg = frozen_ee_sign(A, L, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2])) if lab[0] == "EE" else 1.0
        zf = float(escape_height_from_frozen_cover(A, L, lab, (0.0, 0.0, 0.0), ee_sign=sg))
        assert abs(zf - 0.2) <= 1e-6, (seed, lab, zf)
        if seed < 3:
            assert abs(sol.height - escape_height_brute(A, L, (0.0, 0.0, 0.0), hi=2.0, contact_window=window)) <= 1e-6


@pytest.mark.parametrize("t,ulps", [(1e5, 4), (1e4, 1), (1e3, 4), (0.0, 0)])
def test_clearance_keeps_jittered_walls_from_controlling_height(t,ulps):
    """The original 80-cell construction, now with 1e-6 true lateral clearance."""
    L0,Am=_prism_xz(U_PROF,-1.,1.),_key(clearance=1e-6)
    for seed in range(20):
        rng=random.Random(seed)
        A,L=_place(Am,.7,t,rng,ulps),_place(L0,.7,t,rng,ulps)
        sol=escape_height_covers(A,L,(0.,0.,0.))
        assert sol.exact_height==earliest_wall_escape(A,L), 'clearance exact root'
        assert abs(sol.height-.2)<=1e-6
        lab=sol.cover_label
        sg=frozen_ee_sign(A,L,(lab[1][1],lab[1][2]),(lab[2][1],lab[2][2])) if lab[0]=='EE' else 1.
        frozen=float(escape_height_from_frozen_cover(A,L,lab,(0.,0.,0.),ee_sign=sg))
        assert abs(frozen-.2)<=1e-6, (seed,lab,frozen)


@pytest.mark.parametrize('scale,translation',[(1.,0.),(1e-3,0.),(1e3,1e5),(1.,1e5)])
def test_exactly_vertical_ideal_walls_give_point_two(scale,translation):
    """No float rotation/jitter: exact rational affine data preserve vertical walls."""
    from fractions import Fraction as F
    A,L=_key(),_prism_xz(U_PROF,-1.,1.)
    s,t=F(scale),F(translation)
    def affine(P):
        # Rational z-rotation (3/5,-4/5;4/5,3/5), no intermediate float rounding.
        return Polyhedron([(s*(F(3,5)*F(x)-F(4,5)*F(y))+t,
                            s*(F(4,5)*F(x)+F(3,5)*F(y))-t,s*F(z)+t) for x,y,z in P.verts],P.faces)
    A,L=affine(A),affine(L)
    sol=escape_height_covers(A,L,(0,0,0))
    assert sol.exact_height==F(.2)*s
    assert abs(sol.height/scale-.2)<1e-12
    lab=sol.cover_label
    sg=frozen_ee_sign(A,L,(lab[1][1],lab[1][2]),(lab[2][1],lab[2][2])) if lab[0]=='EE' else 1.
    assert abs(float(escape_height_from_frozen_cover(A,L,lab,(0,0,0),ee_sign=sg))/scale-.2)<1e-10
