"""Exercise both exact node-accounting declarations without adding suite nodes."""
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[4]
TMP = ROOT / "reports/codex/H1_evidence/tmp/fix_verification/node_delta_teeth"
TMP.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location("delta", ROOT / "tools/h1_node_delta.py")
delta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delta)
current = ROOT / "reports/codex/H1_evidence/tmp/fix_verification/current_collection.txt"
text = current.read_text("utf-8")
first = next(line for line in text.splitlines() if line.startswith("tests/"))
total = next(line for line in text.splitlines() if "tests collected in" in line)
cases = {
    "utf16_equivalent": (text, "utf-16", True),
    "unknown_same_count": (text.replace(first, "tests/test_unapproved.py::test_unknown", 1), "utf-8", False),
    "duplicate_node": (text.replace(first, first+"\n"+first, 1), "utf-8", False),
    "missing_summary": (text.replace(total, ""), "utf-8", False),
    "collection_error": (text+"\nERROR collecting tests/test_unapproved.py\n", "utf-8", False),
}
records = []
for basis, old in (
    ("pre-h1", ROOT / "reports/codex/H1_evidence/tmp/baseline_temp/collection.txt"),
    ("h1-v1", ROOT / "reports/codex/H1_evidence/tmp/fix_baseline/collection.txt"),
):
    for name, (source, encoding, complete) in cases.items():
        path = TMP / (basis+"_"+name+".txt")
        path.write_text(source, encoding=encoding, newline="")
        result = delta.account(old, path, basis)
        assert result["complete"] is complete, (basis, name, result["issues"])
        records.append(dict(basis=basis, case=name, expected_complete=complete,
                            observed_complete=result["complete"], issues=result["issues"]))
output = Path(__file__).with_suffix(".json")
output.write_text(json.dumps(dict(passed=len(records), records=records), indent=2)+"\n",
                  encoding="utf-8", newline="")
print("exact node-accounting self-checks:", len(records), "passed")
