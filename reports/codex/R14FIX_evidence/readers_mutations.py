"""Rerun internal N03/reader mutations without touching source-file bytes.
Run from repo root: python -X utf8 reports/codex/R14FIX_evidence/readers_mutations.py
"""
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
import pytest
from eab import contact_record as cr
from eab.adapters import bdda2d as adapter
from eab.readers import bdda3d, numeric_decode as decoder
from fractions import Fraction as F

spec = importlib.util.spec_from_file_location("r14_reader_gates", ROOT / "tests/test_r14_readers.py")
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)
paths = [ROOT / p for p in ("src/eab/contact_record.py", "src/eab/readers/bdda3d.py",
                            "src/eab/readers/numeric_decode.py", "src/eab/adapters/bdda2d.py")]
before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
tmp = ROOT / "reports/codex/R14FIX_evidence/tmp/readers_mutations"
tmp.mkdir(parents=True, exist_ok=True)
results = []


def check(name, namespace_module, owner, attr, old, new, gate_name, call, expected="DID NOT RAISE"):
    original = getattr(owner, attr)
    source = textwrap.dedent(inspect.getsource(original))
    assert old in source, name
    namespace = dict(vars(namespace_module))
    exec(compile(source.replace(old, new), f"<R14 mutation {name}>", "exec"), namespace)
    setattr(owner, attr, namespace[original.__name__])
    try:
        call()
    except (pytest.fail.Exception, AssertionError) as exc:
        assert expected in str(exc), str(exc)
        results.append(dict(mutation=name, gate=gate_name, assertion=str(exc), caught=True))
    else:
        raise AssertionError(f"mutant escaped: {name}")
    finally:
        setattr(owner, attr, original)


check("JSON early float", decoder, bdda3d, "loads_exact", "parse_float=_decimal", "parse_float=float",
      "test_real_bdda3d_json_literal_is_checked_before_decoding[1e-400-area]",
      lambda: gates.test_real_bdda3d_json_literal_is_checked_before_decoding(tmp, "area", "1e-400"))
check("direct Fraction unchecked float", cr, cr, "_decode",
      'scalar_rational(x, quantity=f"{name}[{i}]")', "float(x)",
      "test_contact_dict_rational_rejects_nonzero_zero_or_infinity[value0-normal]",
      lambda: gates.test_contact_dict_rational_rejects_nonzero_zero_or_infinity("normal", F(1, 2**2000)))
check("identity integrality guard removed", decoder, cr, "integer",
      "if q.denominator != 1:", "if False:",
      "test_fractional_feature_identifiers_are_rejected_not_truncated[value1]",
      lambda: gates.test_fractional_feature_identifiers_are_rejected_not_truncated(F(1, 2**2000)))
check("window output-range guard replaced by float", adapter, adapter.Bdda2DWindow, "__post_init__",
      'scalar_rational(q, quantity=f"bdda2d.window.{name}")', "float(q)",
      "test_adapter_window_checks_exact_inputs_before_libm_or_float[value0-d0]",
      lambda: gates.test_adapter_window_checks_exact_inputs_before_libm_or_float("d0", F(1, 2**2000)))
check("signed zero guard removed", decoder, cr, "scalar_rational",
      "return value if isinstance(value, float) and value == 0.0 else result", "return result",
      "test_reader_preserves_signed_float_zero_through_json_roundtrip[dict-normal]",
      lambda: gates.test_reader_preserves_signed_float_zero_through_json_roundtrip("normal", "dict"),
      expected="reader must preserve signed binary64 zero")
check("reference evidence integer guard bypassed", bdda3d, bdda3d, "record_from_entrance",
      'extra[k] = [list(r) for r in refs] if k == "refs" else c[k]', 'extra[k] = c[k]',
      "test_bdda3d_reference_evidence_keeps_checked_integer_identity[json]",
      lambda: gates.test_bdda3d_reference_evidence_keeps_checked_integer_identity("json", tmp),
      expected="reference evidence must preserve exact integer identity")
after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert before == after
payload = dict(mutations=results, source_bytes_restored=before == after, sha256=after)
output = ROOT / "reports/codex/R14FIX_evidence/readers_mutations.json"
with output.open("w", encoding="utf-8", newline="") as stream:
    stream.write(json.dumps(payload, indent=2)+"\n")
print(f"{len(results)} internal mutations caught; source bytes restored; UTF-8 JSON: {output}")
