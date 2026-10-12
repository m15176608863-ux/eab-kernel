"""G6E-49 equivalent production mutation only in a review/copies replica."""
from pathlib import Path
import sys,subprocess,shutil,json,hashlib,os
ROOT=Path(__file__).resolve().parents[2]
COPY=ROOT/'review/copies/geom2_vv_widened'
src=ROOT/'src/eab/kernel2d/covers.py'
before=hashlib.sha256(src.read_bytes()).hexdigest()
shutil.copytree(ROOT/'src',COPY/'src',dirs_exist_ok=True)
(COPY/'pytest.ini').write_text('[pytest]\npythonpath = src\n','utf-8')
(COPY/'tests').mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'tests/test_kernel2d_covers_e3.py',COPY/'tests/test_kernel2d_covers_e3.py')
target=COPY/'src/eab/kernel2d/covers.py'
old=b'return cross2_sign(lo, v) > 0 and cross2_sign(v, hi) > 0'
new=b'return _cone_accepts(lo, hi, v, Fraction(1, 100))'
raw=target.read_bytes();assert raw.count(old)==1;target.write_bytes(raw.replace(old,new))
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(COPY/'src');env['PYTHONIOENCODING']='utf-8'
cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider','tests/test_kernel2d_covers_e3.py','-k','vv_active_exact_support','--basetemp='+str(COPY/'tmp')]
p=subprocess.run(cmd,cwd=COPY,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8')
(ROOT/'review/geom2/g6e49_vv_mutation.log').write_text(p.stdout,'utf-8')
assert p.returncode==1 and 'VV activity must match exact neighbor support' in p.stdout,p.stdout
assert hashlib.sha256(src.read_bytes()).hexdigest()==before
print(json.dumps({'status':'CAUGHT','raw_id':'G6E-49','mutation':'production _open_cone widened to sin window 0.1','original_tracked_SHA256_unchanged':before,'target_failure':'VV activity must match exact neighbor support','last_output_line':p.stdout.strip().splitlines()[-1],'copy':str(COPY)},ensure_ascii=False,indent=2))
