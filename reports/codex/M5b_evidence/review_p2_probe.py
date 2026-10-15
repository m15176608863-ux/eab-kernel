"""Independent reviewer probes, exact expectations; run from repository root."""
from fractions import Fraction as F
import json
from pathlib import Path
from random import Random
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from eab.kernel2d.algebraic import RealAlgebraic, roots_interval
from eab.kernel2d.dda_motion import DDAAnchoredMotion, dda_first_entrance
from m5b_independent_oracle import first_contact, compare, certificate_root


def product(a, b):
    answer = [F(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            answer[i+j] += x*y
    return tuple(answer)


def main():
    start = time.monotonic()
    known = tuple(F(k, 7) for k in (-9, -3, -1, 0, 4, 11))
    polynomial = (F(1),)
    for root in known:
        polynomial = product(polynomial, (-root, 1))
    assert roots_interval(polynomial, -2, 2) == known
    assert roots_interval(polynomial, known[0], known[-1]) == known
    negative, positive = roots_interval((-2, 0, 0, 0, 0, 0, 1), -2, 2)
    assert -2 < negative < -1 < 0 < 1 < positive < 2
    assert negative.sign_polynomial(-2, 0, 0, 0, 0, 0, 1) == 0
    assert positive.sign_polynomial(-2, 0, 0, 0, 0, 0, 1) == 0
    rejected = 0
    for operation in (lambda: roots_interval((0, 0, 0, 0, 0, 0, 0, 1), -1, 1),
                      lambda: RealAlgebraic((0, 0, 0, 0, 0, 0, 0, 1), -1, 1),
                      lambda: RealAlgebraic(polynomial, -2, 2)):
        try:
            operation()
        except ValueError:
            rejected += 1
    assert rejected == 3

    rng, rows = Random(170620261016), []
    a = ((-3, 0), (-2, 0), (-F(11, 4), 1))
    b = ((0, 0), (2, 0), (2, 2), (0, 2))
    for index in range(6):
        specs = []
        for body in (0, 1):
            shear = F(rng.randrange(-3, 4), 150)
            strain = ((F(rng.randrange(-3, 4), 100), shear),
                      (shear, F(rng.randrange(-3, 4), 100)))
            specs.append((F(rng.choice((-3, -2, -1, 1, 2, 3)), 11),
                          (F(4 if body == 0 else 0), F(rng.randrange(-2, 3), 15)),
                          (-F(5, 2), F(1, 3)) if body == 0 else (F(1), F(1)), strain))
        ma, mb = specs
        expected = first_contact(a, b, ma, mb)
        result = dda_first_entrance(a, b, DDAAnchoredMotion(*ma), DDAAnchoredMotion(*mb))
        assert result.status == expected["status"] == "contact"
        assert set(result.features) == expected["features"]
        assert set(result.incidences) == expected["incidences"]
        assert compare(certificate_root(result.exact_time.certificate), expected["root"]) == 0

        def reversed_label(label):
            tag, i, j = label
            if tag == "VE":
                return tag, len(a)-1-i, (len(b)-2-j) % len(b)
            if tag == "EV":
                return tag, (len(a)-2-i) % len(a), len(b)-1-j
            return tag, len(a)-1-i, len(b)-1-j

        reversed_result = dda_first_entrance(tuple(reversed(a)), tuple(reversed(b)),
                                             DDAAnchoredMotion(*ma), DDAAnchoredMotion(*mb))
        assert reversed_result.exact_time == result.exact_time
        assert set(reversed_result.features) == {reversed_label(x) for x in result.features}
        assert set(reversed_result.incidences) == {reversed_label(x) for x in result.incidences}
        rows.append(dict(case=index, status=result.status, degree=expected["max_degree"],
                         features=result.features, independent_intervals=len(expected["probes"]),
                         reversed_original_id_mapping="PASS"))
    answer = dict(schema=1, status="PASS", independent_p2_cases=rows,
                  six_signed_rational_roots="PASS", two_signed_irrational_roots="PASS",
                  rejected_invalid_contracts=rejected, mismatches=0, seconds=time.monotonic()-start,
                  source_of_expectations="Fraction products and explicit sign brackets; test-only independent Lagrange/Sturm/G0 oracle; original-ID mapping formulas")
    (Path(__file__).with_suffix(".json")).write_text(json.dumps(answer, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(answer, ensure_ascii=False))


if __name__ == "__main__":
    main()
