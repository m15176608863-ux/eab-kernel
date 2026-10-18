"""Fail-closed module-execution coverage and declarative-module smoke helper."""
import ast
import importlib
from pathlib import Path


DECLARATIVE_MODULES = (
    "eab", "eab.adapters", "eab.readers", "eab.kernel2d", "eab.kernel3d",
    "eab.adapters.bdda3d", "eab.adapters.tf",
)


def module_inventory(root):
    """Return every source module, classified by the presence of an actual def."""
    root = Path(root).resolve()
    result = {"function_modules": [], "declarative_modules": []}
    for path in sorted((root / "src" / "eab").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        key = "function_modules" if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                                       for node in ast.walk(tree)) else "declarative_modules"
        result[key].append(path.relative_to(root).as_posix())
    if not any(result.values()):
        raise ValueError("no src/eab source modules found")
    return result


def reload_declarative_modules():
    """Execute seven data/package modules during a test and check their exports."""
    modules = {name: importlib.reload(importlib.import_module(name)) for name in DECLARATIVE_MODULES}
    for name in DECLARATIVE_MODULES[:5]:
        assert modules[name].__path__, name
    expected = {"ContactRecord", "CoverType", "Feature", "Mode", "validate", "records_to_json", "records_from_json"}
    assert set(modules["eab"].__all__) == expected
    assert all(getattr(modules["eab"], name, None) is not None for name in expected)
    from eab.contact_record import CoverType, Mode
    assert modules["eab.adapters.bdda3d"].BDDA3D_MODE == {
        0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.BONDED}
    assert modules["eab.adapters.bdda3d"].BDDA3D_COVER == {"np": CoverType.VF, "ee": CoverType.EE}
    assert modules["eab.adapters.tf"].TF_MODE == {
        0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.TENSION,
        4: Mode.UNVERIFIED, 5: Mode.UNVERIFIED, 6: Mode.UNVERIFIED}
    assert modules["eab.adapters.tf"].TF_COVER == {0: CoverType.NN, 1: CoverType.NE, 2: CoverType.VF, 3: CoverType.EE}
    return tuple(modules)


def audit_module_coverage(root, records):
    """Audit shard journals; complete requires imports AND actual test execution.

    ``root`` is the exact source snapshot that produced ``records``. A function
    witness cannot substitute for module code in a declarative-only module, or
    vice versa. Collection imports and witnesses of failed/unrun tests do not
    count. The caller must include ``result['complete']`` in its GREEN decision.
    """
    root = Path(root).resolve()
    inventory = module_inventory(root)
    expected = set(inventory["function_modules"] + inventory["declarative_modules"])
    imports, functions, module_code, errors = set(), {}, {}, []
    if not records:
        errors.append("no execution journals")
    for index, record in enumerate(records):
        if not record.get("complete") or record.get("exitstatus") != 0:
            errors.append(f"journal {index}: session did not complete successfully")
        if record.get("coverage_available") is not True:
            errors.append(f"journal {index}: Python monitoring unavailable")
        if Path(record.get("source_root", "")).resolve() != root / "src" / "eab":
            errors.append(f"journal {index}: source root mismatch")
        passed = {item["nodeid"] for item in record.get("reports", [])
                  if item.get("when") == "call" and item.get("outcome") == "passed"}
        imports.update(set(record.get("imported", [])) & expected)
        for key, result, is_module in (("executed_modules", functions, False),
                                        ("executed_module_code", module_code, True)):
            for path, witness in record.get(key, {}).items():
                if path not in expected:
                    errors.append(f"journal {index}: unknown source witness {path}")
                    continue
                if witness.get("nodeid") not in passed or witness.get("nodeid", "").startswith("<"):
                    errors.append(f"journal {index}: witness outside a passed test: {path}")
                    continue
                name = witness.get("function", "")
                if not name or (is_module and name != "<module>") or (not is_module and name.startswith("<")):
                    errors.append(f"journal {index}: invalid execution kind: {path}")
                    continue
                result.setdefault(path, witness)
    missing_functions = sorted(set(inventory["function_modules"]) - functions.keys())
    missing_modules = sorted(set(inventory["declarative_modules"]) - module_code.keys())
    missing_imports = sorted(expected - imports)
    return dict(complete=not (missing_functions or missing_modules or missing_imports or errors),
                **inventory, missing_function_calls=missing_functions,
                missing_module_execution=missing_modules, missing_imports=missing_imports,
                errors=errors, function_witnesses=functions, module_witnesses=module_code,
                module_count=len(expected), imported_count=len(imports),
                function_covered_count=len(set(inventory["function_modules"]) & functions.keys()),
                declarative_covered_count=len(set(inventory["declarative_modules"]) & module_code.keys()))
