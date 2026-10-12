"""Index remaining constructor/contract/reader comparison families.

Manual source-family classifications recorded after reading these modules;
not a claim of exhaustive dynamic proof or a replacement for numeric replays.
"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
rows=json.loads((ROOT/'review/evidence/all_source_comparisons.json').read_text('utf-8'))
excluded=('src/eab/kernel','src/eab/limit','src/eab/lp','src/eab/dual','src/eab/predicates')
remaining=[r.copy() for r in rows if not r['file'].startswith(excluded)]
for row in remaining:
    module=row['file'].split('/')[-1]
    scope=row['scope']
    label='discrete_identity_type_or_structure_control'
    rationale='Source read: branch concerns identity, field presence, enum/type or integer count; no implicit geometric answer band.'
    if module=='construction.py':
        label='exact_rational_integer_rounding_or_named_final_range_boundary'
        rationale='Rational/integer root or RN midpoint comparisons; scalar float==0 detects unrepresentable output and raises, not tolerance-adjusted answer.'
    elif module=='oracle_construction.py':
        label='independent_rounding_cell_certificate_or_candidate_selection'
        rationale='Float/Decimal supply candidate; exact rational midpoint cell certification or full bit search decides final RN view.'
    elif module=='numeric_domain.py':
        label='exact_explicit_support_domain_or_type_dispatch'
        rationale='D400 comparisons use Fraction; constructor rejection/type dispatch does not narrow pure predicates. Entry coverage failures N01/N02/N03 are separately reproduced.'
    elif module=='bdda2d.py' and scope=='_boxes_may_meet':
        label='exact_explicit_legacy_search_window'
        rationale='Coordinate bounds and reach are Fraction; caller declares legacy d0/df convention, not hidden noise. Narrowphase follows.'
    elif module=='bdda2d.py' and scope=='Bdda2DWindow.__post_init__':
        label='declared_window_input_validity'
        rationale='Finite/positive/degree range validation; h1/d0/h5 are declared adapter model inputs.'
    elif module=='bdda_geom.py' and scope.endswith('.same'):
        label='documented_legacy_reader_canonicalization_band_exact_comparison'
        rationale='Near duplicate stripping is an explicit dump-normalization model with declared eps*C floor; comparison itself exact Fraction. Not advertised as default pure geometric predicate.'
    elif module=='margin.py':
        label='exact_source_distance_or_discrete_branch'
        rationale='Default relation, minimum and delta use exact source squared distance; no implicit band. Full source read by primary reviewer.'
        if scope in ('_tie_groups','body_distance','margin_contacts'):
            label='exact_default_with_explicit_window_display_tie_policy'
            rationale='Exact default minimum/classification retained; float tie ordering only in explicitly selected contact_window report mode. Source certificates decide contact/closed.'
        elif scope=='_resolve' and '4.0 * rnd' in row['comparison']:
            label='display_construction_error_check_not_geometric_truth'
            rationale='Exact minimum squared equals independent feature value separately; float witness tolerance audits output construction only. It may reject loudly, cannot replace exact relation.'
        elif scope in ('effective_geom_tol','_effective_geom_tol_exact','rounding_floor','_rounding_floor_exact','contact_resolution','boundary_band'):
            label='declared_diagnostic_window_model'
            rationale='Legacy/report constructor, not implicitly called to widen default truth. Final RN range rejection includes U-GEOM-RANGE execution-contract ambiguity.'
        elif scope=='_contact_window':
            label='explicit_caller_window_validity'
            rationale='None/zero selects exact mode; finite nonnegative window validity only.'
        elif scope=='cover_witness':
            label='display_witness_construction_not_default_distance_oracle'
            rationale='Distance after display-point rounding is audited separately; exact source distance and gap orientation govern real public classification.'
        elif scope=='MarginContact.closed':
            label='exact_closed_certificate_or_user_manual_display_fallback'
            rationale='Production records carry _exact_closed; only user-created records without certificate use supplied display gap.'
    elif module=='contact_record.py':
        rationale+=' Naked float conversion in _decode and early JSON parse loses data (confirmed N03); a Compare-only scan cannot certify constructors.'
    elif module=='bdda3d.py':
        rationale+=' Checked scalar final boundary exists but actual numeric JSON parse precedes it (confirmed N03).'
    row.update(root_audit_class=label,rationale=rationale,verification_level='manual_source_function_family_review')
(ROOT/'review/evidence/root_branch_review.json').write_text(json.dumps({
    'comparison_rows':len(remaining),'rows':remaining,
    'limitation':'Comparison-family classifications do not prove all dynamic inputs correct; conversion bugs have independent entry-path counterexamples.'},ensure_ascii=False,indent=2),encoding='utf-8')
print('ROOT_BRANCH_REVIEW',len(remaining),'constructor/reader/contract/margin Compare nodes')
