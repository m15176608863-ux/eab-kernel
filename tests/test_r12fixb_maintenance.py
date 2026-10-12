"""R12FIXb local-review maintainability and failure-locality gates.

The mechanism fixture has explicitly synthetic reviews of forbidden dispatch;
it tests pin matching only and is not a production numerical exemption. The
repository-copy test exercises the real checked-in policy without refreshing it.
No eab geometry/construction primitive is used as an oracle.
"""
import ast
import importlib.util
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("r12fixb_maintenance_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def test_local_review_fixture(monkeypatch):
    """Hand-built two-function policy, never written into the actual manifest."""
    path = "src/eab/review_pin_probe.py"
    source = (
        "def reviewed_a(record):\n"
        "    return getattr(record, 'display_a')\n"
        "\n"
        "def reviewed_b(record):\n"
        "    return getattr(record, 'display_b')\n"
    )
    base_policy = gate._subset._policy()
    rows = gate._subset.closed_subset_issues(source, path, apply_waivers=False)
    assert {r[2] for r in rows} == {"reviewed_a", "reviewed_b"}
    waivers = [
        {"path": r[0], "function": r[2], "rule": r[3], "node": r[5], "context": r[6],
         "reason": "Synthetic display-label lookup fixture: tests local matching, not numerical safety."}
        for r in rows
    ]
    policy = {**base_policy, "waivers": waivers}
    policy.pop("dependencies", None)
    monkeypatch.setattr(gate._subset, "_policy", lambda: policy)
    assert gate._subset.closed_subset_issues(source, path) == []
    return path, source, waivers


def test_unrelated_source_comment_keeps_real_repository_gate_green(tmp_path):
    copy_root = tmp_path / "comment_repository_copy"
    for folder in ("src", "tests", "tools"):
        shutil.copytree(ROOT / folder, copy_root / folder)
    assert gate.scan_repository(copy_root) == [], "R12FIXb baseline must be green without policy regeneration"
    # Package metadata is unrelated to the numerical construction under review.
    unrelated = copy_root / "src/eab/__init__.py"
    before = unrelated.read_bytes()
    unrelated.write_bytes(before + b"\n# R12FIXb unrelated-source comment probe.\n")
    assert gate.scan_repository(copy_root) == [], "R12FIXb unrelated comment must not invalidate any review"


def test_same_file_other_function_edit_preserves_local_review(test_local_review_fixture):
    path, source, _ = test_local_review_fixture
    source += "\ndef unrelated_metadata():\n    return 'version 1'\n"
    before = gate._subset.approved_sites(source, path)
    changed = source.replace("'version 1'", "'version 2'")
    assert gate._subset.approved_sites(changed, path) == before
    assert gate._subset.closed_subset_issues(changed, path) == []


def test_reviewed_function_body_change_invalidates_only_its_sites(test_local_review_fixture):
    path, source, _ = test_local_review_fixture
    before = gate._subset.approved_sites(source, path)
    changed = source.replace("    return getattr(record, 'display_a')", "    # local review must be renewed\n    return getattr(record, 'display_a')")
    after = gate._subset.approved_sites(changed, path)
    assert after == {r for r in before if r[0] == "reviewed_b"}, "R12FIXb only the edited function's sites may expire"
    issues = gate._subset.closed_subset_issues(changed, path)
    assert issues and {row[2] for row in issues} == {"reviewed_a"}, "R12FIXb edited scope alone must turn red"


@pytest.mark.parametrize("change", ["safe_rewrite", "remove_function"])
def test_expired_review_is_explicit_even_without_an_unsupported_site(test_local_review_fixture, change):
    path, source, _ = test_local_review_fixture
    if change == "safe_rewrite":
        changed = source.replace("return getattr(record, 'display_a')", "return 'safe display'")
    else:
        changed = source[source.index("def reviewed_b"):]
    issues = gate._subset.closed_subset_issues(changed, path)
    assert any(row[2:4] == ("reviewed_a", "closed-stale-waiver") for row in issues), (
        "R12FIXb stale reviews require explicit cleanup even after a safe rewrite", change, issues)
    assert {row[2] for row in issues} == {"reviewed_a"}


def test_new_forbidden_function_is_not_admitted_by_existing_local_reviews(test_local_review_fixture):
    path, source, _ = test_local_review_fixture
    changed = source + "\ndef new_forbidden(record):\n    return getattr(record, 'display_c')\n"
    assert gate._subset.approved_sites(changed, path) == gate._subset.approved_sites(source, path)
    issues = gate._subset.closed_subset_issues(changed, path)
    assert issues and {row[2] for row in issues} == {"new_forbidden"}
    assert any(row[3] == "closed-dynamic-call" for row in issues)
    # Also exercise the full dataflow gate on an actual forbidden construction.
    implant = "\ndef new_bad(q):\n    return norm_rational(vector_rational(q))\n"
    full_issues = gate.scan_text(source + implant, path)
    assert any(row[2] == "new_bad" and row[3] == "rounded-vector" for row in full_issues)


def test_ast_fingerprint_is_required_even_with_a_matching_scope_hash(test_local_review_fixture, monkeypatch):
    path, source, waivers = test_local_review_fixture
    policy = gate._subset._policy()
    # Internally corrupt only the node fingerprint, retaining a valid context.
    corrupted = [{**r, "node": ast.dump(ast.Constant(value="not the reviewed site"), include_attributes=False)}
                 if r["function"] == "reviewed_a" else r for r in waivers]
    monkeypatch.setattr(gate._subset, "_policy", lambda: {**policy, "waivers": corrupted})
    issues = gate._subset.closed_subset_issues(source, path)
    assert issues and {r[2] for r in issues} == {"reviewed_a"}, "R12FIXb context alone cannot approve arbitrary AST sites"


def test_nested_scope_and_sibling_method_pins_are_independent():
    source = (
        "class Record:\n"
        "    label = 'old'\n"
        "    def first(self):\n"
        "        return 1\n"
        "    def second(self):\n"
        "        return 2\n"
        "def outer():\n"
        "    marker = 1\n"
        "    def inner():\n"
        "        return 3\n"
        "    return inner()\n"
    )
    before = gate._subset.site_contexts(source)
    changed_method = gate._subset.site_contexts(source.replace("return 1", "return 4"))
    assert {name for name in before if before[name] != changed_method[name]} == {"Record.first"}
    changed_outer = gate._subset.site_contexts(source.replace("marker = 1", "marker = 5"))
    assert {name for name in before if before[name] != changed_outer[name]} == {"outer"}


def test_function_source_comment_not_only_ast_is_pinned():
    source = "def reviewed():\n    # review note one\n    return 1\n"
    changed = source.replace("review note one", "review note two")
    assert ast.dump(ast.parse(source)) == ast.dump(ast.parse(changed))
    assert gate._subset.site_contexts(source)["reviewed"] != gate._subset.site_contexts(changed)["reviewed"]
    trailing = source + "    # still inside the reviewed source block\n"
    assert ast.dump(ast.parse(source)) == ast.dump(ast.parse(trailing))
    assert gate._subset.site_contexts(source)["reviewed"] != gate._subset.site_contexts(trailing)["reviewed"]
    assert gate._subset.site_contexts(source) == gate._subset.site_contexts(source.replace("\n", "\r\n"))
