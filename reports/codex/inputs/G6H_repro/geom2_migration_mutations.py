"""Mutation verification in a detached file copy, never the audited tree."""
from pathlib import Path
import subprocess,sys,json,shutil,hashlib,os,time
ROOT=Path(__file__).resolve().parents[2]
COPY=ROOT/'review/copies/geom2_migration'
COPY.mkdir(parents=True,exist_ok=True)
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
for name in filter(None,tracked):
    src=ROOT/name;dst=COPY/name
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(COPY/'src')}
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/eab/kernel2d').glob('*.py')}
tasks=[
 ('vv_exact_activity','src/eab/kernel2d/covers.py','active = _open_cone(alo, ahi, d) and _open_cone(blo, bhi, d)','active = True', ['tests/test_kernel2d_lever.py::test_vv_cover_strictness_is_invariant_when_the_separation_direction_is_on_the_cone_boundary','tests/test_kernel2d_covers_e3.py::test_vv_active_exact_support_not_a_roundoff_band']),
 ('segment_hidden_band','src/eab/kernel2d/covers.py','return isfinite(window) and excess * excess <= Fraction(max(window, 0.0)) ** 2 * l2','return isfinite(window) and excess * excess <= Fraction(max(window, 1e-3)) ** 2 * l2', ['tests/test_kernel2d_lever.py::test_ve_cover_in_segment_band_is_invariant_for_a_vertex_over_a_short_edge_endpoint','tests/test_kernel2d_covers_e3.py::test_segment_window_is_not_lifted_to_coordinate_noise']),
 ('facet_gap_sign','src/eab/kernel2d/covers.py','numerator = direction[1]*v[0]-direction[0]*v[1]','numerator = -(direction[1]*v[0]-direction[0]*v[1])',['tests/test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip']),
 ('drop_isolated_boundary','src/eab/kernel2d/g0_oracle.py','if overlap(Ah, B) == 0 and boundary_has_exterior(Ah, B):','if False and overlap(Ah, B) == 0 and boundary_has_exterior(Ah, B):',['tests/test_r7fix_geom2.py::test_g6g01_first_exit_checks_isolated_true_boundary_event']),
]
results=[]
for label,file,old,new,nodes in tasks:
    command=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*nodes,'--basetemp='+str(COPY/'review_tmp'/label)]
    (COPY/'review_tmp').mkdir(exist_ok=True)
    base=subprocess.run(command,cwd=COPY,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    assert base.returncode==0,(label,base.stdout)
    p=COPY/file;original=p.read_bytes();text=original.decode('utf-8-sig');assert text.count(old)==1,(label,text.count(old))
    bom=original.startswith(b'\xef\xbb\xbf')
    p.write_bytes((b'\xef\xbb\xbf' if bom else b'')+text.replace(old,new).encode('utf-8'))
    try:
        mutant=subprocess.run(command,cwd=COPY,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
        assert mutant.returncode==1,(label,mutant.stdout)
        (ROOT/'review/logs'/('geom2_mutation_'+label+'.log')).write_text(mutant.stdout,encoding='utf-8')
        results.append({'label':label,'file':file,'nodes':nodes,'baseline_output':base.stdout,'mutant_exit':mutant.returncode,'verified_output':mutant.stdout,'copy':str(COPY),'before_sha256':hashlib.sha256(original).hexdigest()})
    finally:p.write_bytes(original)
    results[-1]['restored_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    assert results[-1]['restored_sha256']==results[-1]['before_sha256']
after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/eab/kernel2d').glob('*.py')}
assert hashes==after
out={'original_kernel2d_sha256_unchanged':hashes==after,'mutations':results}
(ROOT/'review/agents/geom2/mutations.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'label':r['label'],'baseline_last_line':r['baseline_output'].splitlines()[-1],'mutant_last_line':r['verified_output'].splitlines()[-1],'restored':r['before_sha256']==r['restored_sha256']} for r in results],indent=2))
