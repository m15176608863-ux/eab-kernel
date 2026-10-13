"""Final M4b artifact QA: links, source freeze, logs and immutable git anchors."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BDDA = Path("D:/bdda-wt/shadow")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = ROOT / "reports/codex/M4b_report.md"
    text = report.read_text(encoding="utf-8")
    assert text.rstrip().endswith("M4b_DONE")
    assert sum("\u4e00" <= char <= "\u9fff" for char in text) > 2000
    missing = []
    link_count = 0
    qa_path = HERE / "final_delivery_qa.json"
    for document in (report, HERE / "DELIVERY_INDEX.md"):
        for link in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if link.startswith("file:///"):
                target = Path(unquote(link[8:]))
            elif "://" not in link:
                target = document.parent / unquote(link.split("#", 1)[0])
            else:
                continue
            link_count += 1
            if not target.exists() and target.resolve() != qa_path:
                missing.append(link)
    assert not missing, missing
    delivery = json.loads((HERE / "delivery_manifest.json").read_text(encoding="utf-8"))
    for row in delivery["files"]:
        path = Path(row["path"])
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], str(path)
    exported = json.loads((HERE / "full_suite_r2/export_manifest.json").read_text(encoding="utf-8"))
    relevant = [row for row in exported if row["path"].startswith(("src/", "tests/", "tools/", "fixtures/"))]
    drift = [row["path"] for row in relevant if sha(ROOT / row["path"]) != row["sha256"]]
    assert not drift, drift
    summary = json.loads((HERE / "full_suite_r2/summary.json").read_text(encoding="utf-8"))
    assert summary["audit"] == "GREEN" and summary["static"]["exit_code"] == 0
    assert sum(row["collected_nodes"] for row in summary["shards"]) == summary["collected"]
    bdda = json.loads((HERE / "bdda_verification_summary.json").read_text(encoding="utf-8"))
    for name, expected in bdda["logs_sha256"].items():
        assert sha(BDDA / "bdda2/build/m4b" / name) == expected, name
    anchors = {}
    for name, root, expected in (("eab", ROOT, "0810051ddebe07b39f7313e40517cbaf0988ad25"),
                                 ("bdda", BDDA, "cbf3642e31a3d68790fb62446da185b55ee70e63")):
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
        assert head == expected
        assert subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root).returncode == 0
        anchors[name] = head
    output = {"audit": "GREEN", "report_sha256": sha(report), "missing_links": missing,
              "local_links_verified": link_count, "delivery_file_hashes_verified": len(delivery["files"]),
              "tested_code_test_fixture_files": len(relevant), "drift_since_fresh_export": drift,
              "eab_collected": summary["collected"], "static_violations": 0,
              "bdda_logs_hash_verified": len(bdda["logs_sha256"]), "unchanged_heads": anchors,
              "staged_changes": False,
              "scope": "artifact QA, not a substitute for owner acceptance or full-repository G6"}
    (HERE / "final_delivery_qa.json").write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
