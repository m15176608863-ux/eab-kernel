"""Re-run the actual regression assertion against four internally mutated tools."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

tests_path = ROOT / "tests/test_r13fix_static_lifecycle.py"
regression = module_at("r13_regression_assertion", tests_path)
function = next(n for n in ast.parse(tests_path.read_text(encoding="utf-8")).body
                if isinstance(n, ast.FunctionDef) and n.name == "test_internal_lifecycle_mutation_loses_the_target_diagnostic")
replacements = ast.literal_eval(function.body[0].value)
hashes = {name: hashlib.sha256((ROOT / "tools" / name).read_bytes()).hexdigest()
          for name in ("check_exact_construction.py", "exact_construction_flow.py", "exact_construction_subset.py", "exact_construction_policy.json")}
results = []
for case, (before, after) in replacements.items():
    destination = HERE / "mutants" / case / "tools"
    destination.mkdir(parents=True, exist_ok=True)
    for name in hashes:
        source = (ROOT / "tools" / name).read_text(encoding="utf-8")
        if name == "exact_construction_flow.py":
            assert source.count(before) == 1
            source = source.replace(before, after)
        (destination / name).write_text(source, encoding="utf-8")
    regression.gate = module_at("r13_mutated_gate", destination / "check_exact_construction.py")
    # Resolve production construction imports against this repository, while
    # the checker implementation itself comes exclusively from the mutant.
    original_scan = regression.gate.scan_text
    regression.gate.scan_text = lambda source, path: original_scan(source, path, repository_root=ROOT)
    try:
        regression.test_lifecycle_rounding_reaches_construction_diagnostic(case)
    except AssertionError as exc:
        failure = traceback.format_exc()
        assert "closed-rounded-construction" in failure
        results.append({"case": case, "status": "TARGET_ASSERTION_RED", "removed": before,
                        "replacement": after, "assertion": "any(row[3] == 'closed-rounded-construction' for row in issues)",
                        "exception": str(exc), "traceback": failure})
        print(case, "TARGET_ASSERTION_RED", str(exc))
    else:
        raise AssertionError((case, "mutant unexpectedly passed the regression"))
assert all(hashlib.sha256((ROOT / "tools" / name).read_bytes()).hexdigest() == digest for name, digest in hashes.items())
(HERE / "lifecycle_mutations.json").write_text(json.dumps({"results": results, "source_hashes_unchanged": hashes}, ensure_ascii=False, indent=2), encoding="utf-8")
print("4 internal mutants: 4 target assertions red; original tool/policy bytes unchanged")
