"""Reader uses struct/Fraction and production APIs, never codec encoders.

These tests may construct records using the writer, but the reader module is
independently implemented. Internal serialization corruption must fail exact
field/equation assertions, not a current-source-hash comparison.
"""
import ast
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from eab.adapters.tia2d import g1, g5, g5_seed
from eab.kernel2d.assembly import Assembly2, Body2
from eab.kernel2d.statics import limit_load_ideal_exact_2d
from tia2d_cases import build_case, export_cases, SCHEMA_APPROVAL
import tia2d_readback as reader
from tia2d_seed import geometry_seed


@pytest.mark.parametrize("mu", [Q(0), Q(1), Q(2)])
def test_independent_reader_replays_all_public_fields_and_mills_signs(mu):
    assembly = g5(mu=mu)
    problem = limit_load_ideal_exact_2d(assembly).problem
    plate = assembly.bodies[-1]
    pressure = -plate.dead[0]
    height = max(p[1] for b in assembly.bodies for p in b.vertices)
    jets = {
        "P": geometry_seed(assembly, "P", dead={plate.body_id: (-1, 0, height / 2 - plate.reference_point[1])}),
        "h": geometry_seed(assembly, "h", vertices={(b.body_id, i): (Q(0), Q(p[1]) / height)
             for b in assembly.bodies for i, p in enumerate(b.original_vertices)},
             dead={plate.body_id: (0, 0, pressure / 2)}, anchors={plate.body_id: (0, Q(1, 2))}),
    }
    extra = tuple(dict(seed=g5_seed(problem, parameter), problem=problem, geometry_seed=jets[parameter]) for parameter in ("P", "h"))
    case = build_case(assembly, "reader-test", include_critical=True, include_sensitivity=True, lock_bodies=(2,),
                 _sensitivity_queries=extra)
    result = reader.verify_case(case)
    assert result["status"] == "PASS" and result["queries"] == 8
    assert result["fields_compared"] > 1000
    assert result["lp_certificates"] >= 2
    assert result["mills_certificates"] == (0 if mu == 0 else 6)


def test_independent_reader_unbounded_and_unresolved_are_not_zero():
    result = reader.verify_case(build_case(g1(), "reader-test", include_critical=True, lock_bodies=(1, 2)))
    assert result["lp_certificates"] >= 2
    a = Body2.from_vertices("A", ((0, 0), (1, 0), (1, 1), (0, 1)))
    b = Body2.from_vertices("B", ((1, 1), (2, 1), (2, 2), (1, 2)),
                            boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    case = build_case(Assembly2((a, b), ((0, 1),), "complete"), "reader-test", include_critical=True)
    assert reader.verify_case(case)["lp_certificates"] == 0
    bad = deepcopy(case)
    next(q for q in bad["queries"] if q["kind"] == "limit")["result"]["exact_value"] = "0/1"
    with pytest.raises(ValueError, match="bool/null"):
        reader.verify_case(bad)


@pytest.mark.parametrize("damage", ["value", "ray", "anchor", "unreduced"])
def test_reader_rejects_corrupted_exact_values_not_merely_hashes(damage):
    case = build_case(g1() if damage == "ray" else g5(mu=Q(1, 4)), "reader-test")
    query = next(q for q in case["queries"] if q["kind"] == "limit")
    if damage == "value":
        query["result"]["exact_value"] = "1/1"
    elif damage == "ray":
        query["result"]["improving_ray"][-1] = "2/1"
    elif damage == "anchor":
        case["assembly"]["bodies"][-1]["dof_anchor"][1] = "0/1"
    else:
        query["problem"]["A"][0][0] = "0/2"
    with pytest.raises(ValueError, match="readback mismatch"):
        reader.verify_case(case)


@pytest.mark.parametrize("value", ["-0/1", "01/1", "2/2", "0/2", "1/-2", "1/0"])
def test_reader_rejects_noncanonical_rationals(value):
    with pytest.raises(ValueError):
        reader.read_fraction(value)


def test_reader_import_graph_does_not_consume_codec_encoders():
    tree = ast.parse(Path(reader.__file__).read_text(encoding="utf-8"))
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert not any(name and ("tia2d_cases" in name or "tia2d_export" in name) for name in imports)
    assert reader.read_double("8000000000000000").hex().startswith("-0x0")
    for bad in ("7ff0000000000000", "fff8000000000000", "3FF0000000000000"):
        with pytest.raises(ValueError):
            reader.read_double(bad)


def test_fresh_process_single_query_wallclock_is_verified_not_relabelled(tmp_path):
    case = build_case(g5(mu=Q(1, 4)), "reader-test", include_sensitivity=True)
    path = tmp_path / "case.json"
    path.write_text(json.dumps(case), encoding="utf-8", newline="\n")
    worker = Path(reader.__file__).with_name("tia2d_cold_query.py")
    result = subprocess.run([sys.executable, "-X", "utf8", str(worker), "--worker", str(path), "--query-index", "2"],
                            text=True, encoding="utf-8", capture_output=True, check=True)
    measured = json.loads(result.stdout)
    assert measured["verified"] is True and measured["query_index"] == 2
    assert measured["python_wallclock"]["cache_state"] == "cold"
    assert measured["python_wallclock"]["seconds"] > 0
    case["queries"][2]["result"]["exact_value"] = "19/1"
    path.write_text(json.dumps(case), encoding="utf-8", newline="\n")
    rejected = subprocess.run([sys.executable, "-X", "utf8", str(worker), "--worker", str(path), "--query-index", "2"],
                              text=True, encoding="utf-8", capture_output=True)
    assert rejected.returncode != 0 and "exact rational" in rejected.stderr


@pytest.mark.parametrize("damage", ["singular_slope", "scope", "cache", "repeat", "duplicate", "threshold_ref"])
def test_reader_envelope_mutations_fail_semantic_checks(damage):
    case = build_case(g5(mu=0), "reader-test", include_sensitivity=True)
    limit = next(q for q in case["queries"] if q["kind"] == "limit")
    if damage == "singular_slope":
        query = next(q for q in case["queries"] if q["kind"] == "sensitivity")
        query["directional_values"] = dict(D_plus="999/1", D_minus="999/1")
    elif damage in ("scope", "cache", "repeat"):
        key = dict(scope="scope", cache="cache_state", repeat="repeat_index")[damage]
        limit["python_wallclock"][key] = -8 if damage == "repeat" else "made_up"
    elif damage == "duplicate":
        case["queries"].append(deepcopy(limit))
    else:
        query = next(q for q in case["queries"] if q["kind"] == "sensitivity")
        query["threshold_query_ref"] = "critical"
    with pytest.raises(ValueError, match="readback mismatch"):
        reader.verify_case(case)


def test_independent_batch_reader_rejoins_parts_and_does_not_pin_current_source_hash(tmp_path):
    def save(path, value):
        # Fixture I/O only; no constructed geometry or numeric predicate.
        data = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        path.write_bytes(data)
        return dict(path=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    case = build_case(g5(mu=Q(1, 4)), "reader-test", include_sensitivity=True)
    derivative = next(q for q in case["queries"] if q["kind"] == "sensitivity")
    while len(json.dumps(case).encode()) < 1_800_000:
        case["queries"].append(deepcopy(derivative))
    target = tmp_path / "split"
    manifest = export_cases((case,), target, schema_approval=SCHEMA_APPROVAL, _output_root=tmp_path)
    assert len(manifest["cases"][0]["parts"]) > 1
    reconstructed = reader.load_batch(target)
    assert reconstructed[0]["queries"] == case["queries"]
    source_path = target / "source_manifest.json"
    source = reader.read_json(source_path)
    # Synthetic historical record: internally rebound, deliberately not the
    # current file SHA. The reader must not open/pin today's source paths.
    source["source_files"][0]["sha256"] = "0" * 64
    source["source_files_sha256"] = hashlib.sha256(json.dumps(source["source_files"], sort_keys=True).encode()).hexdigest()
    manifest["source_manifest"] = save(source_path, source)
    for entry in manifest["cases"][0]["parts"]:
        part_path = target / entry["path"]
        part = reader.read_json(part_path)
        part["provenance"] = dict(source_manifest_sha256=manifest["source_manifest"]["sha256"])
        entry.update(save(part_path, part))
    save(target / "manifest.json", manifest)
    assert reader.load_batch(target)[0]["queries"] == case["queries"]
    manifest["cases"][0]["parts"][-1]["query_indices"] = []
    save(target / "manifest.json", manifest)
    with pytest.raises(ValueError, match="fragment ordering"):
        reader.load_batch(target)


def test_independent_python_only_reader_preserves_nonbinary_rationals():
    from tia2d_export import _python_only, python_only_specs
    record = _python_only(python_only_specs()[1], 10)
    result = reader.verify_python_only(record)
    assert result["status"] == "PASS" and result["cpp_input"] is False
    assert result["fields_compared"] > 1000
    record["limit_problem"]["A"][0][0] = "123/100"
    with pytest.raises(ValueError, match="exact rational"):
        reader.verify_python_only(record)


@pytest.mark.parametrize("damage", ["display", "geometry", "concavity", "skeleton", "comparison"])
def test_v2_reader_rejects_semantic_contract_corruption(damage):
    case = build_case(g5(mu=Q(0)), "reader-v2", include_sensitivity=True)
    derivative = next(q for q in case["queries"] if q["kind"] == "sensitivity")
    if damage == "display":
        assert derivative["result"]["directional_derivative"] is None
        derivative["display_status"] = "EXACT"
    elif damage == "geometry":
        derivative["geometry_seed"]["mu"][0] = "2/1"
    elif damage == "concavity":
        case["input_audit"]["concave_vertices_after"][0]["ccw_indices"] = [0]
    elif damage == "skeleton":
        case["input_audit"]["expected_contact_pairs"] = []
    else:
        derivative["comparison_contract"]["rules"]["result.**.exact_x"] = "exact"
    with pytest.raises(ValueError, match="readback mismatch"):
        reader.verify_case(case)


def test_reader_strict_json_rejects_duplicate_keys_even_when_equal():
    with pytest.raises(ValueError, match="duplicate JSON key"):
        reader.parse_json_bytes(b'{"schema":"eab2.case.v1","schema":"eab2.case.v1"}')


def test_overlap_rejection_has_no_lock_display_value_and_roundtrips():
    from tia2d_export import registered_specs, build_registered_case
    spec = next(s for s in registered_specs() if s["case_id"] == "coverage_overlap")
    case = build_registered_case(spec)
    lock = next(q for q in case["queries"] if q["kind"] == "lock")
    assert lock["result"]["status"] is None and lock["display_status"] == "NOT_APPLICABLE"
    assert reader.verify_case(case)["status"] == "PASS"


def test_reader_does_not_feed_expected_tied_labels_back_as_inputs():
    case = build_case(g5(mu=Q(1)), "tied-output", include_sensitivity=True)
    query = next(q for q in case["queries"] if q["kind"] == "sensitivity")
    query["result"]["tied_labels"].append("unproved_fake_mode")
    with pytest.raises(ValueError, match="tied_labels"):
        reader.verify_case(case)


def test_reader_rebuilds_implicit_unit_mu_seed_not_only_geometry_parameter():
    from tia2d_export import registered_specs, build_registered_case
    case = build_registered_case(next(s for s in registered_specs() if s["case_id"] == "g1_slender"))
    query = next(q for q in case["queries"] if q.get("threshold_query_ref"))
    query["threshold_mu_seed"]["dA"] = [[str(q.numerator) + "/" + str(q.denominator)
        for q in (2 * Q(v) for v in row)] for row in query["threshold_mu_seed"]["dA"]]
    with pytest.raises(ValueError, match="geometry-derived LP seed"):
        reader.verify_case(case)


def test_comparison_contract_cannot_downgrade_mathematics_to_information():
    case = build_case(g5(), "comparison-policy")
    case["queries"][0]["comparison_contract"]["rules"]["result.**"] = "informational"
    with pytest.raises(ValueError, match="frozen comparison rule map"):
        reader.verify_case(case)


def test_no_finite_threshold_bracket_has_no_threshold_display_number():
    from tia2d_export import registered_specs, build_registered_case
    specs = [s for s in registered_specs() if s["case_id"] in ("coverage_farkas_free_dead", "g5_n3_mu0")]
    for spec in specs:
        case = build_registered_case(spec)
        query = next(q for q in case["queries"] if q["kind"] == "critical")
        assert query["result"]["mu_hi_bits"] is None
        assert query["display_status"] == "NOT_APPLICABLE"
        assert reader.verify_case(case)["status"] == "PASS"


def test_reader_rejects_unknown_case_top_level_field():
    case = build_case(g5(), "unknown-top-level")
    case["unexpected_public_field"] = "not approved"
    with pytest.raises(ValueError, match="case top-level fields"):
        reader.verify_case(case)


def test_reader_rejects_family_height_not_matching_assembly():
    from tia2d_export import registered_specs, build_registered_case
    spec = next(s for s in registered_specs() if s["case_id"] == "g5_n3_mu1")
    case = build_registered_case(spec)
    case["family_parameters"]["h"] = "999/1"
    with pytest.raises(ValueError, match="family h versus actual height"):
        reader.verify_case(case)


def test_reader_checks_all_114_registered_family_metadata_records_without_adapters():
    from tia2d_export import registered_specs, materialize, family_parameters
    from tia2d_cases import wire
    specs = registered_specs()
    assert len(specs) == 114
    for spec in specs:
        model, _ = materialize(spec)
        reader.verify_family_parameters(model, wire(family_parameters(spec, model)))


@pytest.mark.parametrize("case_id,key,replacement", [
    ("g1_slender", "t", "1/8"), ("g1_slender", "l", "3/1"),
    ("g1_slender", "orientation", "unreversed"),
    ("g5_n3_mu1", "N", "5/1"), ("g5_n3_mu1", "P", "2/1"),
    ("g5_n3_mu1", "widths", ["2/1", "2/1", "2/1"]),
    ("TIA-G2-A2-W1", "A", "1/4"), ("TIA-G3-A2-W1", "wavelength", "2/1"),
    ("TIA-G4-A2-W1", "A", "1/16"), ("coverage_separated", "h", "1/1"),
])
def test_family_metadata_uses_actual_shapes_and_loads_not_declared_defaults(case_id, key, replacement):
    from tia2d_export import registered_specs, materialize, family_parameters
    from tia2d_cases import wire
    spec = next(s for s in registered_specs() if s["case_id"] == case_id)
    model, _ = materialize(spec)
    metadata = wire(family_parameters(spec, model))
    metadata[key] = replacement
    with pytest.raises(ValueError, match="readback mismatch"):
        reader.verify_family_parameters(model, metadata)


def test_zero_slope_orientation_role_is_checked_against_exported_t_jet():
    from tia2d_export import registered_specs, build_registered_case
    spec = next(s for s in registered_specs() if s["case_id"] == "g1_koureas_h0_t0")
    case = build_registered_case(spec)
    # Geometry alone cannot distinguish these orientation labels at t=0;
    # the already declared t-direction input can, without guessing a default.
    case["family_parameters"]["orientation"] = "unreversed"
    with pytest.raises(ValueError, match="orientation versus t geometry jet"):
        reader.verify_case(case)
