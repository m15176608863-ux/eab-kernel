"""Per-query errata ledger: accepted C3-L4 differential vs a fix-round run.

Usage: python tools/eab2_c3l4_errata.py old.json.gz new.json out.json out.md
Keys and comparison precedence are unchanged from the owner's errata_ledger.py:
(case_id, query_index, parameter), followed by FIELDS and classify below.
New-only queries additionally receive individual entries; the original counter
is unchanged. This is a comparison tool, not a certificate verifier. Justification
links to the owner's fix rationale, not a check performed here.
Only the standard library is required.
"""

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path


FIELDS = ("differentiability", "quality", "reason", "method", "directional_values")


def _rows(data):
    return {(r["case_id"], r["query_index"], r["parameter"]): r for r in data["queries"]}


def load(path):
    """Read JSON or gzip JSON, returning the original keyed rows and document."""
    path = Path(path)
    raw = path.read_bytes()
    if str(path).endswith(".gz"):
        raw = gzip.decompress(raw)
    data = json.loads(raw.decode("utf-8"))
    return _rows(data), data


def classify(old, new):
    o, n = old["directional_values"], new["directional_values"]
    old_cert = old["quality"] == "exact_jet" and any(v is not None for v in o.values())
    new_cert = new["quality"] == "exact_jet" and any(v is not None for v in n.values())
    if old_cert and new_cert and o != n:
        return "certified_value_changed"
    if old_cert and not new_cert:
        return "certified_to_unresolved"
    if new_cert and not old_cert:
        return "unresolved_to_certified"
    if old["differentiability"] != new["differentiability"]:
        return "class_changed"
    if old["reason"] != new["reason"] and old["quality"] != new["quality"]:
        return "reason_and_quality_changed"
    if old["reason"] != new["reason"]:
        return "reason_changed"
    if old["quality"] != new["quality"]:
        return "quality_changed"
    if old["method"] != new["method"]:
        return "method_changed"
    return "directional_values_changed"


def build_ledger(old_data, new_data, *, old_run="", new_run=""):
    """Compare loaded documents without importing or rerunning the harness."""
    old_rows, new_rows = _rows(old_data), _rows(new_data)
    ledger, counts = [], Counter()
    for key in sorted(old_rows):
        old, new = old_rows[key], new_rows.get(key)
        if new is None:
            counts["missing_in_new"] += 1
            ledger.append(dict(case_id=key[0], query_index=key[1], parameter=key[2], kind="missing_in_new"))
            continue
        if all(old.get(f) == new.get(f) for f in FIELDS):
            counts["unchanged"] += 1
            continue
        kind = classify(old, new)
        counts[kind] += 1
        ledger.append(dict(case_id=key[0], query_index=key[1], parameter=key[2], family=new["family"], kind=kind,
                           old={f: old.get(f) for f in FIELDS}, new={f: new.get(f) for f in FIELDS},
                           proof_references=new.get("branch_proof_references"),
                           justification="Owner fix rationale: docs/eab2_design_amendment_20261023.md; not reverified by this tool."))
    counts["new_only_queries"] = sum(1 for k in new_rows if k not in old_rows)
    # Expand the original new-only count without altering existing comparisons.
    for key in sorted(k for k in new_rows if k not in old_rows):
        new = new_rows[key]
        ledger.append(dict(case_id=key[0], query_index=key[1], parameter=key[2], family=new["family"],
                           kind="new_only_queries", old=None,
                           new={f: new.get(f) for f in FIELDS},
                           proof_references=new.get("branch_proof_references")))
    return dict(old_run=str(old_run), new_run=str(new_run), new_last_line=new_data.get("last_line"),
                counts=dict(counts), entries=ledger)


def _markdown_cell(value):
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _format_fields(fields):
    if fields is None:
        return ""
    return _markdown_cell(
        f"{fields['differentiability']}/{fields['quality']}/{fields['reason']} "
        f"method={fields['method']} directions={json.dumps(fields['directional_values'], ensure_ascii=False)}"
    )


def write_ledger(ledger, out_json, out_markdown):
    """Write the complete JSON and per-query Markdown ledger, UTF-8 without BOM."""
    Path(out_json).write_text(json.dumps(ledger, ensure_ascii=False, separators=(",", ":")) + "\n",
                              encoding="utf-8", newline="\n")
    lines = ["# C3-L4 修复轮 errata 台账（相对 cb14522 已验收差分）", "",
             f"旧运行：`{ledger['old_run']}`；新运行：`{ledger['new_run']}`"
             f"（末行 `{ledger['new_last_line']}`）。", "",
             "本工具仅比较记录；保留的 justification 是原修复说明，不代表本工具重新核验证书。", "",
             "| 类别 | 计数 |", "|---|---:|"]
    lines += [f"| {kind} | {count} |" for kind, count in sorted(ledger["counts"].items())]
    lines += ["", "| case | query | 参数 | 类别 | 旧 | 新 |", "|---|---:|---|---|---|---|"]
    for entry in ledger["entries"]:
        lines.append(
            f"| `{_markdown_cell(entry['case_id'])}` | {entry['query_index']} | "
            f"{_markdown_cell(entry['parameter'])} | {entry['kind']} | "
            f"{_format_fields(entry.get('old'))} | {_format_fields(entry.get('new'))} |"
        )
    Path(out_markdown).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def generate(old_path, new_path, out_json, out_markdown):
    """Load, compare, and write; return the ledger for an owner-pack manifest."""
    _, old_data = load(old_path)
    _, new_data = load(new_path)
    ledger = build_ledger(old_data, new_data, old_run=old_path, new_run=new_path)
    write_ledger(ledger, out_json, out_markdown)
    return ledger


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_run", help="accepted L4 JSON or JSON.gz")
    parser.add_argument("new_run", help="new L4 JSON or JSON.gz")
    parser.add_argument("out_json")
    parser.add_argument("out_markdown")
    args = parser.parse_args(argv)
    ledger = generate(args.old_run, args.new_run, args.out_json, args.out_markdown)
    print("ERRATA_LEDGER", json.dumps(ledger["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
