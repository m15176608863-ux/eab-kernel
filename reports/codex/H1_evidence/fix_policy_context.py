"""One comment/docstring-only local review update, never new admission.

Read-only 476c5d6 anchors the exact old policy; remove real docstrings and
compare complete executable ASTs before changing this one context field.
The original 1ce9a91 historical view must remain byte-data-equivalent.
"""
import argparse
import ast
import copy
import csv
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / "reports/codex/H1_evidence"
sys.path.insert(0, str(ROOT / "tools"))
import exact_construction_subset as subset
from policy_history_view import historical_view


def blob(commit, name):
    return subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT)


def executable(text):
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    node.body = node.body[1:]
    return ast.dump(tree, include_attributes=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source_name = "src/eab/contact_record.py"
    before = blob("476c5d6", source_name).decode("utf-8")
    after = (ROOT/source_name).read_text("utf-8")
    assert executable(before) == executable(after), "review is limited to docs/comments"
    old_context = subset.site_contexts(before)["<module>"]
    new_context = subset.site_contexts(after)["<module>"]
    policy_name = "tools/exact_construction_policy.json"
    relocation_name = "tools/exact_construction_relocations.json"
    original = json.loads(blob("476c5d6", policy_name))
    policy = json.loads((ROOT/policy_name).read_text("utf-8"))
    mapping = json.loads((ROOT/relocation_name).read_text("utf-8"))
    old_mapping = json.loads(blob("476c5d6", relocation_name))
    row = original["waivers"][6]
    assert row["id"] == "R12b-L0008" and row["path"] == source_name
    assert row["context"] == old_context and row["function"] == "<module>"
    assert row["node"] in {ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(after))}
    wanted = copy.deepcopy(original)
    wanted["waivers"][6]["context"] = new_context
    pointer = ["waivers", 6, "context"]
    old_change = next(r for r in old_mapping["changes"] if r["pointer"] == pointer)
    desired_mapping = copy.deepcopy(old_mapping)
    next(r for r in desired_mapping["changes"] if r["pointer"] == pointer)["new"] = new_context
    # proof describes the extra stage; it does not alter the frozen fields.
    desired_mapping["proof"] = old_mapping["proof"] + "; H1-fix: reports/codex/H1_evidence/fix_policy_context.py proves docstring-only executable-AST equivalence"
    assert policy in (original, wanted)
    assert mapping in (old_mapping, desired_mapping)
    assert historical_view(wanted, desired_mapping) == json.loads(blob("1ce9a91", policy_name))
    assert len(wanted["waivers"]) == 3522 and len(desired_mapping["changes"]) == 142
    if args.apply:
        if policy == original:
            raw = (ROOT/policy_name).read_bytes()
            assert raw.count(old_context.encode()) == 1
            (ROOT/policy_name).write_bytes(raw.replace(old_context.encode(), new_context.encode(), 1))
        if mapping == old_mapping:
            raw = (ROOT/relocation_name).read_bytes()
            assert raw.count(old_context.encode()) == 1
            raw = raw.replace(old_context.encode(), new_context.encode(), 1)
            raw = raw.replace(json.dumps(old_mapping["proof"]).encode(), json.dumps(desired_mapping["proof"]).encode(), 1)
            (ROOT/relocation_name).write_bytes(raw)
        assert json.loads((ROOT/policy_name).read_text("utf-8")) == wanted
        assert json.loads((ROOT/relocation_name).read_text("utf-8")) == desired_mapping
    issues = subset.stale_waiver_issues(after, source_name)
    assert not issues, issues
    result = dict(complete=True, applied=args.apply, baseline="476c5d6", pointer=pointer,
                  old=old_context, new=new_context, same_ast_site=True, executable_ast_equal=True,
                  policy_changed_fields=1, grants_before=3522, grants_after=3522,
                  relocation_fields=142, historical_1ce9a91_policy_equal=True,
                  stale_context_issues=issues, no_new_admissions=True)
    (E/"fix_purity/context_update.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
