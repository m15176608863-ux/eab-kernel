"""Compile source-internal L4 defects and require named semantic red gates.

No production file is rewritten. Each mutant is linked ahead of the existing
core archive in a fresh ignored directory; compiler failures never count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
# name, source, test, named gate, exact replacement, expected semantic assertion
MUTATIONS = (
    ("scaled_dual", "sensitivity", "sensitivity", "stable_original_unscaled_dual_three_seeds",
     "dot(*result.exact_x, seed.dc) + dot(*result.exact_y, rhs)",
     "dot(*result.exact_x, seed.dc) + Rational(2) * dot(*result.exact_y, rhs)",
     "stable original unscaled y and dA/db/dc formula"),
    ("missing_live_column", "sensitivity", "sensitivity", "live_load_column_is_not_rhs",
     "rows[m + 1 + i][j] = Rational(sign) * seed.dA[i][j];",
     "rows[m + 1 + i][j] = j + 1 == n ? Rational(0) : Rational(sign) * seed.dA[i][j];",
     "live amplitude derivative is negative capacity"),
    ("fixed_basis_on_unstable_face", "sensitivity", "sensitivity", "unstable_basis_cannot_hide_switch",
     "if (stable(result)) {", "if (true) {", "unstable fixed basis loses G5 switch right zero / left two"),
    ("compare_opposite_lp_values", "sensitivity", "sensitivity", "g5_mills_smooth_and_switch",
     "out.right_derivative == out.left_derivative ?", "*out.right_derivative == -*out.left_derivative ?",
     "G5 bounded-face exact closed-form derivative"),
    ("only_rhs_geometry_seed", "geometry_seed", "geometry_seed", None,
     "return out;\n}\n} // namespace eab2::statics",
     "for (auto& row : out.dA) std::fill(row.begin(), row.end(), Rational(0));\n    return out;\n}\n} // namespace eab2::statics",
     "point tangent normal and mu x propagation"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to((ROOT / "eab2/build/tmp").resolve()) or out.exists():
        parser.error("use a NEW directory inside eab2/build/tmp")
    out.mkdir(parents=True)
    vc = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat")
    lib = args.core.resolve()
    if not vc.is_file() or not lib.is_file():
        raise FileNotFoundError("existing pinned compiler/core required")
    records = []
    started = time.perf_counter()
    baseline = (("baseline_sensitivity", "sensitivity", "sensitivity", None, None, None, None),
                ("baseline_geometry", "geometry_seed", "geometry_seed", None, None, None, None))
    for name, unit, test, gate, before, after, assertion in (*baseline, *MUTATIONS):
        folder = out / name; folder.mkdir()
        temp = folder / "tmp"; temp.mkdir()
        source = ROOT / f"eab2/src/{unit}.cpp"
        raw = source.read_text("utf-8")
        if before is not None and raw.count(before) != 1:
            raise AssertionError(f"{name}: require one exact source site")
        mutant = raw if before is None else raw.replace(before, after)
        cpp = folder / "mutation.cpp"; cpp.write_text(mutant, encoding="utf-8", newline="\n")
        exe = folder / "mutation.exe"
        command = (f'cl /nologo /std:c++20 /O2 /DNDEBUG /MD /utf-8 /permissive- /fp:precise /W4 /EHsc '
                   f'/DBOOST_MP_STANDALONE /I"{ROOT / "eab2/src"}" '
                   f'/I"{ROOT / "eab2/third_party/boost_multiprecision_1_86_0/include"}" '
                   f'"{cpp}" "{ROOT / f"eab2/tests/test_{test}.cpp"}" "{lib}" /Fe:"{exe}"')
        batch = folder / "build.cmd"
        batch.write_bytes((f'@echo off\r\nset "PATH=%ProgramFiles(x86)%\\Microsoft Visual Studio\\Installer;%PATH%"\r\n'
            f'call "{vc}" -vcvars_ver=14.44.35207 >nul\r\nset TEMP={temp}\r\nset TMP={temp}\r\n'
            f'{command}\r\nexit /b %errorlevel%\r\n').encode("ascii"))
        environment = dict(os.environ, TEMP=str(temp), TMP=str(temp), VSLANG="1033")
        (out / "progress.json").write_text(json.dumps(dict(complete=False, running=name, phase="compile", cases=records), indent=2) + "\n", encoding="utf-8")
        build = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=folder, env=environment,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        (folder / "compile.log").write_bytes(build.stdout)
        if build.returncode:
            raise RuntimeError(f"{name}: compilation failed, not a semantic rejection")
        # Baseline every gate actually guarded by these retained mutants.
        # The complete sensitivity executable (including the expensive new
        # branch suite) is still run separately by full CTest, never skipped.
        selected_gates = (tuple(dict.fromkeys(row[3] for row in MUTATIONS if row[1] == "sensitivity"))
                          if name == "baseline_sensitivity" else (gate,))
        if name == "baseline_sensitivity" and (len(selected_gates) != 4 or None in selected_gates):
            raise AssertionError("four named original sensitivity gates required")
        test_runs, outputs = [], []
        for selected_gate in selected_gates:
            (out / "progress.json").write_text(json.dumps(dict(complete=False, running=name, phase="semantic_test",
                gate=selected_gate, cases=records), indent=2) + "\n", encoding="utf-8")
            run = subprocess.run([str(exe)] + ([selected_gate] if selected_gate else []), cwd=folder, env=environment,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
            outputs.append(run.stdout)
            lines = run.stdout.decode("utf-8", errors="replace").splitlines()
            last = lines[-1] if lines else ""
            test_runs.append(dict(gate=selected_gate, exit_code=run.returncode, last_line=last))
            if name == "baseline_sensitivity":
                (folder / (selected_gate + ".log")).write_bytes(run.stdout)
        (folder / "test.log").write_bytes(b"".join(outputs))
        test_exit = next((row["exit_code"] for row in test_runs if row["exit_code"] != 0), 0)
        if name == "baseline_sensitivity":
            passed = sum(row["exit_code"] == 0 and row["last_line"].startswith("sensitivity: ") for row in test_runs)
            good = passed == len(selected_gates)
            last = f"C3L4_SENSITIVITY_MUTATION_BASELINE gates={len(selected_gates)} passed={passed}"
        elif before is None:
            good = test_exit == 0 and (last.startswith("sensitivity: ") or last.startswith("C3L4_GEOMETRY_SEED_OK"))
        else:
            prefix = "sensitivity failed: " if unit == "sensitivity" else "C3L4_GEOMETRY_SEED_FAIL "
            good = test_exit != 0 and last == prefix + assertion
        row = dict(name=name, source=source.relative_to(ROOT).as_posix(),
                   source_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                   mutant_sha256=hashlib.sha256(mutant.encode()).hexdigest(),
                   test=f"eab2/tests/test_{test}.cpp", gate=gate, before=before, after=after,
                   assertion=assertion, command=command, compile_exit=build.returncode,
                   test_exit=test_exit, test_runs=test_runs, last_line=last, semantic_result_verified=good)
        records.append(row)
        (out / "progress.json").write_text(json.dumps(dict(complete=False, cases=records), indent=2) + "\n", encoding="utf-8")
        if not good:
            raise AssertionError(f"{name}: wrong red/green outcome: {last}")
        print(name + ": " + last, flush=True)
    if len({r["mutant_sha256"] for r in records[2:]}) != len(MUTATIONS):
        raise AssertionError("mutants must be distinct")
    last = f"C3L4_MUTATIONS_OK baseline=2 rejected={len(MUTATIONS)} semantic_failures={len(MUTATIONS)}"
    result = dict(schema="eab2.c3l4.mutations.v1", complete=True, cases=records,
                  baseline_scope="every retained sensitivity mutant's named gate; geometry suite in full; complete sensitivity suite remains mandatory in CTest",
                  core_library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),
                  seconds=time.perf_counter() - started, last_line=last)
    (out / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "progress.json").write_text(json.dumps(dict(complete=True, cases=len(records))) + "\n", encoding="utf-8")
    print(last, flush=True)


if __name__ == "__main__":
    main()
