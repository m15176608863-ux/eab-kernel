import os,sys,json,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
rows=[]
for p in sorted((ROOT/'review/repro').glob('g6e_*_original.py')):
 t=time.time();r=subprocess.run([sys.executable,'-X','utf8',str(p)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 log=ROOT/'review/logs'/f'{p.stem}.log';log.write_text(r.stdout+r.stderr,encoding='utf-8')
 row=dict(id=int(p.stem.split('_')[1]),script=p.relative_to(ROOT).as_posix(),log=log.relative_to(ROOT).as_posix(),returncode=r.returncode,seconds=round(time.time()-t,3),verified_output=r.stdout+r.stderr)
 rows.append(row);print(row['id'],row['returncode'],row['seconds'])
(ROOT/'review/agents/legacy_replay_results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(r['returncode']==0 for r in rows)
