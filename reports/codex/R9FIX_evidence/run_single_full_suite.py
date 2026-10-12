"""Standard single-process full pytest, retaining a source freeze and JUnit."""
import importlib.util
import json
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('suite_support', OUT/'run_full_suite.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def main():
    start = time.perf_counter()
    before = support.snapshot()
    command = support.BASE + ['tests', '--basetemp='+str(OUT/'tmp/full_single'),
                              '--junitxml='+str(OUT/'full_single.xml'), '--durations=20']
    with (OUT/'full_single.log').open('wb') as stream:
        result = subprocess.run(command, cwd=support.ROOT, env=support.env,
                                stdout=stream, stderr=subprocess.STDOUT)
    after = support.snapshot()
    cases = ET.parse(OUT/'full_single.xml').getroot().findall('.//testcase')
    expected = json.loads((OUT/'full_suite.json').read_text(encoding='utf8'))['collected']
    metadata = dict(command=command, seconds=time.perf_counter()-start, exit_code=result.returncode,
        tests=len(cases),expected=expected,skipped=sum(c.find('skipped') is not None for c in cases),
        failures=sum(c.find('failure') is not None for c in cases),
        errors=sum(c.find('error') is not None for c in cases),
        source_drift=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p)),
        last_line=(OUT/'full_single.log').read_text(encoding='utf8').strip().splitlines()[-1])
    (OUT/'full_single.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
    (OUT/'full_single_source_freeze.json').write_text(json.dumps(before,indent=2),encoding='utf8')
    print(json.dumps(metadata,indent=2),flush=True)
    return bool(result.returncode or len(cases)!=expected or metadata['source_drift'] or
                any(metadata[key] for key in ('skipped','failures','errors')))


if __name__ == '__main__':
    raise SystemExit(main())
