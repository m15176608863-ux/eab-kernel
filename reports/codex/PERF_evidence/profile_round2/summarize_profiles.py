from pathlib import Path
import json
import pstats

BASE = Path(__file__).resolve().parent
summary = {}
for path in sorted(BASE.glob('*.pstats')):
    stats = pstats.Stats(str(path))
    rows = []
    for (file, line, name), (primitive, calls, own, cumulative, _) in stats.stats.items():
        rows.append(dict(file=file, line=line, function=name, primitive_calls=primitive,
                         calls=calls, self_seconds=own, cumulative_seconds=cumulative))
    project = [r for r in rows if 'eab-wt' in r['file']]
    production = [r for r in project if '\\src\\eab\\' in r['file']]
    oracle = [r for r in project if '\\tests\\e5a_' in r['file'] or '\\tests\\e5b_' in r['file']]
    sort = lambda rows: sorted(rows, key=lambda r: -r['cumulative_seconds'])[:20]
    result = dict(total_seconds=stats.total_tt,
                  top20_self=sorted(rows, key=lambda r: -r['self_seconds'])[:20],
                  project_top20_cumulative=sort(project),
                  production_top20_cumulative=sort(production),
                  oracle_top20_cumulative=sort(oracle))
    path.with_suffix('.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    summary[path.stem] = dict(total_seconds=stats.total_tt,
                             production_top5=sort(production)[:5], oracle_top5=sort(oracle)[:5])
    print(path.stem, 'total', round(stats.total_tt, 3),
          'oracle peak', [(r['function'], round(r['cumulative_seconds'], 3)) for r in sort(oracle)[:3]])
(BASE / 'profile_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
