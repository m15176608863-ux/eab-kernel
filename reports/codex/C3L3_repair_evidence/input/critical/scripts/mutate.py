"""Apply one mutation at a time to the scratch mutation copy, rebuild, run gates, revert."""
import json, os, subprocess, sys, time
from pathlib import Path

BASE = Path(sys.argv[1]).resolve()          # .../critical/mut
SRC = BASE / "src"
OUT = BASE / "out"
OUT.mkdir(exist_ok=True)
ADV = Path(sys.argv[2]).resolve()           # adv.py
ONLY = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else None

CR, ST = "eab2/src/critical.cpp", "eab2/src/statics.cpp"
MUTANTS = [
    ("closed_no_lower_continuation", CR,
     'const bool closed = at.mathematical_status == "UNBOUNDED" && (candidate == Rational(0) || below.has_value());',
     'const bool closed = at.mathematical_status == "UNBOUNDED";'),
    ("open_no_upper_ray", CR,
     'const bool opened = at.mathematical_status == "OPTIMAL" && !nonzero(zero.b) && above && candidate < hi;',
     'const bool opened = at.mathematical_status == "OPTIMAL" && !nonzero(zero.b) && candidate < hi;'),
    ("open_no_zero_dead_check", CR,
     'const bool opened = at.mathematical_status == "OPTIMAL" && !nonzero(zero.b) && above && candidate < hi;',
     'const bool opened = at.mathematical_status == "OPTIMAL" && above && candidate < hi;'),
    ("critical_unbounded_probe_as_finite", CR,
     'if (probe.mathematical_status == "UNBOUNDED") { hi = *mid; high = probe; }\n        else if (probe.mathematical_status == "OPTIMAL" || probe.mathematical_status == "INFEASIBLE") { lo = *mid; low = probe; }',
     'if (probe.mathematical_status == "UNBOUNDED" && false) { hi = *mid; high = probe; }\n        else if (probe.mathematical_status == "OPTIMAL" || probe.mathematical_status == "INFEASIBLE" || probe.mathematical_status == "UNBOUNDED") { lo = *mid; low = probe; }'),
    ("critical_attained_always_true", CR, 'answer.attained = closed;', 'answer.attained = true;'),
    ("critical_reason_overwritten", CR,
     'answer.threshold_proof_reason = "exact_basis_continuation";',
     'answer.threshold_proof_reason = "exact_basis_continuation"; answer.reason = "exact_basis_continuation";'),
    ("statics_unbounded_as_finite", ST,
     'result.mathematical_status = "UNBOUNDED";\n        result.feasible_point = solved.exact_x;',
     'result.mathematical_status = "OPTIMAL"; result.exact_value = Rational(0);\n        result.feasible_point = solved.exact_x;'),
    ("generator_normal_flipped", ST,
     'const Point normal{-contact.tangent[1], contact.tangent[0]};',
     'const Point normal{contact.tangent[1], -contact.tangent[0]};'),
    ("generator_friction_y_sign", ST,
     'normal[1] + Rational(sign) * mu * contact.tangent[1]};',
     'normal[1] - Rational(sign) * mu * contact.tangent[1]};'),
    ("no_reaction_on_b", ST,
     'const Rational sense(static_cast<int>(i == contact.a) - static_cast<int>(i == contact.b));',
     'const Rational sense(static_cast<int>(i == contact.a));'),
    ("no_action_on_a", ST,
     'const Rational sense(static_cast<int>(i == contact.a) - static_cast<int>(i == contact.b));',
     'const Rational sense(-static_cast<int>(i == contact.b));'),
    ("mask_at_reference_not_anchor", ST,
     'wrench[2] - geometry2::cross(offset, {wrench[0], wrench[1]})};',
     'wrench[2] + Rational(0) * geometry2::cross(offset, {wrench[0], wrench[1]})};'),
    ("drop_alpha_column", ST,
     'problem.A[row++][column] = live[k];',
     'problem.A[row++][column] = Rational(0) * live[k];'),
    ("dead_load_sign", ST, 'problem.b.push_back(-dead[k]);', 'problem.b.push_back(dead[k]);'),
]


def sh(cmd, log, timeout=3600):
    t = time.perf_counter()
    env = dict(os.environ, TEMP=str(SRC / "eab2/build/tmp"), TMP=str(SRC / "eab2/build/tmp"))
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        p = subprocess.run(cmd, cwd=SRC, stdout=f, stderr=subprocess.STDOUT, env=env, timeout=timeout)
    return p.returncode, round(time.perf_counter() - t, 1)


def tail(path, n=3):
    return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()[-n:]


def run_gates(name):
    res = dict(mutant=name)
    code, sec = sh(["cmd", "/c", r"eab2\build_eab2.bat"], OUT / f"{name}_build.log")
    text = (OUT / f"{name}_build.log").read_text(encoding="utf-8", errors="replace")
    compiled = "tests passed" in text or "tests failed" in text
    res.update(build_exit=code, build_s=sec, compiled=compiled,
               ctest=[l for l in text.splitlines() if "tests passed" in l or "***Failed" in l or "_FAIL" in l][:12])
    if not compiled:
        res["note"] = "compile failure -- invalid mutant"
        return res
    dll = str(SRC / "eab2/build/eab2.dll")
    code, sec = sh([sys.executable, "-X", "utf8", "tools/eab2_c3l3_diff.py", "--dll", dll, "--family", "all",
                    "--output", str(OUT / f"{name}_diff.json")], OUT / f"{name}_diff.log")
    res.update(diff_exit=code, diff_s=sec, diff_last=tail(OUT / f"{name}_diff.log", 1))
    code, sec = sh([sys.executable, "-X", "utf8", str(ADV), str(SRC), dll, "adversarial", str(OUT / f"{name}_adv.json")],
                   OUT / f"{name}_adv.log")
    res.update(adv_exit=code, adv_s=sec, adv_last=tail(OUT / f"{name}_adv.log", 1))
    try:
        adv = json.loads((OUT / f"{name}_adv.json").read_text(encoding="utf-8"))
        res["adv_bad_cases"] = [r["case"] for r in adv["rows"] if r["bad"]][:40]
    except Exception as e:
        res["adv_bad_cases"] = ["unreadable: %s" % e]
    return res


def main():
    results = []
    for name, rel, old, new in MUTANTS:
        if ONLY and name not in ONLY:
            continue
        path = SRC / rel
        original = path.read_bytes()
        text = original.decode("utf-8")
        assert text.count(old) == 1, (name, text.count(old))
        path.write_bytes(text.replace(old, new).encode("utf-8"))
        try:
            r = run_gates(name)
        finally:
            path.write_bytes(original)
        results.append(r)
        print(json.dumps(r), flush=True)
        (OUT / "mutation_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    # restore baseline build and re-run ctest
    code, sec = sh(["cmd", "/c", r"eab2\build_eab2.bat"], OUT / "restore_build.log")
    print("RESTORE", code, tail(OUT / "restore_build.log", 3), flush=True)


if __name__ == "__main__":
    main()
