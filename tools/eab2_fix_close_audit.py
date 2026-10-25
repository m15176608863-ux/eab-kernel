"""WO-C3L4-fix-close byte/hygiene audit; Git commands are read-only.

Candidate means tracked files still present plus unignored untracked files,
deduplicated by path. Net growth is candidate total minus ALL base blob bytes,
not a sum of positive file deltas. Ignored builds are not delivery artifacts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from repository_size import ALLOW_OVERSIZE

ROOT = Path(__file__).resolve().parents[1]
PROTECTED = ("src/eab/", "eab2/src/", "eab2/include/", "tests/data/", "fixtures/")
DESIGN = "docs/eab2_design.md"
REPORTS = ("reports/codex/C3L4_fix_report.md", "reports/codex/C3L4_report.md")
BOMS = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")
COMPILED = {".exe", ".dll", ".obj", ".lib", ".pdb", ".ilk", ".pyc"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(base, baseline):
    names = sorted({name for name in git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0")
                    if name and (ROOT / name).is_file()})
    blobs = {}
    for line in filter(None, git("ls-tree", "-r", "-l", "-z", base).decode("utf-8").split("\0")):
        metadata, name = line.split("\t", 1)
        mode, kind, oid, size = metadata.split()
        if kind == "blob":
            blobs[name] = dict(oid=oid, bytes=int(size))
    sizes = {name: (ROOT / name).stat().st_size for name in names}
    candidate_bytes, base_bytes = sum(sizes.values()), sum(row["bytes"] for row in blobs.values())
    changed = sorted(set(filter(None, git("diff", "HEAD", "--name-only", "-z").decode().split("\0"))) |
                     set(filter(None, git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))))
    violations, inherited_bom, inherited_oversize = [], [], []
    for name in names:
        path = ROOT / name
        if sizes[name] > 1_000_000:
            raw = path.read_bytes()
            if name in ALLOW_OVERSIZE and name in blobs and raw == git("cat-file", "blob", blobs[name]["oid"]):
                inherited_oversize.append(dict(path=name, bytes=len(raw), sha256=digest(raw),
                    base_blob=blobs[name]["oid"], base_byte_identical=True, reason=ALLOW_OVERSIZE[name]))
            else:
                violations.append("over_1MB:" + name)
        if path.suffix.lower() in COMPILED:
            violations.append("compiled_delivery:" + name)
        with path.open("rb") as stream:
            prefix = stream.read(4)
        if prefix.startswith(BOMS):
            raw = path.read_bytes()
            if name in blobs and raw == git("cat-file", "blob", blobs[name]["oid"]):
                inherited_bom.append(dict(path=name, sha256=digest(raw), base_byte_identical=True))
            else:
                violations.append("new_or_modified_BOM:" + name)
        if path.suffix.lower() in {".bat", ".cmd"} and not path.read_bytes().isascii():
            violations.append("non_ASCII_batch:" + name)
        if name in changed and path.suffix.lower() in {".py", ".md", ".txt", ".json", ".log", ".bat", ".cmd", ".ps1"}:
            raw = path.read_bytes()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                violations.append("non_UTF8_changed_text:" + name)
                continue
            if b"\r\n" in raw and b"\n" in raw.replace(b"\r\n", b""):
                violations.append("mixed_newlines:" + name)
            if any(line.rstrip(" \t") != line for line in text.splitlines()):
                violations.append("changed_text_trailing_whitespace:" + name)
    protected = {name for name in names if name.startswith(PROTECTED) or name == DESIGN}
    expected = baseline["protected"]
    protected_changes = sorted(protected ^ expected.keys())
    protected_changes += [name for name in sorted(protected & expected.keys())
                          if digest((ROOT / name).read_bytes()) != expected[name]]
    if protected_changes:
        violations.append("protected_paths_changed")
    top_changes = []
    current_top = {p.relative_to(ROOT).as_posix() for p in (ROOT / "eab2/build").iterdir() if p.is_file()}
    expected_top = baseline["top_build"]
    for name in sorted(current_top | expected_top.keys()):
        path, old = ROOT / name, expected_top.get(name)
        if old is None or not path.is_file():
            top_changes.append(name)
        elif (path.stat().st_size, path.stat().st_mtime_ns, digest(path.read_bytes())) != (old["bytes"], old["mtime_ns"], old["sha256"]):
            top_changes.append(name)
    if top_changes:
        violations.append("existing_top_build_changed")
    report_checks = {}
    for name in REPORTS:
        raw = (ROOT / name).read_bytes()
        old = baseline["report_prefixes"][name]
        preserved = digest(raw[:old["bytes"]]) == old["sha256"]
        last = raw.decode("utf-8").splitlines()[-1]
        report_checks[name] = dict(original_bytes=old["bytes"], original_sha256=old["sha256"],
                                   original_prefix_preserved=preserved, last_line=last)
        if not preserved or last != "C3L4FIX_PENDING_OWNER_ACCEPTANCE":
            violations.append("report_append_contract:" + name)
    if candidate_bytes - base_bytes > 2_000_000:
        violations.append("net_growth_exceeds_2000000")
    check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, check=False)
    if check.returncode:
        violations.append("git_diff_check_failed")
    package = ROOT / "reports/codex/C3L4_fix_evidence/owner_run_64b499f"
    package_bytes = sum(p.stat().st_size for p in package.rglob("*") if p.is_file())
    if package_bytes > 300_000:
        violations.append("owner_package_exceeds_300000")
    return dict(schema="eab2.fix_close_hygiene.v1", base=base, head=git("rev-parse", "HEAD").decode().strip(),
        candidate_definition="existing tracked plus unignored untracked; unique paths; ignored builds excluded",
        base_blob_count=len(blobs), base_blob_bytes=base_bytes, candidate_file_count=len(names),
        candidate_bytes=candidate_bytes, real_net_growth_bytes=candidate_bytes-base_bytes,
        net_limit_bytes=2_000_000, owner_package_bytes=package_bytes,
        max_candidate_file_bytes=max(sizes.values()), protected_paths_checked=len(protected),
        protected_changes=protected_changes, top_build_changes=top_changes,
        design_sha256=digest((ROOT / DESIGN).read_bytes()), inherited_bom_unchanged=inherited_bom,
        inherited_oversize_unchanged=inherited_oversize,
        bom_boundary="no new/modified BOM; pre-base byte-identical BOM retained, including read-only production files",
        report_append_checks=report_checks, changed_files=[dict(path=n, bytes=sizes.get(n),
            status="present" if n in sizes else "removed",
            link=(ROOT / n).as_uri() if n in sizes else None) for n in changed], git_diff_check_exit=check.returncode,
        git_diff_check_output=(check.stdout+check.stderr).decode("utf-8", errors="replace"),
        violations=violations, status="PASS" if not violations else "FAIL")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="b34c966")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT) or subprocess.run(
            ["git", "check-ignore", "--quiet", str(args.output)], cwd=ROOT, check=False).returncode == 0:
        parser.error("output must be an unignored workspace delivery file")
    baseline = json.loads(args.baseline.read_text("utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Account for the audit file itself. Its own path/size (not self-hash) may
    # change the total by a few digits; settle to a byte-exact fixed point.
    settled = False
    for _ in range(5):
        result = audit(args.base, baseline)
        result["last_line"] = (f"C3L4_CLOSE_HYGIENE status={result['status']} net={result['real_net_growth_bytes']} "
                               f"limit=2000000 findings={len(result['violations'])}")
        raw = (json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        same_size = args.output.exists() and args.output.stat().st_size == len(raw)
        args.output.write_bytes(raw)
        if same_size:
            settled = True
            break
    if not settled:
        raise RuntimeError("byte audit did not converge; no final PASS")
    print(result["last_line"])
    return int(bool(result["violations"]))


if __name__ == "__main__":
    raise SystemExit(main())
