"""Read-only diagnostic inventory. Never writes or refreshes the policy."""
import ast,collections,importlib.util,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("r12b_gate", ROOT/"tools/check_exact_construction.py")
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
label=sys.argv[1]
rows=[];start=time.perf_counter()
for folder in ("src","tests"):
 for p in sorted((ROOT/folder).rglob("*.py")):
  path=p.relative_to(ROOT).as_posix(); text=p.read_text(encoding="utf-8-sig");t=time.perf_counter()
  issues=g.scan_text(text,path,repository_root=ROOT)
  if issues:
   contexts=g._subset.site_contexts(text);tree=ast.parse(text)
   nodes=collections.defaultdict(list)
   for node in ast.walk(tree):
    if hasattr(node,"lineno"):
     nodes[(node.lineno,ast.get_source_segment(text,node))].append(node)
   for row in issues:
    candidates=nodes[(row[1],row[4])]
    assert candidates,(path,row)
    node=candidates[0]
    rows.append(dict(path=path,line=row[1],function=row[2],rule=row[3],source=row[4],node=ast.dump(node,include_attributes=False),context=contexts[row[2]]))
  if len(issues)>20 or time.perf_counter()-t>3:
   print(path,len(issues),round(time.perf_counter()-t,2),flush=True)
(OUT/(label+".json")).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
summary=dict(total=len(rows),distinct=len({(r["path"],r["function"],r["rule"],r["node"],r["context"]) for r in rows}),seconds=time.perf_counter()-start,by_rule=dict(collections.Counter(r["rule"] for r in rows)),by_path=dict(collections.Counter(r["path"] for r in rows)))
(OUT/(label+"_summary.json")).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False),flush=True)
