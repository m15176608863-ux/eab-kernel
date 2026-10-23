"""WO-C3L3 read-back delivery audit. Run after report/archive completion."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/C3L3_evidence"
BASE = "1b6b4f32ff3c5716f8e3a24ad73dd3cf6081f39c"
META = {"reports/codex/C3L3_evidence/artifact_manifest.json",
        "reports/codex/C3L3_evidence/delivery_integrity.json",
        "reports/codex/C3L3_evidence/hygiene.json"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def candidates():
    changed = git("diff", "--name-only", "-z", BASE).decode("utf-8").split("\0")
    other = git("ls-files", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0")
    return sorted(set(filter(None, changed + other)))


def main():
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert git("branch", "--show-current").decode().strip() == "eab2-c3l3"
    assert git("config", "--get", "core.autocrlf").decode().strip() == "false"
    assert not git("diff", BASE, "--", "src/eab", "docs/eab2_design.md", "eab2/src/opt.cpp", "eab2/src/opt.hpp")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    for run in ("baseline", "final_fast", "final_full"):
        data = json.loads((OUT / run / "summary.json").read_text("utf-8"))
        assert data["audit"] == "GREEN" and data["complete"]
        assert data["module_coverage_complete"] and not data["live_tree_changed"] and not data["export_changed"]
        assert all(s["node_sets_equal"] and s["skip_count"] == s["failed_count"] == 0 for s in data["shards"])
    differential = json.loads((OUT / "differential.json").read_text("utf-8"))
    assert differential["source_pre_post_equal"] and not differential["mismatches"]
    assert differential["counts"] == {"limit": 217, "critical": 171}
    assert sha((ROOT / "eab2/build/eab2.dll").read_bytes()) == differential["dll_sha256"]

    tested = json.loads((OUT / "tmp/final_full/source_manifest.json").read_text("utf-8"))
    changed_after_test = [r["path"] for r in tested if sha((ROOT / r["path"]).read_bytes()) != r["sha256"]]
    assert set(changed_after_test) <= {"reports/EVIDENCE_ARCHIVE.md"}, changed_after_test
    all_names = set(filter(None, git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode("utf-8").split("\0")))
    new_after_test = sorted(n for n in all_names - {r["path"] for r in tested}
        if not n.startswith(("reports/codex/C3L3_evidence/", "reports/codex/H1_evidence/")))
    assert set(new_after_test) <= {"reports/codex/C3L3_report.md"}, new_after_test

    metadata = META | {"reports/codex/C3L3_evidence/deliverables.md"}
    # Establish the two forward-linked metadata files as explicitly incomplete.
    # Their verified contents are written below only after every check passes.
    for name in ("delivery_integrity.json", "hygiene.json"):
        if not (OUT / name).exists():
            dump(OUT / name, dict(status="IN_PROGRESS"))
    names = sorted(set(candidates()) | metadata)
    lines = ["# WO-C3L3 delivery index", "", "Only the current differential.json is authoritative.",
        "Implementation checks do not substitute for owner fresh-tree or Claude independent acceptance.", "",
        "## Files", ""]
    lines += [f"- [{n}]({(ROOT / n).as_uri()})" for n in names]
    lines += ["", "## Ignored working areas and append-only archive", "",
        f"- [Builds and isolated mutations]({(ROOT / 'eab2/build').as_uri()}/)",
        f"- [H1 byte exports, original logs and rollback copies]({(OUT / 'tmp').as_uri()}/)",
        "- [Append-only local archive](file:///D:/eab-evidence/reports/codex/C3L3_evidence/run_20261023/)",
        "- [Final tested byte-source ZIP](file:///D:/eab-evidence/reports/codex/C3L3_evidence/run_20261023/final_full_tested_source.zip)", ""]
    (OUT / "deliverables.md").write_text("\n".join(lines), encoding="utf-8")
    tracked = set(filter(None, git("ls-tree", "-r", "--name-only", BASE, "-z").decode("utf-8").split("\0")))
    rows, issues = [], []
    text_ext = {".py", ".cpp", ".hpp", ".h", ".c", ".bat", ".md", ".txt", ".json", ".log"}
    for name in names:
        path = ROOT / name
        if name in META:
            continue
        data = path.read_bytes()
        previous = git("show", f"{BASE}:{name}") if name in tracked else b""
        if path.suffix in text_ext:
            text = data.decode("utf-8")
            if data.startswith(b"\xef\xbb\xbf") or "\ufffd" in text:
                issues.append(dict(path=name, kind="encoding"))
            if b"\r\n" in data and data.count(b"\n") != data.count(b"\r\n"):
                issues.append(dict(path=name, kind="mixed_newlines"))
            if path.suffix == ".bat" and not data.isascii():
                issues.append(dict(path=name, kind="batch_not_ascii"))
        if len(data) > 1_000_000:
            issues.append(dict(path=name, kind="new_or_modified_file_over_1MB"))
        rows.append(dict(path=name, uri=path.as_uri(), tracked_at_base=name in tracked,
            base_bytes=len(previous), base_sha256=sha(previous) if name in tracked else None,
            bytes=len(data), sha256=sha(data), net_bytes=len(data) - len(previous)))
    assert not issues, issues
    dump(OUT / "artifact_manifest.json", dict(schema="eab2.c3l3.artifacts.v1", base_commit=BASE,
        rows=rows, digest_self_exclusions=sorted(META), note="Metadata self-exclusions avoid circular hashes; all delivery source/report/log files are listed."))

    missing_links = []
    for name in names:
        path = ROOT / name
        if path.suffix != ".md":
            continue
        # Audit new report/reviews/index and modified eab2 docs; historical archive links
        # before this work order remain outside the new-link responsibility.
        text = path.read_text("utf-8")
        old_links = set(re.findall(r"\]\(([^)]+)\)", git("show", f"{BASE}:{name}").decode("utf-8"))) if name in tracked else set()
        if name == "reports/EVIDENCE_ARCHIVE.md":
            text = text.split("## WO-C3L3", 1)[-1]
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if link in old_links:
                continue
            if link.startswith(("http:", "https:", "#", "mailto:")):
                continue
            link = unquote(link.split("#", 1)[0])
            target = Path(urlparse(link).path.lstrip("/")) if link.startswith("file:") else path.parent / link
            if not target.exists():
                missing_links.append(dict(source=name, link=link))
    assert not missing_links, missing_links
    archive = json.loads((OUT / "archive_manifest.json").read_text("utf-8"))
    for row in archive["files"]:
        assert sha(Path(row["archive"]).read_bytes()) == row["archive_sha256"]
    zipped = archive["tested_source_zip"]
    assert sha(Path(zipped["path"]).read_bytes()) == zipped["sha256"]
    dump(OUT / "delivery_integrity.json", dict(schema="eab2.c3l3.integrity.v1", status="PASS",
        checked_artifact_hashes=len(rows), missing_links=missing_links, encoding_issues=issues,
        tested_code_unchanged=True, post_test_changed_existing=changed_after_test,
        post_test_new_non_evidence=new_after_test, src_eab_and_opt_unchanged=True,
        design_sha256=sha((ROOT / "docs/eab2_design.md").read_bytes()),
        archive_hashes_verified=True, diff_dll_hash_verified=True,
        owner_fresh_git_checkout_performed=False, claude_independent_adversarial_review_performed=False,
        acceptance_status="PARTIAL_OWNER_GATES_PENDING"))
    hygiene = dict(schema="eab2.c3l3.hygiene.v1", base_commit=BASE, candidate_files=len(names),
        calculation="Current modified files plus nonignored new deliverables minus base blob bytes; not Git pack/history size",
        target_bytes=2_000_000, maximum_candidate_file_bytes=0, net_bytes=0,
        no_compiler_binaries_in_candidates=True, utf8_no_bom_and_uniform_newlines=True)
    for _ in range(4):
        dump(OUT / "hygiene.json", hygiene)
        total = sum((ROOT / n).stat().st_size for n in names)
        baseline = sum(r["base_bytes"] for r in rows)
        hygiene.update(current_candidate_bytes=total, base_candidate_bytes=baseline,
            maximum_candidate_file_bytes=max((ROOT / n).stat().st_size for n in names),
            net_bytes=total-baseline, target_met=total-baseline <= 2_000_000)
    dump(OUT / "hygiene.json", hygiene)
    assert hygiene["target_met"] and hygiene["maximum_candidate_file_bytes"] <= 1_000_000
    assert not any(Path(n).suffix.lower() in {".dll", ".exe", ".obj", ".lib", ".pdb"} for n in names)
    print(f"C3L3_DELIVERY_INTEGRITY_OK files={len(names)} net_bytes={hygiene['net_bytes']} links=OK tested_code=UNCHANGED")


if __name__ == "__main__":
    main()
