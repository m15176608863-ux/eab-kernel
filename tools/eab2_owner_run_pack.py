"""Read-only, bounded evidence index for an owner's possibly unfinished run.

No solver or build is launched. Exit codes come only from summary.txt (or an
explicit JSON exit_code), never from a reassuring log line. Large inputs stay
in place; their sizes and SHA-256 bind this snapshot, not future appended bytes.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

from eab2_c3l4_errata import build_ledger, write_ledger

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OLD = ROOT / "reports/codex/C3L4_evidence/differential/l4.json.gz"
LAYERS = ("build", "c0diff", "c1diff", "optdiff", "l1diff", "l3diff",
          "relabi", "consumer", "meta", "l4diff", "python_full")
L4_SHARDS = ("l4_formal", "l4_t1b", "l4_thickness", "l4_branch",
             *(f"l4_asym{i}" for i in range(6)))
LIMIT = 300_000


def decode(raw):
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def read_snapshot(path):
    """Hash exactly the bytes indexed, flag concurrent append/replacement."""
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    return raw, dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                     stable_during_read=(before.st_size, before.st_mtime_ns) ==
                     (after.st_size, after.st_mtime_ns) and len(raw) == after.st_size)


def last_line(raw):
    return next((line for line in reversed(decode(raw).splitlines()) if line.strip()), "")


def compact_records(value):
    """Keep small fields verbatim, index oversized diagnostics without hiding counts."""
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) <= 8_000:
        return value
    kinds = Counter()
    if isinstance(value, list):
        for row in value:
            if isinstance(row, dict):
                kinds[str(row.get("kind", row.get("classification", row.get("reason", "record"))))] += 1
    return dict(count=len(value), detail="source JSON; not copied (size budget)",
                canonical_sha256=hashlib.sha256(encoded).hexdigest(), by_kind=dict(kinds))


def json_extract(data):
    result = {}
    # Retain scalar counters and named statistical maps, not per-query payloads.
    for key, value in data.items():
        if (not isinstance(value, (dict, list)) or key.endswith(("_counts", "_count"))
                or key in {"counts", "coverage", "branch_certificate_statistics"}):
            result[key] = value
        if isinstance(value, list):
            result[key + "_count"] = len(value)
    for key in ("mismatches", "errata", "failures", "findings"):
        if key in data:
            result[key] = compact_records(data[key])
    return result



def catalog():
    """List source identities only: never import a harness or execute a solver.

    Frozen formal primal metadata determines the asymmetric source filter;
    query repetitions are not extra cases. Source-AST guards fail closed when
    the few generator declarations replicated here change.
    """
    sources = {}

    def read(relative):
        path = ROOT / relative
        raw, metadata = read_snapshot(path)
        if not metadata["stable_during_read"]:
            raise ValueError("catalog changed during read: " + relative)
        sources[relative] = metadata["sha256"]
        return raw

    def tree(relative):
        return ast.parse(decode(read(relative)))

    def assignments(node, names):
        return {target.id: item.value for item in ast.walk(node) if isinstance(item, ast.Assign)
                for target in item.targets if isinstance(target, ast.Name) and target.id in names}

    asym = next(n for n in tree("tools/eab2_c3l4_asymmetric.py").body
                if isinstance(n, ast.FunctionDef) and n.name == "asymmetric_cases")
    expected = ast.parse('''threshold = bool(base and base["result"]["exact_threshold"] is not None)
finite = bool(limit_base and limit_base["result"].get("mathematical_status") == "OPTIMAL"
              and limit_base["result"].get("exact_value") is not None
              and raw_points(source["model"]) and source["contacts"]["constraints"])
name = "asymmetric/" + source["case_id"]
''')
    a, b = assignments(asym, {"threshold", "finite", "name"}), assignments(expected, {"threshold", "finite", "name"})
    if {k: ast.dump(v) for k, v in a.items()} != {k: ast.dump(v) for k, v in b.items()}:
        raise ValueError("asymmetric catalog predicate changed; review inventory")
    calls = [n.func.id for n in ast.walk(asym) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id.endswith("_cases")]
    if calls != ["formal_cases", "t1b_cases", "t1b_cases"]:
        raise ValueError("asymmetric source families changed; review inventory")
    formal = ROOT / "fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64"
    manifest = json.loads(read((formal / "manifest.json").relative_to(ROOT).as_posix()))
    cases, asymmetric = {}, set()
    for entry in manifest["cases"]:
        identity = entry["case_id"]
        if identity in cases:
            raise ValueError("duplicate formal catalog identity")
        cases[identity] = "formal"
        for part in entry["parts"]:
            raw = gzip.decompress((formal / (part["path"] + ".gz")).read_bytes())
            if len(raw) != part["bytes"] or hashlib.sha256(raw).hexdigest() != part["sha256"]:
                raise ValueError("formal catalog integrity: " + part["path"])
            record = json.loads(raw)
            if record["case_id"] != identity:
                raise ValueError("formal catalog fragment identity")
            threshold = finite = contacts = False
            for query in record["queries"]:
                value = query["result"]
                if query["kind"] == "critical" and value.get("exact_threshold") is not None:
                    threshold = True
                if (query["kind"] == "limit" and value.get("mathematical_status") == "OPTIMAL"
                        and value.get("exact_value") is not None):
                    finite = True
                if query["kind"] == "assembly" and value.get("constraints"):
                    contacts = True
            # Same rule as asymmetric_cases: a threshold source always joins; a
            # finite-capacity source joins only with contact primitives.
            if threshold or (finite and contacts):
                asymmetric.add(identity)
    frozen = json.loads(read("tests/data/eab2_c3l4_t1b_expected.json"))
    for i, row in enumerate(frozen["rows"]):
        identity = f"t1b/{i:02d}"
        cases[identity] = "t1b"
        if row["mu_exact"] is not None:
            asymmetric.add(identity)
    thickness = assignments(tree("tools/eab2_c3l3_thickness.py"), {"SAMPLE_NAMES"})
    summary = json.loads(read("tests/data/eab2_c3l3_thickness_summary.json"))
    for name in ast.literal_eval(thickness["SAMPLE_NAMES"]):
        identity = "thickness/sample/" + name.removesuffix(".json.gz")
        cases[identity] = "thickness"
        asymmetric.add(identity)
    for i in range(len(summary["thick_controls"])):
        identity = f"thickness/control/{i:02d}"
        cases[identity] = "thickness"
        asymmetric.add(identity)
    branch = next(n for n in tree("tools/eab2_c3l4_branches.py").body
                  if isinstance(n, ast.FunctionDef) and n.name == "branch_cases")
    names = [ast.dump(n.value) for n in ast.walk(branch) if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "name" for t in n.targets)]
    expected_names = ['"branch/closed_singleton_t1b03"', '"branch/open_" + str(tilt)',
                      '"branch/two_closed" if closed else "branch/two_open"']
    first_loop = next(n for n in branch.body if isinstance(n, ast.For))
    if (sorted(names) != sorted(ast.dump(ast.parse(n, mode="eval").body) for n in expected_names)
            or ast.dump(first_loop.iter) != ast.dump(ast.parse("((Q(1, 4), (2,)), (Q(1, 8), (1, 2, 3, 4, 0)))", mode="eval").body)):
        raise ValueError("branch catalog declarations changed; review inventory")
    for name in ("open_1/4", "open_1/8", "two_closed", "two_open", "closed_singleton_t1b03"):
        cases["branch/" + name] = "branch"
    cases.update({"asymmetric/" + name: "asymmetric" for name in asymmetric})
    return cases, dict(source_sha256=sources, family_case_counts=dict(Counter(cases.values())),
                       expected_case_count=len(cases), expected_case_ids=sorted(cases),
                       basis="read-only frozen inventory and guarded generator declarations; no solver run")


def merge_counts(target, source):
    if not isinstance(target, dict) or not isinstance(source, dict):
        raise ValueError("L4 statistics must be nested integer maps")
    for key, value in source.items():
        if isinstance(value, dict):
            merge_counts(target.setdefault(key, {}), value)
        elif isinstance(value, int) and not isinstance(value, bool):
            if not isinstance(target.get(key, 0), int):
                raise ValueError("conflicting L4 statistic types: " + key)
            target[key] = target.get(key, 0) + value
        else:
            raise ValueError("non-integer L4 statistics: " + key)


def merge_l4(manifest, parsed):
    """Merge validated artifacts without mistaking them for process exit evidence."""
    expected, inventory = catalog()
    files, layers = manifest["files"], manifest["layers"]
    merged = dict(queries=[], mismatches=[], errata=[], family_counts={},
                  differentiability_counts={}, branch_certificate_statistics={})
    owners, query_keys, errors = {}, set(), []
    proof_records = 0
    identities = {data["dll_sha256"] for n, data in parsed.items()
                  if n in L4_SHARDS and isinstance(data.get("dll_sha256"), str) and data["dll_sha256"]}
    if len(identities) > 1:
        errors.append("L4 shards name different DLL hashes")
    unknown = sorted(n for n in parsed if n.startswith("l4_") and n not in L4_SHARDS)
    if unknown:
        errors.append("unexpected L4 shards: " + repr(unknown))
    for name in L4_SHARDS:
        data = parsed.get(name, {})
        if data.get("complete") is True:
            if (data.get("format") != "eab2.c3l4.differential.v1"
                    or data.get("cpp_executed") is not True
                    or data.get("source_pre_post_equal") is not True
                    or not isinstance(data.get("dll_sha256"), str)
                    or re.fullmatch(r"[0-9a-fA-F]{64}", data.get("dll_sha256", "")) is None):
                errors.append(name + ": invalid completed L4 schema/source/DLL binding")
            for field in ("mismatches", "errata", "family_counts", "differentiability_counts", "branch_certificate_statistics"):
                if field not in data:
                    errors.append(name + ": completed L4 lacks " + field)
        queries = data.get("queries", [])
        if not isinstance(queries, list):
            errors.append(name + ": queries is not an array")
            continue
        present = set()
        for row in queries:
            if not isinstance(row, dict) or not isinstance(row.get("case_id"), str):
                errors.append(name + ": query lacks case_id")
                continue
            case = row["case_id"]
            if not isinstance(row.get("query_index"), int) or not isinstance(row.get("parameter"), str):
                errors.append(name + ": query lacks index/parameter")
                continue
            key = (case, row.get("query_index"), row.get("parameter"))
            if key in query_keys:
                errors.append("duplicate query: " + repr(key))
            query_keys.add(key)
            present.add(case)
            group = "asymmetric" if name.startswith("l4_asym") else name.removeprefix("l4_")
            if expected.get(case) != group:
                errors.append(name + ": unknown/wrong-family case " + case)
        for case in present:
            if case in owners:
                errors.append("duplicate case across shards: " + case)
            owners[case] = name
        if layers[name]["json_snapshot_ready"] and not name.startswith("l4_asym"):
            missing = sorted(case for case, family in expected.items()
                             if family == name.removeprefix("l4_") and case not in present)
            if missing:
                errors.append(name + ": missing cases " + repr(missing))
        for field, row_key in (("family_counts", "family"), ("differentiability_counts", "differentiability")):
            if field in data:
                declared = data[field]
                observed = dict(Counter(row.get(row_key) for row in queries if isinstance(row, dict)))
                if not isinstance(declared, dict) or {k: v for k, v in declared.items() if v} != observed:
                    errors.append(name + ": " + field + " does not match query rows")
        proof = data.get("branch_proof_archive", {})
        if not isinstance(proof, dict) or not isinstance(proof.get("records", 0), int):
            errors.append(name + ": invalid proof record count")
        else:
            proof_records += proof.get("records", 0)
        merged["queries"].extend(queries)
        for field in ("mismatches", "errata"):
            value = data.get(field, [])
            if not isinstance(value, list):
                errors.append(name + ": " + field + " is not an array")
            else:
                merged[field].extend(value)
        for field in ("family_counts", "differentiability_counts", "branch_certificate_statistics"):
            try:
                merge_counts(merged[field], data.get(field, {}))
            except (ValueError, AttributeError) as error:
                errors.append(name + ": " + str(error))
    all_complete = all(layers[name]["status"] == "complete" for name in L4_SHARDS)
    artifacts_ready = all(layers[name]["json_snapshot_ready"] for name in L4_SHARDS)
    missing = sorted(set(expected) - set(owners))
    if artifacts_ready and missing:
        errors.append("full L4 missing cases: " + repr(missing))
    status = ("failed" if errors or any(layers[n]["status"] == "failed" for n in L4_SHARDS)
              else "complete" if all_complete else "pending")
    merged["case_count"], merged["shard_count"] = len(owners), len(L4_SHARDS)
    merged["branch_proof_records"] = proof_records
    artifact_complete = artifacts_ready and not errors
    merged["complete"] = artifact_complete
    merged["last_line"] = (f"L4_SHARD_AGGREGATE status={status} shards={len(L4_SHARDS)} "
                           f"cases={len(owners)}/{len(expected)} sensitivity={len(merged['queries'])} "
                           f"mismatch={len(merged['mismatches'])}")
    codes = [layers[name]["exit_code"] for name in L4_SHARDS]
    process_status = ("failed" if any(code is not None and code != 0 for code in codes)
                      else "complete" if all(code == 0 for code in codes) else "pending")
    manifest["l4_aggregate"] = dict(status=status, artifact_complete=artifact_complete,
        process_exit_status=process_status, inventory=inventory,
        input_files=[n + ".json" for n in L4_SHARDS if n + ".json" in files],
        missing_shards=[n for n in L4_SHARDS if not layers[n]["json_snapshot_ready"]],
        unconfirmed_exit_shards=[n for n in L4_SHARDS if layers[n]["exit_code"] is None],
        observed_case_count=len(owners), missing_case_ids=missing, validation_errors=errors,
        totals=json_extract(merged), note="complete stable artifacts can generate comparison errata while process exits remain unconfirmed; aggregate last_line is not a process log")
    layers["l4diff"] = dict(status=status, exit_code=None, json_last_line=merged["last_line"],
                            log_last_line=None, counts=manifest["l4_aggregate"]["totals"],
                            exit_code_basis="per-shard explicit exits; no synthetic aggregate exit code")
    return merged, artifact_complete


def pack(source, output, old=DEFAULT_OLD, source_commit="not_supplied"):
    source, output, old = Path(source).resolve(), Path(output).resolve(), Path(old).resolve()
    if not source.is_dir():
        raise ValueError("source must be an existing output directory")
    if output == source or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("source and output must be disjoint (read-only input)")
    output.mkdir(parents=True, exist_ok=True)
    manifest = dict(schema="eab2.owner_run_manifest.v1", source_directory=str(source),
                    source_commit=source_commit, source_commit_basis="caller supplied; not independently verified",
                    captured_utc=datetime.now(timezone.utc).isoformat(),
                    scope="top-level layer logs/JSON and summary.txt; temporary files and proof payloads stay at source",
                    acceptance="pending_owner_acceptance", files={}, layers={}, dll_sha256={},
                    package_limit_bytes=LIMIT)
    exits = {}
    summary = source / "summary.txt"
    if summary.is_file():
        raw, metadata = read_snapshot(summary)
        content = decode(raw)
        manifest["summary"] = dict(**metadata, text=content)
        for name, code in re.findall(r"(?m)^([A-Za-z0-9_]+)_EXIT\s+(-?\d+)\s*$", content):
            if name.lower() != "l4job":  # Owner job PID lines are not named shard exits.
                exits[name.lower()] = int(code)
    else:
        manifest["summary"] = dict(status="pending", text="")
    sharded = any(source.glob("l4_*.json")) or any(source.glob("l4_*.log"))
    names = set(LAYERS) | set(exits) | (set(L4_SHARDS) if sharded else set())
    parsed = {}
    for path in sorted(source.iterdir()):
        if not path.is_file() or path.suffix not in {".log", ".err", ".json"}:
            continue
        raw, metadata = read_snapshot(path)
        manifest["files"][path.name] = metadata
        name = path.stem.removesuffix(".progress").removesuffix("_progress")
        names.add(name)
        if path.suffix in {".log", ".err"}:
            metadata["last_line"] = last_line(raw)
        else:
            try:
                data = json.loads(decode(raw))
                if not isinstance(data, dict):
                    raise ValueError("expected JSON object")
            except (ValueError, UnicodeError) as error:
                metadata["parse_error"] = str(error)
                continue
            metadata["extracted"] = json_extract(data)
            if path.name.endswith((".progress.json", "_progress.json")):
                metadata["role"] = "progress_only_not_final"
            else:
                parsed[name] = data
            if data.get("dll_sha256"):
                manifest["dll_sha256"][path.name] = data["dll_sha256"]
    for name in sorted(names):
        data = parsed.get(name, {})
        code = exits.get(name, data.get("exit_code"))
        # An existing file is not evidence that the owner process has finished.
        log = manifest["files"].get(name + ".log", {})
        info = manifest["files"].get(name + ".json", {})
        unstable = any(not item.get("stable_during_read", True) for item in (log, info, manifest["summary"]))
        # Every known data layer needs its final JSON, and build needs its log.
        # A summary exit by itself cannot establish which artifact was produced.
        missing = (not log if name == "build" else not log and name not in parsed
                   if name.startswith("python") else name not in parsed)
        invalid = (bool(info.get("parse_error")) or data.get("complete") is False or missing
                   or (name == "l4diff" or name in L4_SHARDS) and not isinstance(data.get("queries"), list)
                   or name in L4_SHARDS and data.get("complete") is not True)
        issues = any(data.get(key) for key in ("mismatches", "mismatch_count", "failures", "findings"))
        failed = (code is not None and code != 0) or issues or data.get("status") == "FAIL" or data.get("source_pre_post_equal") is False
        status = "failed" if failed else "pending" if code is None or unstable or invalid else "complete"
        manifest["layers"][name] = dict(status=status, exit_code=code,
            log_last_line=log.get("last_line"), json_last_line=data.get("last_line"),
            counts={k: v for k, v in info.get("extracted", {}).items()
                    if k.endswith(("_count", "_counts")) or k in {"counts", "selected", "completed", "selected_cases", "completed_cases"}})
        if name in L4_SHARDS:
            manifest["layers"][name]["json_snapshot_ready"] = not (invalid or unstable or failed)
    l4 = manifest["layers"]["l4diff"]
    l4_data = parsed.get("l4diff", {})
    ledger_ready = (l4["exit_code"] is not None and l4_data.get("complete") is not False
                    and isinstance(l4_data.get("queries"), list)
                    and manifest["files"].get("l4diff.json", {}).get("stable_during_read", False)
                    and manifest["summary"].get("stable_during_read", True))
    if sharded:
        l4_data, ledger_ready = merge_l4(manifest, parsed)
        if "l4diff" in parsed:
            manifest["l4_aggregate"]["ignored_monolithic"] = "l4diff.json present; shards take precedence, never double counted"
    ledger_names = ("errata_ledger.json", "errata_ledger.md", "errata_ledger.json.gz", "errata_ledger.md.gz")
    if not ledger_ready and any((output / name).exists() for name in ledger_names):
        raise ValueError("pending snapshot cannot reuse an output with an older errata ledger; use a new output directory")
    if ledger_ready:
        old_raw, old_metadata = read_snapshot(old)
        if not old_metadata["stable_during_read"]:
            raise ValueError("accepted old L4 changed while reading")
        old_data = json.loads(decode(gzip.decompress(old_raw) if old.suffix == ".gz" else old_raw))
        # Use the exact already-hashed L4 bytes, never reopen a live owner's JSON.
        ledger = build_ledger(old_data, l4_data, old_run=old, new_run=source / ("l4_*.json (merged hashed snapshots)" if sharded else "l4diff.json"))
        write_ledger(ledger, output / "errata_ledger.json", output / "errata_ledger.md")
        manifest["accepted_l4"] = dict(path=str(old), **old_metadata)
        # Use reversible gzip for potentially hundreds of full per-query rows.
        # Both JSON and Markdown remain available; no comparison is summarised away.
        ledger_files = {}
        for name in ledger_names[:2]:
            path = output / name
            raw = path.read_bytes()
            compressed = path.with_suffix(path.suffix + ".gz")
            compressed.write_bytes(gzip.compress(raw, mtime=0))
            if gzip.decompress(compressed.read_bytes()) != raw:
                raise ValueError("errata compression readback failed")
            ledger_files[name] = dict(file=compressed.name, uncompressed_bytes=len(raw),
                                      uncompressed_sha256=hashlib.sha256(raw).hexdigest(),
                                      bytes=compressed.stat().st_size,
                                      sha256=hashlib.sha256(compressed.read_bytes()).hexdigest())
            path.unlink()  # Only the raw file just generated by this invocation.
        manifest["errata_ledger"] = dict(status="generated", counts=ledger["counts"],
            json="errata_ledger.json.gz", markdown="errata_ledger.md.gz", files=ledger_files,
            encoding="gzip (lossless JSON and Markdown, byte-for-byte readback verified)",
            note="comparison only; does not independently validate certificates")
        if sharded:
            manifest["errata_ledger"]["process_exit_status"] = manifest["l4_aggregate"]["process_exit_status"]
    else:
        manifest["errata_ledger"] = dict(status="pending", reason="L4 final JSON/exit evidence not ready; no wait or solver launched")
    manifest["pending_layers"] = [k for k, v in manifest["layers"].items() if v["status"] == "pending"]
    manifest["failed_layers"] = [k for k, v in manifest["layers"].items() if v["status"] == "failed"]
    manifest["status"] = ("failed" if manifest["failed_layers"] else "partial"
                          if manifest["pending_layers"] or not ledger_ready else "complete")
    manifest["last_line"] = (f"OWNER_RUN_PACK status={manifest['status']} layers={len(names)} "
                             f"pending={len(manifest['pending_layers'])} failed={len(manifest['failed_layers'])} "
                             f"errata={manifest['errata_ledger']['status']}")
    md = ["# 所有者新鲜运行证据索引", "", f"来源：`{source}`；提交（调用者标注）：`{source_commit}`。",
          "只读快照，不复制大文件、不启动运行、不代签验收；退出码仅取 summary.txt / JSON exit_code。", "",
          "| 层 | 状态 | 退出码 | 原样最后一行（JSON 优先） |", "|---|---|---:|---|"]
    for name, row in manifest["layers"].items():
        last = (row["json_last_line"] or row["log_last_line"] or "").replace("|", "\\|")
        md.append(f"| {name} | {row['status']} | {row['exit_code'] if row['exit_code'] is not None else 'unknown'} | `{last}` |")
    if sharded:
        aggregate = manifest["l4_aggregate"]
        md += ["", f"L4 分片清单：{aggregate['observed_case_count']}/{aggregate['inventory']['expected_case_count']} 个算例；"
               f"{len(aggregate['validation_errors'])} 条合并校验错误。清单来自冻结输入与生成器声明，未运行求解器。",
               f"L4 artifact_complete={aggregate['artifact_complete']}；process_exit_status={aggregate['process_exit_status']}。"
               "完整 JSON 可产生比较台账，但未知退出码始终保留 pending，不推定进程成功。"]
    md += ["", "日志/JSON 的字节与 SHA-256、DLL 字段哈希、原始 summary.txt、计数及诊断摘录见 "
           "[manifest](owner_run_manifest.json)。大型诊断仅保留计数/分类及内容哈希，详情留在来源 JSON。",
           "L4 台账：" + ("[JSON.gz](errata_ledger.json.gz) / [Markdown.gz](errata_ledger.md.gz)（无损压缩，逐字节读回核验）。" if manifest["errata_ledger"]["status"] == "generated"
                        else "**pending**（缺完成证据，未等待）。"),
           "Python 全档若位于另一目录，此索引保留 pending；不据此推断所有者运行失败。", "", manifest["last_line"]]
    (output / "owner_run_manifest.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    target = output / "owner_run_manifest.json"
    # Include the manifest itself and separately supplied mutation summaries.
    for _ in range(5):
        target.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
        size = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
        if manifest.get("package_bytes") == size:
            break
        manifest["package_bytes"] = size
    if size > LIMIT:
        raise ValueError(f"owner package exceeds {LIMIT} bytes: {size}; preserve source detail, compact historical evidence")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--old", type=Path, default=DEFAULT_OLD)
    parser.add_argument("--source-commit", default="not_supplied")
    args = parser.parse_args()
    result = pack(args.source, args.output, args.old, args.source_commit)
    print(result["last_line"])
    return int(result["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
