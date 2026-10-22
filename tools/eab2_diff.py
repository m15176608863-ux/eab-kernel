"""Independent C0 DLL differential runner; deliberately outside pytest.

Expected results are computed only by the existing Python implementation and
standard-library Fraction arithmetic. ctypes is used exclusively on the actual
result path. No C++ predicate, rounding, or exact helper supplies an expectation.

Usage: python tools/eab2_diff.py --dll ABSOLUTE_TEST_DLL --output report.json
The DLL is mandatory: missing DLLs, unsupported capabilities, ABI mismatches,
and load failures are errors, never skipped tests. Counts and elapsed times are
observations, not sample quotas or performance gates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes as C
from dataclasses import dataclass, replace
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab import construction as judge  # noqa: E402
from eab.kernel2d.geom import orient2d  # noqa: E402
from eab.numeric_domain import ConstructionDomainError, exact_input  # noqa: E402
from eab.predicates import cross2_sign, dot2_sign  # noqa: E402


VERSION = 1
SEED = 0xEAB2C0
SENTINEL = 0xA55AA55AA55AA55A
OPERATIONS = {
    1: "scalar_rational", 2: "scalar_algebraic_rational_compare",
    3: "scalar_algebraic_sqrt_compare", 4: "ratio_rational",
    5: "vector_rational", 6: "sqrt_rational", 7: "norm_rational",
    8: "unit_rational", 9: "normalized_difference_rational",
    10: "binary64_decode_roundtrip", 11: "orient2d", 12: "cross2_sign",
    13: "dot_sign", 14: "aabb2",
}
STATUS_NAMES = {
    0: "OK", 1: "INVALID_INPUT", 2: "INVALID_HANDLE", 3: "UNSUPPORTED",
    4: "CONSTRUCTION_RANGE", 5: "RESOURCE_LIMIT", 6: "FP_CONTRACT",
    7: "INTERNAL_ERROR", 8: "CANCELLED",
}
CORPUS_SOURCES = {
    "r9_rounding_cells": "tests/test_r9fix_construction_rounding.py::_rounding_cells",
    "r9_subnormal_sqrt": "tests/test_r9fix_construction_rounding.py::test_r9_exact_sqrt_non_square_subnormal_certificates",
    "r9_vectors": "tests/test_r9fix_construction_rounding.py::test_r9_norm_and_unit_round_exact_final_components",
    "r9_range_policy": "tests/test_r9fix_construction_rounding.py::test_r9_constructor_range_policy_is_explicit",
    "r9_compound": "tests/test_r9fix_compound_construction.py",
    "r8_frozen_projection": "tests/test_r8fix_frozen.py (numeric closed forms only, not geometry/jet coverage)",
    "boundary_matrix": "C0 binary64, exponent, binade, invalid-input and asymmetric geometry matrix",
    "fixed_seed_random": "random.Random(0xEAB2C0); finite binary64 bit strings and exact rational values",
    "invariance_exact_transform": "same RNG stream after random corpus; rational SO(2), positive scaling, large translation; exact transformed-input Python oracle",
}


class Context(C.Structure):
    _fields_ = [("owner", C.c_uint64), ("id", C.c_uint64),
                ("generation", C.c_uint64), ("type", C.c_uint32),
                ("reserved", C.c_uint32)]


class Options(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("flags", C.c_uint32), ("reserved", C.c_uint32)]


class ErrorInfo(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("code", C.c_uint32), ("reserved", C.c_uint32),
                ("index", C.c_uint64), ("field", C.c_char * 48)]


class AbiInfo(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("requested_capabilities", C.c_uint64),
                ("supported_capabilities", C.c_uint64),
                ("unsupported_capabilities", C.c_uint64),
                ("context_size", C.c_uint32), ("context_options_size", C.c_uint32),
                ("error_info_size", C.c_uint32), ("binary64_bits", C.c_uint32),
                ("pointer_bits", C.c_uint32), ("reserved", C.c_uint32),
                ("build_identity", C.c_char * 192)]


class Text(C.Structure):
    _fields_ = [("data", C.c_char_p), ("length", C.c_uint64)]


class NumericInput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("operation", C.c_uint32), ("encoding", C.c_uint32),
                ("flags", C.c_uint32), ("reserved", C.c_uint32),
                ("value_count", C.c_uint64), ("value_stride", C.c_uint64),
                ("values", C.POINTER(Text))]


class NumericOutput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("call_status", C.c_uint32), ("mathematical_status", C.c_uint32),
                ("display_status", C.c_uint32), ("reserved", C.c_uint32),
                ("bits_capacity", C.c_uint64), ("bits_count", C.c_uint64),
                ("bits", C.POINTER(C.c_uint64))]


class BatchInput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("item_count", C.c_uint64), ("item_stride", C.c_uint64),
                ("items", C.POINTER(NumericInput))]


class BatchOutput(C.Structure):
    _fields_ = [("struct_size", C.c_uint32), ("abi_version", C.c_uint32),
                ("item_capacity", C.c_uint64), ("item_stride", C.c_uint64),
                ("item_count", C.c_uint64), ("items", C.POINTER(NumericOutput))]


def bits(value: float) -> str:
    return struct.pack(">d", value).hex()


def from_bits(value: str) -> float:
    return struct.unpack(">d", bytes.fromhex(value))[0]


def rational_text(value) -> str:
    q = F(value)
    return f"{q.numerator}/{q.denominator}"


def sign(value) -> int:
    return (value > 0) - (value < 0)


@dataclass(frozen=True)
class Case:
    case_id: str
    source: str
    operation: int
    values: tuple[str, ...]
    encoding: int = 2
    allow_underflow: bool = False
    protocol_status: int | None = None

    def description(self) -> dict:
        return {"schema": "eab2.case.v1", "version": 1,
                "case_id": self.case_id, "source": self.source,
                "profile": "c0_numeric", "query": OPERATIONS.get(self.operation, "unsupported"),
                "operation": self.operation, "encoding": self.encoding,
                "values": list(self.values), "allow_underflow": self.allow_underflow}


def corpus(random_samples: int) -> list[Case]:
    cases: list[Case] = []

    def add(source, operation, values, allow=False, encoding=2, protocol=None, label=""):
        texts = tuple(bits(float(v)) if encoding == 1 else rational_text(v) for v in values)
        cases.append(Case(f"{source}/{len(cases):05d}/{label or OPERATIONS[operation]}",
                          source, operation, texts, encoding, allow, protocol))

    # Rebuild the existing test's exact 48-cell matrix without importing pytest.
    anchors = [0.0, math.ulp(0.0), 2 * math.ulp(0.0),
               math.nextafter(sys.float_info.min, 0.0), sys.float_info.min,
               math.ldexp(1.0, -600), 1.0, math.nextafter(1.0, math.inf),
               3 / 7, math.ldexp(1.0, 600),
               math.nextafter(sys.float_info.max, 0.0), sys.float_info.max]
    cells = []
    for anchor in anchors:
        low = F(anchor)
        nxt = math.nextafter(anchor, math.inf)
        high = F(nxt) if math.isfinite(nxt) else F(2) ** 1024
        middle, jitter = (low + high) / 2, (high - low) / 16
        cells.extend((low, middle - jitter, middle, middle + jitter))
    for q in cells:
        for allow in (False, True):
            for polarity in (1, -1):
                for op in (1, 2):
                    add("r9_rounding_cells", op, (polarity * q,), allow)
                add("r9_rounding_cells", 4, (7 * polarity * q, 7), allow)
            for op in (3, 6):
                add("r9_rounding_cells", op, (q * q,), allow)
            add("r9_rounding_cells", 5, (q, -q, F(1, 3)), allow)
            # Final norm and compound result traverse the same cells exactly.
            add("r9_rounding_cells", 7, (q, 0), allow)
            add("r9_rounding_cells", 9, (q + 1, 1, 1), allow)
    for m in range(1, 25):
        square = F(m * m, 3) * F(2) ** -2148
        for op in (3, 6):
            add("r9_subnormal_sqrt", op, (square,))

    vectors = [
        (F(2) ** -1074,) * 3, (F(2) ** -1075,) * 3,
        (F(2) ** -600, -F(2) ** -601, F(2) ** -602),
        (F(3), F(-4), F(12)),
        (F(2) ** 600, F(2) ** 599, -F(2) ** 598),
        (F(sys.float_info.max),) * 2,
        (F(2) ** 2000, -F(2) ** 2000, F(2) ** 926),
        (F(1), F(2) ** -1075, -F(2) ** -1074),
    ]
    for vector in vectors:
        for op in (5, 7, 8):
            for allow in (False, True):
                add("r9_vectors", op, vector, allow)
    for operation in (5, 7, 8):
        add("boundary_matrix", operation, (), label="empty_vector_contract")
    for polarity in (1, -1):
        tiny = polarity * F(2) ** -1076
        for allow in (False, True):
            for op in (1, 2):
                add("r9_range_policy", op, (tiny,), allow)
            add("r9_range_policy", 6, (tiny * tiny,), allow)
            for op in (5, 8):
                add("r9_range_policy", op, (1, tiny), allow)

    maximum, ulp = F(sys.float_info.max), F(2) ** 971
    for polarity in (-1, 1):
        add("r9_compound", 9, (polarity * (maximum + ulp / 4 + 1), 1, polarity))
    big = F(2) ** 1100
    for values in ((big, 1, big - 1), (-big, 1, 1 - big),
                   (maximum + F(2) ** 970 + 1, 1, 1),
                   (1 + F(2) ** -1076, 1, 1)):
        for allow in (False, True):
            add("r9_compound", 9, values, allow)

    # Project the named frozen-geometry tests to their exact scalar boundaries.
    # This is not a claim that the C0 suite reruns geometry or Dual APIs.
    for magnitude in (F(10) ** 20, F(10) ** 200, F(10) ** 400):
        for polarity in (-1, 1):
            for allow in (False, True):
                nn = magnitude * magnitude + 1
                add("r8_frozen_projection", 9,
                    (polarity * nn, nn, polarity * magnitude), allow,
                    label="irrational_cancellation")
                add("r8_frozen_projection", 9,
                    (polarity * (magnitude + 1), 1, polarity * magnitude), allow,
                    label="unrepresentable_intermediate")
    for polarity in (-1, 1):
        for step in (0, 1, 2):
            exact = 1 + (F(step) + F(1, 2)) * F(math.ulp(1.0))
            add("r8_frozen_projection", 9,
                (polarity * (F(10 ** 20) + exact), 1, polarity * F(10 ** 20)),
                label="halfway_ties_to_even")
    for scale in (F(2) ** -200, F(1), F(2) ** 200):
        for excess in (-10000, -1, 0, 1, 10000):
            add("r8_frozen_projection", 9,
                ((F(10 ** 20) + excess) * scale, 1, F(10 ** 20) * scale),
                label="scaled_margin_before_display")
    for c, s, magnitude, gap in ((F(3, 5), F(4, 5), F(10 ** 20), F(1)),
                                 (F(4, 5), F(3, 5), F(10 ** 20), F(1)),
                                 (F(3, 5), F(4, 5), F(10 ** 8), F(1, 10 ** 9))):
        point = (c * gap - s * magnitude, s * gap + c * magnitude)
        projection = point[0] * c + point[1] * s
        add("r8_frozen_projection", 9, (projection, c * c + s * s, 0),
            label="large_tangent_exact_projection")
        add("r8_frozen_projection", 8, (c, s), label="raw_normal_unit")
    for polarity in (-1, 1):
        add("r8_frozen_projection", 4, (polarity * F(1, 2), F(4, 5)),
            label="exact_plane_ratio")

    # Explicit finite bits include both zero signs and every binary64 boundary.
    bit_values = ["0000000000000000", "8000000000000000", "0000000000000001",
                  "8000000000000001", "000fffffffffffff", "0010000000000000",
                  "0010000000000001", "3fefffffffffffff", "3ff0000000000000",
                  "3ff0000000000001", "3fffffffffffffff", "4000000000000000",
                  "7fefffffffffffff", "ffefffffffffffff"]
    for text in bit_values:
        for op in (1, 2, 10):
            add("boundary_matrix", op, (from_bits(text),), encoding=1)
    for exponent in (-2200, -1076, -1075, -1074, -1022, -53, -1, 0, 53, 1023, 1024, 2200):
        q = F(2) ** exponent
        for op in (1, 2, 3, 6):
            for allow in (False, True):
                add("boundary_matrix", op, (q,), allow)
    # Non-symmetric, translated, rotated and small-feature/large-coordinate data.
    base = ((F(1, 7), F(-2, 3)), (F(19, 11), F(5, 13)), (F(-3, 17), F(23, 19)))
    for scale in (F(2) ** -200, F(1), F(2) ** 200):
        for shift in (0, 10 ** 3, 10 ** 5, 10 ** 6):
            points = tuple((scale * (F(3, 5) * x - F(4, 5) * y) + shift,
                            scale * (F(4, 5) * x + F(3, 5) * y) - 3 * shift)
                           for x, y in base)
            flat = tuple(v for point in points for v in point)
            add("boundary_matrix", 11, flat)
            add("boundary_matrix", 11, flat[2:4] + flat[0:2] + flat[4:])
            add("boundary_matrix", 14, flat)
            add("boundary_matrix", 12, flat[:4])
            add("boundary_matrix", 13, flat[:4])
    for values in ((1, 1, 2, 2), (1, 1, -1, 1),
                   (F(2) ** -1074, 0, 0, F(2) ** -1074),
                   (F(2) ** 1023, 1, F(2) ** 1023, -1)):
        for op in (12, 13):
            add("boundary_matrix", op, values)
    for values in ((0, 0, 1, 1, 2, 2), (1, 3, 1, 3, -7, 11)):
        add("boundary_matrix", 11, values)
    for values in ((F(1, 3),), (F(3), F(-4), F(12)),
                   (F(2) ** 1023, F(2) ** -1074, F(-7, 13), F(11, 17))):
        add("boundary_matrix", 13, values + tuple(-v for v in values))
        add("boundary_matrix", 13, values + values)
    # Domain failures must not be confused with a successful mathematical false.
    for operation, values in ((3, (-1,)), (6, (-1,)), (4, (1, 0)),
                               (8, (0, 0)), (9, (1, 0, 0)), (9, (1, -1, 0))):
        add("boundary_matrix", operation, values)
    for text in ("7ff0000000000000", "fff0000000000000", "7ff8000000000000",
                 "7ff0000000000001", "3FF0000000000000", "000000000000000", "0x3ff0000000000000"):
        cases.append(Case(f"boundary_matrix/{len(cases):05d}/invalid_bits",
                          "boundary_matrix", 10, (text,), 1, False, 1))
    for text in ("1/0", "2/4", "0/2", "-0/1", "01/1", "+1/1", "1/-2", "1", "1/1 "):
        cases.append(Case(f"boundary_matrix/{len(cases):05d}/invalid_rational",
                          "boundary_matrix", 1, (text,), 2, False, 1))
    cases.append(Case(f"boundary_matrix/{len(cases):05d}/unsupported_operation",
                      "boundary_matrix", 0xFFFF, ("1/1",), 2, False, 3))

    rng = random.Random(SEED)

    def finite():
        raw = rng.getrandbits(64)
        while (raw >> 52) & 0x7FF == 0x7FF:
            raw = rng.getrandbits(64)
        return from_bits(f"{raw:016x}")

    def rational():
        return F(rng.randint(-(1 << 54), 1 << 54), rng.randrange(1, 1 << 28)) * F(2) ** rng.randint(-1200, 1200)

    for index in range(random_samples):
        floats = tuple(finite() for _ in range(6))
        for operation, values in ((1, floats[:1]), (10, floats[:1]),
                                  (5, floats[:3]), (7, floats[:3]), (8, floats[:3]),
                                  (11, floats), (12, floats[:4]), (13, floats[:4]),
                                  (13, floats),
                                  (14, floats)):
            add("fixed_seed_random", operation, values, bool(index % 2), 1)
        a, b, c = (rational() for _ in range(3))
        b = b or F(1)
        for operation, values in ((1, (a,)), (2, (a,)), (3, (abs(a),)),
                                  (4, (a, b)), (5, (a, b, c)), (6, (abs(a),)),
                                  (7, (a, b, c)), (8, (a, b, c)),
                                  (9, (a, b * b, c))):
            add("fixed_seed_random", operation, values, bool(index % 2))

    # Continue (do not reseed) the one fixed-seed generator. Rational half-angle
    # rotations are exactly orthogonal: rounded float rotations are NOT assumed
    # to preserve geometry. AABB is recomputed, not claimed rotation-invariant.
    for rotation_index in range(8):
        t = F(rng.randint(-101, 101), rng.randint(1, 97))
        c, s = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
        if c * c + s * s != 1:
            raise RuntimeError("invalid exact rotation in generated corpus")
        for scale in (F(2) ** -200, F(1), F(2) ** 200):
            for shift in (0, 10 ** 3, 10 ** 5, 10 ** 6):
                points = tuple((scale * (c * x - s * y) + shift,
                                scale * (s * x + c * y) - 3 * shift)
                               for x, y in base)
                flat = tuple(v for point in points for v in point)
                left = tuple(points[1][axis] - points[0][axis] for axis in (0, 1))
                right = tuple(points[2][axis] - points[0][axis] for axis in (0, 1))
                label = f"rotation={rotation_index}/scale={rational_text(scale)}/shift={shift}"
                for operation, values in ((11, flat), (14, flat),
                                          (12, left + right), (13, left + right),
                                          (7, left), (8, left)):
                    add("invariance_exact_transform", operation, values, label=label)
    return cases


def expected(case: Case) -> dict:
    if case.protocol_status is not None:
        status = case.protocol_status
        return {"call_status": status, "mathematical_status": 0,
                "display_status": 2 if status == 4 else 0, "bits": []}
    values = tuple(from_bits(v) if case.encoding == 1 else F(v) for v in case.values)
    kw = {"allow_underflow": case.allow_underflow}
    op = case.operation
    try:
        if op == 1:
            result = judge.scalar_rational(values[0], **kw)
        elif op == 2:
            q = exact_input(values[0], "differential algebraic rational")
            result = judge.scalar_algebraic(lambda x: sign(q - x), **kw)
        elif op == 3:
            q = exact_input(values[0], "differential algebraic root")
            if q < 0:
                raise ValueError("negative radical")
            result = judge.scalar_algebraic(lambda x: 1 if x < 0 else sign(q - x * x), **kw)
        elif op == 4:
            result = judge.ratio_rational(*values, **kw)
        elif op == 5:
            result = judge.vector_rational(values, **kw)
        elif op == 6:
            result = judge.sqrt_rational(values[0], **kw)
        elif op == 7:
            result = judge.norm_rational(values, **kw)
        elif op == 8:
            result = judge.unit_rational(values, **kw)
        elif op == 9:
            result = judge.normalized_difference_rational(*values, **kw)
        elif op == 10:
            result = judge.scalar_rational(exact_input(values[0], "decode input"), **kw)
        elif op == 11:
            result = float(orient2d(values[:2], values[2:4], values[4:6]))
        elif op == 12:
            result = float(cross2_sign(values[:2], values[2:4]))
        elif op == 13:
            half = len(values) // 2
            if half == 2:
                result = float(dot2_sign(values[:2], values[2:]))
            else:
                # No generic public Python dot-sign API: exact Fraction is the
                # independent mathematical oracle outside the two-dimensional API.
                result = float(sign(sum(F(a) * F(b) for a, b in zip(values[:half], values[half:]))))
        elif op == 14:
            # Exact interval extrema; display conversion occurs only at the end.
            xs, ys = tuple(map(F, values[::2])), tuple(map(F, values[1::2]))
            result = judge.vector_rational((min(xs), min(ys), max(xs), max(ys)), **kw)
        else:
            raise RuntimeError(f"missing independent oracle for operation {op}")
    except ConstructionDomainError:
        return {"call_status": 4, "mathematical_status": 0, "display_status": 2, "bits": []}
    except (ValueError, ZeroDivisionError):
        return {"call_status": 1, "mathematical_status": 0, "display_status": 0, "bits": []}
    outputs = result if isinstance(result, tuple) else (result,)
    # C1E display-only refinement: Python's strict construction oracle rejects
    # a nonzero value rounding to zero; opt-in success must identify that zero.
    # No C++ helper participates in this expectation and no math contract changes.
    underflow_zero = case.allow_underflow and expected(replace(case, allow_underflow=False))["call_status"] == 4
    return {"call_status": 0, "mathematical_status": 1, "display_status": 3 if underflow_zero else 1,
            "bits": [bits(value) for value in outputs]}


def load_library(path: Path):
    if not path.is_absolute():
        raise ValueError("--dll must be an explicit absolute path")
    path = path.resolve(strict=True)
    dll = C.CDLL(str(path))
    signatures = {
        "eab2_get_abi_info": [C.POINTER(AbiInfo)],
        "eab2_self_test": [],
        "eab2_context_create": [C.POINTER(Options), C.POINTER(Context)],
        "eab2_context_destroy": [Context],
        "eab2_numeric_batch": [Context, C.POINTER(BatchInput), C.POINTER(BatchOutput)],
    }
    for name, argument_types in signatures.items():
        function = getattr(dll, name)
        function.argtypes, function.restype = argument_types, C.c_uint32
    info = AbiInfo(struct_size=C.sizeof(AbiInfo), abi_version=VERSION,
                   requested_capabilities=3)
    status = dll.eab2_get_abi_info(C.byref(info))
    if status:
        raise RuntimeError(f"get_abi_info failed: {STATUS_NAMES.get(status, status)}")
    checks = {
        "struct_size": (info.struct_size, C.sizeof(AbiInfo)),
        "abi_version": (info.abi_version, VERSION),
        "context_size": (info.context_size, C.sizeof(Context)),
        "context_options_size": (info.context_options_size, C.sizeof(Options)),
        "error_info_size": (info.error_info_size, C.sizeof(ErrorInfo)),
        "binary64_bits": (info.binary64_bits, 64),
        "pointer_bits": (info.pointer_bits, 8 * C.sizeof(C.c_void_p)),
    }
    if any(actual != wanted for actual, wanted in checks.values()):
        raise RuntimeError(f"ABI mismatch: {checks}")
    if info.supported_capabilities & 3 != 3 or info.unsupported_capabilities & 3:
        raise RuntimeError("DLL does not support both context and test numeric capabilities")
    status = dll.eab2_self_test()
    if status:
        raise RuntimeError(f"self_test failed: {STATUS_NAMES.get(status, status)}")
    return dll, {"checks": checks, "supported_capabilities": info.supported_capabilities,
                 "unsupported_capabilities": info.unsupported_capabilities,
                 "build_identity": bytes(info.build_identity).decode("ascii")}


def run_batch(dll, context: Context, cases: list[Case]) -> tuple[list[dict], float]:
    # Respect deterministic C1E parsing work budgets without weakening coverage.
    # Every selected case executes; batching is transport only.
    groups, group, work, values = [], [], 0, 0
    for case in cases:
        cost = sum(len(v) ** 2 for v in case.values)
        if group and (work + cost > 67108864 or values + len(case.values) > 65536):
            groups.append(group)
            group, work, values = [], 0, 0
        group.append(case)
        work += cost
        values += len(case.values)
    if group:
        groups.append(group)
    if len(groups) > 1:
        results, elapsed = [], 0.0
        for group in groups:
            rows, seconds = run_batch(dll, context, group)
            results.extend(rows)
            elapsed += seconds
        return results, elapsed
    inputs = (NumericInput * len(cases))()
    outputs = (NumericOutput * len(cases))()
    text_arrays, byte_strings, buffers = [], [], []
    for index, case in enumerate(cases):
        encoded = [value.encode("ascii") for value in case.values]
        texts = (Text * len(encoded))(*(Text(value, len(value)) for value in encoded))
        capacity = max(4, len(case.values))
        buffer = (C.c_uint64 * capacity)(*([SENTINEL] * capacity))
        # Keep every pointee alive until the real FFI call has returned.
        byte_strings.append(encoded)
        text_arrays.append(texts)
        buffers.append(buffer)
        inputs[index] = NumericInput(C.sizeof(NumericInput), VERSION, case.operation,
                                     case.encoding, int(case.allow_underflow), 0,
                                     len(texts), C.sizeof(Text), texts)
        outputs[index] = NumericOutput(C.sizeof(NumericOutput), VERSION, 0, 0, 0, 0,
                                      capacity, 0, buffer)
    input_batch = BatchInput(C.sizeof(BatchInput), VERSION, len(cases), C.sizeof(NumericInput), inputs)
    output_batch = BatchOutput(C.sizeof(BatchOutput), VERSION, len(cases), C.sizeof(NumericOutput), 0, outputs)
    started = time.perf_counter()
    status = dll.eab2_numeric_batch(context, C.byref(input_batch), C.byref(output_batch))
    elapsed = time.perf_counter() - started
    if status:
        raise RuntimeError(f"numeric_batch structural failure: {STATUS_NAMES.get(status, status)}")
    if output_batch.item_count != len(cases):
        raise RuntimeError(f"numeric_batch returned {output_batch.item_count} of {len(cases)} items")
    actual = []
    for index, output in enumerate(outputs):
        if output.bits_count > len(buffers[index]):
            raise RuntimeError(f"numeric_batch bits_count exceeds capacity at item {index}")
        entry = {"call_status": output.call_status,
                 "mathematical_status": output.mathematical_status,
                 "display_status": output.display_status,
                 "bits": [f"{buffers[index][j]:016x}" for j in range(output.bits_count)]}
        # Status failures must not turn into believable zero/partial output.
        if output.call_status and any(value != SENTINEL for value in buffers[index]):
            entry["failed_item_modified_bits"] = True
        if any(value != SENTINEL for value in buffers[index][output.bits_count:]):
            entry["modified_unused_capacity"] = True
        actual.append(entry)
    return actual, elapsed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True, help="absolute path to the test-only numeric DLL")
    parser.add_argument("--suite", choices=("c0",), default="c0")
    parser.add_argument("--output", type=Path, help="UTF-8 JSON summary; no full successful corpus dump")
    parser.add_argument("--random-samples", type=int, default=128,
                        help="fixed-seed generator iterations (reported, not a pass quota)")
    args = parser.parse_args(argv)
    if args.random_samples < 0:
        parser.error("--random-samples cannot be negative")
    started = time.perf_counter()
    try:
        dll, abi = load_library(args.dll)
        generated = time.perf_counter()
        cases = corpus(args.random_samples)
        generation_seconds = time.perf_counter() - generated
        oracle_started = time.perf_counter()
        # The entire expected-result path runs before the DLL receives inputs.
        expectations = [expected(case) for case in cases]
        oracle_seconds = time.perf_counter() - oracle_started
        options = Options(C.sizeof(Options), VERSION, 0, 0)
        context = Context()
        status = dll.eab2_context_create(C.byref(options), C.byref(context))
        if status:
            raise RuntimeError(f"context_create failed: {STATUS_NAMES.get(status, status)}")
        try:
            actual, ffi_seconds = run_batch(dll, context, cases)
        finally:
            status = dll.eab2_context_destroy(context)
            if status:
                raise RuntimeError(f"context_destroy failed: {STATUS_NAMES.get(status, status)}")
        failures = []
        mismatch_count = 0
        operation_counts, source_counts, expected_status_counts = Counter(), Counter(), Counter()
        bit_comparisons = 0
        for case, wanted, got in zip(cases, expectations, actual):
            operation_counts[OPERATIONS.get(case.operation, "unsupported")] += 1
            source_counts[case.source] += 1
            expected_status_counts[STATUS_NAMES[wanted["call_status"]]] += 1
            bit_comparisons += len(wanted["bits"])
            if wanted != got:
                mismatch_count += 1
                if len(failures) < 16:
                    failures.append({**case.description(), "expected": wanted, "actual": got})
        source_files = ["src/eab/construction.py", "src/eab/numeric_domain.py",
                        "src/eab/predicates.py", "src/eab/kernel2d/geom.py",
                        "tests/test_r9fix_construction_rounding.py",
                        "tests/test_r9fix_compound_construction.py", "tests/test_r8fix_frozen.py"]
        summary = {
            "schema": "eab2.diff.c0.v1", "suite": args.suite,
            "dll": str(args.dll.resolve()), "dll_sha256": hashlib.sha256(args.dll.read_bytes()).hexdigest(),
            "abi": abi, "seed": SEED, "random_generator_iterations": args.random_samples,
            "sample_count": len(cases), "bit_comparisons": bit_comparisons,
            "mismatch_count": mismatch_count, "mismatches_stored": len(failures),
            "operation_counts": dict(sorted(operation_counts.items())),
            "source_counts": dict(sorted(source_counts.items())),
            "expected_status_counts": dict(sorted(expected_status_counts.items())),
            "source_definitions": CORPUS_SOURCES,
            "source_hashes_for_traceability_only": {
                path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in source_files},
            "timing_seconds": {"corpus_generation": generation_seconds, "python_oracle": oracle_seconds,
                               "ctypes_batch_including_c_abi_and_core": ffi_seconds,
                               "total_before_json_write": time.perf_counter() - started},
            "independence": "Python expectations use only existing src/eab and stdlib; ctypes only obtains actual results.",
            "limits": ["No performance gate or sample quota.",
                       "C0 numeric closed forms from frozen tests do not claim geometry or Dual coverage.",
                       "Decode is checked through roundtrip and exact-derived predicate/construction results; no exact-string export.",
                       "Rotation/translation/scaling cases transform exact rationals; no bit invariance is claimed for rounded floating transformations or rotated AABB bounds.",
                       "Successful numerical zero is canonical +0 except explicitly allowed negative underflow.",
                       "This suite is not fresh-tree validation or independent adversarial milestone review."],
            "failures": failures,
        }
        last_line = (f"EAB2_DIFF samples={len(cases)} bits={bit_comparisons} "
                     f"mismatches={mismatch_count} status={'PASS' if not mismatch_count else 'FAIL'}")
        summary["last_line"] = last_line
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"seed={SEED} random_iterations={args.random_samples} operations={json.dumps(dict(sorted(operation_counts.items())))}")
        print(f"timing_seconds={json.dumps(summary['timing_seconds'], sort_keys=True)}")
        if failures:
            print(json.dumps(failures[0], ensure_ascii=False))
        print(last_line)
        return 1 if mismatch_count else 0
    except (OSError, ValueError, RuntimeError, AttributeError) as error:
        print(f"EAB2_DIFF HARD_FAILURE: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
