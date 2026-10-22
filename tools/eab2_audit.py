"""Read-only C0 delivery/build audit; writes only an explicitly requested JSON.

No downloads, Git writes, source rewrites, or numeric oracle helpers. The audit
checks the actual final compiler commands, private vendor bytes, and DLL exports.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / "eab2/build")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build = args.build.resolve()
    findings = []
    vendor = ROOT / "eab2/third_party/boost_multiprecision_1_86_0"
    rows = json.loads((vendor / "COPY_MANIFEST.json").read_text("utf-8"))
    for row in rows:
        path = vendor / row["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            findings.append(f"vendor hash mismatch: {row['path']}")
        if path.is_file() and path.stat().st_size != row["bytes"]:
            findings.append(f"vendor byte count mismatch: {row['path']}")
    expected_vendor = {r["path"] for r in rows} | {"COPY_MANIFEST.json", "PROVENANCE.md"}
    actual_vendor = {p.relative_to(vendor).as_posix() for p in vendor.rglob("*") if p.is_file()}
    if expected_vendor != actual_vendor:
        findings.append("vendor inventory differs from manifest")
    commands = json.loads((build / "compile_commands.json").read_text("utf-8"))
    checked_commands = []
    for entry in commands:
        command = entry["command"]
        suffix = Path(entry["file"]).suffix.lower()
        required = ["/O2", "/MD", "/utf-8", "/fp:precise"]
        if suffix == ".cpp":
            required += ["/std:c++20", "/permissive-"]
        # CMake's MSVC generator spells some equivalent switches with '-'.
        tokens = ["/" + token[1:] if token.startswith("-") else token for token in command.split()]
        for flag in required:
            if flag not in tokens:
                findings.append(f"missing actual flag {flag}: {entry['file']}")
        if re.search(r"(?:/|-)arch:|(?:/|-)GL(?:\s|$)|(?:/|-)fp:(?:fast|contract)", command, re.I):
            findings.append(f"forbidden actual flags: {entry['file']}")
        compiler_match = re.match(r'(?:"([^"]+)"|(\S+))', command)
        compiler = Path(compiler_match.group(1) or compiler_match.group(2)).resolve()
        if "14.44.35207" not in compiler.as_posix():
            findings.append(f"wrong compiler toolset path: {entry['file']}")
        checked_commands.append({"file": entry["file"], "command": command,
                                 "resolved_compiler": str(compiler)})
    if not checked_commands:
        findings.append("no actual compiler commands")
    # Production must expose only lifecycle/capability, not the numeric test ABI.
    production = ctypes.CDLL(str(build / "eab2.dll"))
    testing = ctypes.CDLL(str(build / "eab2_test.dll"))
    public = ["eab2_get_abi_info", "eab2_self_test", "eab2_context_create",
              "eab2_context_destroy", "eab2_context_get_error"]
    for name in public:
        if not hasattr(production, name):
            findings.append(f"missing production export: {name}")
    if hasattr(production, "eab2_numeric_batch"):
        findings.append("test numeric ABI leaked into production DLL")
    if not hasattr(testing, "eab2_numeric_batch"):
        findings.append("numeric test export absent")
    authored = [p for p in (ROOT / "eab2").rglob("*") if p.is_file()
                and not p.is_relative_to(build) and not p.is_relative_to(vendor)]
    authored += sorted((ROOT / "tools").glob("eab2_*.py"))
    for path in authored:
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            findings.append(f"unexpected UTF-8 BOM: {path.relative_to(ROOT)}")
        if b"\r\n" in data and b"\n" in data.replace(b"\r\n", b""):
            findings.append(f"mixed newline convention: {path.relative_to(ROOT)}")
        try:
            data.decode("ascii" if path.suffix == ".bat" else "utf-8")
        except UnicodeError:
            findings.append(f"encoding contract failed: {path.relative_to(ROOT)}")
    sys.path.insert(0, str(ROOT / "tools"))
    from repository_size import assert_deliverable_sizes
    try:
        assert_deliverable_sizes(ROOT)
    except AssertionError as error:
        findings.append(str(error))
    report = {
        "status": "PASS" if not findings else "FAIL", "findings": findings,
        "vendor_files": len(rows), "vendor_bytes": sum(r["bytes"] for r in rows),
        "vendor_max_file_bytes": max(r["bytes"] for r in rows),
        "commands": checked_commands,
        "production_exports_checked": public,
        "production_numeric_absent": not hasattr(production, "eab2_numeric_batch"),
        "testing_numeric_present": hasattr(testing, "eab2_numeric_batch"),
        "encoding_files": len(authored),
        "dll_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (build / "eab2.dll", build / "eab2_test.dll")},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EAB2_DELIVERY_AUDIT status={report['status']} findings={len(findings)} vendor_files={len(rows)} compiler_commands={len(commands)}")
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
