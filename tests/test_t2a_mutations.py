"""Named defect injections execute mutated kernel source, not fake outputs.

Each guard first passes on the real module, then reports its designated
semantic assertion against a separately compiled internal source mutation.
No file hashes, changed expected values or incidental exception count as a
successful mutation kill. The production file is never edited by these tests.
"""
from fractions import Fraction as F
from pathlib import Path
import sys
from types import ModuleType

import pytest

from eab.kernel2d import se2_paths as production
from eab.kernel2d.se2 import SE2Motion, _line_polynomials, _validated_ring


SQUARE = ((0, 0), (1, 0), (1, 1), (0, 1))


def _guard_left_boundary(module):
    obstacle = tuple((x+2, y) for x, y in SQUARE)
    got = module.se2_first_penetration(SQUARE, obstacle, SE2Motion(0, (4, 0)))
    assert got.status == "PENETRATES" and got.exact_time == F(1, 4), \
        "semantic: first penetration is the interval boundary, not its probe"


def _guard_segment_condition(module):
    a = _validated_ring(tuple((F(x)-1, F(y)+3) for x, y in SQUARE), SE2Motion(0, (3, 0)))
    b = _validated_ring(tuple((F(x), F(y)) for x, y in SQUARE), SE2Motion())
    events = tuple((p, q, tag, i, j, _line_polynomials(p, i, q, j))
                   for p, q, tag in ((a, b, "VE"), (b, a, "EV"))
                   for i in range(len(p.start)) for j in range(len(q.start)))
    assert module._event_partition(events) == (0, 1), \
        "semantic: closed-segment condition excludes supporting-line-only cuts"


def _guard_final_endpoint(module):
    obstacle = tuple((x+2, y) for x, y in SQUARE)
    got = module.se2_first_penetration(SQUARE, obstacle, SE2Motion(0, (1, 0)))
    assert got.status == "FREE" and got.touches_end and got.end_state == 0, \
        "semantic: final contact must be reported even without penetration"


def _guard_contact_allowed(module):
    obstacle = tuple((x+1, y) for x, y in SQUARE)
    got = module.se2_first_penetration(SQUARE, obstacle, SE2Motion())
    assert got.status == "FREE" and got.exact_time is None, \
        "semantic: persistent contact is not penetration"


def _guard_strict_overlap(module):
    obstacle = tuple((x+2, y) for x, y in SQUARE)
    got = module.se2_first_penetration(SQUARE, obstacle, SE2Motion(0, (4, 0)))
    assert got.status == "PENETRATES", \
        "semantic: interior penetration cannot be relabeled as allowed contact"


MUTATIONS = (
    ("tau_is_probe", (
        ('"PENETRATES", _public_time(left),',
         '"PENETRATES", _public_time(RealAlgebraic.from_rational(probe)),'),),
     _guard_left_boundary, "interval boundary"),
    ("missing_segment_condition", (
        ("from .algebraic import RealAlgebraic\n", "from .algebraic import RealAlgebraic, roots_interval\n"),
        ("candidates.extend(_event_times(*polynomials))",
         "candidates.extend(roots_interval(polynomials[0]) if any(polynomials[0]) else _event_times(*polynomials))")),
     _guard_segment_condition, "closed-segment condition"),
    ("missing_s1", (
        ("end_state = polygons_overlap_exact(final_a, final_b)", "end_state = -1"),),
     _guard_final_endpoint, "final contact"),
    ("contact_is_penetration", (
        ("if polygons_overlap_exact(at_a, at_b) == 1:",
         "if polygons_overlap_exact(at_a, at_b) >= 0:"),),
     _guard_contact_allowed, "persistent contact"),
    ("penetration_is_contact", (
        ("if polygons_overlap_exact(at_a, at_b) == 1:",
         "if False and polygons_overlap_exact(at_a, at_b) == 1:"),),
     _guard_strict_overlap, "interior penetration"),
)


@pytest.mark.parametrize("name,replacements,guard,assertion", MUTATIONS,
                         ids=[row[0] for row in MUTATIONS])
def test_named_internal_mutation_is_killed(monkeypatch, name, replacements, guard, assertion):
    guard(production)
    source = Path(production.__file__).read_text(encoding="utf-8")
    for original, replacement in replacements:
        assert source.count(original) == 1, "mutation target must be unique and present"
        source = source.replace(original, replacement, 1)
    module_name = "eab.kernel2d._t2a_mutation_"+name
    mutant = ModuleType(module_name)
    monkeypatch.setitem(sys.modules, module_name, mutant)
    exec(compile(source, "<"+module_name+">", "exec"), mutant.__dict__)
    with pytest.raises(AssertionError, match=assertion):
        guard(mutant)
