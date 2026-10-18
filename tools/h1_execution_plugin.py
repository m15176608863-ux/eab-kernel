"""Small execution/coverage journal for H1; requires Python 3.12 monitoring."""
import inspect
import json
import os
from pathlib import Path
import sys
import time

START = time.monotonic()
STARTED_EPOCH = time.time()
COLLECTED = []
REPORTS = []
COUNTS = {"calls": 0, "failed": 0, "skipped": 0}
EXECUTED_MODULES = {}
EXECUTED_MODULE_CODE = {}
CURRENT = "<collection>"
MONITOR = None
MONITOR_ENABLED = False
SOURCE_ROOT = Path.cwd().resolve() / "src" / "eab"
SOURCE_PREFIX = os.path.normcase(str(SOURCE_ROOT)).replace(chr(92), "/") + "/"
TARGET = Path(os.environ["H1_EXECUTION"])


def _relative(filename):
    name = os.path.normcase(str(filename)).replace(chr(92), "/")
    if name.startswith(SOURCE_PREFIX) and name.endswith(".py"):
        return "src/eab/" + name[len(SOURCE_PREFIX):]
    return None


def _started(code, offset=0):
    relative = _relative(code.co_filename)
    if relative is not None:
        # Do not disable a source code object seen outside an actual test: it
        # may run again inside a later test and that is the required witness.
        if CURRENT.startswith("<"):
            return None
        witness = dict(function=code.co_name, line=code.co_firstlineno, nodeid=CURRENT)
        if code.co_name == "<module>":
            EXECUTED_MODULE_CODE.setdefault(relative, witness)
        elif code.co_flags & inspect.CO_NEWLOCALS and not code.co_name.startswith("<"):
            # Class definition bodies have no CO_NEWLOCALS. Comprehensions,
            # generator expressions and lambdas are not def-call witnesses.
            EXECUTED_MODULES.setdefault(relative, witness)
    return sys.monitoring.DISABLE


def pytest_configure(config):
    global MONITOR
    if not hasattr(sys, "monitoring"):
        raise RuntimeError("H1 execution coverage requires Python 3.12+ sys.monitoring; refusing an unmeasured GREEN")
    MONITOR = 4
    sys.monitoring.use_tool_id(MONITOR, "h1-module-execution")
    sys.monitoring.register_callback(MONITOR, sys.monitoring.events.PY_START, _started)


def _progress(complete=False):
    path = Path(os.environ["H1_PROGRESS"])
    data = dict(complete=complete, elapsed_seconds=time.monotonic()-START,
                collected=len(COLLECTED), **COUNTS, current=CURRENT,
                started_epoch=STARTED_EPOCH, last_event_epoch=time.time())
    temporary = path.with_suffix(".writing")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    # A concurrent Windows reader can temporarily hold the destination open.
    for attempt in range(12):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(min(0.01 * (attempt + 1), 0.1))


def pytest_collection_finish(session):
    COLLECTED.extend(item.nodeid for item in session.items)
    _progress()


def pytest_runtest_logstart(nodeid, location):
    global CURRENT, STARTED_EPOCH, MONITOR_ENABLED
    CURRENT = nodeid
    STARTED_EPOCH = time.time()
    if not MONITOR_ENABLED:
        sys.monitoring.set_events(MONITOR, sys.monitoring.events.PY_START)
        MONITOR_ENABLED = True
    _progress()


def pytest_runtest_logreport(report):
    REPORTS.append(dict(nodeid=report.nodeid, when=report.when,
                        outcome=report.outcome, duration=report.duration))
    COUNTS["calls"] += report.when == "call"
    if report.outcome in ("failed", "skipped"):
        COUNTS[report.outcome] += 1
    if report.when == "teardown":
        _progress()


def pytest_runtest_logfinish(nodeid, location):
    global CURRENT
    CURRENT = "<between-tests>"


def pytest_sessionfinish(session, exitstatus):
    if MONITOR is not None:
        sys.monitoring.set_events(MONITOR, 0)
        sys.monitoring.free_tool_id(MONITOR)
    imported = sorted({relative for module in tuple(sys.modules.values())
                       if getattr(module, "__file__", None)
                       and (relative := _relative(module.__file__)) is not None})
    TARGET.write_text(json.dumps(dict(complete=True, collected=COLLECTED, reports=REPORTS,
        exitstatus=int(exitstatus), imported=imported, executed_modules=EXECUTED_MODULES,
        executed_module_code=EXECUTED_MODULE_CODE, source_root=str(SOURCE_ROOT),
        coverage_available=MONITOR is not None,
        coverage_method="stdlib sys.monitoring PY_START during tests; def calls and module code separately"), indent=2), encoding="utf-8")
    _progress(complete=True)
