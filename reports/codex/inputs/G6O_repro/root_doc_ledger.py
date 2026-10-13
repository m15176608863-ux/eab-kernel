"""G6O document-pointer ledger. Existence is deliberately NOT semantic proof."""
from pathlib import Path
import ast, json, re, sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
names = {}
for p in sorted((ROOT / 'tests').rglob('*.py')):
    tree = ast.parse(p.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.setdefault(node.name, []).append({
                'file': p.relative_to(ROOT).as_posix(), 'line': node.lineno})

rows = json.loads((ROOT / 'review/evidence/document_claim_inventory.json').read_text(encoding='utf-8'))
missing = []
for row in rows:
    modules, definitions, wildcards = {}, {}, []
    for name in sorted(set(re.findall(r'\b(test_[A-Za-z0-9_]+)\b', row['claim']))):
        path = ROOT / 'tests' / (name + '.py')
        if path.exists():
            modules[name] = path.relative_to(ROOT).as_posix()
        elif name.endswith('_'):
            wildcards.append(name)
        else:
            definitions[name] = names.get(name, [])
            if not definitions[name]:
                missing.append((row['file'], row['line'], name))
    row.update(test_modules=modules, test_definitions=definitions,
               wildcard_prefixes=wildcards,
               pointer_result='存在' if modules or definitions else '本行没有具体测试指针',
               semantic_verification='不能从存在或全套绿色推出全文数学承诺；具体审读和有限反证见 G6O_report 镜头8及完整性批评')

result = dict(claim_lines=len(rows), missing_concrete_test_definitions=missing,
              interpretation='只核测试文件/函数真实存在；历史上下文和数学含义须另审。', rows=rows)
dest = ROOT / 'review/evidence/root_doc_claim_ledger.json'
dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
assert not missing, missing
print(f'DOC POINTER PASS: {len(rows)} claim lines, no missing concrete test pointer; NOT a mathematical proof')
