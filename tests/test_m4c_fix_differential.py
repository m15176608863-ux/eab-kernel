"""Fixed-seed exact differential; primary oracle shares no production geometry.

Oracle import list and root/segment independence are documented in
m4c_independent_oracle.py. Only this test driver imports motion_first_entrance;
the independent oracle never imports it or any motion helper. Random end maps
are orientation-preserving throughout the step, so the tested domain is valid
by construction (diagonal >= 7/8, off-diagonals <= 1/8). Concave base rings
therefore remain simple, without asking production to select accepted inputs.
"""
import ast
from fractions import Fraction as F
from pathlib import Path
from random import Random

import pytest

from eab.kernel2d.motion import motion_first_entrance
from m4c_independent_oracle import Root, _roots, entrance


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))
TRIANGLE = ((0, 0), (2, 0), (F(1, 3), 1))
CONCAVE = ((0, 0), (2, 0), (2, F(1, 2)),
           (F(1, 2), F(1, 2)), (F(1, 2), 2), (0, 2))


def _move(poly, x, y):
    return tuple((F(a)+x, F(b)+y) for a, b in poly)


def _deform(poly, rng):
    ax, ay, bx, by = (F(rng.randrange(-1, 2), 8) for _ in range(4))
    # Ensure every random case has true shape motion, rather than accepting a
    # chance all-zero matrix as a nontranslation test.
    if not any((ax, ay, bx, by)):
        ax = F(1, 8)
    dx, dy = (F(rng.randrange(-12, 13), 4) for _ in range(2))
    return tuple(((1+ax)*x+bx*y+dx, ay*x+(1+by)*y+dy) for x, y in poly)


def cases():
    rng = Random(20261014)
    result = []
    shapes = (SQUARE, TRIANGLE, CONCAVE)
    for i in range(108):
        a = _move(shapes[i % 3], F(rng.randrange(-8, 9), 4), F(rng.randrange(-8, 9), 4))
        b = _move(shapes[(i//3) % 3], F(rng.randrange(-8, 9), 4), F(rng.randrange(-8, 9), 4))
        result.append((f"random_{i:03}", (a, b, _deform(a, rng), _deform(b, rng))))
    # Fifteen exact structured probes are part of the same independent
    # differential, not expected answers imported from another motion test.
    for scale in (F(1, 7), F(1), F(13)):
        irrational_a = ((0, 0), (-F(1, 10), -1), (F(1, 10), -1))
        irrational_b = ((-1, F(1, 2)), (1, F(1, 2)), (1, 3))
        probes = (
            ("irrational", (irrational_a, irrational_b, _move(irrational_a, 1, 0),
                            ((-1, F(1, 2)), (1, -F(1, 2)), (1, 3)))),
            ("face_tie", (_move(SQUARE, -2, 0), SQUARE, SQUARE, SQUARE)),
            ("corner_tie", (SQUARE, _move(SQUARE, 2, 2), SQUARE, _move(SQUARE, 1, 1))),
            ("concave_slot", (_move(SQUARE, 3, 1), CONCAVE, _move(SQUARE, -1, 1), CONCAVE)),
            ("initial_touch_slide", (SQUARE, _move(SQUARE, 1, 0), SQUARE, _move(SQUARE, 1, 1))),
        )
        for name, data in probes:
            transformed = tuple(tuple((scale*x+7, scale*y-3) for x, y in p) for p in data)
            result.append((f"{name}_{scale}", transformed))
    return tuple(result)


CASES = cases()


@pytest.mark.parametrize("name,data", CASES, ids=[item[0] for item in CASES])
def test_fixed_seed_motion_matches_independent_event_superset_and_body_states(name, data):
    """123 inputs; full exact time/state/incidence/cover sets, not one witness."""
    expected = entrance(*data)
    got = motion_first_entrance(*data)
    certificate = None if got.exact_time is None else got.exact_time.certificate
    assert (got.initial_state, got.status) == expected[:2], f"{name}: initial/body status"
    assert certificate == expected[2], f"{name}: complete exact first-time certificate"
    assert got.incidences == expected[3], f"{name}: full incidence set"
    assert got.features == expected[4], f"{name}: full normal-support cover set"
    if name.startswith("irrational"):
        assert expected[2]["rational"] is None, "constructed irrational-root coverage"
    if "tie" in name:
        assert len(expected[4]) >= 3, "constructed multi-feature tie coverage"
    if name.startswith("initial_touch_slide"):
        assert expected[0] == 0 and {state for _, state in expected[5]} == {0}, \
            "initial touching and persistent-contact interval coverage"


def test_independent_oracle_import_boundary_and_exact_root_selfchecks():
    """Executable import inventory; oracle does not import the tested path."""
    path = Path(__file__).with_name("m4c_independent_oracle.py")
    parsed = ast.parse(path.read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(parsed) if isinstance(node, ast.ImportFrom)}
    assert imports == {"dataclasses", "fractions", "math", "eab.kernel2d.g0_oracle"}
    assert not any(isinstance(node, ast.Import) for node in ast.walk(parsed))
    assert len(CASES) == 123 and sum("random_" in name for name, _ in CASES) == 108
    assert set(_roots((F(1, 4), F(-1), F(1)))) == {Root(F(1, 2))}
    golden, = _roots((F(-1), F(1), F(1)))
    assert golden.certificate() == {"rational": None, "polynomial": ["-1", "1", "1"], "branch": 1}
    assert golden.relative(F(3, 5)) > 0 and golden.relative(F(2, 3)) < 0
