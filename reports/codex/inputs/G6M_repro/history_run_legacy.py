from pathlib import Path
import subprocess,sys,json,time,os
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/logs/history_legacy'; OUT.mkdir(parents=True,exist_ok=True)
rows=[]
for p in sorted((ROOT/'review/repro/history_legacy').glob('g6e_*_original.py')):
    start=time.perf_counter()
    try:
        r=subprocess.run([sys.executable,'-X','utf8',str(p)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=420,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8'))
        d=dict(id=int(p.stem.split('_')[1]),source=str(p),returncode=r.returncode,seconds=time.perf_counter()-start,verified_output=r.stdout+r.stderr)
    except subprocess.TimeoutExpired as e:d=dict(id=int(p.stem.split('_')[1]),source=str(p),returncode='timeout',seconds=time.perf_counter()-start,verified_output=str(e))
    (OUT/(p.stem+'.log')).write_text(d['verified_output'],encoding='utf-8');rows.append(d)
    (OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(d['id'],d['returncode'],round(d['seconds'],2),d['verified_output'][-300:].replace('\n',' | '),flush=True)
print('LEGACY_REPLAYS_COMPLETE',len(rows))
