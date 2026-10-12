from pathlib import Path
import os,subprocess,sys,time,json
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'review/geometry';rows=[]
for p in sorted((ROOT/'review/repro/legacy_g6e').glob('g6e_*_original.py')):
 start=time.perf_counter()
 try:
  r=subprocess.run([sys.executable,'-X','utf8',str(p)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  data=dict(id=int(p.stem.split('_')[1]),source=str(p),returncode=r.returncode,seconds=time.perf_counter()-start,verified_output=r.stdout+r.stderr)
 except subprocess.TimeoutExpired as e:data=dict(id=int(p.stem.split('_')[1]),source=str(p),returncode='timeout',seconds=time.perf_counter()-start,verified_output=str(e))
 (out/(p.stem+'.log')).write_text(data['verified_output'],encoding='utf-8');rows.append(data);print(data['id'],data['returncode'],round(data['seconds'],2),flush=True)
 (out/'legacy_replay_results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('LEGACY REPLAY COMPLETE',len(rows),'scripts;',sum(r['returncode']==0 for r in rows),'successful invocations')
