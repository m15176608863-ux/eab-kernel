"""溯源说明里的 Windows 路径不许被转义吃掉（G6 第五轮 minor，2026-10-10）。

699f481 把 `D:\\3-b-dda\\src\\bdda3d\\cases.py` 写进了非 raw f-string：`\\3` 成了 chr(3)、`\\b` 成了退格，`\\s`/`\\c` 触发
SyntaxWarning。下次重跑 ingest_bdda3d.py 时 upsert_provenance 会把带控制字符的路径写进 PROVENANCE.json，溯源门照绿。
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


@pytest.mark.parametrize("name", ["cb2_locked", "cb2_sliding", "cb_bond"])
def test_source_note_keeps_the_sibling_path_readable(name):
    with warnings.catch_warnings():
        warnings.simplefilter("error", SyntaxWarning)
        import importlib
        import ingest_bdda3d
        importlib.reload(ingest_bdda3d)
    note = ingest_bdda3d.source_note(name)
    assert not any(ord(ch) < 32 for ch in note), [hex(ord(ch)) for ch in note if ord(ch) < 32]
    assert "3-b-dda\\src\\bdda3d\\cases.py:112-128" in note
