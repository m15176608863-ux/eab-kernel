"""Explicit R15 local AST-pin review ledger; not an analyzer or blanket waiver.

Only scopes listed below may be renewed/added. Unknown scopes fail closed.
Each admitted node still has its own AST and enclosing-source hash.
"""
import ast
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
POLICY = ROOT / "tools/exact_construction_policy.json"
spec = importlib.util.spec_from_file_location("r15_static", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
REVIEWS = {('src/eab/limit.py', 'limit_load'): 'O01 exact column products, exact squared magnitude selection, Fraction-zero complete per-contact sums, checked final scalar with exact_contact_forces and an explicit iff-underflow flag; overflow remains rejected. Independent single-contact balance and physical intermediate-overflow tests plus four internal mutants; LP candidate/certificate model unchanged.', ('src/eab/limit_multi.py', '<module>'): 'Imports checked scalar construction, no new numeric model or unbounded dynamic dispatch.', ('src/eab/limit_multi.py', 'limit_load_multi'): 'O01 same exact selected-column force report as single body, independently tested via one-body embedding and exact balance. Existing multi-body LP/certificate calls unchanged; no geometry oracle claim.', ('src/eab/readers/numeric_decode.py', '_decimal'): 'O04 lexical decimal stage preserves exact Fraction and negative zero; no continuous-domain validation before schema. Known continuous schema fields retain checked scalar construction; integer identities use denominator=1.', ('src/eab/readers/bdda3d.py', 'record_from_entrance'): 'O04 actual file reader dispatches nsign/owner as exact integers and known continuous extras as checked scalars even if integer tokens or unpaired tangent supplied. Copied dictionary avoids mutating input. Generic unknown evidence remains recursive decoder.', ('src/eab/margin.py', 'margin_contacts'): 'O03 validates finite delta/band before early return; exact -delta rounded with underflow permission backed by squared distance zero and independently exact closed. All normal branches retain squared-distance certificate and full-expression final gap.', ('src/eab/kernel3d/interlock.py', 'escape_height_covers'): 'O05 authoritative rational escape root unchanged; upward nextafter display may reach positive infinity only with explicit height_display_overflow and exact_height. Finite RN conversion still checked. Existing event/interval certification calls unchanged.', ('src/eab/kernel3d/interlock.py', 'escape_height_brute'): 'Bare-float compatibility wrapper cannot propagate overflow certificate, so explicit flagged display overflow raises named domain error. Existing exact-root delegation is secondary oracle only.', ('src/eab/kernel3d/interlock.py', 'dilatancy_profile'): 'Exact supplied delta*direction offsets and complete rational secant of authoritative roots before checked final tan_psi; height plus exact root/overflow metadata propagated. Independent sloped-solid cases detect both prior cancellation sites.'}
REVIEWS.update({('tests/test_r15fix_force_reports.py', '_solve'): 'Test driver invokes real single/multi LP and selfcheck. Independent expected resultant from single-contact statics is asserted outside these production calls; no shared geometry primitive supplies expected value.', ('tests/test_r15fix_force_reports.py', 'test_contact_force_report_rounds_complete_exact_sum'): 'Standard float rounds only completed independent expected Fraction resultant / exact power-of-two weight. No production output is rounded to weaken assertion; tuples are compared exactly.', ('tests/test_r15fix_force_reports.py', 'test_force_selection_does_not_round_overflowing_intermediate_columns'): 'Standard float rounds only completed independent expected Fraction resultant / exact power-of-two weight. No production output is rounded to weaken assertion; tuples are compared exactly.', ('tests/test_r15fix_geometry.py', '_assert_penetration_certificate'): 'Real public margin call; independent zero distance and signed -delta oracle with Fraction and only final float expected display. Exact fields and signed-zero assertions detect missing certificate.', ('tests/test_r15fix_geometry.py', '_assert_escape_display'): 'Independent axis-box interval or explicitly constructed rational tilted plane gives root/slope, not production overlap or event code. Tested escape/profile invocation and explicit new-field presence lookup are test harness, not production dynamic dispatch.', ('tests/test_r15fix_geometry.py', '_tilted_profile'): 'Independent axis-box interval or explicitly constructed rational tilted plane gives root/slope, not production overlap or event code. Tested escape/profile invocation and explicit new-field presence lookup are test harness, not production dynamic dispatch.', ('tests/test_r15fix_geometry.py', '_mutate'): 'Test-only inspect/compile/exec of one exact replacement in real production function and monkeypatch restoration. Deliberately prohibited internal operations must red designated assertion, never fake appended output.', ('tests/test_r15fix_numeric_decode.py', '_accepted'): 'Local test closure invokes one explicitly passed reader entry and converts unexpected domain rejection into named assertion. Arbitrary-call admission not granted to production.', ('tests/test_r15fix_numeric_decode.py', '_internal_mutant'): 'Test-only actual-function source replacement and in-memory compilation. Single matching internal operation checked before mutation; monkeypatch replaces real decoder then restores. Not a production reflection waiver.', ('tests/test_r15fix_shape.py', 'test_shape_dual_complete_coordinate_keeps_midpoint_residual'): 'Independent complete Fraction coordinate/jet oracle; float is solely the final expected RN boundary. Sampled math.sin/cos coefficients define the declared model, not an ideal transcendental accuracy claim.', ('tests/test_r15fix_shape.py', 'test_shape_dual_complete_jet_keeps_midpoint_residual'): 'Independent complete Fraction coordinate/jet oracle; float is solely the final expected RN boundary. Sampled math.sin/cos coefficients define the declared model, not an ideal transcendental accuracy claim.', ('tests/test_r15fix_shape.py', 'test_shape_dual_complete_z_keeps_height_and_jet_residuals'): 'Independent complete Fraction coordinate/jet oracle; float is solely the final expected RN boundary. Sampled math.sin/cos coefficients define the declared model, not an ideal transcendental accuracy claim.', ('tests/test_r15fix_shape.py', 'test_shape_generic_pair_translation_stays_exact_until_final_vertices'): 'Independent complete Fraction coordinate/jet oracle; float is solely the final expected RN boundary. Sampled math.sin/cos coefficients define the declared model, not an ideal transcendental accuracy claim.', ('tests/test_r15fix_shape.py', 'test_shape_phase_jet_is_scaled_before_final_range_check'): 'Independent complete Fraction coordinate/jet oracle; float is solely the final expected RN boundary. Sampled math.sin/cos coefficients define the declared model, not an ideal transcendental accuracy claim.', ('tests/test_r15fix_shape.py', 'test_shape_general_position_all_vertices_and_channels_round_once'): 'All given coefficients and coordinate/jet terms kept Fraction. float(u) reproduces declared sampled binary64 grid angle coefficient (u is already the rational encoding of i/nx float); final float(q/jet) is independent expected output, not a rounded intermediate algebra.', ('tests/test_r15fix_shape.py', 'test_shape_internal_rounded_addition_mutation_has_teeth.rounded_addition'): 'Deliberately rounded primal/jet in the real internal addition method is fault injection. Designated complete-residual assertion must fail; not an approved production early round.'})
REVIEWS[("tests/test_r15fix_force_reports.py", "test_contact_force_nonzero_final_underflow_has_explicit_exact_certificate")] = "Independent exact selected-contact force is -tiny,10. The sole float(-tiny) is final expected display, with explicit exact certificate equality, iff-underflow flag and signed-zero assertions; original subnormal LP success gate stays unchanged."
IMPORTS = []

def write(path, data):
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    mode = sys.argv[1]
    if mode == "renew":
        backup = HERE / "static_policy_before.json"
        if not backup.exists():
            backup.write_bytes(POLICY.read_bytes())
        renewed, removed, kept = [], [], []
        parsed = {}
        for row in policy["waivers"]:
            if row["path"] not in parsed:
                text = (ROOT/row["path"]).read_text(encoding="utf-8-sig")
                parsed[row["path"]] = (gate._subset.site_contexts(text),
                                       {ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(text))})
            contexts, nodes = parsed[row["path"]]
            if contexts.get(row["function"]) == row["context"] and row["node"] in nodes:
                kept.append(row)
                continue
            note = REVIEWS.get((row["path"], row["function"]))
            assert note, ("UNREVIEWED stale scope", row["path"], row["function"])
            if row["node"] not in nodes:
                removed.append(row)
            else:
                update = {**row, "context": contexts[row["function"]],
                          "reason": row["reason"] + " R15 local renewal: " + note,
                          "review_evidence": "reports/codex/R15FIX_evidence/static_review.json"}
                renewed.append(update); kept.append(update)
        policy["waivers"] = kept
        added = sorted(set(IMPORTS)-set(policy["imports"]))
        policy["imports"] = sorted(set(policy["imports"])|set(IMPORTS))
        write(POLICY, policy)
        write(HERE/"static_renewals.json", dict(renewed=renewed, removed=removed, imports_added=added))
        print("renewed", len(renewed), "removed", len(removed), "imports", len(added))
    elif mode.startswith("scan"):
        paths = sorted({p for p, _ in REVIEWS})
        if mode == "scan-local":
            issues = [i for path in paths for i in gate.scan_text((ROOT/path).read_text(encoding="utf-8-sig"), path, repository_root=ROOT)]
        else:
            issues = gate.scan_repository(ROOT)
        write(HERE/"static_pending.json", issues)
        print("issues", len(issues))
        print(json.dumps(Counter(f"{p}::{f}::{r}" for p, _, f, r, _ in issues), indent=2))
    elif mode == "approve":
        issues = json.loads((HERE/"static_pending.json").read_text(encoding="utf-8"))
        added = []
        for path, line, fn, rule, code in issues:
            note = REVIEWS.get((path, fn))
            assert note and rule != "closed-stale-waiver", ("UNREVIEWED site", path, fn, rule, code)
            text = (ROOT/path).read_text(encoding="utf-8-sig")
            nodes = [n for n in ast.walk(ast.parse(text)) if getattr(n, "lineno", None) == line
                     and (ast.get_source_segment(text,n)==code or ast.unparse(n)==code)]
            assert nodes, ("Cannot pin exact node", path, line, fn, rule, code)
            node = min(nodes,key=lambda n:isinstance(n,ast.Expr))
            serial = max((int(r["id"].removeprefix("R15-L")) for r in policy["waivers"]
                          if r["id"].startswith("R15-L")), default=0) + len(added) + 1
            row = dict(id=f"R15-L{serial:04d}", path=path, function=fn, rule=rule,
                       node=ast.dump(node,include_attributes=False), context=gate._subset.site_contexts(text)[fn],
                       category="RUNTIME_TEST_ORACLE_REVIEW" if path.startswith("tests/") else "LOCAL_NUMERIC_OR_PROTOCOL_REVIEW",
                       reason="Specific node: "+code+". "+note,
                       review_evidence="reports/codex/R15FIX_evidence/static_review.json")
            identity=tuple(row[k] for k in ("path","function","rule","node","context"))
            if any(tuple(r[k] for k in ("path","function","rule","node","context"))==identity for r in policy["waivers"]+added):
                continue
            added.append(row)
        policy["waivers"].extend(added)
        assert len({r["id"] for r in policy["waivers"]}) == len(policy["waivers"])
        write(POLICY,policy)
        write(HERE/"static_review.json",[r for r in policy["waivers"] if r["id"].startswith("R15-") or "R15 local renewal:" in r["reason"]])
        print("explicit added site reviews",len(added),"total",len(policy["waivers"]))
    else:
        raise ValueError(mode)


if __name__=="__main__":
    main()
