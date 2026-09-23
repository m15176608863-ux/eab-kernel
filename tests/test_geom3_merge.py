"""`merge_coplanar` 的邻接判定——审查 C8（major）。

缺陷：只按支撑平面分组、不看是否共棱，然后把边界边塞进 `boundary[a] = b` 的普通字典、
用无界的 `while cur != start` 走环。两种合法闭流形因此出错：
  (a) 两个共面面只在一个顶点相触（pinch）：字典静默丢掉一条出边，走环**死循环**；
  (b) 两个共面但不共棱的面（U 形棱柱两个端面）被强行归并，抛"多于一个边界环"。
修法：平面组内按**共棱**做并查集分连通分量，各分量分别归并；分量内若仍有 pinch（洞贴着外边界）
或多环（面上有洞）——这种区域不是简单多边形，Polyhedron 表示不了——**明确报错**，且走环有步数上界。

所有调用都经 `_call_with_timeout`：旧实现会死循环，门本身绝不能挂死。

oracle（纪律 A）：期望的归并结果是**构造时就知道的原始多边形环**（先造多边形面、再三角化、
再归并回去），以及闭式体积；比较只用整数下标与算术。流形自检 `manifold_issues` 是 geom3 的
拓扑计数，与 merge_coplanar 的实现不共享代码路径。
纪律 B：分界（单点相触 pinch、完全不相触、共棱）、一般位置（随机旋转）、尺度 ×1e-3 / ×1 / ×1e3。
"""

import math
import random
import threading

import pytest

from eab.kernel3d.geom3 import Polyhedron, convex_hull_3d, merge_coplanar, box

SCALES = [1e-3, 1.0, 1e3]


def _call_with_timeout(fn, *args, timeout: float = 20.0):
    """在守护线程里跑；超时即判红（旧实现死循环时线程会一直占着，但测试进程照常结束）。"""
    box_ = {}

    def run():
        try:
            box_["value"] = fn(*args)
        except BaseException as exc:  # noqa: BLE001 — 原样转交给主线程
            box_["error"] = exc

    th = threading.Thread(target=run, daemon=True)
    th.start()
    th.join(timeout)
    if th.is_alive():
        raise AssertionError(f"{getattr(fn, '__name__', fn)} did not return within {timeout} s (hang)")
    if "error" in box_:
        raise box_["error"]
    return box_["value"]


def _rotation(seed: int):
    if seed == 0:
        return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rng = random.Random(3000 + seed)
    q = [rng.gauss(0.0, 1.0) for _ in range(4)]
    n = math.sqrt(sum(c * c for c in q))
    w, x, y, z = (c / n for c in q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def _place(verts, seed: int, scale: float):
    R = _rotation(seed)
    o = (0.0, 0.0, 0.0) if seed == 0 else (0.7 * scale, -1.9 * scale, 2.3 * scale)
    return [tuple(o[i] + scale * (R[i][0] * p[0] + R[i][1] * p[1] + R[i][2] * p[2]) for i in range(3))
            for p in verts]


def _canon(ring):
    k = ring.index(min(ring))
    return tuple(ring[k:] + ring[:k])


def _face_set(P):
    return sorted(_canon(list(f)) for f in P.faces)


def _prism_faces(n):
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return faces


def _prism_verts(base, h=1.0):
    return [(float(x), float(y), 0.0) for x, y in base] + [(float(x), float(y), h) for x, y in base]


def _triangulate(poly_faces, top_tris, n):
    """把棱柱的顶/底多边形按给定三角化拆开，侧面四边形各拆两个三角——同一几何、不同网格。"""
    out = []
    out += [(n + a, n + b, n + c) for a, b, c in top_tris]               # 顶面 CCW（外法向 +z）
    out += [(c, b, a) for a, b, c in top_tris]                            # 底面反向
    for f in poly_faces[2:]:
        i, j, jn, iN = f
        out += [(i, j, jn), (i, jn, iN)]
    return out


U_BASE = [(0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)]
U_TRIS = [(1, 2, 3), (1, 3, 4), (0, 1, 4), (0, 4, 5), (0, 5, 7), (5, 6, 7)]
L_BASE = [(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)]
L_TRIS = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5)]


# ---------------------------------------------------------------- 审查原例

def _dented_block():
    V = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0), (0, 0, 1), (1, 0, 1), (2, 0, 1), (2, 1, 1), (2, 2, 1),
         (1, 2, 1), (0, 2, 1), (0, 1, 1), (1, 1, 1), (1.5, 0.5, 0.5), (0.5, 1.5, 0.5)]
    F = [(0, 3, 2, 1), (4, 5, 12, 11), (12, 7, 8, 9), (0, 1, 6, 5, 4), (1, 2, 8, 7, 6), (2, 3, 10, 9, 8),
         (3, 0, 4, 11, 10), (5, 6, 13), (6, 7, 13), (7, 12, 13), (12, 5, 13), (11, 12, 14), (12, 9, 14),
         (9, 10, 14), (10, 11, 14)]
    return [tuple(float(c) for c in p) for p in V], F


@pytest.mark.parametrize("seed,scale", [(0, 1.0), (1, 1e-3), (2, 1e3)])
def test_vertex_pinched_coplanar_faces_do_not_hang(seed, scale):
    """(a) 顶面两块共面方片只在顶点 12 相触（其余两个象限是凹坑）：旧实现死循环。
    两片不共棱 ⇒ 不应归并；结果与输入逐面相同。"""
    V, F = _dented_block()
    P = Polyhedron(_place(V, seed, scale), F)
    assert P.manifold_issues() == []
    M = _call_with_timeout(merge_coplanar, P)
    assert _face_set(M) == _face_set(P)
    assert M.volume() == pytest.approx(11.0 / 3.0 * scale ** 3, rel=1e-12)
    assert M.manifold_issues() == []


@pytest.mark.parametrize("seed,scale", [(0, 1.0), (1, 1e-3), (2, 1e3)])
def test_u_prism_prong_ends_stay_separate(seed, scale):
    """(b) U 形棱柱两个端面（y=3）共面但不共棱：旧实现强行归并后抛 ValueError。"""
    P = Polyhedron(_place(_prism_verts(U_BASE), seed, scale), _prism_faces(8))
    assert P.manifold_issues() == []
    M = _call_with_timeout(merge_coplanar, P)
    assert _face_set(M) == _face_set(P)
    assert M.volume() == pytest.approx(7.0 * scale ** 3, rel=1e-12)
    assert M.manifold_issues() == []


# ---------------------------------------------------------------- 三角化 → 归并回原多边形

@pytest.mark.parametrize("seed,scale", [(0, s) for s in SCALES] + [(1, 1.0), (2, 1e3)])
@pytest.mark.parametrize("name", ["U", "L"])
def test_triangulated_concave_prism_merges_back_to_its_polygons(name, seed, scale):
    base, tris = (U_BASE, U_TRIS) if name == "U" else (L_BASE, L_TRIS)
    n = len(base)
    poly_faces = _prism_faces(n)
    V = _place(_prism_verts(base), seed, scale)
    T = Polyhedron(V, _triangulate(poly_faces, tris, n))
    assert T.manifold_issues() == []
    M = _call_with_timeout(merge_coplanar, T)
    assert _face_set(M) == _face_set(Polyhedron(V, poly_faces))       # 恰好回到原来的多边形面
    area = 7.0 if name == "U" else 5.0
    assert M.volume() == pytest.approx(area * scale ** 3, rel=1e-12)
    assert M.manifold_issues() == []
    if name == "U":                                                     # 两个端面各自保留
        ends = [f for f in M.faces if len(f) == 4 and all(abs(_unplace_y(V[i], seed, scale) - 3.0) < 1e-9
                                                          for i in f)]
        assert len(ends) == 2


def _unplace_y(p, seed, scale):
    R = _rotation(seed)
    o = (0.0, 0.0, 0.0) if seed == 0 else (0.7 * scale, -1.9 * scale, 2.3 * scale)
    d = tuple(p[i] - o[i] for i in range(3))
    return sum(R[i][1] * d[i] for i in range(3)) / scale


def test_triangulated_box_still_merges_to_six():
    M = _call_with_timeout(merge_coplanar, convex_hull_3d(box().verts))
    assert len(M.faces) == 6 and M.manifold_issues() == []


# ---------------------------------------------------------------- 分量内 pinch：明确报错，不挂死

def _pocketed_slab(dents=frozenset({(1, 1), (0, 2)})):
    """3×3 网格顶面，dents 里的格是向下的金字塔凹坑，其余格平顶。
    默认 (1,1) 与 (0,2)：7 个平顶格**共棱连通**，而两个凹坑在 (1,2) 顶点处相触 ⇒ 平顶区域的
    边界在 (1,2) 处 pinch（一个贴着外边界的洞），不是简单多边形。"""
    V = [(float(i), float(j), 1.0) for i in range(4) for j in range(4)]          # idx = 4i + j
    T = lambda i, j: 4 * i + j                                                    # noqa: E731
    b = [(0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (3.0, 3.0, 0.0), (0.0, 3.0, 0.0)]
    b0 = len(V)
    V += b
    faces = [(b0, b0 + 3, b0 + 2, b0 + 1)]                                        # 底面 −z
    for i in range(3):
        for j in range(3):
            c = [T(i, j), T(i + 1, j), T(i + 1, j + 1), T(i, j + 1)]              # 俯视 CCW
            if (i, j) in dents:
                V.append((i + 0.5, j + 0.5, 0.5))
                ap = len(V) - 1
                faces += [(c[k], c[(k + 1) % 4], ap) for k in range(4)]
            else:
                faces.append(tuple(c))
    faces.append((b0, b0 + 1) + tuple(T(i, 0) for i in (3, 2, 1, 0)))           # y = 0
    faces.append((b0 + 1, b0 + 2) + tuple(T(3, j) for j in (3, 2, 1, 0)))       # x = 3
    faces.append((b0 + 2, b0 + 3) + tuple(T(i, 3) for i in (0, 1, 2, 3)))       # y = 3
    faces.append((b0 + 3, b0) + tuple(T(0, j) for j in (0, 1, 2, 3)))           # x = 0
    return Polyhedron(V, faces)


def test_pinch_inside_an_edge_connected_group_raises_clearly():
    P = _pocketed_slab()
    assert P.manifold_issues() == [], P.manifold_issues()
    with pytest.raises(ValueError, match="pinch"):
        _call_with_timeout(merge_coplanar, P)


def test_hole_inside_an_edge_connected_group_raises_clearly():
    """只挖中心格：平顶 8 格成环，边界是两个互不相触的环（面上有洞）——同样表示不了，明确报错。"""
    P = _pocketed_slab(frozenset({(1, 1)}))
    assert P.manifold_issues() == [], P.manifold_issues()
    with pytest.raises(ValueError, match="more than one boundary ring"):
        _call_with_timeout(merge_coplanar, P)


def test_pocketed_slab_with_separate_dents_merges_what_it_can():
    """对照：两个凹坑互不相触且都不孤立平顶区——(0,0) 与 (2,2) 挖掉，其余 7 格仍是简单多边形。"""
    P = _pocketed_slab(frozenset({(0, 0), (2, 2)}))
    assert P.manifold_issues() == []
    M = _call_with_timeout(merge_coplanar, P)
    assert M.manifold_issues() == []
    assert M.volume() == pytest.approx(P.volume(), rel=1e-12)
    top = [f for f in M.faces if all(M.verts[i][2] == 1.0 for i in f)]
    assert len(top) == 1 and len(top[0]) == 12      # 7 格之并的边界环：12 个网格点（含共线顶点）
