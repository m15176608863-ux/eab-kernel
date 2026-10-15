import json, os, time, threading, math
from pathlib import Path
collected = []
reports = []
started = time.monotonic()
active_timer = None
timeout_seconds = float(os.environ.get("M5A2_TEST_TIMEOUT", "180"))
if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
    raise ValueError("test timeout must be finite and positive")

def pytest_runtest_logstart(nodeid, location):
    global active_timer
    def expired():
        row = dict(nodeid=nodeid, when="watchdog", outcome="failed", reason="per-test timeout")
        Path(os.environ["M5A2_TIMEOUT_RECORD"]).write_text(json.dumps(row), encoding="utf-8")
        print("M5A2_TEST_TIMEOUT "+nodeid, flush=True)
        os._exit(124)
    active_timer = threading.Timer(timeout_seconds, expired)
    active_timer.daemon = True
    active_timer.start()

def pytest_runtest_logfinish(nodeid, location):
    if active_timer is not None:
        active_timer.cancel()
def progress(complete=False):
    target = Path(os.environ["M5A2_NODE_PROGRESS"])
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
    with Path(os.environ["M5A2_NODE_JOURNAL"]).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row)+"\n")
    if report.when == "teardown":
        progress()
def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["M5A2_EXECUTION_RECORD"]).write_text(json.dumps(dict(
        complete=True, collected=collected, reports=reports, exitstatus=int(exitstatus)), indent=2), encoding="utf-8")
    progress(complete=True)
