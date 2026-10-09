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
  共用：2026-09-24 之前 convex_hull_3d 内部用 Polyhedron.face_normal 判可见性；M0.2 起凸包是
  Quickhull、用自己的三角叉积，不再调用 face_normal，两侧只共用顶点坐标。face_normal 整体出错时
  票二局部侧会错、凸包侧不受影响；票一（暴力谓词，与法向符号无关）另行兜底，见 test_kernel3d_covers
  的翻转法向牙。
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
    """多报也要红：往严格集合里塞一个不是 facet 的标签（一个非支撑的 VF）。

    M0.3 起票二按**组合**配对（标签的顶点集 ⊆ 凸包 facet 的支撑集），不按法向夹角：非支撑的 VF 的顶点不在
    该 facet 的 A 侧支撑集里，报 local_only（旧版按法向配对只能报 duplicate——它的法向确实是某个 facet 的法向）。
    duplicate 分支的牙见 test_vote2_two_labels_on_one_plane_are_reported_duplicate。"""
    A, B = _random_pair(0)
    full = local_facets3(A, B, 1e-12)
    used = {(lab[1][1], lab[2][1]) for lab in full if lab[0] == "VF"}
    bogus = next(("VF", ("vertex", ia), ("face", fb)) for ia in range(len(A.verts))
                 for fb in range(len(B.faces)) if (ia, fb) not in used)
    monkeypatch.setattr(g03, "local_facets3", lambda a, b, t: set(full) | {bogus})
    rep = g0_convex3(A, B, samples=0, seed=0)
    assert not rep.passed
    assert rep.facet_symmetric_diff == [("local_only", bogus)], rep.facet_symmetric_diff


def test_vote2_two_labels_on_one_plane_are_reported_duplicate():
    """duplicate 分支：三角化的方块（凸包输出）对四面体——同一个平面被拆成两个三角，一个顶点对它给出两个 VF
    标签，而凸包侧只有一个 facet（支撑集 = 整个面）。第二个标签报 duplicate。"""
    from eab.kernel3d.geom3 import Polyhedron
    tri_box = convex_hull_3d(box(half=(1.0, 1.0, 1.0)).verts)
    assert len(tri_box.faces) == 12
    t = tetra((3.0, 0.2, 0.1), (4.0, 0.3, 0.2), (3.2, 1.0, 0.4), (3.3, 0.1, 1.0))
    rep = g0_convex3(t, tri_box, samples=0)
    kinds = [e[0] for e in rep.facet_symmetric_diff]
    assert kinds and set(kinds) == {"duplicate"}, rep.facet_symmetric_diff


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


# ---------------------------------------------------------------- G6 minor 17：票二 local_only 分支的牙
#
# 审查：唯一的"多报"测试注入的 VF 恰好用了一个已是 facet 的 B 面法向，只能走到 duplicate 分支；
# 把 g03.py 的 local_only 分支改成 pass，全套 1209 照绿。这里注入**不是 facet 的** EE 标签与
# 非支撑的 FV 标签（法向与任何严格 facet 都不同向），samples=0 只看票二，断言对称差恰是 local_only。

def _non_facet_ee_labels(A, B, full):
    """不是 facet 的 EE 标签，且其 facet_normal3 与任何严格 facet 法向都不同向（只能走 local_only）。"""
    from eab.kernel3d.covers3 import facet_normal3
    from eab.kernel3d.geom3 import angle_between
    normals = [facet_normal3(A, B, lab) for lab in full]
    out = []
    for ea in A.edges():
        for eb in B.edges():
            lab = ("EE", ("edge",) + ea, ("edge",) + eb)
            if lab in full:
                continue
            try:
                n = facet_normal3(A, B, lab)
            except ZeroDivisionError:
                continue
            if all(angle_between(n, m) > 1e-3 for m in normals):
                out.append(lab)
    return out


@pytest.mark.parametrize("seed", range(6))
def test_vote2_has_teeth_a_non_facet_ee_is_reported_local_only(monkeypatch, seed):
    A, B = _random_pair(seed)
    full = local_facets3(A, B, 1e-12)
    bogus = _non_facet_ee_labels(A, B, full)[:10]
    assert len(bogus) >= 5, len(bogus)
    for lab in bogus:
        monkeypatch.setattr(g03, "local_facets3", lambda a, b, t, _l=lab: set(full) | {_l})
        rep = g0_convex3(A, B, samples=0, seed=seed)
        assert not rep.passed, lab
        assert rep.facet_symmetric_diff == [("local_only", lab)], (lab, rep.facet_symmetric_diff)
    monkeypatch.undo()


@pytest.mark.parametrize("seed", range(6))
def test_vote2_non_supporting_fv_is_reported_local_only(monkeypatch, seed):
    """非支撑的 FV（A 的面配错了 B 的顶点）：法向 −n_A 是某个严格 facet 的法向，但配错的 B 顶点不在该 facet 的
    B 侧支撑集里——组合配对报 local_only（旧版按法向配对报 duplicate）。"""
    A, B = _random_pair(seed)
    full = local_facets3(A, B, 1e-12)
    fv = sorted(lab for lab in full if lab[0] == "FV")[0]
    bogus = next(("FV", fv[1], ("vertex", ib)) for ib in range(len(B.verts)) if ("FV", fv[1], ("vertex", ib)) not in full)
    monkeypatch.setattr(g03, "local_facets3", lambda a, b, t: set(full) | {bogus})
    rep = g0_convex3(A, B, samples=0, seed=seed)
    assert not rep.passed
    assert rep.facet_symmetric_diff == [("local_only", bogus)], rep.facet_symmetric_diff


# ---------------------------------------------------------------- G6 minor 9：G0 门自身的尺度格（纪律 B）
#
# 缺陷（g03.py:187）：convex_hull_3d(diffs, tol=1e-12) 把绝对 1e-12 与 ∝ 长度³ 的三重积比较，尺度 ≤ 1e-5
# 时凸包报"共面"、门不能用；票三的 round(., 7) 顶点键也是绝对的。
# oracle：同一对物体在 ×s 下的 G0 报告结构计数必须与 ×1 相同（tetra vs box 的解析计数 7/7/3、13 顶点）。

@pytest.mark.parametrize("scale", [1e-6, 1e-5, 1e-3, 1.0, 1e3, 1e5])
def test_g0_gate_works_at_every_scale_tetra_box(scale):
    t = tetra((0.0, 0.0, 0.0), (scale, 0.0, 0.0), (0.0, scale, 0.0), (0.0, 0.0, scale))
    b = box(half=(scale, scale, scale))
    rep = g0_convex3(t, b, samples=60, seed=0)
    assert (rep.facet_local, rep.facet_global, rep.facet_degenerate) == (7, 7, 3), rep
    assert rep.hull_vertices == rep.e_vertices == 13 and rep.hull_vertex_mismatch == 0, rep
    assert rep.mismatches == [] and rep.passed, rep
    assert rep.samples > 20, rep


@pytest.mark.parametrize("scale", [1e-5, 1e3])
@pytest.mark.parametrize("seed", range(3))
def test_g0_gate_works_at_every_scale_random_pairs(seed, scale):
    A0, B0 = _random_pair(seed)
    from eab.kernel3d.geom3 import Polyhedron
    A = Polyhedron([tuple(scale * c for c in p) for p in A0.verts], list(A0.faces))
    B = Polyhedron([tuple(scale * c for c in p) for p in B0.verts], list(B0.faces))
    r0 = g0_convex3(A0, B0, samples=40, seed=seed)
    r = g0_convex3(A, B, samples=40, seed=seed)
    assert r.passed, (r.facet_symmetric_diff[:3], r.hull_vertices, r.e_vertices, r.mismatches[:2])
    assert (r.facet_local, r.facet_global, r.hull_vertices, r.e_vertices) ==         (r0.facet_local, r0.facet_global, r0.hull_vertices, r0.e_vertices)



# ---------------------------------------------------------------- G6 第三轮 major：说不清的 facet 被报成 hull_anomaly

def _quat_rotation(seed: int):
    import math
    rng = random.Random(seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


@pytest.mark.parametrize("seed", range(20))
@pytest.mark.parametrize("yaw", [1e-3, 3e-4, 1e-4])
def test_yawed_stack_passes_g0_under_random_rotations(yaw, seed):
    """1 m 方块绕 z 偏航 yaw 搁在 2 m 板上方 0.1，再整体随机旋转：旧版 facet_vote3 先查"异常"后查"说不清"，紧带支撑集
    退化成 (0,0)/(1,0) 的歧义 facet 被报成 hull_anomaly（yaw 1e-3 时 2/20 姿态、3e-4 时 15/20、1e-4 时 17/20 门红）；
    根因是 _hull_facets 棱×棱候选的噪声没除 sinθ，近平行最远点对以 4e-14 的自报噪声压过 3e-16 的精确平面候选。
    现在 20 个姿态全部通过、对称差为空、无 hull_anomaly。"""
    import math
    from eab.kernel3d.geom3 import Polyhedron
    c, s = math.cos(yaw), math.sin(yaw)
    A0 = box(center=(0.0, 0.0, 1.1), half=(0.5, 0.5, 0.5))
    A0 = Polyhedron([(c * x - s * y, s * x + c * y, z) for x, y, z in A0.verts], list(A0.faces))
    B0 = box(half=(1.0, 1.0, 0.5))
    R = _quat_rotation(seed)
    xf = lambda P: Polyhedron([tuple(sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in P.verts], list(P.faces))
    r = g0_convex3(xf(A0), xf(B0), samples=12, seed=0)
    assert r.passed and r.facet_symmetric_diff == [] and not any(d[0] == "hull_anomaly" for d in r.facet_symmetric_diff), r
