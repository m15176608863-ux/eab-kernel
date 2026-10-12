"""把 docs/canon_map.md 的 file:line 指针统一改写成"带函数名、行号 = 当前定义行"的形式，以便指针门逐条自动核。

带名指针（`f.py:N name`、链式 `:N name`）：N 改成 name 的当前定义行。
无名指针（`f.py:N`、`f.py:N-M`、`f.py:N/M/K`）：git blame 出 canon_map 那一行最后写入的提交 C，在 C 版本的 f.py 里找 N 所在的
最内层 def/class，改写成 `f.py:当前定义行 name`（段落指针在后面括注"段内"）；找不到外围 def（模块级段落）的保留原样并报告。
只改 canon_map；打印每处改动，便于人工复核。门：tests/test_doc_pointers.py。

用法：python tools/fix_canon_ptrs.py            （只看）
      python tools/fix_canon_ptrs.py --apply    （写回）"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs' / 'canon_map.md'
APPLY = '--apply' in sys.argv


def git(*a):
    return subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True, encoding='utf-8').stdout


FILES = {}
for p in sorted((ROOT / 'src').rglob('*.py')) + sorted((ROOT / 'tools').rglob('*.py')) + sorted((ROOT / 'tests').rglob('*.py')):
    FILES.setdefault(p.name, []).append(p.relative_to(ROOT).as_posix())


def resolve(f):
    if '/' in f:
        hits = [q for qs in FILES.values() for q in qs if q.endswith(f)]
    else:
        hits = FILES.get(f, [])
    src = [h for h in hits if h.startswith('src/')]
    hits = src or hits
    return hits[0] if len(hits) == 1 else None


DEF = re.compile(r'^(\s*)(?:async\s+)?(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)')


def defs(text):
    out = []
    for i, l in enumerate(text.splitlines(), 1):
        m = DEF.match(l)
        if m:
            out.append((i, len(m.group(1)), m.group(3)))
    return out


def enclosing(text, ln):
    lines = text.splitlines()
    best = None
    for i, ind, name in defs(text):
        if i > ln:
            break
        # 这个 def 的体是否覆盖 ln：之后第一个缩进 ≤ ind 的非空行之前
        end = len(lines)
        for j in range(i, len(lines)):
            s = lines[j]
            if s.strip() and (len(s) - len(s.lstrip())) <= ind and j + 1 > i:
                end = j
                break
        if i <= ln <= end:
            best = (i, ind, name)
    return best


def cur_def_line(path, name):
    text = (ROOT / path).read_text(encoding='utf-8')
    hits = [i for i, _, n in defs(text) if n == name]
    return hits[0] if len(hits) == 1 else (hits[0] if hits else None)


doc = DOC.read_text(encoding='utf-8')
lines = doc.split('\n')
blame_cache = {}


def commit_of(lineno):
    if lineno not in blame_cache:
        out = git('blame', '-L', f'{lineno},{lineno}', '--porcelain', 'HEAD', '--', 'docs/canon_map.md')
        blame_cache[lineno] = out.split()[0] if out else 'HEAD'
    return blame_cache[lineno]


PTR = re.compile(r'`([A-Za-z0-9_./]*\.py)?:(\d+)((?:[-/]\d+)*)(?:\s+([A-Za-z_][A-Za-z0-9_]*))?`')
report = []
unresolved = []
for li, line in enumerate(lines, 1):
    cur_file = None

    def fix(m):
        global cur_file
        f, ln, tail, name = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        if f:
            cur_file = f
        if cur_file is None:
            unresolved.append((li, m.group(0), 'no file'))
            return m.group(0)
        path = resolve(cur_file)
        if path is None:
            unresolved.append((li, m.group(0), 'ambiguous/unknown file'))
            return m.group(0)
        shown = m.group(1) or ''
        if name:
            nl = cur_def_line(path, name)
            if nl is None:
                unresolved.append((li, m.group(0), f'no def {name} in {path}'))
                return m.group(0)
            new = f'`{shown}:{nl}{"" if not tail else ""} {name}`' if tail == '' else f'`{shown}:{nl} {name}`'
        else:
            c = commit_of(li)
            old = git('show', f'{c}:{path}') or (ROOT / path).read_text(encoding='utf-8')
            enc = enclosing(old, ln)
            if enc is None:
                unresolved.append((li, m.group(0), f'module-level in {path}@{c[:7]}'))
                return m.group(0)
            nl = cur_def_line(path, enc[2])
            if nl is None:
                unresolved.append((li, m.group(0), f'def {enc[2]} gone from HEAD'))
                return m.group(0)
            seg = '' if (not tail and ln == enc[0]) else '（段内）'
            new = f'`{shown}:{nl} {enc[2]}`{seg}'
        if new != m.group(0):
            report.append((li, m.group(0), new))
        return new
    lines[li - 1] = PTR.sub(fix, line)

for r in report:
    print('FIX', *r)
for u in unresolved:
    print('KEEP', *u)
print(len(report), 'rewritten;', len(unresolved), 'kept')
if APPLY:
    DOC.write_text('\n'.join(lines), encoding='utf-8', newline='')
    print('applied')
