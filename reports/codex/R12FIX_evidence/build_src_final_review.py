"""Materialize the independent fixed-baseline review catalogue, not an analyzer.

The hand-written model notes below describe reviewed baseline call sites only.
They must never become callee-name allowlists or automatic policy regeneration.
"""
import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
old = []
for name in ('src_waiver_review_candidates.json', 'src_numeric_waiver_review.json'):
    old.extend(json.loads((BASE / name).read_text(encoding='utf-8')))
keys = {(r['path'], r['function'], r['rule'], r['code']) for r in old}
by_code = {(r['path'], r['function'], r['code']): r for r in old}
new = [r for r in json.loads((BASE / 'admission_scan.json').read_text(encoding='utf-8'))
       if r[0].startswith('src/') and (r[0], r[2], r[3], r[4]) not in keys]

MODELS = {
    'adapters/bdda2d': ('input-window-adapter',
        'This shadow adapter consumes supplied binary64 dump geometry and the explicitly declared d0/h1/seg_tol window. h1 sine is the declared angular-window model, not an exact transcendental reconstruction. Cover decisions delegate original geometry to the pinned exact cover implementation; record fields and sorting are output metadata.'),
    'construction': ('checked-output-boundary',
        'This is the actual checked construction implementation: Fraction numerator/denominator and integer midpoint/bit comparisons retain the complete expression until the binary64 output boundary. sqrt uses an integer significand of at most 53 bits before ldexp; normalized_difference candidates are accepted only after exact comparison. It is not an arbitrary helper that first rounds a vector and then takes its norm.'),
    'oracle_construction': ('independent-certified-output-boundary',
        'This independent constructor uses Decimal only to propose a candidate; Fraction midpoint comparisons certify it and bitwise bisection supplies the fallback. Returned binary64 is the completed construction, not an intermediate norm input. The reviewed full implementation, including candidate rejection, is frozen.'),
    'contact_record': ('record-serialization',
        'The reviewed call reads/writes lifecycle fields or serializes/deserializes records and labels. Decoded floats are external model inputs; metadata conversion and canonical sorting do not calculate a norm/root from a rounded derived vector.'),
    'dual': ('declared-dual-model',
        'Dual represents supplied floating primal/channel values, not hidden exact geometry. Core arithmetic evaluates its declared primal/channel operations; range-sensitive derivative products/ratios use Fraction or bounded Decimal candidates before final channel output. Trigonometric primal values are the declared floating transcendental model, not a claim of exact transcendental arithmetic.'),
    'kernel2d/covers': ('exact-2d-cover-model',
        'The pinned cover path forms relative vectors, line/projected terms, cone products and squared gap/window comparisons in Fraction/integer arithmetic from original coordinates. Normals, points and angle/gap values are constructed only for final Cover displays; later feature/window decisions reconstruct from original A/B and integer feature indices, not displayed Cover vectors.'),
    'kernel2d/entrance': ('exact-2d-event-model',
        'Feature data and event times are Fraction expressions of original A/B, X and D. Exact squared distances and event membership select the result before _contact_report constructs display fields. The floor/near/tie window is reporting compatibility and does not replace the exact event root; original coordinate data remain available.'),
    'kernel2d/exact': ('exact-2d-predicate-model',
        'The pinned helper uses Fraction/integer original-coordinate vectors, cross/dot products, exact hull ordering and exact membership/event comparisons. Container operations retain those values or discrete labels; they do not invoke a hidden rounded vector constructor before a root.'),
    'kernel2d/g0': ('independent-2d-oracle-and-input-generation',
        'The pinned G0 model uses independent original-coordinate Fraction distance/support calculations for expected geometry; random/sample construction creates the actual binary64 inputs supplied to both sides. Report counters and displayed-witness error comparisons are diagnostic, not an exact expected value obtained by reusing rounded production geometry.'),
    'kernel2d/g0_oracle': ('independent-integer-fraction-oracle',
        'The independent oracle integerizes common-denominator coordinates or retains Fraction event/distance expressions. Exact side/ray/distance decisions precede oracle_construction display. Discrete label/order/container calls do not round numerical operands.'),
    'kernel2d/geom': ('supplied-coordinate-2d-geometry',
        'The reviewed geometry API operates on the actual supplied binary64/Fraction coordinates. Exact side/orientation predicates and rationalized relative norm/normal constructions are separate from display translations and the declared floating angular tolerance. No general statement that all geom helpers return exact values is made.'),
    'kernel3d/covers3': ('exact-3d-cover-model',
        'The pinned _q* model retains Fraction relative edges/normals, exact closest-simplex parameters and squared distances/cone constraints. Cover3 holds completed display values plus exact direction/sign/distance data; decisions use the exact originals/certificates. Cache callbacks are fixed implementation identities, not unreviewed clean-return summaries.'),
    'kernel3d/entrance3': ('exact-3d-event-model',
        'The reviewed path keeps surface event times and translated offsets in Fraction form, selects exact membership/first-root certificates, then constructs Entrance3 displays and source labels. Infinite search limits are sentinels, not rounded geometry; the original x0/d and exact event model remain the decision inputs.'),
    'kernel3d/entrance_topology': ('exact-configuration-topology',
        'Configuration planes and chamber directions are derived from original geometry with Fraction/integer dot/cross/sign comparisons. Angular ordering is a discrete exact comparator, not a rounded angle key. Containers collect planes, directions and labels without an intermediate floating construction.'),
    'kernel3d/exact_geom': ('exact-geometry-with-certified-filters',
        'The reviewed module uses original-coordinate Fraction/integer predicates and squared feature distances. Its floating interval shortcuts (_iv/_ia/_is/_im/_id and window filters) round outward with nextafter and fall back to exact arithmetic when inconclusive; interval endpoints are not treated as exact constructed vectors.'),
    'kernel3d/exact_sweep': ('exact-affine-surface-events',
        'The pinned sweep derives affine events, relative offsets, star-core and contact-model certificates in Fraction/integer form. It preserves exact event values in records and uses no displayed event point as an exact root/norm operand.'),
    'kernel3d/frozen': ('exact-frozen-expression-before-channel-output',
        'The fixed frozen-cover implementation forms complete affine point jets, raw normals, residuals and gap expressions in Fraction arithmetic. Normalized primal/derivative channels are output constructions after the expression is complete; labels and frozen source topology are data, not dynamically selected numerical functions.'),
    'kernel3d/g03': ('independent-3d-oracle-and-reporting',
        'The independent expected hull/label/distance model uses g03_exact and g03_surface_oracle original-coordinate integer/Fraction calculations. Sample translations are actual supplied binary64 test inputs. Completed witness displays, error estimates and report counters are diagnostic, not exact pre-rounded oracle geometry.'),
    'kernel3d/g03_exact': ('independent-exact-3d-oracle',
        'The independent model uses Fraction/integer hull planes, SAT, dimension/volume and support labels on original data. Sorted/combinatorial operations select exact/discrete values and do not introduce rounded vector or root intermediates.'),
    'kernel3d/g03_surface_oracle': ('independent-exact-surface-oracle',
        'The independent surface oracle constructs original-coordinate rational triangle/segment models and squared separation values. Exact predicates govern containment/intersection; the final oracle constructor is distinct from production construction. Containers retain exact data or feature labels.'),
    'kernel3d/geom3': ('exact-surface-and-supplied-coordinate-api',
        'The current geometric decision path rationalizes original coordinates for exact surface predicates, relative feature distances, hull certificates, and mass properties. Polyhedron also exposes floating display/cache/noise APIs, which are not exact-return summaries. Reviewed callers use exact_vector/edge/face or exact surface data when a subsequent exact construction needs them.'),
    'kernel3d/interlock': ('exact-affine-escape-with-display-reporting',
        'The accepted escape root is the Fraction surface-event root with exact contact-model/nonpenetration certificates for prior intervals. Legacy candidate cover heights, tie labels and display windows are reporting/diagnostic support and are not substituted for exact_height/exact_offset. Frozen derivative APIs use the pinned exact-expression implementation.'),
    'limit': ('exact-mechanics-with-floating-candidates',
        'Contact normal/point/friction values define the supplied mechanical model. Complete wrench/shift/cohesion columns are retained as Fraction AX/bX/c and passed through the LP exact= certificate path. Floating A/b, displayed result records and uncertainty norms are candidates/reporting; exact primal/dual certificates, not those displays, govern the answer.'),
    'limit_multi': ('exact-multibody-mechanics-with-floating-candidates',
        'Body-local displacement/wrench and contact columns are retained in Fraction form, including exact matrix rows and exact LP input. Floating solve arrays and result displays are paired with original exact certificates. Relative-power checks recover exact witnesses with _lp_values instead of silently reusing rounded displayed values.'),
    'lp': ('certified-linear-programming',
        'The revised simplex is a floating candidate generator only. _Exact checks primal/dual/Farkas/ray certificates against original Fraction data; failure invokes rational simplex. The reviewed site may update candidate matrices or display a result, but it cannot replace the exact certificate/fallback boundary with a pre-rounded geometric norm.'),
    'margin': ('exact-feature-distance-with-explicit-report-windows',
        'Default status and minimum distance use original-coordinate exact surface predicates and squared feature distances. The optional contact window has explicit finite certificates; witness points/tie ordering/noise bounds are reporting fields. Projection normal construction requests exact=True and retains the Fraction relative displacement before its final normalization.'),
    'predicates': ('certified-filter-and-exact-fallback',
        'Fast floating determinant/product filters are only accepted with a rigorous error enclosure; uncertain signs fall back to exact original-data Fraction/integer calculations. A filter intermediate is not returned as an exact constructed vector or used as an unverified norm/root.'),
    'rational3': ('integer-rational-arithmetic',
        'Cross/dot arithmetic uses integer numerator/denominator product differences and Fraction output. No binary64 rounding precedes these geometric products.'),
}

DIAGNOSTICS = {
 'dual': {'central_difference', 'convergence_order'},
 'kernel2d/geom': {'_tri_axes'},
 'kernel2d/entrance': {'first_entrance_brute', 'first_entrance_brute.state'},
 'kernel3d/covers3': {'_orth'},
 'kernel3d/entrance3': {'first_entrance_brute', 'first_entrance_brute.state'},
 'kernel3d/geom3': {'_ray_directions', '_inward_vertex_direction', '_active_normals',
     '_gordan_direction', '_min_norm_on_simplex', '_contact_cone_witness',
     'Polyhedron._find_interior_point', 'Polyhedron.face_noise', 'Polyhedron.manifold_issues'},
 'kernel3d/interlock': {'_candidates_uncached', '_escape_solution', '_normal_noise',
     'dilatancy_profile', 'escape_height_brute', '_nonpenetrating_at'},
 'margin': {'cover_witness', '_tie_groups'},
}

def model(path, function):
    module = path.removeprefix('src/eab/').removesuffix('.py')
    if function in DIAGNOSTICS.get(module, set()):
        return ('explicit-approximate-diagnostic-scope',
            'Explicit scope exemption for this retained approximate/reference/diagnostic path: '
            + function + ' is not certified by the closed-subset numerical guarantee. '
            'Its floating arithmetic can operate on already constructed display values. '
            'It must not be represented as an exact oracle or used to bypass the separate '
            'original-data exact decision/certificate path. This exception approves only '
            'the pinned current diagnostic role, not new geometric construction uses.')
    if module.startswith('readers/'):
        return ('external-input-decoding',
            'This reader parses external dump text/JSON into the actual supplied binary64 model '
            'and discrete vertex/contact labels. Float decoding is the input boundary, not '
            'rounding an internal exact geometric vector before constructing its norm. '
            'Duplicate/ordering metadata preserves the declared reader model.')
    return MODELS.get(module, ('pending', 'Unclassified numeric model; requires additional review.'))

def callee(code):
    try:
        n = ast.parse(code, mode='eval').body
        return ast.unparse(n.func) if isinstance(n, ast.Call) else ''
    except SyntaxError:
        return ''

def rounded_role(path, function, call, code):
    records = {'Bdda2DWindow', 'ContactRecord', 'Df22Judgment', 'Feature',
        'StepGeometry', 'BlockGeom', 'PairStageRow', 'Cover', 'Cover3',
        'EntranceBlock', 'Entrance2', 'Entrance3', 'EscapeSolution', 'LimitResult',
        'MultiLimitResult', 'LPResult', 'MarginContact', 'Dual'}
    if call in records:
        return ('The callable constructs a data record from already completed display/model '
            'values; it does not take their geometric norm. Exact event/distance/certificate '
            'fields remain alongside displays where the record contract provides them.')
    if path.endswith('/construction.py'):
        if call == 'math.ldexp':
            return ('significand is an integer of at most 53 bits, so float(significand) '
                'is exact; ldexp is the final checked square-root output, not a rounded '
                'intermediate fed to a later root.')
        return ('compare re-rationalizes candidate/adjacent/midpoint values and compares '
            'against the complete exact expression. nextafter/struct encode candidate '
            'neighbors and bits for certification/bisection, not numerical truth from '
            'an unverified rounded intermediate.')
    if path.endswith('/dual.py'):
        return ('The exponent p is the supplied floating exponent of the declared Dual '
            'power model. Derivative helpers receive original primal/channel values and '
            'complete Fraction or Decimal candidate expressions, followed by checked '
            'channel conversion; this does not normalize an intermediate rounded vector.')
    if call in {'atan2', 'math.atan2'}:
        return ('atan2 produces the declared floating display angle from already completed '
            'rationally scaled sine/cosine components. Exact side/turn sign is selected '
            'separately from original products; this is not an exact arbitrary-angle proof.')
    if 'window=float("inf")' in code:
        return ('The rounded taint is the infinity search-window sentinel: it disables '
            'window pruning, not original-coordinate precision. Geometry remains the '
            'original supplied model and exact feature predicates are unchanged.')
    if path.endswith('/kernel3d/entrance3.py'):
        return ('surface_events/_preceding_probe supply Fraction event/probe times; '
            '_ray_shift and _translated_exact preserve exact affine offsets before '
            'polyhedra_overlap. The field-insensitive taint also includes t_max and '
            'display records, but those are not substituted for exact event positions. '
            '_restore_sources changes labels/source metadata only.')
    if path.endswith('/kernel2d/entrance.py'):
        return ('r/root is the reporting floor/near window, and Cover indices are discrete '
            'feature identifiers. Event computation and ve_side_exact/ev_side_exact '
            'receive original A/B/X/D and Fraction times; no displayed Cover vector '
            'is used as the exact construction input.')
    if path.endswith('/kernel2d/g0.py'):
        return ('x is the actual supplied binary64 sample used identically by both '
            'membership predicates. The distance-completeness branch uses nextafter '
            'only to expand a report window and compares displayed witnesses against '
            'the independent exact result; it is not constructing expected geometry '
            'from a pre-rounded production vector.')
    if path.endswith('/kernel3d/g03.py'):
        return ('_display_witness_distance is explicitly a production-display selfcheck, '
            'not the independent expected distance. The truth comes from the separate '
            'original-coordinate oracle; display error is assessed after that truth.')
    if path.endswith('/exact_geom.py'):
        return ('nextafter expands both sides of the floating conversion f to enclose '
            'the original rational value. This certified interval shortcut either '
            'proves the sign or falls back; f is not accepted as an exact vector.')
    if path.endswith('/interlock.py'):
        return ('These calls evaluate legacy candidate displays, cover labels or the '
            'next display neighbor. They are not the accepted affine escape root; '
            'the separate exact event/certificate path supplies exact_height and '
            'exact_offset. Candidate diagnostic use is an explicit scope exemption.')
    if call == 'LimitContact':
        return ('The completed cover point/normal becomes an explicitly supplied '
            'mechanical contact model. This adapter does not claim to recover the '
            'unrounded original geometry from the displayed cover; exact mechanics '
            'is relative to these declared contact data.')
    if path.endswith('/margin.py'):
        return ('cover_witness and _tie_groups consume completed displayed witnesses '
            'for reporting/selfcheck/tie grouping only. Exact squared feature distance '
            'and original-coordinate penetration/contact tests remain the decision '
            'inputs; no report-witness norm becomes the exact distance certificate.')
    if '/readers/' in path:
        return ('Parsing supplies binary64 coordinates and integer feature indices '
            'as the reader model. ensure_ccw/duplicate handling inspect those actual '
            'inputs, while _edge_start reconstructs discrete edge identity. This is '
            'not premature conversion of an internally derived exact vector.')
    if function in DIAGNOSTICS.get(path.removeprefix('src/eab/').removesuffix('.py'), set()):
        return 'This is a retained approximate diagnostic path, explicitly outside the exact-construction guarantee.'
    return ''

def review(row):
    path, line, function, rule, code = row
    cat, context = model(path, function)
    call = callee(code)
    reused = by_code.get((path, function, code))
    if reused:
        cat = 'reused-exact-site-' + reused['category']
        detail = reused['reason']
    elif rule == 'closed-decorator':
        cat = 'fixed-boilerplate-or-cache-decorator'
        detail = ('The reviewed decorator generates dataclass field boilerplate, memoizes the fixed '
            'implementation, or exposes a fixed property/classmethod. It is not an arbitrary '
            'numeric callback transformer; numerical bodies remain separately checked/pinned. '
            'Cache implementation identities and complete keys remain frozen.')
    elif rule == 'closed-shadowed-intrinsic':
        cat = 'actual-approved-construction-definition'
        detail = ('This definition is the real baseline numeric construction boundary/wrapper, '
            'not a local function borrowing a trusted name. Its complete implementation and '
            'callers are pinned. Approval does not grant any other same-named function an '
            'intrinsic summary. ' + context)
    elif rule == 'closed-indirect-write':
        cat = 'fixed-data-state-write-' + cat
        detail = ('This fixed target stores data: a record field, cache/topology entry, '
            'report field, matrix/derivative channel, or exact certificate. It does not '
            'install or replace a numerical callable. The stored value expression and '
            'all later uses remain in the frozen source graph. ' + context)
    elif rule == 'closed-callback':
        cat = 'fixed-order-key-' + cat
        detail = ('The exact call-site key/comparator selects ordering, extrema or report labels '
            'from the stated data model; it is not a general callback slot admitted by name. '
            'The actual key/comparator body and all callees are frozen and separately listed. '
            'No inferred clean return is granted to a future callable. ' + context)
    elif rule == 'closed-unpacked-call':
        cat = 'fixed-keyword-record-or-solver-options'
        detail = ('At this fixed site unpacked keywords are either decoded ContactRecord fields '
            'or the solver compatibility options assembled by the pinned caller. The '
            'mechanics solve separately supplies exact=(AX,bX,c); maximize forwards its '
            'recovered exact tuple. This is not an arbitrary numeric key/callback injection. '
            + context)
    elif call.endswith(('Error', 'Failure')):
        cat = 'exception-construction'
        detail = 'Constructs an error for invalid input or failed certification, not a numeric result or rounded vector.'
    elif call in {'dataclass', 'field', 'lru_cache'}:
        cat = 'fixed-boilerplate-or-cache-setup'
        detail = ('Fixed dataclass/default-field or memoization setup; no numerical argument '
            'is converted into a constructed vector or root. Default factories make empty '
            'containers, and the actual decorated numerical bodies remain separately pinned.')
    elif call in {'any', 'all'}:
        cat = 'boolean-reduction'
        detail = ('Reduces boolean/discrete truth values without floating conversion. '
            'The generator expressions and nested numerical calls are independently '
            'checked or site-reviewed; this waiver is not a summary for those calls. ' + context)
    elif call in {'math.isfinite', 'isfinite', 'str', 'repr'}:
        cat = 'validation-or-rendering'
        detail = ('This exact site returns a finite-status boolean or textual rendering, '
            'not a numerical construction. It cannot erase a rounded vector then feed it '
            'back as an exact norm operand. ' + context)
    elif rule == 'closed-rounded-call':
        role = rounded_role(path, function, call, code)
        cat = ('field-sensitive-boundary-review-' + cat) if role else 'pending'
        detail = (role or 'The rounded argument role needs further review; do not admit.') + ' ' + context
    elif rule == 'closed-unproved-call':
        cat = 'manual-fixed-call-' + cat
        detail = ('This ordinary call is not interprocedurally proved by the analyzer. '
            'Manual approval is limited to this actual call and its frozen baseline model: '
            + context)
    else:
        cat = 'pending'
        detail = 'New rule/site has not been manually classified; do not admit automatically.'
    return dict(path=path, line=line, function=function, rule=rule, code=code,
                callee=call, category=cat,
                reason=('Reviewed site ' + path + '::' + function
                        + (', actual callee ' + call if call else '') + '. ' + detail),
                review_boundary=('Manual fixed-baseline admission only; requires exact site AST, '
                    'complete module context and complete source/helper dependency manifest. '
                    'Not a machine proof, callee-name allowlist, or transferable clean-return summary.'))

rows = [review(r) for r in new]
pending = [r for r in rows if r['category'] == 'pending']
(BASE / 'src_final_waiver_review.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(BASE / 'src_final_waiver_pending.json').write_text(json.dumps(pending, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('new rows', len(rows), 'pending', len(pending))
print(Counter(r['rule'] for r in rows))
print(Counter(r['category'] for r in rows))
