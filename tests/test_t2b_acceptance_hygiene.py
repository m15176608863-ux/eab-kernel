"""Acceptance repair: raw JSON hygiene and exact edge/vertex contact.

The input oracle is the hand-built rectangle cage, not the proposer.  All
malformed certificates enter both verifiers as raw JSON (the independent
implementation uses its own loader).  The contact oracle is a vertical edge
x = 3 touching a triangle only at (3, 1), with a strictly overlapping control.
"""
from fractions import Fraction as F
import json

from eab.kernel2d.se2_cage import _strict_points, verify_se2_cage
from t2b_cage_fixtures import (
    capped_certificate, closed_disk_certificate, instance_of, json_text,
)
from t2b_independent_cage_verifier import _load_result




def test_raw_radius_unreduced_six_over_two_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data.__setitem__("radius", "6/2")
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_radius_decimal_three_point_zero_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data.__setitem__("radius", 3.0)
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_rho_boolean_true_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data["intervals"][0].__setitem__("rho", True)
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_unknown_nested_key_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data["disk"].__setitem__("unknown", [])
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_wrong_format_literal_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data.__setitem__("format", "eab.t2b.cage/0")
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_wrong_chain_kind_literal_is_v0(tmp_path):
    certificate = capped_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data["chain"].__setitem__("kind", "other")
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_three_coordinate_point_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data["center"].append("0")
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_convex_ring_collinear_vertex_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data["disk"]["polygon"].insert(1, ["0", "-1"])
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_interval_count_mismatch_is_v0(tmp_path):
    certificate = closed_disk_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data["intervals"].pop()
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_raw_kernel_piece_index_out_of_bounds_is_v0(tmp_path):
    certificate = capped_certificate()
    instance_text = json_text(instance_of(certificate))
    certificate_text = json_text(certificate)
    assert verify_se2_cage(instance_text, certificate_text).valid
    data = json.loads(certificate_text)
    data["intervals"][0]["pieces"][0].__setitem__("piece", 1)
    bad_text = json.dumps(data)
    instance_path = tmp_path / "instance.json"
    certificate_path = tmp_path / "certificate.json"
    instance_path.write_text(instance_text, encoding="utf-8", newline="\n")
    certificate_path.write_text(bad_text, encoding="utf-8", newline="\n")
    try:
        production = verify_se2_cage(instance_text, bad_text)
    except IndexError as error:
        raise AssertionError("semantic: malformed indices/counts must return V0, not escape as IndexError") from error
    independent = _load_result(instance_path, certificate_path)
    assert not production.valid and production.condition == "V0", production
    assert not independent["valid"] and independent["condition"] == "V0", independent


def test_strict_points_edge_touching_vertex_is_not_penetration():
    first = tuple((F(x), F(y)) for x, y in ((0, 0), (2, 0), (2, 2)))
    second = tuple((F(x), F(y)) for x, y in ((3, 1), (4, 0), (4, 2)))
    touching = (F(1), F(0))
    interior = (F(3, 2), F(0))
    assert _strict_points(first, second, (interior, interior))
    assert not _strict_points(first, second, (touching, touching))
    assert not _strict_points(first, second, (touching, interior))
    assert not _strict_points(first, second, (interior, touching))
    # Reversing the pair tests the opposite SAT bound without a redundant
    # parallel edge of a rectangle masking a one-sided strictness defect.
    reverse_touching = tuple(-v for v in touching)
    reverse_interior = tuple(-v for v in interior)
    assert _strict_points(second, first, (reverse_interior, reverse_interior))
    assert not _strict_points(second, first, (reverse_touching, reverse_touching))
