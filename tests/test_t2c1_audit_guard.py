"""Finite-verifier disagreement is an orchestration error, not UNPROVED.

These explicit control-flow fixtures are NOT geometric oracle results. The
tested guard is removed inside a compiled audit_proposal copy to demonstrate
the semantic exception assertion fails; no output rows are fabricated after
the audit returns. Real numerical oracle tests stay in the unchanged suites.
"""
from fractions import Fraction as F
import inspect
import json

import pytest

from eab.kernel2d.se2_paths import SE2EscapeVerification, SE2Penetration2
from eab.kernel2d.translation_certificates import CertificateVerification
import t2c_escape_proposer as proposer


@pytest.fixture
def test_guard_inputs():
    moving = ((F(0), F(0)), (F(1), F(0)), (F(0), F(1)))
    obstacles = (((F(10), F(0)), (F(11), F(0)), (F(10), F(1))),)
    end = tuple((x, y+2) for x, y in moving)
    return dict(moving=moving, obstacles=obstacles), dict(moving=moving, obstacles=obstacles,
        pieces=[dict(start=moving, end=end, u1=F(0), translation=(F(0), F(2)), center=(F(0), F(0)))],
        ray_path=((F(0), F(0)), (F(0), F(100))))


@pytest.fixture
def test_control_records():
    free = SE2Penetration2(-1, "FREE", None, False, (), (), False, -1)
    penetration = SE2Penetration2(-1, "PENETRATES", None, False, (), (), False, -1)
    good_tail = CertificateVerification(True, "control-flow fixture", 1, 0, (), (F(0), F(1)))
    bad_tail = CertificateVerification(False, "control-flow rejected infinite tail")
    good = SE2EscapeVerification(True, "exact original path and certified infinite ray", 1, 1, ((free,),), good_tail)
    bad_finite = SE2EscapeVerification(False, "a rigid path segment enters strict overlap", 1, 1, ((penetration,),))
    bad_ray = SE2EscapeVerification(False, "infinite ray certificate rejected: control-flow fixture", 1, 1, ((free,),), bad_tail)
    bad_pose = SE2EscapeVerification(False, "consecutive poses are not exactly joined by the motion")
    independent_free = dict(valid=True, infinite_ray_verified=False, fixture="finite control-flow fixture")
    independent_bad = dict(valid=False, infinite_ray_verified=False, fixture="finite control-flow fixture")
    return {"production_accepts_independent_rejects": (good, independent_bad),
            "production_finite_rejects_independent_accepts": (bad_finite, independent_free),
            "ray_only": (bad_ray, independent_free), "pose_encoding": (bad_pose, independent_free),
            "both_reject": (bad_finite, independent_bad)}


@pytest.mark.parametrize("kind", ["production_accepts_independent_rejects", "production_finite_rejects_independent_accepts"])
def test_same_scope_disagreement_stops_and_preserves_both_results(monkeypatch, test_guard_inputs, test_control_records, kind):
    production, independent = test_control_records[kind]
    monkeypatch.setattr(proposer, "verify_se2_escape", lambda *args: production)
    monkeypatch.setattr(proposer, "validate_escape_segments", lambda *args: independent)
    with pytest.raises(RuntimeError, match="finite_verifier_disagreement") as caught:
        proposer.audit_proposal(*test_guard_inputs)
    record = json.loads(str(caught.value).split(": ", 1)[1])
    assert record["production"]["valid"] is production.valid
    assert record["production"]["reason"] == production.reason
    assert record["production"]["checked_pairs"] == production.checked_pairs
    assert record["independent"] == independent
    assert "proposal.json" in record["input_evidence"]


@pytest.mark.parametrize("kind", ["ray_only", "pose_encoding", "both_reject"])
def test_different_scope_or_common_rejection_remains_unproved(monkeypatch, test_guard_inputs, test_control_records, kind):
    production, independent = test_control_records[kind]
    monkeypatch.setattr(proposer, "verify_se2_escape", lambda *args: production)
    monkeypatch.setattr(proposer, "validate_escape_segments", lambda *args: independent)
    result = proposer.audit_proposal(*test_guard_inputs)
    assert result["status"] == "UNPROVED"
    assert result["finite_and_production_valid"] is False
    assert result["eligible_new_upper"] is False


@pytest.mark.parametrize("kind", ["production_accepts_independent_rejects", "production_finite_rejects_independent_accepts"])
def test_internal_guard_removal_fails_semantic_exception_assertion(monkeypatch, test_guard_inputs, test_control_records, kind):
    production, independent = test_control_records[kind]
    monkeypatch.setattr(proposer, "verify_se2_escape", lambda *args: production)
    monkeypatch.setattr(proposer, "validate_escape_segments", lambda *args: independent)
    source = inspect.getsource(proposer.audit_proposal)
    begin = source.index("    finite_disagreement = ")
    end = source.index('    valid = production.valid and independent["valid"]', begin)
    mutant = source[:begin] + source[end:]
    namespace = dict(vars(proposer))
    exec(compile(mutant, "<T2c1 internal finite-guard removal>", "exec"), namespace)
    # Failure must be the same assertion that protects stop-on-disagreement,
    # not a source hash mismatch, parse error or incidental ordering change.
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        with pytest.raises(RuntimeError, match="finite_verifier_disagreement"):
            namespace["audit_proposal"](*test_guard_inputs)
