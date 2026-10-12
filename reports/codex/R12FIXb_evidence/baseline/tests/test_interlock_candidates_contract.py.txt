"""公开入口 `escape_candidates` 的两半句契约各自有牙（G6 第五轮 minor，2026-10-10）。

docstring 说按 z* 处的 in_extent 过滤"既不漏真解、又只留真接触"，并说 z* 处的棱内带是谓词分辨率 geom_tol_eff：
  · "只留真接触"：每个候选的盖在它自己的 z* 处必须 in_extent（把过滤整个撤掉，旧门 test_interlock_escape 19 条全绿）；
  · 棱内带 = geom_tol_eff：陡坡折点的谓词分辨带内，逃逸解的并列集（内部路径，已有门）里的每一支都必须出现在公开候选集里
    （把公开入口的带改成 0，旧的三份门 520 条全绿）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from osteomorphic import interlocking_pair  # noqa: E402
from eab.kernel3d.interlock import _cover_at, escape_candidates, escape_height_covers  # noqa: E402
from eab.margin import effective_geom_tol  # noqa: E402


@pytest.mark.parametrize("delta", [0.05, 0.13, 0.2, 0.3, 0.41, 0.45])
def test_every_public_candidate_is_a_real_contact_at_its_own_height(delta):
    A, L = interlocking_pair(nx=5, ny=2, amp=0.3, phase=1.0)
    off = (delta, 0.0, 0.0)
    gtol = effective_geom_tol(A.translated(off), L, None)
    cands = escape_candidates(A, L, off)
    assert cands
    for z, lab in cands:
        if z <= 0.0:
            continue
        c = _cover_at(A.translated((off[0], off[1], off[2] + z)), L, lab, 1e-9, gtol)
        assert c is not None and c.in_extent, (delta, z, lab)


STEEP_KINK = 0.16


@pytest.mark.parametrize("side", (-1.0, 1.0))
@pytest.mark.parametrize("e", (1e-11, 1e-10, 5e-10, 1e-9))
def test_public_candidates_keep_both_branches_inside_the_predicate_band(side, e):
    """陡坡块（nx=5、lx=0.2，活动支 n_z ≈ 0.117）折点两侧谓词分辨带内：逃逸解报出两支并列；两支都得在公开候选集里。"""
    A, L = interlocking_pair(nx=5, ny=2, amp=0.3, phase=1.0, lx=0.2, ly=1.0, lz=1.0)
    off = (STEEP_KINK + side * e, 0.0, 0.0)
    sol = escape_height_covers(A, L, off)
    pub = {lab for _, lab in escape_candidates(A, L, off)}
    missing = [lab for lab in sol.tied_labels if lab not in pub]
    assert not missing, (side * e, missing, sol.tied_labels)
    if e <= 1e-10:
        assert len(sol.tied_labels) >= 2              # 分辨带确实存在（门不许退化）
