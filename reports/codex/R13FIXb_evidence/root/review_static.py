"""Local, explicit review ledger maintenance; NEVER called by the AST gate.

Only listed source scopes and R13FIXb test oracles may be reviewed. New syntax
does not gain general admission. Each approved site retains AST and source pins.
"""
import ast
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
POLICY = ROOT / "tools/exact_construction_policy.json"
spec = importlib.util.spec_from_file_location("r13b_static", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

REVIEWS = {}


def review(path, names, reason):
    for name in names.split():
        REVIEWS[path, name] = reason


review("src/eab/construction.py", "<module> scalar_rational ratio_rational vector_rational sqrt_rational norm_rational unit_rational normalized_difference_rational",
       "Checked exact construction boundary: Fraction input and complete expression; scalar/root final rounding plus named range errors. normalized_difference candidate subtraction remains heuristic only, followed by exact midpoint proof. R9 and R13b domain gates.")
review("src/eab/numeric_domain.py", "<module> ConstructionDomainError ConstructionDomainError.__init__ exact_input check_input check_inputs float_algebra",
       "Central domain protocol: finite float check, exact Fraction magnitude comparison, named exception only; builtin type classifier never consumes a rounded magnitude. Not a geometry predicate or new static proof rule.")
for path in ("src/eab/kernel2d/geom.py", "src/eab/kernel3d/geom3.py", "src/eab/kernel3d/exact_geom.py"):
    review(path, "<module> add sub mul dot cross", "Raw builtin real path now completes Fraction algebra then rounds once. Exact-only and Dual/custom protocol fallback retained; only the stated scalar families are contracted. R13b mixed-vector and old E5a2 compatibility gates.")
review("src/eab/kernel3d/geom3.py", "Polyhedron.face_noise Polyhedron.dihedral_noise _extended_edge_length",
       "Extended-range 53-bit per-edge radical model, exact rational perimeter/Newell square then final root. 2u+u^2 relative bound, not correctly-rounded sum of radicals; infinity only pre-existing degenerate geometry sentinel. R13b squared independent bound gates.")
review("src/eab/kernel3d/exact_geom.py", "orient2 normal triangle_locate point_segment_distance_squared segment_triangle",
       "Predicate/construction inputs explicitly lifted to Fraction before determinant and quotient; exact topology is not restricted by engineering envelope.")
review("src/eab/dual.py", "<module> Dual.const Dual.seed Dual._pair Dual.__add__ Dual.__sub__ Dual.__mul__ Dual.__truediv__ Dual.__rtruediv__ Dual.__pow__ Dual.__lt__ Dual.__le__ Dual.__gt__ Dual.__ge__ _derivative_float _ratio_derivative _product_derivative val is_exact_zero central_difference convergence_order",
       "Algebraic jets use complete rational formulas; access/comparison does not coerce exact values. General noninteger power and log diagnostic retain documented coefficient approximation and remain inventory gaps, not certified transcendental arithmetic. Callback finite differences use declared sampled-value model. New R13b channel and range gates plus migrated old underflow contract.")
review("src/eab/margin.py", "<module> rounding_floor _rounding_floor_exact effective_geom_tol _effective_geom_tol_exact cover_witness contact_resolution boundary_band _witnesses",
       "Complete rational tolerance expression uses given rounded-length diagnostic model, not ideal geometric threshold; witness difference lifted before norm. These diagnostic quantities do not decide exact geometry.")
review("src/eab/kernel3d/interlock.py", "<module> _candidates _candidates_uncached escape_candidates escape_height_covers _escape_solution",
       "Internal extent/tie windows remain exact Fraction, even below binary64, rather than constructing a zero tolerance. Comparisons form complete rational products/differences/ratios; exact sweep root and final height construction are unchanged. Cache includes the actually used helper identity. Public floating tolerance reports remain range checked.")
review("src/eab/kernel3d/interlock.py", "escape_height_brute dilatancy_profile",
       "Unchanged callers of escape_height_covers now transitively see the exact-window helper. Brute entry remains a shared-predicate secondary reference, not independent oracle; legacy dilatancy sampled-profile outer arithmetic is outside this repair and not newly certified by this site waiver.")
review("src/eab/limit.py", "<module> LimitContact.__post_init__", "Finite check only converts builtin floats; arbitrary finite int/Fraction values remain exact. Certificate-backed LP displays retain their distinct semantics; no solver modification.")
review("src/eab/limit_multi.py", "<module>", "Module documentation only: references numerical domain and distinguishes LP certificate displays from finite constructed quantities.")
review("src/eab/kernel2d/g0.py", "<module> sample_translations random_convex_polygon", "Random draw is a supplied binary64 coefficient; exact affine combination rounds only output. Random polygon is approximate generated input, not geometric oracle truth; scale domain is checked.")
review("src/eab/kernel2d/g0_oracle.py", "<module> turn segment_square", "Reference determinant/distance uses Fraction-lifted raw inputs; independent of production geometry.")
review("src/eab/kernel3d/g03.py", "<module> sample_translations3", "Sampled RNG coefficients enter exact affine combinations before final checked coordinate rounding.")
for path, names in (("src/eab/kernel3d/g03_exact.py", "<module> _lift_binary64 minus scalar wedge"),
                    ("src/eab/kernel3d/g03_surface_oracle.py", "<module> _lift_binary64 minus dot cross")):
    review(path, names, "Independent oracle raw binary64 inputs rationalised before polynomial arithmetic; exact-only existing path retained. No shared tested geometry primitive.")
review("src/eab/kernel3d/entrance3.py", "<module> first_entrance_brute first_entrance_brute.state", "Secondary brute reference uses exact translation and rational time bisection with binary64 adjacent endpoints, not length-versus-time stopping; it remains a secondary oracle, not an independent production membership proof.")
review("src/eab/adapters/bdda2d.py", "<module> load_window Bdda2DWindow.cone_tol", "Input conversion uses named checked scalar boundary. Cone angle has engineering guard and platform libm coefficient model; generic libm error proof remains explicit gap.")
review("src/eab/oracle_construction.py", "<module> _round_positive", "Independent rational midpoint oracle retains algorithm and only upgrades range exception type; not shared with production construction implementation.")
review("src/eab/readers/bdda3d.py", "<module> record_from_entrance", "Numeric fields checked at final reader conversion; exact integer identifiers never pass through float. Reader classification remains legacy exported-code mapping.")
review("src/eab/readers/bdda_df.py", "<module> _read_csv read_contacts_csv read_df18_csv load_records", "CSV numeric field conversion through checked rational scalar; textual df18 table deliberately untouched until numeric load. Exact integer IDs bypass binary64.")
review("src/eab/readers/bdda_geom.py", "<module> strip_duplicate_vertices strip_duplicate_vertices.same load_step_geometries", "Duplicate comparison uses exact coordinate differences and explicit rational window; coordinate reading final checked scalar. Existing alias and canonical vertex data are structural.")
review("src/eab/readers/tf_probe.py", "<module> _rows", "Named checked construction at reader numeric boundary; exported classification/count fields remain integer data.")
review("src/eab/adapters/bdda2d.py", "_record detect_step", "Existing call chain now sees explicit angle-domain guard in metadata. It retains legacy libm coefficient semantics and corresponding inventory limitation, not an exact sine claim.")
review("src/eab/kernel2d/g0.py", "g0_convex", "Existing caller of newly rationalised sample_translations; sampled coordinates are constructed once and then used as supplied input, not hidden approximation in a geometric oracle.")
review("src/eab/kernel3d/geom3.py", "_point_segment_distance _distance_to_face_polygon", "Each point is explicitly exact_vector lifted before exact_geom distance squared. Raw float alternatives in that helper are unreachable from this call; distance selection takes minimum final rounded nonnegative lengths, not a derived rounded square.")

TEST_FILES = {"tests/test_r13fixb_domain.py", "tests/test_r13fixb_dual_margin.py",
              "tests/test_r13fixb_kernel_numeric.py", "tests/test_r13fixb_readers_oracles.py"}
review("tests/test_r6fix_geom3.py", "test_r6fix_mutation_rounding_squared_norm_is_caught",
       "Existing mutation restored to raw float sum(x*x): deliberately wrong early square injected into real norm. Keeps original nonzero representable-norm assertion, instead of being intercepted by newly checked dot. Not production admission.")
review("tests/test_r7fix_geom3.py", "test_g6g08_internal_mutation_rounding_before_cross_product_is_caught",
       "Existing mutation injects raw float cross product into the real mass-property weight statement. Fraction only transports the already corrupted value, retaining the original axis-product-volume assertion and scale. String injection is test-only.")
review("tests/test_r9fix_normalized_input.py", "test_normalized_difference_float_nn_mutant_hits_target_assertion",
       "Existing normalized-difference mutant follows the renamed exact input statement, keeping the original early squared-norm fault and target midpoint assertion. No production rule change.")
review("tests/test_m4_bdda_shadow.py", "test_legacy_reader_shifted_column_is_rejected_by_independent_raw_identity test_legacy_reader_shifted_column_is_rejected_by_independent_raw_identity.shifted_column",
       "Existing test mutation wrapper now forwards validate_numeric keyword. Its internal p1 <- p2 shift and independent legacy p1 identity assertion remain unchanged; adapter bookkeeping only.")
review("tests/test_interlock_escape.py", "_check_escape",
       "Unchanged runtime regression helper invokes the tested escape API then compares provided analytic truth and frozen derivative reports. Transitive exact-threshold call is not an oracle proof by sharing production construction.")
review("tests/test_interlock_exact.py", "_assert_exact_wall",
       "Unchanged runtime gate compares exact escape height with its separate wall reference; this particular call invokes the tested API, not expected-value construction.")
review("tests/test_invariance_geom.py", "body_distance",
       "Existing explicit legacy contact-window wrapper, now transitively using exact internal max before the checked public report. No change to exact default or to invariance test inputs.")
review("tests/test_invariance_interlock.py", "body_distance _escape _resolution _tia_kink_offset",
       "Existing invariance drivers and legacy reporting-band test setup use the revised checked diagnostic API. These runtime approximate comparison windows are not promoted to primary exact geometry oracles; source is unchanged.")
review("tests/test_margin_penetration.py", "_check_monotone_contact_resolution",
       "Unchanged regression explicitly opts into legacy report band only on the separated side; penetrating side stays default exact. This is a tested call, not shared expected geometry.")
review("tests/test_margin_resolution.py", "_expected _assert_distance _assert_margin_consistent",
       "Existing legacy-window consistency helpers intentionally consume the declared diagnostic threshold to test that report model. They are secondary consistency checks, not independent exact-oracle coverage for the 138-item ledger.")
TEST_REASON = ("R13b runtime test driver/independent oracle: Fraction/Decimal reference or text fixture, deliberate float final comparison, executable source mutation or assertion. This specific test site is not a production exact-construction guarantee; test docstring states independent primitives.")


def reason(path, fn):
    return TEST_REASON if path in TEST_FILES else REVIEWS.get((path, fn))


def write(path, data):
    # Policy baseline is LF; do not turn every unchanged line into a diff on Windows.
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    mode = sys.argv[1]
    if mode == "renew":
        renewed, removed, kept = [], [], []
        parsed = {}
        for row in policy["waivers"]:
            if row["path"] not in parsed:
                text = (ROOT / row["path"]).read_text(encoding="utf-8-sig")
                parsed[row["path"]] = (gate._subset.site_contexts(text),
                    {ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(text))})
            contexts, nodes = parsed[row["path"]]
            if contexts.get(row["function"]) == row["context"] and row["node"] in nodes:
                kept.append(row)
                continue
            note = reason(row["path"], row["function"])
            assert note, ("UNREVIEWED stale scope", row["path"], row["function"])
            if row["node"] not in nodes:
                removed.append(row)
            else:
                update = {**row, "context": contexts[row["function"]],
                          "reason": row["reason"] + " R13FIXb local renewal: " + note,
                          "review_evidence": "reports/codex/R13FIXb_evidence/root/static_review.json"}
                renewed.append(update); kept.append(update)
        policy["waivers"] = kept
        # Specific reviewed imports, not a new AST form or automatic wildcard.
        imports = [".numeric_domain:ConstructionDomainError", ".numeric_domain:exact_input",
                   "..numeric_domain:check_input", "..kernel2d.geom:EPS", "..kernel2d.geom:ROUND_C",
                   "eab.numeric_domain:ConstructionDomainError", "eab.numeric_domain:exact_input",
                   "eab.numeric_domain:check_input", "eab.numeric_domain:check_inputs",
                   "eab.numeric_domain:float_algebra", "eab:numeric_domain", "dataclasses:asdict",
                   "..margin:_effective_geom_tol_exact", "..margin:_rounding_floor_exact"]
        added = sorted(set(imports) - set(policy["imports"]))
        policy["imports"] = sorted(set(policy["imports"]) | set(imports))
        write(POLICY, policy)
        write(HERE / "static_renewals.json", {"renewed": renewed, "removed": removed, "imports_added": added})
        print("renewed", len(renewed), "removed", len(removed), "imports", len(added))
        return
    if mode in ("scan", "scan-local"):
        if mode == "scan-local":
            paths = sorted({p for p, _ in REVIEWS} | TEST_FILES)
            issues = [i for path in paths for i in gate.scan_text((ROOT/path).read_text(encoding="utf-8-sig"), path, repository_root=ROOT)]
        else:
            issues = gate.scan_repository(ROOT)
        write(HERE / "static_pending.json", issues)
        print("issues", len(issues))
        print(json.dumps(Counter(f"{p}::{f}::{r}" for p, _, f, r, _ in issues), indent=2))
        return
    assert mode == "approve"
    issues = json.loads((HERE / "static_pending.json").read_text(encoding="utf-8"))
    added = []
    for path, line, fn, rule, code in issues:
        note = reason(path, fn)
        assert note and rule != "closed-stale-waiver", ("UNREVIEWED site", path, fn, rule, code)
        text = (ROOT / path).read_text(encoding="utf-8-sig")
        nodes = [n for n in ast.walk(ast.parse(text)) if getattr(n, "lineno", None) == line
                 and ast.get_source_segment(text, n) == code]
        if not nodes:
            # Legacy pass renders some expressions with ast.unparse.
            nodes = [n for n in ast.walk(ast.parse(text)) if getattr(n, "lineno", None) == line
                     and ast.unparse(n) == code]
        assert nodes, ("Cannot pin exact node", path, line, fn, rule, code)
        node = min(nodes, key=lambda n: isinstance(n, ast.Expr))
        serial = sum(r["id"].startswith("R13b-") for r in policy["waivers"]) + len(added) + 1
        row = {"id": f"R13b-L{serial:04d}", "path": path, "function": fn, "rule": rule,
               "node": ast.dump(node, include_attributes=False), "context": gate._subset.site_contexts(text)[fn],
               "category": "RUNTIME_TEST_ORACLE_REVIEW" if path in TEST_FILES else "LOCAL_NUMERIC_OR_PROTOCOL_REVIEW",
               "reason": "Specific node: " + code + ". " + note,
               "review_evidence": "reports/codex/R13FIXb_evidence/root/static_review.json"}
        identity = tuple(row[k] for k in ("path", "function", "rule", "node", "context"))
        if any(tuple(r[k] for k in ("path", "function", "rule", "node", "context")) == identity
               for r in policy["waivers"] + added):
            continue
        added.append(row)
    policy["waivers"].extend(added)
    write(POLICY, policy)
    write(HERE / "static_review.json", [r for r in policy["waivers"] if r["id"].startswith("R13b-")])
    print("explicit site reviews", len(added), "total", len(policy["waivers"]))


if __name__ == "__main__":
    main()
