"""M2 门：G2 从"集合同构"扩展到**入口选择**——对三份 bdda3d 夹具的每个 legacy 块对，内核沿"动块趋近固定块"方向的首入
退化族（FF）展开成的 VF 成员，必须与 legacy 的 np 入口（动块顶点 × 固定块面）逐条相同；退化族合并前后 legacy 的 4 个 np 入口
能被还原（计划 M2 的门）。oracle 仍是 legacy 的手写入口清单（不是检测器，见 README L1 三维行）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from g2_bdda3d import face_vertex_sets, load_case_full  # noqa: E402

from eab.kernel3d.entrance3 import first_entrance3  # noqa: E402

FIXTURES = sorted((ROOT / "fixtures" / "bdda3d").glob("*.json"))


def _centroid(P):
    return tuple(sum(p[i] for p in P.verts) / len(P.verts) for i in range(3))


@pytest.mark.parametrize("path", FIXTURES, ids=[p.stem for p in FIXTURES])
def test_first_entrance_members_reproduce_the_legacy_np_entrances(path):
    lc = load_case_full(path, tol=1e-9)
    blocks, aliases, entrances = lc["blocks"], lc["aliases"], lc["entrances"]

    def canon(b: int, i: int) -> int:
        return aliases[b].get(i, i)

    pairs = sorted({(e["bi"], e["bj"]) for e in entrances})
    assert pairs
    for bi, bj in pairs:
        A, B = blocks[bi], blocks[bj]
        faces_B = face_vertex_sets(B)
        legacy = set()
        for e in entrances:
            if (e["bi"], e["bj"]) != (bi, bj):
                continue
            assert e["etype"] == "np"
            refs = [(int(b), canon(int(b), int(i))) for b, i in e["refs"]]
            vblk, vidx = refs[0]
            tri = [r[1] for r in refs[1:]]
            assert vblk == bi and {r[0] for r in refs[1:]} == {bj}
            gi = next(k for k, vs in enumerate(faces_B) if set(tri) <= vs)
            legacy.add((vidx, gi))
        # 动块趋近固定块：方向取形心差（夹具里两块已相触，首入在 t = 0）
        ca, cb = _centroid(A), _centroid(B)
        d = tuple(cb[i] - ca[i] for i in range(3))
        e = first_entrance3(A, B, (0.0, 0.0, 0.0), d)
        assert e.kind == "entrance" and abs(e.t) <= 1e-9, (path.stem, (bi, bj), e.kind, e.t)
        assert e.label[0] == "FF", (path.stem, (bi, bj), e.label, e.members)
        mine = set()
        for lab in e.members:
            assert lab[0] == "VF", lab                               # 展开视图：动块顶点 × 固定块面
            gi = next(k for k, vs in enumerate(faces_B) if set(B.faces[lab[2][1]]) <= vs)
            mine.add((lab[1][1], gi))
        assert mine == legacy, (path.stem, (bi, bj), sorted(mine), sorted(legacy))
        assert len(e.members) == len(legacy) == 4
