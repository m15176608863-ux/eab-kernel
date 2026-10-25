"""Exact independent differential checks, including 1024 distinct segments.

The oracle uses independent six-sample event interpolation, private Sturm
roots and G0 integer-lifted winding/crossing tests. This wrapper alone imports production
SE(2); the oracle helper has no access to production root primitives.
"""
import ast
from fractions import Fraction as F
from pathlib import Path
from random import Random

import pytest

from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import se2_first_penetration
from t2a_independent_oracle import first_penetration, time_matches
from t2a_oracle_audit import validate_escape_segments
from t2a_truth_geometry import doorway, doorway_motion_specs, rectangle


def random_cases(count=1024):
    rng = Random(2026102502)
    cases = []
    for index in range(count):
        # An asymmetric rational triangle avoids a symmetric grid-only
        # population. Every eighth input starts in exact edge contact.
        sx, sy = F(rng.randrange(2, 9), 5), F(rng.randrange(2, 9), 7)
        a = ((F(0), F(0)), (sx, F(0)), (sx/F(3), sy))
        if index % 8 == 0:
            b = rectangle(sx, F(-1, 3), sx+1, sy+F(1, 3))
        else:
            bx, by = F(rng.randrange(-8, 13), 5), F(rng.randrange(-7, 11), 7)
            b = ((bx, by), (bx+F(6, 5), by+F(1, 7)), (bx+F(2, 5), by+F(9, 7)))
        ua = F(rng.randrange(-7, 8), 7)
        ub = F(0) if index % 3 else F(rng.randrange(-5, 6), 5)
        # Index-dependent rational x-translation makes every full segment
        # distinct without using a floating generator or snapping inputs.
        da = (F(rng.randrange(-15, 16), 7)+F(index, 2**20),
              F(rng.randrange(-13, 14), 11))
        db = (F(rng.randrange(-3, 4), 13), F(rng.randrange(-3, 4), 17))
        ca = (sx/F(4), sy/F(3))
        cb = (F(rng.randrange(-2, 5), 3), F(rng.randrange(-2, 5), 5))
        cases.append((a, b, (ua, da, ca), (ub, db, cb)))
    return cases


def assert_match(case):
    a, b, ma, mb = case
    expected = first_penetration(a, b, ma, mb)
    actual = se2_first_penetration(a, b, SE2Motion(*ma), SE2Motion(*mb))
    assert actual.initial_state == expected["initial_state"], "independent exact initial state"
    assert actual.status == expected["status"], "independent full-interval overlap status"
    assert actual.immediate == expected["immediate"], "independent zero infimum"
    assert actual.touches_end == expected["touches_end"], "independent closed endpoint contact"
    assert actual.end_state == expected["end_state"]
    assert set(actual.incidences) == expected["incidences"], "independent complete incidences at tau_P"
    assert set(actual.features) == expected["features"], "independent normal-cone labels at tau_P"
    if expected["root"] is None:
        assert actual.exact_time is None
    else:
        assert time_matches(actual.exact_time.certificate, expected["root"]), "independent exact interval-left time"
    return expected


def test_small_random_rational_independent_population():
    cases = tuple(random_cases(12))
    outcomes = [assert_match(case) for case in cases]
    assert len(set(cases)) == 12
    assert any(item["initial_state"] == 0 for item in outcomes)
    assert any(item["status"] == "PENETRATES" for item in outcomes)


@pytest.mark.slow
@pytest.mark.parametrize("batch", range(16))
def test_1024_random_rational_segments_independent_partition(batch):
    cases = tuple(random_cases())
    assert len(cases) == len(set(cases)) == 1024, "random population is not duplicated by parameterization"
    selected = cases[64*batch:64*(batch+1)]
    outcomes = [assert_match(case) for case in selected]
    assert len(outcomes) == 64
    assert sum(item["initial_state"] == 0 for item in outcomes) >= 8


def test_independent_helper_imports_never_reach_production_root_code():
    """Structural gate complements, but cannot replace, semantic controls."""
    base = Path(__file__).parent
    for name in ("t2a_independent_oracle.py", "t2a_oracle_audit.py", "m5a_independent_oracle.py"):
        tree = ast.parse((base/name).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert all(module in {"fractions", "functools", "m5a_independent_oracle",
                              "eab.kernel2d.g0_oracle", "t2a_independent_oracle"} for module in imports)


def test_independent_escape_audit_records_every_pair_and_limits_its_claim():
    moving, obstacles = doorway(F(1, 8))
    audit = validate_escape_segments(moving, obstacles, doorway_motion_specs(), ((0, 0), (0, 100)))
    assert audit["valid"] and audit["overlapping_probe_count"] == 0
    assert audit["se2_pair_checks"] == 15 and audit["ray_prefix_pair_checks"] == 5
    assert audit["first_contact_calls"] == len(audit["pairs"]) == 20
    assert audit["infinite_ray_verified"] is False, "finite oracle must not claim an infinite-ray proof"
    assert sum(row["first_contact_status"] == "contact" for row in audit["pairs"]) == 4
    with pytest.raises(ValueError, match="exact zero"):
        validate_escape_segments(moving, obstacles, (), ((F(1, 10**20), 0), (0, 100)))
    with pytest.raises(ValueError, match="quarter-turn"):
        validate_escape_segments(moving, obstacles, ((F(1001, 1000), (0, 0), (0, 0)),))

