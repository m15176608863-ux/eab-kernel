"""互锁块几何生成器：osteomorphic（骨形）块——拓扑互锁结构（TIA）的原型块。

Dyskin/Estrin 一族的 osteomorphic 块：两组相对的面是**相互补的曲面**（一凸一凹），
使块只能沿特定方向组装、组装后彼此约束。这是 04 号文档判为首选方向（TIA）的对象，
也是 Phase 3 凹块内核的第一个真实算例——它的凹几何没有 legacy 可对，只能靠 G0 自证。

本文件用**分段平面**近似曲面（每方向 n 段），得到真正的凹多面体（有反射棱），
参数化程度足以做界面几何的灵敏度/优化（TIA 论文的核心量）。
"""

from __future__ import annotations

from math import pi, sin

from eab.kernel3d.geom3 import Polyhedron, Vec3


def osteomorphic_block(nx: int = 4, ny: int = 4, *, lx: float = 2.0, ly: float = 1.0,
                       lz: float = 1.0, amp: float = 0.25, center: Vec3 = (0.0, 0.0, 0.0),
                       phase: float = 0.0) -> Polyhedron:
    """骨形块：顶/底面为沿 x 起伏的互补曲面（顶凸则底凹），侧面竖直。

    顶面高度  z = +lz/2 + amp·sin(2π·u + phase)
    底面高度  z = −lz/2 + amp·sin(2π·u + phase)      （同相位 ⇒ 上下互补，可堆叠咬合）
    其中 u = (x + lx/2)/lx ∈ [0,1]。amp=0 退化为长方体（可作对照）。

    nx 段沿 x、ny 段沿 y；顶底各 (nx+1)×(ny+1) 个网格点，侧面由边界网格线构成。
    """
    cx, cy, cz = center
    top: list[list[int]] = []
    bot: list[list[int]] = []
    verts: list[Vec3] = []

    def add(p: Vec3) -> int:
        verts.append(p)
        return len(verts) - 1

    for i in range(nx + 1):
        u = i / nx
        x = cx - lx / 2 + lx * u
        h = amp * sin(2 * pi * u + phase)
        row_t: list[int] = []
        row_b: list[int] = []
        for j in range(ny + 1):
            y = cy - ly / 2 + ly * (j / ny)
            row_t.append(add((x, y, cz + lz / 2 + h)))
            row_b.append(add((x, y, cz - lz / 2 + h)))
        top.append(row_t)
        bot.append(row_b)

    faces: list[tuple[int, ...]] = []
    # 顶面：外法向 +z ⇒ 从上方看逆时针
    for i in range(nx):
        for j in range(ny):
            faces.append((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
    # 底面：外法向 −z ⇒ 反向
    for i in range(nx):
        for j in range(ny):
            faces.append((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    # 侧面 y = −ly/2（外法向 −y）与 y = +ly/2（外法向 +y）
    for i in range(nx):
        faces.append((bot[i][0], bot[i + 1][0], top[i + 1][0], top[i][0]))
        faces.append((bot[i + 1][ny], bot[i][ny], top[i][ny], top[i + 1][ny]))
    # 端面 x = −lx/2（外法向 −x）与 x = +lx/2（外法向 +x）
    # 绕向按右手法则核过：+y 再 −z 给 −x；−y 再 −z 给 +x（manifold_issues 是这条的门）
    for j in range(ny):
        faces.append((top[0][j], top[0][j + 1], bot[0][j + 1], bot[0][j]))
        faces.append((top[nx][j + 1], top[nx][j], bot[nx][j], bot[nx][j + 1]))
    return Polyhedron(verts, faces)


def interlocking_pair(**kw) -> tuple[Polyhedron, Polyhedron]:
    """一对可咬合的骨形块：上块 = 下块沿 +z 抬升 lz（同相位 ⇒ 面面互补贴合）。"""
    lz = kw.get("lz", 1.0)
    lower = osteomorphic_block(**kw)
    upper_kw = dict(kw)
    c = kw.get("center", (0.0, 0.0, 0.0))
    upper_kw["center"] = (c[0], c[1], c[2] + lz)
    upper = osteomorphic_block(**upper_kw)
    return upper, lower


def osteomorphic_block_generic(nx: int = 4, ny: int = 4, *, lx=2.0, ly=1.0, lz=1.0,
                               amp=0.25, center=(0.0, 0.0, 0.0), phase=0.0, sin_fn=None):
    """与 osteomorphic_block 同构，但所有标量可为对偶数（几何参数的解析灵敏度用）。

    sin_fn：标量的 sin 实现（float 用 math.sin，对偶用 eab.dual.sin）。
    面表与 osteomorphic_block **逐项相同** —— 组合结构必须一致，否则冻结的盖标签对不上。
    """
    import math as _m
    if sin_fn is None:
        sin_fn = _m.sin
    cx, cy, cz = center
    top, bot, verts = [], [], []

    def add(p):
        verts.append(p)
        return len(verts) - 1

    for i in range(nx + 1):
        u = i / nx
        x = cx - lx / 2 + lx * u
        h = amp * sin_fn(2 * _m.pi * u + phase)
        rt, rb = [], []
        for j in range(ny + 1):
            y = cy - ly / 2 + ly * (j / ny)
            rt.append(add((x, y, cz + lz / 2 + h)))
            rb.append(add((x, y, cz - lz / 2 + h)))
        top.append(rt)
        bot.append(rb)

    faces = []
    for i in range(nx):
        for j in range(ny):
            faces.append((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
    for i in range(nx):
        for j in range(ny):
            faces.append((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    for i in range(nx):
        faces.append((bot[i][0], bot[i + 1][0], top[i + 1][0], top[i][0]))
        faces.append((bot[i + 1][ny], bot[i][ny], top[i][ny], top[i + 1][ny]))
    for j in range(ny):
        faces.append((top[0][j], top[0][j + 1], bot[0][j + 1], bot[0][j]))
        faces.append((top[nx][j + 1], top[nx][j], bot[nx][j], bot[nx][j + 1]))
    return Polyhedron(verts, faces)


def interlocking_pair_generic(**kw):
    lz = kw.get("lz", 1.0)
    lower = osteomorphic_block_generic(**kw)
    up = dict(kw)
    c = kw.get("center", (0.0, 0.0, 0.0))
    up["center"] = (c[0], c[1], c[2] + lz)
    return osteomorphic_block_generic(**up), lower
