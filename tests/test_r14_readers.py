"""R14 N03: exact decimal/rational boundaries before reader float coercion.

Oracle: Fraction token values and the mathematical binary64 RN zero/overflow
cells; no production geometry, parsing helper, or construction is the oracle.
"""
from fractions import Fraction as F
import json
import math
import inspect
import textwrap

import pytest

from eab.contact_record import ContactRecord, records_from_json, records_to_json
from eab.numeric_domain import ConstructionDomainError
from eab.readers import bdda3d


BASE = dict(source="r14", step=0, contact_index=0, block_a=1, block_b=2)
VECTORS = ("ref_points", "normal", "params", "shear", "slip_ref")
SCALARS = ("length_or_area", "gap", "normal_force", "gap_ref", "lock_position")
TOKENS = ("1e-400", "-1e-400", "1e400", "-1e400")


def _value(field, value):
    if field == "ref_points":
        return [[value, 0]]
    if field in VECTORS:
        return [value, 0]
    return value


def _record_literal(field, token):
    d = dict(BASE, **{field: _value(field, "TOKEN")})
    return json.dumps([d]).replace('"TOKEN"', token)


@pytest.mark.parametrize("field", VECTORS + SCALARS)
@pytest.mark.parametrize("token", TOKENS)
def test_contact_json_literal_rejects_nonzero_zero_or_infinity(field, token):
    assert F(token) != 0  # Literal is finite and nonzero before decoding.
    with pytest.raises(ConstructionDomainError):
        records_from_json(_record_literal(field, token))


@pytest.mark.parametrize("field", VECTORS + SCALARS)
@pytest.mark.parametrize("value", [F(1, 2**2000), -F(1, 2**2000), F(2**2000)])
def test_contact_dict_rational_rejects_nonzero_zero_or_infinity(field, value):
    with pytest.raises(ConstructionDomainError, match=field):
        ContactRecord.from_dict(dict(BASE, **{field: _value(field, value)}))


@pytest.mark.parametrize("field", ["area", "t1", "t2", "o3t", "slip_ref", "extra_probe"])
@pytest.mark.parametrize("token", TOKENS)
def test_real_bdda3d_json_literal_is_checked_before_decoding(tmp_path, field, token):
    c = {"bi": 1, "bj": 2, "etype": "np", "t1": 0, "t2": 0}
    c[field] = ["TOKEN", 0, 0] if field == "slip_ref" else "TOKEN"
    path = tmp_path / "bdda3d.json"
    path.write_text(json.dumps({"entrances": [c]}).replace('"TOKEN"', token), encoding="utf-8")
    with pytest.raises(ConstructionDomainError):
        bdda3d.load_records(path)


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_contact_json_nonfinite_constants_are_not_a_numeric_escape(token):
    with pytest.raises(ConstructionDomainError):
        records_from_json(_record_literal("gap", token))


@pytest.mark.parametrize("token", ["5e-324", "1e-200", "1e200", "1.7976931348623157e308", "0.1", "-0.125"])
def test_reader_keeps_full_binary64_output_domain_not_d400(token):
    rec, = records_from_json(_record_literal("normal", token))
    expected = float(F(token))
    assert rec.normal == (expected, 0.0)
    assert math.isfinite(rec.normal[0]) and rec.normal[0] != 0
    assert records_from_json(records_to_json([rec])) == [rec]


@pytest.mark.parametrize("value", [F(1, 2), F(1, 2**2000), F(2**54 + 1, 2)])
def test_fractional_feature_identifiers_are_rejected_not_truncated(value):
    with pytest.raises(ConstructionDomainError, match="feature_a.index"):
        ContactRecord.from_dict(dict(BASE, feature_a={"block": 1, "kind": "vertex", "index": value}))


def test_large_exact_integer_identity_is_never_rounded_to_binary64():
    identifier = 2**2000 + 1
    rec = ContactRecord.from_dict(dict(BASE, feature_a={"block": 1, "kind": "vertex", "index": identifier}))
    assert rec.feature_a.index == identifier
    assert records_from_json(records_to_json([rec])) == [rec]


@pytest.mark.parametrize("field", ["d0", "seg_tol", "fit_tol", "h1_degrees"])
@pytest.mark.parametrize("value", [F(1, 2**2000), F(2**2000)])
def test_adapter_window_checks_exact_inputs_before_libm_or_float(field, value):
    from eab.adapters.bdda2d import Bdda2DWindow
    kwargs = dict(step=1, d0=1, h1_degrees=3, seg_tol=1, fit_tol=1)
    kwargs[field] = value
    with pytest.raises((ConstructionDomainError, ValueError)):
        Bdda2DWindow(**kwargs)


def test_decimal_integer_identity_does_not_round_before_integer_check():
    text = json.dumps([dict(BASE, feature_a={"block": 1, "kind": "vertex", "index": "TOKEN"})])
    text = text.replace('"TOKEN"', "18014398509481985.0")
    rec, = records_from_json(text)
    assert rec.feature_a.index == 2**54 + 1


@pytest.mark.parametrize("field", ["bi", "bj", "m0init", "m0_0"])
def test_bdda3d_direct_fractional_identity_is_rejected_not_truncated(field):
    c = dict(bi=1, bj=2, m0init=0, m0_0=0)
    c[field] = F(1, 2**2000)
    with pytest.raises(ConstructionDomainError, match=field):
        bdda3d.record_from_entrance(c)


@pytest.mark.parametrize("field", ["step", "contact_index", "block_a", "block_b", "raw_mode", "raw_cover"])
def test_contact_integer_fields_do_not_accept_fractional_ids(field):
    with pytest.raises(ConstructionDomainError, match=field):
        ContactRecord.from_dict(dict(BASE, **{field: F(3, 2)}))


@pytest.mark.parametrize("field", ["step", "index"])
def test_bdda3d_direct_step_and_index_are_exact_integers(field):
    with pytest.raises(ConstructionDomainError, match=field):
        bdda3d.record_from_entrance(dict(bi=1, bj=2), **{field: F(3, 2)})


@pytest.mark.parametrize("sign", [-1, 1])
def test_reader_output_domain_has_open_rn_zero_and_infinity_boundaries(sign):
    lo = F(1, 2**1075)
    hi = F(2**1024 - 2**970)
    for q in (lo, hi):
        with pytest.raises(ConstructionDomainError):
            ContactRecord.from_dict(dict(BASE, gap=sign*q))
    low = ContactRecord.from_dict(dict(BASE, gap=sign*(lo + lo/2))).gap
    high = ContactRecord.from_dict(dict(BASE, gap=sign*(hi - 2**970))).gap
    assert F(low) == sign*F(1, 2**1074)
    assert F(high) == sign*F(2**1024 - 2**971)


@pytest.mark.parametrize("field", VECTORS + SCALARS + ("extra",))
@pytest.mark.parametrize("api", ["dict", "json"])
def test_reader_preserves_signed_float_zero_through_json_roundtrip(field, api):
    value = {"probe": -0.0} if field == "extra" else _value(field, -0.0)
    payload = dict(BASE, **{field: value})
    text = json.dumps([payload])
    if api == "dict":
        rec = ContactRecord.from_dict(payload)
    else:
        rec, = records_from_json(text)
    actual = getattr(rec, field)
    if field == "extra": actual = actual["probe"]
    elif field == "ref_points": actual = actual[0][0]
    elif field in VECTORS: actual = actual[0]
    assert actual == 0.0 and math.copysign(1.0, actual) == -1.0, "reader must preserve signed binary64 zero"
    serialized = records_to_json([rec])
    assert records_to_json(records_from_json(serialized)) == serialized, "signed-zero JSON bytes must roundtrip"


def test_integer_negative_zero_literal_retains_existing_json_integer_semantics():
    rec, = records_from_json(json.dumps([dict(BASE, step="TOKEN")]).replace('"TOKEN"', "-0"))
    assert rec.step == 0 and type(rec.step) is int


@pytest.mark.parametrize("api", ["json", "dict"])
def test_bdda3d_reference_evidence_keeps_checked_integer_identity(api, tmp_path):
    identifier = 2**54 + 1 if api == "json" else 2**2000 + 1
    ref = "TOKEN" if api == "json" else F(identifier)
    entrance = dict(etype="np", bi=1, bj=2, refs=[[1, 0], [2, ref], [2, 2], [2, 3]])
    if api == "json":
        path = tmp_path / "identity.json"
        path.write_text(json.dumps({"entrances": [entrance]}).replace('"TOKEN"', str(identifier)+".0"), encoding="utf-8")
        rec, = bdda3d.load_records(path)
    else:
        rec = bdda3d.record_from_entrance(entrance)
    assert rec.extra["refs"][1][1] == identifier, "reference evidence must preserve exact integer identity"
    assert type(rec.extra["refs"][1][1]) is int
    assert identifier in rec.feature_b.verts


def _internal_mutant(module, function, old, new):
    source = textwrap.dedent(inspect.getsource(function))
    assert old in source
    namespace = dict(vars(module))
    exec(compile(source.replace(old, new), "<R14 reader internal mutation>", "exec"), namespace)
    return namespace[function.__name__]


def test_n03_json_guard_mutation_is_caught_inside_real_decoder(monkeypatch, tmp_path):
    from eab import numeric_decode as decoder
    mutant = _internal_mutant(decoder, decoder.loads, "parse_float=_decimal", "parse_float=float")
    monkeypatch.setattr(bdda3d, "loads_exact", mutant)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_real_bdda3d_json_literal_is_checked_before_decoding(tmp_path, "area", "1e-400")


def test_n03_direct_fraction_guard_mutation_is_caught_inside_decode(monkeypatch):
    from eab import contact_record as cr
    old = 'scalar_rational(x, quantity=f"{name}[{i}]")'
    monkeypatch.setattr(cr, "_decode", _internal_mutant(cr, cr._decode, old, "float(x)"))
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_contact_dict_rational_rejects_nonzero_zero_or_infinity("normal", F(1, 2**2000))


def test_identity_integrality_guard_mutation_is_caught(monkeypatch):
    from eab import numeric_decode as decoder
    from eab import contact_record as cr
    mutant = _internal_mutant(decoder, decoder.integer, "if q.denominator != 1:", "if False:")
    monkeypatch.setattr(cr, "integer", mutant)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_fractional_feature_identifiers_are_rejected_not_truncated(F(1, 2**2000))


def test_window_range_guard_mutation_is_caught_at_constructor(monkeypatch):
    from eab.adapters import bdda2d as adapter
    old = 'scalar_rational(q, quantity=f"bdda2d.window.{name}")'
    mutant = _internal_mutant(adapter, adapter.Bdda2DWindow.__post_init__, old, "float(q)")
    monkeypatch.setattr(adapter.Bdda2DWindow, "__post_init__", mutant)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_adapter_window_checks_exact_inputs_before_libm_or_float("d0", F(1, 2**2000))


def test_signed_zero_preservation_has_an_internal_mutation_tooth(monkeypatch):
    from eab import numeric_decode as decoder
    from eab import contact_record as cr
    mutant = _internal_mutant(decoder, decoder.scalar,
                             "return value if isinstance(value, float) and value == 0.0 else result",
                             "return result")
    monkeypatch.setattr(cr, "scalar_rational", mutant)
    with pytest.raises(AssertionError, match="reader must preserve signed binary64 zero"):
        test_reader_preserves_signed_float_zero_through_json_roundtrip("normal", "dict")


def test_bdda3d_reference_evidence_guard_has_an_internal_mutation_tooth(monkeypatch, tmp_path):
    mutant = _internal_mutant(bdda3d, bdda3d.record_from_entrance,
                             'extra[k] = [list(r) for r in refs] if k == "refs" else c[k]',
                             'extra[k] = c[k]')
    monkeypatch.setattr(bdda3d, "record_from_entrance", mutant)
    with pytest.raises(AssertionError, match="reference evidence must preserve exact integer identity"):
        test_bdda3d_reference_evidence_keeps_checked_integer_identity("json", tmp_path)
