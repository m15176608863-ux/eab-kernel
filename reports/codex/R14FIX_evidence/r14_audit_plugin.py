"""Audit-only pytest plugin: records exact node IDs, never changes selection."""
import json
import os
from pathlib import Path


def pytest_collection_finish(session):
    Path(os.environ["R14_COLLECTION"]).write_text(
        json.dumps([item.nodeid for item in session.items], ensure_ascii=False, indent=2), encoding="utf-8")


def pytest_runtest_logreport(report):
    if "R14_RESULTS" in os.environ:
        with open(os.environ["R14_RESULTS"], "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"nodeid": report.nodeid, "when": report.when,
                                     "outcome": report.outcome, "duration": report.duration}) + "\n")
