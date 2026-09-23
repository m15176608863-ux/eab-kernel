"""三维 G0 的**票二**：局部法锥规则给出的严格 facet 集合 == 由 conv{b − a} 读出的 facet 集合。

审查 C23 / C27（major）：`g0_convex3` 的文档写"三票"，实现只有两票——`local_facets3`
算出来只存了个计数，从不与凸包比较；删掉任一严格 facet，190 次里 181 次仍 passed。

票二的两侧（纪律 A：写明共用了什么）：
  局部侧  每个严格标签的定向外法向 `facet_normal3`：VF → B 面法向；FV → −A 面法向；
          EE → ±unit(t_B × t_A) 按 B 的棱弧定向。用到 Polyhedron.face_normal、edge_arc_contains。
  凸包侧  conv{b − a} 的三角面给候选法向（叉积 + **支撑定向**：全部差点落在非正侧），
          再对每个法向数 A、B 各自有几个顶点达到支撑值（k_A、k_B）：
            k_A = 1 且 k_B ≥ 3 → 严格 VF；k_B = 1 且 k_A ≥ 3 → 严格 FV；k_A = k_B = 2 → 严格 EE；
            其余（k_A, k_B ≥ 2 且非 2/2）→ FF/FE 退化 facet，局部规则按设计不给严格标签。
          只用顶点坐标与点积，不经法锥、不经面环朝向。
  共用：convex_hull_3d 内部用 Polyhedron.face_normal 判可见性。风险：face_normal 若整体出错，
  凸包本身会坏——此时票一（暴力谓词，与法向符号无关）兜底，见 test_kernel3d_covers 的翻转法向牙。
"""

import random

import pytest

import eab.kernel3d.g03 as g03
from eab.kernel3d.covers3 import local_facets3
from eab.kernel3d.g03 import g0_convex3
from eab.kernel3d.geom3 import box, convex_hull_3d, tetra


def _random_pair(seed: int):
    """与 tests/test_kernel3d_covers.py::test_g0_convex3_random_pairs 同一生成器（同一六对）。"""
    rng = random.Random(seed)

    def rnd_hull(n: int, s: float):
        pts = [(rng.uniform(-s, s), rng.uniform(-s, s), rng.uniform(-s, s)) for _ in range(n)]
        return convex_hull_3d(pts)

    A = rnd_hull(7, rng.uniform(0.5, 1.5))
    B = rnd_hull(7, rng.uniform(0.5, 1.5))
    return A, B


@pytest.mark.parametrize("seed", range(6))
def test_vote2_local_facets_equal_hull_facets_on_random_pairs(seed):
    A, B = _random_pair(seed)
    rep = g0_convex3(A, B, samples=0, seed=seed)
    assert rep.facet_symmetric_diff == [], rep.facet_symmetric_diff[:5]
    assert rep.facet_local == rep.facet_global > 0, (rep.facet_local, rep.facet_global)
    assert rep.facet_degenerate == 0                        # 随机凸包处于一般位置
    assert rep.passed


def test_vote2_has_teeth_every_single_dropped_facet_is_caught(monkeypatch):
    """审查实测：删一个严格 facet，旧门 181/190 仍 passed。票二必须 190/190 报红，
    且对称差里恰好点名被删的那个标签。samples=0：只看票二（票一对单个 facet 本来就近乎盲）。"""
    total = caught = 0
    for seed in range(6):
        A, B = _random_pair(seed)
        full = sorted(local_facets3(A, B, 1e-12))
        for lab in full:
            monkeypatch.setattr(g03, "local_facets3", lambda a, b, t, _f=full, _d=lab: set(_f) - {_d})
            rep = g0_convex3(A, B, samples=0, seed=seed)
            total += 1
            if not rep.passed and [e[0] for e in rep.facet_symmetric_diff] == ["hull_only"]:
                caught += 1
        monkeypatch.undo()
    assert total == 190, total                              # 审查计数：27..37 个/对，共 190
    assert caught == total, f"{total - caught}/{total} dropped facets not caught"


def test_vote2_has_teeth_a_spurious_label_is_caught(monkeypatch):
    """多报也要红：往严格集合里塞一个不是 facet 的标签（一个非支撑的 VF）。"""
    A, B = _random_pair(0)
    full = local_facets3(A, B, 1e-12)
    used = {(lab[1][1], lab[2][1]) for lab in full if lab[0] == "VF"}
    bogus = next(("VF", ("vertex", ia), ("face", fb)) for ia in range(len(A.verts))
                 for fb in range(len(B.faces)) if (ia, fb) not in used)
    monkeypatch.setattr(g03, "local_facets3", lambda a, b, t: set(full) | {bogus})
    rep = g0_convex3(A, B, samples=0, seed=0)
    assert not rep.passed
    assert any(e[0] in ("local_only", "duplicate") for e in rep.facet_symmetric_diff), rep.facet_symmetric_diff


def test_vote2_accounts_for_degenerate_facets_tetra_box():
    """四面体 vs 轴对齐方块：E 有 10 个 facet；四面体的 x=0 / y=0 / z=0 三个面与方块的
    +x / +y / +z 面反平行（FF 退化）⇒ 严格 facet = 10 − 3 = 7（解析计数）。"""
    t = tetra((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rep = g0_convex3(t, box(half=(1.0, 1.0, 1.0)), samples=0)
    assert (rep.facet_local, rep.facet_global, rep.facet_degenerate) == (7, 7, 3), rep
    assert rep.facet_symmetric_diff == [] and rep.passed


def test_vote2_accounts_for_degenerate_facets_box_box():
    """两个轴对齐方块：E 的 6 个 facet 全是 FF 退化，严格集合为空，票二照样通过。"""
    rep = g0_convex3(box(half=(1.0, 1.0, 1.0)), box(center=(0.3, 0.0, -0.2), half=(2.0, 0.5, 1.0)),
                     samples=0)
    assert (rep.facet_local, rep.facet_global, rep.facet_degenerate) == (0, 0, 6), rep
    assert rep.facet_symmetric_diff == [] and rep.passed
