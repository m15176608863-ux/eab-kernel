"""Read-back audit after the repair report and append-only archive are complete.

This script does not run tests, rebuild, modify Git, or change historical evidence.
It writes only four repair delivery metadata files. PASS means delivery integrity;
acceptance remains PARTIAL pending Claude's repaired-critical re-review.
"""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[3]
PREFIX = "reports/codex/C3L3_repair_evidence/"
OUT = ROOT / PREFIX
TMP = OUT / "tmp"
BASE = "1b6b4f32ff3c5716f8e3a24ad73dd3cf6081f39c"
HEAD = "c8718bb0850328defd8f0cc16fb4f3a09e922975"
DESIGN_SHA256 = "6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac"
ARCHIVE_ROOT = Path("D:/eab-evidence/reports/codex/C3L3_evidence/acceptance_repair_20261023")
POST_TEST_REPORTS = {"reports/codex/C3L3_report.md", "reports/EVIDENCE_ARCHIVE.md"}
DELETED = {"reports/codex/C3L3_evidence/differential" + suffix
           for suffix in (".json", ".log", ".progress.json")}
META = {PREFIX + name for name in
        ("artifact_manifest.json", "delivery_integrity.json", "hygiene.json")}
GENERATED = META | {PREFIX + "deliverables.md"}
TEXT_EXT = {".py", ".cpp", ".hpp", ".h", ".c", ".bat", ".md", ".txt", ".json", ".log",
            ".yml", ".yaml", ".toml", ".ini", ".cfg", ".cmake", ".csv", ".jsonl"}
BINARY_EXT = {".dll", ".exe", ".obj", ".o", ".lib", ".a", ".pdb", ".exp", ".ilk", ".pch", ".pyc"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(Path(path).read_text("utf-8"))


def dump(path, value):
    Path(path).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def names(*args):
    return set(filter(None, git(*args, "-z").decode("utf-8").split("\0")))


def inside(root, name):
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), f"path escaped {root}: {name}")
    return path


def tree(commit):
    result = {}
    for entry in git("ls-tree", "-r", "-l", "-z", commit).split(b"\0"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            mode, kind, oid, size = metadata.decode("ascii").split()
            require(kind == "blob", f"unsupported tree entry: {entry!r}")
            result[name.decode("utf-8")] = dict(bytes=int(size), git_blob_oid=oid, mode=mode)
    return result


def live_names():
    return {n for n in names("ls-files", "--cached", "--others", "--exclude-standard")
            if inside(ROOT, n).is_file()}


def source_names():
    return {n for n in live_names() if not n.startswith((PREFIX, "reports/codex/H1_evidence/"))}


def changed_names(commit):
    return names("diff", "--name-only", commit) | names("ls-files", "--others", "--exclude-standard")


def verify_bytes(path, expected_sha, expected_bytes=None):
    data = Path(path).read_bytes()
    require(sha(data) == expected_sha, f"SHA mismatch: {path}")
    if expected_bytes is not None:
        require(len(data) == expected_bytes, f"size mismatch: {path}")
    return data


def audit_snapshot(manifest_path, snapshot, *, exact_snapshot_names):
    rows = load(manifest_path)
    by_name = {r["path"]: r for r in rows}
    require(len(rows) == len(by_name) and rows, f"duplicate/empty source manifest: {manifest_path}")
    for name, row in by_name.items():
        verify_bytes(inside(snapshot, name), row["sha256"], row["bytes"])
    if exact_snapshot_names:
        actual = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob("*") if p.is_file()}
        require(actual == set(by_name), f"tested byte export changed: {snapshot}")
    changed = sorted(n for n, r in by_name.items()
                     if not inside(ROOT, n).is_file() or sha((ROOT / n).read_bytes()) != r["sha256"])
    added = sorted(source_names() - set(by_name))
    require(set(changed) | set(added) <= POST_TEST_REPORTS,
            f"code/source changed after verification: {changed}, added={added}")
    return rows, dict(manifest_uri=manifest_path.as_uri(), manifest_sha256=sha(manifest_path.read_bytes()),
                      files=len(rows), changed_existing=changed, added_non_evidence=added,
                      allowed_report_changes=sorted(POST_TEST_REPORTS), code_unchanged=True)


def audit_h1(name, expected_shards):
    out, temp = OUT / name, TMP / name
    summary = load(out / "summary.json")
    require(summary["audit"] == "GREEN" and summary["complete"], f"{name} incomplete/RED")
    require(summary["module_coverage_complete"] and not summary["live_tree_changed"]
            and not summary["export_changed"], f"{name} changed source/incomplete coverage")
    require(len(summary["shards"]) == expected_shards, f"{name} wrong shard count")
    require(load(out / "state.json") == {"complete": True, "status": "GREEN"}, f"{name} invalid state")
    source = temp / "source"
    require(Path(summary["source"]).resolve() == source.resolve(), f"{name} source path")
    rows, snapshot = audit_snapshot(temp / "source_manifest.json", source, exact_snapshot_names=True)
    collection = [line for line in (temp / "collection.txt").read_text("utf-8").splitlines()
                  if line.startswith("tests/") and "::" in line]
    require(len(collection) == summary["collected"] == len(set(collection)), f"{name} collection")
    records, dispatched_all = [], []
    for i, shard in enumerate(summary["shards"], 1):
        require(shard == load(out / f"shard_{i}.json"), f"{name}/{i} summary disagrees")
        require(shard["exit_code"] == 0 and shard["complete"] and shard["node_sets_equal"]
                and shard["skip_count"] == shard["failed_count"] == 0, f"{name}/{i} not GREEN")
        command = shard["command"]
        require("no:cacheprovider" in command and "--basetemp" in command, f"{name}/{i} pytest contract")
        require(("--runslow" in command) == (expected_shards == 4), f"{name}/{i} slow contract")
        dispatched = (temp / f"shard_{i}_nodes.txt").read_text("utf-8").splitlines()
        record = load(temp / f"shard_{i}_execution.json")
        require(record["complete"] and record["exitstatus"] == 0 and record["coverage_available"],
                f"{name}/{i} journal incomplete")
        calls = [r["nodeid"] for r in record["reports"] if r["when"] == "call"]
        require(Counter(dispatched) == Counter(record["collected"]) == Counter(calls),
                f"{name}/{i} dispatched/collected/executed multiset mismatch")
        require(not any(r["outcome"] in {"failed", "skipped"} for r in record["reports"]),
                f"{name}/{i} failed/skipped journal report")
        require(shard["dispatched"] == shard["collected"] == shard["executed"] == len(calls),
                f"{name}/{i} counts")
        log = temp / f"shard_{i}.txt"
        require(Path(shard["log"]).resolve() == log.resolve(), f"{name}/{i} log path")
        require(log.read_text("utf-8").splitlines()[-1] == shard["last_line"], f"{name}/{i} last line")
        dispatched_all.extend(dispatched)
        records.append(record)
    require(Counter(collection) == Counter(dispatched_all), f"{name} global node multiset")
    # Recompute the existing execution-witness audit against the actual tested bytes.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("_c3l3_delivery_coverage", source / "tools/h1_module_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    coverage = module.audit_module_coverage(source, records)
    require(coverage["complete"] and coverage == load(out / "module_coverage.json"),
            f"{name} recomputed actual-execution coverage disagrees")
    if expected_shards == 4:
        static = summary["static"]
        require(static["exit_code"] == 0 and (temp / "exact_construction.txt").read_text("utf-8").splitlines()[-1]
                == static["last_line"], "full static-construction check")
    return rows, dict(audit="GREEN", collected=len(collection), shards=expected_shards,
                      node_multisets_recomputed=True, coverage_recomputed=True,
                      module_count=coverage["module_count"], snapshot=snapshot,
                      last_lines=[s["last_line"] for s in summary["shards"]])


def audit_previous(head_tree):
    path = OUT / "previous_archive.json"
    previous = load(path)
    require(previous["base_commit"] == HEAD and set(previous["removed_after_verified_archive"]) == DELETED,
            "previous archive anchor/deletion list")
    archive_root = Path(previous["archive_root"])
    require(archive_root.resolve() == (ARCHIVE_ROOT / "history_c8718bb").resolve(), "history archive root")
    require((archive_root / "archive_manifest.json").read_bytes() == path.read_bytes(),
            "history local/external manifest bytes disagree")
    mapping = {}
    for row in previous["files"]:
        name = row["original"]
        require(name in head_tree and name not in mapping, f"history unknown/duplicate source: {name}")
        archive = Path(row["archive"])
        require(archive.resolve().is_relative_to(archive_root.resolve()), f"history archive escape: {archive}")
        raw = gzip.decompress(verify_bytes(archive, row["archive_sha256"]))
        require(len(raw) == row["bytes"] and sha(raw) == row["sha256"]
                and raw == git("show", f"{HEAD}:{name}"), f"history archive did not preserve HEAD: {name}")
        if name in DELETED:
            require(not (ROOT / name).exists(), f"obsolete differential still present: {name}")
        elif name != "reports/codex/C3L3_report.md":
            require((ROOT / name).read_bytes() == raw, f"historical evidence rewritten: {name}")
        mapping[name] = row
    require(DELETED <= set(mapping), "deleted differential lacks archived predecessor")
    require(previous["new_authority"] == PREFIX + "differential.json.gz", "authority mapping")
    return mapping, dict(manifest_uri=path.as_uri(), manifest_sha256=sha(path.read_bytes()),
                         files=len(mapping), hashes_and_decompression_verified=True,
                         original_HEAD_bytes_verified=True, historical_evidence_not_relabelled=True)


def audit_archive(tested_rows):
    path = OUT / "archive_manifest.json"
    data = load(path)
    dest = ARCHIVE_ROOT / "final_runs"
    require(data["schema"] == "eab2.c3l3.repair_archive.v1" and data["append_only"]
            and data["no_input_removed"] and data["verified_decompression"], "repair archive contract")
    require((dest / "archive_manifest.json").read_bytes() == path.read_bytes(),
            "repair local/external archive manifests differ")
    originals = set()
    for row in data["files"]:
        require(row["original"] not in originals, "duplicate archived original")
        originals.add(row["original"])
        archive = Path(row["archive"])
        require(archive.resolve().is_relative_to(dest.resolve()), f"archive path escape: {archive}")
        packed = verify_bytes(archive, row["archive_sha256"], row["archive_bytes"])
        raw = gzip.decompress(packed)
        require(sha(raw) == row["sha256"] and len(raw) == row["bytes"], f"archive payload: {archive}")
        require(inside(ROOT, row["original"]).read_bytes() == raw, f"archived input changed: {row['original']}")
    required = {PREFIX + "tmp/complete_build_source_manifest.json", PREFIX + "tmp/differential.json",
                PREFIX + "tmp/final_full/source_manifest.json", PREFIX + "tmp/final_fast/source_manifest.json"}
    require(required <= originals, "archive missing authority/source manifests")
    zipped = data["tested_source_zip"]
    zip_path = Path(zipped["path"])
    require(zip_path.resolve() == (dest / "final_full_tested_source.zip").resolve(), "tested ZIP path")
    verify_bytes(zip_path, zipped["sha256"], zipped["bytes"])
    require(zipped["files"] == len(tested_rows) and zipped["fresh_git_checkout"] is False, "tested ZIP provenance")
    with zipfile.ZipFile(zip_path) as stream:
        require(len(stream.namelist()) == len(tested_rows)
                and set(stream.namelist()) == {r["path"] for r in tested_rows}, "tested ZIP members")
        for row in tested_rows:
            raw = stream.read(row["path"])
            require(len(raw) == row["bytes"] and sha(raw) == row["sha256"], f"tested ZIP payload: {row['path']}")
    return data, dict(manifest_uri=path.as_uri(), manifest_sha256=sha(path.read_bytes()), files=len(originals),
                      hashes_and_decompression_verified=True, tested_source_zip_verified=True,
                      tested_source_zip_uri=zip_path.as_uri(), local_archive_not_remote_backup=True)


def audit_differential(records):
    meta = load(OUT / "differential_archive.json")
    require(meta["authority"] == "differential.json.gz" and meta["verified_decompression"], "diff authority")
    path = OUT / meta["authority"]
    packed = verify_bytes(path, meta["compressed_sha256"], meta["compressed_bytes"])
    raw = gzip.decompress(packed)
    require(len(raw) == meta["bytes"] and sha(raw) == meta["sha256"], "differential decompression SHA")
    require(Path(meta["original_ignored_path"]).resolve() == (TMP / "differential.json").resolve()
            and (TMP / "differential.json").read_bytes() == raw, "differential ignored original mismatch")
    data = json.loads(raw)
    require(data["schema"] == "eab2.c3l3.differential.v1" and data["cpp_executed"]
            and data["source_pre_post_equal"] and not data["mismatches"], "differential invalid")
    counts = Counter(r["kind"] for r in data["queries"])
    families = Counter(r["family"] + "/" + r["kind"] for r in data["queries"])
    require(dict(counts) == data["counts"] and dict(families) == data["family_counts"], "differential counters")
    require(all(not r["differences"] for r in data["queries"]), "query differences present")
    require(counts["critical"] > 0 and counts["limit"] > 0, "empty differential family")
    for name, expected in data["source_sha256"].items():
        verify_bytes(inside(ROOT, name), expected)
    command = records["differential"]["command"]
    require(command[command.index("--family") + 1] == "all", "incomplete differential family selection")
    dll = Path(command[command.index("--dll") + 1])
    require(dll.resolve() == (TMP / "complete_build_source/eab2/build/eab2.dll").resolve(), "wrong differential DLL")
    verify_bytes(dll, data["dll_sha256"])
    last = f"C3L3_DIFF limit={counts['limit']} critical={counts['critical']} mismatch=0"
    require(data["last_line"] == meta["last_line"] == records["differential"]["last_line"] == last, "diff last line")
    log_raw = gzip.decompress((OUT / "differential.log.gz").read_bytes())
    require(log_raw == (TMP / "differential.log").read_bytes()
            and log_raw.decode("utf-8").splitlines()[-1] == last, "differential log authority")
    return dict(authority_uri=path.as_uri(), sha256=sha(raw), compressed_sha256=sha(packed),
                counts=dict(counts), family_counts=dict(families), mismatches=0,
                source_pre_post_equal=True, current_source_hashes_verified=True,
                dll_uri=dll.as_uri(), dll_sha256=data["dll_sha256"], last_line=last)


def audit_repair_red_gates(archive):
    mutations = load(OUT / "critical_mutations.json")
    require(mutations["passed"] and mutations["sources_unchanged"] and len(mutations["mutations"]) == 7,
            "seven critical mutations did not pass")
    require(mutations["baseline"]["run"]["returncode"] == 0, "mutation baseline not GREEN")
    for name, expected in mutations["source_sha256"].items():
        verify_bytes(Path(name), expected)
    for item in mutations["mutations"]:
        require(item["caught"] and item["build"]["returncode"] == 0 and item["run"]["returncode"] != 0
                and item["expected_semantic_assertion"] in item["run"]["final_line"], "mutation escaped intended assertion")
        require(Path(item["run"]["log"]).read_text("utf-8").splitlines()[-1] == item["run"]["final_line"],
                "mutation log changed")
    red = load(OUT / "continuation_dll_red_gates.json")
    require(red["checker_unchanged"] and red["all_rejected"] and len(red["rows"]) == 2,
            "two production-DLL false proofs not rejected")
    verify_bytes(ROOT / "tools/eab2_c3l3_diff.py", red["checker_sha256"])
    for row in red["rows"]:
        require(row["rejected"] and row["actual_exception_type"] == "ValueError"
                and row["actual_exception"] == row["expected_exception"] and not row["dispositions"],
                "false certificate admitted or rejected for a wrong reason")
        raw_path = Path(row["native_false_certificate_path"])
        verify_bytes(raw_path, row["native_false_certificate_sha256"], row["native_false_certificate_bytes"])
        verify_bytes(raw_path.parent / "eab2.dll", row["dll_sha256"])
    archived = {r["original"] for r in archive["files"]}
    queue = load(OUT / "continuation_dll_archive_queue.json")
    for row in queue["files"]:
        path = Path(row["path"])
        verify_bytes(path, row["sha256"], row["bytes"])
        require(path.relative_to(ROOT).as_posix() in archived, "DLL red-gate queue not completely archived")
    return dict(mutations=7, intended_assertions_verified=True, dll_false_proofs_rejected=2,
                final_checker_sha256=red["checker_sha256"], archive_queue_files=len(queue["files"]),
                mutation_last_line=mutations["final_line"], dll_red_gate_last_line=red["final_line"],
                independent_adversarial_review=False)


def audit_links(candidate_names, head_tree, previous):
    audited, archived = 0, []
    for name in sorted(candidate_names):
        path = ROOT / name
        if path.suffix.lower() != ".md" or not path.is_file():
            continue
        links = re.findall(r"\]\(([^)]+)\)", path.read_text("utf-8"))
        old = set(re.findall(r"\]\(([^)]+)\)", git("show", f"{HEAD}:{name}").decode("utf-8"))) if name in head_tree else set()
        for link in links:
            if name != "reports/codex/C3L3_report.md" and link in old:
                continue
            if link.startswith(("http:", "https:", "#", "mailto:")):
                continue
            value = unquote(link.split("#", 1)[0])
            target = (Path(urlsplit(value).path.lstrip("/")) if value.startswith("file:")
                      else path.parent / value).resolve()
            audited += 1
            if target.exists():
                continue
            relative = target.relative_to(ROOT.resolve()).as_posix() if target.is_relative_to(ROOT.resolve()) else None
            require(relative in DELETED and relative in previous, f"broken new/report link in {name}: {link}")
            archived.append(dict(source=name, historical_link=link, original=relative,
                                 resolved_archive_uri=Path(previous[relative]["archive"]).as_uri()))
    return dict(scope="Main report all links; other Markdown only links added since c8718bb. Historical unchanged links are not relabelled current.",
                checked_local_links=audited, missing_links=[], resolved_deleted_historical_links=archived)


def main():
    require(git("rev-parse", "HEAD").decode().strip() == HEAD, "wrong repair HEAD")
    require(git("branch", "--show-current").decode().strip() == "eab2-c3l3", "wrong work branch")
    require(git("config", "--get", "core.autocrlf").decode().strip() == "false", "autocrlf changed")
    subprocess.run(["git", "diff", "--check", HEAD], cwd=ROOT, check=True)
    base_tree, head_tree = tree(BASE), tree(HEAD)
    frozen = {n for n in head_tree if n.startswith(("src/eab/", "eab2/src/")) or n == "docs/eab2_design.md"}
    require(not ((changed_names(HEAD)) & frozen), "production/design modified since repair HEAD")
    require({n for n in live_names() if n.startswith(("src/eab/", "eab2/src/"))} == frozen - {"docs/eab2_design.md"},
            "production source added/deleted")
    for name in frozen:
        require((ROOT / name).read_bytes() == git("show", f"{HEAD}:{name}"), f"frozen source bytes differ: {name}")
    verify_bytes(ROOT / "docs/eab2_design.md", DESIGN_SHA256)
    # Historical documents and manifests are records of the earlier run, not editable current metadata.
    old_changes = {n for n in changed_names(HEAD) if n.startswith("reports/codex/C3L3_evidence/")}
    require(old_changes == DELETED, f"unexpected old-evidence edits: {old_changes}")
    previous, previous_audit = audit_previous(head_tree)
    require({n for n in changed_names(HEAD) if n in head_tree and not (ROOT / n).is_file()} == DELETED,
            "unexpected tracked deletion")

    progress, records_list = load(OUT / "progress.json"), load(OUT / "verification_runs.json")
    require(progress["complete"] and progress["live_source_pre_post_equal"]
            and progress["fresh_git_checkout"] is False and progress["records"] == records_list, "final sequence incomplete")
    order = ["complete_build", "cpp_statics", "cpp_critical", "cpp_c3l3_abi", "delivery_audit",
             "differential", "final_fast", "final_full"]
    require([r["name"] for r in records_list] == order, "final sequence run order")
    for record in records_list:
        require(record["returncode"] == 0, f"failed final run: {record['name']}")
        log = verify_bytes(Path(record["log"]), record["sha256"])
        require(log.decode("utf-8").splitlines()[-1] == record["last_line"], f"changed last line: {record['name']}")
    records = {r["name"]: r for r in records_list}
    _, build_snapshot = audit_snapshot(TMP / "complete_build_source_manifest.json", TMP / "complete_build_source",
                                       exact_snapshot_names=False)
    delivery = load(OUT / "delivery_audit.json")
    require(delivery["status"] == "PASS" and not delivery["findings"], "compiled delivery audit failed")
    differential = audit_differential(records)
    _, fast = audit_h1("final_fast", 1)
    tested_rows, full = audit_h1("final_full", 4)
    archive, archive_audit = audit_archive(tested_rows)
    red_gates = audit_repair_red_gates(archive)
    intake = load(OUT / "intake.json")
    provenance = intake["baseline_provenance"]
    require(intake["base_commit"] == HEAD and intake["entry_clean"], "repair intake provenance")
    require(provenance["owner_reported_full_count"] == 15056 and provenance["new_opening_full_run"] is False,
            "owner fresh c8718bb baseline provenance changed")
    require((OUT / provenance["owner_reported_fresh_c8718bb"]).is_file(), "missing owner acceptance record")
    report = (ROOT / "reports/codex/C3L3_report.md").read_text("utf-8")
    require(report.rstrip().splitlines()[-1].startswith("C3L3_PARTIAL"), "report must remain PARTIAL pending Claude")

    candidates = changed_names(BASE) | changed_names(HEAD) | GENERATED
    existing = sorted(n for n in candidates if (ROOT / n).is_file() or n in GENERATED)
    deleted = sorted(n for n in candidates if n not in existing)
    require(set(deleted) == DELETED, f"unexpected absent candidate: {deleted}")
    for name in META:
        dump(ROOT / name, dict(status="IN_PROGRESS", acceptance_status="PARTIAL_CRITICAL_REVIEW_PENDING"))
    lines = ["# WO-C3L3 返修交付清单", "", "本轮差分唯一权威为 differential.json.gz；旧证据保留历史身份。",
             "完整性 PASS 不等于验收通过：C3L3_PARTIAL，等待 Claude 对 critical 修复复验。",
             "所有者已提供 c8718bb 新鲜树全档证据；本轮使用受检字节副本，不冒称新的 Git 新鲜树。", "", "## 文件", ""]
    lines += [f"- [{n}]({(ROOT / n).as_uri()})" for n in existing]
    lines += ["", "## 已验证归档后删除的旧差分", ""]
    lines += [f"- [{n}（历史归档）]({Path(previous[n]['archive']).as_uri()})" for n in deleted]
    lines += ["", "## ignored 运行副本与本地追加归档", "",
              f"- [完整构建与 H1 字节副本、日志]({TMP.as_uri()}/)",
              f"- [本轮外归档]({(ARCHIVE_ROOT / 'final_runs').as_uri()}/)",
              f"- [全档受检源 ZIP]({Path(archive['tested_source_zip']['path']).as_uri()})", ""]
    (OUT / "deliverables.md").write_bytes("\n".join(lines).encode("utf-8"))
    rows = []
    for name in sorted(candidates - META):
        path = ROOT / name
        data = path.read_bytes() if path.is_file() else None
        refs = {commit: dict(table.get(name, dict(bytes=0, git_blob_oid=None)))
                for commit, table in ((BASE, base_tree), (HEAD, head_tree))}
        rows.append(dict(path=name, uri=path.as_uri() if data is not None else Path(previous[name]["archive"]).as_uri(),
                         disposition="current" if data is not None else "deleted_after_verified_archive",
                         bytes=len(data) if data is not None else 0, sha256=sha(data) if data is not None else None,
                         baselines=refs, net_bytes={k: (len(data) if data is not None else 0) - v["bytes"] for k, v in refs.items()}))
    dump(OUT / "artifact_manifest.json", dict(schema="eab2.c3l3.repair_artifacts.v1", base_commit=BASE,
        repair_head=HEAD, rows=rows, digest_self_exclusions=sorted(META),
        note="Three metadata files exclude their own circular digests, but are included in byte/encoding/size audits. Deleted history is counted negatively and resolved to verified archives."))
    links = audit_links(set(existing), head_tree, previous)
    integrity = dict(schema="eab2.c3l3.repair_integrity.v1", status="PASS", acceptance_status="PARTIAL_CRITICAL_REVIEW_PENDING",
        base_commit=BASE, repair_head=HEAD, checked_artifact_hashes=len(rows), frozen_production_files=len(frozen),
        src_eab_eab2_src_and_design_unchanged_from_HEAD=True, design_sha256=DESIGN_SHA256,
        complete_build_source=build_snapshot, final_fast=fast, final_full=full, differential=differential,
        archive=archive_audit, previous_archive=previous_audit, links=links, repair_red_gates=red_gates,
        verification_last_lines={k: r["last_line"] for k, r in records.items()},
        owner_fresh_c8718bb_full_reported=True, owner_fresh_c8718bb_evidence_uri=(OUT / provenance["owner_reported_fresh_c8718bb"]).as_uri(),
        owner_fresh_c8718bb_reported_test_count=15056, repair_fresh_git_checkout_performed=False,
        repaired_critical_claude_re_review_performed=False,
        acceptance_note="Owner c8718bb fresh-tree baseline and prior statics closure are historical facts; this repair audit is not Claude's new critical acceptance.")
    dump(OUT / "delivery_integrity.json", integrity)
    hygiene = dict(schema="eab2.c3l3.repair_hygiene.v1", status="PASS", base_commit=BASE, repair_head=HEAD,
        calculation="Current modified/new nonignored candidate bytes minus baseline blob bytes, including verified deletions; not Git history/pack size.",
        candidate_files=len(candidates), current_files=len(existing), deleted_files=deleted,
        maximum_file_limit_bytes=1_000_000, overall_net_limit_bytes=2_000_000,
        utf8_no_bom_and_consistent_per_file_newlines=True, batch_ascii=True, no_compiler_binaries_in_candidates=True,
        git_diff_check=True, totals={})
    # Fixed point includes the byte sizes of all three metadata files, including this one.
    for _ in range(20):
        dump(OUT / "hygiene.json", hygiene)
        current = sum((ROOT / n).stat().st_size for n in existing)
        totals = {commit: dict(current_candidate_bytes=current,
                               base_candidate_bytes=sum(table.get(n, {}).get("bytes", 0) for n in candidates),
                               net_bytes=current - sum(table.get(n, {}).get("bytes", 0) for n in candidates))
                  for commit, table in ((BASE, base_tree), (HEAD, head_tree))}
        maximum = max((ROOT / n).stat().st_size for n in existing)
        if hygiene["totals"] == totals and hygiene.get("maximum_candidate_file_bytes") == maximum:
            break
        hygiene.update(totals=totals, maximum_candidate_file_bytes=maximum)
    else:
        raise ValueError("metadata byte-size fixed point did not converge")
    require(totals[BASE]["net_bytes"] <= 2_000_000 and maximum <= 1_000_000, "delivery byte-size budget exceeded")
    for name in existing:
        path = ROOT / name
        data = path.read_bytes()
        require(path.suffix.lower() not in BINARY_EXT, f"compiled artifact candidate: {name}")
        if path.suffix.lower() in TEXT_EXT or path.name in {".gitattributes", ".gitignore"}:
            text = data.decode("utf-8")
            require(not data.startswith(b"\xef\xbb\xbf") and "\ufffd" not in text, f"UTF-8/BOM issue: {name}")
            require(b"\r" not in data.replace(b"\r\n", b"")
                    and (b"\r\n" not in data or data.count(b"\n") == data.count(b"\r\n")), f"mixed/CR-only newline: {name}")
            require(path.suffix.lower() != ".bat" or data.isascii(), f"non-ASCII batch: {name}")
    require(changed_names(BASE) | changed_names(HEAD) | GENERATED == candidates, "candidate set changed during audit")
    for row in rows:
        if row["sha256"] is not None:
            verify_bytes(ROOT / row["path"], row["sha256"], row["bytes"])
    subprocess.run(["git", "diff", "--check", HEAD], cwd=ROOT, check=True)
    print(f"C3L3_REPAIR_DELIVERY_INTEGRITY_OK files={len(candidates)} net_bytes={totals[BASE]['net_bytes']} "
          f"repair_net_bytes={totals[HEAD]['net_bytes']} links=OK tested_code=UNCHANGED status=PARTIAL")


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        # Never leave a premature metadata PASS after a failed terminal hygiene check.
        for leaf in ("delivery_integrity.json", "hygiene.json"):
            dump(OUT / leaf, dict(status="FAIL", error=type(error).__name__ + ": " + str(error),
                                 acceptance_status="PARTIAL_CRITICAL_REVIEW_PENDING"))
        raise
