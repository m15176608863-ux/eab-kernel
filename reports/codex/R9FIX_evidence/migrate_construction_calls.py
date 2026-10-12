"""One-shot reviewed AST-guided boundary migration; byte/newline preserving."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OWNED = {
    'tests/e5a_cover_oracle.py', 'tests/e5a_escape_oracle.py', 'tests/e5a_g2_oracle.py',
    'tests/perf_cover_oracle_reference.py', 'tests/perf_escape_oracle_reference.py',
    'tests/e5b_margin_oracle.py', 'tests/test_near_parallel_edges.py',
}
MUTANTS = {'test_g6f06_gap_magnitude_gate_has_teeth',
           'test_g2_oracle_early_square_rounding_mutation_is_caught'}
SOURCE = {'src/eab/kernel2d/geom.py', 'src/eab/kernel2d/g0.py',
          'src/eab/kernel3d/entrance3.py', 'src/eab/kernel3d/interlock.py',
          'src/eab/kernel3d/g03.py', 'src/eab/margin.py'}
ledger = []
for path in [*sorted((ROOT/'tests').rglob('*.py')),
             *(ROOT/p for p in sorted(SOURCE))]:
    rel = path.relative_to(ROOT).as_posix()
    if rel in OWNED or path.name.startswith('test_r9fix') or path.name == 'construction_oracle.py':
        continue
    raw = path.read_bytes()
    text = raw.decode('utf-8-sig')
    tree = ast.parse(text)
    lines = text.encode('utf8').splitlines(keepends=True)
    offsets = [0]
    for line in lines: offsets.append(offsets[-1]+len(line))
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node): parents[child] = node
    test = rel.startswith('tests/') or rel == 'src/eab/kernel2d/g0.py'
    suffix = 'exact' if test else 'rational'
    edits, used = [], set()
    def edit(node, replacement):
        edits.append((offsets[node.lineno-1]+node.col_offset,
                      offsets[node.end_lineno-1]+node.end_col_offset,
                      replacement.encode('utf8')))
        ledger.append(dict(path=rel,line=node.lineno,before=ast.get_source_segment(text,node),after=replacement))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call): continue
        parent = node
        function = None
        while parent in parents:
            parent = parents[parent]
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function = parent.name;break
        if function in MUTANTS: continue
        name = (node.func.id if isinstance(node.func,ast.Name)
                else node.func.attr if isinstance(node.func,ast.Attribute) else '')
        if name == 'sqrt' and len(node.args)==1:
            arg=node.args[0]
            if isinstance(arg,ast.Call) and isinstance(arg.func,ast.Name) and arg.func.id=='float':
                used.add('sqrt_'+suffix)
                edit(node, 'sqrt_'+suffix+'('+ast.get_source_segment(text,arg.args[0])+')')
                continue
        if name == 'float' and isinstance(node.func,ast.Name):
            if len(node.args)==1 and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str) and node.args[0].value.lower().lstrip('+-') in {'inf','nan','infinity'}:
                continue
            used.add('scalar_'+suffix)
            edit(node.func,'scalar_'+suffix)
        elif name=='map' and node.args and isinstance(node.args[0],ast.Name) and node.args[0].id=='float':
            used.add('scalar_'+suffix)
            edit(node.args[0],'scalar_'+suffix)
    if not edits: continue
    # A root replacement supersedes its internal callee replacement.
    filtered=[]
    for edit_ in sorted(edits,key=lambda e:(e[0],-e[1])):
        if filtered and edit_[0]<filtered[-1][1]:continue
        filtered.append(edit_)
    data=text.encode('utf8')
    for start,end,replacement in reversed(filtered): data=data[:start]+replacement+data[end:]
    module = ('construction_oracle' if rel.startswith('tests/') else
              'eab.oracle_construction' if test else 'eab.construction')
    import_line='from '+module+' import '+', '.join(sorted(used))
    updated=data.decode('utf8')
    t=ast.parse(updated); last=0
    for n in t.body:
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):last=n.end_lineno
        elif isinstance(n,ast.ImportFrom) and n.module=='__future__':last=n.end_lineno
        else:break
    rows=updated.splitlines(keepends=True); newline='\r\n' if b'\r\n' in raw else '\n'
    rows.insert(last,import_line+newline)
    path.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(rows).encode('utf8'))
(ROOT/'reports/codex/R9FIX_evidence/construction_migration.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf8')
print(len(ledger), 'AST boundary edits; formulas audited separately')
