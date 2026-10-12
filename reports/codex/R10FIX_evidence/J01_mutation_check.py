"""Re-run target regression against an in-memory keyword-step rollback."""
from pathlib import Path
import sys
import types

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
baseline = "--baseline" in sys.argv
source_path = (ROOT / "reports/codex/R10FIX_evidence/baseline/tools/check_exact_construction.py"
               if baseline else ROOT / "tools/check_exact_construction.py")
source = source_path.read_text(encoding="utf-8")
step = "return [*node.args, *(item.value for item in node.keywords)]"
if not baseline:
    assert source.count(step) == 1
    source = source.replace(step, "return node.args")
namespace = {"__file__": str(source_path), "__name__": "j01_keyword_rollback"}
exec(compile(source, "<J01 baseline gate>" if baseline else "<J01 gate keyword rollback>", "exec"), namespace)


class RollbackPlugin:
    def pytest_collection_modifyitems(self, items):
        for item in items:
            item.module.gate = types.SimpleNamespace(scan_text=namespace["scan_text"])


if __name__ == "__main__":
    targets = (["tests/test_r10_static_construction.py::test_j01_all_seven_review_syntaxes_are_rejected",
                "tests/test_r10_static_construction.py::test_j01_seven_mutations_inside_real_cone_path_are_rejected"]
               if baseline else ["tests/test_r10_static_construction.py::test_j01_seven_mutations_inside_real_cone_path_are_rejected[norm_keyword]"])
    raise SystemExit(pytest.main([
        "-q", *targets,
        "--basetemp=reports/codex/R10FIX_evidence/tmp/j01_baseline" if baseline else "--basetemp=reports/codex/R10FIX_evidence/tmp/j01_keyword_rollback",
    ], plugins=[RollbackPlugin()]))
