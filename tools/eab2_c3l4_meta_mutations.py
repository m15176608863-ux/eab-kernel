"""Source-internal M5/M7 mutants must fail the public-DLL metamorphic gate.

Compile a copied geometry translation unit, link it before a completed build's
core archive, and use the real release C ABI object. No production edits or
post-output corruption. Compilation/runtime setup failures never count as red.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from eab2_branch_mutations import pinned_compiler_environment

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = (
    ("M5_tangent_ignores_edge_sense",
     "geometry2::mul(geometry2::sub(index.velocities.at(end), index.velocities.at(start)), sense)",
     "geometry2::sub(index.velocities.at(end), index.velocities.at(start))",
     "regression_f_convex_in_notch/reflect_y"),
    ("M7_arm_force_jet_wrong_sign",
     "geometry2::cross(velocity, force) + geometry2::cross(arm, df)",
     "geometry2::cross(velocity, force) - geometry2::cross(arm, df)",
     "regression_f_convex_in_notch/anchor_only"),
)


def run(build, output):
    output, build = output.resolve(), build.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "eab2/build/tmp").resolve()):
        raise ValueError("use a NEW directory under ignored eab2/build/tmp")
    output.mkdir(parents=True)
    source = ROOT / "eab2/src/geometry_seed.cpp"
    raw = source.read_text("utf-8")
    library = build / "eab2_core.lib"
    abi_object = build / "CMakeFiles/eab2.dir/src/c_api.cpp.obj"
    if not library.is_file() or not abi_object.is_file():
        raise FileNotFoundError("completed release build/core/ABI object required")
    watched = [source, library, abi_object, ROOT / "tools/eab2_c3l4_meta.py", ROOT / "tools/eab2_c3l4_diff.py"]
    watched += sorted((ROOT / "eab2/src").glob("*.hpp"))
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
    records, started = [], time.perf_counter()
    vc = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat")
    compiler_environment = pinned_compiler_environment(output, vc)
    runs = [("baseline_" + name, None, None, case) for name, _, _, case in MUTATIONS] + list(MUTATIONS)
    for name, before, after, case in runs:
        folder = output / name
        folder.mkdir()
        temporary = folder / "tmp"
        temporary.mkdir()
        if before is not None and raw.count(before) != 1:
            raise AssertionError("mutant site must occur once: " + name)
        mutated = raw if before is None else raw.replace(before, after)
        copied = folder / "geometry_mutation.cpp"
        copied.write_text(mutated, encoding="utf-8", newline="\n")
        compile_command = (
            'cl /nologo /c /std:c++20 /O2 /DNDEBUG /MD /utf-8 /permissive- /fp:precise /W4 /EHsc /DBOOST_MP_STANDALONE '
            f'/I"{ROOT / "eab2/src"}" /I"{ROOT / "eab2/third_party/boost_multiprecision_1_86_0/include"}" '
            f'"{copied}" /Fo:"{folder / "geometry_mutation.obj"}"')
        link_command = (f'link /nologo /dll /machine:x64 /INCREMENTAL:NO "{abi_object}" '
                        f'"{folder / "geometry_mutation.obj"}" "{library}" /out:"{folder / "eab2.dll"}" '
                        f'/implib:"{folder / "eab2.lib"}" '
                        'kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib')
        batch = folder / "compile.cmd"
        batch.write_bytes(('@echo off\r\n'
            f'{compile_command}\r\nif errorlevel 1 exit /b %errorlevel%\r\n{link_command}\r\nexit /b %errorlevel%\r\n').encode("ascii"))
        environment = dict(compiler_environment, TEMP=str(temporary), TMP=str(temporary), VSLANG="1033")
        with (folder / "compile.log").open("wb") as log:
            compiled = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=folder, env=environment,
                                      stdout=log, stderr=subprocess.STDOUT, check=False)
        if compiled.returncode:
            raise RuntimeError(name + ": compiler/linker failure is not a semantic red gate")
        command = [sys.executable, "-X", "utf8", str(ROOT / "tools/eab2_c3l4_meta.py"), "--dll", str(folder / "eab2.dll"),
                   "--output", str(folder / "meta.json"), "--case", case]
        with (folder / "meta.log").open("wb") as log:
            checked = subprocess.run(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT, check=False)
        result = json.loads((folder / "meta.json").read_text("utf-8"))
        failures = result["failures"]
        if before is None:
            accepted = checked.returncode == 0 and not failures and len(result["cases"]) == 1
        else:
            accepted = checked.returncode == 1 and len(failures) == 1 and failures[0] == dict(
                case_id=case, error="ValueError: C++ geometry-derived seed mismatch")
        record = dict(name=name, case=case, semantic_result_verified=accepted, compile_exit=compiled.returncode,
                      gate_exit=checked.returncode, last_line=result["last_line"], failures=failures,
                      source_sha256=hashlib.sha256(raw.encode()).hexdigest(), mutant_sha256=hashlib.sha256(mutated.encode()).hexdigest(),
                      dll_sha256=hashlib.sha256((folder / "eab2.dll").read_bytes()).hexdigest(), before=before, after=after)
        records.append(record)
        (output / "progress.json").write_text(json.dumps(dict(complete=False, records=records), indent=2)+"\n", encoding="utf-8")
        if not accepted:
            raise AssertionError(name + ": expected exact named semantic outcome not observed")
        print(name + ": " + result["last_line"], flush=True)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != value for p, value in hashes.items()):
        raise AssertionError("source/build changed during mutation run; invalidate whole run")
    if len({r["mutant_sha256"] for r in records[-2:]}) != 2:
        raise AssertionError("mutants must be distinct")
    last = "C3L4_META_MUTATIONS_OK baseline=2 rejected=2 semantic_failures=2"
    (output / "summary.json").write_text(json.dumps(dict(complete=True, records=records, inputs=hashes,
        seconds=time.perf_counter()-started, last_line=last), indent=2)+"\n", encoding="utf-8")
    (output / "progress.json").write_text(json.dumps(dict(complete=True, last_line=last))+"\n", encoding="utf-8")
    print(last, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.build, args.output)
