"""Re-run exact-cover internal mutations in workspace-only isolated packages."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
source=ROOT/'src/eab/kernel3d/covers3.py'
original=source.read_bytes()
records=json.loads((OUT/'covers_mutations.json').read_text(encoding='utf-8'))
for row in records:
    dest=OUT/'tmp'/'covers_final_mutations'/row['mutation']
    shutil.copytree(ROOT/'src/eab',dest/'eab',dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    old,new=row['old'],row['new']
    text=original.decode('utf-8')
    assert text.count(old)==1,row['mutation']
    (dest/'eab/kernel3d/covers3.py').write_bytes(text.replace(old,new).encode('utf-8'))
    cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',
         '-o',f'pythonpath={dest.as_posix()}',f'--basetemp={dest/"pytest"}',
         'tests/test_covers3_e5a.py','-k',row['test'],'--tb=short']
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['TEMP']=env['TMP']=str(OUT/'tmp')
    start=time.perf_counter()
    run=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    output=run.stdout+run.stderr
    (OUT/f'mutation_{row["mutation"]}.txt').write_text(output,encoding='utf-8')
    row.update(exit_code=run.returncode,elapsed_s=time.perf_counter()-start,
               summary=output.strip().splitlines()[-1],command=cmd,
               source_sha256=hashlib.sha256(original).hexdigest(),source_unchanged=source.read_bytes()==original)
    assert run.returncode==1 and 'E   assert' in output and 'FAILED tests/' in output,row
    assert row['source_unchanged']
(OUT/'covers_mutations.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('\n'.join(r['mutation']+': '+r['summary'] for r in records))
