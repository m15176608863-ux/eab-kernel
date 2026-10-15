"""Independent R3 adversarial sweep (not a replacement for a continuous proof).

Oracle: tests/m5c_teeth_oracle.py, fractions-only linear incidence enumeration.
This script does not share production geometry primitives for expected labels.
"""
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
from eab.kernel2d import m5c_certificates as cert
from m5c_teeth_oracle import translation_first_events
from m4c_independent_oracle import entrance as independent_affine_entrance


def paths(ring, velocity):
    return tuple(((F(x), F(velocity[0])), (F(y), F(velocity[1])), (F(1),)) for x, y in ring)


def independently_simple(ring):
    """Exact closed-segment intersection enumeration, no production helpers."""
    def orient(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def on_segment(a, b, p):
        return orient(a, b, p) == 0 and all(min(a[k], b[k]) <= p[k] <= max(a[k], b[k]) for k in (0, 1))
    edges = tuple(zip(ring, ring[1:]+ring[:1]))
    for i, (a, b) in enumerate(edges):
        if a == b:
            return False
        previous = ring[i-1]
        if orient(a, previous, b) == 0 and sum((previous[k]-a[k])*(b[k]-a[k]) for k in (0, 1)) >= 0:
            return False
        for j, (c, d) in enumerate(edges[i+1:], i+1):
            if j == i+1 or (i == 0 and j == len(edges)-1):
                continue
            signs = (orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b))
            if signs[0]*signs[1] < 0 and signs[2]*signs[3] < 0:
                return False
            if on_segment(a, b, c) or on_segment(a, b, d) or on_segment(c, d, a) or on_segment(c, d, b):
                return False
    return True


def main():
    evidence = ROOT / "reports/codex/M5c_evidence"
    os.environ["TEMP"] = os.environ["TMP"] = str(evidence / "tmp")
    rng = random.Random(20261016041)
    affine_rng = random.Random(20261016042)
    wall = ((F(1), F(-2)), (F(3), F(-2)), (F(3), F(2)), (F(1), F(2)))
    diamond = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
    concave = ((-2, -1), (-1, -1), (-1, F(-1, 2)), (0, 0),
               (-1, F(1, 2)), (-1, 1), (-2, 1), (F(-3, 2), 0))
    started = time.perf_counter()
    signed = rejected = probes = affine_probes = 0
    examples = []
    # Concavity, near-corner grazing, oblique translation, close competitors and
    # error radii straddling nominal gaps. The seed and rational grid are fixed.
    for index in range(90):
        base = concave if index % 3 == 0 else diamond
        height = F(rng.choice((1, 2, 5, 10)), 10)
        front_gap = F(rng.choice((1, 10, 1000)), 1000)
        yshift = F(rng.choice((-2001, -1999, -1500, 0, 1500, 1999, 2001)), 1000)
        a = tuple((F(x)*front_gap, F(y)*height+yshift) for x, y in base)
        velocity = (F(2), F(rng.choice((-1, 0, 1)), 100))
        t, labels = translation_first_events(a, wall, velocity)
        if t is None or len(labels) != 1 or not 0 < t < 1:
            rejected += 1
            continue
        radius = F(1, 10**rng.choice((3, 5, 7)))
        pad = F(rng.choice((1, 5, 10)), 1000)
        bracket = max(F(0), t-pad), min(F(1), t+pad)
        result = cert.single_cover_certificate(paths(a, velocity), paths(wall, (0, 0)),
                                                labels[0], bracket, radius, radius, panels=2)
        if result is None:
            rejected += 1
            continue
        signed += 1
        for probe in range(40):
            perturbed = [tuple((F(x)+rng.choice((-radius, F(0), radius)),
                                F(y)+rng.choice((-radius, F(0), radius))) for x, y in ring)
                         for ring in (a, wall)]
            expected_t, expected_labels = translation_first_events(*perturbed, velocity)
            assert expected_labels == (result["label"],), (index, probe, expected_labels, result["label"])
            assert expected_t is not None and bracket[0] < expected_t < bracket[1], (index, probe, expected_t)
            probes += 1
        for probe in range(6):
            # Independent offsets at both endpoints are linearly interpolated;
            # the coordinate error remains in the same L-infinity tube, while
            # each vertex has its own velocity (not a rigid perturbation).
            a0 = tuple((x+affine_rng.choice((-radius, F(0), radius)),
                        y+affine_rng.choice((-radius, F(0), radius))) for x, y in a)
            b0 = tuple((x+affine_rng.choice((-radius, F(0), radius)),
                        y+affine_rng.choice((-radius, F(0), radius))) for x, y in wall)
            a1 = tuple((x+velocity[0]+affine_rng.choice((-radius, F(0), radius)),
                        y+velocity[1]+affine_rng.choice((-radius, F(0), radius))) for x, y in a)
            b1 = tuple((x+affine_rng.choice((-radius, F(0), radius)),
                        y+affine_rng.choice((-radius, F(0), radius))) for x, y in wall)
            expected = independent_affine_entrance(a0, b0, a1, b1)
            assert expected[1] == "contact" and expected[4] == (result["label"],), (index, probe, expected[1:5])
            affine_probes += 1
        examples.append(dict(index=index, label=result["label"], nominal_time=str(t), radius=str(radius)))
        if index % 10 == 0:
            (evidence / "tmp/review_r3_progress.json").write_text(json.dumps(dict(complete=False, index=index,
                signed=signed, rejected=rejected, perturbation_probes=probes)), encoding="utf-8")
    # Structural A1 counterexamples exercise the new production path directly.
    a = ((-2, -10), (0, 0), (-2, 10))
    b = ((1, 1), (3, -1), (3, 3))
    assert cert.single_cover_certificate(paths(a, (4, 0)), paths(b, (0, 0)),
                                         ("VE", 1, 0), (F(1, 4), F(11, 20))) is None
    projection_cases = []
    for side in (-1, 1):
        a = tuple((x, y+5*side) for x, y in diamond)
        assert translation_first_events(a, wall, (2, 0)) == (None, ())
        assert cert.single_cover_certificate(paths(a, (2, 0)), paths(wall, (0, 0)),
                                             ("VE", 2, 3), (F(2, 5), F(3, 5))) is None
        projection_cases.append(side)
    a = ((F(-198, 1000), F(1403, 1000)), (F(-1198, 1000), F(2403, 1000)),
         (F(-2198, 1000), F(1903, 1000)))
    assert cert.single_cover_certificate(paths(a, (2, 1)), paths(wall, (0, 0)),
                                         ("VE", 0, 3), (F(29, 50), F(3, 5))) is None
    early = tuple(((F(x)/10-47, F(296), F(-600), F(400)),
                   (F(y)-11, F(20)), (F(1),)) for x, y in diamond)
    assert cert.single_cover_certificate(early, paths(wall, (0, 0)),
                                         ("VE", 2, 3), (F(59, 100), F(61, 100))) is None
    diagonal_a, diagonal_b = ((0, 0), (2, 0), (0, 2)), ((2, 2), (4, 2), (2, 4))
    assert cert.relative_separation_certificate(paths(diagonal_a, (0, 0)), paths(diagonal_b, (0, 0)),
                                                 F(3, 5), F(3, 5)) is None
    simple_signed = simple_probes = 0
    shape_rng = random.Random(20261016043)
    # Collinear continuation is legal; adjacent reversal/overlap is not. Added
    # points and permutations target nonlocal crossings hidden by local turns.
    shapes = [concave, diamond, ((0, 0), (1, 0), (2, 0), (2, 2), (0, 2)),
              ((0, 0), (2, 0), (1, 0), (2, 2), (0, 2)),
              ((0, 0), (2, 2), (0, 2), (2, 0))]
    for index in range(80):
        ring = tuple((F(x), F(y)) for x, y in shapes[index % len(shapes)])
        if index % 4 == 0:
            ring = tuple(shape_rng.sample(ring, len(ring)))
        radius = F(shape_rng.choice((0, 1, 10, 100)), 1000)
        margin = cert._simple(paths(ring, (0, 0)), radius, F(0), F(1))
        if margin <= 0:
            continue
        simple_signed += 1
        assert independently_simple(ring)
        for probe in range(20):
            perturbed = tuple((x+shape_rng.choice((-radius, F(0), radius)),
                               y+shape_rng.choice((-radius, F(0), radius))) for x, y in ring)
            assert independently_simple(perturbed), (index, probe, ring, perturbed)
            simple_probes += 1
    result = dict(complete=True, seed=20261016041, nominal_cases=90, signed=signed,
                  rejected_or_inapplicable=rejected, perturbation_probes=probes, false_certificates=0,
                  independent_vertex_affine_probes=affine_probes,
                  simple_ring_candidates=80, simple_ring_signed=simple_signed,
                  independent_simple_ring_probes=simple_probes,
                  structural_counterexamples=6, seconds=time.perf_counter()-started, examples=examples,
                  oracle_imports=["fractions.Fraction", "m4c_independent_oracle (dataclasses, fractions, math.isqrt/lcm, g0_oracle.overlap)",
                                  "g0_oracle imports fractions, math.lcm, oracle_construction; none is a shared R3 geometry primitive"],
                  limits=["finite adversarial sweep, not a proof", "constant and independently affine per-vertex perturbations, not arbitrary continuous paths"],
                  source_hashes={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
                                 ("src/eab/kernel2d/m5c_certificates.py", "tests/m5c_teeth_oracle.py",
                                  "tests/m4c_independent_oracle.py", "tools/m5c_independent_review.py")})
    (evidence / "review_r3.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in ("examples", "source_hashes")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
