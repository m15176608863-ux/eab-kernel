"""Rerun the review's three component files with persistent UTF-8 evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode=True
out=Path(__file__).resolve().parent
root=out.parents[3]
temporary=out.parent/'tmp'/'review_probe_r4'
temporary.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TEMP=str(temporary),TMP=str(temporary))
files=('src/eab/kernel2d/motion.py','src/eab/kernel2d/motion_exit.py',
       'tests/test_m4c_motion.py','tests/test_m4c_exit.py','tests/test_m4c_numeric.py')
before={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
command=[sys.executable,'-X','utf8','-m','pytest','-q','tests/test_m4c_motion.py',
         'tests/test_m4c_exit.py','tests/test_m4c_numeric.py','--durations=3']
start=time.perf_counter()
run=subprocess.run(command,cwd=root,env=env,stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT,text=True,encoding='utf-8')
after={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
(out/'component_stdout.txt').write_text(run.stdout,encoding='utf-8',newline='')
result={'complete':True,'command':command,'returncode':run.returncode,
        'elapsed_seconds':time.perf_counter()-start,'last_line':run.stdout.strip().splitlines()[-1],
        'initial_sha256':before,'final_sha256':after,'input_hashes_unchanged':before==after}
(out/'component_run.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='')
print(run.stdout)
raise SystemExit(run.returncode if before==after else 2)
