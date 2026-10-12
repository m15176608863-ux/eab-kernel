import sys,os,subprocess,time,json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
name=sys.argv[1]
command=sys.argv[2:]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
t=time.monotonic()
r=subprocess.run(command,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                 text=True,encoding='utf8',errors='replace')
(root/'review/logs'/f'{name}.log').write_text(r.stdout,encoding='utf8')
(root/'review/logs'/f'{name}.json').write_text(json.dumps(dict(command=command,exit_code=r.returncode,
              elapsed_seconds=time.monotonic()-t),indent=2),encoding='utf8')
print(r.stdout)
print('EXIT',r.returncode)
