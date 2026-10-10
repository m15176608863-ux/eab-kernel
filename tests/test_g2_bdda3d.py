"""G2 三维同构门 · 对 bdda3d 的入口列表，外加共面归并的门。

三维接触枚举此前**没有任何 legacy 对账通道**（docs/sibling_observations.md），这是第一份。
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from g2_bdda3d import G2_BAND, G2_WINDOW, compare, load_case, polyhedron_preserving_indices  # noqa: E402
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

def _assert_g2_gate(res, band=G2_BAND):
    """G2 门的判据（门本身；牙测试调用同一个函数）。

    旧门只看 legacy_only / mine_only，而两者只由 np↔VF/FV 构成：legacy 的 ee 入口进 UNSUPPORTED 桶、
    内核的 EE/VE3/EV3/VV3 盖进 detail 桶，都不参与判定（审查 C17）。现在二者都进 violations，非空即红；
    另外独立断言"窗口内每个有效盖都参与了对账"（n_covers == len(mine)）。
    窗口从 1.0 收到 G2_WINDOW 之后，旧窗口对 (G2_WINDOW, 1.0] 内多余盖的那颗牙由 `band` 接住：
    非空即红，**不论盖的种类**（G6 minor 29：旧版只收 VF/FV）；带内贯入（gap < −G2_WINDOW）另由 `penetration` 单独判红。
    band 是夹具长度量纲：缩放过的夹具（×1e-3 / ×1e3）要按同一比例给，且门断言枚举器**实际收到**的窗口不窄于它
    （enumerated_window 取自 _enumerate_recorded，G6 minor 25）。
    块对取 legacy 与内核的并（G6 minor 14）：内核看到、legacy 没列的块对以 legacy == [] 报红。
    """
    assert res["rows"]
    for r in res["rows"]:
        assert r["legacy"], (r["pair"], "legacy 侧为空，夹具或读取有问题")
        assert r["legacy_only"] == [], (r["pair"], r["legacy_only"])
        assert r["mine_only"] == [], (r["pair"], r["mine_only"])
        assert not [x for x in r["legacy_detail"] if x[0] == "UNSUPPORTED"], (r["pair"], "legacy 有门不认识的入口类")
        assert r["n_covers"] == len(r["mine"]), (r["pair"], "内核有盖未参与对账", r["mine_detail"])
        assert r["violations"] == [], (r["pair"], r["violations"])
        assert r["band_limit"] >= band and r["band"] == [], (r["pair"], "带内有多余的盖", r["band"])
        assert r["penetration"] == [], (r["pair"], "带内有贯入", r["penetration"])
        assert r["enumerated_window"] >= band, (r["pair"], "枚举窗口窄于带宽：带内盖根本不会被枚举")


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_isomorphism_against_bdda3d(path):
    res = compare(path)
    _assert_g2_gate(res)
    for r in res["rows"]:
        assert len(r["mine"]) == len(r["legacy"]) == 4


def _fake_case(tmp_path, mutate):
    d = json.loads(CASES[0].read_text(encoding="utf-8"))
    mutate(d)
    p = tmp_path / f"{CASES[0].stem}_mutated.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    return p


def test_g2_gate_red_on_fabricated_ee_legacy_entrance(tmp_path):
    """审查 C17 REPRO-1：legacy 多一条 `ee` 入口（门不认识的类），门必须红，不许停在 UNSUPPORTED 桶里。"""
    def add_ee(d):
        e = dict(d["entrances"][0])
        e["etype"] = "ee"
        e["refs"] = [[2, 0], [2, 1], [1, 0], [1, 1]]
        d["entrances"].append(e)
    with pytest.raises(AssertionError):
        _assert_g2_gate(compare(_fake_case(tmp_path, add_ee)))


def test_g2_gate_red_on_extra_kernel_ee_cover(monkeypatch):
    """审查 C17 REPRO-2：内核在对账窗口内多出一个 EE 盖（legacy 没有的类），门必须红。"""
    import g2_bdda3d as g2
    from eab.kernel3d.covers3 import Cover3
    orig = g2.enumerate_covers3

    def plus_ee(A, B, **kw):
        out = orig(A, B, **kw)
        p = A.verts[0]
        return out + [Cover3("EE", ("edge", 0, 1), ("edge", 4, 5), (0.0, 0.0, 1.0), 0.0, p, p,
                             (0.5, 0.5), None, True, True)]
    monkeypatch.setattr(g2, "enumerate_covers3", plus_ee)
    with pytest.raises(AssertionError):
        _assert_g2_gate(compare(CASES[0]))


def _inject(monkeypatch, cover):
    """在 compare 拿到的枚举结果后追加一个盖（不看枚举窗口——窗口/带的划分由 compare 自己做，这里要测的就是它）。"""
    import g2_bdda3d as g2
    orig = g2.enumerate_covers3
    monkeypatch.setattr(g2, "enumerate_covers3", lambda A, B, **kw: orig(A, B, **kw) + [cover(A, B)])


def _vf(gap, kind="VF"):
    """一个法锥有效、投影在面内、间隙为 gap 的 VF（或 FV）盖——几何上并不存在（夹具带内为空）。"""
    from eab.kernel3d.covers3 import Cover3

    def make(A, B):
        p = A.verts[4]                                  # 动块顶面一角：它对宿主任何面都不在 0 < |gap| ≤ 1 内
        if kind == "VF":
            return Cover3("VF", ("vertex", 4), ("face", 0), (0.0, 0.0, 1.0), gap, p, p, (), 1.0, True, True)
        return Cover3("FV", ("face", 0), ("vertex", 4), (0.0, 0.0, -1.0), gap, p, p, (), 1.0, True, True)
    return make


@pytest.mark.parametrize("kind", ["VF", "FV"])
@pytest.mark.parametrize("gap", [2e-6, 0.5, -0.5, 1.0], ids=["just_above_window", "mid", "mid_negative", "band_edge"])
def test_g2_gate_red_on_spurious_vf_cover_in_band(monkeypatch, gap, kind):
    """被放松的旧断言恢复成门：窗口 1.0 时代，|gap| ∈ (G2_WINDOW, 1.0] 的多余 VF/FV 盖会以 mine_only 报红；
    窗口收到 G2_WINDOW 后它们不进对账——现在由 band 报红。分界点：刚过窗口、带边 1.0（含），正负间隙。"""
    _inject(monkeypatch, _vf(gap, kind))
    res = compare(CASES[0])
    assert any(r["band"] for r in res["rows"])
    with pytest.raises(AssertionError, match="带内有多余的盖"):
        _assert_g2_gate(res)


def test_g2_band_edge_is_inclusive_and_nothing_beyond_is_reconciled(monkeypatch):
    """带的另一侧分界点：|gap| 刚过 G2_BAND 的 VF 盖不进带（与旧窗口 `abs(gap) <= 1.0` 同一口径）。"""
    _inject(monkeypatch, _vf(G2_BAND * (1 + 1e-12)))
    _assert_g2_gate(compare(CASES[0]))


def _box_vf_oracle(V, lim):
    """轴对齐长方体对的 VF/FV 暴力枚举（内联算术，不调 covers3/geom3——纪律 A）。

    顶点 v 的法锥（闭）= {d : s_k·d_k ≥ 0 ∀k}，s = v 相对块心的符号；面 (m, σ) 的外法向 σ·e_m。
    VF(a, 面 (m,σ) of B) 有效 ⟺ s^A_m = −σ；间隙 σ·(a_m − 面坐标)；投影在面内 ⟺ 另两坐标落在面的闭矩形内。
    FV(面 (m,σ) of A, b) 同理，间隙 σ·(b_m − A 的面坐标)。返回 {(种类, 顶点所在块, 顶点号, (面所在块, m, σ)): gap}。
    """
    out = {}
    lo = {k: [min(v[a] for v in vs) for a in range(3)] for k, vs in V.items()}
    hi = {k: [max(v[a] for v in vs) for a in range(3)] for k, vs in V.items()}
    for kind, vb, fb in (("VF", 2, 1), ("FV", 1, 2)):     # 动块 A = 2，宿主 B = 1；FV 的顶点在 B、面在 A
        for i, v in enumerate(V[vb]):
            s = [1 if v[a] > 0.5 * (lo[vb][a] + hi[vb][a]) else -1 for a in range(3)]
            for m in range(3):
                for sg in (1, -1):
                    if s[m] != -sg:
                        continue
                    plane = hi[fb][m] if sg == 1 else lo[fb][m]
                    gap = sg * (v[m] - plane)
                    if abs(gap) > lim:
                        continue
                    if all(lo[fb][a] - 1e-9 <= v[a] <= hi[fb][a] + 1e-9 for a in range(3) if a != m):
                        out[(kind, vb, i, (fb, m, sg))] = gap
    return out


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_band_is_geometrically_empty(path):
    """G2_BAND 注释里的几何理由钉成门：
      (1) 暴力枚举（上面的长方体 oracle）在 |gap| ≤ G2_BAND 内只给出零间隙坐落，恰是 legacy 的 4 条；
      (2) 内核的 VF/FV 盖在更宽的 |gap| ≤ 3 上与 oracle 逐条同集、同间隙（oracle 确实刻画了内核的有效性规则）；
      (3) G2_BAND 之外最近的 VF/FV 在 |gap| = 2.0——带边离它还有 1.0，不是刀口。
    前提：两块都是轴对齐长方体（断言）。
    """
    d = json.loads(path.read_text(encoding="utf-8"))
    V = {int(k): [tuple(v) for v in vs] for k, vs in d["verts"].items()}
    for vs in V.values():
        assert len(vs) == 8 and all(len({v[k] for v in vs}) == 2 for k in range(3))
    near = _box_vf_oracle(V, G2_BAND)
    assert len(near) == len(d["entrances"]) == 4 and set(near.values()) == {0.0}
    assert {(k[1], k[2]) for k in near} == {tuple(e["refs"][0]) for e in d["entrances"]}
    wide = _box_vf_oracle(V, 3.0)
    assert min(abs(g) for g in wide.values() if abs(g) > G2_BAND) == 2.0

    _, _, blocks, _ = load_case(path)
    A, B = blocks[2], blocks[1]

    def axis(n):
        m = max(range(3), key=lambda a: abs(n[a]))
        return m, (1 if n[m] > 0 else -1)
    mine = {}
    for c in enumerate_covers3(A, B, window=3.0, tol=1e-9):
        if not c.in_extent or c.kind not in ("VF", "FV"):
            continue
        if c.kind == "VF":
            mine[("VF", 2, c.a_feature[1], (1, *axis(B.face_normal(c.b_feature[1]))))] = c.gap
        else:
            mine[("FV", 1, c.b_feature[1], (2, *axis(A.face_normal(c.a_feature[1]))))] = c.gap
    assert set(mine) == set(wide)
    assert all(abs(mine[k] - wide[k]) < 1e-12 for k in wide)


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_geometry_details_match(path):
    """不只比集合：间隙与法向也要对上。cb2 是零间隙坐落，法向 +z。"""
    _, _, blocks, entrances = load_case(path)
    A, B = blocks[2], blocks[1]
    covs = [c for c in enumerate_covers3(A, B, window=G2_WINDOW, tol=1e-9)
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
    state = {"key": None}

    def lossy(A, ia, B, fb, tol=0.0, extent_tol=0.0):
        c = orig(A, ia, B, fb, tol, extent_tol)
        # 必须同时满足 in_extent **与窗口**才是会进最终清单的盖；
        # 只看 in_extent 会丢掉一个本来就被窗口滤掉的盖，门当然不会红（2026-09-20 踩过）。
        # 丢的是**同一个**（顶点, 面）——每次调用都丢，不按调用次数（compare 现在先做块对发现、再枚举，
        # "只丢第一次"会丢在发现阶段，2026-09-24 G6 minor 14 修复后踩到）。
        if c is not None and c.in_extent and abs(c.gap) <= G2_WINDOW:
            if state["key"] is None:
                state["key"] = (ia, fb)
            if state["key"] == (ia, fb):
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


# ---------------------------------------------------------------- 审查 C18：未被任何面引用的输入顶点

def _scaled(d, s):
    d["verts"] = {k: [[s * c for c in v] for v in vs] for k, vs in d["verts"].items()}


def _dup_append_moving(d):
    """动块 2 的顶点 0 复制成顶点 8，legacy 入口改用 8。"""
    d["verts"]["2"].append(list(d["verts"]["2"][0]))
    for e in d["entrances"]:
        if e["refs"][0] == [2, 0]:
            e["refs"][0] = [2, 8]


def _dup_prepend_moving(d):
    """动块 2 的顶点 3 复制到**下标 0**（其余顺移 +1）：重复者下标更低、成为规范号，
    原顶点（新号 4）反成 alias；legacy 仍引用 4，须经 alias 归并到 0。"""
    vs = d["verts"]["2"]
    d["verts"]["2"] = [list(vs[3])] + vs
    for e in d["entrances"]:
        e["refs"] = [[b, i + 1] if b == 2 else [b, i] for b, i in e["refs"]]


def _dup_host_face(d):
    """宿主块 1 的顶点 6 复制成 8，一条 legacy 三角改用 8。"""
    d["verts"]["1"].append(list(d["verts"]["1"][6]))
    e = d["entrances"][0]
    e["refs"] = [[b, 8] if [b, i] == [1, 6] else [b, i] for b, i in e["refs"]]


def _near_dup_moving(d):
    """近重复（1e-10 < tol=1e-9）：动块 2 的顶点 1 的近重复点作顶点 8。"""
    v = list(d["verts"]["2"][1])
    v[0] += 1e-10
    d["verts"]["2"].append(v)
    for e in d["entrances"]:
        if e["refs"][0] == [2, 1]:
            e["refs"][0] = [2, 8]


@pytest.mark.parametrize("scale", [1.0, 1e-3, 1e3], ids=["x1", "x1e-3", "x1e3"])
@pytest.mark.parametrize("mut", [_dup_append_moving, _dup_prepend_moving, _dup_host_face, _near_dup_moving],
                         ids=["dup_append_moving", "dup_prepend_moving", "dup_host_face", "near_dup_moving"])
def test_g2_duplicate_vertices_are_aliased_and_reconcile(tmp_path, mut, scale):
    """重复顶点（精确或 tol 内近重复、在动块或宿主块、重复者下标高于或低于原点）登记 alias，
    legacy 引用经 alias 归并后与几何上完全相同的干净夹具一样零差异（旧实现：假 legacy_only/mine_only）。"""
    p = _fake_case(tmp_path, lambda d: (_scaled(d, scale), mut(d)))     # 先缩放、后造重复：近重复偏移恒为 1e-10
    res = compare(p, band=G2_BAND * scale)                              # VF/FV 带随几何缩放
    _assert_g2_gate(res, band=G2_BAND * scale)
    for r in res["rows"]:
        assert len(r["mine"]) == len(r["legacy"]) == 4


@pytest.mark.parametrize("scale", [1.0, 1e-3, 1e3], ids=["x1", "x1e-3", "x1e3"])
@pytest.mark.parametrize("pt,kind", [
    ([0.0, -2.0, 0.0], "mid_edge"),       # 块 1 顶面前棱中点
    ([0.0, 0.0, -1.0], "mid_face"),       # 块 1 底面中心
    ([0.3, 0.2, -0.5], "interior"),       # 块 1 内部
])
def test_g2_non_corner_vertex_is_a_clear_error(tmp_path, pt, kind, scale):
    """既非凸包角点、也不在 tol 内重复任何角点的输入顶点（T 形顶点 / 内点）：
    构造多面体时报 ValueError，带块号、顶点号与分类——不许静默保留、也不许到 compare 里撞裸 assert。"""
    want = {"mid_edge": "mid-edge T-junction", "mid_face": "mid-face T-junction", "interior": "interior"}[kind]

    def add(d):
        _scaled(d, scale)
        d["verts"]["1"].append([scale * c for c in pt])
        if kind == "mid_edge":
            e = d["entrances"][0]
            e["refs"] = [e["refs"][0], [1, 4], [1, 8], [1, 5]]
    with pytest.raises(ValueError, match=r"block 1\b.*vertex 8\b.*" + want):
        compare(_fake_case(tmp_path, add))


def test_polyhedron_aliases_leave_no_input_vertex_silently_unreferenced():
    """每个输入顶点要么被某个面引用，要么被显式登记为某个被引用顶点的 alias（审查 C18 的 near-dup 复现）。"""
    from g2_bdda3d import polyhedron_with_aliases
    pts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1e-10, 0.0, 0.0)]
    P, alias = polyhedron_with_aliases(pts, block=7)
    ref = {i for f in P.faces for i in f}
    assert ref == {0, 1, 2, 3}
    assert alias == {4: 0}
    assert ref | set(alias) == set(range(len(pts)))
    assert P.verts == pts                                     # 编号原样保留


# ---------------------------------------------------------------- 窗口的理由（纪律 C：陈述要有门）

def _sub3(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _seg_seg_dist(p1, q1, p2, q2):
    """闭线段间距离（Ericson《Real-Time Collision Detection》§5.1.9 的夹紧解），只用内联算术。"""
    def clamp(x):
        return min(max(x, 0.0), 1.0)
    d1, d2, r = _sub3(q1, p1), _sub3(q2, p2), _sub3(p1, p2)
    a, e, f = _dot3(d1, d1), _dot3(d2, d2), _dot3(d2, r)
    if a <= 1e-300 and e <= 1e-300:
        s = t = 0.0
    elif a <= 1e-300:                                   # 第一段退化为点
        s, t = 0.0, clamp(f / e)
    else:
        c = _dot3(d1, r)
        if e <= 1e-300:                                 # 第二段退化为点
            s, t = clamp(-c / a), 0.0
        else:
            b = _dot3(d1, d2)
            den = a * e - b * b
            s = clamp((b * f - c * e) / den) if den > 1e-300 else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, clamp(-c / a)
            elif t > 1.0:
                t, s = 1.0, clamp((b - c) / a)
    c1 = (p1[0] + d1[0] * s, p1[1] + d1[1] * s, p1[2] + d1[2] * s)
    c2 = (p2[0] + d2[0] * t, p2[1] + d2[1] * t, p2[2] + d2[2] * t)
    w = _sub3(c1, c2)
    return _dot3(w, w) ** 0.5


def _box_edges(vs):
    """轴对齐长方体的 12 条棱：恰有一个坐标不同的顶点对（前提由调用方断言）。"""
    return [(vs[i], vs[j]) for i in range(8) for j in range(i + 1, 8)
            if sum(vs[i][k] != vs[j][k] for k in range(3)) == 1]


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_window_contains_every_legacy_gap_and_nothing_else(path):
    """`G2_WINDOW` 的理由钉成门：
      (1) legacy 每个 np 入口的几何间隙（顶点到所指三角所在平面的距离）≤ 窗口——legacy 侧全进得来；
      (2) 窗口 ≪ 夹具里任何"非面接触"特征对的距离（顶点-棱段、棱段-棱段的最小值）——窗口内几何上
          只可能出现 VF/FV 盖。所以门在窗口内对任何多出的盖都会红（见 EE 注入的牙测试），却不会因为
          低维盖（VE3/EV3/VV3）strict 过滤的去留而误红——M0.b 计划删除那道过滤门，本门对它稳健。
    oracle：点-平面、线段-线段距离全用内联算术，不调 covers3 / geom3（纪律 A）。前提：两块都是轴对齐长方体。
    """
    d = json.loads(path.read_text(encoding="utf-8"))
    V = {int(k): [tuple(v) for v in vs] for k, vs in d["verts"].items()}
    for vs in V.values():
        assert len(vs) == 8 and all(len({v[k] for v in vs}) == 2 for k in range(3))
    gaps = []
    for e in d["entrances"]:
        (vb, vi), *tri = e["refs"]
        a, b, c = (V[bb][ii] for bb, ii in tri)
        u, w = _sub3(b, a), _sub3(c, a)
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        gaps.append(abs(_dot3(n, _sub3(V[vb][vi], a))) / _dot3(n, n) ** 0.5)
    A, B = V[2], V[1]
    non_face = min([_seg_seg_dist(p, p, *eb) for p in A for eb in _box_edges(B)]
                   + [_seg_seg_dist(p, p, *ea) for p in B for ea in _box_edges(A)]
                   + [_seg_seg_dist(*ea, *eb) for ea in _box_edges(A) for eb in _box_edges(B)])
    assert max(gaps) <= G2_WINDOW
    assert non_face == pytest.approx(1.0, abs=1e-12)          # cb2：上块底角到下块顶棱，最近也有 1
    assert G2_WINDOW <= 1e-3 * non_face


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_band_catches_a_real_kernel_defect_through_enumeration(path, monkeypatch):
    """带的牙必须**穿过枚举器**：在内核里打一个真缺陷，而不是在枚举之后追加假盖。

    缺陷 = 顶点法锥判据恒返回"边界"（0）。于是 vf_cover 对本不该有效的顶点-面对也产盖，
    cb2 上在 |gap| = 1.0 处冒出假 VF 盖——只有当 compare() 真的把枚举窗口伸到带宽时，
    它们才进得了 band。复核实测：把 compare() 的枚举窗口改回 `window=window`，旧的注入测试
    （都是枚举后追加）全绿、整套 460 全绿，而本测试会红（该变异下 band 恒空，门不报警）。
    """
    import eab.kernel3d.covers3 as cv
    monkeypatch.setattr(cv, "vertex_cone_contains", lambda P, vi, d, tol=0.0: 0)
    res = compare(path)
    assert any(r["band"] for r in res["rows"]), "内核缺陷产出的带内假盖没有进入 band"
    with pytest.raises(AssertionError):
        _assert_g2_gate(res)


# ---------------------------------------------------------------- G6 minor 14：legacy 没列出的块对也要进对账

def _third_block_on_top(d):
    """块 3 = 块 2 上移 1（z），零间隙坐落在块 2 顶面上；legacy 对 (3,2) 一条入口都没有。"""
    d["verts"]["3"] = [[x, y, z + 1.0] for x, y, z in d["verts"]["2"]]


def test_g2_pair_seen_only_by_the_kernel_is_red(tmp_path):
    """G6 minor 14：旧 compare 的块对只取自 legacy 入口，(3,2) 上内核有 16 个带内盖（8 个零间隙 VF/FV + EE），
    门照绿。现在块对 = legacy 块对 ∪ 内核在枚举窗口内有盖的块对；legacy 为空的行必红。"""
    res = compare(_fake_case(tmp_path, _third_block_on_top))
    rows = {tuple(r["pair"]): r for r in res["rows"]}
    assert (3, 2) in rows, sorted(rows)
    assert rows[(3, 2)]["legacy"] == [] and rows[(3, 2)]["mine_only"], rows[(3, 2)]["mine_only"]
    with pytest.raises(AssertionError, match="legacy 侧为空"):
        _assert_g2_gate(res)


_PAIRS_WINDOW_MUTANT = ("kernel_pairs(blocks, max(window, band), tol)", "kernel_pairs(blocks, window, tol)")


@pytest.mark.parametrize("gap", [0.5, 1.0])
def test_g2_pair_seen_only_in_the_band_is_red(tmp_path, gap):
    """G6 第二轮 minor：块对并集里"内核在**带内**有盖"那一半（kernel_pairs 用 max(window, band)）没有门——上面的例子
    是零间隙，窗口 1e-6 也看得见。块 3 悬在块 2 上方 gap（0 < gap ≤ 带宽 1）：legacy 为空、只有带内盖，门必须红；
    把块对枚举窗口改回 window 的变异（G6 复核实测全套照绿）下 (3,2) 从对账里消失——同一夹具上一并断言。"""
    def lift(d):
        d["verts"]["3"] = [[x, y, z + 1.0 + gap] for x, y, z in d["verts"]["2"]]
    case = _fake_case(tmp_path, lift)
    rows = {tuple(r["pair"]): r for r in compare(case)["rows"]}
    assert (3, 2) in rows and rows[(3, 2)]["legacy"] == [] and rows[(3, 2)]["band"], sorted(rows)
    with pytest.raises(AssertionError, match="legacy 侧为空"):
        _assert_g2_gate(compare(case))
    mutant_rows = {tuple(r["pair"]) for r in _mutant_g2(*_PAIRS_WINDOW_MUTANT).compare(case)["rows"]}
    assert (3, 2) not in mutant_rows, sorted(mutant_rows)


def test_g2_pair_outside_the_band_is_not_reconciled(tmp_path):
    """对照：块 3 悬在块 2 上方 1.5（带外），(3,2) 不进对账，门不因它报红。"""
    def lift(d):
        d["verts"]["3"] = [[x, y, z + 2.5] for x, y, z in d["verts"]["2"]]
    res = compare(_fake_case(tmp_path, lift))
    assert (3, 2) not in {tuple(r["pair"]) for r in res["rows"]}
    _assert_g2_gate(res)


# ---------------------------------------------------------------- G6 minor 29：带收所有盖类 + 带内无贯入

def _low_dim(kind, gap):
    from eab.kernel3d.covers3 import Cover3

    def make(A, B):
        p = A.verts[0]
        fa = {"VE3": ("vertex", 0), "EV3": ("edge", 0, 1), "VV3": ("vertex", 0), "EE": ("edge", 0, 1)}[kind]
        fb = {"VE3": ("edge", 4, 5), "EV3": ("vertex", 5), "VV3": ("vertex", 5), "EE": ("edge", 4, 5)}[kind]
        return Cover3(kind, fa, fb, (1.0, 0.0, 0.0), gap, p, p, (), None, True, True)
    return make


@pytest.mark.parametrize("gap", [1.0, -1.0, 0.5, -1e-3, 2e-6], ids=["gap_1", "gap_-1", "gap_0.5", "pen_1e-3", "just_above_window"])
@pytest.mark.parametrize("kind", ["VE3", "EV3", "VV3", "EE"])
def test_g2_band_catches_every_cover_kind(monkeypatch, kind, gap):
    """G6 minor 29（反转旧的 test_g2_band_ignores_low_dim_covers_at_gap_one）：旧注释说"低维盖在 gap 1.0 合法存在
    （cb2 上块底角到下块顶棱 = 1.0）"——是错的：正确内核在三份夹具上一个低维盖都不出、|gap| ≤ 1 的在程 EE 也没有
    （test_g2_band_is_geometrically_empty 钉着）。所以带收**所有**盖类，带内任何盖都红；负间隙另进 `penetration`。"""
    _inject(monkeypatch, _low_dim(kind, gap))
    res = compare(CASES[0])
    assert any(r["band"] for r in res["rows"])
    assert any(r["penetration"] for r in res["rows"]) == (gap < 0)
    with pytest.raises(AssertionError, match="带内有多余的盖"):
        _assert_g2_gate(res)


def test_g2_penetration_is_its_own_verdict(monkeypatch):
    """带内无贯入单独断言：把带的判据关掉（band 恒空）时，负间隙盖仍由 penetration 报红。"""
    _inject(monkeypatch, _low_dim("EE", -0.25))
    res = compare(CASES[0])
    for r in res["rows"]:
        r["band"] = []
    with pytest.raises(AssertionError, match="带内有贯入"):
        _assert_g2_gate(res)


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_edge_arc_defect_turns_the_gate_red(path, monkeypatch):
    """G6 minor 29 的复现钉成牙（缺陷在内核里，穿过枚举器）：edge_arc_contains 恒 0 时内核在窗口 1.0 内吐出
    EE −1.0 ×6、EE +1.0 ×2、VE3 1.0 ×8——旧门（带只收 VF/FV）三份夹具全绿。"""
    import eab.kernel3d.covers3 as cv
    monkeypatch.setattr(cv, "edge_arc_contains", lambda *a, **k: 0)
    res = compare(path)
    kinds = {b[0] for r in res["rows"] for b in r["band"]}
    assert {"EE", "VE3"} <= kinds, kinds
    with pytest.raises(AssertionError):
        _assert_g2_gate(res)


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_band_is_empty_for_every_cover_kind(path):
    """正确内核在 (G2_WINDOW, G2_BAND] 上**任何种类**的在程盖都没有（不止 VF/FV）；放宽到 require_in_extent=False
    也没有低维盖——旧注释"低维盖在 1.0 处合法存在"的反证。"""
    _, _, blocks, _ = load_case(path)
    A, B = blocks[2], blocks[1]
    inb = [(c.kind, c.gap) for c in enumerate_covers3(A, B, window=G2_BAND, tol=1e-9)
           if c.in_extent and G2_WINDOW < abs(c.gap) <= G2_BAND]
    assert inb == []
    allk = {c.kind for c in enumerate_covers3(A, B, window=3.0, tol=1e-9)}
    assert not allk & {"VE3", "EV3", "VV3"}, allk


# ---------------------------------------------------------------- G6 minor 25：enumerated_window 不许是同义反复

def _mutant_g2(old: str, new: str):
    """对 tools/g2_bdda3d.py 做一处源码替换（断言恰好命中一次），编译成独立模块返回。"""
    import types
    src = (ROOT / "tools" / "g2_bdda3d.py").read_text(encoding="utf-8")
    assert src.count(old) == 1, ("mutation site must match exactly once", old)
    mod = types.ModuleType("g2_bdda3d_mutant")
    mod.__file__ = str(ROOT / "tools" / "g2_bdda3d.py")
    exec(compile(src.replace(old, new), mod.__file__, "exec"), mod.__dict__)
    return mod


def test_g2_enumerated_window_is_read_off_the_actual_enumeration():
    """G6 minor 25：旧 compare 记 enumerated_window = max(window, band)（局部变量的回声），把传给枚举器的窗口改回
    `window=window`，第 76 行那条断言永不触发（G6 实测 0 次）。现在记录值取自枚举器实际收到的参数——同一个变异
    必须让**那条**断言红（不是别的断言碰巧红）。"""
    mod = _mutant_g2("window=ewin, tol=tol)", "window=window, tol=tol)")
    res = mod.compare(CASES[0])
    assert all(r["enumerated_window"] == G2_WINDOW for r in res["rows"]), [r["enumerated_window"] for r in res["rows"]]
    with pytest.raises(AssertionError, match="枚举窗口窄于带宽"):
        _assert_g2_gate(res)


# ---------------------------------------------------------------- G6 minor 22：机器报告不许过期

def test_g2_committed_report_equals_the_live_comparison():
    """reports/g2_bdda3d.json 必须等于当前 compare() 在三份夹具上的输出（G6 minor 22：旧文件停在 6934694，
    记着 6 个盖、重复 VF 行、没有 window/band 字段）。重生成：python tools/g2_bdda3d.py。"""
    committed = json.loads((ROOT / "reports" / "g2_bdda3d.json").read_text(encoding="utf-8"))
    live = json.loads(json.dumps([compare(p) for p in CASES], indent=1, default=str))
    assert committed == live


# ---------------------------------------------------------------- 纪律 F：G2 门在刚体运动 + 换单位下不变

def _rot3(seed):
    import math
    import random
    rng = random.Random(seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(x * x for x in q))
    a, b, c, d = (x / n for x in q)
    R = [[a * a + b * b - c * c - d * d, 2 * (b * c - a * d), 2 * (b * d + a * c)],
         [2 * (b * c + a * d), a * a - b * b + c * c - d * d, 2 * (c * d - a * b)],
         [2 * (b * d - a * c), 2 * (c * d + a * b), a * a - b * b - c * c + d * d]]
    u = [rng.gauss(0.0, 1.0) for _ in range(3)]
    nu = math.sqrt(sum(x * x for x in u))
    return R, [x / nu for x in u]


_R3, _DIR3 = _rot3(20260924)
_NEEDS_GEOM = pytest.mark.xfail(strict=True, reason=(
    "needs m2-geom: G6 confirmed[6] (covers3 cone tests compare unit vectors against the caller's length tol with no "
    "c*eps*C/l rounding floor -- vertex_cone_contains covers3.py:53-64 has the same pattern as edge_arc_contains:80); "
    "face-face contact VF covers sit on the cone boundary and are dropped once coordinates carry eps*C noise. "
    "Verified 2026-09-24: adding a c*eps*C/l floor to those two predicates alone turns all six cells green."))
G2_MOTIONS = [pytest.param(s, tm, id=f"s{s:g}_t{tm:g}", marks=[])
              for s in (1e-3, 1.0, 1e3) for tm in (0.0, 1e3, 1e5)]


def _moved(d, s, tm):
    d["verts"] = {k: [[s * sum(_R3[i][j] * v[j] for j in range(3)) + tm * _DIR3[i] for i in range(3)] for v in vs]
                  for k, vs in d["verts"].items()}


def _row_digest(r, blocks):
    """行摘要。键 (动块, 顶点, 面号) 里的**面号**是凸包的枚举序，不是物理量：m2-geom 换成 Quickhull 后
    面的排列随坐标变化（2026-09-27 合并时实测 cb2 顶面在恒等与 ×1e3 下分别是 5 号与 4 号）。所以面号换成
    该面的**顶点集合**——夹具顶点编号在刚体运动与缩放下保持不变，这才是可比的身份。"""
    def canon(keys, pair):
        out = []
        for vblk, vidx, gi in keys:
            host = pair[1] if vblk == pair[0] else pair[0]
            out.append((vblk, vidx, tuple(sorted(blocks[host].faces[gi]))))
        return sorted(out)
    pair = tuple(r["pair"])
    return (pair, canon(r["legacy"], pair), canon(r["mine"], pair), r["n_covers"], len(r["band"]),
            len(r["penetration"]), len(r["violations"]))


@pytest.mark.parametrize("s,tm", G2_MOTIONS)
@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_g2_gate_is_invariant_under_rigid_motion_and_units(tmp_path, path, s, tm):
    """夹具整体随机旋转（固定种子、非轴对齐）× 平移 |t| ∈ {0, 1e3, 1e5} × 单位缩放 s ∈ {1e-3, 1, 1e3}；
    窗口、带、容差随单位缩放。门必须照绿，块对、legacy/内核键、盖数、带/贯入/违规计数与恒等变换逐项相同。
    b6468f3 上 s=1e-3、|t| ≥ 1e3 六格全红（共面归并在原点系里量平面偏移，顶面两片三角不归并，面号错位）；
    本组修了拓扑那一半（凸包/归并挪到块局部坐标、容差抬到舍入下限），剩下的是内核 covers3 的法锥判据没有舍入下限
    （面-面坐落的 VF 盖卡在锥边界上），属 m2-geom——六格曾标 strict xfail。2026-09-27 合并：m2-geom 的 angular_floor
    已补上，xfail 标记摘除；合并时另发现摘要用面号（凸包枚举序）不可比，改用面的顶点集合（见 _row_digest）。"""
    ref = [_row_digest(r, load_case(path)[2]) for r in compare(path)["rows"]]
    d = json.loads(path.read_text(encoding="utf-8"))
    _moved(d, s, tm)
    p = tmp_path / f"{path.stem}_moved.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    res = compare(p, window=G2_WINDOW * s, band=G2_BAND * s, tol=1e-9 * s)
    _assert_g2_gate(res, band=G2_BAND * s)
    assert [_row_digest(r, load_case(p)[2]) for r in res["rows"]] == ref


@pytest.mark.parametrize("C,h", [(0.0, 1e-6), (1e5, 1e-6), (1e6, 1e-5)])
@pytest.mark.parametrize("rot", [0, 3, 11])
def test_polyhedron_with_aliases_keeps_a_small_chamfer_at_any_coordinate_magnitude(C, h, rot):
    """G6 第三轮 minor：1 km 立方体一个角削去 h 的倒角（10 顶点 7 面）：旧版把绝对地板当相对容差传给凸包，C = 1e5 时倒角
    顶点被吸进厚平面带、再被当"非凸包角点"抛错。第四轮 minor：一般旋转后共面归并在局部坐标里低估法向噪声，返回 8～10 面——
    归并改在原坐标做；这里加一般旋转格（rot = 0 为恒等）。"""
    import math
    import random
    from g2_bdda3d import polyhedron_with_aliases
    L = 1000.0
    pts = [(0, 0, 0), (L, 0, 0), (L, L, 0), (0, L, 0), (0, 0, L), (L, 0, L), (L - h, L, L), (0, L, L), (L, L - h, L), (L, L, L - h)]
    if rot:
        rng = random.Random(9100 + rot)
        q = [rng.gauss(0.0, 1.0) for _ in range(4)]
        n = math.sqrt(sum(c * c for c in q))
        w, x, y, z = (c / n for c in q)
        R = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
             (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
             (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
        pts = [tuple(sum(R[i][j] * p[j] for j in range(3)) for i in range(3)) for p in pts]
    pts = [(x + C, y + C, z + C) for x, y, z in pts]
    P, _ = polyhedron_with_aliases(pts, block=1)
    assert len(P.faces) == 7 and P.manifold_issues() == []
