"""Read-only audit: four independent pytest shards, every collected node once."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, time
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'review'
(OUT/'logs').mkdir(parents=True, exist_ok=True)
(OUT/'tmp').mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
env['PYTHONPATH'] = str(ROOT/'src') + os.pathsep + env.get('PYTHONPATH','')
tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
snapshot = {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in tracked if f and (ROOT/f).is_file()}
(OUT/'tracked_before.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
base = [sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider']
t0 = time.perf_counter()
collection = subprocess.run(base+['--collect-only','tests'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(OUT/'logs/full_collection.log').write_bytes(collection.stdout)
nodes = [s for s in collection.stdout.decode('utf-8',errors='replace').splitlines() if s.startswith('tests/') and '::' in s]
assert collection.returncode == 0 and len(nodes)>10000,(collection.returncode,len(nodes))
counts = {}
for node in nodes:
    module=node.split('::')[0]
    counts[module]=counts.get(module,0)+1
groups=[[] for _ in range(4)]; loads=[0]*4
for module,count in sorted(counts.items(),key=lambda x:(-x[1],x[0])):
    i=loads.index(min(loads)); groups[i].append(module); loads[i]+=count
processes=[]; streams=[]; commands=[]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
for i,group in enumerate(groups):
    command=base+group+['--basetemp='+str(OUT/'tmp'/('full_'+str(i))), '--junitxml='+str(OUT/'logs'/('full_'+str(i)+'.xml')),'--durations=10']
    stream=(OUT/'logs'/('full_'+str(i)+'.log')).open('wb'); streams.append(stream); commands.append(command)
    processes.append(subprocess.Popen(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT))
results=[]
for i,p in enumerate(processes):
    code=p.wait(); streams[i].close()
    log=(OUT/'logs'/('full_'+str(i)+'.log')).read_text(encoding='utf-8',errors='replace')
    results.append(dict(shard=i,count=loads[i],exit_code=code,last_line=log.strip().splitlines()[-1]))
drift=[f for f,h in snapshot.items() if not (ROOT/f).is_file() or hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h]
metadata=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),mode='4 independent module shards, no xdist',collected=len(nodes),start_utc=start,end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),seconds=time.perf_counter()-t0,commands=commands,results=results,tracked_drift=drift)
(OUT/'full_suite.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(metadata,ensure_ascii=False,indent=2))
raise SystemExit(bool(drift) or any(r['exit_code'] for r in results))
