"""前向模式对偶数（多通道）。纪律照搬 b-DDA 的 bdda2，逐条都有血的教训在后面。

  Dual(v, e) 表示 v + Σ_k e_k·ε_k，ε_k·ε_l = 0。W = 通道数（同时对 W 个参数求导）。

三条铁律：
1. **`val()` 只用于择支**（开闭判定、主元选择、钳位、排序）。任何进入本构/几何量的运算
   都必须走对偶通道，否则导数被静默丢掉。
2. **跳过恒等更新前必须 `is_exact_zero()` 看全部通道**，不许写 `if x != 0`。
   `v == 0 而 e ≠ 0` 的分量导数会被静默清零，而这类错误**任何逐位门都抓不到**
   （b-DDA 2026-08-14 实证：GJ 消去里只看 primal，primal 逐位不变而 Jacobian 被清零）。
3. 判据函数（primal-only）与本构函数（dual-through）在**签名上**区分开。

梯度正确性的判据是**收敛阶**（h 扫描误差呈 V 形、大端按 O(h²)），不是某个 h 上的一致；
纯相对误差判据会被接近零的分量主导而误报。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence, Union

Number = Union[int, float, "Dual"]


@dataclass(slots=True, frozen=True)
class Dual:
    v: float
    e: tuple[float, ...]

    # ---------------- 构造 ----------------
    @staticmethod
    def const(v: float, width: int) -> "Dual":
        return Dual(float(v), (0.0,) * width)

    @staticmethod
    def seed(v: float, width: int, k: int) -> "Dual":
        """第 k 个参数的种子：值 v，第 k 通道导数 1。"""
        e = [0.0] * width
        e[k] = 1.0
        return Dual(float(v), tuple(e))

    @property
    def width(self) -> int:
        return len(self.e)

    # ---------------- 纪律 ----------------
    def is_exact_zero(self) -> bool:
        """值与**全部**导数通道都精确为零。跳过恒等更新前必须用它，不能只看 v。"""
        return self.v == 0.0 and all(x == 0.0 for x in self.e)

    # ---------------- 算术 ----------------
    def _pair(self, o: Number) -> tuple[float, tuple[float, ...]]:
        if isinstance(o, Dual):
            if o.width != self.width:
                raise ValueError(f"dual width mismatch: {self.width} vs {o.width}")
            return o.v, o.e
        return float(o), (0.0,) * self.width

    def __add__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(self.v + ov, tuple(a + b for a, b in zip(self.e, oe)))

    __radd__ = __add__

    def __neg__(self) -> "Dual":
        return Dual(-self.v, tuple(-a for a in self.e))

    def __sub__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(self.v - ov, tuple(a - b for a, b in zip(self.e, oe)))

    def __rsub__(self, o: Number) -> "Dual":
        return (-self).__add__(o)

    def __mul__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(self.v * ov, tuple(a * ov + self.v * b for a, b in zip(self.e, oe)))

    __rmul__ = __mul__

    def __truediv__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        inv = 1.0 / ov
        return Dual(self.v * inv, tuple((a * ov - self.v * b) * inv * inv
                                        for a, b in zip(self.e, oe)))

    def __rtruediv__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        inv = 1.0 / self.v
        return Dual(ov * inv, tuple((b * self.v - ov * a) * inv * inv
                                    for a, b in zip(self.e, oe)))

    def __pow__(self, p: float) -> "Dual":
        """实指数幂。负底的非整数幂在实数里无定义：float.__pow__ 会静默给出复数并流进后续
        对偶运算，所以这里当场报错。指数本身不许是对偶数（不支持 ∂/∂p）。"""
        if isinstance(p, Dual):
            raise TypeError("Dual ** Dual is not supported (no derivative w.r.t. the exponent)")
        p = float(p)
        if self.v < 0.0 and not p.is_integer():
            raise ValueError(f"Dual ** {p!r}: negative base {self.v!r} has no real power")
        c = p * (self.v ** (p - 1.0))
        return Dual(self.v ** p, tuple(c * a for a in self.e))

    # ---------------- 择支（只看 primal，禁止参与本构） ----------------
    def __float__(self) -> float:
        """**禁止**隐式转 float。CPython 的 float()/math.*/%-格式化都走这条协议，
        若返回 primal，math.sin(Dual) 会静默丢掉全部导数通道（primal 逐位不变，任何值门都抓不到）。
        择支请显式用 `val()`；超越函数请用本模块的 sin/cos/sqrt/atan2。"""
        raise TypeError("Dual cannot be implicitly converted to float (it would silently drop the "
                        "derivative channels); use eab.dual.val() for branching, eab.dual.sin/cos/"
                        "sqrt/atan2 for arithmetic")

    def __lt__(self, o: Number) -> bool:
        return self.v < (o.v if isinstance(o, Dual) else float(o))

    def __le__(self, o: Number) -> bool:
        return self.v <= (o.v if isinstance(o, Dual) else float(o))

    def __gt__(self, o: Number) -> bool:
        return self.v > (o.v if isinstance(o, Dual) else float(o))

    def __ge__(self, o: Number) -> bool:
        return self.v >= (o.v if isinstance(o, Dual) else float(o))

    def __repr__(self) -> str:
        return f"Dual({self.v!r}, {self.e!r})"


def val(x: Number) -> float:
    """取 primal。**只用于择支**：开闭判定、主元、钳位、排序、打印。"""
    return x.v if isinstance(x, Dual) else float(x)


def grad(x: Number, width: int | None = None) -> tuple[float, ...]:
    if isinstance(x, Dual):
        return x.e
    return (0.0,) * (width or 0)


def is_exact_zero(x: Number) -> bool:
    """跳过恒等更新的**唯一**合法判据。对 float 退化为 x == 0。"""
    return x.is_exact_zero() if isinstance(x, Dual) else (float(x) == 0.0)


def sqrt(x: Number) -> Number:
    if isinstance(x, Dual):
        s = math.sqrt(x.v)
        c = 0.5 / s
        return Dual(s, tuple(c * a for a in x.e))
    return math.sqrt(x)


def sin(x: Number) -> Number:
    if isinstance(x, Dual):
        c = math.cos(x.v)
        return Dual(math.sin(x.v), tuple(c * a for a in x.e))
    return math.sin(x)


def cos(x: Number) -> Number:
    if isinstance(x, Dual):
        c = -math.sin(x.v)
        return Dual(math.cos(x.v), tuple(c * a for a in x.e))
    return math.cos(x)


def atan2(y: Number, x: Number) -> Number:
    if not isinstance(y, Dual) and not isinstance(x, Dual):
        return math.atan2(y, x)
    if isinstance(y, Dual) and isinstance(x, Dual) and y.width != x.width:
        raise ValueError(f"dual width mismatch: {y.width} vs {x.width}")
    yv, xv = val(y), val(x)
    w = y.width if isinstance(y, Dual) else x.width       # type: ignore[union-attr]
    ye = grad(y, w)
    xe = grad(x, w)
    den = xv * xv + yv * yv
    return Dual(math.atan2(yv, xv), tuple((xv * a - yv * b) / den for a, b in zip(ye, xe)))


def lift(xs: Sequence[float], width: int) -> tuple[Dual, ...]:
    return tuple(Dual.const(x, width) for x in xs)


def seeded(values: Sequence[float]) -> tuple[Dual, ...]:
    """把一组标量做成互相独立的种子（第 k 个种到第 k 通道）。"""
    w = len(values)
    return tuple(Dual.seed(v, w, k) for k, v in enumerate(values))


def central_difference(f, theta: Sequence[float], h: float) -> list[float]:
    """中心差分（G3 的对照）。返回每个参数通道的导数。"""
    out = []
    for k in range(len(theta)):
        tp = list(theta)
        tm = list(theta)
        tp[k] += h
        tm[k] -= h
        out.append((f(tp) - f(tm)) / (2.0 * h))
    return out


def convergence_order(f, theta: Sequence[float], analytic: Sequence[float],
                      hs: Iterable[float] = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7)) -> dict:
    """G3 的正当判据：h 扫描误差呈 V 形、大端按 O(h²)。

    返回 {h: 最大绝对误差}、谷底 h 与谷底误差、以及大端两点的实测阶。
    """
    hs = list(hs)
    errs = {}
    for h in hs:
        fd = central_difference(f, theta, h)
        errs[h] = max(abs(a - b) for a, b in zip(fd, analytic))
    big = sorted(hs, reverse=True)[:2]
    order = None
    if len(big) == 2 and errs[big[1]] > 0 and errs[big[0]] > 0:
        order = math.log(errs[big[0]] / errs[big[1]]) / math.log(big[0] / big[1])
    hmin = min(errs, key=lambda k: errs[k])
    return {"errors": errs, "valley_h": hmin, "valley_error": errs[hmin], "large_h_order": order}
