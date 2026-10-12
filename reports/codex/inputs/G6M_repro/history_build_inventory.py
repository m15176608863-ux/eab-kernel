from pathlib import Path
import ast,hashlib,json,subprocess
root=Path('.')
oldroot=root/'review/copies/history_old';newroot=root/'review/copies/history_current'
def inventory(folder):
 out={}
 for p in (folder/'tests').glob('test_*.py'):
  src=p.read_text(encoding='utf-8-sig');tree=ast.parse(src)
  for n in tree.body:
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_'):
    k=p.name+'::'+n.name
    out[k]={'ast':ast.dump(n,include_attributes=False),'decorators':[ast.dump(d,include_attributes=False) for d in n.decorator_list],'asserts':[ast.unparse(a.test) for a in ast.walk(n) if isinstance(a,ast.Assert)],'source_sha256':hashlib.sha256(ast.get_source_segment(src,n).encode()).hexdigest()}
 return out
old,new=inventory(oldroot),inventory(newroot)
changed=[]
for k in sorted(old.keys()&new.keys()):
 if old[k]['ast']!=new[k]['ast']:
  changed.append({'test':k,'old':old[k],'new':new[k]})
d=dict(old_commit='b6126cf',new_commit=subprocess.check_output(['git','rev-parse','HEAD'],encoding='utf-8').strip(),old_test_function_count=len(old),new_test_function_count=len(new),common_names=len(old.keys()&new.keys()),changed_common_functions=len(changed),removed=sorted(old.keys()-new.keys()),added=sorted(new.keys()-old.keys()),changes=changed)
(root/'review/logs/history_test_migration_inventory.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print({k:v for k,v in d.items() if k not in ('changes','added')})
source=Path('D:/eab-wt/g6l/review/repro/legacy_g6e')
rows=[]
for p in sorted((root/'review/repro/history_legacy').glob('g6e_*_original.py')):
 x=source/p.name
 rows.append(dict(id=int(p.stem.split('_')[1]),source=str(x),copied=str(p),source_sha256=hashlib.sha256(x.read_bytes()).hexdigest(),copied_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),same_bytes=x.read_bytes()==p.read_bytes()))
(root/'review/logs/history_legacy_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('24 original copied script SHA match',all(r['same_bytes'] for r in rows))
