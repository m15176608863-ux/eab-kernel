"""Acceptance-repair counterexamples with isolated semantic first failures.

All geometry is assembled from the independent hand builder and lemma. These
normal-verifier tests are deliberately not source-mutating; the external
acceptance harness independently confirms each specified single mutant accepts.
"""
import json
from fractions import Fraction as F
from pathlib import Path

import t2b_independent_cage_verifier as verifier
from t2b_hand_cage_builder import (
    build_hand_cages, build_low_room_cage, contraction_chain, rotate_ring,
)


HAND_CAGES = build_hand_cages()


def clone(value):
    return json.loads(json.dumps(value))


def ring_rectangle(x0, y0, x1, y1):
    return [[str(F(x0)), str(F(y0))], [str(F(x1)), str(F(y0))],
            [str(F(x1)), str(F(y1))], [str(F(x0)), str(F(y1))]]


def fraction_ring(ring):
    result = []
    for x, y in ring:
        result.append((F(x), F(y)))
    return result


def shifted_ring(ring, dx, dy):
    result = []
    for x, y in ring:
        result.append([str(F(x) + dx), str(F(y) + dy)])
    return result


def radius_last_vertex_forgery():
    instance, certificate = clone(HAND_CAGES["doorway"])
    ring = clone(certificate["moving"])
    ring[-1] = ["-3/2", "1"]
    instance["moving"] = clone(ring)
    certificate["moving"] = clone(ring)
    certificate["moving_pieces"] = [ring]
    certificate["radius"] = "3/2"
    return instance, certificate


def negative_disk_support_forgery():
    instance, certificate = clone(HAND_CAGES["windmill"])
    ring = shifted_ring(certificate["moving"], F(10), F(0))
    instance["moving"] = clone(ring)
    certificate["moving"] = clone(ring)
    certificate["moving_pieces"] = [ring]
    certificate["radius"] = "100"
    # Center and D deliberately stay at zero. The left support is negative,
    # yet all squared host-distance inequalities hold with r_D=1.
    return instance, certificate


def colliding_start_without_origin_crossing():
    instance, certificate = clone(HAND_CAGES["doorway"])
    dy = F(-1, 4)
    certificate["moving"] = shifted_ring(certificate["moving"], F(0), dy)
    instance["moving"] = clone(certificate["moving"])
    certificate["moving_pieces"] = [clone(certificate["moving"])]
    certificate["center"][1] = str(F(certificate["center"][1]) + dy)
    for interval in certificate["intervals"]:
        interval["loop"] = shifted_ring(interval["loop"], F(0), -dy)
    for link in certificate["links"]:
        lines = []
        for line in link["chain"]:
            lines.append(shifted_ring(line, F(0), -dy))
        link["chain"] = lines
    return instance, certificate


def equal_area_overlapping_partition():
    instance, certificate = clone(HAND_CAGES["doorway"])
    ring = certificate["moving"]
    half_width = F(ring[1][0]) / 2
    central = ring_rectangle(-half_width, F(ring[0][1]), half_width, F(ring[2][1]))
    certificate["moving_pieces"] = [clone(central), clone(central)]
    return instance, certificate


def equal_area_boundary_crossing_partition():
    instance, certificate = clone(HAND_CAGES["doorway"])
    ring = clone(certificate["moving"])
    shift = F(1, 10)
    for index in (0, 1):
        ring[index][0] = str(F(ring[index][0]) - shift)
    for index in (2, 3):
        ring[index][0] = str(F(ring[index][0]) + shift)
    certificate["moving_pieces"] = [ring]
    return instance, certificate


def selected_interval_zero_winding_forgery():
    """Different winding is joined only where the origin really penetrates.

    I_1 lies left of zero, with the low-room barrier winding once. I_2 contains
    zero but is a constant barrier at (0,-1), winding zero. At -1/23 the old
    exact-rotation cap contracts Gamma to zero; zero and (0,-1) both strictly
    penetrate the floor at that angle. Thus all connection witnesses are real.
    """
    instance, certificate = build_low_room_cage()
    base = clone(certificate["intervals"][0])
    loop = fraction_ring(base["loop"])
    moving = fraction_ring(certificate["moving"])
    obstacles = []
    for ring in certificate["obstacles"]:
        obstacles.append(fraction_ring(ring))
    first_cap = None
    for count in (4, 8, 16, 32):
        first_cap = contraction_chain(rotate_ring(moving, F(-1, 22)), obstacles, loop, count)
        if first_cap is not None:
            break
    if first_cap is None:
        raise ValueError("left-end exact contraction unavailable")
    first_cap["at"] = 0
    first = clone(base)
    first["rho"] = "1/250"
    second = clone(base)
    constant = []
    for point in base["loop"]:
        constant.append(["0", "-1"])
    second["loop"] = clone(constant)
    second["witnesses"] = []
    for point in constant[:-1]:
        second["witnesses"].append([0, 0])
    link = clone(certificate["caps"][0])
    link["at"] = 1
    link["chain"].append(clone(constant))
    row = []
    for point in constant[:-1]:
        row.append([["exact", 0], 0])
    link["witnesses"].append(clone(row))
    last_cap = {"at": 2, "chain": [clone(constant), clone(constant)], "witnesses": [clone(row)]}
    certificate["chain"]["breakpoints"] = ["-1/22", "-1/23", "1/23"]
    certificate["start_interval"] = 2
    certificate["intervals"] = [first, second]
    certificate["links"] = [link]
    certificate["caps"] = [first_cap, last_cap]
    return instance, certificate


def test_acceptance_a05_radius_checks_last_vertex_not_only_prefix():
    instance, certificate = radius_last_vertex_forgery()
    center = tuple(F(value) for value in certificate["center"])
    squared = []
    for point in fraction_ring(certificate["moving_pieces"][0]):
        x, y = point[0] - center[0], point[1] - center[1]
        squared.append(x * x + y * y)
    bound = F(certificate["radius"]) * F(certificate["radius"])
    assert all(value <= bound for value in squared[:-1]) and squared[-1] > bound
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V0" and result["where"]["check"] == "radius_bound", result
    assert result["valid"] is False


def test_acceptance_v302_disk_host_requires_nonnegative_support():
    instance, certificate = negative_disk_support_forgery()
    host = fraction_ring(certificate["moving_pieces"][0])
    negative = False
    for index, a in enumerate(host):
        b = host[(index + 1) % len(host)]
        nx, ny = b[1] - a[1], a[0] - b[0]
        support = nx * a[0] + ny * a[1]
        assert support * support >= nx * nx + ny * ny
        negative = negative or support < 0
    assert negative
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V3" and result["where"]["check"] == "disk_host", result
    assert result["valid"] is False


def test_acceptance_v601_v607_start_collision_without_origin_crossing():
    instance, certificate = colliding_start_without_origin_crossing()
    loop = fraction_ring(certificate["intervals"][0]["loop"])
    origin = (F(0), F(0))
    assert verifier._winding(loop, origin) == 1
    for index in range(len(loop) - 1):
        assert not verifier._on_segment(origin, loop[index], loop[index + 1])
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V6" and result["where"]["check"] == "start_free", result
    assert result["valid"] is False


def test_acceptance_a07_overlap_rejected_even_when_area_sum_matches():
    instance, certificate = equal_area_overlapping_partition()
    parent = fraction_ring(certificate["moving"])
    pieces = [fraction_ring(ring) for ring in certificate["moving_pieces"]]
    assert verifier._area2(pieces[0]) + verifier._area2(pieces[1]) == verifier._area2(parent)
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V0" and result["where"]["check"] == "partition_disjoint", result
    assert result["valid"] is False


def test_acceptance_a08_boundary_rejected_even_when_area_sum_matches():
    instance, certificate = equal_area_boundary_crossing_partition()
    assert verifier._area2(fraction_ring(certificate["moving_pieces"][0])) == verifier._area2(fraction_ring(certificate["moving"]))
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V0" and result["where"]["check"] == "partition_boundary", result
    assert result["valid"] is False


def test_acceptance_v608_winding_uses_selected_interval_not_first():
    instance, certificate = selected_interval_zero_winding_forgery()
    assert certificate["start_interval"] == 2
    origin = (F(0), F(0))
    assert verifier._winding(fraction_ring(certificate["intervals"][0]["loop"]), origin) == 1
    assert verifier._winding(fraction_ring(certificate["intervals"][1]["loop"]), origin) == 0
    result = verifier.verify_cage(instance, certificate)
    assert result["condition"] == "V6" and result["where"]["check"] == "start_winding", result
    assert result["valid"] is False


def test_acceptance_geometry_exported_pairs_equal_independent_builders():
    directory = Path(__file__).resolve().parent / "data/t2b_acceptance"
    cases = (
        ("geometry_a05", radius_last_vertex_forgery()),
        ("geometry_a07", equal_area_overlapping_partition()),
        ("geometry_a08", equal_area_boundary_crossing_partition()),
        ("geometry_v302", negative_disk_support_forgery()),
        ("geometry_start_free", colliding_start_without_origin_crossing()),
        ("geometry_v608", selected_interval_zero_winding_forgery()),
    )
    for stem, pair in cases:
        instance, certificate = pair
        instance_path = directory / (stem + ".instance.json")
        certificate_path = directory / (stem + ".cert.json")
        assert json.loads(instance_path.read_text(encoding="utf-8")) == instance
        assert json.loads(certificate_path.read_text(encoding="utf-8")) == certificate
        for path in (instance_path, certificate_path):
            raw = path.read_bytes()
            assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw
