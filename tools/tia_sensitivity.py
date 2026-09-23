"""TIA 首枪：互锁界面几何 → 逃逸剖面 → 剪胀比 → **解析灵敏度**。

这是 04/06 号文档判定的首选方向（拓扑互锁结构）里那个"全场没有第二家"的东西：
石根华的盖机器给"算得对"，可微层给"能求导"，叠起来是**可优化的接触设计**。

物理量（都由入口块边界读出）：
  h(δ)     逃逸高度剖面 —— 横移 δ 时必须抬升多少才不互相贯入
  tanψ     = ∂h/∂δ，剪胀比；无摩擦极限下即横向承载 / 法向压力（Rowe 剪胀关系）
  ∂·/∂θ    对界面几何参数（幅值 amp、相位 phase）的解析导数

实现要点（"片 + 划"）：float 路径定出**哪个盖当家**（组合结构，含 EE 法向朝向），
对偶路径在冻结的片内做纯解析运算。δ 本身也种成一个对偶通道 —— 于是 tanψ 不是差分出来的，
而是同一次对偶求值的一个导数通道。

**不可微点（2026-09-21 审查 C13）。** 冻结的盖只是该点"并列活跃"的接触盖里被裁决选中的一支；
并列的盖若在某通道给出不同导数，h 在该通道就不可微（默认剖面 phase=0 处 h 关于 phase 是偶函数、
V 形；δ=0.5 是剖面峰值折点），此时那支的 AD 值只是单侧方向导数，不是导数。所以每一行同时报
  differentiable_by[通道]  = 全部并列活跃盖在该通道的导数一致（差 ≤ DERIV_TOL）
  derivative_range[通道]   = 这些导数的 [最小, 最大]（分段光滑时即两个单侧导数；可微时退化为一点）
  differentiable           = 三个通道都可微
并列按高度判（相对 TIE_TOL = 1e-9，见 eab.kernel3d.interlock），是精确的一阶判据、无需步长 ε；
门（tests/test_interlock_sensitivity.py）用与盖路径零共用的解析逃逸高度的单侧差商（ε=1e-7）核对它。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from eab import dual as D  # noqa: E402
from eab.dual import Dual, val  # noqa: E402
from eab.kernel3d.interlock import (escape_height_covers, escape_height_from_frozen_cover,  # noqa: E402
                                    frozen_ee_sign)
from osteomorphic import interlocking_pair, interlocking_pair_generic  # noqa: E402

CH_DELTA, CH_AMP, CH_PHASE = 0, 1, 2
W = 3
CHANNELS = (("tan_psi", CH_DELTA), ("dh_damp", CH_AMP), ("dh_dphase", CH_PHASE))
DERIV_TOL = 1e-9          # 并列活跃盖的导数视为一致的绝对容差（导数 O(1)，对偶求值舍入 ~1e-15）


def _ee_sign(A, L, lab) -> float:
    if lab[0] == "EE":
        return frozen_ee_sign(A, L, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2]))
    return 1.0


def _frozen_structure(delta: float, *, nx: int, ny: int, amp: float, phase: float):
    """float 路径：逃逸解，以及该高度上并列活跃的全部 (盖标签, EE 朝向)，胜出者排第一。"""
    A, L = interlocking_pair(nx=nx, ny=ny, amp=amp, phase=phase)
    sol = escape_height_covers(A, L, (delta, 0.0, 0.0))
    return sol, [(lab, _ee_sign(A, L, lab)) for lab in sol.tied_labels]


def freeze_cover(delta: float, *, nx: int, ny: int, amp: float, phase: float):
    """float 路径：定出该 δ 处决定逃逸高度的盖标签与 EE 法向朝向（冻结的组合结构）。"""
    sol, active = _frozen_structure(delta, nx=nx, ny=ny, amp=amp, phase=phase)
    if sol.cover_label is None:
        return None, 1.0, sol.height
    lab, sign = active[0]
    return lab, sign, sol.height


def sensitivity_at(delta: float, *, nx: int = 4, ny: int = 2, amp: float = 0.25,
                   phase: float = 0.0) -> dict | None:
    """在给定 δ 处返回 {h, tan_psi, dh_damp, dh_dphase, cover, differentiable, differentiable_by,
    derivative_range, n_active}。δ/amp/phase 三通道同时求导。

    tan_psi / dh_damp / dh_dphase 是**冻结胜出盖**的 AD 值；只有 differentiable_by[该通道] 为真时
    它才是经典导数，否则它只是 derivative_range 两端之一（单侧方向导数），见模块说明。
    """
    sol, active = _frozen_structure(delta, nx=nx, ny=ny, amp=amp, phase=phase)
    if sol.cover_label is None:
        return None
    d_d = Dual.seed(delta, W, CH_DELTA)
    d_amp = Dual.seed(amp, W, CH_AMP)
    d_ph = Dual.seed(phase, W, CH_PHASE)
    A, L = interlocking_pair_generic(nx=nx, ny=ny, amp=d_amp, phase=d_ph, sin_fn=D.sin)
    off = (d_d, Dual.const(0.0, W), Dual.const(0.0, W))
    zs = [escape_height_from_frozen_cover(A, L, lab, off, ee_sign=sign) for lab, sign in active]
    z = zs[0]
    lab = active[0][0]
    rng = {name: (min(zz.e[ch] for zz in zs), max(zz.e[ch] for zz in zs)) for name, ch in CHANNELS}
    by = {name: (hi - lo) <= DERIV_TOL for name, (lo, hi) in rng.items()}
    return {"delta": delta, "h": z.v, "h_float": sol.height,
            "tan_psi": z.e[CH_DELTA], "dh_damp": z.e[CH_AMP], "dh_dphase": z.e[CH_PHASE],
            "cover": (lab[0], lab[1][1:], lab[2][1:]),
            "differentiable": all(by.values()), "differentiable_by": by,
            "derivative_range": rng, "n_active": len(active)}


def profile(*, nx: int = 4, ny: int = 2, amp: float = 0.25, phase: float = 0.0,
            deltas: list[float] | None = None) -> list[dict]:
    if deltas is None:
        deltas = [round(0.05 * i, 4) for i in range(1, 20)]
    out = []
    for d in deltas:
        r = sensitivity_at(d, nx=nx, ny=ny, amp=amp, phase=phase)
        if r is not None:
            out.append(r)
    return out


def main() -> int:
    rows = profile()
    print(f"{'delta':>6} {'h':>10} {'tan_psi':>9} {'dh/damp':>9} {'dh/dphase':>10}  cover")

    def cell(r, name, width):
        if r["differentiable_by"][name]:
            return f"{r[name]:{width}.4f}"
        lo, hi = r["derivative_range"][name]
        return f"[{lo:+.4f},{hi:+.4f}]*".rjust(width)

    for r in rows:
        assert abs(r["h"] - r["h_float"]) < 1e-9, r
        print(f"{r['delta']:6.2f} {r['h']:10.6f} {cell(r, 'tan_psi', 9)} {cell(r, 'dh_damp', 9)} "
              f"{cell(r, 'dh_dphase', 10)}  {r['cover']}")
    print("  * 不可微：并列活跃的接触盖在该通道给出不同导数，列出的是 [最小, 最大]（两个单侧导数）")
    peak = max(rows, key=lambda r: r["h"])
    print(f"\npeak escape height {peak['h']:.4f} at delta={peak['delta']}")
    pos = [r for r in rows if r["tan_psi"] > 0 and r["differentiable_by"]["tan_psi"]]
    if pos:
        print(f"mean |tan psi| on the rising branch = "
              f"{sum(r['tan_psi'] for r in pos) / len(pos):.4f}  "
              f"(= lateral capacity / normal load in the frictionless limit)")
    # 幅值扫描：峰值逃逸高度与剪胀比对 amp 的依赖
    print("\namp sweep at delta=0.30:")
    for a in (0.10, 0.15, 0.20, 0.25, 0.30):
        r = sensitivity_at(0.30, amp=a)
        print(f"  amp={a:.2f}  h={r['h']:.5f}  tan_psi={r['tan_psi']:.4f}  dh/damp={r['dh_damp']:.4f}")
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "tia_sensitivity.json").write_text(
        json.dumps({"profile": rows}, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
