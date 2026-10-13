import json, os
from pathlib import Path
collected = []
reports = []
def pytest_collection_finish(session):
    collected.extend(item.nodeid for item in session.items)
def pytest_runtest_logreport(report):
    reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome))
def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["M3_EXECUTION_RECORD"]).write_text(json.dumps(dict(
        collected=collected, reports=reports, exitstatus=int(exitstatus)), indent=2), encoding="utf-8")
