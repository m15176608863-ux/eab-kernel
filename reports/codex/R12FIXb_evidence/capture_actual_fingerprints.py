"""Evidence-only exact diagnostic capture; never changes policy or source files.

The original scan_candidates.py guessed nodes from line/source and selected an
Expr wrapper before its Call/Yield. Preserve each scanner's real issue node
instead. This changes only the in-memory diagnostic payload, not decisions.
"""
import collections
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
scanner = ROOT / 'tools/check_exact_construction.py'
source = scanner.read_text(encoding='utf-8')
old = 'issues = [row[:5] for row in closed_rows]'
assert source.count(old) == 1
source = source.replace(old, 'issues = list(closed_rows)')
old = 'issues.append((path, node.lineno, function, rule, ast.get_source_segment(text, node)))'
assert source.count(old) == 1
source = source.replace(old, 'issues.append((path, node.lineno, function, rule, ast.get_source_segment(text, node), ast.dump(node, include_attributes=False), _subset.site_contexts(text)[function]))')
namespace = {'__file__': str(scanner), '__name__': 'evidence_actual_ast_capture'}
exec(compile(source, '<diagnostic payload only>', 'exec'), namespace)
subset = namespace['_subset']
policy = subset._policy()
subset._policy = lambda: {**policy, 'waivers': []}
rows = []
start = time.perf_counter()
for folder in ('src', 'tests'):
    for path in sorted((ROOT / folder).rglob('*.py')):
        rel = path.relative_to(ROOT).as_posix()
        for row in namespace['scan_text'](path.read_text(encoding='utf-8-sig'), rel, repository_root=ROOT):
            assert len(row) == 7, row
            rows.append(dict(zip(('path', 'line', 'function', 'rule', 'source', 'node', 'context'), row)))
payload = json.dumps(rows, ensure_ascii=False, indent=2)
(HERE / 'raw_actual_fingerprints.json').write_text(payload, encoding='utf-8')
result = {'rows': len(rows), 'distinct': len({tuple(r[k] for k in ('path','function','rule','node')) for r in rows}),
          'wall_seconds': time.perf_counter() - start, 'policy_writes': 0,
          'payload_sha256': hashlib.sha256(payload.encode()).hexdigest()}
(HERE / 'raw_actual_fingerprints_summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
