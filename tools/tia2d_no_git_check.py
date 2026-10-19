"""Verify TIA gates in a read-only git-archive export overlaid by repair bytes.

This is a no-.git byte export, NOT a new worktree or fresh merged checkout.
The immutable source list/hash records distinguish HEAD archive provenance
from the actual repaired working bytes tested. No Git writes are performed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

from tia2d_run_gates import source_names

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in (".", ".."):
        parser.error("new single directory name required")
    evidence = ROOT / "reports/codex/T1a_evidence"
    output, scratch = evidence / args.name, evidence / "tmp" / args.name
    if output.exists() or scratch.exists():
        parser.error("new output and scratch required")
    output.mkdir()
    scratch.mkdir()
    source = scratch / "source"
    source.mkdir()
    archive = scratch / "head.zip"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    roots = subprocess.check_output(["git", "ls-tree", "--name-only", head], cwd=ROOT, text=True).splitlines()
    roots = [name for name in roots if name not in ("reports", "AGENTS.md")]
    command = ["git", "archive", "--format=zip", "--output=" + str(archive), head, *roots]
    subprocess.run(command, cwd=ROOT, check=True)
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            if entry.is_dir():
                continue
            target = (source / entry.filename).resolve()
            if not target.is_relative_to(source.resolve()):
                raise ValueError("unsafe archive member")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.read(entry))
    manifest = []
    for name in source_names(ROOT):
        if name.startswith("reports/"):
            continue
        data = (ROOT / name).read_bytes()
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    # Exclude deleted files from the archive baseline; every removal stays in
    # this verified snapshot, never in the live working tree.
    names = {row["path"] for row in manifest}
    for path in sorted(source.rglob("*")):
        if path.is_file() and path.relative_to(source).as_posix() not in names:
            if not path.resolve().is_relative_to(source.resolve()):
                raise ValueError("unsafe snapshot deletion")
            path.unlink()
    (scratch / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(source.parent),
        PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
        TEMP=str(evidence / "tmp"), TMP=str(evidence / "tmp"),
        PYTHONPATH=os.pathsep.join((str(source / "src"), str(source / "tools"))))
    probe = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, env=env, capture_output=True)
    if probe.returncode == 0 or (source / ".git").exists():
        raise ValueError("verification copy can still discover Git")
    tests = sorted("tests/" + p.name for p in (source / "tests").glob("test_tia2d_*.py"))
    tests.append("tests/test_kernel_purity.py")
    test_command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    "--basetemp", str(scratch / "pytest"), "--runslow", *tests]
    state = dict(status="RUNNING", head_archive=head, archive_command=command, command=test_command,
        fresh_git_checkout=False, method="git_archive_plus_exact_working_byte_overlay",
        git_unavailable_verified=True, source_manifest_sha256=hashlib.sha256((scratch / "source_manifest.json").read_bytes()).hexdigest())
    def save():
        (output / "summary.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    save()
    start = time.perf_counter()
    with (output / "pytest.log").open("wb") as stream:
        process = subprocess.Popen(test_command, cwd=source, env=env, stdout=stream, stderr=subprocess.STDOUT)
        while process.poll() is None:
            state.update(pid=process.pid, wall_seconds=time.perf_counter() - start)
            save()
            time.sleep(2)
    changed = [row["path"] for row in manifest if
        hashlib.sha256((source / row["path"]).read_bytes()).hexdigest() != row["sha256"] or
        hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() != row["sha256"]]
    lines = (output / "pytest.log").read_text(encoding="utf-8").splitlines()
    state.update(exit_code=process.returncode, changed_sources=changed,
        status="PASS" if process.returncode == 0 and not changed else "FAILED_OR_INVALIDATED",
        wall_seconds=time.perf_counter() - start, last_line=lines[-1])
    save()
    print(state["status"], state["last_line"], flush=True)
    return int(state["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
