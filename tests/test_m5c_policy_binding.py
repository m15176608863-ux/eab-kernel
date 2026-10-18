"""M5c review-domain boundaries; historical source pins retired by H1.

Independent oracle imports: stdlib copy/pathlib and literal
accepted review domains. No numerical geometry primitive is an oracle here.
Policy mutants alter the production guard before evaluation; fingerprints are
not called by those semantic drivers. The retired source-byte tests are replaced by fixed real-data semantic
subsets listed in docs/frozen_evidence.md.
"""
import copy
from pathlib import Path
import sys

import pytest
from mutation_support import mutated_function

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_exact_construction as gate


@pytest.mark.parametrize("widening", ("numerical_rule", "production_path", "ordinary_test", "parent_traversal"))
def test_appended_broader_review_is_rejected_before_any_site_can_be_waived(monkeypatch, widening):
    subset = gate._subset
    policy = copy.deepcopy(subset._policy())
    path, function = "tests/test_int1_semantics.py", "inject_semantic_mutation"
    source = (ROOT / path).read_text(encoding="utf-8")
    assert subset.instrumentation_scope(source, path, function, "closed-dynamic-call")
    widened = copy.deepcopy(policy["mutation_instrumentation_reviews"][-1])
    if widening == "numerical_rule":
        widened["rules"].append("closed-rounded-construction")
    else:
        alien = copy.deepcopy(widened["scopes"][0])
        alien["path"] = {"production_path": "src/eab/construction.py",
                         "ordinary_test": "tests/test_unreviewed_numerical_oracle.py",
                         "parent_traversal": "tests/../src/eab/construction.py"}[widening]
        widened["scopes"].append(alien)
    policy["mutation_instrumentation_reviews"].append(widened)
    monkeypatch.setattr(subset, "_policy", lambda: policy)
    # No source-hash or accepted-review fingerprint check occurs here. Even an
    # unchanged, valid old scope must lose authorization under a broader review.
    assert not subset.instrumentation_scope(source, path, function, "closed-dynamic-call"), \
        "M5c an appended broader review must not discharge any diagnostic"


@pytest.mark.parametrize("widening,before,after", (
    ("numerical_rule", 'set(review.get("rules", ())) <= MUTATION_RULES', "True"),
    ("production_path", 'all(row.get("path") in MUTATION_PATHS\n                    for row in review.get("scopes", ()))', "True"),
    ("ordinary_test", 'all(row.get("path") in MUTATION_PATHS\n                    for row in review.get("scopes", ()))', "True"),
    ("parent_traversal", 'all(row.get("path") in MUTATION_PATHS\n                    for row in review.get("scopes", ()))', "True"),
))
def test_internal_review_domain_mutants_die_at_the_broader_review_assertion(monkeypatch, widening, before, after):
    subset = gate._subset
    changed = mutated_function(subset.mutation_review_domain_is_bounded, subset, ((before, after),))
    monkeypatch.setattr(subset, "mutation_review_domain_is_bounded", changed)
    with pytest.raises(AssertionError, match="appended broader review must not discharge"):
        test_appended_broader_review_is_rejected_before_any_site_can_be_waived(monkeypatch, widening)

