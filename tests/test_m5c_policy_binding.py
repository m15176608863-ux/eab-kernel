"""M5c review boundaries and complete runtime source binding.

Independent oracle imports: stdlib hashlib/json/pathlib/subprocess and literal
accepted review domains. No numerical geometry primitive is an oracle here.
Policy mutants alter the production guard before evaluation; fingerprints are
not called by those semantic drivers. Source-byte tests deliberately exercise
binding itself, not numerical correctness, and mutate only scratch copies.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
from mutation_support import mutated_function

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_exact_construction as gate
import m5c_source_binding as binding


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


@pytest.mark.parametrize("replay_name,summary_name", (
    ("m5b_endpoint_replay", "endpoint_summary.json"),
    ("m5b_robust_replay", "robust_summary.json"),
))
def test_frozen_summaries_bind_every_runtime_transitive_source_at_both_ends(replay_name, summary_name):
    summary = json.loads((ROOT / "reports/codex/M5b_evidence" / summary_name).read_text(encoding="utf-8"))
    # A fresh interpreter is essential: pytest loads many unrelated modules.
    code = ("import sys,json; sys.path.insert(0,'tools'); import " + replay_name
            + " as replay; print(json.dumps(replay.source_hashes(),sort_keys=True))")
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", check=True)
    actual = json.loads(proc.stdout)
    assert summary["complete"] and summary["source_binding"] == "runtime-loaded-repository-closure-start-and-end.v1"
    assert summary["source_hashes"] == actual, "M5c every actual transitive runtime dependency must be frozen at current bytes"
    assert summary["source_hashes_end"] == actual, "M5c source closure must be rechecked at end, not only at start"
    for name, digest in summary["source_hashes"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    binding.assert_current_sources(ROOT, summary["source_hashes"], summary["source_hashes_end"])
    if summary_name == "robust_summary.json":
        for case in summary["cases"].values():
            assert case["source_hashes"] == case["source_hashes_end"] == actual


@pytest.mark.parametrize("replay_name", ("m5b_endpoint_replay", "m5b_robust_replay"))
def test_changing_any_transitive_source_file_in_a_scratch_copy_is_rejected(tmp_path, replay_name):
    code = ("import sys,json; sys.path.insert(0,'tools'); import " + replay_name
            + " as replay; print(json.dumps(replay.source_hashes(),sort_keys=True))")
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", check=True)
    expected = json.loads(proc.stdout)
    assert len(expected) > 4, "M5c closure may not regress to the old four direct dependencies"
    for name in expected:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    binding.assert_current_sources(tmp_path, expected, expected)
    checked = set()
    for name in expected:
        target = tmp_path / name
        original = target.read_bytes()
        target.write_bytes(original + b"\n# M5c transitive dependency mutation\n")
        with pytest.raises(ValueError, match="runtime source bytes changed"):
            binding.assert_current_sources(tmp_path, expected, expected)
        target.write_bytes(original)
        checked.add(name)
    assert checked == set(expected), "M5c every file, not a selected pair, must receive the rejection probe"


def test_new_runtime_import_after_start_invalidates_the_sealed_closure(tmp_path):
    target = tmp_path / "tools/example.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"value = 1\n")
    expected = {"tools/example.py": hashlib.sha256(target.read_bytes()).hexdigest()}
    binding.assert_current_sources(tmp_path, expected, expected)
    observed = dict(expected, **{"tools/late_import.py": "0"*64})
    with pytest.raises(ValueError, match="runtime source closure changed"):
        binding.assert_current_sources(tmp_path, expected, observed)


def test_source_binding_rejects_parent_traversal_even_with_matching_content(tmp_path):
    target = tmp_path / "tools/example.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"value = 1\n")
    bad = {"tools/../tools/example.py": hashlib.sha256(target.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match="invalid runtime source path"):
        binding.assert_current_sources(tmp_path, bad)


@pytest.mark.parametrize("replay_name", ("m5b_endpoint_replay", "m5b_robust_replay"))
@pytest.mark.parametrize("omit_dependency", (False, True))
def test_runtime_source_closure_matches_independent_import_origins_and_kills_omission(replay_name, omit_dependency):
    # Independent enumeration uses import specs, not the production __file__
    # scanner or its expected hash map. A true internal dict-comprehension
    # mutant drops an existing transitive dependency before any output exists.
    code = r'''import importlib, inspect, json, sys
from pathlib import Path
sys.path.insert(0, "tools")
replay = importlib.import_module(sys.argv[1])
import m5c_source_binding as binding
if sys.argv[2] == "omit":
    source = inspect.getsource(binding.runtime_source_hashes)
    old = "for path in sorted(paths)}"
    assert source.count(old) == 1
    changed = source.replace(old, "for path in sorted(paths) if path.name != 'numeric_domain.py'}")
    namespace = dict(vars(binding))
    exec(compile(changed, "<internal closure omission>", "exec"), namespace)
    binding.runtime_source_hashes = namespace["runtime_source_hashes"]
    if hasattr(replay, "runtime_source_hashes"):
        replay.runtime_source_hashes = binding.runtime_source_hashes
actual = replay.source_hashes()
root = Path.cwd().resolve()
expected = set()
for name in tuple(sys.modules):
    spec = getattr(sys.modules[name], "__spec__", None)
    origin = getattr(spec, "origin", None)
    if not origin or not origin.endswith(".py"):
        continue
    path = Path(origin).resolve()
    if not path.is_relative_to(root):
        continue
    relative = path.relative_to(root).as_posix()
    if relative.startswith("src/eab/") or relative.startswith("tools/"):
        expected.add(relative)
assert "src/eab/numeric_domain.py" in expected
assert set(actual) == expected, "M5c independent import origins require every transitive source, including numeric_domain"
print(json.dumps(sorted(expected)))
'''
    result = subprocess.run([sys.executable, "-c", code, replay_name,
                             "omit" if omit_dependency else "normal"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if omit_dependency:
        assert result.returncode != 0
        assert "AssertionError: M5c independent import origins require every transitive source" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert len(json.loads(result.stdout)) > 4
