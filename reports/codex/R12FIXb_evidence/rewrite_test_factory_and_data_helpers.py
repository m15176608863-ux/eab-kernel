"""Replace fixed fixture factories and numeric callbacks with explicit helpers."""
import ast
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
records = []


def save(path, old, new, changes):
    assert old != new
    a, b = ast.parse(old.decode("utf-8-sig")), ast.parse(new.decode("utf-8-sig"))
    def nodes(t):
        return [(n.name, ast.dump(n.args, include_attributes=False),
                 [ast.dump(d, include_attributes=False) for d in n.decorator_list])
                for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert nodes(a) == nodes(b), "Keep every original test node and parametrization"
    backup = BASE / "test_factory_rewrite_backup" / path.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    assert not backup.exists()
    backup.write_bytes(old)
    path.write_bytes(new)
    records.append({"path": path.relative_to(ROOT).as_posix(), "backup": backup.relative_to(ROOT).as_posix(),
                    "sha256_before": hashlib.sha256(old).hexdigest(), "sha256_after": hashlib.sha256(new).hexdigest(),
                    "test_definitions_and_parametrization_preserved": True, "changes": changes})


def factory(file, table, index, factory_name, caller, direct_call=None):
    path = ROOT / "tests" / file
    raw = path.read_bytes()
    source = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in source else "\n"
    tree = ast.parse(source)
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == table for t in n.targets))
    assert isinstance(assignment.value, ast.Dict)
    lines = source.splitlines(keepends=True)
    offsets = []
    total = 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    def pos(line, col):
        return offsets[line-1] + len(lines[line-1].encode("utf-8")[:col].decode("utf-8"))
    edits, branches = [], []
    for key, value in zip(assignment.value.keys, assignment.value.values):
        name = ast.literal_eval(key)
        maker = value.elts[index]
        if isinstance(maker, ast.Name):
            body = maker.id + "()"
        else:
            assert isinstance(maker, ast.Lambda) and not maker.args.args
            body = ast.get_source_segment(source, maker.body)
        branches.extend([f"    if name == {json.dumps(name)}:", "        return " + body])
        edits.append((pos(maker.lineno, maker.col_offset), pos(maker.end_lineno, maker.end_col_offset), json.dumps(name)))
    for start, stop, replacement in sorted(edits, reverse=True):
        source = source[:start] + replacement + source[stop:]
    helper = nl.join([f"def {factory_name}(name):", '    """Build the same fixed fixture through transparent first-order calls."""',
                      *branches, "    raise KeyError(name)", "", ""])
    marker = "@lru_cache(maxsize=None)" + nl + f"def {caller}("
    assert source.count(marker) == 1
    source = source.replace(marker, helper + marker)
    # Exactly the old factory call, not any numerical expression, changes.
    assert source.count("    A, B = make()") == 1
    source = source.replace("    A, B = make()", f"    A, B = {factory_name}(name)")
    if direct_call:
        assert source.count(direct_call) == 1
        source = source.replace(direct_call, f"{factory_name}(name)")
    # Preserve BOM and line endings; the table keeps its original tuple layout.
    encoded = (b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + source.encode("utf-8")
    save(path, raw, encoded, ["fixed factory table now holds data labels only", "same factory expressions called through explicit branches"])


factory("test_invariance_geom.py", "PAIRS", 0, "_pair_for_name", "_base")
factory("test_invariance_interlock.py", "MARGIN_CASES", 1, "_margin_pair_for_name", "_margin_ref", "MARGIN_CASES[name][1]()")

path = ROOT / "tests/test_margin.py"
raw = path.read_bytes()
source = raw.decode("utf-8-sig")
nl = "\r\n" if "\r\n" in source else "\n"
tree = ast.parse(source)
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
old = ast.get_source_segment(source, functions["_lipschitz_worst"])
new = nl.join(["def _lipschitz_worst(samples):", '    """Each sample is (x, y, normal_at_x, normal_at_y); no callback."""',
               "    worst = 0.0", "    for x, y, nx, ny in samples:",
               "        worst = max(worst, norm(sub(nx, ny)) / norm(sub(x, y)))", "    return worst"])
assert source.count(old) == 1
source = source.replace(old, new)
old = ast.get_source_segment(raw.decode("utf-8-sig"), functions["_lipschitz_verdict"])
new = nl.join(["def _lipschitz_verdict(local, loops, glob, delta=0.25):", '    """Check the original ordered samples; their normals are supplied data."""',
               "    w_local = max(_lipschitz_worst(local), _lipschitz_worst(loops))",
               "    w_global = _lipschitz_worst(glob)",
               "    ok = max(w_local, w_global) <= 2.0 / delta + 1e-9 and w_local >= 0.9 / delta",
               "    return (w_local, w_global), ok"])
assert source.count(old) == 1
source = source.replace(old, new)
source = source.replace("_TRUE_INFLATED_NORMAL = inflated_normal", "from eab.margin import inflated_normal as _TRUE_INFLATED_NORMAL")
source = source.replace("    _, _, _, glob = _lipschitz_setup(delta)", "    E, local, loops, glob = _lipschitz_setup(delta)")
old = "    (w_local, w_global), ok = _lipschitz_verdict(fn, delta)"
new = nl.join(["    samples = [[(x, y, fn(E, x), fn(E, y)) for x, y in pairs]", "               for pairs in (local, loops, glob)]",
               "    (w_local, w_global), ok = _lipschitz_verdict(*samples, delta=delta)"])
assert source.count(old) == 1
source = source.replace(old, new)
old = "    for name, fn in mutants.items():" + nl + "        worst, ok = _lipschitz_verdict(fn)"
new = nl.join(["    E, local, loops, glob = _lipschitz_setup(0.25)", "    for name, fn in mutants.items():",
               "        samples = [[(x, y, fn(E, x), fn(E, y)) for x, y in pairs]", "                   for pairs in (local, loops, glob)]",
               "        worst, ok = _lipschitz_verdict(*samples)"])
assert source.count(old) == 1
source = source.replace(old, new)
old = "    (w_local, w_global), ok = _lipschitz_verdict(bump, delta)" + nl + "    (w_true, _), _ = _lipschitz_verdict(_true_normal, delta)"
new = nl.join(["    samples = [[(x, y, bump(E, x), bump(E, y)) for x, y in pairs]", "               for pairs in (local, loops, glob)]",
               "    (w_local, w_global), ok = _lipschitz_verdict(*samples, delta=delta)",
               "    true_samples = [[(x, y, _true_normal(E, x), _true_normal(E, y)) for x, y in pairs]", "                    for pairs in (local, loops, glob)]",
               "    (w_true, _), _ = _lipschitz_verdict(*true_samples, delta=delta)"])
assert source.count(old) == 1
source = source.replace(old, new)
# Preserve all implanted faulty-normal expression bodies, including RNG order.
new_tree = ast.parse(source)
old_lambdas = [ast.dump(n, include_attributes=False) for n in ast.walk(tree) if isinstance(n, ast.Lambda)]
new_lambdas = [ast.dump(n, include_attributes=False) for n in ast.walk(new_tree) if isinstance(n, ast.Lambda)]
assert old_lambdas == new_lambdas
old_bump = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "bump")
new_bump = next(n for n in ast.walk(new_tree) if isinstance(n, ast.FunctionDef) and n.name == "bump")
assert ast.dump(old_bump, include_attributes=False) == ast.dump(new_bump, include_attributes=False)
encoded = (b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + source.encode("utf-8")
save(path, raw, encoded, ["numeric Lipschitz helpers accept ordered coordinate/normal samples, not callbacks",
                          "existing test drivers evaluate identical normal functions in local/loop/global order",
                          "all mutant lambda and bump bodies unchanged", "saved true normal now a direct import alias"])
(BASE / "test_factory_rewrite_changes.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(records), "paths": [r["path"] for r in records]}, indent=2))
