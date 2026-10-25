"""P0 JSON grammar, schema, CLI, and input binding gates (lemma sections 2,7)."""
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

import pytest

import t2b_independent_cage_verifier as verifier
from t2b_hand_cage_builder import build_hand_cages, build_low_room_cage

def value_copy(value):
    return json.loads(json.dumps(value))



CAGES = build_hand_cages()


def _pair(cages, name="doorway"):
    instance, certificate = cages[name]
    return value_copy(instance), value_copy(certificate)


def _reject(instance, certificate, condition="V0"):
    result = verifier.verify_cage(instance, certificate)
    assert result["valid"] is False, result
    assert result["condition"] == condition, result
    assert result["reason"]
    assert isinstance(result["counts"], dict)
    return result


@pytest.mark.parametrize("name", ("doorway", "windmill", "midpoint_wedges", "diamond_plates"))
def test_four_hand_certificates_accepted(name):
    instance, certificate = _pair(CAGES, name)
    result = verifier.verify_cage(instance, certificate)
    assert result["valid"] and result["condition"] == "OK", result
    assert result["counts"]["start_winding"] != 0
    assert result["counts"]["barrier_segments"] == 2 * (len(certificate["intervals"][0]["loop"]) - 1)


def test_low_room_rotated_capped_certificate_accepted():
    instance, certificate = build_low_room_cage()
    result = verifier.verify_cage(instance, certificate)
    assert result["valid"] and result["condition"] == "OK", result


@pytest.mark.parametrize("text", (
    " 3/8", "1e-3", "0.5", "1_000", "+3", "-0", "0/5", "2/4", "3/1",
    "１", "١", "1/２", "1/-2", "03", "-0/5", "3/0", "3/08", "3/8 ",
    "\t3/8", "3\n", "--3", "", "/3", "1/2/3", "NaN", "Infinity",
))
def test_noncanonical_rational_rejected(text):
    instance, certificate = _pair(CAGES)
    certificate["radius"] = text
    _reject(instance, certificate)


@pytest.mark.parametrize("value", (1, True, None, [], {}, 0.5))
def test_nonstring_rational_rejected(value):
    instance, certificate = _pair(CAGES)
    certificate["radius"] = value
    _reject(instance, certificate)


def test_rational_decoded_length_limit():
    instance, certificate = _pair(CAGES)
    certificate["radius"] = "1" + "0" * 4096
    _reject(instance, certificate)


@pytest.mark.parametrize("field", (
    "format", "moving", "obstacles", "center", "radius", "moving_pieces", "obstacle_pieces",
    "disk", "chain", "start_interval", "intervals", "links", "caps",
))
def test_every_top_level_key_required(field):
    instance, certificate = _pair(CAGES)
    del certificate[field]
    _reject(instance, certificate)


@pytest.mark.parametrize("site", ("top", "chain", "disk", "interval", "piece", "link", "obstacle_piece", "instance"))
def test_unknown_keys_rejected_at_every_object_schema(site):
    instance, certificate = _pair(CAGES)
    selected = certificate
    if site == "chain":
        selected = certificate["chain"]
    elif site == "disk":
        selected = certificate["disk"]
    elif site == "interval":
        selected = certificate["intervals"][0]
    elif site == "piece":
        selected = certificate["intervals"][0]["pieces"][0]
    elif site == "link":
        selected = certificate["links"][0]
    elif site == "obstacle_piece":
        selected = certificate["obstacle_pieces"][0]
    elif site == "instance":
        selected = instance
    selected["unknown"] = 0
    _reject(instance, certificate)


@pytest.mark.parametrize("site", ("start", "host", "obstacle", "barrier_kernel", "barrier_obstacle", "exact", "at", "left"))
@pytest.mark.parametrize("bad", (True, False, -1, "0", None))
def test_index_type_nonnegative_and_bool_exclusion(site, bad):
    instance, certificate = _pair(CAGES)
    if site == "start":
        certificate["start_interval"] = bad
    elif site == "host":
        certificate["disk"]["host"] = bad
    elif site == "obstacle":
        certificate["obstacle_pieces"][0]["obstacle"] = bad
    elif site == "barrier_kernel":
        certificate["intervals"][0]["witnesses"][0][0] = bad
    elif site == "barrier_obstacle":
        certificate["intervals"][0]["witnesses"][0][1] = bad
    elif site == "exact":
        certificate["links"][0]["witnesses"][0][0][0] = ["exact", bad]
    elif site == "at":
        certificate["links"][0]["at"] = bad
    else:
        certificate["links"][0]["witnesses"][0][0][0] = ["left", bad]
    _reject(instance, certificate)


@pytest.mark.parametrize("site", ("start", "host", "obstacle", "barrier_kernel", "barrier_obstacle", "exact", "at"))
def test_index_out_of_bounds_is_v0(site):
    instance, certificate = _pair(CAGES)
    bad = 1000000
    if site == "start":
        certificate["start_interval"] = bad
    elif site == "host":
        certificate["disk"]["host"] = bad
    elif site == "obstacle":
        certificate["obstacle_pieces"][0]["obstacle"] = bad
    elif site == "barrier_kernel":
        certificate["intervals"][0]["witnesses"][0][0] = bad
    elif site == "barrier_obstacle":
        certificate["intervals"][0]["witnesses"][0][1] = bad
    elif site == "exact":
        certificate["links"][0]["witnesses"][0][0][0] = ["exact", bad]
    else:
        certificate["links"][0]["at"] = bad
    _reject(instance, certificate)


@pytest.mark.parametrize("tag", ("left", "right"))
def test_side_index_out_of_bounds_is_v5(tag):
    instance, certificate = _pair(CAGES)
    certificate["links"][0]["witnesses"][0][0][0] = [tag, 1000000]
    _reject(instance, certificate, "V5")


@pytest.mark.parametrize("site", ("format", "chain", "piece", "reference"))
def test_unknown_fixed_tags_are_v0(site):
    instance, certificate = _pair(CAGES)
    if site == "format":
        certificate["format"] = "eab.t2b.cage/2"
    elif site == "chain":
        certificate["chain"]["kind"] = "open"
    elif site == "piece":
        certificate["intervals"][0]["pieces"][0]["kind"] = "magic"
    else:
        certificate["links"][0]["witnesses"][0][0][0] = ["magic"]
    _reject(instance, certificate)


@pytest.mark.parametrize("site", ("interval", "link"))
@pytest.mark.parametrize("bad", ("null", "missing", "short", "long"))
def test_witnesses_mandatory_exact_shape(site, bad):
    instance, certificate = _pair(CAGES)
    obj = certificate["intervals"][0]
    if site == "link":
        obj = certificate["links"][0]
    if bad == "null":
        obj["witnesses"] = None
    elif bad == "missing":
        del obj["witnesses"]
    elif bad == "short":
        obj["witnesses"].pop()
    else:
        obj["witnesses"].append(value_copy(obj["witnesses"][0]))
    _reject(instance, certificate)


@pytest.mark.parametrize("bad", ("short", "long"))
def test_quadrilateral_witness_row_exact_shape(bad):
    instance, certificate = _pair(CAGES)
    row = certificate["links"][0]["witnesses"][0]
    if bad == "short":
        row.pop()
    else:
        row.append(value_copy(row[0]))
    _reject(instance, certificate)


@pytest.mark.parametrize("field", ("moving", "obstacles"))
def test_geometry_binding_rejects_cyclic_reindexing(field):
    instance, certificate = _pair(CAGES)
    if field == "moving":
        ring = certificate["moving"]
        certificate["moving"] = ring[1:] + ring[:1]
    else:
        ring = certificate["obstacles"][0]
        certificate["obstacles"][0] = ring[1:] + ring[:1]
    result = _reject(instance, certificate)
    assert result["where"]["check"] == "instance_binding"


def test_geometry_binding_rejects_obstacle_reorder():
    instance, certificate = _pair(CAGES)
    certificate["obstacles"][0], certificate["obstacles"][1] = certificate["obstacles"][1], certificate["obstacles"][0]
    result = _reject(instance, certificate)
    assert result["where"]["check"] == "instance_binding"


def test_disk_null_cannot_be_referenced():
    instance, certificate = _pair(CAGES)
    certificate["disk"] = None
    _reject(instance, certificate)


def test_interval_count_and_nonempty_kernel():
    instance, certificate = _pair(CAGES)
    certificate["intervals"].pop()
    _reject(instance, certificate)
    instance, certificate = _pair(CAGES)
    certificate["intervals"][0]["pieces"] = []
    _reject(instance, certificate)


def test_homotopy_needs_two_polylines():
    instance, certificate = _pair(CAGES)
    certificate["links"][0]["chain"].pop()
    certificate["links"][0]["witnesses"] = []
    _reject(instance, certificate)


@pytest.mark.parametrize("token", ("-0", "-1", "1.0", "1e0", "1E+0", "NaN", "Infinity", "-Infinity", "true"))
def test_raw_integer_tokens_rejected_before_information_loss(tmp_path, token):
    instance, certificate = _pair(CAGES)
    text = json.dumps(certificate).replace('"start_interval": 1', '"start_interval": ' + token)
    a = tmp_path / "instance.json"
    b = tmp_path / "certificate.json"
    a.write_text(json.dumps(instance), encoding="utf-8")
    b.write_text(text, encoding="utf-8")
    result = verifier._load_result(a, b)
    assert not result["valid"] and result["condition"] == "V0", result


@pytest.mark.parametrize("escaped", (False, True))
def test_raw_duplicate_keys_rejected_even_when_unicode_escaped(tmp_path, escaped):
    instance, certificate = _pair(CAGES)
    key = '"radius"'
    if escaped:
        key = '"\\u0072adius"'
    text = json.dumps(certificate).replace('"radius": "2"', '"radius": "2", ' + key + ': "2"', 1)
    a = tmp_path / "instance.json"
    b = tmp_path / "certificate.json"
    a.write_text(json.dumps(instance), encoding="utf-8")
    b.write_text(text, encoding="utf-8")
    result = verifier._load_result(a, b)
    assert not result["valid"] and result["condition"] == "V0", result


def test_cli_many_pairs_one_line_each_and_nonzero_for_any_rejection(tmp_path):
    instance, certificate = _pair(CAGES)
    a = tmp_path / "instance.json"
    b = tmp_path / "valid.json"
    c = tmp_path / "invalid.json"
    a.write_text(json.dumps(instance), encoding="utf-8")
    b.write_text(json.dumps(certificate), encoding="utf-8")
    certificate["radius"] = "1/1000"
    c.write_text(json.dumps(certificate), encoding="utf-8")
    script = Path(verifier.__file__)
    result = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(script),
                             str(a), str(b), str(a), str(c), str(a), str(b)],
                            capture_output=True, encoding="utf-8", check=False)
    assert result.returncode != 0
    lines = result.stdout.splitlines()
    assert len(lines) == 3, (result.stdout, result.stderr)
    outcomes = [json.loads(line)["condition"] for line in lines]
    assert outcomes == ["OK", "V0", "OK"]


def test_cli_only_valid_returns_zero(tmp_path):
    instance, certificate = _pair(CAGES)
    a = tmp_path / "instance.json"
    b = tmp_path / "valid.json"
    a.write_text(json.dumps(instance), encoding="utf-8")
    b.write_text(json.dumps(certificate), encoding="utf-8")
    result = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", verifier.__file__, str(a), str(b)],
                            capture_output=True, encoding="utf-8", check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["condition"] == "OK"


def test_v0_precedes_chain_and_chain_precedes_v1():
    instance, certificate = _pair(CAGES)
    certificate["radius"] = "1/1000"
    certificate["chain"]["breakpoints"] = ["-1", "-1", "3"]
    certificate["intervals"][0]["rho"] = "-1"
    _reject(instance, certificate, "V0")
    certificate["radius"] = "2"
    _reject(instance, certificate, "CHAIN")
    certificate["chain"]["breakpoints"] = ["-1", "1", "3"]
    _reject(instance, certificate, "V1")


def test_same_condition_obeys_json_object_field_order():
    instance, certificate = _pair(CAGES)
    certificate["radius"] = "1/1000"
    certificate["moving"] = certificate["moving"][1:] + certificate["moving"][:1]
    result = _reject(instance, certificate)
    assert result["where"]["check"] == "instance_binding"
    reordered = {"radius": certificate["radius"]}
    for key, value in certificate.items():
        if key != "radius":
            reordered[key] = value
    result = _reject(instance, reordered)
    assert result["where"]["check"] == "radius_bound"


def test_schema_error_does_not_hide_earlier_v0_geometry_error():
    instance, certificate = _pair(CAGES)
    certificate["moving"] = certificate["moving"][1:] + certificate["moving"][:1]
    certificate["caps"] = None
    result = _reject(instance, certificate)
    assert result["where"]["check"] == "instance_binding"


def test_late_schema_error_does_not_hide_earlier_radius_bound():
    instance, certificate = _pair(CAGES)
    certificate["radius"] = "1/1000"
    certificate["caps"] = None
    result = _reject(instance, certificate)
    assert result["where"]["check"] == "radius_bound"
