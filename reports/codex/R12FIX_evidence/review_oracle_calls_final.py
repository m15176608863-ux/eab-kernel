"""Finite, source-read human review of non-test-driver oracle call sites.

This ledger does not update scanner policy and is not a numerical proof.
"""
import collections
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
rows = json.loads((BASE / 'test_final_waiver_review.json').read_text())
reasons = {}


def group(path, descriptions):
    for function, reason in descriptions.items():
        reasons[path + '::' + function] = reason


group('tests/e5a2_entrance_oracle.py', {
    '_cross': 'Integer determinant components of exact common-denominator coordinates. No conversion or norm construction occurs.',
    '_canonical': 'gcd normalization divides an integer axis exactly with // and fixes sign using its first nonzero integer; the output is an equivalent integer direction, not a rounded unit vector.',
    '_model': 'Lifts every supplied coordinate/velocity to Fraction, clears their common positive lcm denominator into exact integers, and forms integer triple/chord SAT axes. No intermediate float constructor participates.',
})
group('tests/e5a2_surface_oracle.py', {
    '_ring_triangles.orient': 'The captured v table contains projected Fraction coordinates; orient is the two-dimensional determinant polynomial used for ear cutting, without conversion or a numerical callback.',
    '_ring_triangles': 'Test-owned projected ear cutting computes exact orientation/parity on Fraction coordinates and returns existing input vertices, not rounded constructed points.',
    '_tetrahedra.visible': 'Captured planes and point are Fraction values. visible returns all exact strict half-plane scalar comparisons and never constructs a numerical answer.',
    '_tetrahedra': 'Lifts supplied vertices to Fraction, constructs rational candidate centers, certifies strict plane visibility, and returns center-plus-face tetrahedra. Center division stays Fraction; no float conversion is used.',
    '_sat': 'Called after star_overlap clears all positive denominators into integer coordinates. It compares integer projection bounds over exact face and cross-edge axes, returning only -1/0/1.',
    'star_overlap': 'Uses test-owned rational tetrahedra then exact integer SAT on every tetrahedral pair. Its return is a state, not a constructed float; no production primitive is shared.',
})
group('tests/e5a_convex_oracle.py', {
    'canonical_payload.same_cycle': 'Only checks cyclic equality of integer face-index sequences, preserving labels; this local function does no numerical construction.',
    'canonical_payload': 'The reviewed payload invokes the independent g03 exact hull to select/reindex existing raw input vertices and face labels. No new vertex coordinate or rounded geometric witness is constructed.',
})
group('src/eab/kernel3d/g03_exact.py', {
    'qpoint': 'Exact Fraction lifting of each supplied coordinate, not a floating approximation.',
    'hull': 'Reviewed hull lifts inputs to Fraction, clears common denominators into integers, finds support facets with integer determinants and verifies every support sign. It returns original rational points and rational planes rather than rounded coordinates.',
})

cover = {
    'model': 'The actual model lifts coordinates through q/Fraction before cyclic Newell sums, edge differences and adjacency. Its normals and directions remain rational; no unit-vector rounding is fed into later geometry.',
    '_model': 'Only freezes supplied verts/faces as tuples and calls the reviewed Fraction model; no numerical conversion is inserted.',
    'outside': 'A sign and squared inequality against Fraction(tol)**2; it avoids a square root or normalized approximate direction and returns a boolean.',
    'vertex': 'Reads rational model edge directions, evaluates exact dot/sign and outside squared-band checks, and returns a cone membership state. It does not construct a rounded direction.',
    'arc': 'Reads rational edge/Newell data, uses determinant signs and Gram coefficients for exterior rays, and applies squared tolerance comparisons. Return is a state, not a normalized float.',
    'face_extent': 'Projects the rational point and ring onto coordinate axes and uses exact determinant/parity comparisons; no floating geometry construction is introduced.',
    'strict_cone': 'Gordan-ray search rescales rational constraints by their rational max component, forms exact cross products and exact cone signs. It returns feasibility and does not normalize via a rounded Euclidean norm.',
    'cover_labels': 'Tuple/cache wrapper for the exact local-cover label enumerator. It returns label/strictness records, not float coordinates.',
    '_cover_labels_cached': 'Reviewed exact local-cover enumeration: model lifting precedes rational Gram solves, vertex/arc signs, projection extent and Gordan rays. Results are labels and boolean strictness only.',
    'witness_points': 'Reviewed Gram/projection witness helper preserves Fraction points for exact=True. Its default vector_exact is explicitly a terminal display output; recursive FV/EV3 calls forward exact=exact, and every distance caller requests exact=True before norm.',
    'witness_distance': 'Calls witness_points(exact=True), subtracts the rational coordinates, and only then calls norm_exact once. It does not subtract already displayed points.',
}
group('tests/e5a_cover_oracle.py', cover)
group('tests/perf_cover_oracle_reference.py', cover)
group('tests/e5a_cover_oracle.py', {
    '_margin_witness_distance': 'Retains exact witnesses for planar/nonface features; folded faces use test-owned ear cutting and rational squared point/triangle distance before a single sqrt_exact output.',
    'assert_margin_gap_rounding.compare': 'Captured squared and delta are Fraction. The helper compares the exact signed radical to a rational midpoint by sign-checked squaring and returns -1/0/1; no square root is evaluated.',
})

escape = {
    'face_band': 'The actual helper first runs exact projected face extent, then rational clamped point-edge projection and squared distance against Fraction(extent)**2. It returns a boolean without rounding a witness.',
    'parameter_band': 'Compares exact segment parameter and rational direction squared length with the supplied legacy extent squared. It does not take a norm of a rounded direction.',
    'facet': 'Reviewed local facet helper uses rational model coordinates and Gram parameters. exact_coefficients=True returns retained rational normal/numerator; extent_only=True returns a rational extent decision without constructing unused display gaps. Default normal and signed gap are separate terminal displays from retained exact data.',
    'unit': 'Calls independent unit_exact on the retained rational direction only for a terminal displayed normal. Cone decisions use the original direction; the explicit legacy nz cutoff is at least 1e-12, not a claim about subnormal components.',
    '_signed_gap': 'Forms the rational numerator squared divided by rational normal squared before sqrt_exact, and retains exact numerator sign. A displayed normal is never used to reconstruct this distance.',
    'norm': 'This fixed wrapper directly calls independent norm_exact. In geometry_noise/windows, the supplied vector may already be the declared legacy float-difference diagnostic; those caller scopes are explicitly exempt, not asserted to be exact geometric reconstruction.',
    'geometry_noise': 'EXPLICIT LEGACY SCOPE EXEMPTION: reproduces the declared face/edge uncertainty report. Raw float coordinate subtraction and already displayed lengths can enter this diagnostic; it is not a principal exact-geometry oracle and is not claimed to meet the exact-construction theorem.',
    'direction_noise': 'EXPLICIT LEGACY SCOPE EXEMPTION: combines the declared geometry_noise diagnostics and reports angular uncertainty, including documented infinity saturation. It cannot certify an exact distance; local geometry coefficients are separately retained as Fraction.',
    'windows': 'EXPLICIT LEGACY SCOPE EXEMPTION: computes documented floating extent/rounding policy from supplied vertices, which may include float subtractions. This is a legacy policy comparison, not an exact numerical oracle.',
    'candidates': 'EXPLICIT LEGACY SCOPE EXEMPTION: tuple/cache entry to legacy candidate-window policy. Exact local facet signs are separate from this deliberately historical floating height/tie selection policy.',
    '_candidates': 'EXPLICIT LEGACY SCOPE EXEMPTION: historical candidate height/extent cache and window policy. It uses exact local facet coefficients, constructs output height once, then treats that displayed height as a new supplied pose for extent checks. This must not be represented as an exact earliest-escape oracle.',
}
group('tests/e5a_escape_oracle.py', escape)
group('tests/perf_escape_oracle_reference.py', escape)
group('tests/e5a_escape_oracle.py', {
    'move': 'Lifts both supplied point and offset components with Fraction before affine addition. At the later displayed candidate height this is a new supplied pose model, not recovery of its unrounded ideal root.',
})
group('tests/perf_escape_oracle_reference.py', {
    'move': 'EXPLICIT LEGACY SCOPE EXEMPTION: this frozen performance reference intentionally reproduces the callers rounded translation p+offset, as its source comment states. That rounded pose is input to the reference comparison, not a principal exact-affine oracle.',
})

group('tests/e5a_g2_oracle.py', {
    'support_sets': 'Exhaustive rational support triples use test-owned q/cross/dot on supplied vertices and return vertex-index sets. No production hull or rounded normal enters the support test.',
    'assert_exact_hull': 'Asserts the actual face-index sets equal independently enumerated rational support sets, and exact outward signs hold. This is a boolean/topology assertion boundary, not a new numeric construction.',
    'construction': 'Reviewed G2 construction retains model coordinates and Gram solutions as Fraction. distance_squared=True returns exact numerator**2/dot(n,n). Display gap and normal are independently constructed from those exact values, never from one another.',
    '_unit': 'Terminal independent unit_exact display from retained rational n; selection and distance use the exact n separately.',
    '_distance_display': 'Terminal independent bit-pattern/midpoint-certified sqrt_exact of an already exact squared distance, with no scalar narrowing first.',
})
group('tests/e5b_frozen_oracle.py', {
    'surface': 'Tuple/cache wrapper for the reviewed exact folded-surface representation; does not change coordinates.',
    '_surface': 'Lifts every coordinate to Fraction, tests exact Newell coplanarity and splits only folded rings through independent rational ear clipping. Existing rational vertices and source labels are returned, without constructing rounded points.',
})
group('tests/e5b_margin_oracle.py', {
    '_cover_squared': 'Uses independent rational folded-surface models and exact Newell/Gram/Gordan label paths; all feature squared distances are rational expressions returned without a root or float conversion.',
    'cover_squared': 'Freezes input tuples and materializes the reviewed exact squared-distance pairs as a dict. It does not convert values to displayed distances.',
})
group('tests/e5b_wall_oracle.py', {
    'triangles': 'Lifts all supplied vertices to Fraction before invoking the test-owned projected ear cutter; returns rational triangles.',
    '_interval': 'Uses integer triangle SAT axes and exact Fraction projection-time ratios to return strict/closed collision intervals. No root/norm or approximate motion coordinate participates.',
    'inside': 'Independent rational Moller-style parity rays use Fraction direction and exact barycentric/time ratios, explicitly exclude boundary and reject degenerate rays. Return is boolean, not a display point.',
    '_earliest': 'Clears positive coordinate denominators exactly, unions rational SAT intervals, and certifies boundary/right-neighborhood noncontainment with independent parity. The root and verification poses remain Fraction; no rounded exit height enters the proof.',
    '_star_root': 'Clears common rational denominators into integers, derives strict tetrahedral swept SAT intervals by exact Fraction ratios and unions them. Returned earliest root remains Fraction.',
})
group('tests/perf_sweep_reference.py', {
    '_descriptor': 'Exact cross/dot coplanarity selects only source face/triangle labels. This frozen performance reference intentionally shares exact production primitives, not an independent geometric oracle.',
    '_point_edge_time': 'On rational supplied reference data it computes cross/dot ratios for exact time and segment parameter and returns a rational time tuple. No displayed point or time is used in the solve; this is a shared-primitive equivalence reference.',
    'reference_events.put': 'Stores supplied rational time/normal and tuple label in SurfaceEvent after exact interval filtering; no conversion occurs. This is a frozen algorithm equivalence record boundary.',
})
group('src/eab/kernel3d/exact_sweep.py', {
    'SurfaceEvent': 'The actual dataclass is only fields time: Fraction, label: tuple, normal: tuple. Constructor stores exact supplied event fields unchanged; no hidden rounding method is defined.',
})
group('src/eab/kernel3d/exact_geom.py', {
    'triangle_locate': 'Reviewed exact helper uses retained rational cross/dot plane and edge signs to return -1/0/1. This call is shared deliberately by the frozen performance reference, not an independent geometry oracle.',
    'point_segment_distance_squared': 'Reviewed exact helper computes a clamped Fraction projection and rational residual squared without display conversion. It is a shared performance-equivalence primitive, not an independent expected geometry formula.',
    'triangulate': 'Reviewed helper first vector-lifts supplied vertices to Fraction, then performs rational projected ear cutting and returns index triangles. No constructed float coordinates enter the reference event formula.',
    '_triangle_bounds': 'Only selects componentwise min/max of already rational triangle vertices. No arithmetic narrowing or numerical callback is used.',
    '_split_polygon': 'Reviewed arrangement splitter evaluates rational signed distances and rational plane-intercept ratio a/(a-b), returning exact rational cell vertices. It introduces no floating point constructor.',
    '_point_in_triangles': 'Reviewed parity helper clears positive denominators into exact integers, checks integer boundaries and counts rational ray crossings. It returns only exact -1/0/1 membership state.',
    '_inward_sample': 'Computes exact rational positive plane-intercept ratios and takes half the first step; returned point remains rational, with no epsilon ladder or float conversion.',
    '_coplanar_interior_witness': 'Uses exact rational inward sample and exact membership checks, returning the retained rational witness or None. In this callsite the shared primitives are explicitly an equivalence reference, not a G0 oracle.',
})

reviewed = []
for row in rows:
    row['review_boundary'] = 'Human candidate only; require full module AST and all src/tests/tools source-graph pins. No automatic policy refresh.'
    if not row['needs_review'] or row['path'].startswith('tests/test_'):
        continue
    reason = reasons.get(row['resolved_callee'])
    if row['path'] == 'tests/e5a_cover_oracle.py' and row['callee'] == 'math.copysign':
        reason = 'Reads only the sign bit of the already returned float for the independent signed-underflow assertion. The magnitude is constant 1.0; this does not reconstruct a norm.'
    if row['path'] == 'tests/e5b_margin_oracle.py' and row['function'] == 'check_exact_margin':
        if row['callee'].startswith('production.'):
            reason = 'Explicit actual-API invocation in check_exact_margin, not generation of the expected answer. The caller compares it to independently computed Fraction squared distances, exact midpoint certificates and exact inclusion states; production does not supply those expected quantities.'
        elif row['callee'] == 'assert_sqrt_rounding':
            reason = 'Actual binding is construction_oracle re-export of eab.oracle_construction.assert_sqrt_rounding. Read implementation checks exact Fraction lower/upper midpoint squares and RN-even parity against the actual float; it does not construct a shared expected root.'
            row['resolved_callee'] = 'src/eab/oracle_construction.py::assert_sqrt_rounding (via tests/construction_oracle.py re-export)'
    if reason:
        # The scope exemption is explicit even when this particular callee is
        # exact: its consumer is a deliberately historical float policy.
        legacy = row['path'] in ('tests/e5a_escape_oracle.py', 'tests/perf_escape_oracle_reference.py') and row['function'] in ('geometry_noise', 'direction_noise', 'windows', 'candidates', '_candidates', 'tied_labels')
        legacy |= row['path'] == 'tests/perf_escape_oracle_reference.py' and row['callee'] == 'move'
        if legacy and 'EXPLICIT LEGACY SCOPE EXEMPTION' not in reason:
            reason += ' Caller scope is an EXPLICIT LEGACY SCOPE EXEMPTION: a documented floating noise/window/candidate policy comparison, not a principal exact-geometry oracle.'
        row.update(reason='Finite source review of '+str(row['resolved_callee'])+': '+reason, status='reviewed_candidate', needs_review=False, scope_exemption=legacy)
        reviewed.append(row)

for name, data in (
    ('test_oracle_final_call_review.json', reviewed),
    ('test_final_waiver_review.json', rows),
    ('test_final_needs_review.json', [r for r in rows if r['needs_review']]),
    ('test_legacy_oracle_scope_exemptions.json', [r for r in reviewed if r.get('scope_exemption')]),
):
    (BASE/name).write_text(json.dumps(data, ensure_ascii=True, indent=2)+'\n', encoding='utf-8')
print('oracle calls reviewed:', len(reviewed))
print('legacy explicit scope sites:', sum(r.get('scope_exemption',False) for r in reviewed))
print('remaining non-driver helpers:', collections.Counter(r['path'] for r in rows if r['needs_review'] and not r['path'].startswith('tests/test_')))
print('overall:', collections.Counter(r['status'] for r in rows))
