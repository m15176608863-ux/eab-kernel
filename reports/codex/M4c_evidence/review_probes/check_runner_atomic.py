"""Read-only reviewer probe of the actual pytest plugin in child processes."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
import m4c_run_gates as runner

OUT=Path(__file__).resolve().parent
TEMP=OUT.parent/'tmp'/'review_runner_r2'
TEMP.mkdir(exist_ok=True)
FILES=('tools/m4c_run_gates.py','tests/test_m4c_runner.py')
BEFORE={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
PROBE=r'''
# Reviewer injection inside actual atomic filesystem replacement. No output
# object or node list is forged. Each real pytest hook calls actual progress.
_review_original_replace = Path.replace
_review_original_progress = progress
_review_records = []
_review_mode = os.environ["REVIEW_REPLACE_MODE"]
_review_telemetry = Path(os.environ["REVIEW_REPLACE_TELEMETRY"])
def _review_write():
    _review_telemetry.write_text(json.dumps(_review_records), encoding="utf-8")
def progress(complete=False):
    _review_records.append(dict(complete=complete, attempts=0, delays=[]))
    _review_write()
    return _review_original_progress(complete)
def _review_replace(source, destination):
    if str(destination) == os.environ["M4C_NODE_PROGRESS"]:
        item = _review_records[-1]
        item["attempts"] += 1
        _review_write()
        if _review_mode == "permanent" or (_review_mode == "transient" and item["attempts"] <= 2):
            raise PermissionError(5, "independent reviewer simulated sharing denial")
        if _review_mode == "other_error":
            raise FileNotFoundError("independent reviewer non-sharing I/O error")
    return _review_original_replace(source, destination)
def _review_sleep(delay):
    _review_records[-1]["delays"].append(delay)
    _review_write()
Path.replace = _review_replace
time.sleep = _review_sleep
'''

results={}
start=time.perf_counter()
for mode in ('transient','permanent','other_error'):
    work=TEMP/mode
    work.mkdir(exist_ok=False)
    (work/'test_one.py').write_text('def test_one():\n    assert 1 + 1 == 2\n',encoding='utf-8')
    (work/'review_plugin.py').write_text(runner.PLUGIN+PROBE,encoding='utf-8')
    progress=work/'progress.json'
    progress.write_text('{"previous":true}',encoding='utf-8')
    execution=work/'execution.json'
    telemetry=work/'telemetry.json'
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',
             PYTHONPATH=str(work),TEMP=str(TEMP),TMP=str(TEMP),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
             M4C_NODE_PROGRESS=str(progress),M4C_NODE_JOURNAL=str(work/'journal.jsonl'),
             M4C_EXECUTION_RECORD=str(execution),REVIEW_REPLACE_MODE=mode,
             REVIEW_REPLACE_TELEMETRY=str(telemetry))
    command=[sys.executable,'-X','utf8','-m','pytest','-q','--rootdir',str(work),'-p','no:cacheprovider','-p','review_plugin','test_one.py']
    child=subprocess.run(command,cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                         text=True,encoding='utf-8',timeout=30)
    (OUT/f'runner_plugin_{mode}.txt').write_text(child.stdout,encoding='utf-8')
    attempts=json.loads(telemetry.read_text(encoding='utf-8'))
    data=json.loads(execution.read_text(encoding='utf-8')) if execution.exists() else {}
    actual=[r['nodeid'] for r in data.get('reports',[]) if r['when']=='call']
    collected=data.get('collected',[])
    if mode=='transient':
        assert child.returncode==0
        assert len(attempts)==3 and all(r['attempts']==3 and r['delays']==[0.01,0.02] for r in attempts)
        assert collected==actual==['test_one.py::test_one']
        assert data['complete'] is True and data['exitstatus']==0
        assert not any(r['outcome']=='skipped' for r in data['reports'])
    else:
        assert child.returncode!=0
        expected=12 if mode=='permanent' else 1
        assert attempts and all(r['attempts']==expected for r in attempts)
        delays=[min(0.01*n,0.1) for n in range(1,12)] if mode=='permanent' else []
        assert all(r['delays']==delays for r in attempts)
        assert actual==[]
        assert json.loads(progress.read_text(encoding='utf-8'))=={'previous':True}
    runner_green=(child.returncode==0 and data.get('complete',False)
                  and sorted(collected)==sorted(actual)==['test_one.py::test_one']
                  and not any(r['outcome']=='skipped' for r in data.get('reports',[])))
    assert runner_green==(mode=='transient')
    results[mode]={'exit_code':child.returncode,'progress_invocations':len(attempts),'telemetry':attempts,
                   'actual_collected':collected,'actual_executed':actual,'runner_would_be_green':runner_green,
                   'execution_complete':data.get('complete',False),'plugin_exitstatus':data.get('exitstatus'),
                   'last_line':child.stdout.strip().splitlines()[-1]}

after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
assert BEFORE==after
result={'complete':True,'seconds':time.perf_counter()-start,'cases':results,
        'before_sha256':BEFORE,'after_sha256':after,
        'scope':'Actual pytest hooks of generated real PLUGIN; temporary Path.replace and sleep injection inside child only; not full suite'}
(OUT/'runner_atomic_probe.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'complete':True,'seconds':result['seconds'],'cases':{k:{'exit_code':v['exit_code'],'runner_would_be_green':v['runner_would_be_green'],'progress_invocations':v['progress_invocations']} for k,v in results.items()}}))
