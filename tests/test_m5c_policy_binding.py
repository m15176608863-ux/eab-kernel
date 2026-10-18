"""M5c review domains and the retained within-run source-closure guard.

Independent oracle imports: stdlib copy/pathlib and literal
accepted review domains. No numerical geometry primitive is an oracle here.
Policy mutants alter the production guard before evaluation; fingerprints are
not called by those semantic drivers. Historical source-byte pins remain
retired. Fresh snapshots below exercise the live guard itself, never geometry.
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


def test_new_runtime_import_after_start_invalidates_the_sealed_closure(tmp_path):
    target = tmp_path / "tools/example.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"value = 1\n")
    expected = {"tools/example.py": hashlib.sha256(target.read_bytes()).hexdigest()}
    binding.assert_run_sources_unchanged(tmp_path, expected, expected)
    observed = dict(expected, **{"tools/late_import.py": "0"*64})
    with pytest.raises(ValueError, match="runtime source closure changed"):
        binding.assert_run_sources_unchanged(tmp_path, expected, observed)


def test_source_binding_rejects_parent_traversal_even_with_matching_content(tmp_path):
    target = tmp_path / "tools/example.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"value = 1\n")
    bad = {"tools/../tools/example.py": hashlib.sha256(target.read_bytes()).hexdigest()}
    with pytest.raises(ValueError, match="invalid runtime source path"):
        binding.assert_run_sources_unchanged(tmp_path, bad, bad)


@pytest.mark.parametrize("replay_name", ("m5b_endpoint_replay", "m5b_robust_replay"))
@pytest.mark.parametrize("omit_dependency", (False, True))
def test_runtime_source_closure_matches_independent_import_origins_and_kills_omission(replay_name, omit_dependency):
    # Independent import-spec enumeration, not the production __file__ scan.
    # Every node first checks the unmodified path; the omission nodes then
    # exercise an internal scanner defect through the retained live guard.
    code = r'''import hashlib, importlib, inspect, json, sys
from pathlib import Path
sys.path.insert(0, "tools")
replay = importlib.import_module(sys.argv[1])
import m5c_source_binding as binding
actual = replay.source_hashes()
root = Path.cwd().resolve()
expected = {}
for name in tuple(sys.modules):
    spec = getattr(sys.modules[name], "__spec__", None)
    origin = getattr(spec, "origin", None)
    if not origin or not origin.endswith(".py"):
        continue
    path = Path(origin).resolve()
    if not path.is_relative_to(root):
        continue
    relative = path.relative_to(root).as_posix()
    if relative.startswith(("src/eab/", "tools/")):
        expected[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
assert "src/eab/numeric_domain.py" in expected
assert len(expected) > 4, "M5c closure must exceed the old four direct dependencies"
assert set(actual) == set(expected), "M5c independent import origins require every transitive source, including numeric_domain"
binding.assert_run_sources_unchanged(root, expected, actual)
if sys.argv[2] == "omit":
    source = inspect.getsource(binding.runtime_source_hashes)
    old = "for path in sorted(paths)}"
    assert source.count(old) == 1
    changed = source.replace(old, "for path in sorted(paths) if path.name != 'numeric_domain.py'}")
    namespace = dict(vars(binding))
    exec(compile(changed, "<internal closure omission>", "exec"), namespace)
    observed = namespace["runtime_source_hashes"](root, replay.__file__)
    try:
        binding.assert_run_sources_unchanged(root, expected, observed)
    except ValueError as exc:
        assert "runtime source closure changed" in str(exc)
    else:
        raise AssertionError("M5c live guard must reject the internal numeric_domain omission")
print(json.dumps(sorted(expected)))
'''
    result = subprocess.run([sys.executable, "-c", code, replay_name,
                             "omit" if omit_dependency else "normal"], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert result.returncode == 0, result.stderr
    assert len(json.loads(result.stdout)) > 4

