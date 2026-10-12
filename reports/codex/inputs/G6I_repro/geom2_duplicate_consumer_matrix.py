"""Scope duplicate-display-facet gate observation against all direct test consumers."""
from pathlib import Path
import ast,shutil,subprocess,sys,os,json,hashlib
ROOT=Path(__file__).resolve().parents[2];COPY=ROOT/'review/copies/geom2_display_duplicate'
for directory in ('src','tests','tools','fixtures'):
    shutil.copytree(ROOT/directory,COPY/directory,dirs_exist_ok=True)
(COPY/'pytest.ini').write_text('[pytest]\npythonpath = src\n','utf-8')
source_path=ROOT/'src/eab/kernel2d/covers.py';before=hashlib.sha256(source_path.read_bytes()).hexdigest()
target=COPY/'src/eab/kernel2d/covers.py';source=target.read_text('utf-8')
old='return EntranceBlock(verts, [f.label for f in ex.facets], list(ex.pairs))'
new='''labels = [f.label for f in ex.facets]
    if max(abs(p[0]) for P in (A, B) for p in P) > 100:
        labels.append(labels[0])
    return EntranceBlock(verts, labels, list(ex.pairs))'''
assert source.count(old)==1;target.write_text(source.replace(old,new),'utf-8')
nodes=[]
for path in (ROOT/'tests').glob('test_*.py'):
    tree=ast.parse(path.read_text('utf-8-sig'))
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_') and any(
            isinstance(call,ast.Call) and ((isinstance(call.func,ast.Name) and call.func.id=='convex_entrance_block') or
                (isinstance(call.func,ast.Attribute) and call.func.attr=='convex_entrance_block')) for call in ast.walk(node)):
            nodes.append(path.relative_to(ROOT).as_posix()+'::'+node.name)
nodes.append('tests/test_invariance_2d.py::test_convex_g0_is_invariant')
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(COPY/'src');env['PYTHONIOENCODING']='utf-8'
cmd=[sys.executable,'-X','utf8','-m','pytest','-q','-p','no:cacheprovider',*nodes,'--basetemp='+str(COPY/'tmp')]
r=subprocess.run(cmd,cwd=COPY,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8')
(ROOT/'review/geom2/duplicate_consumer_matrix.log').write_text(r.stdout,'utf-8')
assert r.returncode==1 and 'test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation' in r.stdout
assert hashlib.sha256(source_path.read_bytes()).hexdigest()==before
out={'status':'CAUGHT_BY_OTHER_EXISTING_GATES','all_direct_test_consumers_included':True,'test_function_nodes':nodes,
     'function_node_count':len(nodes),'pytest_last_line':r.stdout.strip().splitlines()[-1],
     'original_tracked_SHA256_unchanged':before,'decision':'local migration observation only; do not count as a new major or whole-suite no-teeth finding',
     'copy':str(COPY)}
(ROOT/'review/geom2/duplicate_consumer_matrix.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
