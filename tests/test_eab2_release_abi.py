"""Release ABI gates without Git or a build prerequisite.

The PE oracle is a hand-built PE32+ byte image, independent of the reader.
Actual production DLL/ctypes checks remain mandatory CLI evidence.
"""
import ast
import copy
from pathlib import Path
import struct
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from eab2_release_abi import ReleaseHeader, canonical_c_field, differences, frozen_contract, header_contract, pe_exports
from eab2_tia_consumer import (PublicHeader, cases, compare_derived_seed, compare_threshold_labels,
                               compare_validity_conditions, DEFAULT_CASES)


def test_release_pe_reads_all_names_not_only_a_known_symbol_allowlist():
    # Integer offsets and bytes only: local protocol fixture setup, not a numeric oracle.
    names = ("eab2_one", "eab2_two")
    data = bytearray(1024)
    data[:2] = b"MZ"
    def u16(at, value):
        struct.pack_into("<H", data, at, value)
    def u32(at, value):
        struct.pack_into("<I", data, at, value)
    u32(60, 128)
    data[128:132] = b"PE\0\0"
    u16(132, 0x8664)
    u16(134, 1)
    u16(148, 240)
    u16(152, 0x20b)
    u32(260, 16)
    u32(264, 0x1000)
    u32(268, 256)
    u32(400, 512)
    u32(404, 0x1000)
    u32(408, 512)
    u32(412, 512)
    u32(528, 1)
    u32(532, len(names))
    u32(536, len(names))
    u32(540, 0x1028)
    u32(544, 0x1038)
    u32(548, 0x1048)
    cursor = 0x1060
    for i, name in enumerate(names):
        u32(552 + 4*i, 0x2000+16*i)
        u32(568 + 4*i, cursor)
        u16(584 + 2*i, i)
        encoded = name.encode("ascii") + b"\0"
        offset = 512+cursor-0x1000
        data[offset:offset+len(encoded)] = encoded
        cursor += len(encoded)
    assert [r["name"] for r in pe_exports(data)] == ["eab2_one", "eab2_two"]
    assert [r["ordinal"] for r in pe_exports(data)] == [1, 2]


@pytest.mark.parametrize("defect", ("unnamed", "forward", "duplicate", "ordinal", "rva", "machine", "truncated"))
def test_release_pe_rejects_nonconforming_export_tables(defect):
    # Integer offsets and bytes only: local protocol fixture setup, not a numeric oracle.
    names = ("eab2_one", "eab2_two")
    data = bytearray(1024)
    data[:2] = b"MZ"
    def u16(at, value):
        struct.pack_into("<H", data, at, value)
    def u32(at, value):
        struct.pack_into("<I", data, at, value)
    u32(60, 128)
    data[128:132] = b"PE\0\0"
    u16(132, 0x8664)
    u16(134, 1)
    u16(148, 240)
    u16(152, 0x20b)
    u32(260, 16)
    u32(264, 0x1000)
    u32(268, 256)
    u32(400, 512)
    u32(404, 0x1000)
    u32(408, 512)
    u32(412, 512)
    u32(528, 1)
    u32(532, len(names))
    u32(536, len(names))
    u32(540, 0x1028)
    u32(544, 0x1038)
    u32(548, 0x1048)
    cursor = 0x1060
    for i, name in enumerate(names):
        u32(552 + 4*i, 0x2000+16*i)
        u32(568 + 4*i, cursor)
        u16(584 + 2*i, i)
        encoded = name.encode("ascii") + b"\0"
        offset = 512+cursor-0x1000
        data[offset:offset+len(encoded)] = encoded
        cursor += len(encoded)
    raw = data
    if defect == "unnamed":
        struct.pack_into("<I", raw, 532, 3)
    elif defect == "forward":
        struct.pack_into("<I", raw, 552, 0x1020)
    elif defect == "duplicate":
        struct.pack_into("<I", raw, 572, struct.unpack_from("<I", raw, 568)[0])
    elif defect == "ordinal":
        struct.pack_into("<H", raw, 584, 2)
    elif defect == "rva":
        struct.pack_into("<I", raw, 568, 0xffffffff)
    elif defect == "machine":
        struct.pack_into("<H", raw, 132, 0x14c)
    else:
        raw = raw[:535]
    with pytest.raises((AssertionError, UnicodeError)):
        pe_exports(raw)


def test_release_frozen_contract_matches_public_header_and_all_struct_fields():
    actual = header_contract(PublicHeader(ROOT / "eab2/include/eab2/c_api.h"))
    frozen = frozen_contract(ROOT / "eab2/ABI_CONTRACT.md")
    assert not differences(frozen, actual, actual["exports"], actual["supported_capabilities"])
    assert len(actual["exports"]) == 31
    assert len(actual["structures"]) == 28
    assert len(actual["constants"]) == 64
    assert len(actual["return_types"]) == 31
    assert actual == header_contract(ReleaseHeader(ROOT / "eab2/include/eab2/c_api.h"))
    assert "release_acceptance" not in frozen


@pytest.mark.parametrize("defect", ("extra_export", "missing_export", "capability", "size", "offset", "signature", "version"))
def test_release_gate_rejects_contract_drift_not_just_missing_known_symbols(defect):
    actual = header_contract(PublicHeader(ROOT / "eab2/include/eab2/c_api.h"))
    frozen = copy.deepcopy(actual)
    exports, supported = actual["exports"][:], actual["supported_capabilities"]
    if defect == "extra_export":
        exports.append("eab2_numeric_batch")
    elif defect == "missing_export":
        exports.pop()
    elif defect == "capability":
        supported |= 2
    elif defect == "size":
        frozen["structures"]["eab2_sensitivity2_input"]["size"] += 8
    elif defect == "offset":
        frozen["structures"]["eab2_sensitivity2_input"]["fields"]["mu"] += 8
    elif defect == "signature":
        frozen["signatures"]["eab2_evaluate_sensitivity2"].pop()
    else:
        frozen["abi_version"] = 2
    assert differences(frozen, actual, exports, supported)


@pytest.mark.parametrize("declaration,expected", (
    ("const char* data", ("data", "const char*")),
    ("char const * data", ("data", "const char*")),
    ("const eab2_string * const * values", ("values", "const eab2_string* const*")),
    ("uint64_t data[2][3]", ("data", "uint64_t[2][3]")),
    ("uint64_t * items[3]", ("items", "uint64_t*[3]")),
))
def test_release_canonical_field_types_preserve_const_pointer_depth_and_array_shape(declaration, expected):
    assert canonical_c_field(declaration) == expected


@pytest.mark.parametrize("replacement", ("const uint32_t* data", "char* data", "const char** data"))
def test_release_gate_rejects_same_size_offset_field_type_drift(tmp_path, replacement):
    """Change the input declaration, not the validator's output table."""
    source = (ROOT / "eab2/include/eab2/c_api.h").read_text("utf-8")
    original = "typedef struct eab2_string { const char* data; uint64_t length; } eab2_string;"
    changed = "typedef struct eab2_string { " + replacement + "; uint64_t length; } eab2_string;"
    assert source.count(original) == 1
    altered = tmp_path / "altered_c_api.h"
    altered.write_text(source.replace(original, changed), encoding="utf-8")
    if "**" in replacement:
        # The strict transport parser rejects this outside its one-pointer
        # vocabulary before any runtime ABI call. The canonical type reader
        # nevertheless retains both levels, as the direct gate above proves.
        from eab2_release_abi import canonical_c_fields
        assert canonical_c_fields(source.replace(original, changed).encode())["eab2_string"]["data"] == "const char**"
        with pytest.raises(AssertionError, match="unsupported public declaration"):
            PublicHeader(altered)
        return
    frozen, actual = header_contract(PublicHeader(ROOT / "eab2/include/eab2/c_api.h")), header_contract(PublicHeader(altered))
    for name in frozen["structures"]:
        assert actual["structures"][name]["size"] == frozen["structures"][name]["size"]
        assert actual["structures"][name]["fields"] == frozen["structures"][name]["fields"]
    assert frozen["structures"]["eab2_string"]["field_types"]["data"] == "const char*"
    assert actual["structures"]["eab2_string"]["field_types"]["data"] == replacement.rsplit(" ", 1)[0]
    assert "header/frozen contract mismatch: structures" in differences(
        frozen, actual, actual["exports"], actual["supported_capabilities"])


def test_independent_consumer_imports_only_stdlib_not_python_referee_or_harness():
    source = (ROOT / "tools/eab2_tia_consumer.py").read_text("utf-8")
    tree = ast.parse(source)
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"__import__", "eval", "exec"}
    assert modules and all(name in sys.stdlib_module_names for name in modules)
    assert not any("sys.path" in ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Call))


def test_independent_consumer_default_covers_open_closed_singular_switch_and_both_modes():
    directory = ROOT / "fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64"
    rows = list(cases(directory, DEFAULT_CASES))
    assert len(rows) == 6
    assert sum(q["kind"] == "sensitivity" for _, _, _, qs in rows for q in qs) == 18
    classes = {q["result"]["differentiability"] for _, _, _, qs in rows for q in qs if q["kind"] == "sensitivity"}
    assert {"smooth", "one_sided", "singular", "unresolved"} <= classes


@pytest.mark.parametrize("reader", (PublicHeader, ReleaseHeader))
@pytest.mark.parametrize("defect", ("new_void", "new_missing_api", "changed_return", "missing_api", "duplicate", "status_width", "broken_prototype"))
def test_release_every_public_prototype_is_validated_not_silently_filtered(tmp_path, reader, defect):
    source = (ROOT / "eab2/include/eab2/c_api.h").read_text("utf-8")
    original = "EAB2_API eab2_call_status eab2_self_test(void);"
    changed = {
        "new_void": original + "\nEAB2_API void eab2_unfrozen(void);",
        "new_missing_api": original + "\neab2_call_status eab2_unfrozen(void);",
        "changed_return": "EAB2_API uint64_t eab2_self_test(void);",
        "missing_api": "eab2_call_status eab2_self_test(void);",
        "duplicate": original + "\n" + original,
        "broken_prototype": "EAB2_API eab2_call_status eab2_self_test(void;",
    }
    if defect == "status_width":
        source = source.replace("typedef uint32_t eab2_call_status;", "typedef uint64_t eab2_call_status;")
    else:
        assert source.count(original) == 1
        source = source.replace(original, changed[defect])
    path = tmp_path / "altered.h"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(AssertionError, match="prototype|call_status"):
        reader(path)


@pytest.mark.parametrize("reader", (PublicHeader, ReleaseHeader))
@pytest.mark.parametrize("defect", ("value", "width", "extra", "missing", "version", "unknown_expression", "duplicate"))
def test_release_all_integer_constants_are_frozen_including_status_and_flags(tmp_path, reader, defect):
    source = (ROOT / "eab2/include/eab2/c_api.h").read_text("utf-8")
    original = "#define EAB2_INVALID_INPUT UINT32_C(1)"
    replacement = {
        "value": "#define EAB2_INVALID_INPUT UINT32_C(99)",
        "width": "#define EAB2_INVALID_INPUT UINT64_C(1)",
        "extra": original + "\n#define EAB2_UNFROZEN_FLAG UINT32_C(128)",
        "missing": "",
        "unknown_expression": "#define EAB2_INVALID_INPUT (1 << 0)",
        "duplicate": original + "\n" + original,
    }
    if defect == "version":
        source = source.replace("#define EAB2_ABI_VERSION UINT32_C(1)", "#define EAB2_ABI_VERSION UINT32_C(2)")
    else:
        source = source.replace(original, replacement[defect])
    path = tmp_path / "altered.h"
    path.write_text(source, encoding="utf-8")
    if defect in {"unknown_expression", "duplicate"}:
        with pytest.raises(AssertionError, match="constant"):
            reader(path)
        return
    actual = header_contract(reader(path))
    errors = differences(frozen_contract(ROOT / "eab2/ABI_CONTRACT.md"), actual, actual["exports"], actual["supported_capabilities"])
    assert "header/frozen contract mismatch: constants" in errors
    if defect == "version":
        assert "header/frozen contract mismatch: abi_version" in errors


def test_release_return_types_are_a_frozen_comparison_dimension():
    actual = header_contract(ReleaseHeader(ROOT / "eab2/include/eab2/c_api.h"))
    altered = copy.deepcopy(actual)
    altered["return_types"]["eab2_self_test"] = "uint64_t"
    assert "header/frozen contract mismatch: return_types" in differences(altered, actual, actual["exports"], actual["supported_capabilities"])


def test_release_cli_isolated_outside_repository_without_consumer_import(tmp_path):
    (tmp_path / "eab2_tia_consumer.py").write_text("raise RuntimeError('untrusted module imported')\n", encoding="utf-8")
    source = (ROOT / "tools/eab2_release_abi.py").read_text("utf-8")
    tree = ast.parse(source)
    modules = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    modules += [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert all(module.split(".")[0] in sys.stdlib_module_names for module in modules)
    assert "eab2_tia_consumer" not in source
    run = subprocess.run([sys.executable, "-I", "-S", "-X", "utf8", str(ROOT / "tools/eab2_release_abi.py"), "--help"],
                         cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=False)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "--dll" in run.stdout


@pytest.mark.parametrize("actual_present,expected_present", ((False, False), (True, True), (False, True), (True, False)))
def test_consumer_derived_seed_presence_is_iff_not_optional(actual_present, expected_present):
    seed = dict(parameter="p", dA=[["1/2"]], db=["0/1"], dc=["0/1"])
    channel, query = {"derived_seed": seed if actual_present else None}, {"seed": seed if expected_present else None}
    if actual_present == expected_present:
        compare_derived_seed(channel, query, "case.propagation")
    else:
        with pytest.raises(AssertionError, match="presence mismatch"):
            compare_derived_seed(channel, query, "case.propagation")


@pytest.mark.parametrize("defect", ("missing_actual", "missing_expected", "dA"))
def test_consumer_derived_seed_missing_field_or_wrong_value_is_red(defect):
    seed = dict(parameter="p", dA=[["1/2"]], db=["0/1"], dc=["0/1"])
    channel, query = {"derived_seed": copy.deepcopy(seed)}, {"seed": seed}
    if defect == "missing_actual":
        channel.clear()
    elif defect == "missing_expected":
        query.clear()
    else:
        channel["derived_seed"]["dA"] = [["-1/2"]]
    with pytest.raises(AssertionError, match="missing derived seed|propagation.dA"):
        compare_derived_seed(channel, query, "case.propagation")


@pytest.mark.parametrize("bad", (b"\xff\xfeP\x00A\x00S\x00S\x00", b"\xef\xbb\xbfPASS\n", b"\x80\n", b"PASS\r\nFAIL\n"))
def test_build_audit_delivered_logs_reject_bom_bad_utf8_and_mixed_newlines(bad):
    from eab2_audit import encoding_findings
    assert encoding_findings("evidence.log", bad)
    assert not encoding_findings("evidence.log", "通过\n".encode("utf-8"))


def test_build_audit_checks_historical_forensics_log_and_excludes_ignored_tmp(tmp_path):
    from eab2_audit import delivered_logs, encoding_findings
    paths = delivered_logs(ROOT)
    expected = ROOT / "reports/codex/C3L4_evidence/tied_labels_forensics.log"
    assert expected in paths
    assert not encoding_findings(expected, expected.read_bytes())
    local = tmp_path / "reports/codex/C3L4_fix_evidence"
    (local / "tmp").mkdir(parents=True)
    (local / "tmp/ignored.log").write_bytes(b"\xff\xfe")
    (local / "delivered.log").write_bytes(b"PASS\n")
    assert delivered_logs(tmp_path) == [local / "delivered.log"]


@pytest.mark.parametrize("defect", (None, "extra_label", "missing_label", "slope", "missing_upper", "wrong_direction"))
def test_consumer_branch_labels_are_internal_consistency_not_frozen_basis_identity(defect):
    label = [["A", "B", ["0/1", "0/1"], "B", [2, 3]], -1]
    domain = {"exact_mu_min": "0/1", "exact_mu_max": "1/1"}
    component = dict(index=3, label=label, s="1/2", partial_mu="2/1", partial_parameter="-1/1")
    forward = dict(status="certified", s="1/2", lower={"witness": "internal only"},
                   upper=dict(point={}, ray={}), candidate_branches=[dict(components=[component])])
    reverse = dict(status="unresolved", s=None, candidate_branches=[])
    result = dict(right_derivative="1/2", left_derivative=None, tied_labels=[label],
                  branch_certificate=dict(version=1, order="epsilon_then_eta", search_domain=domain, forward=forward, reverse=reverse))
    if defect == "extra_label":
        result["tied_labels"].append("extra")
    elif defect == "missing_label":
        result["tied_labels"].clear()
    elif defect == "slope":
        component["partial_parameter"] = "1/1"
    elif defect == "missing_upper":
        forward["upper"] = None
    elif defect == "wrong_direction":
        result["right_derivative"] = "-1/2"
    if defect:
        with pytest.raises(AssertionError):
            compare_threshold_labels(result, dict(tied_labels=[]), dict(search_domain=domain))
    else:
        disposition = compare_threshold_labels(result, dict(tied_labels=[]), dict(search_domain=domain))
        assert disposition["actual"] == [label] and disposition["frozen"] == []
        assert "internal component consistency only" in disposition["policy"]


@pytest.mark.parametrize("defect", (None, "wrong_root", "wrong_slope", "not_monic", "constant", "negative_order", "noninteger_order"))
def test_consumer_singular_candidate_metadata_checks_monic_exact_root_not_partial_ratio(defect):
    label = ["singular", 3]
    domain = {"exact_mu_min": "0/1", "exact_mu_max": "1/1"}
    component = dict(index=3, label=label, s="1/2", leading_epsilon_order=2,
                     leading_polynomial=["1/4", "-1/1", "1/1"])
    forward = dict(status="certified", s="1/2", lower={}, upper=dict(point={}, ray={}),
                   candidate_branches=[dict(singular=True, components=[component])])
    result = dict(right_derivative="1/2", left_derivative=None, tied_labels=[label],
                  branch_certificate=dict(version=1, order="epsilon_then_eta", search_domain=domain,
                      forward=forward, reverse=dict(status="unresolved", s=None, candidate_branches=[])))
    if defect == "wrong_root":
        component["leading_polynomial"][0] = "1/3"
    elif defect == "wrong_slope":
        component["s"] = "1/3"
    elif defect == "not_monic":
        component["leading_polynomial"] = ["1/2", "-2/1", "2/1"]
    elif defect == "constant":
        component["leading_polynomial"] = ["1/1"]
    elif defect == "negative_order":
        component["leading_epsilon_order"] = -1
    elif defect == "noninteger_order":
        component["leading_epsilon_order"] = True
    if defect:
        with pytest.raises(AssertionError, match="singular candidate|branch crossing slope"):
            compare_threshold_labels(result, dict(tied_labels=[]), dict(search_domain=domain))
    else:
        assert compare_threshold_labels(result, dict(tied_labels=[]), dict(search_domain=domain))["actual"] == [label]


@pytest.mark.parametrize("defect", (None, "other_condition_removed", "other_method", "not_threshold"))
def test_consumer_versioned_condition_errata_only_removes_superseded_single_basis_assumptions(defect):
    old = ["L1接触骨架不变", "true_vv_excluded_from_statics", "临界证书基非奇异", "所列越零分量及方向保持有效"]
    actual = dict(method="branch_certificate", validity_conditions=old[:2])
    if defect == "other_condition_removed":
        actual["validity_conditions"].pop()
    elif defect == "other_method":
        actual["method"] = "stable_basis"
    if defect:
        with pytest.raises(AssertionError, match="validity_conditions"):
            compare_validity_conditions(actual, dict(validity_conditions=old), defect != "not_threshold")
    else:
        disposition = compare_validity_conditions(actual, dict(validity_conditions=old), True)
        assert disposition["version"] == "WO-C3L4-fix/20261023/branch-proof-v1"
        assert disposition["old"] == old and disposition["new"] == old[:2]
