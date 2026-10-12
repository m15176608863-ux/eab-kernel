"""Read-only pytest observer: retain root-side failure traces as they arrive."""
import json
import os
from pathlib import Path

def pytest_runtest_logreport(report):
    target = os.environ.get('R8FIX_LIVE_FAILURES')
    if not target or os.environ.get('PYTEST_XDIST_WORKER') or not report.failed:
        return
    item = dict(nodeid=report.nodeid, when=report.when, duration=report.duration,
                longrepr=str(report.longrepr))
    with Path(target).open('a',encoding='utf-8') as out:
        out.write(json.dumps(item,ensure_ascii=False)+'\n')
