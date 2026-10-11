"""Independent exact classification of the final run's 41 margin failures.

The original factory/rigid helper only supplies raw input coordinates.  All
relation and precondition checks use the independent test surface oracle.
"""
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import combinations
from math import gcd, lcm
from pathlib import Path
import hashlib
import json
import re
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools"), str(ROOT / "tests")]
import test_invariance_interlock as T
import e5a2_surface_oracle as O
from eab.kernel3d.geom3 import polyhedra_overlap
from eab.margin import PENETRATING, INSIDE, body_distance, margin_contacts, inflated_membership


def preconditions(P):
    edges = defaultdict(list)
    for fi, face in enumerate(P.faces):
        assert len(set(face)) == len(face) >= 3
        for i, j in zip(face, face[1:]+face[:1]):
            edges[tuple(sorted((i, j)))].append((i, j, fi))
    assert all(len(es) == 2 and es[0][:2] == es[1][:2][::-1] for es in edges.values())
    tets = O._tetrahedra(P)  # independently checks a strict star kernel
    assert tets
    center = tets[0][0]
    kernel_slacks = []
    for kernel, a, b, c in tets:
        assert kernel == center
        n = O._times(O._minus(b, a), O._minus(c, a))
        assert n != (0, 0, 0)
        slack = -O._scalar(n, O._minus(center, a))
        assert slack > 0
        kernel_slacks.append(slack)
    # These inputs contain only triangles or near-rectangular quad rings.
    # Prove every quad's dominant-axis projected ring is strictly convex,
    # which is stronger than the simple nondegenerate ring prerequisite.
    v = [tuple(map(F, p)) for p in P.verts]
    for face in P.faces:
        if len(face) == 3:
            continue
        assert len(face) == 4
        n = [F(0), F(0), F(0)]
        for i, j in zip(face, face[1:]+face[:1]):
            cross = O._times(O._minus(v[i], v[face[0]]), O._minus(v[j], v[face[0]]))
            n = [n[k]+cross[k] for k in range(3)]
        drop = max(range(3), key=lambda k: abs(n[k]))
        axes = [(drop+1) % 3, (drop+2) % 3]
        turns = []
        for k in range(4):
            a, b, c = (v[face[(k+j) % 4]] for j in range(3))
            turns.append((b[axes[0]]-a[axes[0]])*(c[axes[1]]-b[axes[1]])
                         -(b[axes[1]]-a[axes[1]])*(c[axes[0]]-b[axes[0]]))
        assert all(x > 0 for x in turns) or all(x < 0 for x in turns)
    return tets, dict(closed_oriented_edges=len(edges), triangles=len(tets),
        strict_star_kernel=[str(x) for x in center],
        smallest_kernel_plane_slack=str(min(kernel_slacks)),
        all_quad_projections_strictly_convex=True)


def positive_tetra_certificate(aa, bb):
    D = lcm(*(x.denominator for tet in aa+bb for p in tet for x in p))
    ai, bi = ([tuple(tuple(int(x*D) for x in p) for p in tet) for tet in ts]
              for ts in (aa, bb))
    for ia, a in enumerate(ai):
        for ib, b in enumerate(bi):
            if O._sat(a, b) != 1:
                continue
            axes = []
            for tet in (a, b):
                axes.extend(O._times(O._minus(tet[j], tet[i]), O._minus(tet[k], tet[i]))
                            for i, j, k in combinations(range(4), 3))
            axes.extend(O._times(O._minus(q, p), O._minus(v, u))
                        for p, q in combinations(a, 2) for u, v in combinations(b, 2))
            slacks = []
            for n in axes:
                if n == (0, 0, 0):
                    continue
                g = gcd(gcd(abs(n[0]), abs(n[1])), abs(n[2]))
                n = tuple(x//g for x in n)
                ap, bp = [O._scalar(n, p) for p in a], [O._scalar(n, p) for p in b]
                slack = min(max(ap), max(bp))-max(min(ap), min(bp))
                assert slack > 0
                slacks.append(slack)
            return dict(a_tetra_index=ia, b_tetra_index=ib,
                        common_coordinate_denominator=str(D),
                        tested_nonzero_SAT_axes=len(slacks),
                        minimum_primitive_integer_axis_overlap=str(min(slacks)))
    raise AssertionError("no strict interior tetrahedron pair exists")


start = time.perf_counter()
xml = ET.parse(ROOT / "reports/codex/E5a2_evidence/final.xml")
nodes = [n for n in xml.iter("testcase") if n.find("failure") is not None
         and n.get("classname", "").endswith("test_invariance_interlock")
         and n.get("name", "").startswith("test_margin_")]
assert len(nodes) == 41, len(nodes)
rows = []
for node in nodes:
    name = node.get("name")
    match = re.search(r"\[(touch|subtol)-(I|q4|q6)-([0-9.]+)-([0-9.]+)\]", name)
    if match:
        case, rotation, translation, scale = match.groups()
        translation, scale = float(translation), float(scale)
        _, factory = T.MARGIN_CASES[case]
        a, b = factory()
        A, B = T._rigid(a, T.ROT_3[rotation], translation, scale), T._rigid(b, T.ROT_3[rotation], translation, scale)
    else:
        assert name == "test_margin_reference_cases_are_what_they_claim"
        case, rotation, translation, scale = "subtol", "reference", 0., 1.
        A, B = T.MARGIN_CASES[case][1]()
    aa, ac = preconditions(A)
    bb, bc = preconditions(B)
    independent = O.star_relation(A, B, 0)
    assert independent == 1, (name, independent)
    witness = positive_tetra_certificate(aa, bb)
    observed = polyhedra_overlap(A, B, 0)
    d, label = body_distance(A, B)
    assert observed == independent and (d, label) == (0., (PENETRATING,))
    margins = []
    for delta in (0., 0.01*scale):
        contacts = margin_contacts(A, B, delta=delta)
        member = inflated_membership(A, B, delta=delta)
        assert len(contacts) == 1 and contacts[0].label == (PENETRATING,)
        assert contacts[0].closed and contacts[0].distance == 0.
        assert contacts[0].margin_gap == -delta and member == INSIDE
        margins.append(dict(delta=delta, state=member, closed=contacts[0].closed,
                            margin_gap=contacts[0].margin_gap))
    raw = dict(A=dict(vertices_hex=[[float(x).hex() for x in p] for p in A.verts], faces=A.faces),
               B=dict(vertices_hex=[[float(x).hex() for x in p] for p in B.verts], faces=B.faces))
    rows.append(dict(node=name, case=case, rotation=rotation, translation=translation, scale=scale,
                     independent_exact_state=independent, production_zero_band_state=observed,
                     body_distance=d, label=label, margins=margins, preconditions_A=ac,
                     preconditions_B=bc, strict_interior_certificate=witness, raw_input=raw,
                     input_sha256=hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
                     classification="obsolete ideal-contact assertion; actual input has strict interior overlap"))

out = dict(failed_nodes_audited=len(rows), independent_state_counts=dict(Counter(r["independent_exact_state"] for r in rows)),
    cases=dict(Counter(r["case"] for r in rows)), elapsed_seconds=time.perf_counter()-start,
    hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [ROOT/"tests/test_invariance_interlock.py", ROOT/"tests/e5a2_surface_oracle.py",
             ROOT/"src/eab/kernel3d/exact_geom.py", ROOT/"src/eab/margin.py"]}, rows=rows)
dest = Path(__file__).with_name("margin_failed_exact_audit.json")
dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
