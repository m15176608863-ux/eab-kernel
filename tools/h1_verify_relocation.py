"""Read-only H1 production-definition and mapping-table relocation check."""
import argparse
import ast
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MOVES = {
    "src/eab/kernel3d/interlock.py": "src/eab/adapters/tia3d.py",
    "src/eab/kernel2d/dda_motion.py": "src/eab/adapters/bdda2d_motion.py",
    "src/eab/readers/numeric_decode.py": "src/eab/numeric_decode.py",
}
TABLES = {"BDDA_MODE", "BDDA_COVER", "BDDA3D_MODE", "BDDA3D_COVER", "TF_MODE", "TF_COVER"}


def target(path, name):
    if path == "src/eab/kernel2d/affine_motion.py" and name.split(".")[0] == "DDAAffineMotion":
        return "src/eab/adapters/bdda2d_affine.py"
    if path == "src/eab/kernel2d/model_robustness.py" and name == "dda_paths":
        return "src/eab/adapters/bdda2d_motion.py"
    return MOVES.get(path, path)


def definitions(text):
    result = {}
    class Gather(ast.NodeVisitor):
        prefix = ""
        def definition(self, node):
            key = self.prefix + node.name
            assert key not in result, key
            result[key] = ast.dump(node, include_attributes=False)
            old = self.prefix
            self.prefix = key + "."
            self.generic_visit(node)
            self.prefix = old
        visit_ClassDef = visit_FunctionDef = visit_AsyncFunctionDef = definition
    Gather().visit(ast.parse(text))
    return result


def _verify(root, old_files, read_old):
    new_defs = {p.relative_to(root).as_posix(): definitions(p.read_text(encoding="utf-8-sig"))
                for p in (root / "src/eab").rglob("*.py")}
    matched = set()
    for file in old_files:
        source = read_old(file)
        if file == "src/eab/kernel3d/geom3.py":
            source = source.replace("reader boundary (readers.bdda_geom.strip_duplicate_vertices)", "input boundary")
        for name, node in definitions(source).items():
            new = target(file, name)
            assert new_defs[new][name] == node, (file, name, new)
            matched.add((new, name))
    actual = {(path, name) for path, defs in new_defs.items() for name in defs}
    assert actual == matched, sorted(actual - matched)
    old = ast.parse(read_old("src/eab/contact_record.py"))
    original = {n.target.id: ast.dump(n, include_attributes=False) for n in old.body
                if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id in TABLES}
    relocated = {}
    for name in ("bdda2d", "bdda3d", "tf"):
        for node in ast.parse((root / f"src/eab/adapters/{name}.py").read_text(encoding="utf-8")).body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in TABLES:
                assert node.target.id not in relocated
                relocated[node.target.id] = ast.dump(node, include_attributes=False)
    assert original == relocated and len(original) == 6
    return dict(old_modules=len(old_files), new_modules=len(new_defs), equal_definitions=len(matched),
                equal_mapping_tables=6, unmatched_new_definitions=0, mathematical_ast_equal=True,
                diagnostic_text_exception="geom3.Polyhedron.edge_dir: reader example -> input boundary")


def verify_relocation(root, baseline):
    """Compare two source trees, allowing only the explicit H1 ownership map.

    All classes/functions (including nested definitions) must map one to one.
    Their entire AST is unchanged except the named diagnostic-text edit.
    Imports and package exports are outside this check and require a separate
    binding comparison; it is not an arbitrary module-source refresh permit.
    """
    root, baseline = Path(root).resolve(), Path(baseline).resolve()
    old_files = sorted(p.relative_to(baseline).as_posix() for p in (baseline / "src/eab").rglob("*.py"))
    result = _verify(root, old_files, lambda file: (baseline / file).read_text(encoding="utf-8-sig"))
    result["baseline"] = str(baseline)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--baseline", type=Path)
    group.add_argument("--baseline-ref", default="1ce9a91")
    args = parser.parse_args()
    if args.baseline:
        result = verify_relocation(args.root, args.baseline)
    else:
        def git(*command):
            return subprocess.check_output(["git", *command], cwd=args.root).decode("utf-8-sig")
        old_files = [p for p in git("ls-tree", "-r", "--name-only", args.baseline_ref, "src/eab").splitlines() if p.endswith(".py")]
        result = _verify(args.root, old_files, lambda file: git("show", args.baseline_ref + ":" + file))
        result["baseline"] = args.baseline_ref
    print(json.dumps(result))


if __name__ == "__main__":
    main()
