"""Append-only admission history: literal accepted-state fingerprints.

Oracle imports: json and hashlib, not the checker or numerical implementation.
The source anchor is accepted df4f6f1 (M3, INT1-C, old shared review, renewals),
plus the explicitly reviewed M5b shared successor. Hash checks here are the
history contract itself, never evidence that a numerical mutant was killed.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

HISTORY = (
    ("M3", 39, "4353be0c206120394f0ff82f967a7b5f67ac6fe0ee923735a289609817b39b01"),
    ("INT1-C", 23, "54dcf27d48c7d4723d1c11d69198cce503734599dd8321cd5fdd71e00b23fed4"),
    ("waivers", 3452, "5b6a77f47b392d8c3f110ba9cb5ed343b0508d75dce8c05849563181b8547bf2"),
    ("renewals", 92, "a7855600150e24324ee28647a72d473f1ea38354ea3376551df508108bd677e7"),
    ("mutation_instrumentation_reviews", 1, "9695d46a1a6af3af8dd9dff33634f9b7aa2d42b0071386b20ae4127761733650"),
    ("mutation_instrumentation_reviews", 2, "a8e5b80d4d395de140382609a78c5a83f243c968709c13bd335538838974c466"),
)


@pytest.mark.parametrize("group,count,fingerprint", HISTORY)
def test_m3_int1c_renewal_and_shared_records_are_append_only(group, count, fingerprint):
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    if group == "M3":
        rows = [r for r in policy["waivers"] if r["id"].startswith("M3b-")]
    elif group == "INT1-C":
        rows = [r for r in policy["waivers"] if r["id"].startswith("INT1-C")]
    else:
        rows = policy[group]

    def assert_preserved(candidate):
        actual = hashlib.sha256(json.dumps(candidate[:count], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        assert len(candidate) >= count and actual == fingerprint, "M5b accepted admission history is immutable and append-only"

    assert_preserved(rows)
    assert_preserved(rows + [{"append_only_probe": True}])
    # These are data-contract defects, not source-body/numerical mutations.
    deleted = copy.deepcopy(rows)
    deleted.pop(0)
    rewritten = copy.deepcopy(rows)
    rewritten[0]["reason"] = "silently rewritten history"
    for bad in (deleted, rewritten, [{"inserted_at_front": True}] + rows):
        with pytest.raises(AssertionError, match="M5b accepted admission history"):
            assert_preserved(bad)


def test_original_int1_shared_review_is_immutable_not_rewritten_by_its_successor():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    old = policy["mutation_instrumentation_review"]
    fingerprint = hashlib.sha256(json.dumps(old, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert fingerprint == "5ff343c439a8321479c68d4470220042ea9996f50683ad29a689089dfbca109a"
    assert policy["mutation_instrumentation_reviews"][0]["supersedes_sha256"] == fingerprint


def test_rule_site_audit_counts_identical_same_line_ast_occurrences_separately():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import m5b_audit_admissions as audit

    source = "def caller(a=Factory(), b=Factory()):\n    return a, b\n"
    row = ("tests/probe.py", 1, "<module>", "closed-unproved-call", "Factory()")
    sites = audit.diagnostic_occurrences(source, row)
    assert len(sites) == 2 and len({site["column"] for site in sites}) == 2, \
        "M5b per-site count must not collapse identical same-line AST occurrences into one admission row"


def test_current_effective_shared_review_has_its_own_accepted_fingerprint(policy=None):
    if policy is None:
        policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    active = policy["mutation_instrumentation_reviews"][-1]
    actual = hashlib.sha256(json.dumps(active, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert actual == "cb2f1e7fe51137a61fcf9126f756af55fce22875beac487cedc27ec5e7b78cdc", \
        "M5c effective shared review must itself be explicitly accepted; append-only history is insufficient"


def test_appending_a_wider_review_does_not_inherit_the_effective_fingerprint():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    active = policy["mutation_instrumentation_reviews"][-1]
    bad = copy.deepcopy(active)
    bad["rules"].append("closed-rounded-construction")
    candidate = policy["mutation_instrumentation_reviews"] + [bad]
    # Old prefix remains exact: this specifically defeats the former loophole.
    assert candidate[:-1] == policy["mutation_instrumentation_reviews"]
    policy["mutation_instrumentation_reviews"] = candidate
    with pytest.raises(AssertionError, match="effective shared review must itself be explicitly accepted"):
        test_current_effective_shared_review_has_its_own_accepted_fingerprint(policy)
