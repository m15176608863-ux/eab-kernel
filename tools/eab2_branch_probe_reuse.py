"""White-box C++ reuse-loop gate: original source fragment, independent JSON oracle.

This is not an end-to-end solver run. The local lambda and four reuse loops are
extracted byte-for-byte from branch.cpp into a tiny fixture in the same TU.
Only the recorded probe changes: 1-32*epsilon is positive in K and at 1/64,
but negative at 1/16. Removing the internal probe guards must fail this gate.
"""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess
import time

from eab2_branch_mutations import pinned_compiler_environment

ROOT = Path(__file__).resolve().parents[1]
START = b"            const auto probe_primal_ok ="
END = b"            if (out.lower && out.point && out.ray) {"
DEFECT = b" && probe_primal_ok(*f)"
DRIVER = r'''#include "branch_current.cpp"
#include <iostream>
namespace eab2::statics::branch_detail {
void probe_fixture(const Rational& e) {
    const Rational h = Rational(1) / Rational(4);
    const P polynomial = P(Rational(1)) + monomial(1, 0, Rational(-32));
    const Family high{PM{{P(Rational(1))}}, PV{polynomial}, PV{P(Rational(1))}};
    const Family low = high;
    const auto a_low = values(low.A, e, h);
    const auto c = values(low.c, e, h);
    const PM a_aug = high.A; const PV b_aug = high.b;
    const std::size_t alpha = 0;
    const Selection pick{{0}, {0}};
    const std::vector<Selection> seen_lower, seen_ray_aug, seen_ray_py;
    const std::vector<Selection> seen_point{pick};
    Direction out;
    const auto candidate = lift(high.A, high.b, pick, 1, e, h);
    if (!candidate) throw std::logic_error("fixture has a nonsingular basis");
#include "reuse_fragment.inc"
    std::cout << "{\"epsilon\":" << quote(e.canonical()) << ",\"eta\":" << quote(h.canonical())
        << ",\"denominator\":" << json(candidate->denominator)
        << ",\"numerator\":" << json(candidate->numerators[0])
        << ",\"k_feasible\":" << (equality(high.A, high.b, *candidate, true) ? "true" : "false")
        << ",\"accepted\":" << (out.point ? "true" : "false") << "}\n";
}
}
int main() {
    using namespace eab2::statics::branch_detail;
    probe_fixture(eab2::exact::Rational(1) / eab2::exact::Rational(64));
    probe_fixture(eab2::exact::Rational(1) / eab2::exact::Rational(16));
}
'''


def verify_reused_basis_records(records):
    """Primary oracle is hand polynomial Fraction arithmetic, not C++ helpers."""
    assert len(records) == 2, "two probes of the same reused basis required"
    for record, epsilon in zip(records, (Q(1, 64), Q(1, 16))):
        assert Q(record["epsilon"]) == epsilon and Q(record["eta"]) == Q(1, 4)
        denominator = {(i, j): Q(v) for i, j, v in record["denominator"]}
        numerator = {(i, j): Q(v) for i, j, v in record["numerator"]}
        assert denominator == {(0, 0): Q(1)}
        assert numerator == {(0, 0): Q(1), (1, 0): -Q(32)}
        assert numerator[min(numerator)] > 0 and record["k_feasible"] is True
        at_probe = Q(1) - Q(32) * epsilon
        assert at_probe == (Q(1, 2) if epsilon == Q(1, 64) else -Q(1))
        assert record["accepted"] is (at_probe >= 0), "reused probe-negative basis must be skipped"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out, core = args.output.resolve(), args.core.resolve()
    if out.exists() or not out.is_relative_to((ROOT / "eab2/build/tmp").resolve()):
        parser.error("output must be a new descendant of eab2/build/tmp")
    if not core.is_file():
        parser.error("current isolated core archive required")
    source = ROOT / "eab2/src/branch.cpp"
    raw = source.read_bytes()
    assert raw.count(START) == 1 and raw.count(END) == 1 and raw.count(DEFECT) == 3
    fragment = raw[raw.index(START):raw.index(END)]
    out.mkdir(parents=True)
    vc = Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat")
    environment = pinned_compiler_environment(out, vc)
    records = []
    for name, data in (("baseline", raw), ("omit_internal_probe_guard", raw.replace(DEFECT, b""))):
        folder = out / name
        folder.mkdir()
        (folder / "tmp").mkdir()
        (folder / "branch_current.cpp").write_bytes(data)
        part = data[data.index(START):data.index(END)]
        (folder / "reuse_fragment.inc").write_bytes(part)
        (folder / "driver.cpp").write_text(DRIVER, encoding="utf-8", newline="\n")
        assert (folder / "reuse_fragment.inc").read_bytes() == part
        executable = folder / "probe.exe"
        command = (f'cl /nologo /std:c++20 /O2 /DNDEBUG /MD /utf-8 /permissive- /fp:precise /W4 /EHsc '
                   f'/DBOOST_MP_STANDALONE /I"{ROOT / "eab2/src"}" '
                   f'/I"{ROOT / "eab2/third_party/boost_multiprecision_1_86_0/include"}" '
                   f'"{folder / "driver.cpp"}" "{core}" /Fe:"{executable}"')
        batch = folder / "build.cmd"
        batch.write_bytes((f'@echo off\r\n{command}\r\nexit /b %errorlevel%\r\n').encode("ascii"))
        env = dict(environment, TEMP=str(folder / "tmp"), TMP=str(folder / "tmp"))
        (out / "progress.json").write_text(json.dumps(dict(running=name, phase="build")), encoding="utf-8")
        before = time.time_ns()
        with (folder / "compile.log").open("wb") as log:
            built = subprocess.run(["cmd.exe", "/d", "/c", str(batch)], cwd=folder,
                                   env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        assert built.returncode == 0, "compile failure is not a semantic kill"
        assert executable.stat().st_mtime_ns >= before, "new executable timestamp required"
        with (folder / "records.jsonl").open("wb") as log:
            ran = subprocess.run([str(executable)], cwd=folder, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, check=False)
        assert ran.returncode == 0, "C++ driver must successfully emit its own JSON"
        payloads = [json.loads(line) for line in (folder / "records.jsonl").read_text("utf-8").splitlines()]
        message = None
        try:
            verify_reused_basis_records(payloads)
        except AssertionError as error:
            message = str(error)
        assert message == (None if name == "baseline" else "reused probe-negative basis must be skipped")
        records.append(dict(name=name, compile_exit=built.returncode, test_exit=ran.returncode,
            semantic_failure=message, fragment_sha256=hashlib.sha256(part).hexdigest(),
            source_sha256=hashlib.sha256(data).hexdigest(), executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
            executable_mtime_ns=executable.stat().st_mtime_ns, build_started_ns=before,
            json_sha256=hashlib.sha256((folder / "records.jsonl").read_bytes()).hexdigest()))
    assert source.read_bytes() == raw, "production source must remain unchanged"
    last = "C3L4_PROBE_REUSE_CPP_OK baseline=1 killed=1 survived=0 json_records=4"
    summary = dict(last_line=last, scope="white-box original reuse fragment; not end-to-end solver",
        source_sha256=hashlib.sha256(raw).hexdigest(), core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),
        original_fragment_sha256=hashlib.sha256(fragment).hexdigest(), byte_exact_original_fragment=True, cases=records)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out / "progress.json").write_text(json.dumps(dict(complete=True, last_line=last)), encoding="utf-8")
    print(last, flush=True)


if __name__ == "__main__":
    main()
