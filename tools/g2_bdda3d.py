"""G2 三维同构门 · 对 bdda3d 的入口列表。

**三维接触枚举此前没有任何 legacy 对账通道**（见 docs/sibling_observations.md）。
这是第一次。

对账口径（守同构、不守逐字节 —— AGENTS.md §2）：
  · bdda3d 的 `np` 入口 = (动块的一个顶点, 固定块面上的一个三角形)；
    盖内核的 VF 盖 = (动块的一个顶点, 固定块的一个**面**)。
    同一个面可以被 legacy 用不同的顶点三元组表示（实测 cb2 里同时出现 (4,7,6) 与 (4,6,5)），
    所以匹配必须把三元组归约到"它所在的那个面"，而不是比顶点号。
  · 顶点编号必须沿用夹具里的编号：凸包会重编号，故用坐标精确回映。
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


def polyhedron_preserving_indices(pts: list[tuple[float, float, float]],
                                  tol: float = 1e-9) -> Polyhedron:
    """由点集造凸多面体，但**沿用输入的顶点编号**（凸包会重编号，这里按坐标回映）。"""
    hull = merge_coplanar(convex_hull_3d(pts), tol)
    remap: dict[int, int] = {}
    for hi, hv in enumerate(hull.verts):
        best, bd = None, float("inf")
        for oi, ov in enumerate(pts):
            d = norm(sub(hv, ov))
            if d < bd:
                best, bd = oi, d
        if bd > tol:
            raise ValueError(f"hull vertex {hi} has no original counterpart (d={bd})")
        remap[hi] = best
    faces = [tuple(remap[i] for i in f) for f in hull.faces]
    return Polyhedron(list(pts), faces)


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


def load_case(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    blocks = {int(k): polyhedron_preserving_indices([tuple(v) for v in vs])
              for k, vs in d["verts"].items()}
    return d["case"], d["step"], blocks, d["entrances"]


def compare(path: Path, *, window: float = 1.0, tol: float = 1e-9) -> dict:
    case, step, blocks, entrances = load_case(path)
    pairs = sorted({(e["bi"], e["bj"]) for e in entrances})
    rows = []
    for bi, bj in pairs:
        A, B = blocks[bi], blocks[bj]
        faces_B = face_vertex_sets(B)
        faces_A = face_vertex_sets(A)

        # legacy 侧：np 入口 → (动顶点, 该三元组所在的几何面下标)
        legacy = set()
        legacy_detail = []
        for e in entrances:
            if (e["bi"], e["bj"]) != (bi, bj):
                continue
            if e["etype"] != "np":
                legacy_detail.append(("UNSUPPORTED", e["etype"], tuple(map(tuple, e["refs"]))))
                continue
            refs = e["refs"]
            vblk, vidx = refs[0]
            tri = [r[1] for r in refs[1:]]
            triblk = {r[0] for r in refs[1:]}
            assert len(triblk) == 1, refs
            host = blocks[triblk.pop()]
            hostfaces = faces_B if host is B else faces_A
            gi = next((k for k, vs in enumerate(hostfaces) if set(tri) <= vs), None)
            assert gi is not None, f"triple {tri} not on any face"
            legacy.add((vblk, vidx, gi))
            legacy_detail.append((vblk, vidx, tuple(tri), gi))

        # 内核侧：VF / FV 盖 → 同一形式的键
        covs = [c for c in enumerate_covers3(A, B, window=window, tol=tol) if c.in_extent]
        mine = set()
        mine_detail = []
        for c in covs:
            if c.kind == "VF":
                gi = next((k for k, vs in enumerate(faces_B) if set(B.faces[c.b_feature[1]]) <= vs), None)
                key = (bi, c.a_feature[1], gi)
            elif c.kind == "FV":
                gi = next((k for k, vs in enumerate(faces_A) if set(A.faces[c.a_feature[1]]) <= vs), None)
                key = (bj, c.b_feature[1], gi)
            else:
                mine_detail.append((c.kind, c.a_feature, c.b_feature, round(c.gap, 12), c.strict))
                continue
            mine.add(key)
            mine_detail.append((c.kind, key, round(c.gap, 12),
                                tuple(round(x, 12) for x in c.normal) if c.normal else None, c.strict))
        rows.append({"pair": (bi, bj), "legacy": sorted(legacy), "mine": sorted(mine),
                     "legacy_only": sorted(legacy - mine), "mine_only": sorted(mine - legacy),
                     "legacy_detail": legacy_detail, "mine_detail": mine_detail,
                     "n_covers": len(covs)})
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
