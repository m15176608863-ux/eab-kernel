"""C3-L1 exact LP DLL differential gate, outside pytest.

The expected path uses only Python eab.lp and existing Python test generators.
The certificate checker uses Fraction and the ORIGINAL matrices. ctypes is used
only to obtain C++ answers: no DLL helper contributes to expected values.
Nonunique primal/dual/basis choices are not byte-equality promises; every field
that represents a certificate is checked by its exact mathematical definition.

Run: python tools/eab2_opt_diff.py --dll ABSOLUTE_TEST_DLL --output REPORT.json
The default selects all listed LP-model families, not all limit_load modelling,
resolvability or tolerance-policy assertions in the source pytest modules.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes as C
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "src", ROOT / "tools", ROOT / "tests"):
    sys.path.insert(0, str(directory))
from eab import lp  # noqa: E402
from eab2_diff import AbiInfo, Context, Options, Text  # noqa: E402
from eab2_diff_c1 import ExactResult, initialized  # noqa: E402


@dataclass(frozen=True)
class Case:
    family: str
    name: str
    A: tuple
    b: tuple
    c: tuple
    maximize: bool = False


def case(family, name, A, b, c, maximize=False):
    return Case(family, name, tuple(tuple(F(v) for v in row) for row in A),
                tuple(map(F, b)), tuple(map(F, c)), maximize)


def source_module(name):
    spec = importlib.util.spec_from_file_location("c3l1_" + name, ROOT / "tests" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def corpus():
    cert = source_module("test_lp_certificates")
    scale = source_module("test_lp_scale")
    loud = source_module("test_lp_fail_loud")
    basic = source_module("test_lp")
    for name, model in cert.INFEASIBLE_LPS.items():
        yield case("certificate_farkas", name, *model)
    for name, model in cert.REVERIFY3_LPS.items():
        yield case("certificate_reverify3", name, *model)
    for seed in range(12):
        yield case("basic_random", str(seed), *basic._random_lp(seed))
    for eta, delta in itertools.product((1e-5, 1e-8, 1e-10), (1e-10, 5e-11, 1e-11)):
        A = [[1, -1, -1, 0], [0, eta, eta, 1]]
        for order, c in enumerate(([-1, 1, 1-delta, 0], [-1, 1-delta, 1, 0])):
            yield case("certificate_huge_step", f"{eta}/{delta}/{order}", A, [1, 1], c)
    for delta in (1e-6, 1e-8, 1e-10, 1e-11, 1e-12, 1e-13):
        yield case("certificate_near_parallel", str(delta), [[1, -1, 0], [-1, 1+delta, -1]], [1, 0], [0, 1, 0])
    cycling = {
        "beale": ([[1, 0, 0, F(1, 4), -8, -1, 9], [0, 1, 0, F(1, 2), -12, F(-1, 2), 3], [0, 0, 1, 0, 0, 1, 0]],
                  [0, 0, 1], [0, 0, 0, F(-3, 4), 20, F(-1, 2), 6]),
        "kuhn": ([[-2, -9, 1, 9, 1, 0, 0], [F(1, 3), 1, F(-1, 3), -2, 0, 1, 0], [2, 3, -1, -12, 0, 0, 1]],
                 [0, 0, 2], [-2, -3, 1, 12, 0, 0, 0]),
        "chvatal": ([[F(1, 2), F(-11, 2), F(-5, 2), 9, 1, 0, 0], [F(1, 2), F(-3, 2), F(-1, 2), 1, 0, 1, 0], [1, 0, 0, 0, 0, 0, 1]],
                    [0, 0, 1], [-10, 57, 9, 24, 0, 0, 0]),
    }
    for name, model in cycling.items():
        yield case("certificate_cycling", name, *model)
    rng = random.Random(4)
    for index in range(200):
        m, n = rng.randint(2, 4), rng.randint(2, 6)
        base = [[rng.randint(-2, 2) for _ in range(n)] for _ in range(m)]
        A = base + [[2 * v for v in base[rng.randrange(m)]]]
        x = [rng.randint(0, 1) for _ in range(n)]
        b = [sum(a*v for a, v in zip(row, x)) for row in A]
        c = [rng.randint(-3, 3) for _ in range(n)]
        yield case("certificate_redundant", str(index), A, b, c)
    tiny = F(1, 10**400)
    edge_models = {
        "empty": ([], [], []),
        "no_rows_finite": ([], [], [0, 2]),
        "no_rows_tiny_unbounded": ([], [], [-tiny]),
        "no_columns_feasible": ([[], []], [0, 0], []),
        "no_columns_infeasible": ([[], []], [0, -tiny], []),
        "negative_rhs_underflow": ([[1, -1]], [-tiny], [1, 0]),
        "display_overflow": ([[1e-300, 1, -1]], [1e10], [0, 1, 1]),
        "candidate_overflow": ([[1e-300]], [1e-300], [1e10]),
        "dual_underflow_positive": ([[1e300, 1e300]], [1e300], [1e-25, 5e-26]),
        "dual_underflow_negative": ([[1e300, 1e300]], [1e300], [-1e-25, -5e-26]),
        "ray_not_improving": ([[1, -1]], [1], [0, 1]),
        "artificial_ray_blocker": ([[-1, 1], [0, 1]], [0, 0], [-1, 0]),
        "feasible_unbounded_nonzero": ([[1, -1, 0], [0, 1, -1]], [7, 3], [-2, 0, 0]),
    }
    for name, model in edge_models.items():
        yield case("certificate_exact_edges", name, *model)
        yield case("certificate_max_sign", name, model[0], model[1], [-F(v) for v in model[2]], True)
    for seed in scale.SEEDS:
        A, b, c = scale._system(seed)
        for amount in scale.SCALES:
            yield case("scale_rhs", f"{seed}/{amount}", A, [amount*v for v in b], c)
        A2, b2 = [row[:] for row in A], b[:]
        for i in (1, 3, 5):
            A2[i] = [1e-3*v for v in A2[i]]
            b2[i] *= 1e-3
        for amount in scale.SCALES:
            yield case("scale_rows", f"{seed}/{amount}", A2, [amount*v for v in b2], c)
        for exponent in (10, 20, 40):
            yield case("scale_binary_rhs", f"{seed}/{exponent}", A, [4 * 2**exponent * v for v in b], c)
    for amount in scale.SCALES:
        A, b, c = scale._system(7, zero_row=True)
        yield case("scale_zero_rhs", str(amount), A, [amount*v for v in b], c)
    for seed, factor, amount in itertools.product(scale.COLSCALE_SEEDS, (1e2, 1e4, 1e-4), (1.0, 1e4)):
        A, b, c = scale._system(seed)
        for j in random.Random(1000 + seed).sample(range(len(c)), 10):
            for row in A:
                row[j] *= factor
            c[j] *= factor
        yield case("scale_columns", f"{seed}/{factor}/{amount}", A, [amount*v for v in b], c)
    for seed, index in cert.SI_WORST:
        contacts, dead, live, dimension, k = cert._si_case(seed, index)
        yield case("certificate_si_worst", f"{seed}/{index}", *cert._exact_limit_lp(contacts, dead, live, dimension, k), True)
    for index, (length, cohesion, seed, offset) in enumerate(cert.OLD_GRID):
        rotation = cert._rot(seed) if seed is not None else ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
        contacts, dead, live, _ = cert._block(length, cohesion, .6, offset, rotation)
        A, b, c, _ = cert._old_formulation(contacts, dead, live)
        yield case("certificate_old_scale", str(index), A, b, c, True)
    for (force, geometry), k in itertools.product(((1., 1.), (1e4, 1.), (1e4, 1e-3), (1e-3, 1e3)), (5, 16)):
        contacts, dead, live, _ = loud._cohesive_block(force, geometry)
        yield case("fail_loud_cohesive", f"{force}/{geometry}/{k}", *cert._exact_limit_lp(contacts, dead, live, 3, k), True)
    for k, angle in itertools.product((4, 6, 8, 12, 16, 32), (0., .1, .3, .5, .785)):
        contacts, dead, live, _ = loud._si_block(5., 1e5, .6, th=angle)
        yield case("fail_loud_si", f"{k}/{angle}", *cert._exact_limit_lp(contacts, dead, live, 3, k), True)
    origin = (0., 0., 0.)
    contacts = [cert.LimitContact((sx, .6*sy, 0.), (0., 0., 1.), 1., cohesion=.01, area=1.)
                for sx in (-1., 1.) for sy in (-1., 1.)]
    dead = cert.wrench((0., 0., -10.), (0., 0., .5), origin, 3)
    live = cert.wrench((math.cos(.3), math.sin(.3), 0.), origin, origin, 3)
    for k in (8, 64, 127, 128, 129, 256):
        yield case("fail_loud_fine_cone", str(k), *cert._exact_limit_lp(contacts, dead, live, 3, k), True)
    offsets = ((0., 0., 0.), (50., 80., 20.), (300., 500., 120.), (1e3, 2e3, 300.), (2e3, 3e3, 500.))
    for index, (offset, length, cohesion, friction, angle) in enumerate(itertools.product(
            offsets, (1., 5., 20.), (0., 1e4, 1e5, 1e6), (.3, .6), (.3, 1.))):
        contacts, dead, live, _ = loud._si_block(length, cohesion, friction, offset, angle)
        yield case("fail_loud_site", str(index), *cert._exact_limit_lp(contacts, dead, live, 3, 8), True)


class OptInput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("sense", C.c_uint32), ("reserved", C.c_uint32),
                ("rows", C.c_uint64), ("columns", C.c_uint64), ("max_pivots", C.c_uint64),
                ("value_count", C.c_uint64), ("value_stride", C.c_uint64), ("values", C.POINTER(Text))]


class Dll:
    def __init__(self, path):
        if not path.is_absolute() or not path.is_file():
            raise ValueError("--dll must be an existing absolute test DLL")
        self.lib = C.CDLL(str(path))
        for name, arguments in {
            "get_abi_info": [C.POINTER(AbiInfo)],
            "context_create": [C.POINTER(Options), C.POINTER(Context)],
            "context_destroy": [Context],
            "result_destroy": [Context, Context],
            "opt_solve_exact": [Context, C.POINTER(OptInput), C.POINTER(ExactResult)],
        }.items():
            function = getattr(self.lib, "eab2_" + name)
            function.argtypes, function.restype = arguments, C.c_uint32
            setattr(self, name, function)
        info = initialized(AbiInfo)
        self.check(self.get_abi_info(C.byref(info)), "get_abi_info")
        self.identity = bytes(info.build_identity).decode("ascii")
        self.context = Context()
        options = initialized(Options)
        self.check(self.context_create(C.byref(options), C.byref(self.context)), "context_create")

    @staticmethod
    def check(status, label):
        if status:
            raise AssertionError(f"{label}: call_status={status}")

    def close(self):
        self.check(self.context_destroy(self.context), "context_destroy")

    def solve(self, model):
        values = [v for row in model.A for v in row] + list(model.b) + list(model.c)
        keepalive = [f"{v.numerator}/{v.denominator}".encode("ascii") for v in values]
        encoded = (Text * len(values))(*(Text(v, len(v)) for v in keepalive))
        request = initialized(OptInput)
        request.rows, request.columns, request.sense = len(model.b), len(model.c), int(model.maximize)
        request.max_pivots = 1000000
        request.value_count, request.value_stride, request.values = len(values), C.sizeof(Text), encoded
        output = initialized(ExactResult)
        started = time.perf_counter()
        self.check(self.opt_solve_exact(self.context, C.byref(request), C.byref(output)), "opt_solve_exact")
        seconds = time.perf_counter() - started
        try:
            self.check(output.call_status, "opt result")
            result = json.loads(C.string_at(output.data, output.byte_count))
            mathematical = {"optimal": 1, "infeasible": 5, "unbounded": 6}[result["status"]]
            if output.mathematical_status != mathematical:
                raise AssertionError("ABI mathematical status contradicts exact JSON")
            return result, seconds
        finally:
            self.check(self.result_destroy(self.context, output.result), "result_destroy")


def exact_vector(values):
    if not isinstance(values, list):
        raise AssertionError("rational vector must be a JSON array")
    parsed = [F(v) for v in values]
    if values != [f"{v.numerator}/{v.denominator}" for v in parsed]:
        raise AssertionError("noncanonical rational export")
    return parsed


def require(condition, message):
    # This is an executable gate, including when Python is invoked with -O.
    if not condition:
        raise AssertionError(message)


def verify(model, result):
    """Original-data algebra only; does not call any C++/Python LP helper."""
    A, b, c = model.A, model.b, model.c
    m, n = len(b), len(c)
    require(len(A) == m and all(len(row) == n for row in A), "original LP dimensions")
    x, y, ray = (exact_vector(result[key]) for key in ("x", "y", "ray"))
    dot = lambda a, z: sum((v*w for v, w in zip(a, z)), F(0))
    if result["sense"] != ("max" if model.maximize else "min"):
        raise AssertionError("objective sense lost")
    status = result["status"]
    if status == "infeasible":
        require(len(y) == m and dot(y, b) > 0, "Farkas dimensions and strict positive rhs")
        require(not x and not ray and result["objective"] is None, "infeasible nonapplicable fields")
        require(all(sum((A[i][j]*y[i] for i in range(m)), F(0)) <= 0 for j in range(n)), "Farkas original columns")
    else:
        require(len(x) == n and all(v >= 0 for v in x), "primal dimensions and nonnegativity")
        require(all(dot(row, x) == rhs for row, rhs in zip(A, b)), "original feasible point Ax=b")
        if status == "unbounded":
            require(len(ray) == n and not y and result["objective"] is None, "unbounded applicable fields")
            require(all(v >= 0 for v in ray) and all(dot(row, ray) == 0 for row in A), "unbounded nonnegative kernel ray")
            require(dot(c, ray) == (1 if model.maximize else -1), "unbounded strict improvement normalization")
            require(result["auxiliary_solves"] == 2, "unbounded auxiliary witness LP count")
        else:
            require(status == "optimal" and len(y) == m and not ray, "optimal status and applicable fields")
            value = exact_vector([result["objective"]])[0]
            require(dot(c, x) == dot(b, y) == value, "exact zero duality gap")
            for j in range(n):
                dual = sum((A[i][j]*y[i] for i in range(m)), F(0))
                require(dual >= c[j] if model.maximize else dual <= c[j], "original dual column inequality")
    require(len(result["basis"]) == m and len(set(result["basis"])) == m, "basis dimension and uniqueness")
    require(all(type(j) is int and 0 <= j < m+n for j in result["basis"]), "basis index range and type")
    for key in ("pivots", "auxiliary_solves", "max_stored_integer_bits"):
        require(type(result[key]) is int and result[key] >= 0, "integer statistics: " + key)


def python_answer(model):
    def display(value):
        try:
            return float(value)
        except OverflowError:
            return 0.0  # This is only a candidate; exact= retains the model.
    A, b, c = model.A, model.b, model.c
    solve = lp.maximize if model.maximize else lp.solve
    started = time.perf_counter()
    result = solve([[display(v) for v in row] for row in A], list(map(display, b)),
                   list(map(display, c)), exact=(A, b, c))
    seconds = time.perf_counter() - started
    objective = None
    if result.status == "optimal":
        require(result.exact_x is not None and result.exact_y is not None, "Python optimum lacks exact witnesses")
        objective = sum((v*w for v, w in zip(c, result.exact_x)), F(0))
    return result.status, objective, seconds


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--family-prefix", default="")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--source-commit", default="not_supplied")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    selected = [model for model in corpus() if model.family.startswith(args.family_prefix)]
    if args.limit is not None:
        selected = selected[:args.limit]
    if not selected:
        raise ValueError("empty selected LP corpus")
    dll = Dll(args.dll)
    sources = ("tools/eab2_opt_diff.py", "src/eab/lp.py", "tests/test_lp.py", "tests/test_lp_certificates.py",
               "tests/test_lp_scale.py", "tests/test_lp_fail_loud.py")
    report = {"schema": "eab2.c3l1.opt.diff.v1", "source_commit": args.source_commit,
              "source_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},
              "dll": str(args.dll), "dll_sha256": hashlib.sha256(args.dll.read_bytes()).hexdigest(),
              "build_identity": dll.identity, "selected": len(selected), "completed": 0,
              "family_counts": dict(Counter(model.family for model in selected)), "mismatches": [], "cases": [],
              "scope": "LP-model state and exact optimum differential; all three C++ certificates independently checked over Fraction. Nonunique witnesses checked semantically, not by basis identity. No limit_load policy or full-physics claim.",
              "timing": "One cold solve per distinct query; C++ interval includes exact JSON construction but excludes Python serialization/parsing; Python interval includes exact LP construction/candidate/certification. No speed gate."}
    started = time.perf_counter()
    try:
        for index, model in enumerate(selected, 1):
            label = model.family + "/" + model.name
            print(f"OPT_CASE_BEGIN {index}/{len(selected)} {label}", flush=True)
            actual = None
            try:
                expected, objective, python_seconds = python_answer(model)
                actual, cpp_seconds = dll.solve(model)
                verify(model, actual)
                require(actual["status"] == expected, f"state mismatch: {actual['status']} != {expected}")
                if objective is not None:
                    require(F(actual["objective"]) == objective, f"exact objective mismatch: {actual['objective']} != {objective}")
                data = json.dumps({"A": model.A, "b": model.b, "c": model.c, "max": model.maximize}, default=str, sort_keys=True)
                report["cases"].append({"name": label, "rows": len(model.b), "columns": len(model.c),
                    "model_sha256": hashlib.sha256(data.encode()).hexdigest(), "status": expected,
                    "objective": str(objective) if objective is not None else None,
                    "cpp_seconds": cpp_seconds, "python_seconds": python_seconds,
                    "pivots": actual["pivots"], "max_stored_integer_bits": actual["max_stored_integer_bits"],
                    "certificate_sha256": hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()})
                report["completed"] += 1
            except Exception as error:
                failure = args.output.parent / "tmp" / "opt_failures" / f"case_{index:04d}.json"
                write_json(failure, {"case": label, "A": [[str(v) for v in row] for row in model.A],
                    "b": list(map(str, model.b)), "c": list(map(str, model.c)), "max": model.maximize,
                    "actual": actual, "error": repr(error)})
                report["mismatches"].append({"name": label, "error": repr(error), "artifact": str(failure)})
                write_json(args.output, report)
                raise
            report["elapsed_seconds"] = time.perf_counter() - started
            write_json(args.output, report)
            print(f"OPT_CASE_PASS {index}/{len(selected)} {label}", flush=True)
        report["status_counts"] = dict(Counter(row["status"] for row in report["cases"]))
        report["last_line"] = f"OPT_DIFF selected={len(selected)} completed={report['completed']} mismatches=0"
        write_json(args.output, report)
        print(report["last_line"], flush=True)
    finally:
        dll.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"OPT_DIFF_FAIL {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
