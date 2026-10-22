"""C3-L1 exact LP semantic mutation teeth, five bounded short compilations.

Production sources are only read. Each mutation is compiled in a new directory
under this work order's tmp. A nonzero exit alone is insufficient: the expected
original-model certificate or anti-cycling diagnostic must be observed.
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
MUTATIONS = (
    ("optimal_dual_check", "if ((model.c[j] - dot(y, model.column(j))).sign() < 0) return std::nullopt;",
     "if (false) return std::nullopt;", "basis certificate disagrees with original LP",
     "A suboptimal basis must not certify as optimal; independent original-data dual inequality rejects it."),
    ("farkas_column_check", "if (dot(y, model.column(j)).sign() > 0) return std::nullopt;",
     "if (false) return std::nullopt;", "basis certificate disagrees with original LP",
     "Positive b separation alone is insufficient; every original Farkas column must be nonpositive."),
    ("strict_ray_improvement", "if (improvement.sign() >= 0) return std::nullopt;",
     "if (false) return std::nullopt;", "basis certificate disagrees with original LP",
     "A feasible recession direction with increasing objective is not an unbounded certificate."),
    ("unbounded_feasible_point", "answer.exact_x = point.exact_x;",
     "answer.exact_x.assign(c.size(), Rational(0));", "LP result failed original-model certificate",
     "An improving homogeneous ray does not replace the nonzero original-RHS feasible point."),
    ("bland_anti_cycling", "if (degenerate > 2 * model.m + 10)",
     "if (false)", "exact LP pivot work limit exceeded; no answer returned",
     "Known exact cycling examples must switch to Bland and finish within the 1000-pivot test budget."),
)


def write(path, value):
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ROOT / "eab2/src/opt.cpp")
    parser.add_argument("--header", type=Path, default=ROOT / "eab2/src/opt.hpp")
    parser.add_argument("--test-source", type=Path, default=ROOT / "eab2/tests/test_opt.cpp")
    parser.add_argument("--baseline-exe", type=Path, default=ROOT / "eab2/build/eab2_test_opt.exe")
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    permitted = (ROOT / "reports/codex/C3L1_evidence/tmp").resolve()
    if not destination.is_relative_to(permitted) or destination == permitted:
        raise ValueError("mutation artifacts must stay in a child of this work order's tmp")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("mutation output directory must be new or empty; prior evidence is not overwritten")
    destination.mkdir(parents=True, exist_ok=True)
    source = args.source.read_text(encoding="utf-8")
    source_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
    environment = os.environ.copy()
    environment["PATH"] = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer;" + environment["PATH"]
    environment["TEMP"] = environment["TMP"] = str(permitted)
    environment["VSLANG"] = "1033"
    environment.pop("CL", None)
    environment.pop("_CL_", None)
    baseline = subprocess.run([str(args.baseline_exe.resolve())], cwd=destination, env=environment,
                              capture_output=True, timeout=120, encoding="utf-8", errors="replace")
    write(destination / "baseline.log", baseline.stdout + baseline.stderr)
    if baseline.returncode or "failed=0" not in baseline.stdout:
        raise RuntimeError("unmutated static baseline is not green")
    report = {"schema": "eab2.c3l1.opt.mutations.v1", "source": str(args.source),
              "source_sha256": source_hash, "baseline_last_line": baseline.stdout.strip().splitlines()[-1],
              "mutation_count": len(MUTATIONS), "killed": 0, "survived": 0, "mutations": []}
    for name, before, after, diagnostic, meaning in MUTATIONS:
        if source.count(before) != 1:
            raise ValueError(f"mutation {name} source anchor is not unique")
        directory = destination / name
        directory.mkdir()
        write(directory / "opt.cpp", source.replace(before, after))
        write(directory / "opt.hpp", args.header.read_text(encoding="utf-8"))
        # Pure ASCII batch; all objects/executables are confined by cwd to the
        # checked output directory. No file deletion or git operation occurs.
        compile_command = '\r\n'.join((
            "@echo off", "setlocal",
            'call "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat" -vcvars_ver=14.44.35207 >nul',
            "if errorlevel 1 exit /b %errorlevel%",
            'cl /nologo /O2 /DNDEBUG /std:c++20 /MD /fp:precise /EHsc /W4 /utf-8 /permissive- /DBOOST_MP_STANDALONE '
            f'/I"{directory}" /I"{ROOT / "eab2/src"}" /I"{ROOT / "eab2/third_party/boost_multiprecision_1_86_0/include"}" '
            f'"{directory / "opt.cpp"}" "{args.test_source.resolve()}" /Fe"{directory / "mutant.exe"}"',
            "exit /b %errorlevel%", ""))
        (directory / "compile.bat").write_bytes(compile_command.encode("ascii"))
        started = time.perf_counter()
        compiled = subprocess.run(["cmd", "/d", "/c", str(directory / "compile.bat")], cwd=directory,
                                  env=environment, capture_output=True, timeout=180, encoding="utf-8", errors="replace")
        write(directory / "compile.log", compiled.stdout + compiled.stderr)
        if compiled.returncode:
            raise RuntimeError(f"{name} compilation failed, not a valid semantic kill")
        tested = subprocess.run([str(directory / "mutant.exe")], cwd=directory, env=environment,
                                capture_output=True, timeout=120, encoding="utf-8", errors="replace")
        output = tested.stdout + tested.stderr
        write(directory / "test.log", output)
        killed = tested.returncode != 0 and diagnostic in output and "failed=1" in output
        report["killed" if killed else "survived"] += 1
        report["mutations"].append({"name": name, "killed": killed, "semantic_contract": meaning,
            "expected_diagnostic": diagnostic, "exit_code": tested.returncode,
            "last_line": output.strip().splitlines()[-1] if output.strip() else "",
            "seconds": time.perf_counter()-started, "directory": str(directory),
            "mutant_sha256": hashlib.sha256((directory / "opt.cpp").read_bytes()).hexdigest()})
        write(destination / "summary.json", json.dumps(report, indent=2) + "\n")
        print(f"OPT_MUTANT {name} killed={int(killed)}", flush=True)
    if hashlib.sha256(args.source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("original source changed during mutation run")
    report["last_line"] = f"OPT_MUTATIONS total={len(MUTATIONS)} killed={report['killed']} survived={report['survived']}"
    write(destination / "summary.json", json.dumps(report, indent=2) + "\n")
    print(report["last_line"], flush=True)
    return int(report["survived"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
