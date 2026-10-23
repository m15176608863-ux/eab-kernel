"""Rebuild source-internal statics mutations and require semantic test failures.

Only ignored scratch files are written. The production source is never edited.
The existing, pinned MSVC 14.44 installation and core library are reused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(data):
    return hashlib.sha256(data).hexdigest()


MUTATIONS = (
    ("ignore_physical_anchor",
     "wrench[2] - geometry2::cross(offset, {wrench[0], wrench[1]})",
     "wrench[2]", 1, "released plate physical-anchor counterexample"),
    ("same_friction_sign",
     "Rational(sign) * mu * contact.tangent",
     "Rational(1) * mu * contact.tangent", 2, "G5 closed form and C3-L1 regression d"),
    ("same_action_reaction_sign",
     "static_cast<int>(i == contact.a) - static_cast<int>(i == contact.b)",
     "static_cast<int>(i == contact.a) + static_cast<int>(i == contact.b)", 1,
     "G5 closed form and C3-L1 regression d"),
)


def run(args):
    root = args.root.resolve()
    source_dir = (args.source_dir or root / "eab2/src").resolve()
    test_file = (args.test_file or root / "eab2/tests/test_statics.cpp").resolve()
    output = args.output.resolve()
    allowed = (root / "eab2/build/tmp").resolve()
    if not output.is_relative_to(allowed):
        raise ValueError("output must stay inside ignored eab2/build/tmp")
    output.mkdir(parents=True, exist_ok=True)
    source = (source_dir / "statics.cpp").read_bytes()
    text = source.decode("utf-8")
    vcvars = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat")
    library = (root / "eab2/build/eab2_core.lib").resolve()
    if not vcvars.is_file() or not library.is_file():
        raise FileNotFoundError("pinned compiler or existing core library unavailable")
    cases = [("baseline", None, None, 0, None), *MUTATIONS]
    records = []
    started = time.perf_counter()
    for name, before, after, count, assertion in cases:
        folder = output / name
        folder.mkdir(parents=True, exist_ok=True)
        temporary = folder / "tmp"
        temporary.mkdir(exist_ok=True)
        if before is not None and text.count(before) != count:
            raise ValueError(f"mutation {name} needs exactly {count} source matches")
        mutated = text if before is None else text.replace(before, after)
        cpp = folder / "statics_mutation.cpp"
        cpp.write_bytes(mutated.encode("utf-8"))
        executable = folder / "statics_mutation.exe"
        command = (
            f'cl /nologo /std:c++20 /O2 /DNDEBUG /MD /utf-8 /permissive- '
            f'/fp:precise /W4 /EHsc /DBOOST_MP_STANDALONE '
            f'/I"{source_dir}" /I"{root / "eab2/src"}" '
            f'/I"{root / "eab2/third_party/boost_multiprecision_1_86_0/include"}" '
            f'"{cpp}" "{test_file}" "{library}" /Fe:"{executable}"'
        )
        batch = folder / "build.cmd"
        batch.write_bytes((f'@echo off\r\ncall "{vcvars}" -vcvars_ver=14.44 >nul\r\n'
                           f'set TEMP={temporary}\r\nset TMP={temporary}\r\n'
                           f'{command}\r\nexit /b %errorlevel%\r\n').encode("ascii"))
        environment = os.environ.copy()
        environment["TEMP"] = environment["TMP"] = str(temporary)
        compile_run = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=folder,
                                     env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     check=False)
        (folder / "compile.log").write_bytes(compile_run.stdout)
        if compile_run.returncode:
            raise RuntimeError(f"mutation {name} build failed; this is not a semantic red gate")
        test_run = subprocess.run([str(executable)], cwd=folder, env=environment,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        (folder / "test.log").write_bytes(test_run.stdout)
        lines = test_run.stdout.decode("utf-8", errors="replace").splitlines()
        last_line = lines[-1] if lines else ""
        expected = (test_run.returncode == 0 and last_line.startswith("C3L3_STATICS_OK")) if before is None else (
            test_run.returncode != 0 and last_line == "C3L3_STATICS_FAIL " + assertion)
        if not expected:
            raise AssertionError(f"{name}: expected semantic {'green' if before is None else 'red'}: {last_line}")
        records.append(dict(name=name, source_sha256=sha(source), mutant_sha256=sha(mutated.encode("utf-8")),
                            before=before, after=after, replacements=count, expected_assertion=assertion,
                            build_command=command,
                            compile_exit=compile_run.returncode, test_exit=test_run.returncode,
                            semantic_last_line=last_line, compile_log=str(folder / "compile.log"),
                            test_log=str(folder / "test.log")))
        print(name + ": " + last_line, flush=True)
    result = dict(schema="eab2-c3l3-statics-mutations-1", source=str(source_dir / "statics.cpp"),
                  source_sha256=sha(source), test_file=str(test_file), test_sha256=sha(test_file.read_bytes()),
                  core_library=str(library), core_library_sha256=sha(library.read_bytes()),
                  cases=records, elapsed_s=time.perf_counter() - started,
                  summary="C3L3_STATICS_MUTATIONS_OK baseline=1 rejected=3 semantic_failures=3")
    (output / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["summary"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--test-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
