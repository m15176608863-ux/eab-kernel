"""Compile three isolated C1 geometry mutants and require semantic assertion kills.

Uses the verified baseline test object and core library, overriding geometry with
an explicitly linked mutant object. Only the copied .cpp under evidence/tmp is
modified. Compiler flags come from the current compile_commands.json, not a
reconstructed flag list. This is author gate-sensitivity evidence, not the
independent adversarial review required from Claude's reviewer.
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


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/codex/C1E_evidence"
BUILD = ROOT / "eab2/build"
SOURCE = ROOT / "eab2/src/geometry2.cpp"
VS = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community")
VCVARS = VS / "VC/Auxiliary/Build/vcvars64.bat"
MUTANTS = (
    {
        "name": "closed_E_mislabelled_as_O",
        "old": "const auto value = cell_state(cells[i], point);\n        if (value == 1) return 1;",
        "new": "const auto value = cell_state(cells[i], point);\n        if (value >= 0) return 1;",
        "expected": "failed=1 detail=nonconvex exact rectangle-union oracle",
        "defect": "Treat closed product-cell contact as strict body overlap inside membership.",
    },
    {
        "name": "isolated_contact_removed",
        "old": "if (membership(point) == 0) point_result.push_back({point, std::vector<Label>(labels.begin(), labels.end())});",
        "new": "if (membership(point) == 0 && std::any_of(contact_result.begin(), contact_result.end(), [&](const ContactSegment& e) { return on_segment(point, e.start, e.end); })) point_result.push_back({point, std::vector<Label>(labels.begin(), labels.end())});",
        "expected": "failed=1 detail=isolated contact retained",
        "defect": "Discard state-zero points not incident to a retained open contact segment.",
    },
    {
        "name": "window_promoted_to_strict",
        "old": "return w2 > Rational(0) && cone_nonreflex(cone.first, cone.second, w2) && cone_accepts(cone.first, cone.second, v, w2) ? 0 : -1;",
        "new": "return w2 > Rational(0) && cone_nonreflex(cone.first, cone.second, w2) && cone_accepts(cone.first, cone.second, v, w2) ? 1 : -1;",
        "expected": "failed=1 detail=explicit cone admits small reflex but never strict",
        "defect": "Promote an explicitly enlarged VE cone window to exact strictness.",
    },
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.name):
        parser.error("--name must be an ASCII single path component")
    run_root = EVIDENCE / "tmp" / f"mutations_{args.name}"
    run_root.mkdir(parents=True, exist_ok=False)
    output = EVIDENCE / f"mutations_{args.name}.json"
    if output.exists():
        raise RuntimeError("refuse to overwrite existing mutation evidence")
    database = BUILD / "compile_commands.json"
    compile_rows = json.loads(database.read_text(encoding="utf-8"))
    row = next(r for r in compile_rows if Path(r["file"]).resolve() == SOURCE.resolve())
    command = row["command"]
    compiler = command.split(" ", 1)[0]
    test_object = BUILD / "CMakeFiles/eab2_test_geometry2.dir/tests/test_geometry2.cpp.obj"
    core = BUILD / "eab2_core.lib"
    executable = BUILD / "eab2_test_geometry2.exe"
    baseline_files = [SOURCE, ROOT / "eab2/src/geometry2.hpp", ROOT / "eab2/tests/test_geometry2.cpp",
                      ROOT / "eab2/src/numeric.hpp", ROOT / "eab2/src/exact.hpp", database, test_object, core, executable]
    before = {str(p.relative_to(ROOT)): sha(p) for p in baseline_files}
    original = SOURCE.read_bytes()
    environment = dict(os.environ)
    if "CL" in environment or "_CL_" in environment:
        raise RuntimeError("ambient compiler flags are forbidden")
    environment.update(TEMP=str(EVIDENCE / "tmp"), TMP=str(EVIDENCE / "tmp"), VSLANG="1033")
    installer = Path(environment.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer"
    environment["PATH"] = str(installer) + os.pathsep + environment.get("PATH", "")
    started = time.perf_counter()
    baseline = subprocess.run([str(executable)], capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=environment, check=False, timeout=10)
    if baseline.returncode:
        raise RuntimeError("baseline geometry test is not green: " + baseline.stdout + baseline.stderr)
    results = []
    for mutant in MUTANTS:
        source = run_root / f"{mutant['name']}.cpp"
        obj = run_root / f"{mutant['name']}.obj"
        exe = run_root / f"{mutant['name']}.exe"
        old, new = mutant["old"].encode(), mutant["new"].encode()
        if original.count(old) != 1:
            raise RuntimeError(f"mutation anchor must occur exactly once: {mutant['name']}")
        source.write_bytes(original.replace(old, new, 1))
        compile_command = command.replace(str(SOURCE), str(source))
        # CMake may use forward slashes in its source path.
        compile_command = compile_command.replace(SOURCE.as_posix(), source.as_posix())
        compile_command, count = re.subn(r"/Fo(?:\"[^\"]+\"|\S+)", f'/Fo"{obj.as_posix()}"', compile_command)
        if count != 1 or str(source) not in compile_command and source.as_posix() not in compile_command:
            raise RuntimeError("cannot uniquely redirect the actual geometry compile command")
        compile_command = re.sub(r"/Fd(?:\"[^\"]+\"|\S+)", f'/Fd"{(run_root / (mutant["name"] + ".pdb")).as_posix()}"', compile_command)
        link_command = f'{compiler} /nologo /MD "{test_object}" "{obj}" "{core}" /link /OUT:"{exe}" /INCREMENTAL:NO /MACHINE:X64'
        batch = run_root / f"{mutant['name']}.bat"
        batch.write_text(f'@echo off\ncall "{VCVARS}" -vcvars_ver=14.44.35207 >nul\nif errorlevel 1 exit /b 70\n'
                         f'cd /d "{row["directory"]}"\n{compile_command}\nif errorlevel 1 exit /b 71\n'
                         f'{link_command}\nif errorlevel 1 exit /b 72\n"{exe}"\nexit /b %errorlevel%\n',
                         encoding="ascii", newline="\r\n")
        log = run_root / f"{mutant['name']}.log"
        remaining = 58 - (time.perf_counter() - started)
        if remaining <= 0:
            raise RuntimeError("mutation check exceeded its bounded one-minute budget")
        then = time.perf_counter()
        with log.open("xb") as stream:
            process = subprocess.run([environment.get("COMSPEC", r"C:\Windows\System32\cmd.exe"), "/d", "/c", str(batch)],
                                     cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT,
                                     check=False, timeout=remaining)
        text = log.read_text(encoding="utf-8", errors="replace")
        passed = process.returncode == 1 and mutant["expected"] in text
        results.append({**mutant, "passed": passed, "exit_code": process.returncode,
                        "last_line": text.strip().splitlines()[-1], "seconds": time.perf_counter() - then,
                        "source_copy": str(source), "source_sha256": sha(source), "log": str(log), "log_sha256": sha(log),
                        "actual_compile_command": compile_command, "link_command": link_command})
    after = {str(p.relative_to(ROOT)): sha(p) for p in baseline_files}
    passed = all(r["passed"] for r in results) and before == after
    last = f'C1_GEOMETRY_MUTATIONS mutants={len(results)} semantic_kills={sum(r["passed"] for r in results)} original_unchanged={int(before == after)}'
    report = {"schema": "eab2.c1.mutations.v1", "passed": passed,
              "scope": "Author gate sensitivity only; no claim of independent review or fresh-tree acceptance.",
              "baseline_last_line": baseline.stdout.strip().splitlines()[-1], "baseline_sha256": before,
              "original_unchanged": before == after, "mutants": results,
              "seconds": time.perf_counter() - started, "last_line": last}
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(last)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
