"""Named C1 binary64 corpus; original rational cases are explicitly RN inputs."""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import runpy
import struct


ROOT = Path(__file__).resolve().parents[1]
DOMAIN_EXCLUSIONS = []


@dataclass
class Case:
    name: str
    a: tuple
    b: tuple
    sources: list[str] = field(default_factory=list)
    rounded_coordinates: int = 0


def bits(x):
    return struct.pack(">d", x).hex()


def from_bits(x):
    return struct.unpack(">d", bytes.fromhex(x))[0]


def make_case(name, a, b, source):
    bodies = [tuple(tuple(float(x) for x in p) for p in body) for body in (a, b)]
    changed = sum(F(x) != F(float(x)) for body in (a, b) for p in body for x in p)
    if any(not math.isfinite(x) for body in bodies for p in body for x in p):
        raise ValueError(f"{name}: nonfinite RN input")
    return Case(name, *bodies, [source], changed)


def named_cases():
    m3 = runpy.run_path(str(ROOT / "tests/test_m3_global2d.py"))
    for name, a, b in m3["_families"]():
        yield make_case("m3/"+name, a, b, "tests/test_m3_global2d.py::_families (RN binary64)")
    m3b = runpy.run_path(str(ROOT / "tests/test_m3b_2d.py"))
    for an, bn in (("FLAT", "SQUARE"), ("FLAT", "L"), ("PLUG", "POCKET"), ("SQUARE", "L")):
        yield make_case(f"m3b/{an}_{bn}", m3b[an], m3b[bn], "tests/test_m3b_2d.py (RN binary64)")
    yield make_case("m3b/SQUARE_SQUARE", m3b["SQUARE"], m3b["SQUARE"], "test_m3b_2d.py::test_contact_skeleton_subdivision_checks_every_stratum")
    from eab.kernel2d.global_entrance import _ring
    def in_domain(name, a, b, source):
        case = make_case(name, a, b, source)
        try:
            _ring(case.a)
            _ring(case.b)
        except ValueError as exc:
            DOMAIN_EXCLUSIONS.append({"name": name, "reason": "RN binary64 ring invalid: "+str(exc),
                                      "scope": "original exact rational fixture remains Python-only"})
            return None
        return case
    for exponent in (-400, 0, 400):
        scale = F(2)**exponent
        for kind in ("isolated_point", "collinear_seam"):
            if kind == "isolated_point":
                a = m3b["PLUG"]
                b = m3b["POCKET"][:-1]+((F(10, 3), 6),)+m3b["POCKET"][-1:]
            else:
                a, b = [tuple((-y, x) for x, y in body) for body in (m3["PIN"], m3["U"])]
            a = tuple((scale*x+100000, scale*y-3000) for x, y in a)
            b = tuple((scale*x-2000, scale*y+4000) for x, y in b)
            case = in_domain(f"m3b/adjacent_{kind}_{exponent}", a, b,
                             "test_m3b_2d.py::test_compact_side_probes_stay_in_adjacent_open_faces_before_every_event")
            if case:
                yield case
        a = tuple((scale*x, scale*y) for x, y in m3b["SQUARE"])
        b = tuple((scale*x+F(13, 7), scale*y-F(29, 11)) for x, y in ((0, 0), (2, 0), (2, 3), (0, 3)))
        case = in_domain(f"m3b/rectangle_{exponent}", a, b,
                         "test_m3b_2d.py::test_every_compact_subdivision_coordinate_has_an_independent_rectangle_value")
        if case:
            yield case
    for exponent, shift, rotation in ((-400, 0, 0), (0, 1000, 1), (400, 100000, 2)):
        scale = F(2)**exponent
        def rotate(p):
            return p if rotation == 0 else ((-p[1], p[0]) if rotation == 1 else
                                            ((3*p[0]-4*p[1])/F(5), (4*p[0]+3*p[1])/F(5)))
        def body(poly, x, y):
            return tuple((scale*rotate(p)[0]+x, scale*rotate(p)[1]+y) for p in poly)
        yield make_case(f"m3b/tier_{exponent}", body(m3b["SQUARE"], shift, -shift),
                        body(m3b["L"], -2*shift, 3*shift),
                        "test_m3b_2d.py::test_compact_constructions_three_tiers_with_independent_rigid_motion (RN binary64)")
    from bb52_g0 import load_blocks
    blocks, _ = load_blocks(1)
    for i, j in ((3, 8), (4, 9), (7, 8)):
        yield make_case(f"m3b/bb52_{i}_{j}", blocks[i]["poly"], blocks[j]["poly"],
                        "test_m3b_2d.py::test_bb52_representative_complete_subdivisions (frozen fixtures only)")
    m3c = runpy.run_path(str(ROOT / "tests/test_m3c_determinism.py"))
    for exponent in (-4, 0, 4):
        model = m3c["_model"](exponent)
        yield make_case(f"m3c/exponent_{exponent}", model.A, model.B,
                        "tests/test_m3c_determinism.py::_model (RN binary64; not exact rational rotation)")
    # The following directly reproduce all parameter combinations of the small
    # finite-binary64 cover examples, without executing pytest test functions.
    square = ((0., 0.), (1., 0.), (1., 1.), (0., 1.))
    triangle = ((0., 0.), (-1., 1.), (-1., -1.))
    for shift in (0., 1e3, 1e5):
        for theta in (-5., 0., 5., 45., 50.):
            angle = math.radians(theta)
            a = [(shift+x+1e-6*math.cos(angle), shift+y+1e-6*math.sin(angle)) for x, y in square]
            b = [(shift+x, shift+y) for x, y in triangle]
            yield make_case(f"covers_e3/vv_{shift}_{theta}", a, b, "test_kernel2d_covers_e3.py::test_vv_active_exact_support_not_a_roundoff_band")
        h = math.ulp(max(shift, 1.))
        a = [(shift, shift), (shift+1, shift), (shift+1, shift+1), (shift, shift+1), (shift+h, shift+.5)]
        b = [(shift-1, shift), (shift, shift), (shift, shift+1), (shift-1, shift+1)]
        yield make_case(f"covers_e3/reflex_{shift}", a, b, "test_kernel2d_covers_e3.py::test_local_no_window_rejects_a_real_reflex_vertex")
    for scale in (1e-200, 1., 1e200):
        ring = [(scale*x, scale*y) for x, y in m3b["L"]]
        for reverse in (False, True):
            p = list(reversed(ring)) if reverse else ring
            yield make_case(f"covers_e3/exponent_{scale}_{reverse}", p, p, "test_kernel2d_covers_e3.py::test_exact_overlap_triangulation_orientation_cannot_underflow")
    shift = 1e5
    for name, a in (("zero_window", [(shift+x, shift+y+1+math.ulp(shift)) for x, y in square]),
                    ("segment_window", [(shift-math.ulp(shift), shift+1.2), (shift+.2, shift+1.5), (shift-.2, shift+1.5)])):
        yield make_case("covers_e3/"+name, a, [(shift+x, shift+y) for x, y in square],
                        "tests/test_kernel2d_covers_e3.py::test_"+name)


def formal_cases():
    directory = ROOT / "fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64"
    index = json.loads((directory / "gzip_index.json").read_text(encoding="utf-8"))
    for item in index["files"]:
        packed = (directory / item["gz_path"]).read_bytes()
        if hashlib.sha256(packed).hexdigest() != item["gz_sha256"]:
            raise AssertionError("formal gzip integrity mismatch: "+item["gz_path"])
        data = gzip.decompress(packed)
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise AssertionError("formal decompressed integrity mismatch: "+item["path"])
        doc = json.loads(data)
        assembly = doc.get("assembly")
        if not assembly:
            continue
        bodies = {b["body_id"]: tuple(tuple(from_bits(x) for x in p) for p in b["vertices_xy_bits"])
                  for b in assembly["bodies"]}
        adjacency = assembly["adjacency"]
        if adjacency is None:
            # Unknown assembly completeness does not prohibit testing every
            # geometric body pair; it is not promoted to a complete contact set.
            adjacency = list(combinations(bodies, 2))
        for a, b in adjacency:
            yield make_case(f"formal/{doc['case_id']}/{a}--{b}", bodies[a], bodies[b],
                            f"{item['gz_path']}::assembly.adjacency::{a}--{b}")


def corpus(include_formal=True):
    """Deduplicate identical ordered input bits, preserve every source alias."""
    DOMAIN_EXCLUSIONS.clear()
    all_cases = list(named_cases()) + (list(formal_cases()) if include_formal else [])
    unique = {}
    for case in all_cases:
        key = tuple(tuple(tuple(bits(x) for x in p) for p in body) for body in (case.a, case.b))
        if key in unique:
            unique[key].sources.extend(case.sources)
        else:
            unique[key] = case
    return list(unique.values()), {"named_and_formal_pair_occurrences": len(all_cases),
                                  "unique_ordered_binary64_pairs": len(unique),
                                  "deduplicated_occurrences": len(all_cases)-len(unique),
                                  "python_only_input_domain_exclusions": list(DOMAIN_EXCLUSIONS)}
