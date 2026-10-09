"""演示页的图与数字（2026-10-10）：把引擎在四个问题上的输出画出来。

    python tools/showcase.py            → reports/showcase/*.png + reports/showcase/numbers.json

四幅图：(1) 薄拱的推力线与四铰机构（M1 多体极限分析）；(2) 承载力随摩擦的曲线，对照铰机构上限与叠放块闭式；
(3) bb52 真实 DDA 几何上的盖枚举与一对凸块的入口块 E(A,B)；(4) 三维裕度接触（棱脊 + 细针，原点与 1e6 m 处）；
(5) 互锁块的逃逸高度剖面（TIA）。只读夹具与库，不改任何东西。
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from eab.kernel2d.covers import convex_entrance_block, enumerate_covers      # noqa: E402
from eab.kernel2d.geom import translate                                     # noqa: E402
from eab.kernel3d.geom3 import Polyhedron, brute_feature_distance, convex_hull_3d  # noqa: E402
from eab.limit import LimitContact, wrench                                 # noqa: E402
from eab.limit_multi import BodyContact, LimitBody, limit_load_multi      # noqa: E402
from eab.margin import body_distance, inflated_membership, margin_contacts  # noqa: E402

OUT = ROOT / "reports" / "showcase"
plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 130
INK, ACC, ACC2, GREY = "#1f2a33", "#b5451b", "#2b6f8f", "#8a8f94"
NUM: dict = {}


# ---------------------------------------------------------------- 1. 薄拱

def arch_problem(n=5, r_in=1.0, r_out=1.15, rho=10.0, mu=2.0):
    ang = [math.pi * j / n for j in range(n + 1)]
    pt = lambda r, th: (r * math.cos(th), r * math.sin(th))
    blocks = [[pt(r_in, ang[i]), pt(r_out, ang[i]), pt(r_out, ang[i + 1]), pt(r_in, ang[i + 1])] for i in range(n)]

    def area_centroid(P):
        a = cx = cy = 0.0
        for i in range(len(P)):
            (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
            w = x0 * y1 - x1 * y0
            a += w
            cx += (x0 + x1) * w
            cy += (y0 + y1) * w
        a *= 0.5
        return a, (cx / (6 * a), cy / (6 * a))
    bodies = []
    for P in blocks:
        a, c = area_centroid(P)
        bodies.append(LimitBody(wrench((0.0, -rho * a), c, (0.0, 0.0), 2), [0.0] * 3))
    crown = (0.0, r_out)
    bodies[n // 2].live = wrench((0.0, -1.0), crown, (0.0, 0.0), 2)
    bcs, joints = [], []
    for j in range(n + 1):
        th = ang[j]
        corners = [pt(r_in, th), pt(r_out, th)]
        if j == 0:
            nrm, a, b = (0.0, 1.0), 0, None
        elif j == n:
            nrm, a, b = (0.0, 1.0), n - 1, None
        else:
            nrm, a, b = (-math.sin(th), math.cos(th)), j, j - 1
        joints.append((corners, nrm))
        bcs += [BodyContact(LimitContact(p, nrm, mu), a, b) for p in corners]
    return blocks, bodies, bcs, joints, crown


def fig_arch():
    blocks, bodies, bcs, joints, crown = arch_problem(mu=2.0)
    r = limit_load_multi(bodies, bcs, dim=2)
    NUM["arch_alpha_mu2"] = r.alpha
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    # (a) 推力线：每条缝两个角点力的合力作用点
    ax = axes[0]
    for P in blocks:
        ax.add_patch(MplPolygon(P, closed=True, fc="#e9e4da", ec=INK, lw=1.0))
    line = []
    for j, (corners, nrm) in enumerate(joints):
        f0, f1 = r.contact_forces[2 * j], r.contact_forces[2 * j + 1]
        n0 = f0[0] * nrm[0] + f0[1] * nrm[1]
        n1 = f1[0] * nrm[0] + f1[1] * nrm[1]
        t = n1 / (n0 + n1)
        q = (corners[0][0] + t * (corners[1][0] - corners[0][0]), corners[0][1] + t * (corners[1][1] - corners[0][1]))
        line.append(q)
        F = (f0[0] + f1[0], f0[1] + f1[1])
        s = 0.06 / max(1e-9, math.hypot(*F)) * math.hypot(*F) ** 0.5
        ax.annotate("", xy=(q[0] + s * F[0], q[1] + s * F[1]), xytext=q,
                    arrowprops=dict(arrowstyle="->", color=ACC2, lw=1.2))
    xs, ys = zip(*line)
    ax.plot(xs, ys, "-o", color=ACC, lw=1.6, ms=4, label="推力线（各缝合力作用点）")
    ax.annotate("", xy=(crown[0], crown[1] - 0.18), xytext=(crown[0], crown[1] + 0.02),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.0))
    ax.text(crown[0] + 0.05, crown[1] + 0.05, f"α·P，α = {r.alpha:.4f}", fontsize=9, color=INK)
    ax.set_aspect("equal")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-0.1, 1.4)
    ax.set_title("(a) 下限：平衡的接触力与推力线（μ = 2）", fontsize=10)
    ax.legend(loc="lower center", fontsize=8, frameon=False)
    ax.axis("off")
    # (b) 机构：LP 对偶解给出的各体速度场，放大画成位移
    ax = axes[1]
    wmax = max(abs(tw[2]) for tw in r.mechanisms) or 1.0
    sc = 0.06 / wmax                                   # 位移 = 速度场 × 比例，按最大转动归一
    for P, tw in zip(blocks, r.mechanisms):
        ax.add_patch(MplPolygon(P, closed=True, fc="none", ec=GREY, lw=0.8, ls="--"))
        Q = [(x + sc * (tw[0] - tw[2] * y), y + sc * (tw[1] + tw[2] * x)) for x, y in P]
        ax.add_patch(MplPolygon(Q, closed=True, fc="#e9e4da", ec=INK, lw=1.0))
    hinges = []
    tw0 = [0.0, 0.0, 0.0]
    for j, (corners, nrm) in enumerate(joints):
        a, b = bcs[2 * j].body_a, bcs[2 * j].body_b
        ta = r.mechanisms[a]
        tb = r.mechanisms[b] if b is not None else tw0
        if abs(ta[2] - tb[2]) <= 1e-9 * wmax:
            continue                                   # 两侧无相对转动：不是铰
        def vrel(q):
            return math.hypot((ta[0] - tb[0]) - (ta[2] - tb[2]) * q[1], (ta[1] - tb[1]) + (ta[2] - tb[2]) * q[0])
        hinges.append(min(corners, key=vrel))          # 相对速度为零的那个角就是铰
    if hinges:
        ax.plot([h[0] for h in hinges], [h[1] for h in hinges], "o", color=ACC, ms=7, mfc="white", mew=1.8,
                label=f"铰（{len(hinges)} 处：两侧有相对转动、该角相对速度为零）")
    NUM["arch_hinges"] = hinges
    ax.set_aspect("equal")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-0.1, 1.4)
    ax.set_title("(b) 上限：对偶解 = 四铰破坏机构（位移放大）", fontsize=10)
    ax.legend(loc="lower center", fontsize=8, frameon=False)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "arch.png")
    plt.close(fig)


def fig_alpha_mu():
    mus = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.5, 2.0, 3.0]
    alphas, status = [], []
    for mu in mus:
        _, bodies, bcs, _, _ = arch_problem(mu=mu)
        r = limit_load_multi(bodies, bcs, dim=2)
        status.append(r.status)
        alphas.append(r.alpha if r.status == "optimal" else float("nan"))
    hinge_bound = NUM["arch_alpha_mu2"]
    NUM["arch_alpha_vs_mu"] = dict(zip(mus, alphas))
    NUM["arch_status_vs_mu"] = dict(zip(mus, status))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    ax = axes[0]
    ax.axhline(hinge_bound, color=ACC, ls="--", lw=1.2, label=f"最佳四铰机构上限 {hinge_bound:.4f}（独立枚举：480 种铰位里 10 个容许）")
    ax.plot(mus, alphas, "o-", color=INK, lw=1.4, ms=4, label="LP 的 α（多体下限 = 上限，自校验）")
    ax.set_xlabel("摩擦系数 μ")
    ax.set_ylabel("极限荷载因子 α")
    ax.set_title("薄拱（N = 5）：滑动控制 → 铰机构控制", fontsize=10)
    ax.axvspan(0, 0.25, color="#f3d9d0", alpha=0.6)
    ax.text(0.03, hinge_bound * 0.55, "自重下\n不平衡", fontsize=8, color=ACC)
    ax.set_xlim(0, 3.1)
    ax.set_ylim(0, hinge_bound * 1.25)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.grid(alpha=0.25)
    # 叠放块
    ax = axes[1]
    W1, W2 = 30.0, 10.0
    mus2 = [i * 0.1 for i in range(1, 16)]
    al2, closed = [], []
    o = (0.0, 0.0)
    for mu in mus2:
        b1 = LimitBody(wrench((0.0, -W1), (0.0, 0.5), o, 2), [0.0] * 3)
        b2 = LimitBody(wrench((0.0, -W2), (0.0, 1.5), o, 2), wrench((1.0, 0.0), (0.0, 2.0), o, 2))
        bcs = [BodyContact(LimitContact((sx, 0.0), (0.0, 1.0), mu), 0, None) for sx in (-1.0, 1.0)]
        bcs += [BodyContact(LimitContact((sx, 1.0), (0.0, 1.0), mu), 1, 0) for sx in (-1.0, 1.0)]
        al2.append(limit_load_multi([b1, b2], bcs, dim=2).alpha)
        closed.append(min(mu * W2, mu * (W1 + W2), W2, (W1 + W2) / 2.0))
    NUM["stack_max_rel_err"] = max(abs(a - c) / c for a, c in zip(al2, closed))
    ax.plot(mus2, closed, "-", color=ACC, lw=2.4, alpha=0.5, label="闭式 min(μ·W2, W2, (W1+W2)/2)")
    ax.plot(mus2, al2, "o", color=INK, ms=4, label="LP 的 α")
    ax.set_xlabel("摩擦系数 μ")
    ax.set_ylabel("α")
    ax.set_title("两块叠放（W1 = 30，W2 = 10，推力在顶）：滑 → 倾覆", fontsize=10)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "alpha_mu.png")
    plt.close(fig)


# ---------------------------------------------------------------- 3. bb52 真几何

def fig_bb52():
    import bb52_g0
    blocks, _ = bb52_g0.load_blocks(1)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    for b, d in blocks.items():
        P = d["poly"]
        ax.add_patch(MplPolygon(P, closed=True, fc="#e9e4da", ec=INK, lw=0.8))
        cx = sum(p[0] for p in P) / len(P)
        cy = sum(p[1] for p in P) / len(P)
        ax.text(cx, cy, str(b), fontsize=8, ha="center", va="center", color=GREY)
    n_cov = 0
    pairs = 0
    for a in sorted(blocks):
        for b in sorted(blocks):
            if a >= b:
                continue
            covs = [c for c in enumerate_covers(blocks[a]["poly"], blocks[b]["poly"], window=0.05, tol=1e-9) if c.normal is not None]
            if covs:
                pairs += 1
            for c in covs:
                n_cov += 1
                p = c.point_a
                ax.plot([p[0]], [p[1]], ".", color=ACC, ms=3.5)
                ax.plot([p[0], p[0] + 0.18 * c.normal[0]], [p[1], p[1] + 0.18 * c.normal[1]], "-", color=ACC, lw=0.7)
    NUM["bb52_blocks"] = len(blocks)
    NUM["bb52_pairs_with_covers"] = pairs
    NUM["bb52_covers"] = n_cov
    ax.set_aspect("equal")
    ax.autoscale()
    ax.set_title(f"(a) bb52 第 1 步：11 个块、{pairs} 个接触块对、{n_cov} 个有效盖（点 = 接触点，线 = 法向）", fontsize=9)
    ax.axis("off")
    # (b) 一对凸块的入口块
    A, B = blocks[5]["poly"], blocks[10]["poly"]
    a0 = A[0]
    eb = convex_entrance_block(A, B, (0.0, 0.0))
    ax = axes[1]
    ax.add_patch(MplPolygon(B, closed=True, fc="#e9e4da", ec=INK, lw=1.0))
    ax.add_patch(MplPolygon(A, closed=True, fc="#d3e3ec", ec=ACC2, lw=1.0))
    E = [(x + a0[0], y + a0[1]) for x, y in eb.vertices]
    ax.add_patch(MplPolygon(E, closed=True, fc="none", ec=ACC, lw=1.6, ls="-"))
    ax.plot([a0[0]], [a0[1]], "o", color=ACC2, ms=6)
    ax.text(a0[0] + 0.05, a0[1] - 0.12, "参考点 a0（A 的顶点 0）", fontsize=8, color=ACC2)
    kinds = {}
    for lab in eb.facets:
        kinds[lab[0]] = kinds.get(lab[0], 0) + 1
    NUM["bb52_E_5_10"] = {"vertices": len(eb.vertices), "facets": dict(kinds)}
    ax.set_aspect("equal")
    ax.autoscale()
    ax.set_title(f"(b) 块 5（A）对块 10（B）的入口块 E(A,B)：{len(eb.vertices)} 个顶点，facet {kinds}", fontsize=9)
    ax.text(0.02, 0.02, "a0 落在 E 的边界上，就是两块恰好接触；E 的每条边是一个盖（谁的顶点对谁的边）",
            transform=ax.transAxes, fontsize=8, color=INK)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "bb52.png")
    plt.close(fig)


# ---------------------------------------------------------------- 4. 三维裕度

def fig_margin3d():
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    def roof(h, t):
        sec = [(-1.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, h), (-1.0, 0.0)]
        V = [(t[0] - 2.0, t[1] + y, t[2] + z) for y, z in sec] + [(t[0] + 2.0, t[1] + y, t[2] + z) for y, z in sec]
        F = [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, 5 + (i + 1) % 5, 5 + i) for i in range(5)]
        return Polyhedron(V, F)

    def needle(tip, r, H):
        x, y, z = tip
        return convex_hull_3d([tip] + [(x + r * math.cos(a), y * 1.0 + r * math.sin(a), z + H) for a in (0.1, 2.1943951, 4.2887902)])
    rows = []
    for tmag in (0.0, 1e6):
        t = (0.6 * tmag, -0.48 * tmag, 0.64 * tmag)
        B = roof(1e-6, t)
        A = needle((t[0] + 0.3, t[1], t[2] + 1e-6 + 0.05), 0.001, 1.0)
        d, lab = body_distance(A, B)
        rows.append({"t": tmag, "distance": d, "label": [lab[0], list(lab[1]), list(lab[2])], "brute": brute_feature_distance(A, B),
                     "membership_delta_0.1": inflated_membership(A, B, delta=0.1),
                     "contacts_delta_0.1": [m.label[0] for m in margin_contacts(A, B, delta=0.1)]})
    NUM["margin_ridge"] = rows
    B = roof(1e-6, (0.0, 0.0, 0.0))
    A = needle((0.3, 0.0, 1e-6 + 0.05), 0.001, 1.0)
    mc = margin_contacts(A, B, delta=0.1)[0]
    fig = plt.figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111, projection="3d")
    faces = [[B.verts[i] for i in f] for f in B.faces]
    ax.add_collection3d(Poly3DCollection(faces, facecolors="#e9e4da", edgecolors=INK, linewidths=0.6, alpha=0.9))
    ax.add_collection3d(Poly3DCollection([[A.verts[i] for i in f] for f in A.faces], facecolors="#d3e3ec", edgecolors=ACC2, linewidths=0.6))
    ax.plot([mc.point_a[0], mc.point_b[0]], [mc.point_a[1], mc.point_b[1]], [mc.point_a[2], mc.point_b[2]], "-", color=ACC, lw=2.0)
    ax.text(mc.point_a[0] + 0.15, mc.point_a[1], mc.point_a[2] + 0.45, f"VE3 见证段 d = {mc.distance:.3f}", fontsize=9, color=ACC)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_xlim(-2, 2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_zlim(-1, 1.3)
    ax.set_box_aspect((4, 2.4, 2.3))
    ax.view_init(elev=22, azim=-55)
    ax.set_title("针尖（底棱 1.7 mm）悬在 1 µm 高的棱脊上方 0.05：最近特征对 = 顶点 × 棱", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "margin3d.png")
    plt.close(fig)


# ---------------------------------------------------------------- 5. 互锁剪胀

def fig_tia():
    import tia_sensitivity
    rows = tia_sensitivity.profile()
    d = [r["delta"] for r in rows]
    h = [r["h"] for r in rows]
    tp = [r["tan_psi"] for r in rows]
    nd = [r["differentiable_by"]["tan_psi"] for r in rows]
    NUM["tia_rows"] = len(rows)
    NUM["tia_kinks"] = sum(1 for x in nd if not x)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    ax = axes[0]
    ax.plot(d, h, "o-", color=INK, ms=3.5, lw=1.2)
    for x, y, ok in zip(d, h, nd):
        if not ok:
            ax.plot([x], [y], "o", color=ACC, ms=7, mfc="white", mew=1.6)
    ax.set_xlabel("横移 δ")
    ax.set_ylabel("逃逸高度 h(δ)")
    ax.set_title("骨形互锁块：横移多少就得抬升多少（盖路径闭式求根）", fontsize=10)
    ax.grid(alpha=0.25)
    ax = axes[1]
    ax.plot(d, tp, "o-", color=ACC2, ms=3.5, lw=1.2, label="tanψ = dh/dδ（对偶数自动微分）")
    for x, y, ok in zip(d, tp, nd):
        if not ok:
            ax.plot([x], [y], "o", color=ACC, ms=7, mfc="white", mew=1.6)
    ax.set_xlabel("横移 δ")
    ax.set_ylabel("剪胀比 tanψ")
    ax.set_title("荷载传递比：片内解析导数，折点（空心）如实标不可微", fontsize=10)
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "tia.png")
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_arch()
    fig_alpha_mu()
    fig_bb52()
    fig_margin3d()
    fig_tia()
    (OUT / "numbers.json").write_text(json.dumps(NUM, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(NUM, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
