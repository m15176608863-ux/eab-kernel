"""Explicit R14 local AST-pin review ledger; not an analyzer or blanket waiver.

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
spec = importlib.util.spec_from_file_location("r14_static", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
REVIEWS = {}


def review(path, names, reason):
    for name in names.split():
        REVIEWS[path, name] = reason


review("src/eab/contact_record.py", "<module> _decode ContactRecord.from_dict records_from_json",
       "R14 N03 exact-first JSON and quantity-named scalar boundary; decimal tokens retain Fraction until integer/continuous field dispatch. Structured enum/Feature/list transport is not geometric arithmetic. Integer IDs require denominator one; extras preserve strings and integers. Reader roundtrip and exact RN endpoint gates pass.")
review("src/eab/readers/numeric_decode.py", "<module> _decimal scalar _nonfinite loads integer decode_tree",
       "R14 N03 reviewed parser callbacks: exact decimal Fraction checked before binary64; nonfinite JSON constants rejected; exact integers unbounded but never truncated. Signed binary64 zero retained after range check; only negative real zero token receives -0.0, integer -0 unchanged. Recursive evidence tree retains dict/list/tuple and strings, only float/Fraction continuous numeric evidence takes checked scalar output. Dynamic type(value) is restricted by preceding isinstance(list,tuple), not arbitrary protocol dispatch.")
review("src/eab/readers/bdda3d.py", "<module> record_from_entrance load_records",
       "Actual JSON file path now uses exact-first decoder; all mapped continuous fields take checked scalar, discrete references/step/index take exact integer guard, numeric extras use checked tree decoding. Legacy source-code maps and feature semantics unchanged; M4/readers roundtrip regression passed.")
review("src/eab/adapters/bdda2d.py", "<module> Bdda2DWindow.__post_init__ Bdda2DWindow.cone_tol load_window",
       "R14 adapter entry validates the four explicitly enumerated dataclass numeric fields by exact input, sign and named output-range checks. getattr names are closed literal field list. Exact geometry windows remain exact; angle is 0 or [2^-400,90) degrees, then declared bounded binary64/libm coefficient. Existing CSV checked decoding/fallback remains unchanged.")
review("src/eab/numeric_domain.py", "<module> check_mu binary64_argument",
       "Quantity-specific exact domain only: mu compared rationally to [0,2^20]; lossless libm parameter recognized from denominator power-of-two, odd significand <=53 bits, lowest exponent >=-1074 and highest <=1023. float(q) occurs only after representability proof. Bit-length methods act on Fraction numerator/denominator integers, not unknown numeric protocols.")
review("src/eab/dual.py", "<module> Dual.__pow__ _check_exact_power_size _lossless_libm_input sin cos atan2",
       "N01 exact exponent retained through integer/half-integer dispatch and complete rational derivative. Materialization has explicit 2^20 bit resource domain except trivial bases. Other exponents/base and trig arguments pass exact lossless binary64 guard before libm. Existing 80-digit Decimal general-power coefficient is an approximate model, not exact transcendental proof. Final nonzero underflow and atan2 RN-zero cell fail loud. Parity, full finite binary64 subnormal grid and internal mutations exercise these sites.")
review("src/eab/kernel2d/geom.py", "<module> reflex_vertices is_convex",
       "Existing reflex-angle window explicitly uses a binary64 libm coefficient model; new lossless argument guard prevents exact Fraction/int corruption before sin/cos. is_convex is unchanged caller; determinant remains exact. Module aliases/annotations unchanged apart from this import.")
review("src/eab/limit.py", "<module> _inside_friction_cone _certified_friction_direction friction_generators LimitContact.__post_init__ contacts_from_covers",
       "N04 mu guard is rational and precedes construction. Candidate tangent/libm rays are approximate model; every final binary64 ray independently passes rational positive normal work and circular cone containment. The 2D caller supplies completed RN float candidates: the same-sign finite one-ulp grid contains at most nine points, each is independently certified, and the exact squared-distance/tuple lexicographic minimum selects the nearest safe point to that RN candidate. nextafter enumerates representations, not a approximate branch oracle. If no neighbor succeeds, unchanged finite inward contraction recertifies or fails loud; 3D does not enter neighbor search. Rounded g is the object intentionally certified, not a hidden intermediate oracle.")
review("src/eab/limit.py", "_cohesion_directions _build_columns _check_columns",
       "Cohesion directions projected exactly into given normal tangent plane; if squared norm exceeds one, rational upper-bound sqrt ceiling scales inward and exact LP coefficients are retained. Independent checker uses exact cross-product circular inequality and cohesive tangency/unit disk, not generator truth. Cohesion cap is complete Fraction(cohesion)*Fraction(area), and mutable material values are revalidated before use. Runtime physical cone/capacity gates cover these changes.")
review("src/eab/limit.py", "_check_material",
       "Finite/nonnegative material-domain check at construction, empty-cover adapters and mutable-record assembly; only builtin float takes math.isfinite so finite Fraction is not prematurely rounded. mu separately uses exact [0,2^20] guard; area/cohesion retain unbounded finite nonnegative rational input and exact product. No new numerical construction or approximate predicate.")
review("src/eab/limit.py", "limit_load mechanism_is_admissible check_duality",
       "Unchanged solver/checker callers now transitively reach certified generators and quantity guards. Original exact LP certificate and model assembly obligations remain; these pins do not assert static proof of the LP algorithm or mathematical circular capacity equality.")
review("src/eab/limit_multi.py", "<module> contacts_from_covers_multi limit_load_multi check_duality_multi mechanism_is_admissible_multi",
       "Existing multi-block assembly/checker calls same single-contact generator/checker; mu is explicitly checked even for empty covers. Exact row/origin/certificate semantics unchanged; transitive reviewed circular generator checks are not a new independent geometric oracle.")

# Existing unchanged test helpers: reviewed their reported expressions as
# fixture construction or invocation of the system under test, not new oracles.
OLD_TEST_HELPERS = {
    "test_e5a2_interlock_bridge": "_pair",
    "test_end_to_end_cb2": "_capacity",
    "test_interlock_sensitivity": "_steep_two_branches_in_report_band",
    "test_interlocking": "_scaled_pair",
    "test_invariance_interlock": "_ilock _escape _resolution _tia_kink_offset _ilock_pair _margin_pair_for_name _margin_ref",
    "test_invariance_limit": "_transform _reference",
    "test_limit": "_block_on_ground _interlock_capacity _flat_block_ratio",
    "test_limit_arch": "Arch.problem",
    "test_limit_contacts": "_hovering_block",
    "test_limit_duality": "_assert_duality _pure_cohesion _asym_cohesive_block",
    "test_limit_exact_selfcheck": "slide",
    "test_limit_flat_arch": "_problem",
    "test_limit_fuzz": "_exact_status_alpha _genuinely_unresolvable _case",
    "test_limit_multi": "_stack_2d _row_2d _stack_3d _stack_plus_far _stack_cohesive_2d",
    "test_limit_scale": "_interlock_covers _capacity_ratio _block _cb2_at _site_block _g6_rock_block",
    "test_limit_selfcheck": "_box _utm_block _tipping_2d",
    "test_lp_certificates": "_old_formulation _exact_limit_lp _assert_same_exact_limit_result _exact_alpha _block _lock_case _nmm_block _si_case _floor",
    "test_lp_fail_loud": "_cohesive_block _si_block",
    "test_m4_bdda_adapter": "_window",
    "test_margin_penetration": "_interlock_case",
    "test_perf_surface_witness": "_inputs",
    "test_r10_resolution": "_unbounded",
    "test_r13fixb_readers_oracles": "_adapter_mixed_coordinate_gate",
}
for stem, names in OLD_TEST_HELPERS.items():
    review(f"tests/{stem}.py", names,
           "Existing runtime test setup or tested-API invocation, unchanged source; transitive call graph now encounters the new certified cone/angle/reader domain checks. Floating fixture coordinates and reported candidate values define supplied inputs, not a new exact oracle guarantee. Existing LP shared-model certificate comparisons remain such; no claim that a shared generator proves circular-model containment.")
review("tests/test_r13fix_mechanics_differential.py",
       "test_public_friction_generators_round_complete_component test_public_3d_friction_generators_follow_exact_given_coefficient_model",
       "Original full candidate component rational oracle and parameter grid retained. Out-of-mu-domain case now requires named rejection, not dropped. Final physical direction adds independent exact cone containment and bounded correction; subtraction between actual and reference outputs is intentional test error measurement, not production construction.")
review("tests/test_r13fixb_readers_oracles.py", "_mutate test_cone_coefficient_domain_guard_has_teeth",
       "Existing internal source mutation migrates to the actual eager and property angle-domain guards. Each literal replacement must occur exactly once; unequal replacement list lengths reject. Module-local inspect/compile/exec is test-only injection, not a production dispatch waiver. Original 2^-1074 input and DID NOT RAISE assertion remain, production is first checked to reject; all original Taylor grid/error and domain assertions unchanged.")
review("tests/test_r14_cone.py",
       "test_two_d_final_generator_uses_the_nearest_safe_one_ulp_neighbor test_two_d_final_generator_uses_the_nearest_safe_one_ulp_neighbor.safe test_two_d_neighbor_removal_is_caught_by_the_unchanged_near_lock_gate",
       "New 2D oracle independently constructs completed candidate components in Fraction and final RN, then checks cone membership with exact determinant instead of production dot/norm primitives. The public 2D caller itself passes those RN candidates to certification, so distance-to-initial in oracle matches the selected production model. Neighbor enumeration preserves finite values and nonzero signs; exact candidate ordering is not floating geometry branching. Internal source mutation removes real neighbor branch and inspects the caught traceback to require the unchanged old near-lock closed-form error assertion, not incidental status or uncertainty failure.")
review("tests/test_r14_dual.py",
       "<module> _mutated_function test_r14_integer_power_keeps_exact_parity test_r14_half_integer_power_keeps_exact_fraction test_r14_trig_removed_lossless_check_mutation_is_caught",
       "New parity oracle uses exact integer signs; float(exponent) is only the expected final RN derivative display. Deliberately lossy float mutation is injected into actual function body and must red the target gate. inspect/compile/exec operate on test-local source strings, not production permissive dispatch.")
review("tests/test_r14_readers.py",
       "<module> _record_literal _internal_mutant test_reader_keeps_full_binary64_output_domain_not_d400",
       "Test JSON literal builder preserves exact source token; independent Fraction and standard RN expected output checks full reader domain. Source compile/exec deliberately mutates internal conversion statements and expects the named exception assertion to fail, restoring bindings. This test-only reflection is not a production admission rule.")
review("tests/test_r14_tool_readers.py",
       "<module> _invoke _copied_bb52 _replace_csv_field test_r14_tool_removed_exact_numeric_boundary_is_caught test_r14_m4_cs1_bare_float_mutation_is_caught",
       "Runtime export-tool fixture driver: creates exact decimal JSON/CSV tokens only under pytest tmp_path. SimpleNamespace/lambdas are explicit local stubs; subprocess/sibling entry is monkeypatched so no external process or sibling write occurs. Calls exercise actual public tool decoding paths; expected underflow/overflow classification is independent rational token magnitude. Bare float is a deliberately reintroduced decoder mutation required to red the exact-boundary gate, not production admission.")
review("tests/test_r14_showcase.py", "<module> _builder _expected_load",
       "Test-only builder extracts exactly the existing tools/showcase.py arch_problem AST into an explicit namespace, avoiding gallery/plot side effects; optional string edits are targeted internal mutations. Independent Fraction shoelace area and first moment compute the complete gravity/moment polynomial; float occurs only on the final expected outputs over three bounded exponent cells, not on reference inputs or intermediate geometry. Not a production dynamic-code exemption.")

IMPORTS = ["..numeric_domain:exact_input", "..numeric_domain:ConstructionDomainError",
           "..readers.numeric_decode:integer", ".readers.numeric_decode:decode_tree",
           ".readers.numeric_decode:integer", ".readers.numeric_decode:loads", ".readers.numeric_decode:scalar",
           ".numeric_decode:decode_tree", ".numeric_decode:integer", ".numeric_decode:loads", ".numeric_decode:scalar",
           ".numeric_domain:check_mu", "eab.numeric_domain:binary64_argument"]


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
                          "reason": row["reason"] + " R14 local renewal: " + note,
                          "review_evidence": "reports/codex/R14FIX_evidence/static_review.json"}
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
            serial = max((int(r["id"].removeprefix("R14-L")) for r in policy["waivers"]
                          if r["id"].startswith("R14-L")), default=0) + len(added) + 1
            row = dict(id=f"R14-L{serial:04d}", path=path, function=fn, rule=rule,
                       node=ast.dump(node,include_attributes=False), context=gate._subset.site_contexts(text)[fn],
                       category="RUNTIME_TEST_ORACLE_REVIEW" if path.startswith("tests/") else "LOCAL_NUMERIC_OR_PROTOCOL_REVIEW",
                       reason="Specific node: "+code+". "+note,
                       review_evidence="reports/codex/R14FIX_evidence/static_review.json")
            identity=tuple(row[k] for k in ("path","function","rule","node","context"))
            if any(tuple(r[k] for k in ("path","function","rule","node","context"))==identity for r in policy["waivers"]+added):
                continue
            added.append(row)
        policy["waivers"].extend(added)
        assert len({r["id"] for r in policy["waivers"]}) == len(policy["waivers"])
        write(POLICY,policy)
        write(HERE/"static_review.json",[r for r in policy["waivers"] if r["id"].startswith("R14-") or "R14 local renewal:" in r["reason"]])
        print("explicit added site reviews",len(added),"total",len(policy["waivers"]))
    else:
        raise ValueError(mode)


if __name__=="__main__":
    main()
