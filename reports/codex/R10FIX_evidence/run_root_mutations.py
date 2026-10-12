"""Restore individual pre-fix function bodies in memory and run target assertions."""
from pathlib import Path
import ast
import os
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

if len(sys.argv) > 1:
    import pytest
    import eab.kernel2d.covers as C
    import eab.limit as L
    import eab.limit_multi as M
    key = sys.argv[1]
    if key == "J03":
        module, name, source_path = C, "in_cone", "src/eab/kernel2d/covers.py"
        targets = ["tests/test_r10_cone_contract.py::test_public_micro_reflex_cone_rejects_opposite_hemisphere"]
    else:
        module, name, source_path = L, "_wrench_rounding", "src/eab/limit.py"
        targets = ["tests/test_r10_resolution.py::test_unbounded_capacity_reports_finite_analytic_uncertainty_bounds"]
    source = (HERE / "baseline" / source_path).read_text(encoding="utf-8")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = dict(vars(module))
    exec(compile(ast.get_source_segment(source, node), f"<R10-{key}-baseline-body>", "exec"), namespace)
    setattr(module, name, namespace[name])
    if key == "J05":
        M._wrench_rounding = namespace[name]
    sys.exit(pytest.main(["-q", *targets, f"--basetemp={HERE}/tmp/root_mutation_{key}"]))
else:
    rows = []
    for key in ("J03", "J05"):
        result = subprocess.run([sys.executable, "-X", "utf8", __file__, key], cwd=ROOT,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = HERE / f"{key}_mutation_red.log"
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        target = "opposite thin sector is exterior" if key == "J03" else "assert (4 *"
        rows.append({"id": key, "returncode": result.returncode,
                     "target_assertion_seen": target in result.stdout, "log": log.name})
    (HERE / "root_mutations.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))
    sys.exit(not all(r["returncode"] == 1 and r["target_assertion_seen"] for r in rows))
