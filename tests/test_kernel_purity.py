"""Kernel boundary gates use independent Python AST parsing, never geometry.

Mutation teeth modify the source copy that is parsed by the real audit; no
post-audit fake result is appended. They identify the relevant failing rule.
"""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from h1_kernel_purity import DOMAIN_WORDS, audit_kernel, words


def test_kernel_domain_purity():
    assert audit_kernel(ROOT / "src") == []


@pytest.mark.parametrize("injection,expected", [
    ("from eab.adapters import bdda2d\n", "forbidden import path"),
    ("mtype = 0\n", "domain token mtype"),
])
def test_kernel_purity_rejects_actual_source_mutations(tmp_path, injection, expected):
    copied = tmp_path / "src"
    shutil.copytree(ROOT / "src" / "eab", copied / "eab", ignore=shutil.ignore_patterns("__pycache__"))
    assert audit_kernel(copied) == []
    path = copied / "eab" / "kernel2d" / "geom.py"
    with path.open("a", encoding="utf-8", newline="") as stream:
        stream.write("\n" + injection)
    failures = audit_kernel(copied)
    assert any("eab/kernel2d/geom.py" in line and expected in line for line in failures), failures
    checked = subprocess.run([sys.executable, str(ROOT / "tools" / "h1_kernel_purity.py"),
                              "--source-root", str(copied)],
                             capture_output=True, text=True, encoding="utf-8")
    assert checked.returncode == 1 and expected in checked.stdout, (checked.stdout, checked.stderr)


def test_kernel_purity_follows_transitive_imports(tmp_path):
    copied = tmp_path / "src"
    shutil.copytree(ROOT / "src" / "eab", copied / "eab", ignore=shutil.ignore_patterns("__pycache__"))
    (copied / "eab" / "bridge.py").write_text("from eab.readers import bdda_geom\n", encoding="utf-8")
    path = copied / "eab" / "kernel2d" / "geom.py"
    with path.open("a", encoding="utf-8", newline="") as stream:
        stream.write("\nfrom eab import bridge\n")
    failures = audit_kernel(copied)
    assert any("eab.kernel2d.geom -> eab.bridge -> eab.readers" in line for line in failures), failures


def test_kernel_domain_vocabulary_covers_required_tokens_and_spelling():
    assert set("dda bdda tia tf rock joint mtype df04 df05 df06 df07".split()) <= DOMAIN_WORDS
    for token in ("DDAAnchoredMotion", "BDDA3D_MODE", "rock_joint", "mType", "df05", "岩石", "节理"):
        assert DOMAIN_WORDS & words(token), token


def test_only_real_docstrings_are_exempt(tmp_path):
    package = tmp_path / "eab" / "kernel2d"
    package.mkdir(parents=True)
    path = package / "example.py"
    path.write_text('"""DDA adapter example."""\n\ndef example():\n    """DDA adapter example."""\n    return 0\n', encoding="utf-8")
    assert audit_kernel(tmp_path) == []
    with path.open("a", encoding="utf-8", newline="") as stream:
        stream.write('\nLABEL = "DDA"\n')
    assert any("domain token dda" in line for line in audit_kernel(tmp_path))
