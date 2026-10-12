"""L5 static-window adapter gates; oracle shares no production geometry primitive.

The independent oracle is the existing E3 Fraction neighbor-support/Fourier-Motzkin
implementation in test_kernel2d_covers_e3, not covers/geom/exact. Analytic invariance
checks use exact rational rigid transforms and compare the unchanged feature labels.
"""
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
import random

import pytest

from eab.adapters import bdda2d as adapter
from eab.contact_record import CoverType, validate
from eab.readers.bdda_geom import BlockGeom, StepGeometry, load_step_geometries
from test_kernel2d_covers_e3 import independent_cover_oracle


ROOT = Path(__file__).resolve().parents[1]
SLAB = [(-3, -1), (3, -1), (3, 0), (-3, 0)]
TIP = [(0, F(1, 16)), (1, F(17, 16)), (-1, F(17, 16))]
# Slightly rotated square: both lower vertices belong to the 3-degree window,
# but only one belongs to the exact downward supporting cone.
TILTED = [(0, F(1, 16)), (1, F(5, 64)), (F(63, 64), F(69, 64)), (-F(1, 64), F(17, 16))]


def _geometry(A=TIP, B=SLAB, reverse=False):
    ai, bi = (7, 2) if reverse else (2, 7)
    return StepGeometry(3, {ai: BlockGeom(ai, list(A), list(range(100, 100+len(A))), False),
                            bi: BlockGeom(bi, list(B), list(range(200, 200+len(B))), False)})


def _window(**kwargs):
    return adapter.Bdda2DWindow(3, F(1, 8), 3, **kwargs)


def _key_from_label(kind, i, j, A, B):
    if kind == "EV":
        return _key_from_label("VE", j, i, B, A)
    return (kind, A.block, A.vidx[i], B.block, B.vidx[j])


def _record_key(rec):
    return (rec.cover.value, rec.block_a, rec.feature_a.index, rec.block_b, rec.feature_b.index)


def _assert_matches_independent_oracle(geometry, window):
    """No shared production geometry: oracle is Fraction neighbor support and elimination."""
    expected = set()
    ids = sorted(geometry.blocks)
    for k, ai in enumerate(ids):
        for bi in ids[k+1:]:
            A, B = geometry.blocks[ai], geometry.blocks[bi]
            for kind, i, j, strict in independent_cover_oracle(
                    A.poly, B.poly, window.d0, cone_tol=window.cone_tol, seg_tol=window.seg_tol):
                expected.add(_key_from_label(kind, i, j, A, B))
    records = adapter.detect_step(geometry, window)
    actual = {_record_key(rec) for rec in records}
    assert actual == expected, "static domain-window membership differs from independent exact oracle"
    assert len(records) == len(actual), "adapter emitted duplicate feature keys"
    for rec in records:
        validate(rec)
        assert rec.extra["observable"] == adapter.OBSERVABLE
    return records


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("A", [TIP, TILTED])
@pytest.mark.parametrize("d0", [F(1, 32), F(1, 16), F(1, 8), F(3)])
def test_static_domain_window_matches_independent_exact_oracle(reverse, A, d0):
    _assert_matches_independent_oracle(_geometry(A, reverse=reverse), replace(_window(), d0=d0))


@pytest.mark.parametrize("reverse", [False, True])
def test_vertex_edge_record_direction_and_global_ids_do_not_depend_on_block_sort(reverse):
    records = _assert_matches_independent_oracle(_geometry(reverse=reverse), _window())
    assert len(records) == 1
    rec = records[0]
    assert rec.cover == CoverType.VE
    assert rec.feature_a.index == 100 and rec.feature_b.index == 202
    assert rec.normal == (0, 1) and rec.gap == F(1, 16)
    assert rec.params == (F(1, 2),)
    assert rec.length_or_area == 6
    assert rec.extra["edge_vertices"] == (202, 203)
    assert rec.feature_a.kind == "vertex" and rec.feature_b.kind == "edge"
    assert rec.entrance_index is None


@pytest.mark.parametrize("drop", ["distance", "angle", "segment"])
def test_dropping_an_adapter_window_is_caught_inside_the_enumeration_path(monkeypatch, drop):
    """Mutate real call arguments, not returned records; membership assertion must reject it."""
    geometry, window = _geometry(TILTED), _window()
    if drop == "segment":
        A = [(-F(1, 10**10), 0), (-1, 1), (-2, 1)]
        B = [(0, -1), (1, -1), (1, 0), (0, 0)]
        geometry, window = _geometry(A, B), replace(window, d0=0)
    _assert_matches_independent_oracle(geometry, window)
    real = adapter.covers.enumerate_covers

    def mutated(A, B, **kwargs):
        kwargs[{"distance": "window", "angle": "cone_tol", "segment": "seg_tol"}[drop]] = (
            100 if drop == "distance" else 0)
        return real(A, B, **kwargs)

    monkeypatch.setattr(adapter.covers, "enumerate_covers", mutated)
    with pytest.raises(AssertionError, match="static domain-window membership"):
        _assert_matches_independent_oracle(geometry, window)


def test_exact_broadphase_includes_the_segment_extension_and_has_teeth(monkeypatch):
    A = [(-F(1, 10**10), 0), (-1, 1), (-2, 1)]
    B = [(0, -1), (1, -1), (1, 0), (0, 0)]
    geometry, window = _geometry(A, B), replace(_window(), d0=0)
    records = _assert_matches_independent_oracle(geometry, window)
    assert len(records) == 1
    real = adapter._boxes_may_meet
    monkeypatch.setattr(adapter, "_boxes_may_meet", lambda a, b, w: real(a, b, replace(w, seg_tol=0)))
    with pytest.raises(AssertionError, match="static domain-window membership"):
        _assert_matches_independent_oracle(geometry, window)


@pytest.mark.parametrize("translation", [0, 10**3, 10**5, 10**6])
@pytest.mark.parametrize("scale", [F(1, 1000), F(1), F(1000)])
@pytest.mark.parametrize("seed", [43, 59])
def test_static_contact_labels_normals_and_gaps_obey_exact_rigid_and_unit_transform(translation, scale, seed):
    """Oracle: analytic tip/slab and rational SO(2); no production geometric primitive."""
    rng = random.Random(seed)
    tangent = F(rng.randint(-19, 19), 23)
    c, s = (1-tangent*tangent)/(1+tangent*tangent), 2*tangent/(1+tangent*tangent)
    shift = (F(3, 5)*translation, -F(4, 5)*translation)

    def transform(P):
        return [(scale*(c*x-s*y)+shift[0], scale*(s*x+c*y)+shift[1]) for x, y in P]

    geometry = _geometry(transform(TIP), transform(SLAB))
    window = replace(_window(), d0=F(1, 8)*scale, seg_tol=F(1, 10**9)*scale,
                     fit_tol=F(1, 10**6)*scale)
    records = _assert_matches_independent_oracle(geometry, window)
    assert [_record_key(rec) for rec in records] == [("VE", 2, 100, 7, 202)]
    rec = records[0]
    assert abs(F(rec.gap)-F(1, 16)*scale) <= F(1, 10**14)*scale
    assert abs(F(rec.normal[0])+s) < F(1, 10**14)
    assert abs(F(rec.normal[1])-c) < F(1, 10**14)


def test_window_loader_uses_each_step_and_marks_only_missing_parameters(tmp_path):
    p = tmp_path / "bdda_debug_detparams.csv"
    p.write_text("step,d0,h1,w0\n1,0.1,3,7\n2,0.2,4,8\n", encoding="utf-8")
    first, second = adapter.load_window(tmp_path, 1), adapter.load_window(tmp_path, 2)
    assert (first.d0, first.h1_degrees, second.d0, second.h1_degrees) == (0.1, 3, 0.2, 4)
    assert second.raw_parameters["w0"] == 8 and second.fallback_fields == ()
    with pytest.raises(ValueError, match="expected one row, got 0"):
        adapter.load_window(tmp_path, 3)
    p.write_text("step,d0,h1\n1,0.1,3\n1,0.1,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected one row, got 2"):
        adapter.load_window(tmp_path, 1)
    p.write_text("step,d0\n1,0.1\n", encoding="utf-8")
    fallback = adapter.load_window(tmp_path, 1)
    assert fallback.fallback_fields == ("h1",) and fallback.h1_degrees == 3
    assert fallback.source == "detparams+bb52_fallback"


def test_missing_detparams_is_an_explicit_bb52_fallback_not_an_unreported_default(tmp_path):
    window = adapter.load_window(tmp_path, 4)
    assert window.d0 == adapter.FALLBACK_D0
    assert window.h1_degrees == 3
    assert window.seg_tol == 1e-9 and window.fit_tol == 1e-6
    assert window.fallback_fields == ("d0", "h1")
    assert window.source == "bb52_fallback:no_detparams"


@pytest.mark.parametrize("kwargs", [{"d0": -1}, {"d0": float("inf")}, {"h1_degrees": 90},
                                    {"h1_degrees": -1}, {"seg_tol": -1}, {"fit_tol": -1}])
def test_illegal_windows_fail_loud(kwargs):
    with pytest.raises(ValueError):
        replace(_window(), **kwargs)


def test_step_mismatch_fails_loud():
    with pytest.raises(ValueError, match="geometry step"):
        adapter.detect_step(_geometry(), replace(_window(), step=4))


def test_bb52_static_legacy_window_retains_all_53_previously_verified_vertex_edge_contacts():
    fixture = ROOT / "fixtures" / "bdda_df" / "studio_20260712"
    geometry = load_step_geometries(fixture / "bdda_debug_verts.csv")[1]
    records = adapter.detect_step(geometry, adapter.load_window(fixture, 1))
    # This is the legacy seam check, not the primary geometric oracle above.
    from eab.readers.bdda_df import load_records
    legacy = [r for r in load_records(fixture) if r.step == 1 and r.cover == CoverType.VE]
    assert len(legacy) == 53
    got = {r.canonical_key(): r for r in records}
    assert all(r.canonical_key() in got for r in legacy)
    assert [r.canonical_key() for r in records] == sorted(got)
    assert [r.contact_index for r in records] == list(range(1, len(records)+1))
    assert len({r.canonical_key() for r in records}) == len(records)
