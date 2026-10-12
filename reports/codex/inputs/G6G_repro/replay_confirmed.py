"""Run each unique confirmed-defect reproducer once, preserving root evidence."""
from pathlib import Path
import sys,os,json,subprocess
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'review'
data=json.loads((R/'G6G_findings.json').read_text(encoding='utf-8'))
scripts=sorted({f['repro_script'] for f in data['findings']})
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
failed=[]
for p in scripts:
    print('\n=== '+p+' ===',flush=True)
    result=subprocess.run([sys.executable,'-X','utf8',p],cwd=ROOT,env=env)
    if result.returncode:failed.append([p,result.returncode])
print(json.dumps({'unique_scripts':len(scripts),'reproduction_failures':failed},ensure_ascii=False))
sys.exit(bool(failed))
