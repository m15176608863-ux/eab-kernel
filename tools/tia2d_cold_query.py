"""Measure each exported target query in a new process, after its prerequisites.

Interpreter startup, imports, decoding, input audit and required prebuilt
contacts/base optima are excluded from the target wallclock. No earlier target
call occurs in that process. This is cold target invocation, not OS page-cache
eviction. Exact public outputs are compared with the batch's untimed record
before accepting the timing. Warm initial clocks are private evidence only.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from tia2d_readback import ROOT, compare_result, prepare_query, require, display_status


def cold_case(case, *, scratch=None, progress=None):
    """Mutate only query clocks; one worker per target, returning warm evidence.

The input is an in-memory codec case (possibly larger than one artifact before
query splitting). Its temporary transport stays below ignored evidence/tmp.
No public schema fields are added. Any failed comparison aborts the caller's
batch. The source manifest guard belongs to the encompassing exporter.
"""
    parent = (ROOT / "reports/codex/T1a_evidence/tmp" if scratch is None else Path(scratch)).resolve()
    require(parent.is_relative_to(ROOT / "reports/codex/T1a_evidence/tmp"), "cold scratch domain")
    parent.mkdir(parents=True, exist_ok=True)
    warm = []
    with tempfile.TemporaryDirectory(prefix="cold_query_", dir=parent) as directory:
        transport = Path(directory) / "case.json"
        transport.write_text(json.dumps(case, ensure_ascii=False, allow_nan=False), encoding="utf-8", newline="\n")
        for index, query in enumerate(case["queries"]):
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", TEMP=str(parent), TMP=str(parent))
            result = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()),
                                     "--worker", str(transport), "--query-index", str(index)],
                                    cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", check=True)
            timing = json.loads(result.stdout)
            require(timing["case_id"] == case["case_id"] and timing["query_index"] == index
                    and timing["verified"] is True, "cold worker identity")
            warm.append(dict(query_index=index, kind=query["kind"], original_warm_clock=query["python_wallclock"]))
            query["python_wallclock"] = timing["python_wallclock"]
            if progress is not None:
                progress(timing)
    return warm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path, required=True)
    parser.add_argument("--query-index", type=int, required=True)
    args = parser.parse_args()
    case = json.loads(args.worker.read_text(encoding="utf-8"))
    query = case["queries"][args.query_index]
    call, expected = prepare_query(case, args.query_index)
    start = time.perf_counter()
    answer = call()
    seconds = time.perf_counter() - start
    compare_result(expected, answer)
    if query["kind"] == "limit":
        compare_result(query["problem"], answer.problem)
    require(query["call_status"] == answer.call_status and query["mathematical_status"] == answer.mathematical_status
            and query["display_status"] == display_status(query["kind"], answer),
            "cold status envelope")
    print(json.dumps(dict(case_id=case["case_id"], query_index=args.query_index, verified=True,
          python_wallclock=dict(seconds=seconds, clock="perf_counter", repeat_index=0,
                                cache_state="cold", scope=query["python_wallclock"]["scope"])), allow_nan=False))


if __name__ == "__main__":
    main()
