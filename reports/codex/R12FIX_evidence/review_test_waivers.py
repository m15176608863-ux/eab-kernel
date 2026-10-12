"""Human-reviewed site candidates, NOT automatic admission or numeric proof."""
import ast
import collections
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/codex/R12FIX_evidence'
initial=[r for r in json.loads((BASE/'initial_scan.json').read_text(encoding='utf-8')) if r[0].startswith('tests/') and r[3].startswith('closed-')]
groups=collections.defaultdict(list)
for r in initial: groups[(r[0],r[2])].append(r)
notes={}
def note(ids,text):
 for i in map(int,ids.split()): notes[i]=text
note('0 1 3 18 20 22 52 54 55 85 118 122 144 146 209 218 230 252 256 259 260 261', 'Fraction/F lifts supplied coordinates exactly, without converting derived rational quantities to float. This map site does not compute a rounded root/norm; subsequent oracle algebra retains rational inputs. Only this binding and pinned context were reviewed, not arbitrary map.')
note('8 15 16 24', 'Reviewed q definition is tuple(Fraction(x) for x in p). This fixed map only lifts supplied vertices; the Newell/support calculations continue in rational arithmetic, with no preliminary float construction.')
note('6 7', 'F and int are type tokens in type(x) in (F,int), not numerical callbacks; the rational branch uses integer numerator/denominator algebra.')
note('2', 'The lambda selects a projection index by an exact rational normal component. ring=list(face) contains integer vertex indices; pop removes an ear index, never a callable. No float construction is performed at these sites.')
note('4', 'The lambda orders integer face-ring identifiers by tuple(sorted(ring)); this is topological canonicalization, not numeric construction.')
note('5', 'map(frozenset,faces) converts integer face-index lists to sets solely for topology comparison, not numeric data conversion.')
note('9 25', 'The lambda only chooses a projection index using abs of a rational normal component, without float/root/norm construction.')
note('10 26', 'The mapped abs takes absolute values of exact rational components to choose a scale; it loses no bits and does not call a root or norm constructor.')
note('13 14 28 29', 'The lambda returns the first field of an existing candidate row for ordering/grouping; it neither invokes numeric functions nor reuses a rounded display as an exact construction.')
note('17', 'repr is a diagnostic sorting key for labels in assertions; formatted strings do not contribute to any expected numeric result.')
note('21 23', 'Reviewed aa/bb are Fraction triangles/tetrahedra, denominator is the lcm of all denominators, and every int((p-origin)*denominator) is already an exact integer. The local lambda performs this exact embedding; the walrus only retains an exact SAT interval.')
note('30', 'The fixed imported vector function lifts supplied endpoints componentwise to Fraction. This frozen performance reference explicitly shares rational primitives and is not advertised as an independent geometric oracle; no float construction occurs in map.')
note('31', 'The event-ordering lambda returns existing (time,label) fields unchanged, without numeric reconstruction.')
note('32 37', 'These are fixed BB52 displacement/tolerance constants at the documented legacy input boundary, not conversions of exact intermediate geometry.')
note('33 34 35 36 79 80 81 82 170 213 235 239 246 247 248 249 250 257 266 267 268 272', 'This helper assembles deliberate internal mutants in an isolated namespace or monkeypatch context. It reads/replaces the tested callable/source so independent assertions reject defective behavior. It is NOT production numerical logic or an oracle for correct expected values.')
note('41 46 73 74', 'edges() retrieves existing integer topology; volume() where present only checks input-shape orientation/diagnostics. Exception names match an error branch. None is used to round an exact quantity before a norm/root.')
note('47 48 62 63 64 65 78 84 115 154 166 187 188 189 191 233 237 242 243 244 269 270 273', 'The flagged operation handles paths, source/fixture bytes, CSV/text, hashes, or a temporary test-input file. A mutate callback here changes copied test fixtures. These operations are not exact geometric intermediates or numeric expected-value constructors.')
note('51', 'Reviewed eager EE reference uses fixed c=covers3: qvector/qedge/sub/mul/neg/qclamp retain Fraction data. unit_normal is final display only; gap2 independently uses unrounded numerator/candidate before sqrt_exact. qa/qb/params convert only at returned display fields. This is an equivalence reference, not a zero-shared-primitive geometric oracle.')
note('53 68 69 70 71 72 87 88 89 100 108 112 113 116 120 124 125 126 128 129 134 135 136 137 138 141 143 157 175 177 179 183 198 200 205 224 227 229', 'This test-model/motion adapter constructs supplied coordinates, poses, loads, or identity labels used jointly by the tested API and its oracle. It is an explicit input-model boundary, not a prematurely rounded exact distance/root expected value. The local method/closure is fixed by the pinned context, not globally trusted dynamic dispatch.')
note('58 225', 'The fixed exact_geom.vector member lifts each supplied endpoint/vertex to Fraction. This map has no float, norm, or root construction.')
note('61 76 110 202 204 241 262', 'These is_convex/reflex_edges/manifold_issues/metrics/volume calls audit topology, orientation, diagnostics, or preconditions of an already constructed test shape. Their results are not reused as exact root/norm intermediates.')
note('66', 'scalar_exact maps complete exact parameters solely to final display parameters for comparison; the exact Fraction certificate is checked separately and display values do not feed the exact geometry calculation.')
note('77', 'G2_BAND is a fixed detection-window scalar, not a callable; reading it does not convert a derived exact quantity.')
note('92 93', 'This timeout harness dispatches the tested function in a thread; join/is_alive/getattr(__name__) are completion and diagnostic operations. The harness does not construct expected geometric values.')
note('95', 'todo stores integer face IDs and boundary is a Counter of oriented integer edges. pop/elements operate on topology data, never callable objects or numeric construction.')
note('96', 'T(i,j)=4*i+j indexes integer mesh vertices. Its lambda/calls do not process floating coordinates or numeric construction.')
note('102 160', 'F=Fraction is a fixed local alias. Coordinates are lifted before differences/affine algebra; F does not round, and the result remains rational or an exact sign.')
note('103', 'This is an unused legacy floating diagnostic helper; current hull assertions use _exact_worst_outside, which lifts to Fraction and rounds only via independent sqrt_exact. This waived diagnostic must not be claimed as an exact geometric oracle.')
note('105', 'issubset compares hull vertices with the supplied input set; set membership does not construct numeric quantities.')
note('109', 'W.U_PROF is fixed wall-profile input data, not a callable or a converted exact intermediate.')
note('119', 'Reviewed _g0_exact_affine.vec lifts inputs, scale, and supplied sin/cos values to Fraction before affine arithmetic. map(vec,P) invokes that fixed exact closure without floating intermediate construction.')
note('131', 'exact_oracle.qpoint only lifts raw vertex components to Fraction; the support-gap normal/projection calculations remain in the independent exact oracle.')
note('152', 'corners adds integer offsets 0/1 to integer lattice indices and returns a set. It cannot round numeric intermediates or retrieve a callable.')
note('155', 'idx is the integer face-index list; pop deletes an ear after Fraction orientation tests, not a callable.')
note('161 171', 'centroid() chooses the supplied load/input reference point. The returned coordinate belongs to the model subsequently solved, not to an exact distance/root under construction.')
note('163 164', 'self.joint is this file\'s fixed Arch.joint, returning supplied joint coordinates/normals/body IDs. hinge_mechanisms lifts those coordinates to Fraction before mechanism solving; no later exact intermediate is prematurely converted.')
note('165', 'The lambda only selects a Gaussian-elimination pivot row by absolute value. Entries are already Fraction; pivot selection does not construct geometric quantities.')
note('167', 'getattr reads the result\'s exact certificate field, falling back to Fraction(v) for the actually supplied display value. It does not execute a retrieved callable or label a display approximation as an exact certificate.')
note('173', 'This small legacy floating LP enumeration reference uses the lambda only for pivot-row selection. It performs no exact-to-float or sqrt/norm construction and is not the exact LP certificate oracle; separate exact-certificate gates carry that claim.')
note('180 181', 'X=lambda v:Fraction(v) exactly lifts supplied contact/load fields. Reference shifts and moment columns stay rational; no premature float then reference subtraction occurs.')
note('182', 'getattr(result,resolvability,None) retrieves a diagnostic status string, never a numeric callable or construction value.')
note('192', '_TRUE_INFLATED_NORMAL is a fixed pre-monkeypatch reference, memoized for comparison of observable normal fields. This is not an independent exact geometry oracle, and the saved callable does not round an exact intermediate.')
note('193 194', 'The Lipschitz check compares observable floating normal fields and their finite differences. normal_fn is either the actual field or an injected defective field. It does NOT claim to reconstruct an unrounded exact normal; norm of this supplied observable difference is the intended model, not a hidden exact constructor.')
note('207', 'Reviewed _fv is componentwise Fraction(x). Four endpoints are lifted before cross products/clamped candidates, which remain Fraction; sqrt_exact(best) is the only final root construction.')
note('214 215 216', 'Reviewed _dot/_segment/_triangle use only Fraction sums/products/division/projection. Lambdas choose by exact squared distances or dot products; operation selects only the fixed two rational-returning helpers. No float/root construction is hidden.')
note('219 223 240', 'scalar_exact is applied only at the final input-shape coordinate boundary. The oracle later lifts that actual supplied model, rather than rounding components of an exact distance still awaiting construction.')
note('220', 'func(*args) is an equivalence harness that records either the tested output or the zero-length-edge ValueError, not an expected-value constructor.')
note('221', 'dict.fromkeys deduplicates existing integer edge IDs; random creates supplied rational directions; yield enumerates queries. These sites neither retrieve callable values nor pre-round exact construction inputs.')
note('234 236', 'scan is the controlled static checker under test; this helper asserts source-issue tags only. Independent Fraction KKT assertions supply numeric truth elsewhere; this helper constructs no geometry.')
note('255', 'Reviewed parameter oracle lifts all vertices to Fraction; dot lambda computes rational sums of products and Gram parameters remain rational. exact_params are compared directly, without float/root construction.')
note('258', 'The fixture yield only separates cache setup and cleanup; it transfers no numeric value/callable and performs no construction.')
note('263 264 265', 'canonical_key/parse_again/hash validate identity, reread determinism, or swap symmetry. Their keys/hashes are not numerical expected values or geometric constructors.')
note('271', 'getattr(r,k) reads a fixed list of parsed scalar fields for column-by-column comparison with the source table; it never invokes the field or feeds an exact root/norm construction.')

indexed={}
for i,((p,f),rs) in enumerate(groups.items()):
 for r in rs:indexed[(p,f,r[3],r[4])]=i
rows=[r for r in json.loads((BASE/'strict_scan.json').read_text(encoding='utf-8')) if r[0].startswith('tests/') and r[3].startswith('closed-')]
output=[];missing=[]
for r in rows:
 path,line,fn,rule,code=r[:5]
 i=indexed.get((path,fn,rule,code)); reason=notes.get(i)
 if reason is None:
  if 'rng.' in code:
   reason='The deterministic RNG generates supplied test coordinates/poses, not a rounded exact geometric intermediate. The oracle separately checks the resulting actual input model.'
  elif code.startswith('yield'):
   reason='The generator enumerates already established test-input cells; yield itself performs no numeric conversion or dynamic numeric callable dispatch.'
  elif code in ['math.pi','pi']:
   reason='This reads the fixed pi scalar for supplied test angles/poses, not a callable or a converted exact intermediate.'
  elif code in ['math.inf','sys.float_info.min','sys.float_info.max']:
   reason='This reads a fixed binary64 boundary/nextafter-direction sentinel for range or exact midpoint-cell certification; no derived exact quantity is first rounded.'
  elif code in ['OverflowError','ZeroDivisionError','ValueError','ArithmeticError']:
   reason='The exception class is used for expected-error matching, not a numeric callback or constructor argument.'
  elif code.startswith('float.fromhex('):
   reason='fromhex decodes an explicitly specified IEEE boundary input constant, rather than converting a derived exact value.'
  elif rule in ('closed-namespace-value','closed-callable-value') and (code.startswith(('CoverType.','Mode.','production.','M.','lp.','adapter.')) or code in ['OPTIMAL','INSIDE','OUTSIDE','PENETRATING','FACET_KINDS','REL_GEOM_TOL']):
   reason='This reads a fixed status enum, diagnostic label, observable string, or declared input-tolerance scalar; the value is not invoked or numerically converted.'
 # Additional strict policy rejects built-in data methods unless individually reviewed.
 if reason is None and rule=='closed-method-call':
  call=ast.parse('('+code+')',mode='eval').body
  method=call.func.attr if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) else ''
  recv=ast.get_source_segment('('+code+')',call.func.value) if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) else ''
  old_group=next((j for j,(p,f) in enumerate(groups) if (p,f)==(path,fn)),None)
  if fn=='_eager_ee': reason=notes[51]
  elif method=='join' and recv=='th':
   reason='Thread timeout/completion harness only, not a numerical expected-value constructor.'
  elif method in ('count','replace','split','startswith','endswith','decode','encode','join'):
   reason=f'The receiver {recv!r} is source/CSV/document/diagnostic text (or byte input decoded to text) in this helper. {method} changes representation only; it constructs no numeric expected value and does not dispatch a numerical callable.'
  elif method in ('append','extend','add','update','setdefault','discard','remove','clear','copy','index','sort','get','values','items','keys'):
   reason=f'This pinned {method} call stores, selects, or iterates existing data in the local test list/set/dict/Counter {recv!r}; the payload is coordinate/interval/label/input or report data, not a retrieved callable. The collection operation itself neither converts to float nor computes a root/norm. Nested argument expressions remain subject to the numerical pass; this candidate does not waive their arithmetic.'
   if fn in ('_mutant_scan','_mutant_g2','_mutant_module','_inject','_arithmetic_fault_inside_margin_contacts','convex_view_mutant','reject_z_inside_cone_filter','all_branch_convex_view_mutant','_mutant_function','_mutant_reader'):
    reason='Source-string editing for deliberate internal mutation tests; not an oracle for correct numerical values. Nested defective arithmetic is intentional and must be rejected by the independent target assertion.'
   if method=='update' and recv=='h': reason='h is the SHA256 digest accumulator and chunk is fixture bytes; updating its digest cannot pre-round a numeric construction.'
  elif method=='join' or (method=='join' and recv=='th'):
   reason='Thread timeout/completion harness only, not a numerical expected-value constructor.'
 if reason is None:
  missing.append(r);reason='REVIEW_REQUIRED: this site has not been justified; do not automatically admit it.'
 output.append({'path':path,'function':fn,'rule':rule,'code':code,'reason':fn+': '+reason,'line':line,'review_boundary':'Human-reviewed site candidate, not a static proof. Pin the whole module and its source dependencies before admission.'})
(BASE/'test_waiver_review.json').write_text(json.dumps(output,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print('Reviewed',len(output)-len(missing),'of',len(output),'unresolved',len(missing))
for r in missing:print(r)
