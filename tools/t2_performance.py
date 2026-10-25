"""Three-repeat, exact-input WO-T2a timings; elapsed seconds are diagnostic.

No floating geometry is constructed. The two 16-edge stars move about
different noncentral rational reference points. The second workload runs
the whole three-obstacle query, not a selected easy pair. Timings are for
three consecutive same-process calls, without an unreported warm-up.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import tolerance_dovetail
from eab.kernel2d.erosion import erode_polygon_exact
from eab.kernel2d.se2 import SE2Motion
from eab.kernel2d.se2_paths import se2_first_penetration, se2_first_penetration_many


def star16(center):
    quadrant = ((F(1), F(0)), (F(15, 17), F(8, 17)),
                (F(3, 5), F(4, 5)), (F(5, 13), F(12, 13)))
    directions = []
    for quarter in range(4):
        for x, y in quadrant:
            for _ in range(quarter):
                x, y = -y, x
            directions.append((x, y))
    result = []
    for index, (x, y) in enumerate(directions):
        radius = F(1) if index % 2 == 0 else F(3, 5)
        result.append((center[0] + radius * x, center[1] + radius * y))
    return tuple(result)


def star_workload():
    ca, cb = (F(7, 11), -F(5, 13)), (F(149, 44), -F(9, 91))
    a, b = star16(ca), star16(cb)
    ma = SE2Motion(F(3, 5), (F(9, 4), F(1, 5)), (ca[0] + F(1, 7), ca[1] + F(2, 9)))
    mb = SE2Motion(-F(2, 7), (-F(1, 7), -F(1, 9)), (cb[0] + F(2, 11), cb[1] - F(1, 5)))
    return a, b, ma, mb


def dovetail_workload():
    raw = tolerance_dovetail(head_width=F(5, 2), neck_width=F(3, 2), height=F(2), wall=F(2))
    eroded = erode_polygon_exact(raw["moving"], F(7, 20), "octagon")
    if eroded.status != "ACCEPTED":
        raise ArithmeticError("the fixed performance input erosion was rejected")
    motion = SE2Motion(F(2, 3), (F(1, 7), F(3, 4)), (F(2, 11), F(7, 9)))
    return eroded.polygon, tuple(raw["obstacles"]), motion


def strings(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {key: strings(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [strings(item) for item in value]
    return value


def motion_data(motion):
    return dict(u1=motion.u1, translation=motion.translation, center=motion.center)


def result_data(result):
    answer = dict(status=result.status, exact_tau=None if result.exact_time is None else result.exact_time.certificate,
                  immediate=result.immediate, touches_end=result.touches_end,
                  incidences=result.incidences, features=result.features)
    if hasattr(result, "initial_state"):
        answer.update(initial_state=result.initial_state, end_state=result.end_state)
    if hasattr(result, "results"):
        answer.update(obstacle_indices=result.obstacle_indices,
                      pair_results=[result_data(pair) for pair in result.results])
    return answer


def timed(kind, arguments):
    samples, results = [], []
    for index in range(3):
        start = time.perf_counter()
        if kind == "stars16":
            result = se2_first_penetration(*arguments)
        else:
            result = se2_first_penetration_many(*arguments)
        elapsed = time.perf_counter() - start
        samples.append(elapsed)
        results.append(result)
        print(json.dumps(dict(workload=kind, repeat=index + 1, elapsed_s=elapsed,
                              status=result.status)), flush=True)
    first = results[0]
    agreement = all(result.status == first.status and result.exact_time == first.exact_time
                    for result in results)
    if not agreement or first.status != "PENETRATES" or first.immediate:
        raise ArithmeticError("performance workload lost its nontrivial exact crossing")
    return dict(repetitions=3, elapsed_seconds_diagnostic=samples,
                median_seconds_diagnostic=statistics.median(samples),
                same_status_and_exact_tau=agreement,
                results=[result_data(result) for result in results])


def source_hashes():
    paths = ("tools/t2_performance.py", "src/eab/kernel2d/se2_paths.py", "src/eab/kernel2d/se2.py",
             "src/eab/kernel2d/algebraic.py", "src/eab/kernel2d/exact.py",
             "src/eab/kernel2d/erosion.py", "src/eab/adapters/tia2d.py")
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path("D:/eab-evidence/reports/codex/T2a_evidence/performance_01.json"))
    args = parser.parse_args()
    before = source_hashes()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout.strip()
    star_args, dovetail_args = star_workload(), dovetail_workload()
    jobs = (
        ("stars16", star_args, dict(call="se2_first_penetration", A0=star_args[0], B0=star_args[1],
                                  motion_a=motion_data(star_args[2]), motion_b=motion_data(star_args[3]))),
        ("dovetail_three_obstacles", dovetail_args,
         dict(call="se2_first_penetration_many", A0=dovetail_args[0], obstacles=dovetail_args[1],
              motion_a=motion_data(dovetail_args[2]), motions_b="fixed_identity_default")),
    )
    output = dict(schema="t2a-performance-1", head=head, python=sys.version,
                  executable=sys.executable, platform=platform.platform(),
                  command="python tools/t2_performance.py --output <new_external_json>",
                  geometry_arithmetic="integer/Fraction only; all geometry and motion inputs persisted",
                  timing_scope="three consecutive same-process calls, no warm-up; times are diagnostics only",
                  source_hashes_before=before, workloads=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name, arguments, inputs in jobs:
        output["workloads"].append(dict(name=name, inputs=inputs, **timed(name, arguments)))
        args.output.write_text(json.dumps(strings(output), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after = source_hashes()
    output.update(source_hashes_after=after, sources_unchanged=before == after)
    args.output.write_text(json.dumps(strings(output), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if before != after:
        raise RuntimeError("measured source changed during the timing run; run is not frozen evidence")


if __name__ == "__main__":
    main()
