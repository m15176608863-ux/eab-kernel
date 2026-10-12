"""G6M: real internal constructor mutation, archived repositories only.
The defect sets positive-event output x to start x0, without changing candidates,
exact_t/time, normal, finite-feature label, or the mathematical self-check.
Snapshots are read-only git archives of b6126cf and fabe303; if absent this
script reconstructs them below review/copies only. Run serially: these two
copies are shared with history_x_exhibit.py and history_x_static_redundancy.py.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/logs/history_x_migration';OUT.mkdir(parents=True,exist_ok=True)
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
TARGET='tests/test_entrance3.py::test_first_entrance_agrees_with_the_predicate_only_oracle_on_random_convex_pairs'

def prepare_copy(label, revision):
    folder=ROOT/'review/copies'/label
    if (folder/'pyproject.toml').is_file():
        return
    if folder.exists() and any(folder.iterdir()):
        raise RuntimeError('Refusing to overwrite a partial or unknown review snapshot: '+str(folder))
    folder.mkdir(parents=True,exist_ok=True)
    archive=ROOT/'review/copies'/(label+'.zip')
    # git archive only reads repository objects; no git state-changing operation.
    subprocess.run(['git','archive','--format=zip','--output='+str(archive),revision,
                    'src','tests','tools','fixtures','docs','pyproject.toml','README.md','AGENTS.md'],
                   cwd=ROOT,check=True)
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            target=(folder/item.filename).resolve()
            if not target.is_relative_to(folder.resolve()):
                raise RuntimeError('Unexpected archive path outside review snapshot')
        z.extractall(folder)
    print('prepared read-only git archive',label,revision,flush=True)

prepare_copy('history_old','b6126cf')
prepare_copy('history_current','fabe303b9d574891094b0b9e86b171343e469bfc')
rows=[]
def run(folder,label,stage,targets):
    cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*targets,'--basetemp='+str(folder/'review_tmp'/stage),'--tb=short']
    st=time.perf_counter();r=subprocess.run(cmd,cwd=folder,env=ENV,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=360)
    log=OUT/(label+'_'+stage+'.log');log.write_text(r.stdout,encoding='utf-8')
    d=dict(label=label,stage=stage,command=cmd,exit_code=r.returncode,seconds=time.perf_counter()-st,summary=r.stdout.strip().splitlines()[-1],verified_output=r.stdout,log=str(log));rows.append(d)
    (OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(label,stage,d['exit_code'],d['summary'],flush=True);return d
for label in ('history_old','history_current'):
    folder=ROOT/'review/copies'/label;p=folder/'src/eab/kernel3d/entrance3.py';raw=p.read_bytes();s=raw.decode('utf-8-sig')
    old='return Entrance3("entrance", t, x, rep_label,'
    new='return _restore_sources(Entrance3("entrance", scalar_rational(t), tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x), rep_label,'
    needle=old if label.endswith('old') else new
    change='return Entrance3("entrance", t, x0, rep_label,' if label.endswith('old') else 'return _restore_sources(Entrance3("entrance", scalar_rational(t), tuple(scalar_rational(_mapped_value) for _mapped_value in x0), rep_label,'
    assert s.count(needle)==1,(label,needle)
    assert run(folder,label,'baseline',[TARGET])['exit_code']==0
    p.write_bytes(s.replace(needle,change).encode('utf-8'))
    try:
        result=run(folder,label,'mutant',[TARGET])
        assert result['exit_code']==(1 if label.endswith('old') else 0),result
        if label.endswith('current'):
            broader=run(folder,label,'mutant_entrance_domain',['tests/test_entrance3.py','tests/test_entrance3_concave.py','tests/test_entrance3_exact.py','tests/test_entrance3_g2.py','tests/test_r8fix_initial_state3.py','tests/test_r10_initial_boundary.py'])
            assert broader['exit_code']==0,broader
    finally:
        p.write_bytes(raw)
        assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(raw).digest()
    rows.append(dict(label=label,restored_sha256=hashlib.sha256(raw).hexdigest(),byte_restoration=True))
    (OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('HISTORY_X_MIGRATION_CONFIRMED old gate red / new gate green / archives restored')
