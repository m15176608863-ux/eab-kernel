"""DRAFT installer: run ONLY after root explicitly releases the source freeze."""
from pathlib import Path
import ast
import shutil

ROOT = Path(__file__).resolve().parents[4]
DRAFT = Path(__file__).resolve().parent
SOURCE = ROOT / "src/eab/kernel3d/covers3.py"
TEST = ROOT / "tests/test_perf_edge_frame.py"


def text(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


if __name__ == "__main__":
    source = text(SOURCE)
    proposal = text(DRAFT / "edge_functions.py")
    functions = {n.name: n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
    assert "_integer_ray" not in functions, "Draft must not be applied twice"
    assert not TEST.exists(), "Never overwrite an existing test artifact"
    assert "convex, h1, h2 = _qedge_frame_cached(t, n1, n2, cross, dot)" in source
    old_lines = source.splitlines(keepends=True)
    draft_lines = proposal.splitlines(keepends=True)
    additions = {}
    for node in ast.parse(proposal).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
        additions[node.name] = "".join(draft_lines[start:node.end_lineno])
    replacements = []
    for name in ("_qedge_contains", "_qedge_frame_cached"):
        node = functions[name]
        start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
        new = additions[name]
        if name == "_qedge_contains":
            new = additions["_integer_ray"] + "\n\n" + new
        newline = "\r\n" if "\r\n" in source else "\n"
        new = new.replace("\r\n", "\n").replace("\n", newline)
        replacements.append((start, node.end_lineno, new))
    for start, end, new in sorted(replacements, reverse=True):
        old_lines[start:end] = [new]
    updated = "".join(old_lines)
    ast.parse(updated)
    with SOURCE.open("w", encoding="utf-8", newline="") as handle:
        handle.write(updated)
    shutil.copyfile(DRAFT / "test_perf_edge_frame.py", TEST)
    print("Applied only src/eab/kernel3d/covers3.py and added tests/test_perf_edge_frame.py")
