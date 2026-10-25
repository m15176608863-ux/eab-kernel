"""Artificial nondegenerate L4 differential, not merely C++ self-assertions."""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from eab2_c3l4_diff import exact_wire, mat, vec, verify_limit_sensitivity
from eab2_c3l1_diff import verify_optimum, require


def verify_record(record):
    """Independent exact identities first, repaired Python second."""
    from eab.kernel2d.statics import LimitProblem2, solve_limit_problem2
    from eab.kernel2d.sensitivity import LimitSeed2, evaluate_sensitivity2
    raw, base, result, jet = (record[key] for key in ("problem", "base", "result", "seed"))
    A, b, c = mat(raw["A"]), vec(raw["b"]), vec(raw["c"])
    verify_optimum(A, b, c, vec(base["exact_x"]), vec(base["exact_y"]), Q(base["exact_value"]))
    seed = dict(dA=mat(jet["dA"]), db=vec(jet["db"]), dc=vec(jet["dc"]))
    require(result["method"] == "stable_basis", "artificial LP must execute the stable formula")
    verify_limit_sensitivity(dict(A=A, b=b, c=c), seed, base,
                             dict(direction_domain=dict(positive=True, negative=True)), result)
    problem = LimitProblem2(A, b, c, (), (), (), (), Q(0), None, None)
    referee_base = solve_limit_problem2(problem)
    referee = evaluate_sensitivity2(referee_base, LimitSeed2(seed["dA"], seed["db"], seed["dc"], "p"), parameter="p")
    expected = exact_wire(referee)
    for field in ("differentiability", "quality", "method", "right_derivative", "left_derivative", "reason", "tied_labels"):
        require(expected[field] == result[field], "stable differential Python/C++: " + field)
    if record["minimize"]:
        require(Q(record["ordinary_min_derivative"]) == -Q(expected["right_derivative"]), "ordinary min derivative sign mapping")
    return dict(id=record["id"], minimize=record["minimize"],
                maximize_derivative=result["right_derivative"],
                original_objective_derivative=exact_wire((-1 if record["minimize"] else 1) * Q(result["right_derivative"])),
                original_unscaled_primal_dual_verified=True)


def run(executable, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    call = subprocess.run([str(executable.resolve()), "--differential-stable"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    output.with_suffix(".raw.jsonl").write_bytes(call.stdout)
    require(call.returncode == 0, "stable C++ driver execution (not a semantic failure): " + call.stderr.decode("utf-8", errors="replace"))
    records = [json.loads(line) for line in call.stdout.decode("utf-8").splitlines() if line.strip()]
    require(len(records) >= 4 and len({r["id"] for r in records}) == len(records), "stable differential inventory")
    rows, failures = [], []
    for record in records:
        try:
            rows.append(verify_record(record))
        except (AssertionError, ValueError) as error:
            failures.append(dict(id=record["id"], error=str(error)))
    last = f"C3L4_STABLE_DIFF sensitivity={len(records)} mismatch={len(failures)}"
    result = dict(complete=True, executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                  rows=rows, failures=failures, last_line=last)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(last, flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.executable, args.output))
