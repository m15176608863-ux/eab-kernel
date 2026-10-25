"""Compile four internal threshold-branch defects; compiler failures never count.

All copies, executables, and incremental logs stay in a new ignored directory.
The unchanged core archive is linked only after the mutated authored unit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SIGN = "int sign() const { return terms.empty() ? 0 : terms.begin()->second.sign(); }"
JOBS = (
    ("baseline_branch", "branch", "branch_face2_regression", None, None, None),
    ("baseline_field", "branch", "ordered_field_and_raw_path_guards", None, None, None),
    ("baseline_stable_differential", "sensitivity", "--differential-stable", None, None, None),
    ("single_basis_fallback", "sensitivity", "branch_face2_regression",
     "return branch_detail::certified_threshold(critical, *input, options, candidates);", "return candidates;",
     "face2 branch right one-half left zero requires both K sides"),
    # The screening probe now also guards the upper side. Remove both upper
    # checks to inject the actual lower-only defect, not a masked final check.
    ("lower_dual_only", "branch", "branch_face2_regression",
     ("screened = lower.status == opt::Status::unbounded || upper.status != opt::Status::unbounded;",
      "if (out.lower && out.point && out.ray) {"),
     ("screened = lower.status == opt::Status::unbounded;", "if (out.lower) {"),
     "face2 branch right one-half left zero requires both K sides"),
    ("eta_before_epsilon", "branch", "ordered_field_and_raw_path_guards", SIGN,
     "int sign() const { if (terms.empty()) return 0; auto first = terms.begin(); "
     "for (auto i = terms.begin(); i != terms.end(); ++i) "
     "if (std::pair{i->first.second, i->first.first} < std::pair{first->first.second, first->first.first}) first = i; "
     "return first->second.sign(); }", "K epsilon before eta, not reversed"),
    ("insufficient_truncation", "branch", "ordered_field_and_raw_path_guards", SIGN,
     "int sign() const { if (!terms.empty() && terms.begin()->first.first > 2) return 0; "
     "return terms.empty() ? 0 : terms.begin()->second.sign(); }",
     "nonzero high-order exact coefficient cannot be truncated to zero"),
    ("scaled_y_differential", "sensitivity", "--differential-stable",
     "dot(*result.exact_x, seed.dc) + dot(*result.exact_y, rhs)",
     "dot(*result.exact_x, seed.dc) + Rational(2) * dot(*result.exact_y, rhs)",
     "original unscaled dual derivative"),
    ("missing_live_column_differential", "sensitivity", "--differential-stable",
     "rhs[i] = rhs[i] - dot(seed.dA[i], *result.exact_x);",
     "rhs[i] = rhs[i] - dot(seed.dA[i], *result.exact_x) + seed.dA[i].back() * result.exact_x->back();",
     "original unscaled dual derivative"),
    ("min_max_sign_differential", "opt", "--differential-stable",
     "for (auto& value : result.exact_y) value = -value;",
     "for (auto& value : result.exact_y) value = value;",
     "max LP sign mapping failed certificate"),
)


def pinned_compiler_environment(output, vc):
    """Initialize the installed toolchain once, then verify before reusing it."""
    batch = output / "toolchain_init.cmd"
    batch.write_bytes((f'@echo off\r\ncall "{vc}" -vcvars_ver=14.44.35207 >nul\r\n'
                       'if errorlevel 1 exit /b 90\r\nset\r\n').encode("ascii"))
    initialized = subprocess.run(["cmd.exe", "/d", "/u", "/c", str(batch)],
        env=dict(os.environ, VSLANG="1033", VSCMD_SKIP_SENDTELEMETRY="1"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if initialized.returncode:
        raise RuntimeError("pinned compiler initialization failed; not a semantic rejection")
    environment = dict(line.split("=", 1) for line in
        initialized.stdout.decode("utf-16-le").splitlines() if "=" in line and not line.startswith("="))
    environment = {key.upper(): value for key, value in environment.items()}
    expected = vc.parents[2] / "Tools/MSVC/14.44.35207/bin/Hostx64/x64"
    if (environment.get("VCTOOLSVERSION", "").rstrip("\\") != "14.44.35207"
            or environment.get("VSCMD_ARG_TGT_ARCH") != "x64"
            or environment.get("VSCMD_ARG_HOST_ARCH") != "x64"
            or "CL" in environment or "_CL_" in environment):
        raise RuntimeError("pinned x64 toolchain environment mismatch")
    paths = {name: Path(shutil.which(name, path=environment.get("PATH", "")) or "")
             for name in ("cl.exe", "link.exe")}
    if any(path.resolve() != (expected / name).resolve() for name, path in paths.items()):
        raise RuntimeError("compiler/linker executable path is not the pinned toolchain")
    version = subprocess.run([str(paths["cl.exe"]), "/Bv"], env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False).stdout.decode("utf-8", errors="replace")
    if "19.44." not in version:
        raise RuntimeError("compiler version is not 19.44")
    (output / "toolchain.json").write_text(json.dumps(dict(
        version=version, executables={name: dict(path=str(path),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for name, path in paths.items()},
        host="x64", target="x64", initialized_once=True), indent=2) + "\n", encoding="utf-8")
    return environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, default=ROOT / "eab2/build/fix_branch/eab2_core.lib")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to((ROOT / "eab2/build/tmp").resolve()) or out.exists():
        parser.error("--output must be a new directory under eab2/build/tmp")
    core = args.core.resolve()
    vc = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat")
    if not vc.is_file() or not core.is_file():
        raise FileNotFoundError("pinned installed compiler and current core archive required")
    out.mkdir(parents=True)
    records = []
    started = time.perf_counter()
    compiler_environment = pinned_compiler_environment(out, vc)
    for name, unit, gate, before, after, assertion in JOBS:
        folder = out / name
        folder.mkdir()
        temp = folder / "tmp"
        temp.mkdir()
        source = ROOT / f"eab2/src/{unit}.cpp"
        cpp = source.read_text("utf-8")
        header = (ROOT / "eab2/src/branch.hpp").read_text("utf-8")
        if before is not None:
            edits = zip(before, after) if isinstance(before, tuple) else ((before, after),)
            for old, new in edits:
                target = header if old == SIGN else cpp
                if target.count(old) != 1:
                    raise AssertionError(f"{name}: one exact internal mutation site required per edit")
                if old == SIGN:
                    header = target.replace(old, new)
                else:
                    cpp = target.replace(old, new)
        (folder / "mutation.cpp").write_text(cpp, encoding="utf-8", newline="\n")
        (folder / "branch.hpp").write_text(header, encoding="utf-8", newline="\n")
        (folder / "test.cpp").write_bytes((ROOT / "eab2/tests/test_sensitivity.cpp").read_bytes())
        exe = folder / "test.exe"
        command = (f'cl /nologo /std:c++20 /O2 /DNDEBUG /MD /utf-8 /permissive- /fp:precise /W4 /EHsc '
                   f'/DBOOST_MP_STANDALONE /I"{ROOT / "eab2/src"}" '
                   f'/I"{ROOT / "eab2/third_party/boost_multiprecision_1_86_0/include"}" '
                   f'"{folder / "mutation.cpp"}" "{folder / "test.cpp"}" "{core}" /Fe:"{exe}"')
        batch = folder / "build.cmd"
        batch.write_bytes((f'@echo off\r\nset TEMP={temp}\r\nset TMP={temp}\r\n'
                           f'{command}\r\nexit /b %errorlevel%\r\n').encode("ascii"))
        environment = dict(compiler_environment, TEMP=str(temp), TMP=str(temp), VSLANG="1033")
        (out / "progress.json").write_text(json.dumps(dict(complete=False, running=name, phase="compile", cases=records), indent=2), encoding="utf-8")
        with (folder / "compile.log").open("wb") as log:
            build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=folder, env=environment, stdout=log, stderr=subprocess.STDOUT, check=False)
        if build.returncode:
            raise RuntimeError(f"{name}: compilation failed; not a semantic rejection")
        (out / "progress.json").write_text(json.dumps(dict(complete=False, running=name, phase="semantic_test", cases=records), indent=2), encoding="utf-8")
        with (folder / "test.log").open("wb") as log:
            run = subprocess.run([str(exe), gate], cwd=folder, env=environment, stdout=log, stderr=subprocess.STDOUT, check=False)
        lines = (folder / "test.log").read_text("utf-8", errors="replace").splitlines()
        last = lines[-1] if lines else ""
        differential_process = None
        classification = "baseline" if before is None else "branch_semantic"
        if name == "min_max_sign_differential":
            # This defect is rejected by the production LP certificate guard
            # before a derivative exists. Run the real differential entrypoint
            # as well, but never call it a Fraction derivative comparison.
            differential_command = [sys.executable, "-X", "utf8", str(ROOT / "tools/eab2_c3l4_stable.py"),
                                    "--executable", str(exe), "--output", str(folder / "differential_process.json")]
            with (folder / "differential_process.log").open("wb") as log:
                differential = subprocess.run(differential_command, cwd=ROOT, env=environment,
                                              stdout=log, stderr=subprocess.STDOUT, check=False)
            trace = (folder / "differential_process.log").read_text("utf-8", errors="replace")
            semantic = "sensitivity failed: " + assertion
            good = (run.returncode != 0 and last == semantic and differential.returncode != 0
                    and "stable C++ driver execution" in trace and semantic in trace)
            classification = "backend_certificate_rejection"
            differential_process = dict(command=differential_command, exit_code=differential.returncode,
                                        log="differential_process.log", classification=classification,
                                        driver_semantic_assertion=semantic)
            last = "STABLE_BACKEND_CERTIFICATE_REJECTED differential_exit=" + str(differential.returncode)
        elif gate == "--differential-stable" and run.returncode == 0:
            sys.path.insert(0, str(ROOT / "tools"))
            from eab2_c3l4_stable import verify_record
            failures = []
            payloads = [json.loads(line) for line in lines]
            for payload in payloads:
                try:
                    verify_record(payload)
                except (AssertionError, ValueError) as error:
                    failures.append(dict(id=payload["id"], error=str(error)))
            (folder / "differential_gate.json").write_text(json.dumps(dict(records=len(payloads), failures=failures), indent=2), encoding="utf-8")
            good = len(payloads) >= 5 and (not failures if before is None else any(row["error"] == assertion for row in failures))
            last = f"STABLE_MUTATION_DIFFERENTIAL records={len(payloads)} semantic_failures={len(failures)}"
            if before is not None:
                classification = "derivative_comparison"
        else:
            good = run.returncode == 0 and last.startswith("sensitivity: ") if before is None else (
                run.returncode != 0 and last == "sensitivity failed: " + assertion)
        records.append(dict(name=name, unit=unit, gate=gate, before=before, after=after,
                            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                            mutant_sha256=hashlib.sha256((cpp + header).encode()).hexdigest(),
                            compile_exit=build.returncode, test_exit=run.returncode,
                            classification=classification, differential_process=differential_process,
                            last_line=last, semantic_result_verified=good))
        (out / "progress.json").write_text(json.dumps(dict(complete=False, cases=records), indent=2), encoding="utf-8")
        if not good:
            raise AssertionError(f"{name}: wrong semantic red/green outcome: {last}")
        print(name + ": " + last, flush=True)
    if len({row["mutant_sha256"] for row in records[3:]}) != 7:
        raise AssertionError("seven internally distinct mutants required")
    if sum(row["classification"] == "derivative_comparison" for row in records) != 2 or sum(
            row["classification"] == "backend_certificate_rejection" for row in records) != 1:
        raise AssertionError("two derivative comparisons and one backend certificate rejection required")
    last = "C3L4FIX_BRANCH_AND_STABLE_MUTATIONS_OK baseline=3 rejected=7 branch_semantic=4 derivative_comparison=2 backend_certificate_rejection=1"
    summary = dict(schema="eab2.branch.mutations.v1", complete=True, cases=records,
                   core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(), seconds=time.perf_counter() - started, last_line=last)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out / "progress.json").write_text(json.dumps(dict(complete=True, cases=10)) + "\n", encoding="utf-8")
    print(last, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
