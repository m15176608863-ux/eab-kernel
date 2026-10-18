"""Duration-derived opt-in slow tier. Deselection is not a skipped execution."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False,
                     help="include the measured slow tier (full suite)")


def pytest_collection_modifyitems(config, items):
    policy_path = ROOT / "tests/slow_tests.json"
    policy = json.loads(policy_path.read_text("utf-8"))
    slow = set(policy["slow_functions"])
    promoted = set(policy.get("fast_nodes", ()))
    keep, deselected = [], []
    for item in items:
        if item.nodeid.split("[", 1)[0] in slow and item.nodeid not in promoted:
            item.add_marker(pytest.mark.slow)
        if item.get_closest_marker("slow") is not None and not config.getoption("--runslow"):
            deselected.append(item)
        else:
            keep.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = keep
