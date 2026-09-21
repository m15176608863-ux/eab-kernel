"""G2 三维同构门 · 对 bdda3d 的入口列表，外加共面归并的门。

三维接触枚举此前**没有任何 legacy 对账通道**（docs/sibling_observations.md），这是第一份。
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from g2_bdda3d import compare, load_case, polyhedron_preserving_indices  # noqa: E402
from osteomorphic import osteomorphic_block  # noqa: E402

from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.kernel3d.geom3 import (box, convex_hull_3d, merge_coplanar, tetra)  # noqa: E402

CASES = sorted((ROOT / "fixtures" / "bdda3d").glob("*.json"))


# ---------------------------------------------------------------- 共面归并

@pytest.mark.parametrize("P,name,want", [
    (tetra((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)), "tetra", 4),
    (box(), "box", 6),
    (convex_hull_3d(box().verts), "box_from_hull", 6),
    (osteomorphic_block(nx=4, ny=2, amp=0.0), "osteo_flat", 6),
])
def test_merge_coplanar_face_counts_and_invariants(P, name, want):
    M = merge_coplanar(P)
    assert len(M.faces) == want, (name, len(M.faces))
    assert M.volume() == pytest.approx(P.volume(), abs=1e-12), name   # 体积是归并的不变量
    assert M.manifold_issues() == [], (name, M.manifold_issues())


def test_merge_coplanar_kills_the_triangulation_over_count():
    """归并的理由，钉成反例：三角化会让同一个顶点对**同一个平面**产生多个 VF 盖。

    2026-09-20 G2 实测：cb2 的 4×4 顶面被凸包拆成两个三角形后，上块四个底角给出 **6** 个
    有效盖（投影落在公共对角线上的两个角各被数两次）；归并之后恰好 4 个，与 legacy 一致。
    """
    upper_pts = box(center=(0.0, 0.0, 0.5), half=(1.0, 1.0, 0.5)).verts
    lower_pts = box(center=(0.0, 0.0, -0.5), half=(2.0, 2.0, 0.5)).verts
    At, Bt = convex_hull_3d(upper_pts), convex_hull_3d(lower_pts)
    tri = [c for c in enumerate_covers3(At, Bt, window=1.0, tol=1e-9) if c.in_extent]
    assert len(tri) == 6                                   # 三角化：过计数
    Am, Bm = merge_coplanar(At), merge_coplanar(Bt)
    mer = [c for c in enumerate_covers3(Am, Bm, window=1.0, tol=1e-9) if c.in_extent]
    assert len(mer) == 4                                   # 归并后：几何决定的盖数
    assert len({c.a_feature[1] for c in mer}) == 4


# ---------------------------------------------------------------- G2 同构

@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_isomorphism_against_bdda3d(path):
    res = compare(path)
    assert res["rows"], path
    for r in res["rows"]:
        assert r["legacy"], (path, "legacy 侧为空，夹具或读取有问题")
        assert r["legacy_only"] == [], (path, r["pair"], r["legacy_only"])
        assert r["mine_only"] == [], (path, r["pair"], r["mine_only"])
        assert len(r["mine"]) == len(r["legacy"]) == 4


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_geometry_details_match(path):
    """不只比集合：间隙与法向也要对上。cb2 是零间隙坐落，法向 +z。"""
    _, _, blocks, entrances = load_case(path)
    A, B = blocks[2], blocks[1]
    covs = [c for c in enumerate_covers3(A, B, window=1.0, tol=1e-9)
            if c.in_extent and c.kind == "VF"]
    assert len(covs) == 4
    for c in covs:
        assert abs(c.gap) < 1e-12
        assert c.normal is not None and abs(c.normal[2] - 1.0) < 1e-12
        assert not c.strict            # 面-面退化：法向落在顶点锥的边界上（命题 4）
    # legacy 的 nsign 同号约定
    assert {e["nsign"] for e in entrances} == {1.0}


def test_g2_gate_has_teeth_a_dropped_cover_is_caught(monkeypatch):
    """门要有牙：让枚举漏掉一个 VF 盖，G2 必须报出 legacy_only。"""
    import eab.kernel3d.covers3 as cv
    orig = cv.vf_cover
    state = {"n": 0}

    def lossy(A, ia, B, fb, tol=0.0):
        c = orig(A, ia, B, fb, tol)
        # 必须同时满足 in_extent **与窗口**才是会进最终清单的盖；
        # 只看 in_extent 会丢掉一个本来就被窗口滤掉的盖，门当然不会红（2026-09-20 踩过）。
        if c is not None and c.in_extent and abs(c.gap) <= 1.0:
            state["n"] += 1
            if state["n"] == 1:
                return None
        return c

    monkeypatch.setattr(cv, "vf_cover", lossy)
    res = compare(CASES[0])
    assert any(r["legacy_only"] for r in res["rows"]), "漏掉一个盖却没被门抓住"


def test_vertex_indices_are_preserved_through_hull_reconstruction():
    """夹具的顶点编号必须原样保留（凸包会重编号），否则与 legacy 的 refs 对不上。"""
    pts = [(0.3, -0.2, 0.1), (1.4, 0.0, 0.0), (0.0, 1.1, 0.2), (0.1, 0.2, 1.3),
           (1.0, 1.0, 1.0)]
    P = polyhedron_preserving_indices(pts)
    assert P.verts == pts
    assert all(all(0 <= i < len(pts) for i in f) for f in P.faces)
