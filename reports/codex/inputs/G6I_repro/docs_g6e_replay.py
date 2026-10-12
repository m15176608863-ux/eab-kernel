"""Read-only G6E document/gate replays on the audited HEAD.

IDs use one-based positions in reports/codex/inputs/g6e_findings_raw.json.
No external program or Git write operation is used. In-process mutations are
compiled inside a real implementation and installed only with MonkeyPatch.
"""
from pathlib import Path
from dataclasses import fields
import inspect
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]
import pytest

rows = []
def record(identifier, text, checker):
    try:
        evidence = checker()
        rows.append({"id": identifier, "status": "resolved", "scope": text, "output": evidence})
    except Exception as error:
        rows.append({"id": identifier, "status": "unconfirmed", "scope": text,
                     "output": f"{type(error).__name__}: {error}"})

canon = (ROOT / "docs/canon_map.md").read_text(encoding="utf-8-sig")
readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")

def external_export():
    sibling = (ROOT / "docs/sibling_observations.md").read_text(encoding="utf-8-sig")
    source = Path("C:/Users/m1517/Desktop/PhD/DDA4.5_Performance_RC_20260828/02_source/01_kernel/DDAKernel.cpp")
    code = source.read_text(encoding="utf-8-sig")
    assert "contact_diagnostics_v3.tsv" in code
    assert "contact_diagnostics_v3.tsv" in canon and "contact_diagnostics_v3.tsv" in sibling
    assert "block_vertex" in code and "edge_start_id" in code
    return "DDAKernel.cpp has contact_diagnostics_v3.tsv + per-contact identity columns; both current docs acknowledge it"
record("G6E-01", "actual DDA4.x per-contact export vs corrected premise", external_export)

def contract_gaps():
    from eab.contact_record import ContactRecord
    names = [f.name for f in fields(ContactRecord)]
    assert "canonical_order_key" not in names and "source_engine" not in names
    for phrase in ("canonical_order_key", "FF / FE / EE_PAR", "solver_profile.tsv", "o3 vs o3t"):
        assert phrase in canon, phrase
    assert "Cover3.kind" in canon and "CoverType.FF/FE/EE_PAR" in canon
    return {"actual_fields": names, "registered_gaps": "source/order mapping, zero record constructors, solver_profile, constitutive observable"}
record("G6E-04", "07 contract gaps are now distinguished from implemented lifecycle fields", contract_gaps)

def boundary_votes():
    from eab.kernel2d.g0 import g0_convex
    from eab.kernel3d.g03 import g0_convex3
    from eab.kernel3d.geom3 import box
    square = [(0,0),(1,0),(1,1),(0,1)]
    a = g0_convex(square,square,samples=1)
    b = g0_convex3(box(),box(),samples=1)
    assert a.passed and b.passed
    assert a.band_skipped == b.band_skipped == 0
    assert a.boundary_probes > 0 and b.boundary_probes > 0
    assert a.samples == 1+a.boundary_probes and b.samples == 1+b.boundary_probes
    assert "\u00b1\u03b5" in canon
    return {"2d_samples":a.samples,"2d_boundary":a.boundary_probes,
            "3d_samples":b.samples,"3d_boundary":b.boundary_probes,"skipped":0,
            "scope":"all exact boundary points scored; docs still do not claim universal two-sided probes"}
record("G6E-05", "G0 boundary scoring and explicit remaining 07 deviation", boundary_votes)

def canon_rewrite_status():
    assert "\u5b9e\u9a8c\u6027\u7ed3\u8bba\u5df2\u56de\u519903" not in canon.replace(" ", "")
    assert "03" in canon and "82/39/60" in canon
    assert "GAP3\uff08\u6b63\u672c\u5bf9\u4ee3\u7801\uff09\u5df2\u6309\u5404\u8f6e\u62a5\u544a\u9010\u6761\u5904\u7f6e" in canon
    return "canon documents stale external 03 figures and completed prior GAP3 review; no current 'experiment written back' claim"
record("G6E-06", "external 03 is read-only and prior review status is updated", canon_rewrite_status)

def flat_arch():
    import test_limit_flat_arch as T
    for mu in (.3,.7,2.): T.test_flat_arch_between_rigid_abutments_is_self_locking(mu)
    T.test_frictionless_flat_arch_cannot_carry_its_own_weight()
    assert "test_limit_flat_arch.py" in readme
    return "3 frictional flat arches unbounded + frictionless infeasible; README now cites real separate gate"
record("G6E-10", "the previously missing flat-arch theorem gate exists and executes", flat_arch)

def pointers():
    import test_doc_pointers as T
    T.test_every_code_pointer_in_canon_map_names_a_function_at_its_current_line()
    return "test_every_code_pointer_in_canon_map_names_a_function_at_its_current_line PASS; >=60 named pointers, no unnamed ranges/stale defs"
record("G6E-14", "function pointer drift", pointers)
record("G6E-32", "unnamed and named pointer drift duplicate", pointers)

def entrance_status():
    assert "\u9996\u5165\uff1a\u4e09\u7ef4\u672a\u5b9e\u73b0\uff0c\u4e0d\u80fd\u4e3b\u5f20" not in canon
    assert "\u4e09\u7ef4\u9996\u5165\u96f6\u5b9e\u73b0\uff0c\u5217\u5165 M2" not in readme
    assert "2240" in readme and "480" in readme and "28" in readme
    return "no current contradictory M2 zero-implementation statement; N=5/N=7 mechanism counts separated (480/10;2240/28)"
record("G6E-16", "M2 and arch-count prose consistency", entrance_status)

def design07_gaps():
    for phrase in ("\u9501\u6001\u62d3\u6251\u540c\u6784", "solver_profile.tsv", "\u4e0d\u662f\u5bf9\u539f\u4ef6\u9010\u5b57\u8282", "\u6ca1\u6709\u4e8b\u5148\u767b\u8bb0\u9608\u503c", "\u64a4\u56de\u4f18\u5148\u6027\u4e3b\u5f20"):
        assert phrase in canon, phrase
    return "07 deviations registered: G1 topology/sign, original-byte roundtrip, solver_profile, G4 predeclared threshold/runtime, withdrawn priority"
record("G6E-18", "07 clauses previously omitted are explicitly registered as incomplete", design07_gaps)

def extent_mutants():
    import eab.kernel3d.interlock as I
    import test_interlock_candidates_contract as T
    baseline=[]
    for delta in (.05,.13):
        T.test_every_public_candidate_is_a_real_contact_at_its_own_height(delta)
        baseline.append(delta)
    raw=inspect.getsource(I._candidates_uncached)
    assert raw.count("if c is not None and c.in_extent:") == 1
    scope=dict(vars(I));exec(compile(raw.replace("if c is not None and c.in_extent:", "if c is not None:"), __file__, "exec"),scope)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(I,"_candidates_uncached",scope["_candidates_uncached"])
        try: T.test_every_public_candidate_is_a_real_contact_at_its_own_height(.13)
        except AssertionError as error: caught=f"AssertionError: {error}"
        else:raise AssertionError("unfiltered real candidates survived gate")
    return {"baseline":baseline,"real_internal_mutant":"remove in_extent in _candidates_uncached","caught":caught}
record("G6E-08", "filter removal moved to actual current path is rejected", extent_mutants)

def band_mutant():
    import eab.kernel3d.interlock as I
    import test_interlock_candidates_contract as T
    T.test_public_candidates_keep_both_branches_inside_the_predicate_band(-1.,1e-11)
    raw=inspect.getsource(I.escape_candidates)
    assert raw.count("_candidates(A, B, offset, tol, gtol)") == 1
    scope=dict(vars(I));exec(compile(raw.replace("_candidates(A, B, offset, tol, gtol)", "_candidates(A, B, offset, tol, 0.0)"), __file__, "exec"),scope)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(T,"escape_candidates",scope["escape_candidates"])
        try:T.test_public_candidates_keep_both_branches_inside_the_predicate_band(-1.,1e-11)
        except AssertionError as error:caught=f"AssertionError: {error}"
        else:raise AssertionError("zero report band survived gate")
    return {"baseline":"PASS","real_internal_mutant":"public nominal extent_tol=0","caught":caught}
record("G6E-35", "the public nominal-report extent band is independently guarded from omission", band_mutant)

print(json.dumps(rows, ensure_ascii=False, indent=2))
print("G6E_DOCUMENT_REPLAY resolved="+str(sum(r['status']=='resolved' for r in rows))
      +" unconfirmed="+str(sum(r['status']!='resolved' for r in rows)))
