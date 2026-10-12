"""Finite source bindings and binary-format transfer, without site waivers.

The oracle is Python binding and format/type semantics, not an eab geometry
helper. Negative source probes reach the gate itself, not a mocked diagnostic.
"""
import ast
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("r12fixb_structure_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
flow = gate._subset._flow


@pytest.mark.parametrize("fmt,kind", [(">Q", "exact"), (">d", "float"), ("<2h", "exact"), ("!3xI", "exact")])
def test_literal_unpack_has_finite_result_types(fmt, kind):
    source = f"import struct\ndef read(data: bytes):\n    return struct.unpack({fmt!r}, data)\n"
    analysis = flow.analyze(source, "src/eab/structure_probe.py")
    call = next(node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call))
    assert analysis.call_proved(call)
    assert analysis.return_kind(call) == kind


def test_ieee_binary64_bits_inspection_is_not_numeric_callable_dispatch():
    source = ("import struct\ndef bits(q: float):\n"
              "    return struct.unpack('>Q', struct.pack('>d', q))[0]\n")
    assert gate.scan_text(source, "src/eab/structure_probe.py") == []


@pytest.mark.parametrize("arguments", ["", "7", "7, 2", "start=7, step=2"])
def test_count_of_ints_yields_exact_integers(arguments):
    source = f"from itertools import count\ndef safe():\n    return next(count({arguments})) + 3\n"
    analysis = flow.analyze(source, "src/eab/structure_probe.py")
    node = next(node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.BinOp))
    assert analysis.return_kind(node) == "exact"
    assert not analysis.may_round(node)


@pytest.mark.parametrize("expression", ["count(0.0)", "count(0, 0.1)", "struct.unpack(fmt, b'x')", "struct.pack('@d', 1.0)"])
def test_unmodeled_iterator_or_binary_format_remains_unproved(expression):
    source = f"import struct\nfrom itertools import count\ndef bad(fmt: str):\n    return {expression}\n"
    analysis = flow.analyze(source, "src/eab/structure_probe.py")
    call = next(node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call))
    assert not analysis.call_proved(call)


@pytest.mark.parametrize("fmt,annotation,expression", [(">d", "Fraction", "q"), (">f", "float", "q"), (">d", "float", "q*q")])
def test_binary_pack_cannot_erase_rounding_before_a_root(fmt, annotation, expression):
    source = ("import struct\nfrom fractions import Fraction\n"
              "from eab.construction import sqrt_rational\n"
              f"def bad(q: {annotation}):\n"
              f"    encoded = struct.pack({fmt!r}, {expression})\n"
              f"    decoded = struct.unpack({fmt!r}, encoded)[0]\n"
              "    return sqrt_rational(Fraction(decoded))\n")
    issues = gate.scan_text(source, "src/eab/structure_probe.py")
    assert any(item[3] in {"closed-rounded-construction", "closed-unproved-arithmetic", "closed-rounded-call"} for item in issues), issues


@pytest.fixture
def test_source_project(tmp_path):
    package = tmp_path / "src" / "example"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "values.py").write_text(
        "OPTIMAL = 'optimal'\n_FLIP = {'VF': 'FV'}\n"
        "def exact(q: int):\n    return q*q\n"
        "def unknown(q):\n    return q.callback(q)\n", encoding="utf-8")
    return tmp_path


def test_imported_source_constants_are_data_not_callable_values(test_source_project):
    source = "from example.values import OPTIMAL, _FLIP\ndef use():\n    return OPTIMAL, _FLIP['VF']\n"
    analysis = flow.analyze(source, "src/example/probe.py", test_source_project)
    references = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Name) and n.id in {"OPTIMAL", "_FLIP"}]
    assert len(references) == 2
    assert all(analysis.reference_proved(node) for node in references)
    assert all(analysis.return_kind(node) == "data" for node in references)


def test_direct_source_module_alias_resolves_without_callable_dispatch(test_source_project):
    source = "from example import values\ndef safe(q: int):\n    c = values\n    return c.exact(q)\n"
    analysis = flow.analyze(source, "src/example/probe.py", test_source_project)
    call = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call))
    assert analysis.call_proved(call)
    assert analysis.return_kind(call) == "exact"


@pytest.mark.parametrize("body", [
    "c = values\n    c.exact = q\n    return values.exact(q)",
    "c = values\n    values.exact = q\n    return c.exact(q)",
    "c = values\n    c = q\n    return c.exact(q)",
    "c = [values][0]\n    return c.exact(q)",
    "c = values\n    return c.unknown(q)",
])
def test_module_alias_never_masks_writes_rebinding_dynamic_or_unproved_callee(test_source_project, body):
    source = "from example import values\ndef bad(q):\n    " + body + "\n"
    analysis = flow.analyze(source, "src/example/probe.py", test_source_project)
    call = next(n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call))
    assert not analysis.call_proved(call)
