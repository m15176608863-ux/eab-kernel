"""Read-only C0/C1 delivery/build audit; writes only an explicitly requested JSON.

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
import subprocess

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
    cache_text = (build / "CMakeCache.txt").read_text("utf-8")
    ninja_match = re.search(r"^CMAKE_MAKE_PROGRAM:[^=]+=(.+)$", cache_text, re.M)
    dependency_checks = []
    if not ninja_match:
        findings.append("cannot locate actual Ninja for header dependency check")
    else:
        required_headers = list((ROOT / "eab2/src").glob("*.hpp")) + list((ROOT / "eab2/include/eab2").glob("*.h"))
        required_headers.append(build / "generated/build_identity.hpp")
        for entry in commands:
            query = subprocess.run([ninja_match.group(1).strip(), "-C", str(build), "-t", "query", entry["output"]],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
            normalized = query.stdout.replace("\\", "/").casefold()
            missing = [str(p) for p in required_headers
                       if p.resolve().as_posix().casefold() not in normalized
                       and not (p.is_relative_to(build) and p.relative_to(build).as_posix().casefold() in normalized)]
            if query.returncode or missing:
                findings.append(f"authored-header dependency gap: {entry['file']}: {missing}")
            dependency_checks.append({"object": entry["output"], "required_headers": len(required_headers),
                                      "missing": missing, "query_sha256": hashlib.sha256(query.stdout.encode()).hexdigest()})
    # Actual compiler binary identity must match the declaration embedded in DLL.
    compiler_versions = {}
    for item in checked_commands:
        compiler = item["resolved_compiler"]
        if compiler not in compiler_versions:
            probe = subprocess.run([compiler, "/Bv"], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", check=False)
            output = probe.stdout + probe.stderr
            versions = re.findall(r"\b(19\.44\.\d+(?:\.\d+)?)\b", output)
            if not versions:
                findings.append(f"cannot measure actual compiler version: {compiler}")
            compiler_versions[compiler] = max(versions, key=lambda v: len(v.split("."))) if versions else None
    # Production exposes C1 geometry but never numeric/exact query test bridges.
    production = ctypes.CDLL(str(build / "eab2.dll"))
    testing = ctypes.CDLL(str(build / "eab2_test.dll"))
    public = ["eab2_get_abi_info", "eab2_self_test", "eab2_context_create",
              "eab2_context_destroy", "eab2_context_get_error", "eab2_get_c1_abi_info",
              "eab2_context_get_limits2", "eab2_context_configure_limits2",
              "eab2_body2_create", "eab2_body2_destroy", "eab2_entrance2_create", "eab2_entrance2_destroy",
              "eab2_query2_batch", "eab2_membership2_batch", "eab2_topology2_batch",
              "eab2_result_export_exact", "eab2_result_destroy", "eab2_local_origin2_exact"]
    for name in public:
        if not hasattr(production, name):
            findings.append(f"missing production export: {name}")
    if hasattr(production, "eab2_numeric_batch"):
        findings.append("test numeric ABI leaked into production DLL")
    if not hasattr(testing, "eab2_numeric_batch"):
        findings.append("numeric test export absent")
    for test_name in ("eab2_query2_exact_batch", "eab2_covers2_exact"):
        if hasattr(production, test_name) or not hasattr(testing, test_name):
            findings.append(f"test bridge production/testing isolation failed: {test_name}")
    sys.path.insert(0, str(ROOT / "tools"))
    from eab2_diff import AbiInfo
    info = AbiInfo(struct_size=ctypes.sizeof(AbiInfo), abi_version=1)
    production.eab2_get_abi_info.argtypes = [ctypes.POINTER(AbiInfo)]
    production.eab2_get_abi_info.restype = ctypes.c_uint32
    if production.eab2_get_abi_info(ctypes.byref(info)):
        findings.append("cannot query production build identity")
    identity = bytes(info.build_identity).decode("ascii")
    for compiler, version in compiler_versions.items():
        if version and f"compiler=MSVC-{version};" not in identity:
            findings.append(f"embedded identity disagrees with actual compiler {compiler}: {version}")
    for part in ("isa=x64-SSE2", "fp=precise-contract_off", "crt=MD", "cxx=20", "boost=1.86.0-et_off"):
        if part not in identity:
            findings.append(f"identity missing audited command/source contract: {part}")
    for name in ("exact.hpp", "c_api.cpp", "fp_contract.cpp"):
        if "#if defined(__AVX__)" not in (ROOT / "eab2/src" / name).read_text("utf-8"):
            findings.append(f"controlled-source AVX compile guard absent: {name}")
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
        "commands": checked_commands, "compiler_versions_measured": compiler_versions,
        "explicit_header_dependency_checks": dependency_checks,
        "embedded_build_identity": identity,
        "identity_comparison": "actual compiler /Bv + compile_commands.json flags + guarded source contracts",
        "production_test_exact_absent": not hasattr(production, "eab2_query2_exact_batch"),
        "production_test_covers_absent": not hasattr(production, "eab2_covers2_exact"),
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
