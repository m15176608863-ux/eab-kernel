"""G2 三维同构门 · 对 bdda3d 的入口列表。

**三维接触枚举此前没有任何 legacy 对账通道**（见 docs/sibling_observations.md）。
这是第一次。

对账口径（守同构、不守逐字节 —— AGENTS.md §2）：
  · bdda3d 的 `np` 入口 = (动块的一个顶点, 固定块面上的一个三角形)；
    盖内核的 VF 盖 = (动块的一个顶点, 固定块的一个**面**)。
    同一个面可以被 legacy 用不同的顶点三元组表示（实测 cb2 里同时出现 (4,7,6) 与 (4,6,5)），
    所以匹配必须把三元组归约到"它所在的那个面"，而不是比顶点号。
  · 顶点编号必须沿用夹具里的编号：凸包会重编号，故用坐标精确回映。
    不是凸包角点的输入顶点：tol 内重复某角点者登记 alias（legacy 引用按 alias 归并）；
    其余（棱中点 / 面中点 T 形顶点、内点）构造时即报错，带块号与顶点号（审查 C18）。

门的判据（审查 C17：原门对非 VF 结构性失明）——每个块对：
  · legacy_only == [] 且 mine_only == []（np↔VF/FV 两个方向零差异）；
  · `violations` 为空：legacy 有门不认识的入口类（目前除 np 外全部，含 ee）即红；
    内核在对账窗口内的盖凡未参与对账（EE/VE3/EV3/VV3/…，或两个盖归到同一个键）即红。
  对账窗口 `G2_WINDOW` 见其注释；ee↔EE 的键尚未实现，所以带 ee 的夹具目前**必红**，不是静默绿。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.kernel3d.covers3 import enumerate_covers3  # noqa: E402
from eab.kernel3d.geom3 import (Polyhedron, convex_hull_3d, cross, dot, merge_coplanar,  # noqa: E402
                                norm, sub)


# 对账窗口（长度量纲）。理由：legacy 入口是它自己检测层选出的接触，这三份夹具里全部是零间隙坐落
# （顶点到所指三角平面的距离恰为 0）；窗口必须装得下 legacy 的全部间隙，又必须远小于夹具里任何
# "非面接触"特征对的距离（cb2 里最近的是上块底角到下块顶棱，= 1.0），否则窗口里会混进 legacy 根本
# 不会列出的远处特征对。1e-6：≫ 浮点噪声（坐标是小整数，间隙精确为 0），≪ 1.0。
# 两条都由 tests/test_g2_bdda3d.py::test_g2_window_contains_every_legacy_gap_and_nothing_else 看着。
# 将来夹具的 legacy 入口若带正间隙（legacy 搜索距离内的"近接触"），门会以 legacy_only 报红——不会静默。
G2_WINDOW = 1e-6


def polyhedron_with_aliases(pts: list[tuple[float, float, float]], tol: float = 1e-9, *,
                            block: int | None = None) -> tuple[Polyhedron, dict[int, int]]:
    """由点集造凸多面体，**沿用输入的顶点编号**（凸包会重编号，这里按坐标回映），并交代每个输入顶点。

    先把 tol 内的（近）重复点归并到最小下标的代表（alias[i] = 代表），只用代表建凸包——否则近重复点
    会双双成为凸包角点、夹出一条细缝面，内核对两者各出一个盖（2026-09-24 实测）。然后每个代表要么
    被某个面引用（凸包角点），要么（棱中点 / 面中点这类 T 形顶点，或内点）→ ValueError，带块号、
    顶点号、坐标与分类。不许静默保留一个未被任何面引用的顶点（审查 C18）。
    """
    n = len(pts)
    rep = list(range(n))
    for i in range(n):
        for j in range(i):
            if rep[j] == j and norm(sub(pts[i], pts[j])) <= tol:
                rep[i] = j
                break
    alias: dict[int, int] = {i: rep[i] for i in range(n) if rep[i] != i}
    reps = [i for i in range(n) if rep[i] == i]
    hull = merge_coplanar(convex_hull_3d([pts[i] for i in reps]), tol)
    remap: dict[int, int] = {}
    for hi, hv in enumerate(hull.verts):
        best, bd = None, float("inf")
        for oi in reps:
            d = norm(sub(hv, pts[oi]))
            if d < bd:
                best, bd = oi, d
        if bd > tol:
            raise ValueError(f"block {block}: hull vertex {hi} has no original counterpart (d={bd})")
        remap[hi] = best
    faces = [tuple(remap[i] for i in f) for f in hull.faces]
    P = Polyhedron(list(pts), faces)
    referenced = sorted({i for f in faces for i in f})
    for i in reps:
        if i in referenced:
            continue
        j = min(referenced, key=lambda r: (norm(sub(pts[i], pts[r])), r))
        d = norm(sub(pts[i], pts[j]))
        on = [fi for fi in range(len(faces))
              if abs(dot(P.face_normal(fi), sub(pts[i], pts[faces[fi][0]]))) <= tol]
        if len(on) >= 2:
            kind = "mid-edge T-junction vertex"
        elif on:
            kind = "mid-face T-junction vertex"
        else:
            kind = "interior (non-hull) vertex"
        raise ValueError(f"block {block}: input vertex {i} {tuple(pts[i])} is not a hull corner and duplicates "
                         f"no corner within tol={tol} (nearest corner {j} at d={d:.3g}): {kind}; "
                         f"legacy refs to it cannot be reduced to a face")
    return P, alias


def polyhedron_preserving_indices(pts: list[tuple[float, float, float]],
                                  tol: float = 1e-9, *, block: int | None = None) -> Polyhedron:
    """`polyhedron_with_aliases` 只取多面体（同样对 T 形顶点报错）；需要把引用归并时用前者拿 alias。"""
    return polyhedron_with_aliases(pts, tol, block=block)[0]


def face_vertex_sets(P: Polyhedron) -> list[set[int]]:
    """几何面的顶点集合。几何已在构造时做过共面归并，所以这里一面即一组。"""
    return [set(f) for f in P.faces]


def plane_of_triple(P: Polyhedron, tri: list[int]):
    a, b, c = (P.verts[i] for i in tri)
    n = cross(sub(b, a), sub(c, a))
    ln = norm(n)
    if ln == 0.0:
        return None
    n = (n[0] / ln, n[1] / ln, n[2] / ln)
    return n, dot(n, a)


def load_case_full(path: Path) -> dict:
    """夹具 → {case, step, blocks: {块号: Polyhedron}, aliases: {块号: {顶点: 规范顶点}}, entrances}。"""
    d = json.loads(path.read_text(encoding="utf-8"))
    blocks, aliases = {}, {}
    for k, vs in d["verts"].items():
        blocks[int(k)], aliases[int(k)] = polyhedron_with_aliases([tuple(v) for v in vs], block=int(k))
    return {"case": d["case"], "step": d["step"], "blocks": blocks, "aliases": aliases,
            "entrances": d["entrances"]}


def load_case(path: Path):
    c = load_case_full(path)
    return c["case"], c["step"], c["blocks"], c["entrances"]


def compare(path: Path, *, window: float = G2_WINDOW, tol: float = 1e-9) -> dict:
    lc = load_case_full(path)
    case, step, blocks, aliases, entrances = lc["case"], lc["step"], lc["blocks"], lc["aliases"], lc["entrances"]

    def canon(b: int, i: int) -> int:
        return aliases[b].get(i, i)

    pairs = sorted({(e["bi"], e["bj"]) for e in entrances})
    rows = []
    for bi, bj in pairs:
        A, B = blocks[bi], blocks[bj]
        faces_B = face_vertex_sets(B)
        faces_A = face_vertex_sets(A)
        violations: list[tuple] = []

        # legacy 侧：np 入口 → (动顶点, 该三元组所在的几何面下标)；顶点号先经 alias 归并
        legacy = set()
        legacy_detail = []
        for e in entrances:
            if (e["bi"], e["bj"]) != (bi, bj):
                continue
            if e["etype"] != "np":
                legacy_detail.append(("UNSUPPORTED", e["etype"], tuple(map(tuple, e["refs"]))))
                violations.append(("legacy entrance type not reconciled by this gate", e["etype"],
                                   tuple(map(tuple, e["refs"]))))
                continue
            refs = [(int(b), canon(int(b), int(i))) for b, i in e["refs"]]
            vblk, vidx = refs[0]
            tri = [r[1] for r in refs[1:]]
            triblk = {r[0] for r in refs[1:]}
            if len(triblk) != 1:
                raise ValueError(f"legacy np entrance {e['refs']}: host triangle spans blocks {sorted(triblk)}")
            hb = triblk.pop()
            hostfaces = faces_B if blocks[hb] is B else faces_A
            gi = next((k for k, vs in enumerate(hostfaces) if set(tri) <= vs), None)
            if gi is None:
                pts = [tuple(blocks[hb].verts[i]) for i in tri]
                raise ValueError(f"block {hb}: legacy triangle {tri} {pts} (refs {e['refs']}) lies on no merged face")
            legacy.add((vblk, vidx, gi))
            legacy_detail.append((vblk, vidx, tuple(tri), gi))

        # 内核侧：VF / FV 盖 → 同一形式的键；其余种类在窗口内出现即违规（门不认识的类不许静默）
        covs = [c for c in enumerate_covers3(A, B, window=window, tol=tol) if c.in_extent]
        mine = set()
        mine_detail = []
        n_reconciled = 0
        for c in covs:
            if c.kind == "VF":
                gi = next((k for k, vs in enumerate(faces_B) if set(B.faces[c.b_feature[1]]) <= vs), None)
                key = (bi, c.a_feature[1], gi)
            elif c.kind == "FV":
                gi = next((k for k, vs in enumerate(faces_A) if set(A.faces[c.a_feature[1]]) <= vs), None)
                key = (bj, c.b_feature[1], gi)
            else:
                mine_detail.append((c.kind, c.a_feature, c.b_feature, round(c.gap, 12), c.strict))
                violations.append(("kernel cover kind not reconciled by this gate", c.kind, c.a_feature,
                                   c.b_feature, round(c.gap, 12)))
                continue
            n_reconciled += 1
            mine.add(key)
            mine_detail.append((c.kind, key, round(c.gap, 12),
                                tuple(round(x, 12) for x in c.normal) if c.normal else None, c.strict))
        if n_reconciled != len(mine):
            violations.append(("kernel VF/FV covers collapse onto fewer keys", n_reconciled, len(mine)))
        rows.append({"pair": (bi, bj), "legacy": sorted(legacy), "mine": sorted(mine),
                     "legacy_only": sorted(legacy - mine), "mine_only": sorted(mine - legacy),
                     "legacy_detail": legacy_detail, "mine_detail": mine_detail,
                     "n_covers": len(covs), "violations": violations, "window": window})
    return {"case": case, "step": step, "rows": rows}


def main() -> int:
    args = sys.argv[1:] or sorted(str(p) for p in (ROOT / "fixtures" / "bdda3d").glob("*.json"))
    allrows = []
    for a in args:
        res = compare(Path(a))
        print(f"\n===== {res['case']}  step {res['step']}")
        for r in res["rows"]:
            print(f"  块对 {r['pair']}：legacy {len(r['legacy'])} 条 / 内核 {len(r['mine'])} 条"
                  f"（有效盖 {r['n_covers']}）")
            print(f"    legacy_only = {r['legacy_only']}")
            print(f"    mine_only   = {r['mine_only']}")
            print(f"    violations  = {r['violations']}")
            for d in r["mine_detail"]:
                print(f"      内核: {d}")
            for d in r["legacy_detail"]:
                print(f"      legacy: {d}")
        allrows.append(res)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "g2_bdda3d.json").write_text(
        json.dumps(allrows, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
