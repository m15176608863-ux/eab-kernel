"""Independent scoped review of M5d R3 tests/oracle, not a G6 exit review.

Adds exact closed-form oracle self-checks, replays real internal mutations,
and audits the error tubes in the threshold-edge pytest fixtures. Numerical
expected answers below do not import a production geometry primitive.
"""
import ast
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]
import m5d_r3_oracle as oracle
import test_m5d_r3_semantics as subject
from mutation_support import mutated_callable
from eab.kernel2d import m5c_certificates as cert

EVIDENCE = ROOT / "reports/codex/M5d_evidence"
FILES = ("tests/m5d_r3_oracle.py", "tests/test_m5d_r3_semantics.py", "docs/m5d_r3_theory.md",
         "tests/m5c_teeth_oracle.py", "src/eab/kernel2d/m5c_certificates.py", "tools/m5d_review_r3.py")


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}


def paths(ring, velocity=(0, 0)):
    return tuple(((F(x), F(velocity[0])), (F(y), F(velocity[1])), (F(1),)) for x, y in ring)


def scalar_value(coefficients, time):
    # Independent direct powers, rather than the oracle's Horner evaluator.
    return sum(coefficient*time**power for power, coefficient in enumerate(coefficients))


def positions(ring, time):
    return tuple(tuple(scalar_value(path[k], time)/scalar_value(path[2], time) for k in (0, 1))
                 for path in ring)


def distances(ring):
    return tuple((p[0]-q[0])**2+(p[1]-q[1])**2 for p, q in zip(ring, ring[1:]+ring[:1]))


def oracle_selfchecks():
    a = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
    b = ((1, -2), (3, -2), (3, 2), (1, 2))
    records = []
    for name, aa, bb, expected_time, labels in (
        ("linear_translation", paths(a, (2, 0)), paths(b), F(1, 2), (("VE", 2, 3),)),
        ("disjoint_line_extension", paths(tuple((x, y+5) for x, y in a), (2, 0)), paths(b), None, ()),
        ("four_incidence_corner", paths(tuple((x, y+2) for x, y in a), (2, 0)), paths(b), F(1, 2),
         (("EV", 1, 3), ("EV", 2, 3), ("VE", 2, 2), ("VE", 2, 3))),
        ("double_root_tangency", tuple(((F(x), F(4), F(-4)), (F(y),), (F(1),)) for x, y in a),
         paths(b), F(1, 2), (("VE", 2, 3),)),
    ):
        first, found = oracle.first_events(aa, bb)
        assert found == labels, (name, found)
        if expected_time is None:
            assert first is None
        else:
            assert first.sign((-expected_time, 1)) == 0
        records.append(dict(name=name, exact_time=expected_time, labels=found))
    triangle = ((-1, -3), (0, -2), (-1, -1))
    wall = ((1, -4), (3, -4), (3, 0), (1, 0))
    rotated = tuple(((F(x), -F(y), -F(x, 4)), (F(y), F(x), -F(y, 4)), (F(1), F(0), F(1, 4)))
                    for x, y in triangle)
    # Add common translation (s,2s)/(1+s²) to both rings. The resulting
    # unequal positive denominators preserve exactly the same incidence root.
    moved_rotated = tuple(((F(x), 1-F(y), F(3*x, 4), F(1, 4)-y, F(-x, 4)),
                          (F(y), F(x)+2, F(3*y, 4), F(x)+F(1, 2), F(-y, 4)),
                          (F(1), F(0), F(5, 4), F(0), F(1, 4))) for x, y in triangle)
    moved_wall = tuple(((F(x), F(1), F(x)), (F(y), F(2), F(y)), (F(1), F(0), F(1))) for x, y in wall)
    for name, aa, bb in (("half_angle_rotation", rotated, paths(wall)),
                         ("unequal_denominator_both_moving", moved_rotated, moved_wall)):
        first, found = oracle.first_events(aa, bb)
        # The rightmost tip has x=2s/(1+s²/4). x=1 gives s²-8s+4=0;
        # its unique [0,1] root is 4-2sqrt(3), with all other vertices left.
        assert found == (("VE", 1, 3),)
        assert first.sign((4, -8, 1)) == 0
        assert first.sign((-F(1, 2), 1)) > 0 and first.sign((-F(3, 5), 1)) < 0
        records.append(dict(name=name, defining_polynomial=[4, -8, 1], isolating_interval=["1/2", "3/5"], labels=found))
    return records


def mutation_checks():
    records = []
    for identifier, name, before, after, gate, args, expected in subject.MUTATIONS:
        original = getattr(cert, name)
        setattr(cert, name, mutated_callable(cert, name, [(before, after)]))
        try:
            gate(*args)
        except AssertionError as error:
            assert expected in str(error)
            if identifier == "reuse_wrong_endpoint_budget":
                category = "exact_budget_helper_contract"
            elif identifier in ("omit_w_endpoint_error", "omit_mixed_error"):
                category = "conservative_budget_public_contract"
            else:
                category = "actual_false_certificate_public_path"
            records.append(dict(id=identifier, category=category, function=name, gate=gate.__name__, actual_red=str(error)))
        else:
            raise AssertionError("surviving internal mutation: "+identifier)
        finally:
            setattr(cert, name, original)
    for which in ("w", "v"):
        terms = [f"du*_length1({which}, lo, hi)", "dw*_length1(u, lo, hi)", "2*du*dw"]
        for term in range(3):
            before = f"e{which} = "+"+".join(terms)
            after = f"e{which} = "+"+".join(value for k, value in enumerate(terms) if k != term)
            original = cert._event
            cert._event = mutated_callable(cert, "_event", [(before, after)])
            try:
                subject.test_r3_bilinear_budgets_include_both_endpoints_and_all_terms()
            except AssertionError as error:
                assert f"R3 {which.upper()} endpoint budget" in str(error)
                records.append(dict(id=f"budget_{which}_{term}", category="exact_budget_helper_contract",
                                    function="_event", actual_red=str(error)))
            else:
                raise AssertionError("surviving exact budget mutation")
            finally:
                cert._event = original
    return records


def threshold_checks():
    lower, upper = subject.threshold_bracket()
    assert upper-lower == F(1, 2**43)
    assert upper-lower <= lower*F(1, 2**24)/64
    a, b, label, bracket = subject.p2_case()
    rows = []
    for factor in (F(1, 2), 1-F(1, 2**24)):
        radius = lower*factor
        for index, (aa, bb) in enumerate(subject.perturbations(a, b, radius)):
            for nominal, moved in ((a, aa), (b, bb)):
                original_ends = [positions(nominal, time) for time in (F(0), F(1))]
                changed_ends = [positions(moved, time) for time in (F(0), F(1))]
                errors = [tuple(tuple(v[k]-u[k] for k in (0, 1)) for u, v in zip(original, changed))
                          for original, changed in zip(original_ends, changed_ends)]
                assert all(abs(value) <= radius for end in errors for point in end for value in point)
                assert errors[0] != errors[1], "each ring's actual errors vary with time"
                assert any(distances(original) != distances(changed) for original, changed in zip(original_ends, changed_ends)), \
                    "each ring really changes shape, not just a rigid displacement"
            first, labels = oracle.first_events(aa, bb)
            assert labels == (label,)
            assert first.sign((-bracket[0], 1)) > 0 and first.sign((-bracket[1], 1)) < 0
            rows.append(dict(factor=factor, radius=radius, index=index, labels=labels,
                             time_in_open_bracket=True, both_ring_shape_changes=True, both_ring_errors_time_varying=True))
    a, b, label, _ = subject.p2_case(-100)
    first, labels = oracle.first_events(a, b)
    assert a[0][2] != b[0][2] and len(a[0][2]) == len(b[0][2]) == 3
    assert labels == (label,) and first.sign((-F(2, 5), 1)) > 0
    return dict(threshold_lower=lower, threshold_upper=upper, width=upper-lower,
                edge_offset_to_uncertainty=lower*F(1, 2**24)/(upper-lower),
                false_unequal_p2_bracket=["3/10", "2/5"], actual_first_time_after="2/5", perturbations=rows)


def main():
    os.environ["TEMP"] = os.environ["TMP"] = str(EVIDENCE / "tmp")
    before = hashes()
    tree = ast.parse((ROOT / "tests/m5d_r3_oracle.py").read_text(encoding="utf-8"))
    imports = sorted({node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)})
    assert imports == ["fractions", "functools", "math"]
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    selfchecks, mutations, thresholds = oracle_selfchecks(), mutation_checks(), threshold_checks()
    after = hashes()
    assert before == after, "reviewed source changed; discard review and rerun"
    result = dict(complete=True, scope="R3 oracle/tests/proof, not six-way G6", critical=0, major=0, minor=0,
                  reviewed_hashes=before,
                  oracle_imports=imports, independent_closed_form_selfchecks=selfchecks,
                  actual_internal_mutations=mutations, threshold_audit=thresholds,
                  mutant_assertions_use_source_hash_or_snapshots=False, reviewed_source_bytes_checked_start_and_end=True,
                  resolved_findings=["Theory document's question-mark corruption rewritten and UTF-8 verified",
                                     "Equal W/V L1 lengths replaced by unequal lengths; real ev=ew mutation now caught"],
                  limits=["Oracle denominator-factor optimization is reviewed for positive P2 quadratic denominators and their products",
                          "Conservative budget contract kills are not claimed as actual false first-label witnesses"])
    (EVIDENCE / "review_r3.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str)+"\n",
                                             encoding="utf-8", newline="\n")
    print("M5D_R3_INDEPENDENT_REVIEW_COMPLETE", len(selfchecks), "closed forms", len(mutations), "mutants", len(thresholds["perturbations"]), "threshold perturbations")


if __name__ == "__main__":
    main()
