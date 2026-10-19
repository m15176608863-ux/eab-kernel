"""Exact TIA-G1 t=0 contract conflict; not an eab2.case.v1 export.

Independent hand-built equilibrium columns and a symbolic positive-mu ray
construction check the production assembly without borrowing its contacts.
"""
from fractions import Fraction as Q
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab import lp
from eab.adapters.tia2d import g1
from eab.kernel2d.statics import limit_load_ideal_exact_2d
from tia2d_contract_probe import wire


def dot(a, b):
    return sum((x * y for x, y in zip(a, b)), Q(0))


def independent_model(height, mu):
    h, mu = Q(height), Q(mu)
    o = (Q(5, 8), Q(-3, 8))
    columns = []
    for face, x in enumerate((-3, -1, 1, 3)):
        for y in (Q(0), h):
            for sign in (-1, 1):
                force = (h, sign * mu * h)
                moment = (x - o[0]) * force[1] - (y - o[1]) * force[0]
                column = [Q(0)] * 9
                for body, sense in ((face, 1), (face - 1, -1)):
                    if 0 <= body < 3:
                        for k, value in enumerate((*force, moment)):
                            column[3 * body + k] = sense * value
                columns.append(column)
    live = [Q(0)] * 9
    live[4], live[5] = Q(-1), o[0]
    columns.append(live)
    A = tuple(tuple(row) for row in zip(*columns))
    b, c = (Q(0),) * 9, (Q(0),) * 16 + (Q(1),)
    return A, b, c


def constructive_ray(height, mu):
    """For every rational h>0, mu>0, not just a sampled closed-form value."""
    h, mu = Q(height), Q(mu)
    assert h > 0 and mu > 0
    pressure = max(1 / (2 * mu), 1 / h)
    coefficients = []
    for face in range(4):
        top = Q(0) if face in (0, 3) else 1 / h
        shear = Q(1, 2) if face < 2 else Q(-1, 2)
        for normal in (pressure - top, top):
            endpoint_shear = shear * normal / pressure
            coefficients.extend(((normal - endpoint_shear / mu) / (2 * h),
                                 (normal + endpoint_shear / mu) / (2 * h)))
    return tuple(coefficients) + (Q(1),)


def probe():
    started = time.perf_counter()
    cases = []
    for height in (Q(1), Q(3, 2), Q(2)):
        A, b, c = independent_model(height, 0)
        assert A[4] == (Q(0),) * 16 + (Q(-1),)
        primal = (Q(0),) * 17
        dual = (Q(0),) * 4 + (Q(-1),) + (Q(0),) * 4
        assert all(dot(row, primal) == target for row, target in zip(A, b))
        assert tuple(dot(col, dual) for col in zip(*A)) == c
        result = lp.maximize(A, b, c, exact=(A, b, c))
        assert result.status == lp.OPTIMAL and dot(c, result.exact_x) == 0
        production = limit_load_ideal_exact_2d(g1(t=0, height=height, mu=0))
        assert production.mathematical_status == "OPTIMAL" and production.exact_value == 0
        row_index = production.problem.row_labels.index(("block_3", 1))
        assert production.problem.A[row_index] == A[4]
        witnesses = []
        for mu in (Q(1, 2**60), Q(1, 1024), Q(1, 4), Q(2)):
            matrix, rhs, cost = independent_model(height, mu)
            ray = constructive_ray(height, mu)
            assert all(value >= 0 for value in ray) and ray[-1] == 1
            assert all(dot(row, ray) == 0 for row in matrix)
            witnesses.append(dict(mu=mu, ray=ray, A=matrix, b=rhs, c=cost,
                                  exact_ray_verified=True))
        cases.append(dict(height=height, mu=Q(0), A=A, b=b, c=c,
                          exact_x=primal, exact_y=dual,
                          production_status=production.mathematical_status,
                          exact_value=production.exact_value,
                          work_order_expected="UNBOUNDED",
                          work_order_matches=False,
                          positive_mu_constructive_witnesses=witnesses))
    return wire(dict(artifact_kind="contract_probe_not_eab2.case.v1", issue="T1a-C03",
                     design_sha256=hashlib.sha256((ROOT / "docs/eab2_design.md").read_bytes()).hexdigest(),
                     cases=cases, conclusion="t=0: OPTIMAL 0 at mu=0; unbounded for every mu>0",
                     proposed_threshold="mu_max>0: exact_threshold=0, attained=false; mu_max=0: bounded_on_domain",
                     proposal_approved=False, wall_seconds=time.perf_counter() - started))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        parser.error("choose a new output path inside this worktree")
    data = probe()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print("zero-slope contract probe: 3 exact OPTIMAL zero certificates; 12 constructive improving rays verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
