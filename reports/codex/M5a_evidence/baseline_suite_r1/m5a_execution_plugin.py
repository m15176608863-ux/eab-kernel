import json, os, time
from pathlib import Path
collected = []
reports = []
started = time.monotonic()
def progress(complete=False):
    target = Path(os.environ["M5A_NODE_PROGRESS"])
    temporary = target.with_suffix(".writing")
    temporary.write_text(json.dumps(dict(complete=complete, collected=len(collected),
        calls=sum(r["when"] == "call" for r in reports),
        failed=sum(r["outcome"] == "failed" for r in reports),
        skipped=sum(r["outcome"] == "skipped" for r in reports),
        last=reports[-1] if reports else None, elapsed_seconds=time.monotonic()-started)), encoding="utf-8")
    for attempt in range(12):
        try:
            temporary.replace(target)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(min(0.01 * (attempt + 1), 0.1))
def pytest_collection_finish(session):
    collected.extend(item.nodeid for item in session.items)
    progress()
def pytest_runtest_logreport(report):
    row = dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome, duration=report.duration)
    reports.append(row)
    with Path(os.environ["M5A_NODE_JOURNAL"]).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row)+"\n")
    if report.when == "teardown":
        progress()
def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["M5A_EXECUTION_RECORD"]).write_text(json.dumps(dict(
        complete=True, collected=collected, reports=reports, exitstatus=int(exitstatus)), indent=2), encoding="utf-8")
    progress(complete=True)
