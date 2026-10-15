"""Independent R5 checks: known factorizations and lever closed forms only."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from random import Random
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from eab.kernel2d.algebraic import RealAlgebraic
from eab.kernel2d.motion import QuadraticTime
from eab.kernel2d.se2 import SE2Motion, se2_first_entrance
from m5a_se2_replay import fit_rigid


def multiply(a, b):
    # Review-local coefficient convolution. No production polynomial helper.
    return tuple(sum(a[i]*b[k-i] for i in range(len(a)) if 0 <= k-i < len(b))
                 for k in range(len(a)+len(b)-1))


def run():
    started = time.perf_counter()
    random = Random(5101505)
    counts = {"known_rational_factor_roots": 0, "known_irrational_roots": 0,
              "rational_lever_public_container": 0, "exact_tiny_residuals": 0,
              "closed_endpoint_roots": 0}
    examples = []
    roots = [F(random.randrange(-5000, 5001), random.randrange(2, 1001)) for _ in range(90)]
    roots += [F(1, 2**180+17), F(-1, 10**100+267), F(1, 2**1074), F(0), F(10**80+1, 7)]
    for index, root in enumerate(roots):
        degree = (1, 3, 5)[index % 3]
        p = (-root, F(1))
        for i in range((degree-1)//2):
            p = multiply(p, (F(i+1), F(0), F(1)))
        for multiplier in (F(1), F(-7, 19)):
            value = RealAlgebraic(tuple(multiplier*x for x in p), root-F(2, 7), root+F(3, 11))
            assert value.as_rational() == root, ("known rational factor lost", index, str(root))
            counts["known_rational_factor_roots"] += 1
        endpoint = RealAlgebraic(p, root, root+F(3, 11))
        assert endpoint.rational == endpoint.as_rational() == root and endpoint.lower == endpoint.upper
        counts["closed_endpoint_roots"] += 1
    for degree in range(2, 6):
        for prime in (2, 3, 5, 7, 11):
            p = (-F(prime),)+(F(0),)*(degree-1)+(F(1),)
            # A prime has no rational kth root for k>=2 (prime exponent 1).
            assert RealAlgebraic(p, 1, prime).as_rational() is None
            counts["known_irrational_roots"] += 1
    for rational_root in (F(-50), F(-1, 10**70), F(0), F(1), F(7, 5), F(3, 2), F(4)):
        p = multiply((-rational_root, F(1)), (-F(2), F(0), F(1)))
        # This tiny bracket contains sqrt(2), and none of the rational roots.
        value = RealAlgebraic(p, F(1414213, 1000000), F(1414214, 1000000))
        assert value.as_rational() is None, ("wrong rational branch selected", str(rational_root))
        counts["known_irrational_roots"] += 1
    for index in range(36):
        t = F(random.randrange(1, 9), 10)
        u = F(random.randrange(1, 9), 10)
        scale = (F(1, 2**400), F(1), F(2**397))[index % 3]
        L = 5*scale
        z = u*t
        h = 2*L*z/(1+z*z)
        offset = (F(10**6), -F(10**5)) if index % 2 else (F(0), F(0))
        def point(x, y):
            return x+offset[0], y+offset[1]
        A = tuple(point(x, y) for x, y in ((0, 0), (L, 0), (0, h/10)))
        B = tuple(point(x, y) for x, y in ((-L, h), (2*L, h), (2*L, h+2*L), (-L, h+2*L)))
        result = se2_first_entrance(A, B, SE2Motion(u, center=offset))
        public = result.exact_time
        assert result.status == "contact" and result.features == (("VE", 1, 0),)
        assert isinstance(public, QuadraticTime) and public.rational == t
        expected = QuadraticTime(t)
        assert public == expected and expected == public and hash(public) == hash(t)
        assert len({public, expected, t}) == 1
        assert sorted((public, F(0), expected, 1)) == [0, t, t, 1]
        counts["rational_lever_public_container"] += 1
    square = ((0, 0), (1, 0), (1, 1), (0, 1))
    for delta in (F(1, 2**52), F(1, 2**1074), F(1, 2**1075), F(1, 10**100), F(1, 10**400)):
        end = tuple(((1+2*delta)*x, F(y)) for x, y in square)
        result = fit_rigid(square, end)
        assert result.delta == delta and result.certificate == "UNCERTIFIED_NONRIGID_ENDPOINTS"
        counts["exact_tiny_residuals"] += 1
    payload = {"complete": True, "counts": counts, "mismatches": 0, "seconds": time.perf_counter()-started,
               "oracle_imports": ["fractions.Fraction", "random.Random (input generation only)"],
               "oracle_logic": ["explicit known polynomial factors", "prime-exponent irrationality", "2Lu*t/(1+(u*t)^2) lever height", "centered x scaling exact residual"],
               "source_hashes": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                                  ("src/eab/kernel2d/algebraic.py", "src/eab/kernel2d/se2.py", "tools/m5a_se2_replay.py", "tests/test_m5a2_exact.py")}}
    output = Path(__file__).with_name("review_exact_checks.json")
    output.write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(payload))


if __name__ == "__main__":
    run()
