"""Frozen gzip corpus: strict decode/SHA plus fixed exact production replay.

Historical source bytes are intentionally NOT compared with current source.
The independent reader imports no codec and additionally verifies Fraction
certificate equations. Replay is serialization QA, not a second solver.
"""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from tia2d_readback import load_batch, verify_case, parse_json_bytes

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_gzip_sha_strict_parse_and_fixed_exact_replays():
    batches = list((ROOT / "fixtures/eab2_cases/tia2d-2").glob("*/binary64"))
    assert len(batches) == 1, "exactly one approved corpus batch, no old/new duplication"
    batch = batches[0]
    index = json.loads((batch / "gzip_index.json").read_text(encoding="utf-8"))
    assert (index["compresslevel"], index["mtime"]) == (9, 0)
    for entry in index["files"]:
        packed = (batch / entry["gz_path"]).read_bytes()
        assert len(packed) == entry["gz_bytes"] < 1_000_000
        assert hashlib.sha256(packed).hexdigest() == entry["gz_sha256"]
        assert packed[4:8] == bytes(4)
        raw = gzip.decompress(packed)
        assert len(raw) == entry["bytes"] <= 1_000_000
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
        assert parse_json_bytes(raw)["schema_revision"] == "tia2d-2"
    frozen_cases = {case["case_id"]: case for case in load_batch(batch)}
    for name in ("regression_a_saw", "regression_b_bare_vv", "regression_c_redundant_vv",
        "regression_d_flush_mu0", "regression_d_flush_mu025", "regression_e_mixed_vv_edge",
        "regression_f_convex_in_notch", "g5_n3_mu2", "g1_slender"):
        result = verify_case(frozen_cases[name])
        assert result["status"] == "PASS" and result["queries"] >= 4
        assert result["fields_compared"] > 100

    # Coverage states are facts about the frozen approved batch, never source
    # hashes. The fixed examples above also replay nonunique certificates.
    def result(name, kind):
        return next(q for q in frozen_cases["coverage_" + name]["queries"] if q["kind"] == kind)
    infeasible = result("farkas_free_dead", "limit")["result"]
    assert infeasible["mathematical_status"] == "INFEASIBLE" and infeasible["farkas"] is not None
    assert result("separated", "lock")["mathematical_status"] == "NOT_CONTACT"
    assert result("overlap", "assembly")["mathematical_status"] == "OVERLAP"
    assert result("unsupported_h", "critical")["call_status"] == "UNSUPPORTED"
    assert result("resolution_bracket", "critical")["result"]["bisection_termination"] == "input_resolution_limit"
    assert result("redundant_vv_mu2", "critical")["result"]["reason"] == "bounded_on_domain"
    assert "true_vv_excluded_from_statics" in result("redundant_vv_mu2", "limit")["result"]["validity_conditions"]
