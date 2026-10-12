"""Use ASCII semantic descriptions without changing extracted source inventory."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "review/notes/tolerance_inventory.json"
data = json.loads(path.read_text(encoding="utf8"))
reasons = {
    "speed_filter_exact_fallback": "A floating sign is accepted only outside an error bound; inconclusive and nonfinite cases fall back to rational arithmetic. Two-dimensional finite independent scans passed; this is not an all-input formal proof.",
    "legacy_answer_changing_noise": "Documented historical floating diagnostic API, not an exact production answer. Its live use in nonconvex G0 was independently confirmed to skip strict samples.",
    "float_construction_or_exact_helper": "Floating normals, areas and constructed points are displays; triangulation orientation and hull predicates use exact arithmetic. Construction accuracy is not automatically guaranteed.",
    "confirmed_g0_answer_changing_noise": "Confirmed G2D-01 and G2D-02: implicit 1e-12*L screening skips strict near-boundary samples, or returns an incorrect first exit. This is not a caller-selected window.",
    "confirmed_float_underflow_oracle": "Confirmed G2D-03 proof: a nonzero segment squared length underflows, projection is replaced by an endpoint, and the distance oracle is incorrect.",
    "exact_or_sampling_metadata": "Convex G0 uses rational predicates with no band skipping; other comparisons are sampling, counting, independent support, or independent hull metadata.",
    "float_construction_report": "Only chooses a floating construction for normals on the same exact facet direction; does not choose membership or entrance state.",
    "explicit_domain_window_or_exact": "Caller-selected length, angle, or membership windows are compared using original rational coordinates; zero-window predicates are exact and no rounding floor is added.",
    "exact_decision_resolvability_only": "Times, selected labels and distances used for selection are rational. Bands only affect near_labels. A separate confirmed gap construction underflow does not change those exact choices.",
    "sampling_corroboration_not_oracle": "Documented sampled corroboration with shared production predicate; short crossings or isolated tangency can be missed. Bisection termination only controls display resolution.",
    "exact_or_float_construction": "Rational feature data and input validation, or floating witness construction; inspect the enclosing function rather than inferring dynamic operand type from AST.",
    "exact_predicate": "Comparisons operate on Fraction or integer expressions. No implicit noise-band branch was found in this exact module.",
    "exact_predicate_static": "Rational or integer layer. Positive tol is an explicit reporting band. Three-dimensional complete dynamic verification belongs to the separate review lens.",
    "heuristic_with_exact_candidate_certification": "Floating LP thresholds choose a candidate only; solve subsequently certifies the original rational model and falls back to rational simplex. Root LP review checks actual fallback behavior.",
    "exact_certificate_or_metadata": "Rational certificates or exact simplex, with floating display and iteration metadata. This child review did not dynamically certify every path.",
    "resolution_or_explicit_force_display": "U thresholds report resolvability only. tol*fmax truncates documented display forces and active labels, not the exact certificate model. Root review audits the model and selfcheck.",
    "construction_fail_closed_or_window_report": "Floating discrepancies audit or repair constructed witnesses; relation and minimum squared-distance decisions are separate rational computations. Not all constructions were independently tested here.",
    "explicit_report_policy": "Tolerance helpers expose optional report policies; tie grouping is a legacy display convention in explicit window mode, not default exact geometry.",
    "root_confirmed_public_projection_cancellation": "Root independently confirmed public margin projection error: a global floating nearest point loses a small rational gap at engineering coordinates, giving distance zero and normal None. This is not an allowed contact window.",
    "exact_domain_window_static": "Rational local predicates and integer squared comparisons, with explicit tol, extent_tol and window. Other values are constructions or metadata; full 3D dynamic proof belongs to the 3D lens.",
    "exact_convex_g0_static": "Convex votes use independent integer or rational oracles and exact tested convex views. Full three-dimensional oracle-independence review belongs to the separate lens.",
    "legacy_diagnostic_or_dormant_noise_static": "Historical floating convexity or topology diagnostic, or helper replaced by exact surface overlap. This child review did not prove absence of every possible remaining caller.",
    "construction_heuristic_exact_fallback": "Small angular separation, nonfinite intermediates or underflow use rational segment distance. General branch still constructs floating distances; not exhaustively scanned by this child review.",
    "legacy_float_oracle_shared_primitives": "Legacy feature oracle projects in floating arithmetic and classifies rounded projections. It is used for construction auditing, not the final default exact minimum selection; shared primitives remain a review risk.",
    "exact_forward_or_construction_static": "Overlap, hull and merging forward to exact layers. Other comparisons concern geometric constructions or work ordering. Enclosing function context must be checked.",
    "nominal_report_resolution_or_exact_event": "Noise suppression and clustering affect nominal candidate reports or compatibility labels; exact escape uses independently enumerated rational surface events and exact roots.",
    "sampling_legacy_band_corroboration": "Documented legacy floating scan with geometry band and display stopping scale. It is corroboration, not an independent principal oracle or an isolated-event guarantee.",
    "exact_event_or_float_report_static": "Exact event roots, labels and merging, or floating displays with explicit angle windows. This child review did not prove every three-dimensional path.",
    "primal_branch_analytic_dual_path_static": "Frozen analytic path and primal orientation/domain branches. No complete child dynamic verification; root and 3D reviewers own this scope.",
    "legacy_adapter_simplification": "Documented adapter normalization raises dup_tol to a coordinate rounding floor and may remove actual short edges even at requested zero. Do not confuse normalized input with original-data exactness.",
    "parsing_contract_or_adapter": "Parsing, type/length contracts, mappings or explicit legacy adapter policy. Not independently dynamically verified for geometry by this child review.",
    "scalar_branch_no_tolerance": "Primal scalar branches, channel validation and mathematical domain checks; no noise-band policy found.",
    "static_unverified": "Extracted statically but not independently dynamically verified."
}
for key in ("comparisons", "tolerance_candidates"):
    for row in data[key]:
        row["classification_basis"] = reasons.get(row["category"], reasons["static_unverified"])
data["limitations"] = [
    "Every Compare is extracted, but dynamic Python operand types cannot be proved from AST. Classification is at enclosing-function level, not independent dynamic proof of each expression.",
    "Deep child coverage is kernel2d, predicates and the default margin decision chain; 3D, LP and limit static classifications must be merged with other reviewers' evidence.",
    "No all-input formal error-bound proof was performed. Finite exact differential scans do not prove absence of all counterexamples."
]
encoded = json.dumps(data, ensure_ascii=False, indent=2)
assert "??" not in encoded
path.write_text(encoded, encoding="utf8")
