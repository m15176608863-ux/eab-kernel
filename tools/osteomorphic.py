"""互锁块几何生成器：osteomorphic（骨形）块——拓扑互锁结构（TIA）的原型块。

Dyskin/Estrin 一族的 osteomorphic 块：两组相对的面是**相互补的曲面**（一凸一凹），
使块只能沿特定方向组装、组装后彼此约束。这是 04 号文档判为首选方向（TIA）的对象，
也是 Phase 3 凹块内核的第一个真实算例——它的凹几何没有 legacy 可对，只能靠 G0 自证。

本文件用**分段平面**近似曲面（每方向 n 段），得到真正的凹多面体（有反射棱），
参数化程度足以做界面几何的灵敏度/优化（TIA 论文的核心量）。
"""

from __future__ import annotations

from math import pi, sin
from eab.numeric_domain import binary64_argument, check_input, exact_input
from eab.construction import scalar_rational
from fractions import Fraction
from dataclasses import dataclass
from eab.dual import Dual, val

from eab.kernel3d.geom3 import Polyhedron, Vec3


@dataclass(frozen=True)
class _ShapeJet:
    """Local exact first-order algebra; only final vertices become Dual.

    This does not alter public Dual's per-operation construction semantics.
    Gate: test_shape_dual_complete_jet_keeps_midpoint_residual.
    """
    v: Fraction
    e: tuple[Fraction, ...]

    def _pair(self, other):
        if isinstance(other, _ShapeJet):
            if len(self.e) != len(other.e):
                raise ValueError(f"dual width mismatch: {len(self.e)} vs {len(other.e)}")
            return other.v, other.e
        return Fraction(other), (Fraction(0),)*len(self.e)

    def __add__(self, other):
        value, channels = self._pair(other)
        return _ShapeJet(self.v + value, tuple(a+b for a,b in zip(self.e,channels)))

    __radd__ = __add__

    def __neg__(self):
        return _ShapeJet(-self.v, tuple(-a for a in self.e))

    def __sub__(self, other):
        return self + (-other)

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        value, channels = self._pair(other)
        return _ShapeJet(self.v*value,
                         tuple(a*value+self.v*b for a,b in zip(self.e,channels)))

    __rmul__ = __mul__

    def __truediv__(self, other):
        value, channels = self._pair(other)
        return _ShapeJet(self.v/value,
                         tuple((a*value-self.v*b)/(value*value)
                               for a,b in zip(self.e,channels)))


def _shape_value(value):
    """Retain exact local jets/coefficients until the completed coordinate."""
    if isinstance(value, Dual):
        return _ShapeJet(exact_input(value.v, "osteomorphic primal"),
                         tuple(exact_input(a, "osteomorphic jet") for a in value.e))
    return value if isinstance(value, _ShapeJet) else Fraction(value)


def _shape_primal(value):
    return value.v if isinstance(value, (Dual, _ShapeJet)) else value


def _shape_sin(base_angle, phase, sin_fn):
    """Sample the callback's value/unit derivative, then scale seeds exactly.

    The angle remains the scalar sampled-libm model, shared with the raw path.
    A unit seed avoids range loss before amp and all coordinate terms combine.
    Gate: test_shape_phase_jet_is_scaled_before_final_range_check.
    """
    argument = base_angle + float(_shape_primal(phase))
    if isinstance(phase, Dual):
        sample = sin_fn(Dual(argument, (1.0,)))
        if not isinstance(sample, Dual) or sample.width != 1:
            raise TypeError("osteomorphic sin_fn must preserve the unit Dual channel")
        coefficient = exact_input(sample.e[0], "osteomorphic sin coefficient")
        return _ShapeJet(exact_input(sample.v, "osteomorphic sin value"),
                         tuple(coefficient*exact_input(a, "osteomorphic phase jet")
                               for a in phase.e))
    return _shape_value(sin_fn(argument))


def _shape_parameters(nx, ny, lx, ly, lz, amp, center):
    """Approximate sampled shape: D400 physical inputs, exact coordinate algebra.

    Angles retain the documented sampled libm coefficient model. A completed
    coordinate and each completed jet are checked separately; D400 does not
    imply output range. Local jet algebra stays exact until that boundary.
    Gate: test_shape_dual_complete_coordinate_keeps_midpoint_residual and
    test_shape_complete_jet_outside_output_domain_fails_by_name.
    """
    counts = []
    for name, value in (("nx",nx),("ny",ny)):
        q = exact_input(value, "osteomorphic."+name)
        if q.denominator != 1 or q <= 0:
            raise ValueError("osteomorphic grid counts must be positive integers")
        counts.append(q.numerator)
    for name, value in (("lx",lx),("ly",ly),("lz",lz),("amp",amp)):
        check_input(_shape_primal(value), "osteomorphic."+name)
        if name != "amp" and _shape_primal(value) <= 0:
            raise ValueError("osteomorphic lengths must be positive")
    for i,value in enumerate(center):
        check_input(_shape_primal(value), f"osteomorphic.center[{i}]")
    return (*counts,*(_shape_value(v) for v in (lx,ly,lz,amp)),tuple(_shape_value(v) for v in center))


def _shape_coordinate(value):
    if isinstance(value, _ShapeJet):
        return Dual(scalar_rational(value.v, quantity="osteomorphic coordinate"),
                    tuple(scalar_rational(a, quantity=f"osteomorphic coordinate jet[{i}]")
                          for i,a in enumerate(value.e)))
    return scalar_rational(value, quantity="osteomorphic coordinate")


def osteomorphic_block(nx: int = 4, ny: int = 4, *, lx: float = 2.0, ly: float = 1.0,
                       lz: float = 1.0, amp: float = 0.25, center: Vec3 = (0.0, 0.0, 0.0),
                       phase: float = 0.0) -> Polyhedron:
    """骨形块：顶/底面为沿 x 起伏的互补曲面（顶凸则底凹），侧面竖直。

    顶面高度  z = +lz/2 + amp·sin(2π·u + phase)
    底面高度  z = −lz/2 + amp·sin(2π·u + phase)      （同相位 ⇒ 上下互补，可堆叠咬合）
    其中 u = (x + lx/2)/lx ∈ [0,1]。amp=0 退化为长方体（可作对照）。

    nx 段沿 x、ny 段沿 y；顶底各 (nx+1)×(ny+1) 个网格点，侧面由边界网格线构成。
    """
    from eab.dual import val
    binary64_argument(val(phase), "osteomorphic.phase")
    nx, ny, lx, ly, lz, amp, center = _shape_parameters(nx, ny, lx, ly, lz, amp, center)
    cx, cy, cz = center
    top: list[list[int]] = []
    bot: list[list[int]] = []
    verts: list[Vec3] = []

    def add(p: Vec3) -> int:
        verts.append(tuple(_shape_coordinate(v) for v in p))
        return len(verts) - 1

    for i in range(nx + 1):
        u = i / nx
        x = cx - lx / 2 + lx * Fraction(u)
        h = amp * Fraction(sin(2 * pi * u + phase))
        row_t: list[int] = []
        row_b: list[int] = []
        for j in range(ny + 1):
            y = cy - ly / 2 + ly * Fraction(j / ny)
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
    upper_kw["center"] = (c[0], c[1], _shape_value(c[2]) + _shape_value(lz))
    upper = osteomorphic_block(**upper_kw)
    return upper, lower


def osteomorphic_block_generic(nx: int = 4, ny: int = 4, *, lx=2.0, ly=1.0, lz=1.0,
                               amp=0.25, center=(0.0, 0.0, 0.0), phase=0.0, sin_fn=None):
    """与 osteomorphic_block 同构，但所有标量可为对偶数（几何参数的解析灵敏度用）。

    sin_fn：标量的 sin 实现。默认 `eab.dual.sin`——对 float 退化为 math.sin，对对偶数走导数通道；
    （曾默认 math.sin：配合 Dual 的隐式 float 协议，不传 sin_fn 时 ∂/∂phase 被静默清零。）
    面表与 osteomorphic_block **逐项相同** —— 组合结构必须一致，否则冻结的盖标签对不上。
    本工具内部在有理数上完成整条坐标及一阶 jet，最终逐分量构造 Dual；不改变全局 Dual 逐步舍入语义。
    相位回调收到宽 1 的 Dual(argument, (1.0,)) 以采样局部一阶系数，再精确乘原 seed 与 amp；必须返回宽 1 的 Dual。
    依赖调用方原 seed/通道宽度、而非实现一般标量一阶运算的自定义回调不再兼容。
    门：test_shape_general_position_all_vertices_and_channels_round_once；
    test_shape_phase_jet_is_scaled_before_final_range_check。
    """
    import math as _m
    if sin_fn is None:
        from eab.dual import sin as sin_fn
    from eab.dual import val
    binary64_argument(val(phase), "osteomorphic.phase")
    nx, ny, lx, ly, lz, amp, center = _shape_parameters(nx, ny, lx, ly, lz, amp, center)
    cx, cy, cz = center
    top, bot, verts = [], [], []

    def add(p):
        verts.append(tuple(_shape_coordinate(v) for v in p))
        return len(verts) - 1

    for i in range(nx + 1):
        u = i / nx
        x = cx - lx / 2 + lx * Fraction(u)
        h = amp * _shape_sin(2 * _m.pi * u, phase, sin_fn)
        rt, rb = [], []
        for j in range(ny + 1):
            y = cy - ly / 2 + ly * Fraction(j / ny)
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
    up["center"] = (c[0], c[1], _shape_value(c[2]) + _shape_value(lz))
    return osteomorphic_block_generic(**up), lower
