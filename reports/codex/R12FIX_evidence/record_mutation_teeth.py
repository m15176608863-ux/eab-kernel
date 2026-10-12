"""Record the actual failing assertion after internal rollback of admission."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("r12_teeth", ROOT / "tests/test_r12fix_static_closed.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
scanner = ROOT / "tools/check_exact_construction.py"
text = scanner.read_text(encoding="utf-8")
replacements = {"closed_subset_issues(text, path)": "[]",
                'self.issue(node, "closed-unproved-call")': "pass",
                'self.issue(node, "closed-rounded-call")': "pass"}
for old, new in replacements.items():
    assert text.count(old) == 1
    text = text.replace(old, new)
namespace = {"__file__": str(scanner), "__name__": "r12_mutation_evidence"}
exec(compile(text, "<R12 actual admission rollback>", "exec"), namespace)
path = "src/eab/kernel3d/covers3.py"
source = (ROOT / path).read_text(encoding="utf-8")
rows = []
for label, body in t.CONE_MUTANTS:
    mutant = source.replace("return norm_rational(p), noise", body)
    line = next(i for i, value in enumerate(mutant.splitlines(), 1) if value.strip() == body.splitlines()[0].strip())
    normal = t.gate.scan_text(mutant, path)
    targeted = [r for r in normal if r[1] == line and r[2] == "cone_intersection_margin" and r[3].startswith("closed-")]
    assert targeted
    rolled_back = namespace["scan_text"](mutant, path)
    try:
        t._assert_closed_rejection(namespace["scan_text"], mutant, path, "cone_intersection_margin", line)
    except AssertionError as exc:
        message = str(exc)
        assert "G6L-01 closed-subset rejection assertion" in message
    else:
        raise AssertionError("Admission rollback did not trip its own assertion")
    rows.append({"case": label, "defect_inside": "real cone_intersection_margin",
                 "rollback_inside": "scanner admission layers; old provenance analysis retained",
                 "intact_gate_targeted_issues": targeted, "rollback_issue_count": len(rolled_back),
                 "failed_assertion": message, "status": "EXPECTED_ASSERTION_FAILURE"})
(HERE / "mutation_teeth.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps({"cases": len(rows), "all_target_assertions_failed_on_internal_rollback": True}))
