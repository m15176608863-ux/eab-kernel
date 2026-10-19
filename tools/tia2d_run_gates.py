"""Run unchanged H1 execution/coverage gates in the T1a evidence directory.

--baseline freezes the current HEAD by read-only git archive, so later working
edits cannot change the baseline under test. This is a byte export, NOT a new
Git tree. Normal runs retain H1's live-tree immutability check. No Git writes.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import shutil

import h1_run_gates as gates
from tia2d_provenance import git_provenance


def source_names(root):
    """List source bytes without requiring a Git checkout or ignored caches."""
    root = Path(root).resolve()
    if git_provenance(root)["git_commit"] is not None:
        raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root)
        names = raw.decode("utf-8").split("\0")
    else:
        names = [p.relative_to(root).as_posix() for p in root.rglob("*")
                 if p.is_file() and not any(v in (".git", "__pycache__", ".pytest_cache", "tmp")
                                            for v in p.relative_to(root).parts)]
    return sorted({name for name in names if name and (root / name).is_file()
                   and not name.startswith(("reports/codex/H1_evidence/", "reports/codex/T1a_evidence/"))})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--runslow", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("name must be a new single directory name")
    root = Path(__file__).resolve().parents[1]
    evidence = root / "reports/codex/T1a_evidence"
    gates.EVIDENCE = evidence
    gates.source_names = lambda: source_names(root)
    if args.baseline:
        frozen = evidence / "tmp" / (args.name + "_anchor")
        frozen.mkdir(parents=True, exist_ok=False)
        archive = frozen / "head.zip"
        git = git_provenance(root)
        head = git["git_commit"]
        source = frozen / "source"
        source.mkdir()
        if head is not None:
            subprocess.run(["git", "archive", "--format=zip", "--output=" + str(archive), head], cwd=root, check=True)
            with zipfile.ZipFile(archive) as bundle:
                for member in bundle.infolist():
                    if member.is_dir() or member.filename.startswith("reports/codex/H1_evidence/"):
                        continue
                    target = (source / member.filename).resolve()
                    if not target.is_relative_to(source.resolve()):
                        raise ValueError("archive member outside workspace snapshot")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(bundle.read(member))
        else:
            for name in source_names(root):
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / name, target)
        names = tuple(sorted(p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()))
        provenance = dict(**git, head=head, source=str(source), method="read_only_git_archive" if head else "no_git_byte_snapshot",
                          fresh_git_checkout=False, includes_untracked_diagnostics=False)
        gates.write(evidence / (args.name + "_anchor.json"), provenance)
        gates.ROOT = source
        gates.source_names = lambda: list(names)
    sys.argv = [sys.argv[0], "--name", args.name] + (["--runslow"] if args.runslow else [])
    return gates.main()


if __name__ == "__main__":
    raise SystemExit(main())
