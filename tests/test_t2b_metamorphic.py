"""Exact whole-certificate changes of world frame and physical unit.

The oracle is the explicit affine action on every geometric field: translations
cancel from relative displacements, and planar rotations commute. It uses no
production transformation or proposal routine.
"""
from copy import deepcopy
from fractions import Fraction as F
import random

import pytest

from eab.kernel2d.se2_cage import SE2CageCertificate, verify_se2_cage
from t2b_cage_fixtures import capped_certificate, closed_disk_certificate, instance_of


@pytest.mark.parametrize("factory", [closed_disk_certificate, capped_certificate])
@pytest.mark.parametrize("seed", [7101, 7102, 7103])
@pytest.mark.parametrize("translation", [0, 1000, 100000])
@pytest.mark.parametrize("scale", [F(1, 10**8), F(1), F(1000)])
def test_whole_certificate_rigid_frame_and_unit_covariance(factory, seed, translation, scale):
    parameter = F(random.Random(seed).randint(-97, 97), 101)

    def transform(point, absolute=False):
        x, y = point
        u = parameter
        a = scale*((1-u*u)*x-2*u*y)/(1+u*u)
        b = scale*(2*u*x+(1-u*u)*y)/(1+u*u)
        if absolute:
            a += translation
            b -= F(7, 3)*translation
        return a, b

    def polygon(points, absolute=False):
        return tuple(transform(point, absolute) for point in points)

    original = factory()
    expected = verify_se2_cage(instance_of(original), original)
    assert expected.valid
    certificate = deepcopy(original)
    certificate["moving"] = polygon(original["moving"], True)
    certificate["obstacles"] = tuple(polygon(ring, True) for ring in original["obstacles"])
    certificate["center"] = transform(original["center"], True)
    certificate["radius"] *= scale
    certificate["moving_pieces"] = tuple(polygon(ring, True) for ring in original["moving_pieces"])
    certificate["obstacle_pieces"] = tuple({"obstacle": row["obstacle"],
                                           "ring": polygon(row["ring"], True)}
                                          for row in original["obstacle_pieces"])
    if certificate["disk"] is not None:
        certificate["disk"]["radius"] *= scale
        certificate["disk"]["polygon"] = polygon(certificate["disk"]["polygon"])
    for interval in certificate["intervals"]:
        interval["rho"] *= scale
        interval["loop"] = polygon(interval["loop"])
        for piece in interval["pieces"]:
            if piece["kind"] == "rotated":
                piece["polygon"] = polygon(piece["polygon"])
    for link in certificate["links"]+certificate["caps"]:
        link["chain"] = tuple(polygon(loop) for loop in link["chain"])
    instance = instance_of(certificate)
    result = verify_se2_cage(instance, certificate)
    assert result.valid and result.counts == expected.counts, result
    encoded = SE2CageCertificate.from_data(certificate).to_json()
    reloaded = SE2CageCertificate.from_json(encoded)
    assert verify_se2_cage(instance, reloaded).counts == expected.counts


def test_translation_coordinate_is_not_shifted_by_world_origin():
    certificate = closed_disk_certificate()
    instance = instance_of(certificate)
    for interval in certificate["intervals"]:
        interval["loop"] = [(x+100000, y) for x, y in interval["loop"]]
    for item in certificate["links"]:
        item["chain"] = [[(x+100000, y) for x, y in loop] for loop in item["chain"]]
    result = verify_se2_cage(instance, certificate)
    assert not result.valid and result.condition == "V4"
