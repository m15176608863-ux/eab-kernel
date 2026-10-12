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
Algebraic jet constructions retain the full finite rational input domain;
unrepresentable nonzero outputs raise ConstructionDomainError. Integer and
half-integer powers dispatch from the exact exponent, without losing parity.
Other power exponents/bases and sin/cos/atan2 arguments must be losslessly
representable finite binary64 values before calling the libm model (R14FIX).
This includes all finite binary64 subnormals, not just the engineering D400
interval. Gate: tests/test_r14_dual.py. Diagnostic
finite differences use the input domain in docs/exact_predicates_plan.md.
The callback samples and libm coefficients define their approximate model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from eab.construction import scalar_rational, sqrt_rational
from eab.numeric_domain import ConstructionDomainError, check_input, check_inputs, exact_input, binary64_argument
from fractions import Fraction
from decimal import Decimal, localcontext, Underflow
from typing import Iterable, Sequence, Union

Number = Union[int, float, "Dual"]


@dataclass(slots=True, frozen=True)
class Dual:
    v: float
    e: tuple[float, ...]

    # ---------------- 构造 ----------------
    @staticmethod
    def const(v: float, width: int) -> "Dual":
        return Dual(scalar_rational(v, quantity="Dual.const primal"), (0.0,) * width)

    @staticmethod
    def seed(v: float, width: int, k: int) -> "Dual":
        """第 k 个参数的种子：值 v，第 k 通道导数 1。"""
        e = [0.0] * width
        e[k] = 1.0
        return Dual(scalar_rational(v, quantity="Dual.seed primal"), tuple(e))

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
        return o, (0.0,) * self.width

    def __add__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(scalar_rational(Fraction(self.v) + Fraction(ov)),
                    tuple(_derivative_float(Fraction(a) + Fraction(b)) for a, b in zip(self.e, oe)))

    __radd__ = __add__

    def __neg__(self) -> "Dual":
        return Dual(-self.v, tuple(-a for a in self.e))

    def __sub__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(scalar_rational(Fraction(self.v) - Fraction(ov)),
                    tuple(_derivative_float(Fraction(a) - Fraction(b)) for a, b in zip(self.e, oe)))

    def __rsub__(self, o: Number) -> "Dual":
        return -self + o

    def __mul__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(scalar_rational(Fraction(self.v) * Fraction(ov)), tuple(_product_derivative(self.v, ov, a, b)
                                      for a, b in zip(self.e, oe)))

    __rmul__ = __mul__

    def __truediv__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(scalar_rational(Fraction(self.v) / Fraction(ov)), tuple(_ratio_derivative(self.v, ov, a, b)
                                      for a, b in zip(self.e, oe)))

    def __rtruediv__(self, o: Number) -> "Dual":
        ov, oe = self._pair(o)
        return Dual(scalar_rational(Fraction(ov) / Fraction(self.v)), tuple(_ratio_derivative(ov, self.v, b, a)
                                      for a, b in zip(self.e, oe)))

    def __pow__(self, p: float) -> "Dual":
        """实指数幂。负底的非整数幂在实数里无定义：float.__pow__ 会静默给出复数并流进后续
        对偶运算，所以这里当场报错。指数本身不许是对偶数（不支持 ∂/∂p）。"""
        if isinstance(p, Dual):
            raise TypeError("Dual ** Dual is not supported (no derivative w.r.t. the exponent)")
        p = exact_input(p, "Dual power exponent")
        if p == 0.0:
            return Dual(1.0, (0.0,) * self.width)
        if self.v < 0.0 and p.denominator != 1:
            raise ValueError(f"Dual ** {p!r}: negative base {self.v!r} has no real power")
        if p.denominator == 1:
            _check_exact_power_size(self.v, max(abs(int(p)), abs(int(p)-1)), "Dual integer power")
            value = scalar_rational(Fraction(self.v) ** int(p), quantity="Dual integer power")
            # Dispatch before any binary64 conversion: p can exceed 2**53,
            # and its parity still determines both primal and derivative signs.
            c = Fraction(p) * Fraction(self.v) ** (int(p) - 1)
            return Dual(value, tuple(_derivative_float(c * Fraction(a)) for a in self.e))
        if Fraction(p).denominator == 2:
            _check_exact_power_size(self.v, max(abs(int(2*p)), abs(int(2*p)-2)), "Dual half-integer power")
            value = sqrt_rational(Fraction(self.v) ** int(2*p))
            # The complete half-integer derivative has a rational square;
            # Decimal precision must not perturb exact subnormal ties.
            return Dual(value, tuple(_half_power_derivative(self.v, p, a) for a in self.e))
        p = _lossless_libm_input(p, "Dual power exponent")
        base = _lossless_libm_input(self.v, "Dual power base")
        try:
            value = base ** p
        except OverflowError as exc:
            raise ConstructionDomainError("Dual power: primal exceeds binary64 output range") from exc
        if not math.isfinite(value):
            raise ConstructionDomainError("Dual power: primal is outside finite binary64 range")
        if value == 0.0 and self.v != 0.0:
            raise ConstructionDomainError("Dual power: nonzero primal is below the binary64 range")
        # There is no input-only safe exponent box for powers: even inputs
        # in [2**-200, 2**200] can produce an out-of-range v**(p-1), then
        # return to range after multiplying a seed. Retain a separate exponent
        # through the final product for every noninteger power (G6G-07).
        with localcontext() as ctx:
            ctx.prec = 80
            ctx.traps[Underflow] = True
            # General powers retain an 80-digit transcendental approximation;
            # no exact/correctly-rounded claim is made for that coefficient.
            c = ctx.power(Decimal(base), Decimal(p) - 1)
            return Dual(value, tuple(_derivative_float(Fraction(p) * Fraction(c) * Fraction(a))
                                     for a in self.e))

    # ---------------- 择支（只看 primal，禁止参与本构） ----------------
    def __float__(self) -> float:
        """**禁止**隐式转 float。CPython 的 float()/math.*/%-格式化都走这条协议，
        若返回 primal，math.sin(Dual) 会静默丢掉全部导数通道（primal 逐位不变，任何值门都抓不到）。
        择支请显式用 `val()`；超越函数请用本模块的 sin/cos/sqrt/atan2。"""
        raise TypeError("Dual cannot be implicitly converted to float (it would silently drop the "
                        "derivative channels); use eab.dual.val() for branching, eab.dual.sin/cos/"
                        "sqrt/atan2 for arithmetic")

    def __lt__(self, o: Number) -> bool:
        return self.v < (o.v if isinstance(o, Dual) else o)

    def __le__(self, o: Number) -> bool:
        return self.v <= (o.v if isinstance(o, Dual) else o)

    def __gt__(self, o: Number) -> bool:
        return self.v > (o.v if isinstance(o, Dual) else o)

    def __ge__(self, o: Number) -> bool:
        return self.v >= (o.v if isinstance(o, Dual) else o)

    def __repr__(self) -> str:
        return f"Dual({self.v!r}, {self.e!r})"


def _ordinary(*values: float) -> bool:
    """A safe exponent box for the fast arithmetic path, not a predicate tolerance."""
    return all(v == 0.0 or 2.0 ** -200 <= abs(v) <= 2.0 ** 200 for v in values)


def _derivative_float(q: Fraction) -> float:
    """Round once; an unrepresentable nonzero derivative must not silently be 0."""
    try:
        return scalar_rational(q)
    except ArithmeticError as exc:
        raise ConstructionDomainError("Dual derivative: outside nonzero finite binary64 output range") from exc


def _ratio_derivative(u: float, v: float, a: float, b: float, *, angular=False) -> float:
    """(a*v-u*b)/v^2, or /(u^2+v^2), without intermediate range loss.

    All algebraic jets are completed exactly before final rounding.
    This also retains components whose exponent span exceeds binary64 range.
    The oracle for this contract is test_r6fix07_* (raw Fraction formulas).
    """
    # Complete polynomial/rational expression first: a fast rounded numerator
    # loses a last bit even without severe cancellation (R13FIXb).
    u, v, a, b = (Fraction(q) for q in (u, v, a, b))
    den = u*u + v*v if angular else v*v
    return _derivative_float((a*v-u*b)/den)


def _product_derivative(u: float, v: float, a: float, b: float) -> float:
    """a*v+u*b: the same two-product cancellation risk as quotient/atan2."""
    return _derivative_float(Fraction(a) * Fraction(v) + Fraction(u) * Fraction(b))


def val(x: Number) -> float:
    """取 primal。**只用于择支**：开闭判定、主元、钳位、排序、打印。"""
    return x.v if isinstance(x, Dual) else x


def grad(x: Number, width: int | None = None) -> tuple[float, ...]:
    if isinstance(x, Dual):
        return x.e
    return (0.0,) * (width or 0)


def is_exact_zero(x: Number) -> bool:
    """跳过恒等更新的**唯一**合法判据。对 float 退化为 x == 0。"""
    return x.is_exact_zero() if isinstance(x, Dual) else (x == 0)


def _check_exact_power_size(base, exponent: int, quantity: str) -> None:
    """Bound exact-power materialisation, not exponent parity or output range.

    For bases other than 0/+1/-1 the numerator+denominator bit allocation
    estimate is limited to 2**20. Trivial bases stay exact for arbitrary int
    exponents; final primal/channel range checks still apply. Gate:
    test_r14_exact_power_resource_limit_is_named_without_losing_trivial_bases.
    """
    q = exact_input(base, quantity)
    if q in (0, 1, -1):
        return
    bits = abs(q.numerator).bit_length() + q.denominator.bit_length()
    if bits * abs(exponent) > 2**20:
        raise ConstructionDomainError(quantity, "exact power resource domain: estimated numerator+denominator bits exceed 2^20")


def _half_power_derivative(value: float, power: float, seed: float) -> float:
    """Exact square of p*value**(p-1)*seed for half-integer p."""
    coefficient = Fraction(power) * Fraction(seed)
    squared = coefficient**2 * Fraction(value)**(int(2*power)-2)
    magnitude = sqrt_rational(squared)
    return -magnitude if coefficient < 0 else magnitude


def _sqrt_derivative(value: float, seed: float) -> float:
    """Round seed/(2*sqrt(value)) only after forming its exact square."""
    magnitude = sqrt_rational(Fraction(seed)**2 / (4*Fraction(value)))
    return -magnitude if seed < 0 else magnitude


def sqrt(x: Number) -> Number:
    """Construct both the primal root and complete analytic derivative once.

    The derivative uses its exact rational square, not the rounded primal.
    Gate: test_r10_sqrt_derivative_rounds_the_complete_expression;
    test_r10_sqrt_derivative_out_of_range_fails_loudly.
    Scalar nonfinite behavior is unchanged; a nonfinite Dual has no finite jet.
    """
    if isinstance(x, Dual):
        s = sqrt(x.v)
        if not math.isfinite(s):
            raise ValueError("Dual sqrt requires a finite primal")
        if x.v == 0:
            raise ZeroDivisionError("Dual sqrt derivative is undefined at zero")
        return Dual(s, tuple(_sqrt_derivative(x.v, a) for a in x.e))
    if isinstance(x, float) and not math.isfinite(x):
        if x < 0:
            raise ValueError("math domain error")
        return x
    return sqrt_rational(x)


def _lossless_libm_input(value, quantity: str) -> float:
    """Local seam for the central lossless transcendental-parameter policy."""
    return binary64_argument(value, quantity)


def sin(x: Number) -> Number:
    """Lossless binary64 argument; libm primal/coefficient, checked final jet.

    No correctly-rounded transcendental claim is made for libm coefficients.
    Gate: test_r14_trig_rejects_lossy_exact_parameters;
    test_r10_trigonometric_nonzero_derivative_cannot_underflow_silently.
    """
    argument = _lossless_libm_input(val(x), "sin angle")
    value = math.sin(argument)
    if value == 0.0 and argument != 0.0:
        raise ConstructionDomainError("sin result", "nonzero result is below the binary64 range")
    if isinstance(x, Dual):
        c = math.cos(argument)
        return Dual(value, tuple(_derivative_float(Fraction(c) * Fraction(a))
                                 for a in x.e))
    return value


def cos(x: Number) -> Number:
    """Same lossless-argument/libm-coefficient contract as sin.

    Gate: test_r14_trig_rejects_lossy_exact_parameters;
    test_r10_trigonometric_representable_subnormal_and_zero_channels.
    """
    argument = _lossless_libm_input(val(x), "cos angle")
    value = math.cos(argument)
    if value == 0.0:
        # A finite rational angle is never an odd multiple of pi/2.
        raise ConstructionDomainError("cos result", "nonzero result is below the binary64 range")
    if isinstance(x, Dual):
        c = -math.sin(argument)
        return Dual(value, tuple(_derivative_float(Fraction(c) * Fraction(a))
                                 for a in x.e))
    return value


def atan2(y: Number, x: Number) -> Number:
    if isinstance(y, Dual) and isinstance(x, Dual) and y.width != x.width:
        raise ValueError(f"dual width mismatch: {y.width} vs {x.width}")
    yv = _lossless_libm_input(val(y), "atan2.y")
    xv = _lossless_libm_input(val(x), "atan2.x")
    # For x>0, 0<abs(atan(y/x))<abs(y/x). Certify the RN-zero cell
    # before libm: some platforms incorrectly return min-subnormal at y/x=u/2.
    if xv > 0 and yv != 0 and 2*abs(Fraction(yv)) <= Fraction(xv)*Fraction(math.ulp(0.0)):
        raise ConstructionDomainError("atan2 result", "nonzero angle is below the binary64 range")
    value = math.atan2(yv, xv)
    if value == 0.0 and yv != 0.0:
        raise ConstructionDomainError("atan2 result", "nonzero angle is below the binary64 range")
    if not isinstance(y, Dual) and not isinstance(x, Dual):
        return value
    w = y.width if isinstance(y, Dual) else x.width       # type: ignore[union-attr]
    ye = grad(y, w)
    xe = grad(x, w)
    return Dual(value, tuple(_ratio_derivative(yv, xv, a, b, angular=True)
                             for a, b in zip(ye, xe)))


def lift(xs: Sequence[float], width: int) -> tuple[Dual, ...]:
    return tuple(Dual.const(x, width) for x in xs)


def seeded(values: Sequence[float]) -> tuple[Dual, ...]:
    """把一组标量做成互相独立的种子（第 k 个种到第 k 通道）。"""
    w = len(values)
    return tuple(Dual.seed(v, w, k) for k, v in enumerate(values))


def central_difference(f, theta: Sequence[float], h: float) -> list[float]:
    """中心差分（G3 的对照）。返回每个参数通道的导数。"""
    check_inputs(theta, "central_difference.theta")
    check_input(h, "central_difference.h")
    out = []
    for k in range(len(theta)):
        tp = list(theta)
        tm = list(theta)
        tp[k] += h
        tm[k] -= h
        fp, fm = f(tp), f(tm)
        out.append(scalar_rational((exact_input(fp, "central_difference.f(tp)") - exact_input(fm, "central_difference.f(tm)")) / (2 * Fraction(h))))
    return out


def convergence_order(f, theta: Sequence[float], analytic: Sequence[float],
                      hs: Iterable[float] = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7)) -> dict:
    """G3 的正当判据：h 扫描误差呈 V 形、大端按 O(h²)。

    返回 {h: 最大绝对误差}、谷底 h 与谷底误差、以及大端两点的实测阶。
    """
    hs = list(hs)
    check_inputs(analytic, "convergence_order.analytic")
    errs = {}
    for h in hs:
        fd = central_difference(f, theta, h)
        errs[h] = scalar_rational(max(abs(Fraction(a) - Fraction(b)) for a, b in zip(fd, analytic)))
    big = sorted(hs, reverse=True)[:2]
    order = None
    if len(big) == 2 and errs[big[1]] > 0 and errs[big[0]] > 0:
        ratio = Fraction(errs[big[0]]) / Fraction(errs[big[1]])
        if Fraction(2)**-1000 <= ratio <= Fraction(2)**1000:
            numerator = math.log(scalar_rational(ratio))
        else:
            # Integer log accepts arbitrary magnitudes without a float ratio.
            numerator = math.log(ratio.numerator) - math.log(ratio.denominator)
        order = numerator / math.log(scalar_rational(Fraction(big[0])/Fraction(big[1])))
    hmin = min(errs, key=lambda k: errs[k])
    return {"errors": errs, "valley_h": hmin, "valley_error": errs[hmin], "large_h_order": order}
