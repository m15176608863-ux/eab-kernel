"""Twenty-four semantic guards execute internally mutated production source.

The unchanged guard passes on production, then its named semantic assertion
must fail on a separately compiled source mutant.  Neither altered outputs,
hash mismatches, incidental exceptions nor changing the expected value count
as mutation kills.  The file on disk is not rewritten.
"""
from pathlib import Path
import sys
from types import ModuleType

import pytest

from eab.kernel2d import se2_cage as production
from t2b_cage_fixtures import (
    closed_disk_certificate, exact_copy, forged_case, instance_of, rectangle, repeat_winding,
)


def _reject_guard(name, semantic):
    def guard(module):
        instance, certificate, expected = forged_case(name)
        result = module.verify_se2_cage(instance, certificate)
        assert not result.valid and result.condition == expected, "semantic: " + semantic
    return guard


def _accept_guard(certificate, semantic):
    def guard(module):
        result = module.verify_se2_cage(instance_of(certificate), exact_copy(certificate))
        assert result.valid, "semantic: " + semantic
    return guard


def _exercise(monkeypatch, name, replacements, guard):
    guard(production)
    source = str(Path(production.__file__).read_text(encoding="utf-8"))
    for old, new in replacements:
        assert source.count(old) == 1, "mutation source site must be unique and present"
        source = source.replace(old, new, 1)
    module_name = "eab.kernel2d._t2b_mutant_" + str(name)
    mutant = ModuleType(module_name)
    monkeypatch.setitem(sys.modules, module_name, mutant)
    exec(compile(source, "<" + module_name + ">", "exec"), mutant.__dict__)
    with pytest.raises(AssertionError, match="semantic:"):
        guard(mutant)


def test_mutation_halved_rotation_contraction_bound_is_killed(monkeypatch):
    _exercise(monkeypatch, "half_rho", [("if rho**2 < bound:", "if rho**2 < bound/4:")],
              _reject_guard("small_rho", "a halved rotation contraction bound is insufficient"))


def test_mutation_nonpositive_radius_is_killed(monkeypatch):
    _exercise(monkeypatch, "negative_radius", [("    if radius <= 0:\n        _fail", "    if False and radius <= 0:\n        _fail")],
              _reject_guard("negative_radius", "a negative enclosing radius must be rejected"))


def test_mutation_open_connection_and_cap_polylines_is_killed(monkeypatch):
    _exercise(monkeypatch, "open_polyline", [
        ("if len(poly) < 2 or poly[0] != poly[-1]:", "if len(poly) < 2:")],
        _reject_guard("open_cap_polyline", "every intermediate homotopy polyline must close explicitly"))


def test_mutation_closed_seam_uses_first_chart_is_killed(monkeypatch):
    _exercise(monkeypatch, "wrong_seam_chart", [
        ("chart_index = 0 if at == 0 else at-1", "chart_index = 0 if at in (0, n) else at-1")],
        _accept_guard(closed_disk_certificate(), "the final lift must be evaluated in the last interval chart"))


def test_mutation_truncated_supplied_witnesses_is_killed(monkeypatch):
    _exercise(monkeypatch, "truncated_witness", [
        ('if len(interval["witnesses"]) != len(interval["loop"])-1:',
         'if False and len(interval["witnesses"]) != len(interval["loop"])-1:'),
        ('if len(link["witnesses"]) != len(chain)-1:',
         'if False and len(link["witnesses"]) != len(chain)-1:'),
        ("if len(row) != len(poly)-1:\n                    _fail", "if False and len(row) != len(poly)-1:\n                    _fail")],
        _reject_guard("truncated_barrier_witness", "every listed barrier segment needs its own witness"))


def test_mutation_unbound_instance_geometry_is_killed(monkeypatch):
    _exercise(monkeypatch, "unbound_instance", [
        ('if instance["moving"] != cert["moving"]:', 'if False and instance["moving"] != cert["moving"]:')],
        _reject_guard("instance_mismatch", "certificate vertices must match the independently supplied instance"))


def test_mutation_both_caps_at_same_end_is_killed(monkeypatch):
    _exercise(monkeypatch, "same_end_caps", [
        ('if sorted(cap["at"] for cap in cert["caps"]) != expected_caps:',
         'if False and sorted(cap["at"] for cap in cert["caps"]) != expected_caps:')],
        _reject_guard("same_end_caps", "two caps must occupy distinct arc endpoints"))


def test_mutation_missing_radius_vertex_bound_is_killed(monkeypatch):
    _exercise(monkeypatch, "small_enclosing_radius", [
        ('if any((v[0]-center[0])**2+(v[1]-center[1])**2 > radius**2\n           for p',
         'if False and any((v[0]-center[0])**2+(v[1]-center[1])**2 > radius**2\n           for p')],
        _reject_guard("undersized_radius", "the enclosing radius must dominate every source vertex norm"))


def test_mutation_searches_for_omitted_witnesses_is_killed(monkeypatch):
    original_loop = ('        for s, ((a, b), (k, l)) in enumerate(zip(zip(interval["loop"], '
                     'interval["loop"][1:]), interval["witnesses"])):')
    searched_loop = '''        witnesses = interval["witnesses"]
        if not witnesses:
            witnesses = tuple(next((k, l)
                for k in range(len(interval["pieces"]))
                for l in range(len(cert["obstacle_pieces"]))
                if _strict_points(_inner(cert, i, k), cert["obstacle_pieces"][l]["ring"], (a, b)))
                for a, b in zip(interval["loop"], interval["loop"][1:]))
        for s, ((a, b), (k, l)) in enumerate(zip(zip(interval["loop"], interval["loop"][1:]), witnesses)):'''
    _exercise(monkeypatch, "search_missing_witness", [
        ('def _interval(value, where):\n',
         'def _interval(value, where):\n    value = dict(value)\n    value.setdefault("witnesses", [])\n'),
        ('if len(interval["witnesses"]) != len(interval["loop"])-1:',
         'if interval["witnesses"] and len(interval["witnesses"]) != len(interval["loop"])-1:'),
        (original_loop, searched_loop)],
        _reject_guard("missing_barrier_witness", "omitted witnesses cannot be silently replaced by a search"))


def test_mutation_nonconvex_inner_polygon_is_killed(monkeypatch):
    _exercise(monkeypatch, "nonconvex_polygon", [
        ('if j not in (i, (i+1) % len(poly)) and _orientation(a, b, p) <= 0:',
         'if False and j not in (i, (i+1) % len(poly)) and _orientation(a, b, p) <= 0:')],
        _reject_guard("nonconvex_disk", "a nonconvex inner polygon cannot use convex separation rows"))


def test_mutation_zero_separating_axis_is_killed(monkeypatch):
    # Entry-point convex-ring validation is intentionally still present.  This
    # independent internal safety guard is tested at the actual SAT primitive;
    # deleting only its defensive check cannot bypass the earlier ring gate.
    def guard(module):
        polygon = tuple(map(tuple, rectangle(-1, -1, 1, 1)))
        repeated = polygon[:1] + polygon
        condition = None
        try:
            module._weak_separated(repeated, polygon)
        except module._Invalid as error:
            condition = error.condition
        assert condition == "V0", "semantic: zero axes must not weakly separate coincident polygons"
    _exercise(monkeypatch, "zero_axis", [("if axis == (0, 0):", "if False and axis == (0, 0):")], guard)


def test_mutation_independent_endpoint_charts_is_killed(monkeypatch):
    _exercise(monkeypatch, "endpoint_charts", [
        ("if not -1 <= low < high <= 1:",
         "if not all(-1 <= _chart(t, t)[2] <= 1 for t in (breaks[i], breaks[i+1])):")],
        _reject_guard("cross_chart_interval", "both endpoints must use the single midpoint-selected chart"))


def test_mutation_omitted_contracted_halfplane_is_killed(monkeypatch):
    _exercise(monkeypatch, "missing_contracted_edge", [
        ("for nx, ny, b in _halfplanes(rotated):", "for nx, ny, b in _halfplanes(rotated)[:-1]:")],
        _reject_guard("missed_contracted_edge", "every source edge must bound the contracted inner polygon"))


def test_mutation_nonstrict_penetration_is_killed(monkeypatch):
    _exercise(monkeypatch, "contact_as_penetration", [
        ("if value <= lower or value >= upper:", "if value < lower or value > upper:")],
        _reject_guard("merely_touching_barrier", "contact alone cannot form a strict penetration barrier"))


def test_mutation_skipped_connections_is_killed(monkeypatch):
    _exercise(monkeypatch, "skip_connections", [
        ('def _check_v5(cert, charts, counts):\n    for family in (key for key in cert if key in ("links", "caps")):',
         'def _check_v5(cert, charts, counts):\n    for family in ("caps",):')],
        _reject_guard("false_link_witness", "a supplied connection witness must really cover its quadrilateral"))


def test_mutation_unchecked_connection_endpoints_is_killed(monkeypatch):
    _exercise(monkeypatch, "wrong_link_endpoints", [
        ('if link["chain"][0] != cert["intervals"][at-1]["loop"] or link["chain"][-1] != cert["intervals"][at % n]["loop"]:',
         'if False and (link["chain"][0] != cert["intervals"][at-1]["loop"] or link["chain"][-1] != cert["intervals"][at % n]["loop"]):')],
        _reject_guard("link_endpoint_mismatch", "the homotopy must connect the actual interval polylines"))


def test_mutation_start_interval_without_zero_is_killed(monkeypatch):
    _exercise(monkeypatch, "wrong_start_interval", [
        ("if not breaks[start] <= 4*k <= breaks[start+1]:", "if False and not breaks[start] <= 4*k <= breaks[start+1]:")],
        _reject_guard("start_interval_without_zero", "the starting interval must contain a lift of zero rotation"))


def test_mutation_cap_uses_absent_side_is_killed(monkeypatch):
    _exercise(monkeypatch, "absent_cap_side", [
        ('if cap and ((at == 0 and kind == "left") or (at == n and kind == "right")):',
         'if False and cap and ((at == 0 and kind == "left") or (at == n and kind == "right")):')],
        _reject_guard("wrong_cap_side", "a cap cannot borrow the absent opposite interval"))


def test_mutation_interval_crosses_chart_boundary_is_killed(monkeypatch):
    _exercise(monkeypatch, "cross_chart", [
        ("if not -1 <= low < high <= 1:", "if False and not -1 <= low < high <= 1:")],
        _reject_guard("cross_chart_interval", "an interval may not cross a Cayley chart boundary"))


def test_mutation_skipped_caps_is_killed(monkeypatch):
    _exercise(monkeypatch, "skip_caps", [
        ('def _check_v5(cert, charts, counts):\n    for family in (key for key in cert if key in ("links", "caps")):',
         'def _check_v5(cert, charts, counts):\n    for family in ("links",):')],
        _reject_guard("false_cap_witness", "a cap homotopy must be verified rather than merely named"))


def test_mutation_unchecked_initial_pose_is_killed(monkeypatch):
    _exercise(monkeypatch, "initial_overlap", [
        ('if not _weak_separated(a, b["ring"]):', 'if False and not _weak_separated(a, b["ring"]):')],
        _reject_guard("initial_overlap", "the certified initial pose must be free"))


def test_mutation_winding_parity_instead_of_integer_is_killed(monkeypatch):
    _exercise(monkeypatch, "parity_winding", [
        ('winding = _winding_value(loop, (F(0), F(0)))',
         'winding = (_winding_value(loop, (F(0), F(0))) or 0) % 2')],
        _accept_guard(repeat_winding(closed_disk_certificate()), "signed winding two remains nonzero"))


def test_mutation_partition_checks_only_area_is_killed(monkeypatch):
    _exercise(monkeypatch, "area_without_containment", [
        ('if not _contained(piece, parent):', 'if False and not _contained(piece, parent):')],
        _reject_guard("equal_area_outside_partition", "equal area does not imply containment in the source polygon"))


def test_mutation_negative_disk_host_halfplane_is_killed(monkeypatch):
    _exercise(monkeypatch, "squared_negative_host_bound", [
        ('if b < 0 or b*b < disk["radius"]**2*(nx*nx+ny*ny):',
         'if b*b < disk["radius"]**2*(nx*nx+ny*ny):')],
        _reject_guard("negative_host_halfplane", "squaring cannot turn a negative host bound into containment"))
