"""Finite human operand/domain review for new R12 fail-closed oracle sites.

No policy is changed. These are source-scoped candidates, not inferred types or
formal proofs of arbitrary Python inputs. All src/tests/tools must be pinned.
"""
import ast
import collections
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
old={(r[0],r[2],r[3],r[4]) for r in json.loads((BASE/'final_raw_scan.json').read_text())}
rows=[r for r in json.loads((BASE/'final_raw_scan_v2.json').read_text())
      if (r[0],r[2],r[3],r[4]) not in old and r[0].startswith('tests/') and not r[0].startswith('tests/test_')]
access={(r['path'],r['function'],r['rule'],r['code']):r for r in json.loads((BASE/'test_data_access_review_v2.json').read_text()) if not r['needs_review']}
notes={}


def put(file, fns, model, reason, exemption=False):
    for fn in fns.split('|'):
        notes['tests/'+file+'.py',fn]=(model,reason,exemption)


put('e5a2_entrance_oracle','_sub|_cross|_dot','integer SAT algebra','Reviewed call chain: _model explicitly F-lifts all coordinates/velocity and clears their lcm denominator with exact integer products. These primitive operands are those integer coordinates/directions. Subtraction, multiplication, determinant sums and an integer-zero-start sum remain integers; no division or implicit binary64 is used.')
put('e5a2_entrance_oracle','_canonical','integer direction gcd','The vector is integer SAT data and divisor is math.gcd of its components with an exact sign choice. Every component is divisible by divisor; // produces an exact equivalent integer axis rather than a rounded normalized vector.')
put('e5a2_entrance_oracle','_model','Fraction input lift -> integer SAT','F(c)+F(t) is Fraction addition. x*denominator is Fraction with a denominator cleared by the common lcm; its int conversion is exact, not truncation. a+b+[velocity] is list concatenation and set - {None} removes invalid axes; neither is numerical narrowing.')
put('e5a2_entrance_oracle','convex_overlap|convex_ray_interval','integer bounds + Fraction time','All projected min/max bounds come from integer coordinates and integer dot products. Their differences stay integer; Fraction(lower,speed) constructs exact times. boundary |= comparison accumulates booleans, not numeric approximations.')
put('e5a2_entrance_oracle','assert_supporting_surface','exact integer embedding','Each x was explicitly F-lifted; denominator is the lcm of every x.denominator. x*denominator is an exact integer-valued Fraction before int, preserving support-sign data.')

put('e5a2_surface_oracle','_minus|_times|_scalar','Fraction/integer determinant algebra','The independent surface path F-lifts raw vertices in _tetrahedra and uses Fraction points for distances; star_overlap instead clears all denominators to integers before SAT. At both reviewed call domains these +,-,* determinant operations remain exact and contain no float literals or casts.')
put('e5a2_surface_oracle','_ring_triangles|_ring_triangles.orient','Fraction planar orientation + integer topology','vertices come from F-lifted oracle models; projected v, accumulated normal and orient values stay Fraction. Shoelace sum starts at integer zero and adds Fraction products. sign is +/-1; drop/k/len are integers, modulo wraps indices, and sliced-ring addition is list/tuple concatenation. No integer/int division appears in these sites.')
put('e5a2_surface_oracle','_tetrahedra','Fraction barycentric centers','v and every triangle component are explicitly F-lifted and the geometry has nonempty vertex/triangle sets. Each sum therefore has Fraction terms; division by len(v), 3 or 4 dispatches Fraction division, not int/int. Candidate and accepted centers remain Fraction until exact visibility certification.')
put('e5a2_surface_oracle','_sat','integer SAT projections','star_overlap has exactly cleared all tetrahedron denominators before _sat; min/max projection differences are integer. boundary |= gap==0 only combines booleans.')
put('e5a2_surface_oracle','star_overlap','exact integer SAT embedding','aa+bb concatenates tetrahedron lists. Each x is a Fraction and denominator is the exact common positive lcm, so x*denominator becomes an integer-valued Fraction before int. contact |= comparison is boolean aggregation.')
put('e5a2_surface_oracle','_point_edge_sq|_point_tri_sq|_edge_edge_sq','Fraction closest-feature squared distance','Inputs are Fraction points from the independent surface model. Dot/scalar values uu/nn and projection parameters are Fraction; every quotient therefore remains Fraction, including division by a nonzero squared direction. Residual squared distances are formed before the eventual single sqrt display boundary.')
put('e5a2_surface_oracle','star_relation','exact rational tolerance comparison','F(tol)**2 is rational exponentiation by nonnegative integer 2. Sliced-triangle addition only enumerates cyclic edges; the numerical tests compare exact squared distances with the squared supplied tolerance.')

put('e5a_convex_oracle','canonical_payload.same_cycle','index-sequence concatenation','b[k:]+b[:k] rotates an integer face-index sequence for exact equality; it performs no scalar numerical construction.')

for module in ('e5a_cover_oracle','perf_cover_oracle_reference'):
    put(module,'add|sub|scale','reviewed Fraction core / declared float diagnostic','The principal cover model q-lifts every input coordinate to Fraction before these simple component operations; integer scale factors preserve Fraction. These helpers also deliberately serve the documented floating noise/window comparison, where the supplied floats are not claimed to recover exact geometric intermediates. This dual use is a human-reviewed boundary, not a universal type proof.',True)
    put(module,'dot|cross','reviewed rational core / bit-preserving float reference','In the principal model and witness callers, operands are Fraction (or exact integer) data, so products, sums and determinants remain exact. The explicit old-float compatibility path is exercised by test_independent_oracle_float_fallback_preserves_original_bits and is not an exact-geometry oracle. A sum with integer zero is exact only in the rational call domain; the float path is a declared secondary equivalence scope.',True)
    put(module,'model','Fraction Newell accumulation + integer indexing','v=tuple(map(q,vertices)) converts every component to Fraction before n[k] += (a[u]-b[u])*(a[w]+b[w]). n starts with F(0), so sums stay rational. k/u/w and modulo are integer coordinate indices; face-slice + is only ring concatenation.')
    put(module,'outside|vertex|arc','Fraction cone-sign and squared-band algebra','The model supplies Fraction edges/Newell directions; direction and Gram dot products stay Fraction. tol is explicitly F-lifted before squaring. All listed products/differences have integer exponents and rational operands, so no Fraction*float narrowing or float norm precedes a cone decision.')
    put(module,'face_extent','Fraction projected polygon parity','a,b,p are retained Fraction points. Signed determinants and the parity-ray intercept numerator/denominator are Fraction, with a nonzero denominator selected by the crossing branch. f[1:]+f[:1] only enumerates integer face indices.')
    put(module,'strict_cone','Fraction Gordan-ray normalization','Only reviewed caller is _cover_labels_cached, passing bd/ad from the F-lifted model edge directions. constraints is nonempty and max(abs(g)) is a nonzero Fraction; 1/Fraction is exact Fraction division, not int/int. Rays and nonempty component sums remain Fraction; (F(0),)*3 only replicates a tuple.')
    put(module,'_cover_labels_cached','Fraction Gram/projected witnesses','model F-lifts coordinates before all listed dot products and Gram determinants. aa/ab/bb/aw/bw/den and component residuals are Fraction; divisions by nonzero den or dot(n,n) retain exact projection/line parameters. No displayed normal or coordinate is fed back into these calculations.')
    put(module,'witness_points','Fraction witnesses before final display','_model F-lifts coordinates and Gram coefficients; the listed quotients are Fraction/Fraction. exact=True returns these witnesses directly, while default vector_exact is the terminal display. The distance callers explicitly use exact=True before subtraction/root, so these expressions do not consume already-rounded global points.')
    put(module,'witness_distance','Fraction displacement before norm','a,b come from witness_points(exact=True); x-y is Fraction subtraction. Only the resulting rational displacement enters independent norm_exact, avoiding subtraction of displayed points.')
    put(module,'margin_selection','explicit legacy selection policy with exact feature values','F(v)-F(origin) and F(hi)-F(lo) preserve exact supplied differences for distance construction. The EPS/1e-9/1e-12 products and final ctol sum intentionally evaluate the documented historical floating selection policy, using final displayed lengths. This window policy is explicitly outside the exact-predicate/construction theorem, not a principal exact margin oracle.',True)
put('e5a_cover_oracle','_minor','integer numerator/denominator algebra','cross calls this branch only when every operand is Fraction or int. numerator/denominator fields are exact integers; lcm gives a common denominator, the // factors are exact integers, and the final F(integer,integer) restores a rational determinant without binary64.')
put('e5a_cover_oracle','assert_margin_gap_rounding.compare','exact Fraction midpoint ordering','squared and delta are explicitly Fraction and midpoint comes from exact neighboring-binary64 Fraction averages. rhs*rhs and its difference remain rational; the final boolean subtraction gives integer -1/0/1, never an approximate radical.')
put('e5a_cover_oracle','assert_margin_gap_rounding','Fraction midpoint and unsigned parity','center/previous/following are Fraction lifts (with F(2)**1024 for overflow neighbors). Their division by integer 2 remains Fraction. Unsigned struct.unpack Q %2 is integer significand parity, not formatting or numeric float modulus.')

for module in ('e5a_escape_oracle','perf_escape_oracle_reference'):
    put(module,'_signed_gap','Fraction signed normal gap','n and displacement are retained rational facet data; numerator*numerator/dot(n,n) is Fraction/Fraction. A single sqrt_exact then constructs the magnitude and exact numerator sign is retained separately, never using a displayed unit normal to recompute it.')
    put(module,'face_band|parameter_band|facet','Fraction projection/Gram and extent tests','a/b model coordinates, normals, directions and Gram parameters are Fraction. Each listed quotient/product/square preserves that domain; extent/tol are explicitly F-lifted before numeric comparison. t-1 subtracts integer 1 from Fraction. Ring slice + is only index concatenation. Optional displayed normal/gap are downstream, separate terminal outputs.')
    put(module,'geometry_noise','explicit legacy floating uncertainty diagnostic','64*EPS, perimeter and uncertainty ratios deliberately reproduce the documented historical noise report. norm results are final display values; raw float coordinate differences may already be rounded. sum has float terms here and is NOT claimed to be an exact rational reduction. This diagnostic cannot be a principal exact-distance oracle.',True)
    put(module,'direction_noise','exact final expression of supplied legacy diagnostics','F(ae[ea])+F(be[eb]) explicitly lifts the already-declared diagnostic values. total and the retained exact model dot products are Fraction, so the final squared-ratio expression is exact for those supplied diagnostics before sqrt_exact. The underlying uncertainty policy/infinity saturation remains a legacy scope, not an exact geometry certificate.',True)
    put(module,'windows','explicit legacy floating window policy','The fixed 64*EPS and 1e-9 factors intentionally form the existing display-comparison window from final lengths/coordinate scale. These floating products are a declared policy output, not an exact geometric norm/predicate or a hidden rational conversion.',True)
    put(module,'_candidates','exact local coefficients; legacy displayed-height selection','labels += combines label lists. normal/numerator/nn are retained Fraction facet coefficients; thresholds/rounding are F-lifted before their squared comparisons, and -numerator/normal[2] remains an exact Fraction before the single scalar_exact height output. z-zprev is deliberately on completed binary64 height displays to apply the historical cache/window policy; it is not an exact earliest-root proof.',True)
    put(module,'tied_labels','explicit legacy floating tie policy','r/zh/z/nz/rounding are completed candidate/report displays and analytic-height inputs; these differences/ratios intentionally reproduce the documented float tie window. No exact-distance guarantee is claimed for this policy, and it is distinct from the independent rational earliest-wall/star oracles.',True)
put('e5a_escape_oracle','move','exact affine supplied-data model','Both point and offset are explicitly F-lifted before addition. The addition cannot silently turn Fraction into float. A displayed candidate height later passed as offset is a new supplied pose, not recovery of its unrounded ideal root.')
put('perf_escape_oracle_reference','move','explicit frozen rounded-input model','This performance reference intentionally preserves p[k]+offset[k] as the supplied rounded translation. It is an explicitly declared equivalence/input-model boundary, not the principal exact affine-motion oracle.',True)

put('e5a_g2_oracle','construction','Fraction Gram geometry before independent display','model converts raw coordinates to Fraction; aa/ab/bb/aw/bw and dot products are rational. Squaring uses exponent 2 and every division has rational numerator/denominator, so squared remains exact before independent _distance_display. Constructed normal and gap are never multiplied to reconstruct one another.')
put('e5a_g2_oracle','assert_comparison','rational window; integer labels/counters/sets','Fraction(max(window,band))**2 is an exact square of the supplied binary64 boundary. x/y/z/n are integer vertex identifiers/counts used solely for a malformed-triangle label; count/reconciled increments are integers and legacy-mine/mine-legacy are set differences. No floating root construction occurs in these arithmetic sites.')
put('e5b_frozen_oracle','_surface','Fraction face vectors and topology','points are explicitly Fraction before cross; normal starts with integer zeros and becomes Fraction on adding exact determinant components. face slices + only concatenate index rings.')
put('e5b_frozen_oracle','distance_squared','cyclic rational-triangle enumeration','tri[1:]+tri[:1] concatenates existing rational point tuples to enumerate their edges, without component arithmetic or conversion. The subsequent minimization retains independent rational squared distances.')
put('e5b_margin_oracle','_cover_squared','independent Fraction squared feature distances','surface and covers._model preserve Fraction coordinates. Newell/Gram dot values are Fraction; integer exponent 2 and exact division by nonzero squared directions produce exact feature d2 before any display output.')
put('e5b_margin_oracle','check_exact_margin','exact supplied-threshold squares','F(delta)**2 and F(probe)**2 explicitly lift the supplied binary64 inclusion thresholds and square rationally. They are compared directly to independent exact squared feature distance; no rounded distance root decides inclusion.')

put('e5b_wall_oracle','sub|dot|cross','Fraction/integer independent wall algebra','triangles F-lifts raw coordinates; inside uses Fraction data and _interval uses exact cleared integer coordinates. In both reviewed domains these +,-,* and zero-start dot sums remain exact, with no float literals or division in these primitives.')
put('e5b_wall_oracle','inside','rational parity rays and integer counts','k/hits are integers. Direction components are explicit F values; det and barycentric/time numerators therefore are Fraction. Their quotients and u+v remain rational, while hits+=1 and hits%2 are exact count/parity operations.')
put('e5b_wall_oracle','_interval','integer swept SAT bounds','a/b/n are integer triangles/axes from positive common-denominator clearing. i is an integer edge index, axes +/+= combines lists, min/max projection differences and n[2]*denominator remain integers. Times are constructed with F(lower,velocity), not integer division.')
put('e5b_wall_oracle','_earliest','integer embedding; rational event/root poses','aa/bb contain Fraction triangles. denominator is their positive lcm and (p-origin)*denominator is exact integer-valued before int. root/probe and moved z components stay Fraction, including division by integer 2 for the right-neighbor midpoint. aa+bb/axis-list + only concatenate containers; i/modulo are integer edge indices.')
put('e5b_wall_oracle','earliest_star_escape','Fraction affine offset','p is a Fraction tetrahedron component and d is tuple(map(F,offset)); p[i]+d[i] remains Fraction before the exact swept SAT union.')
put('e5b_wall_oracle','_star_root','integer embedding and interval union','Input tetrahedra are Fraction. Their common lcm exactly clears (p-origin) before int; projections, differences and n[2]*denominator are integer. aa+bb/axes+= combine containers, and all event times are explicit F(lower,velocity), never int/int.')

put('perf_fraction_reference','segment_distance_squared','shared-primitive Fraction equivalence','The function explicitly map(vector,...) lifts all four supplied endpoints before exact dot/cross algebra. All projection numerators and nonzero squared direction divisors are Fraction, so divisions preserve the exact squared-distance comparison. This is a performance equivalence reference, not a primitive-independent geometry oracle.')
put('perf_fraction_reference','point_triangle_distance_squared','shared-primitive Fraction equivalence','p=vector(p) and the reviewed test callsite map(G.vector,pts) supplies Fraction tri vertices. Thus h/nn and h*h/nn remain Fraction before edge minimization, with no displayed coordinate constructor. This is the declared shared-primitive equivalence reference.')
put('perf_fraction_reference','_convex_surface_sat','Fraction/integer bounds; container concatenation','The reviewed caller supplies vector-lifted geometry/planes. ap+bp and triangle slices concatenate containers; min/max exact dot differences remain Fraction/integer. boundary |= comparison only accumulates booleans. This shared-primitives reference checks optimization equivalence, not oracle independence.')
put('perf_sweep_reference','_point_edge_time|reference_events','Fraction event times; explicit input lifting','test_perf_interlock constructs av/bv via G.vector and direction/time bounds via F before calling this reference. Therefore q-p, dot/cross numerators and every event divisor are Fraction; time divisions remain rational. tri slice + only enumerates edges. The shared-primitive implementation is intentionally an equivalence reference, not an independent G0 oracle.')
put('perf_witness_reference','reference_witness','Fraction arrangement-cell centroids','test_perf_surface_witness._args obtains Fraction triangles/planes through G.triangles/_planes, and exact splitting preserves Fraction cell vertices. The nonempty cell sum has Fraction terms and division by len(cell) remains Fraction. ap+bp and other slices only concatenate containers. Shared primitives are explicitly a performance equivalence boundary.')

source_cache={}
out=[]
for path,line,fn,rule,code,*_ in rows:
    if path not in source_cache:
        source=(ROOT/path).read_text(encoding='utf-8-sig'); tree=ast.parse(source); defs={}
        def walk(n,stack=()):
            if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef)):
                stack=(*stack,n.name);defs['.'.join(stack)]=n
            for c in ast.iter_child_nodes(n):walk(c,stack)
        walk(tree);source_cache[path]=source,defs
    source,defs=source_cache[path]
    reason=None;model=None;exception=False
    a=access.get((path,fn,rule,code))
    if a is not None:
        reason=a['reason'];model='reviewed data/index access';exception=a.get('scope_exemption',False)
    elif rule in ('closed-unproved-arithmetic','closed-reduction','closed-modulo') and (path,fn) in notes:
        model,reason,exception=notes[path,fn]
        if rule=='closed-reduction':
            reason+=' Reduction boundary: the admitted accumulator/element domain above is specific to this exact pinned caller; sum is not globally trusted for arbitrary iterables or start values.'
    status='reviewed_candidate' if reason else 'needs_review'
    node=defs.get(fn)
    out.append(dict(path=path,line=line,function=fn,rule=rule,code=code,
        reason=('Exact site '+code+': '+reason) if reason else 'NEEDS_REVIEW: no source/domain-specific justification, do not admit.',
        operand_model=model,status=status,needs_review=not bool(reason),scope_exemption=exception,
        source_context='\n'.join(source.splitlines()[max(0,line-3):line+2]),
        scope_ast_sha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest() if node else None,
        review_boundary='Human-reviewed exact site, not machine-inferred types. Requires unchanged full module and all src/tests/tools source graph; no automatic refresh or global field/operator waiver.'))

for name,data in [('test_oracle_positive_subset_review.json',out),('test_oracle_positive_subset_needs_review.json',[r for r in out if r['needs_review']]),('test_oracle_positive_subset_scope_exemptions.json',[r for r in out if r['scope_exemption']])]:
    (BASE/name).write_text(json.dumps(data,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print('new non-driver oracle sites',len(out),collections.Counter(r['rule'] for r in out))
print('status',collections.Counter(r['status'] for r in out),'explicit-scope-exemption sites',sum(r['scope_exemption'] for r in out))
print('unreviewed',[(r['path'],r['function'],r['rule'],r['code']) for r in out if r['needs_review']])
