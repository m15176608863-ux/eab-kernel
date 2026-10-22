"""WO-C3L3 sequential authoritative differential and H1 closeout, no Git writes."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"reports/codex/C3L3_evidence"
def write(data):
    (OUT/"closeout_progress.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
def main():
    commands=[
        ("differential",[sys.executable,"-X","utf8","tools/eab2_c3l3_diff.py","--dll",str(ROOT/"eab2/build/eab2.dll"),"--family","all","--output",str(OUT/"differential.json")]),
        ("final_fast",[sys.executable,"-X","utf8","tools/h1_run_gates.py","--name","final_fast","--evidence-root","reports/codex/C3L3_evidence"]),
        ("final_full",[sys.executable,"-X","utf8","tools/h1_run_gates.py","--name","final_full","--runslow","--evidence-root","reports/codex/C3L3_evidence"])]
    records=[]
    env=dict(os.environ,TEMP=str(OUT/"tmp"),TMP=str(OUT/"tmp"),PYTHONIOENCODING="utf-8",PYTHONDONTWRITEBYTECODE="1")
    for name,command in commands:
        start=time.time();write(dict(complete=False,current=name,started=start,records=records,command=command))
        log=OUT/(name+".log")
        with log.open("w",encoding="utf-8",newline="\n") as stream:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,check=False)
        lines=log.read_text("utf-8",errors="replace").splitlines()
        records.append(dict(name=name,command=command,returncode=result.returncode,elapsed_seconds=time.time()-start,last_line=lines[-1] if lines else "",log=str(log)))
        print(json.dumps(records[-1]),flush=True)
        write(dict(complete=False,current=name,records=records))
        if result.returncode:
            write(dict(complete=False,failed=name,records=records));return result.returncode
    write(dict(complete=True,records=records))
    print("C3L3_CLOSEOUT_SEQUENCE_OK",flush=True)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
