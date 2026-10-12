"""Materialize fixed-site arithmetic/data reviews; never refresh policy itself."""
import ast
import contextlib
import io
import json
from pathlib import Path
import runpy
from collections import Counter

BASE = Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):
    previous = runpy.run_path(str(BASE / 'build_src_final_review.py'))
model = previous['model']
old = previous['old'] + json.loads((BASE / 'src_final_waiver_review.json').read_text(encoding='utf-8'))
by_code = {(r['path'], r['function'], r['code']): r for r in old}
old_rows = json.loads((BASE / 'final_raw_scan.json').read_text(encoding='utf-8'))
old_keys = {(r[0], r[2], r[3], r[4]) for r in old_rows}
rows = [r for r in json.loads((BASE / 'final_raw_scan_v2.json').read_text(encoding='utf-8'))
        if r[0].startswith('src/') and (r[0], r[2], r[3], r[4]) not in old_keys]

def context_for(path, function):
    category, context = model(path, function)
    module = path.removeprefix('src/eab/').removesuffix('.py')
    if ((module == 'kernel2d/geom' and function in {'round_floor', 'angle_floor', 'turn_floor'})
            or (module == 'kernel3d/geom3' and function in {'noise_floor', 'Polyhedron.dihedral_noise', 'Polyhedron.edge_noise'})):
        return ('diagnostic-noise-model',
            'This current helper computes a reporting/noise estimate, not an exact geometric '
            'predicate or an exact original-data constructor. Where a squared rational '
            'quantity is used, the final root is still delayed; the diagnostic role itself '
            'is an explicit scope exemption rather than a proof of exact geometry.')
    if module in {'kernel2d/geom', 'kernel3d/geom3'} and function in {'add','sub','mul','cross','dot'}:
        return ('reviewed-polymorphic-arithmetic-primitive',
            'This primitive has both supplied-floating and rational callers. It is not '
            'universally exact: floating arithmetic is the declared floating API result. '
            'Reviewed exact-construction callers provide Fraction relative data (3d dot/cross '
            'dispatch to rational3); their full caller graph is frozen. This site does not '
            'authorize feeding a newly rounded primitive result into a norm.')
    if module == 'limit' and function == '_tangents':
        return ('declared-contact-tangent-model',
            'n/tangent and the projection/squared threshold are Fraction values before '
            'unit construction. The explicit model then defines t2 from n crossed with '
            'the returned binary64 t1, completing each cross product exactly after '
            're-rationalization. This declared second direction is not a claim to recover '
            'an ideal unrounded t1; the existing specific model exception is preserved.')
    if module == 'limit_multi' and function == '_centroid':
        return ('reference-point-selection-not-geometric-truth',
            'This floating average selects a mechanical reference point only. Exact '
            'wrench shifts use original point coordinates and the chosen reference point '
            'in Fraction arithmetic, so no ideal centroid is silently substituted for '
            'the original mechanical input. It is not an exact geometric centroid API.')
    if module == 'lp' and (function.startswith('_Revised.') or function in {'_float_solve','_natural_scales','_ray_verifies','_ray'}):
        return ('floating-lp-candidate-only',
            'These arithmetic/reduction expressions belong to the floating simplex, '
            'candidate pricing/pivot/residual filters, or candidate ray display. They '
            'are not asserted exact. Final status/witness acceptance still requires '
            '_Exact original-Fraction certification or the exact-simplex fallback; '
            'the complete acceptance path is frozen.')
    return category, context

def attribute_reason(code, path, function, context):
    try:
        attribute = ast.parse(code, mode='eval').body.attr
    except (SyntaxError, AttributeError):
        return 'pending', 'Attribute expression requires a further individual review.'
    if attribute in {'numerator','denominator'}:
        return ('fraction-integer-components',
            'This fixed access reads integer numerator/denominator data from the '
            'reviewed Fraction operand. It does not invoke a float constructor or '
            'read hidden runtime call frames. ' + context)
    if code == 'sg.canon':
        return ('fixed-reader-index-method-reference',
            'This is the fixed StepGeometry.canon bound-method reference used to '
            'canonicalize integer dump vertex IDs, not a numerical construction '
            'callback. The receiver class, consumers and method body are frozen.')
    if attribute in {'v','e','width'} and path.endswith('/dual.py'):
        return ('declared-dual-channel-data',
            'Reads the supplied floating primal/channel tuple or its discrete width. '
            'No claim is made that these channels are exact hidden geometry; '
            'subsequent derivative construction retains the reviewed model. ' + context)
    if attribute in {'verts','vertices','faces','poly','blocks','source_faces','source_vertices'}:
        return ('fixed-geometry-model-data',
            'Reads the actual geometry/topology record: original supplied binary64 '
            'coordinates or the explicitly exact translated model, plus integer '
            'rings/source IDs. The access itself performs no conversion. Exact '
            'constructors rationalize these actual data before relative products. ' + context)
    if attribute.startswith('exact') or attribute in {'raw','derivatives','_exact'}:
        return ('fixed-exact-certificate-field',
            'Reads the frozen record/wrapper field carrying its exact certificate, '
            'raw rational expression or derivative data. The defining class and '
            'writers are frozen; no global admission of this attribute spelling or '
            'arbitrary descriptor is implied. ' + context)
    if attribute in {'normal','point_a','point_b','gap','point','height','x','y','alpha','mechanism','mechanisms','margin_gap','value'}:
        return ('fixed-model-or-output-field',
            'Reads a declared input or completed output field of the actual record. '
            'Such fields may be binary64 displays; they are not all exact intermediates. '
            'The caller-specific exact certificate/original-coordinate route, or the '
            'explicit reporting role, is described below and remains frozen. ' + context)
    return ('fixed-record-cache-or-state-field',
        'The specific receiver is the baseline record/cache/solver/topology object '
        'and this field contains data or discrete state. Its property implementation '
        '(if any), writers and consumers are included in the frozen source graph. '
        'This is not admission of arbitrary same-named fields or runtime frames. ' + context)

def review(row):
    path, line, function, rule, code = row
    category, context = context_for(path, function)
    reused = by_code.get((path, function, code))
    if reused:
        category = 'reused-fixed-expression-' + reused['category']
        reason = reused['reason']
    elif rule == 'closed-data-attribute':
        category, reason = attribute_reason(code, path, function, context)
    elif rule == 'closed-runtime-reflection':
        approved = {
            ('src/eab/dual.py','Dual.__rsub__','(-self).__add__'):
                'Calls the fixed Dual arithmetic implementation on a negated Dual; '
                'it does not retrieve runtime annotations, defaults, globals or hidden storage.',
            ('src/eab/kernel3d/frozen.py','_FrozenNormal.__new__','super().__new__'):
                'Allocates the frozen tuple wrapper whose rational raw/derivative fields '
                'are then retained; this is object allocation, not a numeric conversion.',
            ('src/eab/limit.py','_ExactFloat.__new__','super().__new__'):
                'Allocates the displayed float subclass only after checked construction; '
                'the original exact witness is separately retained and immutable.',
            ('src/eab/limit.py','_ExactFloat.__new__','object.__setattr__'):
                'Initializes the immutable exact witness on the already allocated '
                'display wrapper; no callable replacement or hidden rounding is performed.',
        }
        reason = approved.get((path,function,code), 'Unreviewed runtime reflection; do not admit.')
        category = 'fixed-wrapper-protocol' if (path,function,code) in approved else 'pending'
    elif rule == 'closed-syntax':
        category = 'terminal-message-or-discrete-label-formatting'
        reason = ('This reviewed formatting expression produces an exception/report/repr '
            'string or a discrete source/dump-field label. Its formatted output is not '
            'reparsed as Fraction/float or fed to a numerical constructor. The small '
            'format-spec nodes belong to those same terminal diagnostic strings.')
    elif rule == 'closed-modulo':
        if path == 'src/eab/lp.py' and function == '_Revised.optimize':
            category = 'floating-candidate-perturbation-remainder'
            reason = ('This is deliberately floating modulo for the candidate simplex '
                'perturbation schedule, not integer arithmetic and not formatting. '
                'It only changes the float candidate search; original-data exact '
                'certification/fallback decides the answer. ' + context)
        else:
            category = 'integer-index-or-parity-modulo'
            reason = ('The operands at this fixed site are integer ring/feature indices, '
                'integer bit/parity/significand metadata, or bounded discrete iteration '
                'indices. This is integer remainder, not printf-style numeric formatting '
                'or mixed Fraction/float arithmetic. ' + context)
    elif rule == 'closed-reduction':
        category = 'fixed-reduction-' + category
        reason = ('This sum site has been reviewed with its actual iterator and initial '
            'value: exact-model paths sum Fraction/integer terms, while float candidate, '
            'reference-selection or diagnostic paths are explicitly limited by the '
            'following model. It does not admit arbitrary future mixed-type sums. ' + context)
        if path == 'src/eab/limit.py' and function == 'limit_load' and code.startswith('sum(ct.point'):
            category = 'floating-reference-point-selection'
            reason = ('This sum is a floating average used only to select the internal '
                'mechanical reference point. It is not an exact centroid construction. '
                'Exact load/contact wrench shifts subsequently use the original inputs '
                'and this chosen reference point in Fraction arithmetic; source data '
                'are not replaced by averaged values. The exact LP remains reference '
                'independent under the frozen model.')
    elif rule == 'closed-unproved-arithmetic':
        category = 'fixed-arithmetic-' + category
        reason = ('This precise expression is outside the analyzer\'s literal-integer '
            'type proof and is admitted only under the frozen actual model below. '
            'Integer indices/counts, tuple/list assembly and type-union annotations '
            'do not round geometric values; numerical expressions retain the model\'s '
            'exact/Fraction or explicitly candidate/display/diagnostic role. No '
            'name-based type inference or general arithmetic waiver is granted. ' + context)
    else:
        category, reason = 'pending', 'Unclassified new rule; do not admit.'
    return dict(path=path,line=line,function=function,rule=rule,code=code,category=category,
        reason='Reviewed fixed site '+path+'::'+function+'. '+reason,
        review_boundary='Exact AST/module and complete src/tests/tools dependency snapshot must match; manual baseline admission, not a machine proof or transferable arithmetic/attribute summary.')

reviewed = [review(r) for r in rows]
pending = [r for r in reviewed if r['category']=='pending']
(BASE/'src_positive_subset_review.json').write_text(json.dumps(reviewed,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(BASE/'src_positive_subset_pending.json').write_text(json.dumps(pending,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('new source sites',len(reviewed),'pending',len(pending))
print(Counter(r['rule'] for r in reviewed))
