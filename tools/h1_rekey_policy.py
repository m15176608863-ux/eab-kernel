"""Mechanical H1 namespace relocation; never creates a static admission.

Every row retains its id/rule/AST site. Function source pins must be identical.
Only two module (not function) contexts and import-only mutation scaffolding
pins need rebinding: their non-import, non-relocated-definition AST is checked.
This is a migration proof, not an automatic source-hash refresh utility.
"""
import argparse
import ast
import copy
import csv
import hashlib
import json
from pathlib import Path

import exact_construction_subset as subset
from h1_verify_relocation import verify_relocation
from policy_history_view import allowed_pointer, historical_view

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    "src/eab/kernel3d/interlock.py": "src/eab/adapters/tia3d.py",
    "src/eab/kernel2d/dda_motion.py": "src/eab/adapters/bdda2d_motion.py",
    "src/eab/readers/numeric_decode.py": "src/eab/numeric_decode.py",
}
MAPPINGS = {"BDDA_MODE", "BDDA_COVER", "BDDA3D_MODE", "BDDA3D_COVER", "TF_MODE", "TF_COVER"}
IMPORT_BINDINGS = {
    "from .readers.numeric_decode import scalar as scalar_rational": "from .numeric_decode import scalar as scalar_rational",
    "from .readers.numeric_decode import decode_tree, integer, loads as loads_exact": "from .numeric_decode import decode_tree, integer, loads as loads_exact",
    "from eab.kernel2d import affine_motion as affine": "from eab.adapters import bdda2d_affine as affine",
    "import gzip": "import frozen_gzip as gzip",
}


def verify_import_bindings(old_text, new_text, path):
    def imports(text):
        return [ast.unparse(n) for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.Import, ast.ImportFrom))]
    expected = []
    for spelling in imports(old_text):
        if path == "src/eab/kernel2d/dda_motion.py" and spelling.startswith("from .") and not spelling.startswith("from .."):
            spelling = spelling.replace("from .", "from ..kernel2d.", 1)
        elif path == "tests/test_m5a2_replay.py":
            spelling = IMPORT_BINDINGS.get(spelling, spelling)
        else:
            # The gzip reader remap is limited to its explicitly named fixture reader.
            spelling = IMPORT_BINDINGS.get(spelling, spelling) if spelling != "import gzip" else spelling
        expected.append(spelling)
    assert expected == imports(new_text), (path, "unrecognized import rebinding or import-order change")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def relocated(path, function):
    if path == "src/eab/kernel2d/affine_motion.py" and function.split(".")[0] == "DDAAffineMotion":
        return "src/eab/adapters/bdda2d_affine.py"
    if path == "src/eab/kernel2d/model_robustness.py" and function == "dda_paths":
        return "src/eab/adapters/bdda2d_motion.py"
    return MODULES.get(path, path)


def stripped_module(text, *, definitions=False, maps=False):
    """Compare the immutable non-import content, not a convenient new hash."""
    tree = ast.parse(text)
    class Strip(ast.NodeTransformer):
        def visit_Import(self, node):
            return None
        def visit_ImportFrom(self, node):
            return None
    tree = Strip().visit(tree)
    body = []
    for node in tree.body:
        if definitions and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if maps and any(isinstance(t, ast.Name) and t.id in MAPPINGS for t in targets):
            continue
        body.append(node)
    tree.body = body
    return ast.dump(tree, include_attributes=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/codex/H1_evidence")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    baseline = args.baseline.resolve()
    old = json.loads((baseline / "tools/exact_construction_policy.json").read_text("utf-8"))
    new = copy.deepcopy(old)
    definition_proof = verify_relocation(ROOT, baseline)
    # The only deleted module statements are domain tables copied unchanged.
    original_tables = {n.target.id: ast.dump(n, include_attributes=False)
                       for n in ast.parse((baseline / "src/eab/contact_record.py").read_text("utf-8")).body
                       if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id in MAPPINGS}
    relocated_tables = {}
    for name in ("bdda2d", "bdda3d", "tf"):
        for node in ast.parse((ROOT / f"src/eab/adapters/{name}.py").read_text("utf-8")).body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in MAPPINGS:
                relocated_tables[node.target.id] = ast.dump(node, include_attributes=False)
    assert original_tables == relocated_tables and len(original_tables) == 6
    cache = {}
    nodes_cache = {}
    def source(root, name):
        key = (str(root), name)
        if key not in cache:
            text = (root / name).read_text("utf-8-sig")
            cache[key] = text, subset.site_contexts(text)
        return cache[key]
    def nodes(root, name, text):
        key = (str(root), name)
        if key not in nodes_cache:
            nodes_cache[key] = {ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(text))}
        return nodes_cache[key]
    rows = []
    old_by_id = {r["id"]: r for r in old["waivers"]}
    for row in new["waivers"]:
        before = old_by_id[row["id"]]
        path, function = before["path"], before["function"]
        target = relocated(path, function)
        old_text, old_context = source(baseline, path)
        new_text, new_context = source(ROOT, target)
        assert function in old_context and function in new_context, (path, function)
        same_function = old_context[function] == new_context[function]
        if not same_function:
            assert function == "<module>" and path in {"src/eab/contact_record.py", "src/eab/kernel2d/dda_motion.py"}, (path, function)
            assert stripped_module(old_text, definitions=True, maps=True) == stripped_module(new_text, definitions=True, maps=True), (path, "non-import module semantics changed")
            verify_import_bindings(old_text, new_text, path)
            # No retired historical review is silently activated.
            if before["context"] == old_context[function]:
                row["context"] = new_context[function]
        row["path"] = target
        old_nodes = nodes(baseline, path, old_text)
        new_nodes = nodes(ROOT, target, new_text)
        assert (row["node"] in old_nodes) == (row["node"] in new_nodes), (path, function, row["node"])
        assert row["node"] == before["node"] and row["rule"] == before["rule"]
        if row != before:
            rows.append(dict(id=row["id"], old_path=path, new_path=target, function=function,
                             same_ast_site=True, same_function_source=same_function,
                             context_change="module-import-and-constant-relocation-only" if not same_function else "none"))
    new_by_id = {r["id"]: r for r in new["waivers"]}
    for renewal in new.get("renewals", ()):
        old_row = old_by_id[renewal["old_id"]]
        new_row = new_by_id[renewal["old_id"]]
        if old_row != new_row:
            assert renewal["old_row_sha256"] == sha(json.dumps(old_row, sort_keys=True, ensure_ascii=False))
            renewal["old_row_sha256"] = sha(json.dumps(new_row, sort_keys=True, ensure_ascii=False))
    # Module spelling remaps preserve list cardinality, not additional grants.
    import_rekeys = {}
    relocated_import_spellings = {
        "..readers.numeric_decode:integer": "..numeric_decode:integer",
        ".readers.numeric_decode:decode_tree": "..numeric_decode:decode_tree",
        ".readers.numeric_decode:loads": "..numeric_decode:loads",
        ".readers.numeric_decode:scalar": "..numeric_decode:scalar",
        ".frozen:frozen_lift": "..kernel3d.frozen:frozen_lift",
    }
    for key in new["imports"]:
        target = key.replace("eab.kernel3d.interlock", "eab.adapters.tia3d").replace("eab.kernel3d:interlock", "eab.adapters:tia3d")
        target = relocated_import_spellings.get(target, target)
        if target != key:
            import_rekeys[key] = target
    new["imports"] = [import_rekeys.get(k, k) for k in new["imports"]]
    member_rekeys = {key: key.replace("eab.kernel3d.interlock", "eab.adapters.tia3d").replace("eab.kernel3d:interlock", "eab.adapters:tia3d")
                     for key in new["members"] if "eab.kernel3d.interlock" in key or "eab.kernel3d:interlock" in key}
    new["members"] = [member_rekeys.get(k, k) for k in new["members"]]
    assert len(set(new["imports"])) == len(set(old["imports"]))
    assert len(set(new["members"])) == len(set(old["members"]))
    scaffolds = []
    reviews = [new.get("mutation_instrumentation_review", {})] + new.get("mutation_instrumentation_reviews", [])
    for review in reviews:
        for scope in review.get("scopes", ()):
            path = scope["path"]
            old_text, old_context = source(baseline, path)
            new_text, new_context = source(ROOT, path)
            if old_text == new_text:
                continue
            if scope["function"] not in old_context:
                assert scope["function"] not in new_context, (path, "historical scope unexpectedly revived")
                continue  # Obsolete historical scaffolding records remain inactive and byte-identical.
            assert stripped_module(old_text) == stripped_module(new_text), (path, "scaffolding changed beyond imports")
            verify_import_bindings(old_text, new_text, path)
            assert old_context[scope["function"]] == new_context[scope["function"]], (path, scope["function"])
            if scope.get("module_context") == old_context["<module>"]:
                scope["module_context"] = new_context["<module>"]
            if scope.get("module_source_sha256") == sha(old_text):
                scope["module_source_sha256"] = sha(new_text)
            scaffolds.append(dict(path=path, function=scope["function"], function_source_unchanged=True, import_only=True))
    assert len(new["waivers"]) == len(old["waivers"]) == len(new_by_id)
    verify_import_bindings((baseline / "tests/test_m5a2_replay.py").read_text("utf-8"),
                           (ROOT / "tests/test_m5a2_replay.py").read_text("utf-8"), "tests/test_m5a2_replay.py")
    for key in ("imports", "members", "waivers", "renewals", "mutation_instrumentation_reviews"):
        assert len(old[key]) == len(new[key]), key
    changes = []
    def compare(left, right, pointer=()):
        if left == right:
            return
        if isinstance(left, dict) and isinstance(right, dict):
            assert left.keys() == right.keys(), pointer
            for key in left:
                compare(left[key], right[key], (*pointer, key))
        elif isinstance(left, list) and isinstance(right, list):
            assert len(left) == len(right), pointer
            for index, (a, b) in enumerate(zip(left, right)):
                compare(a, b, (*pointer, index))
        else:
            assert allowed_pointer(pointer), pointer
            changes.append(dict(pointer=pointer, old=left, new=right))
    compare(old, new)
    relocation = dict(schema="eab.h1-policy-relocation.v1", baseline_commit="1ce9a91760e22cab7e471e76c39dcc2b786eb6ab",
                      proof="tools/h1_rekey_policy.py: same AST sites and function sources; no new grants",
                      changes=changes)
    assert historical_view(new, relocation) == old, "mechanical projection must recover the entire accepted policy"
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "policy_rekey.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["id"])
        writer.writeheader()
        writer.writerows(rows)
    evidence = dict(complete=True, baseline=str(baseline), old_count=len(old["waivers"]), new_count=len(new["waivers"]),
                    changed_rows=len(rows), unchanged_rows=len(old["waivers"])-len(rows), same_ast_sites=True,
                    same_function_sources=True, module_context_exceptions=[r for r in rows if not r["same_function_source"]],
                    import_rekeys=import_rekeys, member_rekeys=member_rekeys, scaffolding_import_rekeys=scaffolds,
                    historical_projection_fields=len(changes),
                    historical_projection_file="tools/exact_construction_relocations.json",
                    production_definition_proof=definition_proof,
                    counts={k:len(new[k]) for k in ("imports", "members", "waivers", "renewals", "mutation_instrumentation_reviews")})
    (args.output / "policy_rekey.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if args.apply:
        (ROOT / "tools/exact_construction_policy.json").write_text(json.dumps(new, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        (ROOT / "tools/exact_construction_relocations.json").write_text(json.dumps(relocation, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False))


if __name__ == "__main__":
    main()
