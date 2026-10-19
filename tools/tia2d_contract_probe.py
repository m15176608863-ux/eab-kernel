"""Small exact WO-T1a contract probes, not a production contact assembler.

The input is an explicit four-interface static model of TIA-G5, with three
unit rectangular blocks, a fixed left boundary and a right plate. This tool
does not implement any of the eight requested APIs and does not export
eab2.case.v1. It records a specification question and a boundary-frame check.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab import lp


def dot(a, b):
    return sum((u * v for u, v in zip(a, b)), Q(0))


def problem(mu, mask=(1, 0, 0), origin=(Q(5, 8), Q(-3, 8)),
            plate_anchor=(Q(0), Q(0))):
    """Hand-build force/moment columns; no cover/contact production path.

    Blocks occupy [0,1], [1,2], [2,3] times [0,1]. The four interfaces
    are x=0,1,2,3. Force on the right body is g=(1,+/-mu), corresponding
    to its CCW left edge e=(0,-1), N=rot90(e)=(1,0), T=e.
    Equal and opposite forces act on the left body (left boundary fixed).
    Block moments use a fixed, non-centroid reference point. Plate moments
    and its partial DOF mask use the explicitly supplied fixed plate_anchor.
    Moving that anchor while retaining mask [1,0,1] changes the boundary,
    not just the representation. Neither reference depends on mu.
    """
    mu = Q(mu)
    assert mu >= 0 and len(mask) == 3 and all(v in (0, 1) for v in mask)
    rows = [(body, dof) for body in range(3) for dof in range(3)]
    rows.extend((3, dof) for dof, free in enumerate(mask) if free)
    lookup = {key: i for i, key in enumerate(rows)}
    columns, sources = [], []
    for face in range(4):
        for height in (Q(0), Q(1)):
            for sign in (-1, 1):
                force = (Q(1), sign * mu)
                column = [Q(0)] * len(rows)
                for body, sense in ((face, 1), (face - 1, -1)):
                    reference = plate_anchor if body == 3 else origin
                    moment = (face - reference[0]) * force[1] - (height - reference[1]) * force[0]
                    wrench = (*force, moment)
                    for dof, value in enumerate(wrench):
                        if (body, dof) in lookup:
                            column[lookup[body, dof]] += sense * value
                columns.append(column)
                sources.append(dict(face=face, point=(Q(face), height), force=force))
    live = (Q(0), Q(-1), -(Q(3, 2) - origin[0]))
    column = [Q(0)] * len(rows)
    for dof, value in enumerate(live):
        column[lookup[1, dof]] = value
    columns.append(column)
    A = [list(row) for row in zip(*columns)]
    # P=1 acts along -x at (3,1/2); b=-W_dead. Keep only plate free rows.
    negative_dead = (Q(1), Q(0), -(Q(1, 2) - plate_anchor[1]))
    b = [negative_dead[dof] if body == 3 else Q(0) for body, dof in rows]
    c = [Q(0)] * len(columns)
    c[-1] = Q(1)
    return dict(A=A, b=b, c=c, rows=rows, sources=sources, mu=mu,
                mask=mask, origin=origin, plate_anchor=plate_anchor)


def solve_and_verify(model):
    """Existing exact LP plus direct raw equality/inequality verification."""
    A, b, c = (model[key] for key in ("A", "b", "c"))
    result = lp.maximize(A, b, c, exact=(A, b, c))
    assert result.status == lp.OPTIMAL
    x, y = result.exact_x, result.exact_y
    assert x is not None and y is not None
    assert all(v >= 0 for v in x)
    assert [dot(row, x) for row in A] == b
    slacks = [dot(col, y) - cost for col, cost in zip(zip(*A), c)]
    assert all(v >= 0 for v in slacks)
    value = dot(c, x)
    assert value == dot(b, y)
    return dict(value=value, exact_x=x, exact_y=y, dual_slacks=slacks,
                primal_equalities_verified=True, nonnegative_x_verified=True,
                dual_inequalities_verified=True, strong_duality_verified=True)


def zero_friction_recession(model):
    """Exhibit a dual optimum and a nonzero optimal-face recession ray.

    q has only the middle block's vertical velocity -1. At mu=0 every
    contact column has zero y force; only the live-load column has power 1.
    Thus A^T q = c >= 0, b^T q = 0. For every t>=0, (1+t)q stays on
    the dual optimal face, while the primal load optimum is zero.
    """
    assert model["mu"] == 0
    A, b, c = (model[key] for key in ("A", "b", "c"))
    q = [Q(0)] * len(b)
    q[model["rows"].index((1, 1))] = Q(-1)
    atq = [dot(col, q) for col in zip(*A)]
    assert atq == c and all(v >= 0 for v in atq)
    assert dot(b, q) == 0 and any(q)
    # A simple independent primal feasible point: P/2 at each endpoint.
    x0 = [Q(1, 2) if j % 2 == 0 else Q(0) for j in range(16)] + [Q(0)]
    assert [dot(row, x0) for row in A] == b and dot(c, x0) == 0
    return dict(dual_point=q, dual_recession_ray=q, A_transpose_q=atq,
                b_dot_q=dot(b, q), independent_primal_point=x0,
                nonzero_recession_verified=True,
                design_differentiability="singular",
                design_reason="possibly_discontinuous",
                design_directional_derivative=None)


def wire(value):
    if isinstance(value, Q):
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, dict):
        return {key: wire(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [wire(item) for item in value]
    return value


def probe():
    started = time.perf_counter()
    cases = []
    for name, mu, mask, anchor, expected in (
        ("zero_friction", Q(0), (1, 0, 0), (Q(0), Q(0)), Q(0)),
        ("sliding", Q(1, 4), (1, 0, 0), (Q(0), Q(0)), Q(1, 2)),
        ("switch", Q(1), (1, 0, 0), (Q(0), Q(0)), Q(2)),
        ("hinging", Q(2), (1, 0, 0), (Q(0), Q(0)), Q(2)),
        ("released_vertical", Q(2), (1, 1, 0), (Q(0), Q(0)), Q(2, 3)),
        ("released_rotation_global_anchor", Q(2), (1, 0, 1), (Q(0), Q(0)), Q(1, 3)),
        ("released_rotation_plate_anchor", Q(2), (1, 0, 1), (Q(3), Q(1, 2)), Q(4, 3)),
    ):
        before = time.perf_counter()
        model = problem(mu, mask, plate_anchor=anchor)
        certificate = solve_and_verify(model)
        assert certificate["value"] == expected
        row = dict(name=name, model=model, certificate=certificate,
                   wall_seconds=time.perf_counter() - before)
        if mu == 0:
            row["recession"] = zero_friction_recession(model)
        if name == "released_rotation_global_anchor":
            row["work_order_expected_value"] = Q(1, 3)
            row["work_order_value_matches"] = True
        cases.append(row)
    return wire(dict(
        artifact_kind="contract_probe_not_eab2.case.v1",
        scope="hand_assembled_N3_only_not_production_API_or_C3_acceptance",
        profile="profile1", sensitivity_model="ideal_exact_2d",
        design_sha256=hashlib.sha256((ROOT / "docs/eab2_design.md").read_bytes()).hexdigest(),
        python_version=platform.python_version(), cases=cases,
        wall_seconds=time.perf_counter() - started,
        issues=[
            dict(id="T1a-C01", fact="nonzero_dual_optimal_face_recession_at_mu_zero",
                 design="singular/possibly_discontinuous; no slope",
                 question="Exclude mu=0 from the unconditional Mills/Freund requirement?"),
        ],
        boundary_frame_note="1/3 and 4/3 use different plate anchors; not a contradiction",
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT):
        parser.error("output must stay inside this worktree")
    if output.exists():
        parser.error("choose a new evidence output; existing evidence is immutable")
    result = probe()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    for case in result["cases"]:
        print(f"{case['name']}: {case['certificate']['value']}")
    print("contract probe: 7 exact optima verified; 1 specification question")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
