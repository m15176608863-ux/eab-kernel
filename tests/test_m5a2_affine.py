"""M5a2 affine proposals: independent rational arithmetic primary oracles.

Oracle imports: fractions.Fraction only. The three-by-three determinant fit,
component trajectory formulas and covariance maps below share no production
fit, rotation, polynomial, geometry or construction primitive. Imports of SE2
and M4c are consistency checks, not the primary oracle. No first-contact or
physical-path certification claim is made for the general affine proposal.
"""
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
from random import Random
import sys

import pytest

from eab.kernel2d.affine_motion import AffineFit, DDAAffineMotion, fit_affine
from eab.kernel2d.motion import motion_first_entrance
from eab.kernel2d.se2 import SE2Motion

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import m5a2_affine_replay as replay


POINTS = ((0, 0), (4, 0), (5, 2), (3, 4), (-1, 3))
MATRIX = ((F(7, 6), F(1, 9)), (-F(2, 7), F(8, 9)))


def determinant3(a):
    return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
            -a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
            +a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))


def independent_fit(start, end):
    """Raw-coordinate 3x3 normal equations + Cramer's rule, no centering."""
    rows = tuple((F(1), F(x), F(y)) for x, y in start)
    normal = tuple(tuple(sum(row[i]*row[j] for row in rows) for j in range(3)) for i in range(3))
    denominator = determinant3(normal)
    coefficients = []
    for axis in (0, 1):
        right = tuple(sum(row[i]*point[axis] for row, point in zip(rows, end)) for i in range(3))
        coefficients.append(tuple(determinant3(tuple(tuple(right[i] if j == column else normal[i][j]
                                                              for j in range(3)) for i in range(3)))/denominator
                                  for column in range(3)))
    return tuple(coefficients)


def targets(points=POINTS, noisy=False):
    return tuple((F(2)+MATRIX[0][0]*x+MATRIX[0][1]*y+(F(1, 10**100) if noisy and i == 1 else 0),
                  -F(3)+MATRIX[1][0]*x+MATRIX[1][1]*y) for i, (x, y) in enumerate(points))


@pytest.mark.parametrize("points,noisy", ((POINTS, False), (POINTS, True), (POINTS[:3], False)))
def test_fit_matches_independent_three_point_and_normal_equation_oracles(points, noisy):
    end = targets(points, noisy)
    fit, reference = fit_affine(points, end), independent_fit(points, end)
    for i, (x, y) in enumerate(points):
        expected = tuple(row[0]+row[1]*x+row[2]*y for row in reference)
        assert fit.endpoint((x, y)) == expected, "affine endpoint independent normal-equation oracle"
        assert fit.residuals[i] == tuple(end[i][k]-expected[k] for k in (0, 1)), "exact endpoint residual vector"
    assert fit.delta == max(abs(v) for row in fit.residuals for v in row), "exact residual maximum must not be rounded"
    assert (fit.delta > 0) == noisy, "no positive residual may disappear below binary64"
    assert fit.endpoint_certificate == ("UNCERTIFIED_NONAFFINE_ENDPOINTS" if noisy else "EXACT_AFFINE_ENDPOINTS"), "positive residual must not receive endpoint-exact certificate"
    for k in (0, 1):
        assert sum(row[k] for row in fit.residuals) == 0
        assert all(sum(r[k]*F(p[j]) for r, p in zip(fit.residuals, points)) == 0 for j in (0, 1))


@pytest.mark.parametrize("scale,shift", ((F(1, 2**400), (10**6, -10**5)), (F(1), (0, 0)), (F(2**397), (-10**3, 10**5))))
def test_affine_fit_and_trajectory_covary_under_rigid_coordinates_and_units(scale, shift):
    def vector(p):
        return (scale*(3*p[0]-4*p[1])/5, scale*(4*p[0]+3*p[1])/5)

    def point(p):
        q = vector(p)
        return tuple(q[k]+shift[k] for k in (0, 1))

    a, b = fit_affine(POINTS, targets(noisy=True)), fit_affine(tuple(map(point, POINTS)), tuple(map(point, targets(noisy=True))))
    assert b.center == point(a.center)
    assert b.translation == vector(a.translation)
    assert b.residuals == tuple(map(vector, a.residuals)), "rotation/large-translation/unit residual covariance"
    assert sum(v*v for row in b.residuals for v in row) == scale*scale*sum(v*v for row in a.residuals for v in row)
    ma, mb = DDAAffineMotion(a.matrix, F(1, 11), a.translation, a.center), DDAAffineMotion(b.matrix, F(1, 11), b.translation, b.center)
    for p in POINTS:
        for s in (F(0), F(2, 7), F(1)):
            assert mb.at(point(p), s) == point(ma.at(p, s)), "trajectory coordinate covariance"


def test_seeded_random_rational_rotation_covariance():
    random = Random(51027)
    a = fit_affine(POINTS, targets(noisy=True))
    ma = DDAAffineMotion(a.matrix, F(1, 19), a.translation, a.center)
    products = []
    for index in range(6):
        u = F(random.randrange(-39, 40), 41)
        co, si = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        shift = ((0, 0), (10**3, -10**3), (10**5, -10**5), (10**6, -10**6))[index % 4]

        def vector(p):
            return (co*p[0]-si*p[1], si*p[0]+co*p[1])

        def point(p):
            v = vector(p)
            return (v[0]+shift[0], v[1]+shift[1])

        b = fit_affine(tuple(map(point, POINTS)), tuple(map(point, targets(noisy=True))))
        assert b.residuals == tuple(map(vector, a.residuals)), "seeded random rotation residual covariance"
        mb = DDAAffineMotion(b.matrix, ma.u1, b.translation, b.center)
        product = tuple(mb.at(point(p), F(3, 7)) for p in POINTS)
        assert product == tuple(point(ma.at(p, F(3, 7))) for p in POINTS)
        products.append(product)
    assert len(set(products)) == 6, "randomized coordinate-frame products are distinct"


def test_additive_trajectory_matches_independent_component_oracle():
    u = F(2, 9)
    model = DDAAffineMotion(MATRIX, u, (F(3, 8), -F(7, 5)), (13, -9))
    c0, s0 = (1-u*u)/(1+u*u), 2*u/(1+u*u)
    for point in POINTS:
        for t in (F(0), F(1, 10**6), F(1, 3), F(1)):
            x, y = point[0]-13, point[1]+9
            z = t*u
            co, si = (1-z*z)/(1+z*z), 2*z/(1+z*z)
            expected = (13+t*F(3, 8)+co*x-si*y+t*((MATRIX[0][0]-c0)*x+(MATRIX[0][1]+s0)*y),
                        -9-t*F(7, 5)+si*x+co*y+t*((MATRIX[1][0]-s0)*x+(MATRIX[1][1]-c0)*y))
            assert model.at(point, t) == expected, "independent additive rotation/strain components"
        assert model.endpoint(point) == tuple(model.center[k]+model.translation[k]+sum(
            MATRIX[k][j]*(point[j]-model.center[j]) for j in (0, 1)) for k in (0, 1))


def test_zero_strain_is_se2_and_zero_rotation_is_m4c_vertex_chord():
    u = F(1, 3)
    rigid = SE2Motion(u, (F(1, 7), -F(3, 11)), (5, -7))
    exact_rotation = ((F(4, 5), -F(3, 5)), (F(3, 5), F(4, 5)))
    affine_rigid = DDAAffineMotion(exact_rotation, u, rigid.translation, rigid.center)
    deforming = DDAAffineMotion(MATRIX, 0, rigid.translation, rigid.center)
    for point in POINTS:
        for s in (F(0), F(1, 9), F(2, 7), F(1)):
            assert affine_rigid.at(point, s) == rigid.at(point, s), "E=0 exactly reduces to M5a SE2"
            end = deforming.endpoint(point)
            assert deforming.at(point, s) == tuple((1-s)*point[k]+s*end[k] for k in (0, 1)), "u=0 exactly equals M4c chord vertex path"
    square = ((0, 0), (1, 0), (1, 1), (0, 1))
    wall = ((2, -1), (3, -1), (3, 2), (2, 2))
    expanding = DDAAffineMotion(((2, 0), (0, 1)), 0, (1, 0))
    answer = motion_first_entrance(square, wall, tuple(expanding.endpoint(p) for p in square), wall)
    assert answer.exact_time == F(1, 2), "u=0 first contact agrees with independent x_right=1+2s closed form"


def test_linear_residual_correction_closes_data_without_certification():
    end = targets(noisy=True)
    fit = fit_affine(POINTS, end)
    path = DDAAffineMotion(fit.matrix, F(1, 13), fit.translation, fit.center)
    chord_path = DDAAffineMotion(fit.matrix, 0, fit.translation, fit.center)
    for p, q, residual in zip(POINTS, end, fit.residuals):
        assert path.corrected_at(p, residual, 0) == p
        assert path.corrected_at(p, residual, 1) == q, "corrected path exactly closes original snapshot endpoint"
        for s in (F(1, 7), F(3, 5)):
            a, b = path.at(p, s), path.corrected_at(p, residual, s)
            assert max(abs(a[k]-b[k]) for k in (0, 1)) <= s*fit.delta
            assert chord_path.corrected_at(p, residual, s) == tuple((1-s)*p[k]+s*q[k] for k in (0, 1)), "u=0 corrected path equals the original snapshot chord"
    assert fit.delta > 0 and fit.endpoint_certificate == "UNCERTIFIED_NONAFFINE_ENDPOINTS"


def test_orientation_sufficient_bound_and_degenerate_counterexample():
    good = DDAAffineMotion(((F(6, 5), F(1, 10)), (F(1, 10), F(9, 10))))
    bad = DDAAffineMotion(((-1, 0), (0, -1)))
    assert good.orientation_preserving_sufficient
    assert not bad.orientation_preserving_sufficient
    for s in (F(0), F(1, 5), F(1)):
        a, b, c = good.at((0, 0), s), good.at((1, 0), s), good.at((0, 1), s)
        assert (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]) > 0
    assert bad.at((0, 0), F(1, 2)) == bad.at((1, 0), F(1, 2)), "endpoints alone do not prove path non-inversion"


def test_endpoint_residual_cannot_bound_unknown_interior_path():
    # Two exact endpoint-identical paths: stationary versus arbitrary excursion.
    for amplitude in (F(1), F(10**12)):
        excursion = lambda s: 4*amplitude*s*(1-s)
        assert excursion(F(0)) == excursion(F(1)) == 0
        assert excursion(F(1, 2)) == amplitude, "zero endpoint error permits unbounded interior discrepancy"


def test_gap_normalizer_matches_independent_rectangle_closed_forms():
    def square(x, y):
        return tuple((F(x)+a, F(y)+b) for a, b in ((0, 0), (1, 0), (1, 1), (0, 1)))

    origin, diagonal, far, touch = square(0, 0), square(4, 5), square(100, 0), square(1, 0)
    assert replay.gap_square(origin, diagonal) == 25, "independent 3-4-5 nearest-set gap"
    assert replay.gap_square(origin, touch) == 0
    assert replay.gap_square(origin, square(F(1, 2), 0)) == 0
    assert replay.nearest_gap_squares({1: origin, 2: diagonal, 3: far}) == {1: F(25), 2: F(25), 3: F(9041)}, "AABB pruning preserves nearest closed-form distance"
    assert replay.nearest_gap_squares({1: origin, 2: diagonal, 3: touch}) == {1: F(0), 2: F(20), 3: F(0)}


def test_exact_affine_input_domain_rejects_inexact_and_degenerate_data():
    with pytest.raises(ValueError, match="exact integers"):
        fit_affine(((0.0, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)))
    with pytest.raises(ValueError, match="span the plane"):
        fit_affine(((0, 0), (1, 1), (2, 2)), ((0, 0), (1, 0), (0, 1)))
    with pytest.raises(ValueError, match="exact integers"):
        DDAAffineMotion(u1=True)
    with pytest.raises(ValueError, match="closed unit"):
        DDAAffineMotion().at((0, 0), F(4, 3))
    with pytest.raises(ValueError, match="nonempty residual"):
        AffineFit((0, 0), (0, 0), ((1, 0), (0, 1)), ())
    with pytest.raises(ValueError, match="exact integers"):
        AffineFit((0, 0), (0, 0), ((1, 0), (0, 1)), ((1e-100, 0),))
    with pytest.raises(ValueError, match="two-dimensional"):
        AffineFit((0, 0), (0, 0), ((1, 0), (0, 1)), ((0, 0, 0),))


@pytest.mark.parametrize("changed", ("snapshot", "terminal", "m5a_normalized", "m5a_audit"))
def test_affine_replay_rejects_each_consumed_input_changing_during_computation(tmp_path, monkeypatch, changed):
    # Build a small full input closure from TRACKED fixtures. No dependency on
    # ignored 1810-step source exports is allowed in the ordinary test suite.
    root = Path(__file__).resolve().parents[1]
    source = root / "fixtures/m4b_shadow/bbF038.jsonl.gz"
    _, frames, _ = replay.rigid.chord.snapshot.read_snapshot(source)
    endpoint = json.loads((root / "fixtures/m4c_motion/endpoints.json").read_text(encoding="utf-8"))["cases"]["bbF038"]["geometry"]
    copies = {name: tmp_path / (name+".input") for name in ("snapshot", "terminal", "m5a_normalized", "m5a_audit")}
    copies["snapshot"].write_bytes(gzip.decompress(source.read_bytes()))
    copies["m5a_normalized"].write_bytes((root / "fixtures/m5a_se2/bbF038.jsonl.gz").read_bytes())
    groups = [("initial", frames[0]["geometry"]), ("final", endpoint)]
    groups += [(f"step{i}", frame["geometry"]) for i, frame in enumerate(frames)]
    groups.append((f"step{len(frames)}", endpoint))
    csv = "kind,idx,x,y\n"+"".join(f"{kind},{v},{x},{y}\n" for kind, geometry in groups for _, v, x, y in geometry)
    copies["terminal"].write_text(csv, encoding="utf-8", newline="")
    audit = {"complete": True, "audit": "GREEN", "normalized_sha256": replay.file_hash(copies["m5a_normalized"]),
             "input_hashes": {"snapshot": replay.file_hash(copies["snapshot"]), "terminal_source": replay.file_hash(copies["terminal"])}}
    copies["m5a_audit"].write_text(json.dumps(audit), encoding="utf-8")
    monkeypatch.setattr(replay, "input_paths", lambda case: copies)
    original_fit, was_changed = replay.fit_affine, False

    def racing_fit(start, end):
        nonlocal was_changed
        if not was_changed:
            was_changed = True
            suffix = gzip.compress(b"") if changed == "m5a_normalized" else b"\n"
            copies[changed].write_bytes(copies[changed].read_bytes()+suffix)
        return original_fit(start, end)

    monkeypatch.setattr(replay, "fit_affine", racing_fit)
    with pytest.raises(AssertionError, match="affine replay input changed during run"):
        replay.replay_case("bbF038", tmp_path / "out")
    assert was_changed
    assert not (tmp_path / "out/bbF038/summary.json").exists(), "changed inputs cannot publish a complete case summary"


@pytest.mark.parametrize("name", ("../../outside", "..\\outside", "/absolute", "D:\\outside", ".", "..", "", "trailing.", " padded "))
def test_affine_replay_cli_rejects_nonlocal_run_names_before_writing(name):
    with pytest.raises(SystemExit) as error:
        replay.parse_arguments(["--run-name", name])
    assert error.value.code == 2


@pytest.mark.parametrize("workers", ("0", "-1", "5", "100"))
def test_affine_replay_cli_rejects_worker_counts_outside_one_to_four(workers):
    with pytest.raises(SystemExit) as error:
        replay.parse_arguments(["--workers", workers])
    assert error.value.code == 2


def test_affine_replay_cli_resolves_directory_containment(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "TMP", tmp_path)
    args = replay.parse_arguments(["--run-name", "affine-valid_4", "--workers", "4"])
    assert args.run_name == (tmp_path / "affine-valid_4").resolve() and args.workers == 4
    original_resolve = Path.resolve

    def redirected_resolve(path, *args, **kwargs):
        if path.name == "redirected":
            return original_resolve(tmp_path.parent / "outside", *args, **kwargs)
        return original_resolve(path, *args, **kwargs)

    # Exercise the resolved-path check without OS-dependent symlink privileges.
    monkeypatch.setattr(Path, "resolve", redirected_resolve)
    with pytest.raises(SystemExit) as error:
        replay.parse_arguments(["--run-name", "redirected"])
    assert error.value.code == 2

