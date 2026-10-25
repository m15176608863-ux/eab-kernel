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
from h1_kernel_purity import DOMAIN_WORDS, KERNEL_ROOTS, LEXICAL_ALLOWLIST, audit_kernel, words


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


def test_parent_package_imports_are_checked_for_every_kernel_module(tmp_path):
    copied = tmp_path / "src"
    shutil.copytree(ROOT / "src" / "eab", copied / "eab", ignore=shutil.ignore_patterns("__pycache__"))
    expected = {p.relative_to(copied).as_posix() for p in (copied / "eab").rglob("*.py")
                if p.relative_to(copied / "eab").parts[0].removesuffix(".py") in KERNEL_ROOTS}
    # Original 53 plus exact rigid cage certificate module se2_cage.
    assert len(expected) == 54 and "eab/predicates.py" in expected
    path = copied / "eab" / "contact_record.py"
    with path.open("a", encoding="utf-8", newline="") as stream:
        stream.write("\nfrom .adapters import bdda2d\n")
    failures = audit_kernel(copied)
    reached = {line.split(":", 1)[0] for line in failures if "forbidden import path" in line}
    assert reached == expected, (sorted(expected - reached), failures)


@pytest.mark.parametrize("filename,injection,expected", [
    ("probe.py", "joints = 1\n", "domain token joint"),
    ("probe.py", "rocks = 1\n", "domain token rock"),
    ("probe.py", "m4 = 1\nm6 = 2\n", "domain token m4"),
    ("probe.py", "tuple7 = 1\n", "domain token tuple7"),
    ("probe.py", "legacy_slot = 1\n", "domain token legacy,slot"),
    ("probe.py", "zsto = 1\n", "domain token zsto"),
    ("probe.py", "lock_second = 1\n", "domain token lock_second"),
    ("probe.py", "bolt_force = 1\n", "domain token bolt"),
    ("probe.py", "out_csv_z = 1\n", "domain token csv"),
    ("probe.py", "m_type = 1\n", "domain token mtype"),
    ("probe.py", "ddamotion = 1\n", "domain token dda"),
    ("probe.py", "bddacover = 1\n", "domain token bdda,dda"),
    ("probe.py", "tiaprism = 1\n", "domain token tia"),
    ("probe.py", "tia_block = 1\n", "domain token tia"),
    ("probe.py", "class TiaAssembly:\n    pass\n", "domain token tia"),
    ("probe.py", "differentiability_tia = 1\n", "domain token tia"),
    ("probe.py", "csvexport = 1\n", "domain token csv"),
    ("probe.py", "zstorecord = 1\n", "domain token zsto"),
    ("probe.py", "df06state = 1\n", "domain token df06"),
    ("probe.py", "payload = b'df06'\n", "domain token df06"),
    ("probe.py", "label = '岩体围岩断层岩爆'\n", "domain token"),
    ("probe.py", "def probe(value):\n    match value:\n        case complex(mtype=0):\n            return 1\n", "domain token mtype"),
    ("dda_probe.py", "value = 1\n", "domain module token dda"),
    ("tia_prism/probe.py", "value = 1\n", "domain module token tia"),
])
def test_domain_lexical_classes_reject_real_source_injections(tmp_path, filename, injection, expected):
    path = tmp_path / "eab" / "kernel2d" / filename
    path.parent.mkdir(parents=True)
    path.write_text(injection, encoding="utf-8", newline="")
    failures = audit_kernel(tmp_path)
    assert any(path.relative_to(tmp_path).as_posix() in line and expected in line for line in failures), failures


@pytest.mark.parametrize("filename", ["contact_record.py", "numeric_decode.py", "__init__.py"])
def test_shared_contract_modules_are_lexically_scanned(tmp_path, filename):
    package = tmp_path / "eab"
    package.mkdir()
    (package / filename).write_text("mapping = {'mtype': b'df06'}\n", encoding="utf-8")
    failures = audit_kernel(tmp_path)
    assert any("domain token mtype" in line for line in failures), failures
    assert any("domain token df06" in line for line in failures), failures


def test_contract_field_allowlist_is_site_specific_and_documented(tmp_path):
    package = tmp_path / "eab"
    package.mkdir()
    path = package / "contact_record.py"
    text = "class ContactRecord:\n    joint_material: int = None\n_INTEGER_FIELDS = {'joint_material'}\n"
    path.write_text(text, encoding="utf-8")
    assert LEXICAL_ALLOWLIST[("eab.contact_record", "joint_material")]
    assert audit_kernel(tmp_path) == []
    path.write_text(text + "joint_material = {'mtype': 0}\n", encoding="utf-8")
    failures = audit_kernel(tmp_path)
    assert any("domain token joint" in line for line in failures), failures


def test_language_slots_exception_is_not_a_slot_variable_exemption(tmp_path):
    package = tmp_path / "eab" / "kernel2d"
    package.mkdir(parents=True)
    path = package / "probe.py"
    text = "from dataclasses import dataclass\n@dataclass(slots=True)\nclass Point:\n    x: int\n"
    path.write_text(text, encoding="utf-8")
    assert LEXICAL_ALLOWLIST[("*", "slots")]
    assert audit_kernel(tmp_path) == []
    path.write_text(text + "slots = 2\n", encoding="utf-8")
    assert any("domain token slot" in line for line in audit_kernel(tmp_path))


@pytest.mark.parametrize("injection", [
    "import importlib\nvalue = importlib.import_module('eab.' + 'adapters')\n",
    "import sys\nvalue = sys.modules['eab.readers']\n",
])
def test_static_dynamic_import_spellings_reach_forbidden_packages(tmp_path, injection):
    package = tmp_path / "eab" / "kernel2d"
    package.mkdir(parents=True)
    (package / "probe.py").write_text(injection, encoding="utf-8")
    assert any("forbidden import path" in line for line in audit_kernel(tmp_path))
