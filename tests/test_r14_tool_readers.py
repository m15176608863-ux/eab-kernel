"""Physical export tools: exact literal checks before binary64 decoding.

Oracle: decimal 1e-400 is nonzero and below min binary64; 1e400 is finite
and above max binary64. No production decoder computes those facts. Tests
use temporary text only, never a sibling executable or capture operation.
"""
from pathlib import Path
from types import SimpleNamespace
import inspect
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import bb52_g0
import g2_bdda3d
import g4_multistep
import ingest_bdda3d
import m4_capture_family
from eab.numeric_domain import ConstructionDomainError


def _invoke(api, token, tmp_path, monkeypatch):
    if api == "g2_geometry":
        path = tmp_path / "case.json"
        path.write_text('{"case":"probe","step":0,"verts":{"1":[['+token+',0,0],[1,0,0],[0,1,0],[0,0,1]]},"entrances":[]}', encoding="utf-8")
        return g2_bdda3d.load_case_full(path)
    if api == "bb_vertices":
        (tmp_path / "bdda_debug_verts.csv").write_text("step,block,vidx,x,y\n1,1,1,"+token+",0\n1,1,2,1,0\n1,1,3,0,1\n", encoding="utf-8")
        monkeypatch.setattr(bb52_g0, "FIX", tmp_path)
        return bb52_g0.load_blocks()
    if api in ("bb_contacts", "g4_contacts"):
        (tmp_path / "bdda_debug_contacts.csv").write_text("step,contact,mtype,p1,p2,p3,m0_2,o2\n1,18014398509481985,0,1,2,3,0,"+token+"\n", encoding="utf-8")
        if api == "bb_contacts":
            monkeypatch.setattr(bb52_g0, "FIX", tmp_path)
            return bb52_g0.legacy_contacts()
        return g4_multistep.read_contacts(tmp_path)
    if api == "g4_params":
        (tmp_path / "bdda_debug_detparams.csv").write_text("step,d0,h5,h1,w0\n1,"+token+",0.3,3,1\n", encoding="utf-8")
        return g4_multistep.read_detparams(tmp_path)
    if api == "m4_summary":
        (tmp_path / "bdda_debug_contacts.csv").write_text("step,contact,mtype,p1,p2,p3\n1,1,0,1,1,1\n", encoding="utf-8")
        (tmp_path / "bdda_debug_detparams.csv").write_text("step,d0\n1,"+token+"\n", encoding="utf-8")
        geometry = SimpleNamespace(blocks={1: object()}, vertex_block=lambda: {1:1}, canon=lambda i:i)
        record = SimpleNamespace(step=1, contact_index=1, canonical_key=lambda: (1,))
        monkeypatch.setattr(m4_capture_family, "load_step_geometries", lambda path: {1: geometry})
        monkeypatch.setattr(m4_capture_family, "load_records", lambda path: [record])
        return m4_capture_family.fixture_summary(tmp_path, 1)
    if api == "ingest_json":
        (tmp_path / "src" / "bdda3d").mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(ingest_bdda3d, "SIBLING", tmp_path)
        monkeypatch.setattr(ingest_bdda3d, "OUT", tmp_path / "out")
        monkeypatch.setattr(ingest_bdda3d, "BUILDERS", {"cb2_locked": "unused"})
        stdout = '{"case":"cb2_locked","step":0,"verts":{},"entrances":[{"area":'+token+'}]}'
        monkeypatch.setattr(ingest_bdda3d.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=stdout))
        monkeypatch.setattr(ingest_bdda3d, "provenance_entry", lambda *a: {})
        monkeypatch.setattr(ingest_bdda3d, "upsert_provenance", lambda *a: None)
        return ingest_bdda3d.main()
    raise AssertionError(api)


APIS = ["g2_geometry", "bb_vertices", "bb_contacts", "g4_contacts", "g4_params", "m4_summary", "ingest_json"]


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize("token", ["1e-400", "-1e-400", "1e400"])
def test_r14_tool_physical_literal_cannot_silently_lose_range(api, token, tmp_path, monkeypatch):
    with pytest.raises(ConstructionDomainError):
        _invoke(api, token, tmp_path, monkeypatch)


@pytest.mark.parametrize("api", APIS)
def test_r14_tool_ordinary_decimal_literals_remain_accepted(api, tmp_path, monkeypatch):
    _invoke(api, "0.1", tmp_path, monkeypatch)


def test_r14_g4_contact_identity_is_exact_and_real_payload_is_binary64(tmp_path, monkeypatch):
    rows = _invoke("g4_contacts", "0.1", tmp_path, monkeypatch)
    assert rows[1][0]["contact"] == 18014398509481985
    assert rows[1][0]["o2"] == 0.1 and type(rows[1][0]["o2"]) is float


def test_r14_g2_decimal_geometry_retains_original_binary64_model(tmp_path, monkeypatch):
    case = _invoke("g2_geometry", "0.1", tmp_path, monkeypatch)
    assert case["blocks"][1].verts[0][0] == 0.1
    assert type(case["blocks"][1].verts[0][0]) is float


@pytest.mark.parametrize("value", ["1e-400", "-1e-400", "1e400"])
def test_r14_ingest_child_checks_before_vertex_float(value, monkeypatch):
    from fractions import Fraction
    vertices = [(Fraction(value), 0, 0)]
    ss = SimpleNamespace(blocks={1: {"vertices": vertices}})
    cases = SimpleNamespace(build_cb2=lambda *a, **k: (ss, []), build_cb_bond=lambda *a, **k: (ss, []))
    # Only the locally-owned export string is executed against an in-memory
    # sibling stub: no sibling source, executable, directory or process is used.
    monkeypatch.setitem(sys.modules, "bdda3d", SimpleNamespace(cases=cases))
    monkeypatch.setattr(sys, "argv", ["stub", "cb2_locked"])
    with pytest.raises(OverflowError, match="vertex"):
        exec(compile(ingest_bdda3d.CHILD, "<local-export-child-stub>", "exec"), {})


@pytest.mark.parametrize("api", APIS)
def test_r14_tool_removed_exact_numeric_boundary_is_caught(api, tmp_path, monkeypatch):
    import json
    modules = {"g2_geometry":g2_bdda3d, "bb_vertices":bb52_g0, "bb_contacts":bb52_g0,
               "g4_contacts":g4_multistep, "g4_params":g4_multistep,
               "m4_summary":m4_capture_family, "ingest_json":ingest_bdda3d}
    module = modules[api]
    if api in ("g2_geometry", "ingest_json"):
        # Reintroduce early JSON coercion *inside* the real entry path.
        monkeypatch.setattr(module, "numeric_loads", json.loads)
    else:
        # Replace the real field decoder, not the produced row/geometry.
        monkeypatch.setattr(module, "scalar_rational", lambda v, **kw: float(v))
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r14_tool_physical_literal_cannot_silently_lose_range(api, "1e-400", tmp_path, monkeypatch)


def test_r14_ingest_child_bare_float_mutation_is_caught(monkeypatch):
    assert ingest_bdda3d.CHILD.count("list(map(checked_vertex, v))") == 1
    monkeypatch.setattr(ingest_bdda3d, "CHILD", ingest_bdda3d.CHILD.replace("list(map(checked_vertex, v))", "list(map(float, v))"))
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r14_ingest_child_checks_before_vertex_float("1e-400", monkeypatch)



def _copied_bb52(tmp_path):
    for source in (ROOT / "fixtures/bdda_df/bb52_N3").glob("*.csv"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    return tmp_path


def _replace_csv_field(path, predicate, field, value):
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
    changed = 0
    for row in rows:
        if predicate(row):
            row[field] = value
            changed += 1
    assert changed
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8", newline="")


def test_r14_m4_cs1_text_boundary_is_checked_in_actual_compare(tmp_path):
    import m4_bdda_shadow as shadow
    from eab.readers import bdda_df
    fixture = _copied_bb52(tmp_path)
    _replace_csv_field(fixture / "bdda_debug_df18.csv",
                       lambda row: row["step"] == "1" and row["contact"] == "1", "cs1", "1e-400")
    records = [r for r in bdda_df.load_records(fixture) if r.step == 1]
    first = next(r for r in records if r.contact_index == 1)
    assert first.extra["df18_cs1"] == "1e-400", "reader retains original exact text evidence"
    geometry = shadow.load_step_geometries(fixture / "bdda_debug_verts.csv")[1]
    with pytest.raises(ConstructionDomainError, match="cs1"):
        shadow.compare_step(geometry, shadow.load_window(fixture, 1), records)


def test_r14_g4_angle_domain_rejects_radians_underflow_at_actual_analyze(tmp_path):
    fixture = _copied_bb52(tmp_path)
    _replace_csv_field(fixture / "bdda_debug_detparams.csv",
                       lambda row: row["step"] == "1", "h1", "5e-324")
    with pytest.raises(ConstructionDomainError, match="h1"):
        g4_multistep.analyze(fixture)



def test_r14_m4_cs1_bare_float_mutation_is_caught(tmp_path, monkeypatch):
    import m4_bdda_shadow as shadow
    monkeypatch.setattr(shadow, "scalar_rational", lambda value, **kw: float(value))
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r14_m4_cs1_text_boundary_is_checked_in_actual_compare(tmp_path)


def test_r14_g4_removed_angle_domain_mutation_is_caught(tmp_path, monkeypatch):
    from fractions import Fraction
    monkeypatch.setattr(g4_multistep, "check_input", lambda value, quantity: Fraction(value))
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r14_g4_angle_domain_rejects_radians_underflow_at_actual_analyze(tmp_path)



def test_r14_tool_document_decimal_identity_is_not_rounded(tmp_path):
    p = tmp_path / "identity.json"
    p.write_text('{"case":"probe","step":18014398509481985.0,"verts":{},"entrances":[{"bi":18014398509481985.0,"bj":1,"refs":[[18014398509481985.0,18014398509481985.0]],"owner":[1.0],"nsign":1.0,"m0init":1.0,"m0_0":0.0}]}', encoding="utf-8")
    result = g2_bdda3d.load_case_full(p)
    assert result["step"] == 2**54+1 and type(result["step"]) is int, "decimal step must remain exact integer"
    entrance = result["entrances"][0]
    assert entrance["bi"] == 2**54+1, "decimal block identity must remain exact"
    assert entrance["refs"] == [[2**54+1, 2**54+1]], "nested decimal refs must remain exact"
    for key in ("nsign", "m0init", "m0_0"):
        assert type(entrance[key]) is int



def test_r14_tool_document_generic_tree_identity_mutation_is_caught(tmp_path, monkeypatch):
    from eab.readers.numeric_decode import loads, decode_tree
    monkeypatch.setattr(g2_bdda3d, "numeric_loads", lambda text: decode_tree(loads(text), "old document"))
    with pytest.raises(AssertionError, match="decimal step must remain exact integer"):
        test_r14_tool_document_decimal_identity_is_not_rounded(tmp_path)


def test_r14_ingest_decimal_identity_survives_writer(tmp_path, monkeypatch):
    import json
    (tmp_path / "src" / "bdda3d").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ingest_bdda3d, "SIBLING", tmp_path)
    monkeypatch.setattr(ingest_bdda3d, "OUT", tmp_path / "out")
    monkeypatch.setattr(ingest_bdda3d, "BUILDERS", {"cb2_locked": "unused"})
    stdout = '{"case":"cb2_locked","step":18014398509481985.0,"verts":{},"entrances":[]}'
    monkeypatch.setattr(ingest_bdda3d.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=stdout))
    monkeypatch.setattr(ingest_bdda3d, "provenance_entry", lambda *a: {})
    monkeypatch.setattr(ingest_bdda3d, "upsert_provenance", lambda *a: None)
    ingest_bdda3d.main()
    output = json.loads((tmp_path / "out/cb2_locked.json").read_text(encoding="utf-8"))
    assert output["step"] == 2**54+1 and type(output["step"]) is int, "written decimal identity remains exact"
