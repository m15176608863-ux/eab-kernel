"""Rebuild isolated internal mutants and require the intended semantic gates to fail.

This is implementation-author gate sensitivity evidence, not independent review.
Run with a fresh --name. No existing directory/report is overwritten or removed.
Only repository-local copies under C0_evidence/tmp/mutations are modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "eab2"
EVIDENCE = ROOT / "reports" / "codex" / "C0_evidence"
TEMP = EVIDENCE / "tmp"
VS = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community")
CMAKE = VS / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
NINJA = VS / "Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
COMPILER = VS / "VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe"
VCVARS = VS / "VC/Auxiliary/Build/vcvars64.bat"

COMPOUND_OLD = (
    "    return scalar_algebraic([&](const Rational& q) { return "
    "compare_signed_root(c, nn, offset + q); }, allow_underflow);"
)
COMPOUND_NEW = """    // MUTANT: incorrectly round both terms before their cancellation.
    // Retain the exact fallback only if an intermediate display is out of range.
    // This isolates double rounding rather than failing on an incidental overflow.
    try {
        auto root = sqrt_rational(c * c / nn, true);
        if (c.sign() < 0) root |= negative_bit;
        const auto rounded_offset = scalar_rational(offset, true);
        return scalar_rational(decode_binary64(root) - decode_binary64(rounded_offset), allow_underflow);
    } catch (const Error& error) {
        if (error.code != 4) throw;
        return scalar_algebraic([&](const Rational& q) { return compare_signed_root(c, nn, offset + q); }, allow_underflow);
    }"""

MUTATIONS = (
    {
        "name": "scalar_tie_parity",
        "file": "src/numeric.cpp",
        "old": "(twice_remainder == denominator && significand.odd())",
        "new": "(twice_remainder == denominator && !significand.odd())",
        "target": "eab2_test_numeric",
        "expected_marker": "failed=1 detail=scalar RN cell",
        "defect": "Reverse the exact-halfway integer parity decision inside scalar_rational.",
    },
    {
        "name": "compound_early_rounding",
        "file": "src/numeric.cpp",
        "old": COMPOUND_OLD,
        "new": COMPOUND_NEW,
        "target": "eab2_test_numeric",
        "expected_marker": "failed=1 detail=difference default underflow: did not fail",
        "defect": "Round representable normalized term and offset before subtracting; retain exact fallback for intermediate range errors.",
    },
    {
        "name": "missing_daz_guard",
        "file": "src/fp_contract.cpp",
        "old": "(original & (0x8000U | 0x0040U | 0x6000U)) != 0",
        "new": "(original & (0x8000U | 0x6000U)) != 0",
        "target": "eab2_test_abi",
        "expected_marker": "ABI_TESTS FAILED: DAZ rejected",
        "defect": "Remove only the DAZ mask bit from the entry self-test; retain every other environment check.",
    },
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(directory: Path) -> dict[str, str]:
    """Hash source, build definitions, and vendor bytes, excluding generated builds."""
    result = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if "build" in relative.parts:
            continue
        if path.is_symlink():
            raise RuntimeError(f"Refuse symlink in source copy: {path}")
        if path.is_file():
            result[relative.as_posix()] = digest(path)
    return result


def write_json_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def run(command: list[str], cwd: Path, environment: dict[str, str], log: Path,
        timeout: float) -> dict:
    started = time.perf_counter()
    timed_out = False
    with log.open("xb") as output:
        process = subprocess.Popen(command, cwd=cwd, env=environment,
                                   stdout=output, stderr=subprocess.STDOUT)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            code = None
            timed_out = True
            # Kill only this script's timed-out child tree, not unrelated compilers.
            taskkill = Path(environment.get("SYSTEMROOT", r"C:\Windows")) / "System32/taskkill.exe"
            subprocess.run([str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                           stdout=output, stderr=subprocess.STDOUT, check=False, timeout=30)
            process.wait(timeout=30)
    text = log.read_text(encoding="utf-8", errors="replace")
    nonempty = [line for line in text.splitlines() if line.strip()]
    return {
        "command": command,
        "working_directory": str(cwd),
        "exit_code": code,
        "timed_out": timed_out,
        "seconds": round(time.perf_counter() - started, 6),
        "stdout_last_line": nonempty[-1] if nonempty else "",
        "stdout_log": str(log),
        "stdout_sha256": digest(log),
        "stdout_bytes": log.stat().st_size,
    }


def tool_environment(run_root: Path) -> tuple[dict[str, str], dict]:
    if os.name != "nt":
        raise RuntimeError("This C0 mutation check supports Windows/MSVC only")
    for path in (CMAKE, NINJA, COMPILER, VCVARS):
        if not path.is_file():
            raise RuntimeError(f"Pinned tool is missing: {path}")
    environment = dict(os.environ)
    if "CL" in environment or "_CL_" in environment:
        raise RuntimeError("Ambient CL/_CL_ flag injection is not supported")
    environment.update(TEMP=str(TEMP), TMP=str(TEMP), VSLANG="1033")
    installer = Path(environment.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer"
    environment["PATH"] = str(installer) + os.pathsep + environment.get("PATH", "")
    # Do not pass nested quoted CALL syntax through subprocess.list2cmdline.
    # This short ASCII batch keeps cmd quoting in one place; only its pathname
    # crosses the process boundary. It is new and stays inside this run's tmp.
    setup_batch = run_root / "environment_setup.bat"
    with setup_batch.open("x", encoding="ascii", newline="\r\n") as stream:
        stream.write(f'@echo off\ncall "{VCVARS}" -vcvars_ver=14.44.35207 >nul\n')
        stream.write("if errorlevel 1 exit /b %errorlevel%\nset\n")
    command = [environment.get("COMSPEC", r"C:\Windows\System32\cmd.exe"), "/d", "/c", str(setup_batch)]
    # Environment output may include secrets. Parse it in memory, never put it in a log/report.
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=120, check=False)
    if result.returncode:
        raise RuntimeError(f"Pinned vcvars64 setup failed with exit {result.returncode}")
    for line in result.stdout.splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            environment[key.upper()] = value
    environment.update(TEMP=str(TEMP), TMP=str(TEMP), VSLANG="1033")
    actual = shutil.which("cl.exe", path=environment.get("PATH", ""))
    if not actual or Path(actual).resolve() != COMPILER.resolve():
        raise RuntimeError(f"vcvars selected unexpected compiler: {actual}")
    return environment, {
        "setup_command": command,
        "setup_batch_sha256": digest(setup_batch),
        "setup_exit_code": result.returncode,
        "compiler": str(COMPILER),
        "cmake": str(CMAKE),
        "ninja": str(NINJA),
        "toolset": "14.44.35207",
        "temp": str(TEMP),
        "tmp": str(TEMP),
        "environment_output_saved": False,
    }


def check_mutant(specification: dict, run_root: Path, baseline: dict,
                 environment: dict[str, str], timeout: float) -> dict:
    destination = run_root / specification["name"]
    # New run name means every path here is new; no deletion or reset is needed.
    shutil.copytree(SOURCE, destination, ignore=shutil.ignore_patterns("build"))
    copied = manifest(destination)
    copy_manifest_path = run_root / (specification["name"] + "_copied_sha256.json")
    write_json_new(copy_manifest_path, copied)
    row = {
        "name": specification["name"],
        "defect": specification["defect"],
        "source_copy": str(destination),
        "copy_manifest": str(copy_manifest_path),
        "copied_source_and_vendor_equal_original": copied == baseline,
        "target": specification["target"],
        "expected_semantic_marker": specification["expected_marker"],
        "steps": [],
        "passed": False,
    }
    if copied != baseline:
        row["failure"] = "Source/vendor bytes changed during copy; no build attempted"
        return row
    source = destination / specification["file"]
    original = source.read_bytes()
    old = specification["old"].encode("utf-8")
    new = specification["new"].encode("utf-8")
    occurrences = original.count(old)
    row["mutation"] = {
        "file": specification["file"], "old": specification["old"], "new": specification["new"],
        "occurrences_before": occurrences, "source_sha256_before": hashlib.sha256(original).hexdigest(),
    }
    if occurrences != 1:
        row["failure"] = "Mutation anchor must occur exactly once; no build attempted"
        return row
    source.write_bytes(original.replace(old, new, 1))
    row["mutation"]["source_sha256_after"] = digest(source)
    row["mutation"]["replacement_count"] = 1
    mutant_manifest = manifest(destination)
    changed = [path for path in sorted(set(copied) | set(mutant_manifest))
               if copied.get(path) != mutant_manifest.get(path)]
    row["changed_files_in_copy"] = changed
    if changed != [specification["file"]]:
        row["failure"] = "Mutation changed something other than its single product source file"
        return row

    build = destination / "build"
    configure = [str(CMAKE), "-S", str(destination), "-B", str(build), "-G", "Ninja",
                 f"-DCMAKE_MAKE_PROGRAM={NINJA}", "-DCMAKE_BUILD_TYPE=Release",
                 f"-DCMAKE_C_COMPILER={COMPILER}", f"-DCMAKE_CXX_COMPILER={COMPILER}"]
    commands = (
        ("configure", configure),
        ("build", [str(CMAKE), "--build", str(build), "--target", specification["target"], "--verbose"]),
        ("compiler_commands", [str(NINJA), "-C", str(build), "-t", "commands", specification["target"]]),
    )
    for name, command in commands:
        step = run(command, destination, environment, run_root / f"{specification['name']}_{name}.log", timeout)
        step["phase"] = name
        row["steps"].append(step)
        if step["exit_code"] != 0:
            row["failure"] = f"{name} failed; compiler/build failure is not a semantic kill"
            return row
        if name == "compiler_commands":
            # Preserve the actual compiler/link command lines in the compact JSON too.
            row["actual_compiler_commands"] = Path(step["stdout_log"]).read_text(encoding="utf-8", errors="replace").splitlines()
    test = run([str(build / (specification["target"] + ".exe"))], build, environment,
               run_root / f"{specification['name']}_test.log", timeout)
    test["phase"] = "semantic_test"
    row["steps"].append(test)
    row["passed"] = (test["exit_code"] not in (0, None) and not test["timed_out"] and
                     specification["expected_marker"] in test["stdout_last_line"])
    if not row["passed"]:
        row["failure"] = "Mutant did not fail at the required internal-defect semantic assertion"
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Fresh run directory name; existing names are refused")
    parser.add_argument("--timeout", type=float, default=300.0, help="Finite seconds per configure/build/test step")
    args = parser.parse_args()
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.name) or args.name.upper() in reserved:
        parser.error("--name must be a safe fresh Windows directory component")
    if not 0 < args.timeout < 86400:
        parser.error("--timeout must be finite, positive, and less than one day")
    run_root = TEMP / "mutations" / args.name
    report_path = EVIDENCE / f"mutation_{args.name}.json"
    report = {
        "schema": "eab2.c0.mutation_check.v1",
        "role": "implementation-author semantic gate sensitivity; not independent adversarial review",
        "run_name": args.name, "source": str(SOURCE), "run_directory": str(run_root),
        "report": str(report_path), "mutants": [], "passed": False,
    }
    started = time.perf_counter()
    baseline = None
    can_write_report = False
    try:
        if report_path.exists() or run_root.exists():
            raise RuntimeError("Refuse existing run directory or report; choose a new --name")
        if not run_root.resolve().is_relative_to(TEMP.resolve()) or not TEMP.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError("Resolved mutation destination escaped the permitted workspace")
        run_root.mkdir(parents=True, exist_ok=False)
        can_write_report = True
        baseline = manifest(SOURCE)
        baseline_path = run_root / "original_source_vendor_sha256.json"
        write_json_new(baseline_path, baseline)
        report["original_manifest"] = str(baseline_path)
        report["original_manifest_sha256"] = digest(baseline_path)
        report["original_file_count"] = len(baseline)
        environment, toolchain = tool_environment(run_root)
        report["toolchain"] = toolchain
        for specification in MUTATIONS:
            report["mutants"].append(check_mutant(specification, run_root, baseline, environment, args.timeout))
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if baseline is not None:
            try:
                after = manifest(SOURCE)
                report["original_source_and_vendor_unchanged"] = after == baseline
                report["original_changed_files"] = [name for name in sorted(set(baseline) | set(after))
                                                    if baseline.get(name) != after.get(name)]
            except Exception as error:
                report["original_source_and_vendor_unchanged"] = False
                report["original_hash_verification_error"] = str(error)
        report["seconds"] = round(time.perf_counter() - started, 6)
        report["passed"] = (len(report["mutants"]) == len(MUTATIONS) and
                            all(row["passed"] for row in report["mutants"]) and
                            report.get("original_source_and_vendor_unchanged", False) and "error" not in report)
        if can_write_report:
            write_json_new(report_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
