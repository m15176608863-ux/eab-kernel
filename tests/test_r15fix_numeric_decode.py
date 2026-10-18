"""R15 O04: schema dispatch, not JSON spelling, decides the numeric domain.

Oracle uses literal integer/Fraction equality and binary64's known RN endpoint
cells, not production parsing/construction or geometry helpers. Mutations enter
the real parser or reader before schema dispatch, never alter returned records.
"""
from fractions import Fraction as F
import inspect
import json
import math
import textwrap

import pytest

from eab.contact_record import ContactRecord, records_from_json, records_to_json
from eab.numeric_domain import ConstructionDomainError
from eab.readers import bdda3d
from eab import numeric_decode
from tools import bdda3d_document


BASE = dict(source="r15", step=0, contact_index=0, block_a=1, block_b=2)
IDENTITY = 10**400
INTEGER_FIELDS = ("step", "contact_index", "block_a", "block_b", "joint_material",
                  "raw_mode", "raw_mode_prev", "raw_mode_init", "entrance_index",
                  "bond_flag", "raw_cover")


def _literal(value, token):
    return json.dumps(value).replace('"TOKEN"', token)


def _accepted(call):
    try:
        return call()
    except ConstructionDomainError as error:
        raise AssertionError("unbounded integer schema rejected an exact integer") from error


@pytest.mark.parametrize("field", INTEGER_FIELDS)
@pytest.mark.parametrize("token", ["1e400", "10.00e399"])
def test_o04_contact_decimal_integer_identity_is_unbounded(field, token):
    payload = dict(BASE, **{field: "TOKEN"})
    rec, = _accepted(lambda: records_from_json(_literal([payload], token)))
    assert getattr(rec, field) == IDENTITY
    assert type(getattr(rec, field)) is int
    direct = ContactRecord.from_dict(dict(BASE, **{field: F(IDENTITY)}))
    assert rec == direct == records_from_json(records_to_json([rec]))[0]


@pytest.mark.parametrize("field", ["block", "index", "verts"])
def test_o04_nested_feature_decimal_identity_is_unbounded(field):
    feature = dict(block=1, kind="face", index=0, verts=[1, 2, 3])
    feature[field] = ["TOKEN"] if field == "verts" else "TOKEN"
    rec, = _accepted(lambda: records_from_json(_literal([dict(BASE, feature_a=feature)], "1e400")))
    actual = getattr(rec.feature_a, field)
    assert actual == ((IDENTITY,) if field == "verts" else IDENTITY)


@pytest.mark.parametrize("api", ["reader", "document"])
@pytest.mark.parametrize("field", ["step", "bi", "bj", "m0init", "m0_0", "refs"])
def test_o04_real_bdda3d_decimal_integer_identity_is_unbounded(tmp_path, api, field):
    row = dict(bi=1, bj=2, etype="np")
    payload = dict(step=0, entrances=[row])
    if field == "step":
        payload["step"] = "TOKEN"
    elif field == "refs":
        row["refs"] = [[1, 0], [2, "TOKEN"], [2, 2], [2, 3]]
    else:
        row[field] = "TOKEN"
    text = _literal(payload, "1e400")
    if api == "reader":
        path = tmp_path / "identity.json"
        path.write_text(text, encoding="utf-8")
        rec, = _accepted(lambda: bdda3d.load_records(path))
        if field == "refs":
            actual = rec.extra["refs"][1][1]
            assert IDENTITY in rec.feature_b.verts
        else:
            actual = getattr(rec, {"bi": "block_a", "bj": "block_b", "m0init": "raw_mode_init",
                                   "m0_0": "bond_flag"}.get(field, field))
    else:
        doc = _accepted(lambda: bdda3d_document.loads(text))
        actual = (doc["step"] if field == "step" else
                  doc["entrances"][0]["refs"][1][1] if field == "refs" else doc["entrances"][0][field])
    assert actual == IDENTITY and type(actual) is int


@pytest.mark.parametrize("api", ["contact", "reader", "document"])
@pytest.mark.parametrize("token", ["1e400", "1e-400", "-1e400", "-1e-400"])
def test_o04_continuous_values_are_rejected_at_the_field_schema(tmp_path, api, token):
    if api == "contact":
        call = lambda: records_from_json(_literal([dict(BASE, gap="TOKEN")], token))
        quantity = "gap"
    else:
        text = _literal(dict(entrances=[dict(bi=1, bj=2, area="TOKEN")]), token)
        path = tmp_path / "continuous.json"
        path.write_text(text, encoding="utf-8")
        call = (lambda: bdda3d.load_records(path)) if api == "reader" else (lambda: bdda3d_document.loads(text))
        quantity = "area"
    with pytest.raises(ConstructionDomainError) as exc:
        call()
    assert quantity in exc.value.quantity, "continuous domain check must name its schema field"


@pytest.mark.parametrize("token", ["-0.0", "-0e400", "-0e-400"])
def test_o04_decimal_parser_preserves_negative_zero_until_schema(token):
    value = numeric_decode.loads(token)
    assert value == 0.0 and math.copysign(1.0, value) == -1
    assert numeric_decode.integer(value, "identity") == 0


def _internal_mutant(module, function, old, new):
    source = textwrap.dedent(inspect.getsource(function))
    assert old in source
    namespace = dict(vars(module))
    exec(compile(source.replace(old, new), "<R15 reader internal mutation>", "exec"), namespace)
    return namespace[function.__name__]


def test_o04_schema_before_domain_has_an_internal_mutation_tooth(monkeypatch):
    mutant = _internal_mutant(numeric_decode, numeric_decode._decimal,
                             "q = Fraction(token)",
                             'q = Fraction(token)\n    scalar_rational(q, quantity="JSON numeric literal")')
    monkeypatch.setattr(numeric_decode, "_decimal", mutant)
    with pytest.raises(AssertionError, match="unbounded integer schema rejected"):
        test_o04_contact_decimal_integer_identity_is_unbounded("step", "1e400")


@pytest.mark.parametrize("field", ["nsign", "owner"])
def test_o04_scan_discrete_bdda3d_evidence_uses_integer_schema(field):
    row = dict(bi=1, bj=2, etype="np")
    row[field] = [F(IDENTITY), 0, 1, 0] if field == "owner" else F(IDENTITY)
    rec = _accepted(lambda: bdda3d.record_from_entrance(row))
    actual = rec.extra[field][0] if field == "owner" else rec.extra[field]
    assert actual == IDENTITY and type(actual) is int, "discrete evidence must preserve exact integer identity"


@pytest.mark.parametrize("field", ["nsign", "owner"])
def test_o04_scan_discrete_bdda3d_schema_does_not_truncate_fraction(field):
    row = dict(bi=1, bj=2, etype="np")
    row[field] = [F(3, 2), 0, 1, 0] if field == "owner" else F(3, 2)
    with pytest.raises(ConstructionDomainError, match=field):
        bdda3d.record_from_entrance(row)


@pytest.mark.parametrize("field", ["d1", "fa", "coh", "tens", "t1", "t2"])
def test_o04_scan_known_bdda3d_continuous_integer_literals_cannot_bypass_domain(field):
    row = dict(bi=1, bj=2, etype="np", **{field: IDENTITY})
    with pytest.raises(ConstructionDomainError, match=field):
        bdda3d.record_from_entrance(row)


@pytest.mark.parametrize("field", ["nsign", "owner"])
def test_o04_scan_discrete_schema_has_an_internal_mutation_tooth(monkeypatch, field):
    old = ('c["nsign"] = integer(c["nsign"], "bdda3d.nsign")' if field == "nsign" else
           'c["owner"] = [integer(v, "bdda3d.owner") for v in c["owner"]]')
    mutant = _internal_mutant(bdda3d, bdda3d.record_from_entrance, old, "pass")
    monkeypatch.setattr(bdda3d, "record_from_entrance", mutant)
    with pytest.raises(AssertionError, match="unbounded integer schema rejected"):
        test_o04_scan_discrete_bdda3d_evidence_uses_integer_schema(field)


@pytest.mark.parametrize("field", ["d1", "fa", "coh", "tens", "t1", "t2"])
def test_o04_scan_continuous_schema_has_an_internal_mutation_tooth(monkeypatch, field):
    old = 'for name in ("t1", "t2", "d1", "fa", "coh", "tens"):'
    names = tuple(name for name in ("t1", "t2", "d1", "fa", "coh", "tens") if name != field)
    mutant = _internal_mutant(bdda3d, bdda3d.record_from_entrance, old, f"for name in {names!r}:")
    monkeypatch.setattr(bdda3d, "record_from_entrance", mutant)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_o04_scan_known_bdda3d_continuous_integer_literals_cannot_bypass_domain(field)
