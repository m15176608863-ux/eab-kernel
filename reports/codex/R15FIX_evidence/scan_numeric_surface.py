"""Candidate inventory, not a static proof; run from any cwd."""
import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
rows, files = [], []
for folder in ["src", "tools"]:
    for p in sorted((ROOT / folder).rglob("*.py")):
        s = p.read_text(encoding="utf-8-sig")
        t = ast.parse(s)
        files.append(p.relative_to(ROOT).as_posix())
        parents = {c: n for n in ast.walk(t) for c in ast.iter_child_nodes(n)}
        for n in ast.walk(t):
            tags = []
            if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None and any(
                isinstance(v, ast.Constant) and type(v.value) is float and v.value == 0
                for v in ast.walk(n.value)
            ):
                tags.append("float-zero-initializer")
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in [
                "float", "sum", "scalar_rational", "vector_rational", "_fl", "sqrt_rational", "norm_rational"
            ]:
                tags.append("sum-or-display-boundary")
            if isinstance(n, ast.Return):
                tags.append("return-branch")
            if tags:
                par = n
                while par in parents and not isinstance(par, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    par = parents[par]
                rows.append(dict(path=p.relative_to(ROOT).as_posix(), line=n.lineno,
                                 function=getattr(par, "name", "<module>"), tags=tags,
                                 code=ast.get_source_segment(s, n)[:700]))
out = Path(__file__).resolve().parent / (sys.argv[1] if len(sys.argv) > 1 else "numeric_surface_scan.json")
out.write_text(json.dumps(dict(files=files, candidates=rows), indent=2, ensure_ascii=False), encoding="utf-8")
print(len(files), "modules", len(rows), "candidates")
for r in rows:
    if "float-zero-initializer" in r["tags"]:
        print(r["path"], r["line"], r["function"], repr(r["code"][:150]))
