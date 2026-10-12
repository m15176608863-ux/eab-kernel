"""R14 reproducible lexical/AST coverage index, NOT a correctness prover.

No imports of eab and no execution of sibling tools. Record every public
signature and exact-to-binary64 / trigonometric / JSON call candidate.
Manual dispositions live in the report; this cannot infer physical units.
"""
import ast
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
families = {
    "friction": {"mu"},
    "cohesion_area": {"cohesion", "area"},
    "angle_exponent": {"phase", "p", "h1_degrees", "cone_tol", "angle"},
    "length_window": {"delta", "band", "window", "contact_window", "d0", "seg_tol", "fit_tol", "geom_tol", "tol"},
    "geometry_force_motion": {"point", "normal", "tangent", "force", "origin", "dead", "live", "x0", "d", "scale", "center", "half", "verts", "poly", "points", "direction", "velocity", "t_max", "height"},
    "integer_structure": {"k", "dim", "width", "n", "nx", "ny", "step", "index", "max_iter", "steps", "seed"},
}
public = []
sites = []
modules = []
for folder in ("src/eab", "tools"):
    for path in sorted((ROOT/folder).rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        modules.append(relative)
        parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        def scope(node):
            names = []
            while node in parent:
                node = parent[node]
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.append(node.name)
            return ".".join(reversed(names)) or "<module>"
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                params = [a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs) if a.arg not in {"self", "cls"}]
                public.append({"file": relative, "line": node.lineno, "scope": scope(node), "name": node.name,
                               "parameters": params,
                               "lexical_quantity_families": {f: sorted(set(params)&names) for f,names in families.items() if set(params)&names},
                               "proof_status": "signature index only; model/domain reviewed by family, not a full API proof"})
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                tail = name.rsplit(".", 1)[-1]
                if tail in {"float", "sin", "cos", "atan2", "tan", "radians", "pow", "loads", "load", "scalar_rational", "binary64_argument", "check_mu"}:
                    kind = ("checked_boundary" if tail in {"scalar_rational", "binary64_argument", "check_mu"}
                            else "json_or_generic_loader" if tail in {"loads", "load"}
                            else "float_candidate" if tail == "float" else "elementary_candidate")
                    sites.append({"file": relative, "line": node.lineno, "scope": scope(node), "callee": name, "kind": kind,
                                  "source": ast.get_source_segment(source,node)})
result = {"scope": "all src/eab and tools Python modules; signatures include structural arguments, not just quantities",
          "limitations": "AST inventory cannot infer units, prove all branches, or validate all natural-language claims; use manual report dispositions",
          "modules": modules, "counts": {"modules":len(modules), "public_signatures":len(public), "candidate_calls":len(sites),
                                         "site_kinds":dict(collections.Counter(x['kind'] for x in sites))},
          "public_signatures":public, "numeric_call_sites":sites}
(OUT/"numeric_surface_audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(result["counts"]))
