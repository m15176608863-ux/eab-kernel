"""Deliverable size inventory for Git trees and no-Git byte exports.

This is filesystem delivery auditing, not a numerical geometry oracle. Git
commands are read-only; fresh exports obey the positive .gitignore rules.
"""
from pathlib import Path
import os
import re
import subprocess

LIMIT = 1_000_000
DELIVERABLE_ROOTS = ("src", "tests", "tools", "fixtures", "docs", "reports", "eab2")
ALLOW_OVERSIZE = {
    "tools/exact_construction_policy.json":
        "Existing static-construction admission policy is frozen by WO-H1; mechanical rekeys only, no new admissions.",
}


def _glob(pattern):
    # The current .gitignore uses only positive *, ?, and slash patterns.
    return re.compile("^" + "".join("[^/]*" if ch == "*" else "[^/]" if ch == "?" else re.escape(ch)
                                  for ch in pattern) + "$")


def _ignored(relative, rules):
    parts = relative.split("/")
    for raw in rules:
        pattern = raw.strip()
        if not pattern or pattern.startswith("#"):
            continue
        assert not pattern.startswith("!"), "extend export ignore parser before adding negated rules"
        directory = pattern.endswith("/")
        pattern = pattern.strip("/")
        matcher = _glob(pattern)
        candidates = ["/".join(parts[:i]) for i in range(1, len(parts))] if directory else [relative]
        if "/" not in pattern:
            candidates = parts[:-1] if directory else parts
        if any(matcher.fullmatch(candidate) for candidate in candidates):
            return True
    return False


def delivery_files(root):
    root = Path(root)
    if (root / ".git").exists():
        command = ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
        result = subprocess.run(command, cwd=root, check=True, capture_output=True)
        names = sorted(set(name for name in result.stdout.decode("utf-8").split("\0") if name))
        return [root / name for name in names if (root / name).is_file()]
    ignore = root / ".gitignore"
    rules = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
    files = []
    for folder in DELIVERABLE_ROOTS:
        for parent, directories, names in os.walk(root / folder, followlinks=False):
            # Do not walk a test runner's ignored snapshot/basetemp tree before
            # filtering it: such trees can contain hundreds of thousands of files.
            directories[:] = [name for name in directories
                              if not _ignored((Path(parent) / name / "__probe__").relative_to(root).as_posix(), rules)]
            files.extend(Path(parent) / name for name in names)
    files += [path for path in root.iterdir() if path.is_file()]
    return [path for path in files if not _ignored(path.relative_to(root).as_posix(), rules)]


def assert_deliverable_sizes(root):
    root = Path(root)
    bad = []
    for path in delivery_files(root):
        name = path.relative_to(root).as_posix()
        if path.stat().st_size > LIMIT and name not in ALLOW_OVERSIZE:
            bad.append((name, path.stat().st_size))
    assert not bad, ("deliverable file exceeds 1,000,000 bytes", bad)
    assert all(reason.strip() for reason in ALLOW_OVERSIZE.values())


