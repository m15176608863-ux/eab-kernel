"""DDA endpoint gates, independent fan-integration and Taylor oracles.

Primary oracle imports: fractions.Fraction, math.factorial only. They share
no production area, affine, interval, fit, polynomial or geometry primitive.
math.nextafter/ulp are used only in the explicitly binary64 I/O contract.
Frozen all-frame evidence is an audit, not the independent analytic oracle.
"""
from fractions import Fraction as F
from decimal import Decimal, localcontext
import inspect
import json
from math import factorial
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import m5b_endpoint_replay as endpoint
import m5b_grouped_probe as grouped


POLYGON = ((F(2), F(-1)), (F(7), F(-1)), (F(6), F(2)), (F(4), F(5)), (F(1), F(2)))


def fan_centroid(poly):
    """Integrate triangle barycenters relative to the first vertex."""
    origin = poly[0]
    mass = F(0)
    moment = [F(0), F(0)]
    for a, b in zip(poly[1:-1], poly[2:]):
        u, v = tuple(a[k]-origin[k] for k in (0, 1)), tuple(b[k]-origin[k] for k in (0, 1))
        area = (u[0]*v[1]-u[1]*v[0])/2
        mass += area
        for k in (0, 1):
            moment[k] += area*(origin[k]+a[k]+b[k])/3
    return tuple(value/mass for value in moment)


def test_area_centroid_independent_driver(function=endpoint.area_centroid):
    assert function(POLYGON) == fan_centroid(POLYGON), "area centroid must equal independent triangle integrals"


def test_endpoint_independent_driver(function=endpoint.endpoint_map):
    c = fan_centroid(POLYGON)
    z = tuple(F(v) for v in (3, -2, 0, 2, -3, 4))
    cosine, sine = F(3, 5), F(4, 5)
    _, _, values = function(POLYGON, z, cosine, sine)
    for p, result in zip(POLYGON, values):
        # Independent displacement formulation mirrors the mathematical
        # source equation, rather than constructing an affine matrix.
        x, y = p[0]-c[0], p[1]-c[1]
        displacement = (z[0]+z[3]*x+z[5]*y/2+x*(cosine-1)-y*sine,
                        z[1]+z[4]*y+z[5]*x/2+y*(cosine-1)+x*sine)
        assert result == tuple(p[k]+displacement[k] for k in (0, 1)), "endpoint must match independent displacement oracle"


def test_area_centroid_matches_independent_triangle_integrals():
    test_area_centroid_independent_driver(endpoint.area_centroid)
    assert endpoint.area_centroid(POLYGON[::-1]) == fan_centroid(POLYGON)
    assert endpoint.area_centroid(POLYGON) != tuple(sum(p[k] for p in POLYGON)/len(POLYGON) for k in (0, 1))
    with pytest.raises(ValueError, match="zero signed"):
        endpoint.area_centroid(((0, 0), (1, 1), (2, 2)))


def test_endpoint_map_matches_independent_displacement_oracle():
    test_endpoint_independent_driver(endpoint.endpoint_map)


def lagrange_interval(theta, parity, degree=40):
    """Maclaurin polynomial + |x|^(n+1)/(n+1)! Lagrange remainder."""
    value = sum((-1)**((k-parity)//2)*theta**k/F(factorial(k)) for k in range(parity, degree+1, 2))
    error = abs(theta)**(degree+1)/factorial(degree+1)
    return value-error, value+error


def test_trig_independent_driver(function=endpoint.sin_cos_intervals):
    for theta in (F(-1), F(-1, 4), F(0), F(1, 1000), F(1, 3), F(1)):
        bounds = function(theta)
        for interval, parity in zip(bounds, (1, 0)):
            independent = lagrange_interval(theta, parity)
            assert interval[0] <= independent[0] <= independent[1] <= interval[1], "trig enclosure must contain independent Lagrange certificate"


def test_trig_enclosures_match_independent_lagrange_oracle():
    test_trig_independent_driver(endpoint.sin_cos_intervals)
    for theta in (F(-1, 2), F(1, 100), F(3, 4)):
        outer = endpoint.sin_cos_intervals(theta, terms=3)
        inner = endpoint.sin_cos_intervals(theta, terms=10)
        assert all(a[0] <= b[0] <= b[1] <= a[1] for a, b in zip(outer, inner))
    for theta, terms in ((2, 10), (0, 0), (0, True)):
        with pytest.raises(ValueError, match="Taylor enclosure"):
            endpoint.sin_cos_intervals(theta, terms)


@pytest.mark.parametrize("scale", (F(1, 2**200), F(1), F(2**200)))
@pytest.mark.parametrize("shift", ((0, 0), (10**3, -2*10**3), (10**5, 3*10**5), (10**6, -7*10**5)))
def test_centroid_and_endpoint_rigid_motion_and_unit_invariance(scale, shift):
    # Proper rational rotation and an asymmetric centroid/reference frame.
    rotation = ((F(3, 5), -F(4, 5)), (F(4, 5), F(3, 5)))
    vector = lambda p: tuple(sum(rotation[i][j]*p[j] for j in (0, 1)) for i in (0, 1))
    transform = lambda p: tuple(scale*vector(p)[k]+shift[k] for k in (0, 1))
    changed = tuple(transform(p) for p in POLYGON)
    assert endpoint.area_centroid(changed) == transform(fan_centroid(POLYGON))
    z = (F(2), F(-3), F(0), F(1, 5), F(2, 7), F(-3, 8))
    strain = ((z[3], z[5]/2), (z[5]/2, z[4]))
    rotated = tuple(tuple(sum(rotation[i][a]*strain[a][b]*rotation[j][b] for a in (0, 1) for b in (0, 1))
                          for j in (0, 1)) for i in (0, 1))
    translation = tuple(scale*v for v in vector(z[:2]))
    newz = (*translation, z[2], rotated[0][0], rotated[1][1], 2*rotated[0][1])
    old = endpoint.endpoint_map(POLYGON, z, F(5, 13), F(12, 13))[2]
    new = endpoint.endpoint_map(changed, newz, F(5, 13), F(12, 13))[2]
    assert new == tuple(transform(p) for p in old), "DDA endpoint covariance and unit scaling"


@pytest.mark.parametrize("name,before,after,checker,message", (
    ("area_centroid", "/(3*area2)", "/(2*area2)", test_area_centroid_independent_driver, "area centroid must equal"),
    ("endpoint_map", "-sine+gamma/2", "sine+gamma/2", test_endpoint_independent_driver, "endpoint must match"),
    ("sin_cos_intervals", "term *= -theta*theta", "term *= theta*theta", test_trig_independent_driver, "trig enclosure must contain"),
))
def test_internal_endpoint_mutants_fail_designated_semantics(name, before, after, checker, message):
    # No source-hash assertions are involved. Mutate before execution, not
    # data after the tested code has produced it; require the exact reason.
    original = getattr(endpoint, name)
    checker(original)
    source = inspect.getsource(original)
    assert source.count(before) == 1
    namespace = dict(endpoint.__dict__)
    exec(compile(source.replace(before, after), "<endpoint-semantic-mutant>", "exec"), namespace)
    with pytest.raises(AssertionError, match=message):
        checker(namespace[name])


def test_rounding_unit_is_block_ulp_not_epsilon_coordinate():
    assert endpoint.rounding_unit(((F(3), F(-1)),)) == F(1, 2**51)
    assert endpoint.rounding_unit(((F(4), F(-1)),)) == F(1, 2**50)
    assert endpoint.rounding_unit(((F(0), F(0)),)) == F(1, 2**1074)
    assert endpoint.rounding_unit(((F(3), F(-1)),)) != F(3, 2**52)
    assert endpoint.binary64_decimal("0.10000000000000001") == F(3602879701896397, 36028797018963968)
    for text in ("inf", "nan", "1e-10000"):
        with pytest.raises(ValueError):
            endpoint.binary64_decimal(text)


def test_z_rows_pair_by_step_block_not_csv_order_and_snapshot_is_start(tmp_path, monkeypatch):
    """Two intervals, deliberately reverse the CSV displacement row order."""
    source = tmp_path / "original"
    source.mkdir()
    triangle = ((0, 0), (3, 0), (0, 3))
    geometries = {k: [(x+k, y) for x, y in triangle] for k in range(3)}
    frames = []
    for k in (1, 2):
        wrapped = geometries[k-1]+geometries[k-1][:2]
        frames.append({"kind": "step", "step": k, "geometry": [[7, j, *p] for j, p in enumerate(wrapped)]})
    records = [{"requested_steps": 2}, *frames, {"kind": "end", "completed_steps": 2, "status": "ok"}]
    (source / "shadow.jsonl").write_text("\n".join(json.dumps(record) for record in records)+"\n", encoding="utf-8")
    lines = ["kind,idx,x,y"]
    for label, k in (("initial", 0), ("step0", 0), ("step1", 1), ("step2", 2), ("final", 2)):
        for j, (x, y) in enumerate(geometries[k]+geometries[k][:2]):
            lines.append(f"{label},{j},{x},{y}")
    (source / "geom.csv").write_text("\n".join(lines)+"\n", encoding="utf-8")
    (source / "out.csv").write_text("step,block,z1,z2,z3,z4,z5,z6\n2,7,1,0,0,0,0,0\n1,7,1,0,0,0,0,0\n", encoding="utf-8")
    audit = {"cases": [{"case": "tiny", "files": {name: {"copy": str(source/name), "source": str(source/name), "sha256": endpoint.sha(source/name)}
                                                 for name in ("shadow.jsonl", "geom.csv", "out.csv")}}]}
    endpoint.write_json(tmp_path / "reports/codex/M4c_evidence/kinematics_audit.json", audit)
    monkeypatch.setattr(endpoint, "ROOT", tmp_path)
    monkeypatch.setattr(endpoint, "TMP", tmp_path / "scratch")
    bundle = tmp_path / "bundle"
    result = endpoint.freeze_inputs(bundle)
    rows = list(endpoint.iter_inputs(bundle))
    assert result["block_frames"] == 2
    assert [(row["step"], row["block"]) for row in rows] == [(1, 7), (2, 7)]
    assert rows[0]["end"] == rows[1]["start"]
    assert all(endpoint.reconstruct(row)["delta"] == 0 for row in rows), "z step must advance its own start to its own end"
    with pytest.raises(ValueError, match="never overwrite"):
        endpoint.freeze_inputs(bundle)


def test_frozen_endpoint_evidence_has_all_cases_and_recomputable_extrema():
    summary_path = endpoint.EVIDENCE / "endpoint_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads((endpoint.INPUTS / "manifest.json").read_text(encoding="utf-8"))
    assert summary["complete"] and manifest["complete"]
    assert summary["block_frames"] == manifest["block_frames"] == 15220
    assert len(summary["cases"]) == len(manifest["cases"]) == 15
    assert summary["source_hashes"]["tool"] == endpoint.sha(endpoint.__file__)
    assert summary["source_hashes"]["manifest"] == endpoint.sha(endpoint.INPUTS / "manifest.json")
    assert sum(case["steps"] for case in manifest["cases"].values()) == 1810
    assert all(part["bytes"] < 1_000_000 for part in manifest["shards"])
    for field in ("binary_ratio", "ideal_ratio_upper"):
        example = summary["examples"][field]
        result = endpoint.reconstruct(example["input"])
        assert result[field] == F(example["value_exact"]), "frozen endpoint extremum exact reproduction"
    # This is deliberately a bound in the documented one-ULP convention.
    assert F(summary["maxima_exact"]["binary_ratio"]) < F(11, 10)
    # Mathematical real trig is a separate model, not historical CRT bits.
    assert F(summary["maxima_exact"]["ideal_ratio_upper"]) < F(128, 100)


def test_grouped_replay_physical_start_is_not_padding_start(function=grouped.physical_order):
    """Semantic source summation-order gate, not a source-hash tripwire."""
    summary = json.loads((endpoint.EVIDENCE / "endpoint_grouped_summary.json").read_text(encoding="utf-8"))
    witness = summary["example"]
    row, (lo, hi) = witness["input"], witness["physical_range"]
    normalized = function(row, lo, hi)
    matches, count = endpoint.grouped_binary64_replay(normalized)
    assert matches == count, "physical lo..hi summation start must replay observed binary64 endpoints"
    assert endpoint.grouped_binary64_replay(row)[0] < count
    assert summary["counts"]["coordinates"] == summary["counts"]["physical_order_matches"] == 315760


def test_grouped_physical_start_mutation_fails_semantics():
    test_grouped_replay_physical_start_is_not_padding_start()
    source = inspect.getsource(grouped.physical_order)
    before = 'row["start"][1:]+row["start"][:1]'
    after = 'row["start"]'
    assert source.count(before) == 1
    # Keep vertex/end pairing intact: the defect is the centroid summation
    # start, not an unrelated coordinate permutation.
    end_before = 'row["end"][1:]+row["end"][:1]'
    assert source.count(end_before) == 1
    mutated = source.replace(before, after).replace(end_before, 'row["end"]')
    namespace = dict(grouped.__dict__)
    exec(compile(mutated, "<physical-start-mutant>", "exec"), namespace)
    with pytest.raises(AssertionError, match="physical lo..hi summation start"):
        test_grouped_replay_physical_start_is_not_padding_start(namespace["physical_order"])


def determinant3(rows):
    a, b, c = rows
    return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])


def test_midpoint_minimal_example_has_independent_three_by_three_reconstruction():
    """Independent raw-coordinate 3x3 fit, decimal square root, Lagrange trig.

    Additional oracle imports: decimal.Decimal/localcontext, used only to
    select the historical rational u proposal; all final bounds are rational.
    No production fit, rotation, centroid or interval primitive is called.
    """
    summary = json.loads((endpoint.EVIDENCE / "endpoint_summary.json").read_text(encoding="utf-8"))
    example = summary["examples"]["midpoint_linf_upper"]
    row = example["input"]
    start = tuple(tuple(F(v) for v in p) for p in row["start"])
    end = tuple(tuple(F(v) for v in p) for p in row["end"])
    z = tuple(F(v) for v in row["z"])
    rows = tuple((F(1), *p) for p in start)
    normal = tuple(tuple(sum(r[i]*r[j] for r in rows) for j in range(3)) for i in range(3))
    denominator = determinant3(normal)
    coefficients = []
    for axis in (0, 1):
        right = tuple(sum(r[i]*p[axis] for r, p in zip(rows, end)) for i in range(3))
        coefficients.append(tuple(determinant3(tuple(tuple(right[i] if j == column else normal[i][j] for j in range(3))
                                                     for i in range(3)))/denominator for column in range(3)))
    cv = tuple(sum(p[k] for p in start)/len(start) for k in (0, 1))
    target = tuple(sum(p[k] for p in end)/len(end) for k in (0, 1))
    centered_start = tuple(tuple(p[k]-cv[k] for k in (0, 1)) for p in start)
    centered_end = tuple(tuple(p[k]-target[k] for k in (0, 1)) for p in end)
    dot = sum(p[0]*q[0]+p[1]*q[1] for p, q in zip(centered_start, centered_end))
    cross = sum(p[0]*q[1]-p[1]*q[0] for p, q in zip(centered_start, centered_end))
    with localcontext() as context:
        context.prec = 100
        d = Decimal(dot.numerator)/Decimal(dot.denominator)
        c = Decimal(cross.numerator)/Decimal(cross.denominator)
        u = F(c/((d*d+c*c).sqrt()+d)).limit_denominator(2**40)
    ca = fan_centroid(start)
    sine, cosine = lagrange_interval(z[2]/2, 1), lagrange_interval(z[2]/2, 0)
    errors = []
    for p in start:
        x, y = p[0]-cv[0], p[1]-cv[1]
        co, si = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        uh = u/2
        ch, sh = (1-uh*uh)/(1+uh*uh), 2*uh/(1+uh*uh)
        old = (cv[0]+(target[0]-cv[0])/2+ch*x-sh*y+((coefficients[0][1]-co)*x+(coefficients[0][2]+si)*y)/2,
               cv[1]+(target[1]-cv[1])/2+sh*x+ch*y+((coefficients[1][1]-si)*x+(coefficients[1][2]-co)*y)/2)
        a, b = p[0]-ca[0], p[1]-ca[1]
        offset = (ca[0]+z[0]/2+(z[3]*a+z[5]*b/2)/2,
                  ca[1]+z[1]/2+(z[4]*b+z[5]*a/2)/2)
        for k, (cc, ss) in enumerate(((a, -b), (b, a))):
            cends = sorted(cc*v for v in cosine)
            sends = sorted(ss*v for v in sine)
            lo, hi = offset[k]+cends[0]+sends[0]-old[k], offset[k]+cends[1]+sends[1]-old[k]
            errors.append((F(0) if lo <= 0 <= hi else min(abs(lo), abs(hi)), max(abs(lo), abs(hi))))
    lower, upper = max(v[0] for v in errors), max(v[1] for v in errors)
    assert F(9626408, 10**12) < lower <= upper < F(9626410, 10**12), "independent midpoint discrepancy interval"
    assert lower <= F(example["value_exact"]), "frozen midpoint upper bound must cover independent lower bound"
