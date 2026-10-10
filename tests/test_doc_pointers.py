"""docs/canon_map.md 的代码指针门（G6 第四轮建议、第五轮复核仍缺：三次人工校正之后 40 处带名指针里 29 处又过期）。

规则：canon_map 里每个反引号代码指针都必须写成 `file.py:N name`（或链式 `:N name`，沿用前一个文件），N 等于 name 在该文件
**当前**的定义行；不许出现不带函数名的 `file.py:N` / `file.py:N-M`（无法自动核，过期了也没人知道）。模块文档里的段落用
"`file.py` 模块文档「节名」"指，不写行号。改了代码挪动了定义行，这道门会红在具体的那个指针上——跑
`python tools/fix_canon_ptrs.py --apply` 或手改即可。
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "canon_map.md"
PTR = re.compile(r"`([A-Za-z0-9_./]*\.py)?:(\d+)((?:[-/]\d+)*)(?:\s+([A-Za-z_][A-Za-z0-9_]*))?`")
DEF = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")


def _files():
    out = {}
    for p in sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "tools").rglob("*.py")) + sorted((ROOT / "tests").rglob("*.py")):
        out.setdefault(p.name, []).append(p)
    return out


def _resolve(files, f):
    if "/" in f:
        hits = [p for ps in files.values() for p in ps if p.as_posix().endswith(f)]
    else:
        hits = files.get(f, [])
    src = [p for p in hits if (ROOT / "src") in p.parents]
    hits = src or hits
    return hits[0] if len(hits) == 1 else None


def test_every_code_pointer_in_canon_map_names_a_function_at_its_current_line():
    files = _files()
    bad, unnamed, n = [], [], 0
    for li, line in enumerate(DOC.read_text(encoding="utf-8").splitlines(), 1):
        cur = None
        for m in PTR.finditer(line):
            f, ln, tail, name = m.group(1), int(m.group(2)), m.group(3), m.group(4)
            cur = f or cur
            if cur is None:
                continue
            n += 1
            if not name or tail:
                unnamed.append((li, m.group(0)))
                continue
            path = _resolve(files, cur)
            assert path is not None, (li, m.group(0), "file not found or ambiguous")
            lines = path.read_text(encoding="utf-8").splitlines()
            got = [i for i, l in enumerate(lines, 1) if (mm := DEF.match(l)) and mm.group(1) == name]
            if ln not in got:
                bad.append((li, m.group(0), got))
    assert n >= 60, n                     # 门不许退化成"没有指针"
    assert not unnamed, unnamed
    assert not bad, bad
