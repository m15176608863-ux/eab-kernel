"""Exact algebra and metamorphic verification, independent of production code.

Rotation table values use elementary rational unit-circle points.  Whole-input
rigid changes and unit changes preserve predicates rather than tolerances.
These finite gates are not a proof about all polygon inputs.
"""
from fractions import Fraction as F
import random
import json

import pytest

import t2b_independent_cage_verifier as verifier
from t2b_hand_cage_builder import build_hand_cages, build_low_room_cage

def value_copy(value):
    return json.loads(json.dumps(value))



def mapped_point(point, co, si, scale, tx, ty):
    x, y = F(point[0]), F(point[1])
    return [str(scale * (co * x - si * y) + tx),
            str(scale * (si * x + co * y) + ty)]


def mapped_ring(ring, co, si, scale, tx, ty):
    result = []
    for point in ring:
        result.append(mapped_point(point, co, si, scale, tx, ty))
    return result


def transformed_certificate(instance, certificate, co, si, scale, tx, ty):
    """Q commutes with all planar rotations; t is mapped by sQ, not sQ+T."""
    source = value_copy(instance)
    cert = value_copy(certificate)
    source["moving"] = mapped_ring(instance["moving"], co, si, scale, tx, ty)
    source["obstacles"] = []
    for ring in instance["obstacles"]:
        source["obstacles"].append(mapped_ring(ring, co, si, scale, tx, ty))
    cert["moving"] = value_copy(source["moving"])
    cert["obstacles"] = value_copy(source["obstacles"])
    cert["center"] = mapped_point(cert["center"], co, si, scale, tx, ty)
    cert["radius"] = str(scale * F(cert["radius"]))
    cert["moving_pieces"] = []
    for ring in certificate["moving_pieces"]:
        cert["moving_pieces"].append(mapped_ring(ring, co, si, scale, tx, ty))
    for piece in cert["obstacle_pieces"]:
        piece["ring"] = mapped_ring(piece["ring"], co, si, scale, tx, ty)
    if cert["disk"] is not None:
        cert["disk"]["radius"] = str(scale * F(cert["disk"]["radius"]))
        cert["disk"]["polygon"] = mapped_ring(cert["disk"]["polygon"], co, si, scale, F(0), F(0))
    for interval in cert["intervals"]:
        interval["rho"] = str(scale * F(interval["rho"]))
        for piece in interval["pieces"]:
            if piece["kind"] == "rotated":
                piece["polygon"] = mapped_ring(piece["polygon"], co, si, scale, F(0), F(0))
        interval["loop"] = mapped_ring(interval["loop"], co, si, scale, F(0), F(0))
    for category in ("links", "caps"):
        for item in cert[category]:
            chain = []
            for line in item["chain"]:
                chain.append(mapped_ring(line, co, si, scale, F(0), F(0)))
            item["chain"] = chain
    return source, cert


ALL_CAGES = build_hand_cages()
ALL_CAGES["low_room"] = build_low_room_cage()


@pytest.mark.parametrize("name", ("doorway", "windmill", "midpoint_wedges", "diamond_plates", "low_room"))
@pytest.mark.parametrize("translation", (0, 1000, 100000))
@pytest.mark.parametrize("scale", (F(1), F(7), F(1, 1000000)))
def test_exact_random_rotation_translation_and_unit_invariance(name, translation, scale):
    rng = random.Random(47019 + translation)
    u = F(rng.randint(-97, 97), 101)
    denominator = 1 + u * u
    co = (1 - u * u) / denominator
    si = 2 * u / denominator
    instance, certificate = ALL_CAGES[name]
    transformed_instance, transformed_cert = transformed_certificate(
        instance, certificate, co, si, scale, F(3 * translation, 5), F(4 * translation, 5))
    result = verifier.verify_cage(transformed_instance, transformed_cert)
    assert result["valid"] and result["condition"] == "OK", result
    assert result["counts"]["start_winding"] == 1


@pytest.mark.parametrize("lower,upper,expected", (
    (F(-1), F(1), (0, 1, F(-1), F(1), F(0))),
    (F(1), F(3), (2, -1, F(-1), F(1), F(0))),
    (F(3), F(5), (4, 1, F(-1), F(1), F(0))),
    (F(-3), F(-1), (-2, -1, F(-1), F(1), F(0))),
    (F(9, 2), F(5), (4, 1, F(1, 2), F(1), F(3, 4))),
))
def test_midpoint_chart_lift_table(lower, upper, expected):
    assert verifier._chart(lower, upper) == expected


@pytest.mark.parametrize("parameter,sign,expected", (
    (F(0), 1, (F(1), F(0))),
    (F(1), 1, (F(0), F(1))),
    (F(-1), 1, (F(0), F(-1))),
    (F(0), -1, (F(-1), F(0))),
    (F(1, 2), 1, (F(3, 5), F(4, 5))),
    (F(1, 23), 1, (F(264, 265), F(23, 265))),
))
def test_exact_rotation_rational_unit_circle_table(parameter, sign, expected):
    assert verifier._rotate((F(1), F(0)), parameter, sign) == expected


def test_signed_half_open_winding_with_repeated_and_zero_length_segments():
    ring = ((F(-2), F(-1)), (F(3), F(-1)), (F(3), F(0)),
            (F(3), F(0)), (F(3), F(2)), (F(-2), F(2)), (F(-2), F(-1)))
    assert verifier._winding(ring, (F(0), F(0))) == 1
    assert verifier._winding(tuple(reversed(ring)), (F(0), F(0))) == -1
    assert verifier._winding(ring, (F(10), F(0))) == 0


def test_json_order_places_rotated_piece_failure_before_rho_if_piece_is_first():
    instance, certificate = build_low_room_cage()
    interval = certificate["intervals"][0]
    interval["rho"] = "-1"
    # Both constraints belong to V1; in a single rho field negative sign is
    # checked before the magnitude bound.  V2 still must not precede V1.
    interval["pieces"][0]["polygon"][0][0] = "-7/5"
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V1", result
