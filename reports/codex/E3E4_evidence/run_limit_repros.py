from pathlib import Path
import os,subprocess,sys
out=Path(__file__).resolve().parent
root=out.parents[2]
env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONPATH"]=str(root/"src");env["TEMP"]=env["TMP"]=str(out/"tmp")
for p in sorted(out.glob("repro_limit_*_limit*.py")):
    r=subprocess.run([sys.executable,"-X","utf8",str(p)],cwd=root,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace")
    name=p.stem.replace("repro_limit_","")
    (out/("current_"+name+".txt")).write_text(r.stdout+r.stderr,encoding="utf-8")
    print(name,r.returncode)
r=subprocess.run([sys.executable,"-X","utf8",str(out/"repro_limit_238_test.py")],cwd=root,env=env,capture_output=True,text=True,encoding="utf-8")
(out/"current_test_limit_multi_238.txt").write_text(r.stdout+r.stderr,encoding="utf-8")
print("238",r.returncode)
