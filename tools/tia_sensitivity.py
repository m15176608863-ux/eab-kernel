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


def freeze_cover(delta: float, *, nx: int, ny: int, amp: float, phase: float):
    """float 路径：定出该 δ 处决定逃逸高度的盖标签与 EE 法向朝向（冻结的组合结构）。"""
    A, L = interlocking_pair(nx=nx, ny=ny, amp=amp, phase=phase)
    sol = escape_height_covers(A, L, (delta, 0.0, 0.0))
    if sol.cover_label is None:
        return None, 1.0, sol.height
    lab = sol.cover_label
    sign = 1.0
    if lab[0] == "EE":
        sign = frozen_ee_sign(A, L, (lab[1][1], lab[1][2]), (lab[2][1], lab[2][2]))
    return lab, sign, sol.height


def sensitivity_at(delta: float, *, nx: int = 4, ny: int = 2, amp: float = 0.25,
                   phase: float = 0.0) -> dict | None:
    """在给定 δ 处返回 {h, tan_psi, dh_damp, dh_dphase, cover}。δ/amp/phase 三通道同时求导。"""
    lab, sign, h_float = freeze_cover(delta, nx=nx, ny=ny, amp=amp, phase=phase)
    if lab is None:
        return None
    d_d = Dual.seed(delta, W, CH_DELTA)
    d_amp = Dual.seed(amp, W, CH_AMP)
    d_ph = Dual.seed(phase, W, CH_PHASE)
    A, L = interlocking_pair_generic(nx=nx, ny=ny, amp=d_amp, phase=d_ph, sin_fn=D.sin)
    off = (d_d, Dual.const(0.0, W), Dual.const(0.0, W))
    z = escape_height_from_frozen_cover(A, L, lab, off, ee_sign=sign)
    return {"delta": delta, "h": z.v, "h_float": h_float,
            "tan_psi": z.e[CH_DELTA], "dh_damp": z.e[CH_AMP], "dh_dphase": z.e[CH_PHASE],
            "cover": (lab[0], lab[1][1:], lab[2][1:])}


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
    for r in rows:
        assert abs(r["h"] - r["h_float"]) < 1e-9, r
        print(f"{r['delta']:6.2f} {r['h']:10.6f} {r['tan_psi']:9.4f} {r['dh_damp']:9.4f} "
              f"{r['dh_dphase']:10.4f}  {r['cover']}")
    peak = max(rows, key=lambda r: r["h"])
    print(f"\npeak escape height {peak['h']:.4f} at delta={peak['delta']}")
    pos = [r for r in rows if r["tan_psi"] > 0]
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
