"""Compile isolated internal L1 mutants and require named semantic gate failures.

Run after eab2/build_eab2.bat. Only temporary copied sources are mutated; the
authored implementation is read-only. No Git or Python referee helper is used.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import os
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MUTANTS = (
    ("point_boundary_collinearity", "if (cross(n, rot(tangent)) == Rational(0) && dot(n, rot(tangent)) > Rational(0)) {",
     "if (dot(n, rot(tangent)) > Rational(0)) {", "regression a analytic normals"),
    ("actual_twist_rotation", "value = k < 2 ? normal[k] : cross(sub(p, assembly.bodies[i].dof_anchor), normal);",
     "value = k < 2 ? normal[k] : Rational(0);", "regression e same pair edge plus true VV"),
    ("strict_lock_cell", "open = open && sign > 0;", "open = open && sign >= 0;", "pairwise removable union has seam"),
    ("flat_interior_retention", "if (interior) continue;", "if (false && interior) continue;", "flat interior source not force point"),
    ("lock_original_ear_products", "pairs.emplace_back(moving, body, false, true, limits);",
     "pairs.emplace_back(moving, body, true, true, limits);", "lock keeps unmerged ear-product cell witnesses"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "eab2/build")
    parser.add_argument("--evidence", type=Path, default=ROOT / "reports/codex/C3L1_evidence")
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    if ROOT != evidence and ROOT not in evidence.parents:
        raise ValueError("evidence must remain within this worktree")
    original = (ROOT / "eab2/src/l1.cpp").read_text(encoding="utf-8")
    source_hash = hashlib.sha256((ROOT / "eab2/src/l1.cpp").read_bytes()).hexdigest()
    library = args.build_dir.resolve() / "eab2_core.lib"
    if not library.is_file():
        raise FileNotFoundError("build the pinned C++ core before mutation checks")
    tmp = evidence / "tmp/l1_mutations"
    env = dict(os.environ)
    env["PATH"] = r"C:\Program Files (x86)\Microsoft Visual Studio\Installer;" + env["PATH"]
    env["TEMP"] = env["TMP"] = str(evidence / "tmp")
    records = []
    for name, before, after, failure in MUTANTS:
        if original.count(before) != 1:
            raise RuntimeError(f"{name}: intended internal site is no longer unique")
        folder = tmp / name
        folder.mkdir(parents=True, exist_ok=True)
        changed = original.replace(before, after)
        (folder / "l1_mutant.cpp").write_text(changed, encoding="utf-8", newline="")
        diff = "".join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                                          fromfile="eab2/src/l1.cpp", tofile=name + ".cpp"))
        (folder / "mutation.diff").write_text(diff, encoding="utf-8", newline="")
        command = ('call "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat" '
                   '-vcvars_ver=14.44.35207 >nul && cl /nologo /std:c++20 /O2 /MD /DNDEBUG /utf-8 /permissive- /fp:precise '
                   '/W4 /EHsc /DBOOST_MP_STANDALONE '
                   f'/I"{ROOT / "eab2/src"}" /I"{ROOT / "eab2/include"}" '
                   f'/I"{ROOT / "eab2/third_party/boost_multiprecision_1_86_0/include"}" '
                   f'l1_mutant.cpp "{ROOT / "eab2/tests/test_l1.cpp"}" "{library}" /Fe:mutant.exe')
        (folder / "compile.bat").write_text("@echo off\n" + command + "\n", encoding="ascii", newline="")
        build = subprocess.run(["cmd", "/d", "/c", str(folder / "compile.bat")], cwd=folder,
                               env=env, capture_output=True, encoding="utf-8", errors="replace")
        (folder / "compile.log").write_text(build.stdout + build.stderr, encoding="utf-8", newline="")
        if build.returncode:
            raise RuntimeError(f"{name}: compile failure is not a semantic red gate: {build.stdout} {build.stderr}")
        run = subprocess.run([str(folder / "mutant.exe")], cwd=folder, env=env,
                             capture_output=True, encoding="utf-8", errors="replace")
        output = run.stdout + run.stderr
        (folder / "test.log").write_text(output, encoding="utf-8", newline="")
        accepted = run.returncode == 1 and "failed=1 detail=" + failure in output
        records.append(dict(name=name, source_replacements=1, compile_exit=build.returncode,
                            test_exit=run.returncode, semantic_red=accepted, expected_semantic_failure=failure,
                            original_last_line=output.strip().splitlines()[-1],
                            diff=str((folder / "mutation.diff").relative_to(ROOT))))
        if not accepted:
            raise RuntimeError(f"{name}: unexpected semantic failure: {output}")
    # Hash documents provenance only; mutant acceptance above is solely the
    # named semantic failure from the actual compiled altered implementation.
    report = dict(schema="eab2.c3l1.internal_mutations.v1", source_sha256=source_hash,
                  mutants=records, status="GREEN")
    (evidence / "l1_mutations.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8", newline="")
    print(f"EAB2_L1_MUTATIONS mutants={len(records)} semantic_red={sum(r['semantic_red'] for r in records)} failed=0")


if __name__ == "__main__":
    main()
