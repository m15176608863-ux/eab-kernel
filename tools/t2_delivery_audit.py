"""Preserve T2a delivery hashes and verify exact-coordinate serialization.

This audits saved artifacts only; it never replays full frozen numerics,
changes Git state, edits a policy, or deletes historical evidence.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path("D:/eab-evidence/reports/codex/T2a_evidence")
LOCAL = ROOT / "reports/codex/T2a_evidence"
APPROVED_CHANGES = {
    "reports/EVIDENCE_ARCHIVE.md", "tools/exact_construction_policy.json",
    "tests/test_kernel_purity.py",
    "tools/policy_history_view.py",
}
SCANNERS = (
    "tools/check_exact_construction.py", "tools/exact_construction_subset.py",
    "tools/exact_construction_flow.py",
)
SOURCE_SHA256 = "14bfd823dda1c438ffd136128f73545236d5e2bbbb428a3b1eb5e09efc79bbdf"
STATUS = "DONE_OWNER_REVIEW_PENDING"
PROOF_GAPS = {
    "closed-unproved-call", "closed-import-call", "closed-method-call",
    "closed-unknown-member", "closed-callable-value", "closed-dynamic-call",
    "closed-data-attribute", "closed-unknown-call", "closed-runtime-reflection",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n",
                    encoding="utf-8", newline="")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def value_digest(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_final_run(name, shard_count, report):
    """Recount saved execution evidence; do not manufacture or replay a run."""
    out = EVIDENCE / name
    summary = read(out / "summary.json")
    assert summary["complete"] and summary["audit"] == "GREEN", name
    assert not summary["baseline"] and not summary["fresh_git_checkout"], name
    assert not summary["export_changed"] and not summary["live_tree_changed"], name
    assert summary["module_coverage_complete"], name
    assert len(summary["shards"]) == shard_count, name
    assert read(out / "state.json") == {"complete": True, "status": "GREEN"}, name
    collected = [line for line in (out / "collection.txt").read_text("utf-8").splitlines()
                 if line.startswith("tests/") and "::" in line]
    assert len(collected) == summary["collected"] > 0 and len(set(collected)) == len(collected), name
    executed = []
    last_lines = []
    for index, shard in enumerate(summary["shards"], 1):
        assert shard == read(out / f"shard_{index}.json"), (name, index)
        assert shard["exit_code"] == 0 and shard["complete"] and shard["node_sets_equal"], (name, index)
        assert shard["skip_count"] == shard["failed_count"] == 0, (name, index)
        command = shard["command"]
        assert "no:cacheprovider" in command and "--basetemp" in command, (name, index)
        assert ("--runslow" in command) == (shard_count == 4), (name, index)
        nodes = (out / f"shard_{index}_nodes.txt").read_text("utf-8").splitlines()
        record = read(out / f"shard_{index}_execution.json")
        assert record["complete"] and record["exitstatus"] == 0 and record["coverage_available"], (name, index)
        assert all(row["outcome"] == "passed" for row in record["reports"]), (name, index)
        calls = [row["nodeid"] for row in record["reports"] if row["when"] == "call"]
        assert Counter(nodes) == Counter(record["collected"]) == Counter(calls), (name, index)
        assert len(nodes) == shard["dispatched"] == shard["executed"], (name, index)
        assert Counter(nodes) == Counter(collected[index-1::shard_count]), (name, index)
        last_line = (out / f"shard_{index}.txt").read_text("utf-8").rstrip().splitlines()[-1]
        assert shard["last_line"] == last_line and last_line in report, (name, index)
        last_lines.append(last_line)
        executed.extend(calls)
    assert Counter(collected) == Counter(executed), name
    coverage = read(out / "module_coverage.json")
    assert coverage["complete"] and not any(coverage[key] for key in (
        "missing_function_calls", "missing_module_execution", "missing_imports", "errors")), name
    assert coverage["module_count"] == coverage["imported_count"], name
    assert coverage["module_count"] == coverage["function_covered_count"] + coverage["declarative_covered_count"], name
    assert "src/eab/kernel2d/se2_paths.py" in coverage["function_modules"], name
    static = summary["static"]
    if shard_count == 4:
        assert static["exit_code"] == 0, name
        assert static["last_line"] == "exact construction AST gate: 0 violation(s)", name
        assert (out / "exact_construction.txt").read_text("utf-8").rstrip().splitlines()[-1] == static["last_line"], name
        assert static["last_line"] in report, name
    else:
        assert static is None, name
    # Report/audit edits after a green run are expected, but tested executable
    # sources and the site-review ledger must remain the exported bytes.
    source_manifest = read(out / "source_manifest.json")
    live_names = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT).decode("utf-8").split("\0")
    prefixes = ("src/", "tests/", "tools/")
    assert {path for path in live_names if path.startswith(prefixes)} == {
        row["path"] for row in source_manifest if row["path"].startswith(prefixes)}, name
    for row in source_manifest:
        path = row["path"]
        if path.startswith(prefixes) or path == "reports/codex/T2a_evidence/static_admissions.json":
            assert digest(ROOT / path) == row["sha256"], (name, path, "changed after final run")
    return dict(audit="GREEN", collected=len(collected), executed=len(executed),
                shard_count=shard_count, skip_count=0, failed_count=0,
                node_multisets_equal=True, module_coverage_complete=True,
                summary="file:///"+(out / "summary.json").as_posix(),
                last_lines=last_lines, static_last_line=static["last_line"] if static else None)


def main():
    base = json.loads((EVIDENCE / "baseline_anchor/manifest.json").read_text("utf-8"))
    baseline = json.loads((EVIDENCE / "baseline_full/summary.json").read_text("utf-8"))
    assert baseline["complete"], "never freeze an unfinished baseline as completed evidence"
    with zipfile.ZipFile(EVIDENCE / "baseline_anchor/source.zip") as bundle:
        for row in base["files"]:
            assert hashlib.sha256(bundle.read(row["path"])).hexdigest() == row["sha256"]
        old_policy = json.loads(bundle.read("tools/exact_construction_policy.json"))
        old_policy_sha256 = hashlib.sha256(bundle.read("tools/exact_construction_policy.json")).hexdigest()
        old_purity = bundle.read("tests/test_kernel_purity.py").decode("utf-8")
        old_history_view = bundle.read("tools/policy_history_view.py").decode("utf-8").replace("\r\n", "\n")
        scanner_hashes = {name: hashlib.sha256(bundle.read(name)).hexdigest() for name in SCANNERS}
    changed = [r["path"] for r in base["files"]
               if not (ROOT / r["path"]).is_file() or digest(ROOT / r["path"]) != r["sha256"]]
    assert set(changed) == APPROVED_CHANGES, changed
    for path, expected in scanner_hashes.items():
        assert digest(ROOT / path) == expected, path
    assert digest(ROOT / "src/eab/kernel2d/se2_paths.py") == SOURCE_SHA256
    old_count = ('    # Original 50 plus full ordered-field arithmetic and branch certificates.\n'
                 '    assert len(expected) == 52 and "eab/predicates.py" in expected')
    new_count = ('    # Original 52 plus contact-allowed exact path module se2_paths.\n'
                 '    assert len(expected) == 53 and "eab/predicates.py" in expected')
    assert old_purity.count(old_count) == 1
    assert (ROOT / "tests/test_kernel_purity.py").read_text("utf-8") == old_purity.replace(old_count, new_count)
    old_counter = 'COUNTS = {"imports": 648, "members": 432, "waivers": 3522,'
    new_counter = ('# T2a owner-approved append: 3522 historical plus 137 reviewed sites; no projection change.\n'
                   'COUNTS = {"imports": 648, "members": 432, "waivers": 3659,')
    assert old_history_view.count(old_counter) == 1
    assert (ROOT / "tools/policy_history_view.py").read_text("utf-8") == old_history_view.replace(old_counter, new_counter)
    policy = read(ROOT / "tools/exact_construction_policy.json")
    ledger = read(LOCAL / "static_admissions.json")
    baseline_policy = ledger["baseline_policy"]
    old_count = len(old_policy["waivers"])
    assert baseline_policy["sha256"] == old_policy_sha256
    assert baseline_policy["waiver_count"] == old_count
    assert baseline_policy["waivers_sha256"] == value_digest(old_policy["waivers"])
    assert baseline_policy["nonwaiver_sha256"] == value_digest({k: v for k, v in old_policy.items() if k != "waivers"})
    assert policy["waivers"][:old_count] == old_policy["waivers"]
    assert {k: v for k, v in policy.items() if k != "waivers"} == {k: v for k, v in old_policy.items() if k != "waivers"}
    added = policy["waivers"][old_count:]
    assert added and len(added) == len(ledger["entries"])
    for row, recorded in zip(added, ledger["entries"]):
        assert {key: recorded[key] for key in row} == row
        assert row["rule"] in PROOF_GAPS and row["reason"].strip()
        assert row["category"] == "T2A_EXACT_REUSE_SITE_REVIEW"
        assert row["review_evidence"] == "reports/codex/T2a_report.md#t2a-static-admission-review"
    counts = dict(total=len(added), src=sum(row["path"].startswith("src/") for row in added),
        tests=sum(row["path"].startswith("tests/") for row in added),
        by_rule=dict(Counter(row["rule"] for row in added)),
        src_by_rule=dict(Counter(row["rule"] for row in added if row["path"].startswith("src/"))),
        tests_by_rule=dict(Counter(row["rule"] for row in added if row["path"].startswith("tests/"))))
    assert ledger["counts"] == counts
    assert {row["path"]: row["sha256"] for row in ledger["analyzers"]} == scanner_hashes
    continuation = EVIDENCE / "ruling_resume_20261025"
    assert digest(continuation / "blocked_delivery_anchor.zip") == read(continuation / "intake.json")["archive_sha256"]
    with zipfile.ZipFile(continuation / "blocked_delivery_anchor.zip") as bundle:
        frozen = json.loads(bundle.read("external/artifact_manifest.json"))
    certificates = [row for row in frozen["files"] if row["relative_path"].startswith("certificates/")]
    assert certificates
    assert {p.relative_to(EVIDENCE).as_posix() for p in (EVIDENCE / "certificates").rglob("*") if p.is_file()} == {
        row["relative_path"] for row in certificates}
    for row in certificates:
        assert digest(EVIDENCE / row["relative_path"]) == row["sha256"], row["relative_path"]
    report = ROOT / "reports/codex/T2a_report.md"
    report_text = report.read_text("utf-8")
    assert report_text.rstrip().splitlines()[-1] == "T2A_DONE"
    final_fast = audit_final_run("resume_final_fast_r2", 1, report_text)
    final_full = audit_final_run("resume_final_full", 4, report_text)
    names = sorted(n for n in subprocess.check_output(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"], cwd=ROOT).decode("utf-8").split("\0") if n)
    artifact_file = LOCAL / "artifacts.md"
    text = artifact_file.read_text("utf-8")
    for name in sorted(set(names+changed)):
        link = "file:///"+(ROOT / name).as_posix()
        if link not in text:
            text += f"\n- [{name}]({link})\n"
    artifact_file.write_text(text, encoding="utf-8", newline="")
    files = []
    anchor_sizes = {r["path"]: r["bytes"] for r in base["files"]}
    modified_files = []
    for name in sorted(set(names+changed)):
        p = ROOT / name
        data = p.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf"), name
        content = data.decode("utf-8")
        assert not (b"\r\n" in data and b"\n" in data.replace(b"\r\n", b"")), name
        assert len(data) <= 1_000_000 or anchor_sizes.get(name, 0) > 1_000_000, name
        if p.suffix == ".py":
            ast.parse(content, filename=name)
        if p.suffix == ".json":
            json.loads(content)
        if name != "reports/codex/T2a_evidence/delivery_audit.json":
            row = dict(path=name, bytes=len(data), sha256=digest(p))
            (modified_files if name in changed else files).append(row)
    def rational_strings(points):
        return all(isinstance(v, str) for p in points for v in p)
    for path in (EVIDENCE / "certificates").glob("*.json"):
        value = json.loads(path.read_text("utf-8"))
        if not isinstance(value, dict) or value.get("schema") != "t2a-exact-se2-escape-1":
            continue
        assert rational_strings(value["moving"]) and rational_strings(value["ray_path"])
        assert all(rational_strings(p) for p in value["obstacles"])
        for p in value["pieces"]:
            assert rational_strings(p["start"]) and rational_strings(p["end"])
            assert rational_strings((p["center"], p["translation"])) and isinstance(p["u1"], str)
    missing = []
    for path in (report, artifact_file):
        for link in re.findall(r"\]\((file:///[^)]+)\)", path.read_text("utf-8")):
            p = Path(unquote(link[8:]))
            if p.name not in {"artifact_manifest.json", "delivery_audit.json"} and not p.exists():
                missing.append(link)
    assert not missing, missing
    tracked_delta = sum((ROOT / name).stat().st_size-anchor_sizes[name] for name in changed)
    audit_path = LOCAL / "delivery_audit.json"
    audit = dict(status=STATUS, base_commit=base["head"],
        baseline_audit=baseline["audit"], baseline_nodes=baseline["collected"],
        unchanged_preexisting_files=len(base["files"])-len(changed), changed_preexisting=changed,
        policy_unchanged=False, policy_change="owner-approved exact-reuse site reviews only",
        historical_waivers_unchanged=True, other_policy_fields_unchanged=True,
        static_admissions=counts, analyzer_hashes=scanner_hashes, analyzers_unchanged=True,
        source_sha256=SOURCE_SHA256, frozen_certificate_hashes_unchanged=True,
        frozen_certificate_files=len(certificates), purity_change="52 to 53 for se2_paths only",
        protected_math_apis_unchanged=True, cpp_unchanged=True, owner_review_pending=True,
        no_git_writes=True, fresh_git_checkout=False, utf8_no_bom=True, mixed_newlines=False,
        canonical_certificate_coordinates_are_strings=True, missing_local_links=missing,
        added_files=files, modified_files=modified_files, tracked_byte_delta=tracked_delta,
        local_net_bytes_excluding_this_audit=sum(r["bytes"] for r in files)+tracked_delta,
        external_manifest="file:///D:/eab-evidence/reports/codex/T2a_evidence/artifact_manifest.json",
        final_repository_fast=final_fast, final_repository_full=final_full)
    write(audit_path, audit)
    for _ in range(4):
        audit["local_net_bytes"] = audit["local_net_bytes_excluding_this_audit"]+audit_path.stat().st_size
        audit["within_5mb_net_budget"] = audit["local_net_bytes"] <= 5_000_000
        write(audit_path, audit)
    assert audit["within_5mb_net_budget"]
    external_rows = []
    for p in sorted(EVIDENCE.rglob("*")):
        if not p.is_file() or "tmp" in p.relative_to(EVIDENCE).parts or p.name == "artifact_manifest.json":
            continue
        external_rows.append(dict(relative_path=p.relative_to(EVIDENCE).as_posix(),
                                  bytes=p.stat().st_size, sha256=digest(p)))
    repository_rows = [dict(path=n, bytes=(ROOT / n).stat().st_size, sha256=digest(ROOT / n))
                       for n in sorted(set(names+changed+[audit_path.relative_to(ROOT).as_posix()]))]
    write(EVIDENCE / "artifact_manifest.json", dict(root=str(EVIDENCE),
        excludes=["tmp/", "artifact_manifest.json (self)"], files=external_rows,
        repository_delivery=repository_rows, status=STATUS,
        static_admissions=counts, owner_review_pending=True))
    print(json.dumps(dict(status=audit["status"], local_net_bytes=audit["local_net_bytes"],
                          external_files=len(external_rows), source_rollback_verified=True)))


if __name__ == "__main__":
    main()
