"""Sequential WO-C3L3 acceptance-repair verification; no Git writes/install."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/C3L3_repair_evidence"
TMP = OUT / "tmp"
SOURCE = TMP / "complete_build_source"


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert not SOURCE.exists(), "build source must be new"
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    names = sorted({n for n in names if n and not n.startswith(("reports/codex/C3L3_repair_evidence/", "reports/codex/H1_evidence/")) and (ROOT / n).is_file()})
    SOURCE.mkdir(parents=True, exist_ok=False)
    manifest = []
    for name in names:
        path = SOURCE / name
        assert path.resolve().is_relative_to(SOURCE.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
        data = path.read_bytes()
        assert data == (ROOT / name).read_bytes()
        manifest.append(dict(path=name, bytes=len(data), sha256=digest(data)))
    dump(TMP / "complete_build_source_manifest.json", manifest)
    env = dict(os.environ, TEMP=str(TMP), TMP=str(TMP), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    records = []

    def run(name, command, cwd=ROOT):
        log = TMP / (name + ".log")
        started = time.time()
        dump(OUT / "progress.json", dict(complete=False, current=name, started=started, records=records, command=command))
        with log.open("wb") as stream:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, check=False)
        lines = log.read_text("utf-8", errors="replace").splitlines()
        record = dict(name=name, command=command, cwd=str(cwd), log=str(log), returncode=result.returncode,
            elapsed_seconds=time.time()-started, last_line=lines[-1] if lines else "", sha256=digest(log.read_bytes()))
        records.append(record)
        dump(OUT / "verification_runs.json", records)
        print(json.dumps(record), flush=True)
        if result.returncode:
            dump(OUT / "progress.json", dict(complete=False, failed=name, records=records))
            raise SystemExit(result.returncode)
        return record

    run("complete_build", [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(SOURCE / "eab2/build_eab2.bat")], SOURCE)
    build = SOURCE / "eab2/build"
    for unit in ("statics", "critical", "c3l3_abi"):
        run("cpp_"+unit, [str(build / ("eab2_test_"+unit+".exe"))], build)
    run("delivery_audit", [sys.executable, "-X", "utf8", str(SOURCE / "tools/eab2_audit.py"), "--build", str(build), "--output", str(OUT / "delivery_audit.json")], SOURCE)
    run("differential", [sys.executable, "-X", "utf8", "tools/eab2_c3l3_diff.py", "--dll", str(build / "eab2.dll"), "--family", "all", "--output", str(TMP / "differential.json")])
    raw = (TMP / "differential.json").read_bytes()
    data = json.loads(raw)
    assert data["source_pre_post_equal"] and not data["mismatches"]
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    (OUT / "differential.json.gz").write_bytes(packed)
    assert gzip.decompress((OUT / "differential.json.gz").read_bytes()) == raw
    raw_log = (TMP / "differential.log").read_bytes()
    (OUT / "differential.log.gz").write_bytes(gzip.compress(raw_log, compresslevel=9, mtime=0))
    dump(OUT / "differential_archive.json", dict(authority="differential.json.gz", bytes=len(raw), sha256=digest(raw),
        compressed_bytes=len(packed), compressed_sha256=digest(packed), verified_decompression=True,
        original_ignored_path=str(TMP / "differential.json"), last_line=data["last_line"]))
    for name, full in (("final_fast", False), ("final_full", True)):
        command = [sys.executable, "-X", "utf8", "tools/h1_run_gates.py", "--name", name, "--evidence-root", "reports/codex/C3L3_repair_evidence"]
        if full:
            command.append("--runslow")
        run(name, command)
        assert json.loads((OUT / name / "summary.json").read_text("utf-8"))["audit"] == "GREEN"
    unchanged = all(digest((ROOT / r["path"]).read_bytes()) == r["sha256"] for r in manifest)
    assert unchanged, "live non-evidence files changed during final sequence"
    dump(OUT / "progress.json", dict(complete=True, records=records, live_source_pre_post_equal=True, fresh_git_checkout=False))
    print("C3L3_REPAIR_FINAL_SEQUENCE_OK", flush=True)


if __name__ == "__main__":
    main()
