"""Read-only policy audit; update H1-fix evidence, never admission policy."""
import ast
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import exact_construction_subset as subset


def blob(ref, path):
    return subprocess.check_output(["git", "show", ref + ":" + path], cwd=ROOT)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")


def executable(text):
    class Strip(ast.NodeTransformer):
        def generic_visit(self, node):
            node = super().generic_visit(node)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                    node.body.pop(0)
            return node
    return ast.dump(Strip().visit(ast.parse(text)), include_attributes=False)


def main():
    if (OUT / "context_update.json").exists():
        raise SystemExit("Historical addendum already finalized by root; use fix_policy_context.py to verify current state, do not overwrite it.")
    policy_path = ROOT / "tools/exact_construction_policy.json"
    policy_bytes = policy_path.read_bytes()
    policy = json.loads(policy_bytes)
    changed = ["src/eab/contact_record.py", "src/eab/adapters/tf.py", "src/eab/adapters/bdda2d.py",
               "src/eab/adapters/bdda3d.py", "src/eab/kernel2d/affine_motion.py", "src/eab/kernel2d/geom.py",
               "src/eab/kernel2d/model_robustness.py"]
    modules, pins = [], []
    for path in changed:
        old = blob("476c5d6", path).decode("utf-8")
        new = (ROOT / path).read_text("utf-8")
        assert executable(old) == executable(new), path
        before, after = subset.site_contexts(old), subset.site_contexts(new)
        modules.append({"path": path, "executable_ast_equal": True, "source_before_sha256": hashlib.sha256(old.encode()).hexdigest(),
                        "source_after_sha256": hashlib.sha256(new.encode()).hexdigest(),
                        "changed_source_contexts": [k for k in before if before[k] != after[k]]})
        for index, row in enumerate(policy["waivers"]):
            fn = row["function"]
            if row["path"] == path and before[fn] != after[fn]:
                nodes = {ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(new))}
                assert row["node"] in nodes
                pins.append({"id": row["id"], "path": path, "function": fn, "pointer": ["waivers", index, "context"],
                             "old": before[fn], "new": after[fn], "same_executable_ast": True, "same_ast_site": True})
    assert [r["id"] for r in pins] == ["R12b-L0008"]
    dump(OUT / "comment_context_proof.json", {"baseline": "476c5d6", "modules": modules,
        "context_updates_required": pins, "policy_modified_by_this_script": False})

    original_csv = ROOT / "reports/codex/H1_evidence/policy_rekey.csv"
    original_json = ROOT / "reports/codex/H1_evidence/policy_rekey.json"
    for path in (original_csv, original_json):
        saved = OUT / (path.stem + "_v1" + path.suffix)
        if not saved.exists():
            saved.write_bytes(blob("476c5d6", path.relative_to(ROOT).as_posix()))
    old_rows = list(csv.DictReader(io.StringIO((OUT / "policy_rekey_v1.csv").read_text("utf-8"))))
    rows = [dict(row, status="relocated", row_kind="waiver", binding="", source_diff="", evidence="policy_rekey_v1.json") for row in old_rows]
    names = {"BDDA_MODE", "BDDA_COVER", "BDDA3D_MODE", "BDDA3D_COVER", "TF_MODE", "TF_COVER"}
    stale = []
    current_contract = ast.parse((ROOT / "src/eab/contact_record.py").read_text("utf-8"))
    current_names = {n.id for n in ast.walk(current_contract) if isinstance(n, ast.Name)}
    assert not names & current_names
    for group in ("imports", "members"):
        for key in policy[group]:
            if (":contact_record:" in key or "contact_record:" in key or key.startswith("eab:")) and key.split(":")[-1].split(".")[0] in names:
                row = {"group": group, "key": key, "status": "retired", "retained_in_frozen_policy": True,
                       "reason": "Binding was moved out of contact_record/eab; this historical spelling has no current source binding."}
                stale.append(row)
                rows.append(dict(id=f"RETIRED-{group}-{sum(r['group'] == group for r in stale):02d}", old_path="src/eab/contact_record.py",
                                 new_path="", function="", same_ast_site="", same_function_source="", context_change="none; frozen policy bytes retained",
                                 status="retired", row_kind=group, binding=key, source_diff="", evidence="fix_purity/stale_admissions.json"))
    assert len(stale) == 19 and sum(r["group"] == "imports" for r in stale) == 13
    dump(OUT / "stale_admissions.json", {"imports": 13, "members": 6, "rows": stale,
        "policy_sha256": hashlib.sha256(policy_bytes).hexdigest(), "policy_counts": {k: len(policy[k]) for k in ("imports", "members", "waivers", "renewals")}})

    old = blob("1ce9a91", "tests/test_int1_semantics.py").decode("utf-8")
    new = blob("476c5d6", "tests/test_int1_semantics.py").decode("utf-8")
    old_line = "from eab.kernel2d import affine_motion as affine"
    new_line = "from eab.adapters import bdda2d_affine as affine"
    assert old.replace(old_line, new_line) == new
    before, after = subset.site_contexts(old), subset.site_contexts(new)
    assert before["inject_semantic_mutation"] == after["inject_semantic_mutation"]
    details = {"path": "tests/test_int1_semantics.py", "function": "inject_semantic_mutation", "source_change_count": 1,
               "old_source_line": old_line, "new_source_line": new_line, "function_source_unchanged": True,
               "old_module_context": before["<module>"], "new_module_context": after["<module>"],
               "old_module_source_sha256": hashlib.sha256(old.encode()).hexdigest(),
               "new_module_source_sha256": hashlib.sha256(new.encode()).hexdigest(),
               "scope_note": "One module import-only re-pin represented in the three historical instrumentation review occurrences; not a new admission."}
    dump(OUT / "instrumentation_scope_repin.json", details)
    rows.append(dict(id="SCAFFOLD-test_int1_semantics", old_path="tests/test_int1_semantics.py", new_path="tests/test_int1_semantics.py",
                     function="inject_semantic_mutation", same_ast_site=True, same_function_source=True, context_change="module-import-only",
                     status="relocated", row_kind="instrumentation-scope", binding="three historical review occurrences",
                     source_diff=old_line + " -> " + new_line, evidence="fix_purity/instrumentation_scope_repin.json"))
    with original_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    evidence = json.loads((OUT / "policy_rekey_v1.json").read_text("utf-8"))
    evidence["h1_fix_addendum"] = {"historical_proof_scope": "Original mechanical relocation at 476c5d6; original CSV/JSON preserved in fix_purity/*_v1.*",
        "retired_import_keys": 13, "retired_member_keys": 6, "instrumentation_scope_source_edits": 1,
        "csv_waiver_rows": len(old_rows), "csv_retirement_rows": len(stale), "csv_instrumentation_rows": 1,
        "csv_total_rows": len(rows), "current_docstring_context_proof": "fix_purity/comment_context_proof.json"}
    dump(original_json, evidence)
    assert policy_path.read_bytes() == policy_bytes
    print(json.dumps({"comment_only_modules": len(modules), "context_updates_required": pins,
                      "csv_rows": len(rows), "stale_keys": len(stale)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
