"""Rebuild and kill focused C3-L3 critical-parameter internal mutations.

The runner never edits production sources and never reuses historical object
files or libraries. It is an implementation self-check, not Claude's separate
milestone adversarial review. All output is confined to eab2/build/tmp.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


MUTATIONS = (
    ("skip_numerator_sturm",
     "if (root_count(numerator.first, lower, upper)) return std::nullopt;",
     "if (false && root_count(numerator.first, lower, upper)) return std::nullopt;",
     "interior numerator roots rejected despite positive midpoint"),
    ("skip_denominator_sturm",
     "!nonzero(reduced.first) || root_count(reduced.first, lower, upper)",
     "!nonzero(reduced.first)", "interior denominator root rejected"),
    ("drop_last_step_resolution",
     'const auto reason = critical_detail::binary_midpoint(lo, hi) ? "iteration_limit" : "input_resolution_limit";',
     'const auto reason = "iteration_limit";', "last-step resolution reason preserved"),
    ("accept_nonbinary_domain",
     "mu_max < Rational(0) || !critical_detail::is_binary64(mu_max)",
     "mu_max < Rational(0)", "nonbinary64 search endpoint rejected"),
    ("drop_private_integer_scope",
     "exact::IntegerLimitScope integers(contacts.assembly.limits.max_integer_bits);",
     "// Mutant: private critical continuation lacks its integer scope.",
     "private critical input arithmetic observes integer budget"),
    ("closed_no_lower_continuation",
     'const bool closed = at.mathematical_status == "UNBOUNDED" && (candidate == Rational(0) || below.has_value());',
     'const bool closed = at.mathematical_status == "UNBOUNDED";',
     "koureas_wide_four_steps_requires_below: unbounded endpoint is not a closed threshold"),
    ("open_no_upper_ray",
     'const bool opened = at.mathematical_status == "OPTIMAL" && !nonzero(zero.b) && above && candidate < hi;',
     'const bool opened = at.mathematical_status == "OPTIMAL" && !nonzero(zero.b) && candidate < hi;',
     "unreversed_open_requires_above: endpoint states cannot certify an open threshold"),
)
CORE = ("numeric.cpp", "fp_contract.cpp", "geometry2.cpp", "geometry2_local.cpp", "opt.cpp", "l1.cpp", "statics.cpp")
VCVARS = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat")
FLAGS = "/nologo /std:c++20 /O2 /DNDEBUG /MD /utf-8 /permissive- /fp:precise /W4 /EHsc /DBOOST_MP_STANDALONE"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quoted(path: Path) -> str:
    value = str(path)
    if any(c in value for c in '\r\n"%&|<>^!'):
        raise ValueError(f"unsupported shell metacharacter in path: {path}")
    return '"' + value + '"'


def execute(command: list[str], cwd: Path, log: Path, timeout: int = 300) -> dict:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    log.write_bytes(completed.stdout)
    output = completed.stdout.decode("utf-8", errors="replace")
    return dict(command=command, cwd=str(cwd), returncode=completed.returncode,
        wall_seconds=time.perf_counter() - started, log=str(log),
        final_line=output.rstrip().splitlines()[-1] if output.rstrip() else "")


def build(folder: Path, compile_command: str) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "tmp").mkdir(exist_ok=True)
    batch = folder / "build.cmd"
    # This command file is deliberately ASCII-only, matching the C0 contract.
    content = "\n".join(("@echo off", f"call {quoted(VCVARS)} -vcvars_ver=14.44 >nul",
        "if errorlevel 1 exit /b 90", f"set TEMP={folder / 'tmp'}", "set TMP=%TEMP%",
        compile_command, "exit /b %errorlevel%", ""))
    batch.write_text(content, encoding="ascii", newline="")
    result = execute([os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(batch)],
                     folder, folder / "compile.log")
    result["compiler_command"] = compile_command
    if result["returncode"]:
        raise RuntimeError(f"compilation failed (not a killed mutation): {folder / 'compile.log'}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, help="Defaults to ROOT/eab2/src; useful for a byte-copy integration tree")
    parser.add_argument("--test-file", type=Path, help="Defaults to ROOT/eab2/tests/test_critical.cpp")
    parser.add_argument("--output", type=Path, required=True, help="Fresh descendant of ROOT/eab2/build/tmp only")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    source_dir = (args.source_dir or root / "eab2/src").resolve(strict=True)
    test = (args.test_file or root / "eab2/tests/test_critical.cpp").resolve(strict=True)
    output = args.output.resolve()
    allowed = (root / "eab2/build/tmp").resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        parser.error("--output must be a fresh descendant of ROOT/eab2/build/tmp")
    if output.exists() and any(output.iterdir()):
        parser.error("--output must be empty; stale artifacts must not influence a mutation check")
    if "CL" in os.environ or "_CL_" in os.environ:
        parser.error("ambient CL/_CL_ compiler flag injection is not supported")
    if not VCVARS.is_file():
        parser.error("pinned MSVC 14.44 environment is unavailable; do not install from this runner")
    vendor = (root / "eab2/third_party/boost_multiprecision_1_86_0/include").resolve(strict=True)
    public_headers = (root / "eab2/include").resolve(strict=True)
    inputs = [source_dir / name for name in CORE] + [source_dir / "critical.cpp", test]
    inputs += sorted(source_dir.glob("*.hpp"))
    inputs += sorted(public_headers.rglob("*.h"))
    for path in inputs:
        if not path.is_file():
            parser.error(f"required source missing: {path}")
    output.mkdir(parents=True, exist_ok=True)
    source_path = source_dir / "critical.cpp"
    source = source_path.read_bytes().decode("utf-8")
    if source.startswith("\ufeff"):
        raise ValueError("critical source must be UTF-8 without BOM")
    for name, before, _, _ in MUTATIONS:
        if source.count(before) != 1:
            raise ValueError(f"mutation target must have exactly one internal source site: {name}")
    source_hashes = {str(path): digest(path) for path in inputs}
    includes = f"/I{quoted(source_dir)} /I{quoted(public_headers)} /I{quoted(vendor)}"
    common = output / "common"
    common_sources = [source_dir / name for name in CORE] + [test]
    common_command = f"cl /Bv {FLAGS} {includes} /c " + " ".join(quoted(path) for path in common_sources)
    common_build = build(common, common_command)
    if not re.search(r"19\.44\.", (common / "compile.log").read_text(encoding="utf-8", errors="replace")):
        raise RuntimeError("compiler version evidence does not identify the pinned 19.44 toolset")
    objects = [common / (path.stem + ".obj") for path in common_sources]
    if not all(path.is_file() for path in objects):
        raise RuntimeError("fresh common compilation omitted an expected object")
    link_inputs = " ".join(quoted(path) for path in objects)

    def compile_run(folder: Path, text: str) -> tuple[dict, dict]:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "critical.cpp"
        path.write_text(text, encoding="utf-8", newline="")
        command = f"cl {FLAGS} {includes} {quoted(path)} {link_inputs} /Fe:critical_test.exe"
        compiled = build(folder, command)
        executed = execute([str(folder / "critical_test.exe")], folder, folder / "test.log")
        return compiled, executed

    baseline_build, baseline_run = compile_run(output / "baseline", source)
    if baseline_run["returncode"] != 0 or not baseline_run["final_line"].startswith("C3L3_CRITICAL_OK checks="):
        raise RuntimeError(f"unmutated baseline must pass before mutation claims: {baseline_run}")
    summary = dict(schema="eab2.c3l3.critical_mutations.v2", root=str(root), source_dir=str(source_dir),
        test_file=str(test), output=str(output), independent_adversarial_review=False,
        source_sha256=source_hashes,
        common_build=common_build, baseline=dict(build=baseline_build, run=baseline_run), mutations=[])
    summary_path = output / "summary.json"
    for name, before, after, assertion in MUTATIONS:
        mutated = source.replace(before, after)
        compiled, executed = compile_run(output / name, mutated)
        caught = (executed["returncode"] == 1 and executed["final_line"].startswith("C3L3_CRITICAL_FAIL checks=")
                  and executed["final_line"].endswith("reason=" + assertion))
        row = dict(name=name, original_sha256=digest(source_path),
            mutated_sha256=hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
            replacement=dict(before=before, after=after, count=1, character_offset=source.index(before)),
            expected_semantic_assertion=assertion, build=compiled, run=executed, caught=caught)
        summary["mutations"].append(row)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: {'CAUGHT' if caught else 'ESCAPED'} {executed['final_line']}", flush=True)
    # Read-back identity check proves the injected bytes never touched source.
    summary["sources_unchanged"] = all(digest(Path(path)) == expected for path, expected in summary["source_sha256"].items())
    summary["passed"] = summary["sources_unchanged"] and all(row["caught"] for row in summary["mutations"])
    summary["final_line"] = (f"C3L3_CRITICAL_MUTATIONS_OK caught={len(MUTATIONS)} escaped=0"
        if summary["passed"] else "C3L3_CRITICAL_MUTATIONS_FAILED")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(summary["final_line"], flush=True)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
