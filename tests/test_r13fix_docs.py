"""G6M-03: the current canon summary must describe the live, local policy.

This is a documentation consistency gate, not a mathematical correctness gate.
"""
from pathlib import Path

import pytest


def test_canon_current_static_summary_matches_r12fixb_local_policy():
    text = (Path(__file__).resolve().parents[1] / "docs/canon_map.md").read_text(encoding="utf-8")
    summary = text.splitlines()[2]
    assert "全 src/tests/tools 原字节依赖图钉住" not in summary, "obsolete whole-repository pin in current canon summary"
    assert "自动算术证明仅限纯整数字面量" not in summary, "obsolete integer-literal-only proof in current canon summary"
    assert "局部" in summary and "Fraction" in summary, "current local AST/source and Fraction flow contract"
    assert "辅助" in summary and "不是安全保证" in summary, "static checker must not be advertised as a safety guarantee"


def test_canon_gate_rejects_reintroduced_obsolete_summary(monkeypatch):
    original = Path.read_text
    def obsolete(path, *args, **kwargs):
        text = original(path, *args, **kwargs)
        if path.name == "canon_map.md":
            lines = text.splitlines()
            lines[2] = "完整模块 AST／上下文及全 src/tests/tools 原字节依赖图钉住；自动算术证明仅限纯整数字面量"
            return "\n".join(lines)
        return text
    monkeypatch.setattr(Path, "read_text", obsolete)
    with pytest.raises(AssertionError, match="obsolete whole-repository pin"):
        test_canon_current_static_summary_matches_r12fixb_local_policy()
