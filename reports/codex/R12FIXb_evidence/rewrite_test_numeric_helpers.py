"""One-shot, narrowly scoped R12FIXb helper simplification; no policy changes."""
import ast
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
MAPS = {"F", "Fraction", "scalar_exact", "_fv", "exact_oracle.qpoint", "E.vector"}
LAMBDA_SCOPES = {
    ("test_frozen_ee_sign.py", "_ridge_pair"),
    ("test_frozen_ee_sign.py", "_wedge_pair"),
    ("test_geom3_merge.py", "_pocketed_slab"),
    ("test_interlocking.py", "_scaled_pair"),
    ("test_kernel2d_predicates.py", "_grid_truth"),
    ("test_lp_certificates.py", "_block"),
    ("test_lp_certificates.py", "_lock_case"),
    ("test_lp_certificates.py", "_si_case"),
    ("test_lp_certificates.py", "_exact_limit_lp"),
    ("test_lp_certificates.py", "_floor"),
    ("test_margin_resolution.py", "_small_pair"),
    ("test_r9fix_cover_parameters.py", "_assert_parameters"),
}
evidence = []
for path in sorted((ROOT / "tests").glob("test_*.py")):
    if path.name.startswith("test_perf_"):
        continue
    original = path.read_bytes()
    bom = original.startswith(b"\xef\xbb\xbf")
    source = original.decode("utf-8-sig")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    offsets, total = [], 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    newline = "\r\n" if "\r\n" in source else "\n"
    edits = []

    def pos(line, col):
        # Python AST columns are UTF-8 byte offsets, not Unicode characters.
        return offsets[line-1] + len(lines[line-1].encode("utf-8")[:col].decode("utf-8"))

    def walk(node, names=()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names += (node.name,)
        if any(name.startswith("test_") for name in names):
            return
        replacement = None
        kind = None
        if names and isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "map" and len(node.args) == 2 and not node.keywords and ast.unparse(node.args[0]) in MAPS:
            function = ast.get_source_segment(source, node.args[0])
            iterable = ast.get_source_segment(source, node.args[1])
            assert "_r12_item" not in source
            replacement = f"({function}(_r12_item) for _r12_item in {iterable})"
            kind = "known_numeric_map_to_generator"
        if (path.name, ".".join(names)) in LAMBDA_SCOPES and isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Lambda):
            args = ast.unparse(node.value.args)
            body = ast.get_source_segment(source, node.value.body)
            indent = " " * node.col_offset
            replacement = f"def {node.targets[0].id}({args}):{newline}{indent}    return {body}"
            kind = "numeric_lambda_to_direct_local_def"
        if replacement is not None:
            start, stop = pos(node.lineno, node.col_offset), pos(node.end_lineno, node.end_col_offset)
            edits.append((start, stop, replacement, {"function": ".".join(names), "line_before": node.lineno,
                                                    "kind": kind, "before": source[start:stop], "after": replacement}))
            return
        for child in ast.iter_child_nodes(node):
            walk(child, names)

    walk(tree)
    if not edits:
        continue
    updated = source
    for start, stop, replacement, _ in sorted(edits, reverse=True):
        updated = updated[:start] + replacement + updated[stop:]
    parsed = ast.parse(updated)
    before_tests = [(n.name, ast.dump(n.args, include_attributes=False)) for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    after_tests = [(n.name, ast.dump(n.args, include_attributes=False)) for n in ast.walk(parsed)
                   if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert before_tests == after_tests
    backup = BASE / "test_helper_rewrite_backup" / path.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    assert not backup.exists(), "Do not overwrite the rollback anchor"
    backup.write_bytes(original)
    result = (b"\xef\xbb\xbf" if bom else b"") + updated.encode("utf-8")
    path.write_bytes(result)
    evidence.append({"path": path.relative_to(ROOT).as_posix(), "backup": backup.relative_to(ROOT).as_posix(),
                     "sha256_before": hashlib.sha256(original).hexdigest(), "sha256_after": hashlib.sha256(result).hexdigest(),
                     "edits": [e[3] for e in edits], "test_signatures_unchanged": True})
if evidence:
    (BASE / "test_helper_rewrite_changes.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(evidence), "edits": sum(len(e["edits"]) for e in evidence),
                  "paths": [e["path"] for e in evidence]}, ensure_ascii=False, indent=2))
