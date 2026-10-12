"""R7 document contracts and the closed-cavity counterexample.

The cavity oracle uses only exact interval products and connectedness, not any
production geometry primitive. Production overlap/margin are the tested side.
Document mutation guards pass altered actual file contents through the same
assertions as the current-document gates; they do not fabricate runtime output.
"""
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import pytest

from eab.kernel3d.geom3 import Polyhedron, polyhedra_overlap
from eab.margin import body_distance, inflated_membership, INSIDE, ON_BOUNDARY, PENETRATING
from eab.kernel3d.exact_sweep import contact_models
from eab.margin import _penetration_within_window


ROOT = Path(__file__).resolve().parents[1]
CURRENT_WINDOW_DOCS = (
    "README.md", "docs/canon_map.md", "docs/exact_3d_design.md",
    "docs/exact_predicates_plan.md", "reports/codex/PERF_report.md",
)
FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def _assert_window_document(text):
    assert "PD_closed" in text and "rho" in text, "G6G-09: distinguish closed-set PD from interior nonintersection"
    assert "下确界" in text, "G6G-09: closed-set separation is an infimum, not a attained minimum"
    assert "六轴脱离证书 ⇒ PD ≤ w" not in text, "G6G-09: axis acceptance does not bound PD_closed"
    assert "因而 `PD ≤" not in text and "因此 PD≤" not in text, "G6G-09: interior nonintersection does not imply closed separation"


@pytest.mark.parametrize("path", CURRENT_WINDOW_DOCS)
def test_g6g09_window_documents_distinguish_closed_separation_infimum(path):
    _assert_window_document(_read(path))


@pytest.mark.parametrize("function", (contact_models, _penetration_within_window, inflated_membership))
def test_g6g09_window_runtime_docstrings_do_not_promise_closed_separation(function):
    assert "rho" in function.__doc__ and "PD_closed" in function.__doc__
    assert "infimum" in function.__doc__


def _box(half, center=(0, 0, 0)):
    signs = ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))
    # All inputs in this reproduction are exactly representable binary64.
    return Polyhedron([tuple(float(F(center[k]) + s[k]*half) for k in range(3))
                       for s in signs], list(FACES))


def test_g6g09_tight_closed_cavity_distinguishes_rho_from_pd_closed():
    """Oracle: independent box intervals, not production SAT/point/triangles.

    A connected cube avoiding the closed shell must lie wholly in its open
    cavity or wholly outside the outer cube. An equal-size cube cannot fit
    strictly in the cavity. Escaping the outer cube requires one strict axis
    gap: its smallest norm has infimum 19/8, not attained. Interior disjointness
    does allow the exactly fitting cube, at the unique displacement +1/8 e_x.
    """
    h, outer_h, w = F(1, 2), F(2), F(1, 8)
    center = (-w, F(0), F(0))
    A, outer, inner = _box(h, center), _box(outer_h), _box(h)
    B = Polyhedron([*outer.verts, *inner.verts],
                   [*outer.faces, *(tuple(i+8 for i in reversed(f)) for f in inner.faces)])
    At = Polyhedron([tuple(F(p[k]) + (w if k == 0 else 0) for k in range(3))
                     for p in A.verts], A.faces)
    assert set(A.verts) == set(product(*[(c-h, c+h) for c in center]))
    assert set(At.verts) == set(product((-h, h), repeat=3))
    assert set(B.verts[:8]) == set(product((-outer_h, outer_h), repeat=3))
    assert set(B.verts[8:]) == set(product((-h, h), repeat=3))
    pd_closed = min(outer_h + h - abs(c) for c in center)
    rho = min(w, pd_closed)
    assert rho == w == F(1, 8) and pd_closed == F(19, 8) > w
    # At the minimizing outer displacement the cubes still touch; arbitrarily
    # small further shifts strictly separate. This explicitly checks inf, not min.
    assert center[0] - pd_closed + h == -outer_h
    for epsilon in (F(1, 16), F(1, 1024), F(1, 2**80)):
        assert center[0] - pd_closed - epsilon + h < -outer_h
    assert polyhedra_overlap(A, B, 0) == 1
    assert polyhedra_overlap(At, B, 0) == 0
    assert body_distance(A, B) == (0, (PENETRATING,))
    assert inflated_membership(A, B, delta=0) == INSIDE
    assert body_distance(A, B, contact_window=w)[0] == 0
    assert inflated_membership(A, B, delta=0, contact_window=w) == ON_BOUNDARY


def _assert_current_status(readme, canon):
    assert "仍以暴力 `polygons_overlap` 检验距离/出口完备性" not in readme, "G6G-10: stale production oracle claim"
    assert "g0_oracle" in readme, "G6G-10: identify the independent current oracle"
    status = next(line for line in canon.splitlines() if line.startswith("**状态更新"))
    assert "仍开放" not in status, "G6G-10: GAP3 cannot be both open and disposed"
    assert "GAP3（正本对代码）已按各轮报告逐条处置" in canon


def test_g6g10_readme_oracle_and_canon_status_are_current(monkeypatch):
    _assert_current_status(_read("README.md"), _read("docs/canon_map.md"))
    # The README's independence assertion is also checked against execution.
    from eab.kernel2d import g0, geom
    def forbidden(*args, **kwargs):
        raise AssertionError("G6G-10: independent G0 must not call production polygons_overlap")
    monkeypatch.setattr(geom, "polygons_overlap", forbidden)
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]
    report = g0.g0_distance_completeness(square, square, [(2, 0)])
    assert report.passed and report.samples == 1


def _assert_no_priority_advice(canon):
    row = next(line for line in canon.splitlines() if line.startswith('| 07 第 33 行'))
    assert "对外须限定为" not in row, "G6G-11: narrowing priority to DDA is still a false claim"
    assert "不成立" in row and "一份独立实现" in row, "G6G-11: explicitly withdraw the priority claim"
    assert "Zheng" in row and "Zhao" in row and "Ni" in row and "Feng" in row


def test_g6g11_priority_claim_is_withdrawn_instead_of_narrowed():
    _assert_no_priority_advice(_read("docs/canon_map.md"))
    assert "第一份独立 oracle" not in _read("AGENTS.md").splitlines()[2]
    assert "将成为第一份" not in _read("docs/sibling_observations.md")


def test_g6g09_document_gate_rejects_restored_old_pd_implication():
    current = _read("docs/exact_3d_design.md")
    restored = current.replace("六轴非贯入证书 ⇒ rho ≤ w", "六轴脱离证书 ⇒ PD ≤ w")
    assert restored != current
    with pytest.raises(AssertionError, match="axis acceptance does not bound"):
        _assert_window_document(restored)


def test_g6g10_document_gate_rejects_restored_old_oracle():
    current = _read("README.md")
    restored = current.replace("使用独立 `kernel2d/g0_oracle.py` 的有理区间裁剪、段距离与事件检查检验距离/出口完备性（不调用生产 `polygons_overlap`）",
                               "仍以暴力 `polygons_overlap` 检验距离/出口完备性")
    assert restored != current
    with pytest.raises(AssertionError, match="stale production oracle"):
        _assert_current_status(restored, _read("docs/canon_map.md"))


def test_g6g11_document_gate_rejects_restored_priority_advice():
    current = _read("docs/canon_map.md")
    row = next(line for line in current.splitlines() if line.startswith('| 07 第 33 行'))
    restored = current.replace(row, '| 07 第 33 行旧主张 | — | 对外须限定为"DDA 圈内 / 本课题组代码里第一份" |')
    with pytest.raises(AssertionError, match="narrowing priority"):
        _assert_no_priority_advice(restored)
