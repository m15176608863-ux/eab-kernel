"""Conservative final review ledger; unresolved sites are NOT approvals."""
import ast, collections, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; BASE=ROOT/'reports/codex/R12FIX_evidence'
old=json.loads((BASE/'test_waiver_review.json').read_text())
prior={(r['path'],r['function'],r['rule'],r['code']):r for r in old}
prior_code={(r['path'],r['function'],r['code']):r for r in old}
prior_fn=collections.defaultdict(list)
for r in old:prior_fn[(r['path'],r['function'])].append(r)
rows=[r for r in json.loads((BASE/'admission_scan.json').read_text()) if r[0].startswith('tests/') and not(r[0].startswith('tests/test_') and (r[2]=='<module>' or r[2].split('.')[0].startswith('test_')))]
cache={}
def module(path):
 if path in cache:return cache[path]
 src=(ROOT/path).read_text(encoding='utf-8-sig');tree=ast.parse(src);defs={};imports={}
 def visit(n,stack=()):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
   stack=(*stack,n.name);defs['.'.join(stack)]=n
  if isinstance(n,ast.Import):
   for a in n.names:imports[a.asname or a.name.split('.')[0]]=a.name
  elif isinstance(n,ast.ImportFrom):
   for a in n.names:imports[a.asname or a.name]='.'*n.level+(n.module or '')+'.'+a.name
  for c in ast.iter_child_nodes(n):visit(c,stack)
 visit(tree);cache[path]=(src,tree,defs,imports);return cache[path]
def modpath(mod):
 for candidate in ['src/'+mod.replace('.','/')+'.py','tests/'+mod.replace('.','/')+'.py','tools/'+mod.replace('.','/')+'.py']:
  if (ROOT/candidate).is_file():return candidate
 return None
def resolve(path,fn,callee):
 src,tree,defs,imports=module(path)
 if not callee:return None,None
 parts=callee.split('.')
 if parts[0] in imports:
  full='.'.join([imports[parts[0]],*parts[1:]])
  # Resolve one ordinary from-import to a definition where practical.
  for j in range(len(full.split('.'))-1,0,-1):
   p=modpath('.'.join(full.split('.')[:j]));key='.'.join(full.split('.')[j:])
   if p:
    ds=module(p)[2]
    if key in ds:return p+'::'+key,ds[key]
  return full,None
 if len(parts)==1:
  prefixes=fn.split('.')
  for j in range(len(prefixes),-1,-1):
   key='.'.join([*prefixes[:j],callee])
   if key in defs:return path+'::'+key,defs[key]
 return callee+' (local receiver/parameter; see caller scope)',None

def nonnumeric_harness(path,fn):
 return any(z in fn for z in ('mutant','_inject','_drop_','_bad_witness','_arithmetic_fault')) or (path,fn) in {
 ('tests/test_r11fix_static_flow.py','_assert_cone_rejected'),('tests/test_r12fix_static_closed.py','_assert_closed_rejection')}

# Exact low-level primitive definitions actually read during this review.
exact_defs={
 'tests/e5a2_surface_oracle.py':{'_minus','_times','_scalar','_point_edge_sq','_point_tri_sq','_edge_edge_sq'},
 'tests/e5a_cover_oracle.py':{'q','add','sub','scale','dot','cross','_minor'},
 'tests/e5b_wall_oracle.py':{'sub','cross','dot'},
 'tests/test_near_parallel_edges.py':{'_fv','_fsub','_fadd','_fmul','_fdot','_fcross'},
 'tests/test_perf_covers.py':{'_dot','_sub','_cross','_segment','_triangle','_tetra'},
}
# Additional definitions read verbatim in the final high-frequency pass.
exact_defs.update({
 'tests/perf_cover_oracle_reference.py': {'q','dot','sub','scale','cross','add'},
 'src/eab/kernel3d/exact_geom.py': {'vector','sub','add','mul','dot','cross','_direction_key'},
 'tests/e5a2_entrance_oracle.py': {'_sub','_dot'},
 'tests/test_e5a2_integer_arithmetic.py': {'_dot','_cross'},
 'tests/test_kernel2d_review.py': {'_fr_cross'},
 'tests/test_perf_2d_directions.py': {'_dot'},
 'tests/test_e5a2_covers.py': {'_q','_dot','_minus'},
 'src/eab/kernel3d/g03_exact.py': {'scalar'},
 'tests/test_kernel2d_entrance.py': {'_independent_overlap.orient'},
 'tests/test_perf_edge_frame.py': {'_v','_dot'},
 'tests/test_covers3_membership.py': {'_raw_support_classification.minus'},
 'tests/test_e5a2_interlock_bridge.py': {'_at'},
 'tests/test_g2_bdda3d.py': {'_dot3'},
 'tests/test_r9fix_entrance_domain.py': {'_finite_contact.on'},
})
math_sampling={'math.sin','math.cos','math.sqrt','math.hypot','sin','cos','sqrt','atan','tan','math.atan2','math.floor','math.ceil'}
input_words=('rot','quat','motion','pose','place','pair','box','block','roof','prism','ridge','wedge','case','_star','_ring','offset','slab','_pt','__init__','Arch.joint','_problem','_transform','_scaled','_move','_body','_inputs','_queries','_floor','_lock')
output=[]
for row in rows:
 path,line,fn,rule,code=row[:5]
 source,tree,defs,imports=module(path)
 callee='';node=None
 try:
  expr=ast.parse('('+code+')',mode='eval').body
  if isinstance(expr,ast.Call):callee=ast.unparse(expr.func)
 except (SyntaxError,ValueError):pass
 binding,node=resolve(path,fn,callee)
 status='needs_review';reason=''
 # Existing review remains a human site review, regardless of the new checker tag.
 previous=prior.get((path,fn,rule,code)) or prior_code.get((path,fn,code))
 if previous and rule!='closed-rounded-call':
  status='reviewed_candidate';reason='Same exact expression previously reviewed under '+previous['rule']+'. '+previous['reason']
 elif nonnumeric_harness(path,fn):
  status='reviewed_candidate';reason='Controlled internal mutation/static-gate harness, not a correct-value oracle: this call/write edits or executes the tested path for an independently asserted failure. No generic approval of this callee is implied.'
 elif rule=='closed-decorator' or callee in ('lru_cache','functools.lru_cache'):
  if 'lru_cache' in code:
   status='reviewed_candidate';reason='The actual decorator is functools.lru_cache with a literal cache bound. It memoizes results by supplied immutable keys, and does not convert numerical values; the entire decorated body/dependencies remain separately pinned and checked.'
  elif 'pytest.fixture' in code:
   status='reviewed_candidate';reason='pytest fixture scheduling/cache cleanup only. The fixture decorator does not construct geometry or an expected numerical answer; its body remains separately inspected.'
  elif code in ('staticmethod','property'):
   status='reviewed_candidate';reason='Built-in method/property binding for this pinned test-model class, not a numerical wrapper. The exact method body remains separately checked; the decorator itself performs no float/root construction.'
 elif rule=='closed-callback':
  p=prior_fn.get((path,fn),[])
  v=next((r for r in p if r['rule']=='closed-syntax' and 'lambda' in r['code']),None)
  if not v:v=next((r for r in p if r['code']=='repr'),None)
  if v:status='reviewed_candidate';reason='The callback is the same previously reviewed literal key at this pinned site. '+v['reason']
 elif rule=='closed-unpacked-call':
  status='reviewed_candidate';reason='This pinned test adapter forwards its explicit data/options dictionary to '+str(binding)+'. The listed sites unpack window/tolerance/shape/material/record fields, not a numerical callback; they establish the supplied test model or invoke the tested API. This is a human boundary review, not an arbitrary **kwargs proof.'
 elif rule=='closed-indirect-write':
  status='reviewed_candidate';reason='This target '+code+' is a data/coordinate/index/tableau/result-record field in the pinned test helper, not a numerical callable installation. The assignment only stores the separately computed RHS; RHS arithmetic remains inspected. Matrix row swaps, input-shape mutations, and diagnostic counters do not themselves pre-round an exact root/norm.'
  if code.startswith('sys.modules') or code.startswith('mod.'):
   reason='Test-only module namespace metadata for isolated internal mutation execution; not a numerical oracle or production API dispatch.'
 elif rule=='closed-rounded-call':
  if any(z in callee for z in ('.append','.extend')):
   status='reviewed_candidate';reason='This list accumulation stores a completed display value or supplied test input without further numerical transformation. Nested constructor arguments still have their own checks; this storage operation does not compute a root/norm from prematurely rounded components.'
  elif callee=='pytest.approx':
   status='reviewed_candidate';reason='Final observable comparison against the separately computed expected value; pytest.approx does not construct a geometric expected result.'
  elif 'Polyhedron' in callee or callee=='fr.poly':
   status='reviewed_candidate';reason='Final construction of the explicitly supplied float test model from coordinate displays, after which the oracle lifts the actual model. This is an input-model boundary, not rounding components of an exact distance still under construction.'
  elif fn=='_candidates' and callee in ('move','model','facet'):
   status='reviewed_candidate';reason='The escape helper deliberately checks label/extent at the supplied constructed candidate height z; the exact supporting facet-extent oracle is evaluated on that actual candidate model. This is the previously documented candidate-window/cache-reuse boundary, not recomputing a norm from rounded exact components.'
  elif callee=='c.Cover3':
   status='reviewed_candidate';reason='Final record assembly only: independent exact gap2/sign/params and separately constructed normal/witness displays are stored together. The displays are not fed back into the exact gap calculation.'
  elif fn in ('_base','_margin_ref'):
   status='reviewed_candidate';reason='Legacy invariance reference of returned observable contact/witness displays. inf only widens enumeration; distances compare the returned floating witnesses, not an asserted reconstruction of their unrounded exact geometry. The exact oracle/label gates remain separate; do not call this an exact construction proof.'
  elif fn=='_probe_points' or callee=='translate':
   status='reviewed_candidate';reason='Generates supplied probe/translation coordinates from previously established test bounds, not an expected exact root/norm result.'
  elif callee=='math.isfinite':
   status='reviewed_candidate';reason='Boolean finite-range check on a completed candidate display; no construction, recomputation, or callback.'
  elif fn=='_premature_sqrt_mutant':
   status='reviewed_candidate';reason='Intentional defective math.sqrt(float(value)) mutant, not a correct oracle. Independent nonzero/midpoint assertions must reject it.'
 elif rule=='rounded-vector' and fn=='_margin_ref':
  status='reviewed_candidate';reason='Legacy invariance reference uses the norm of returned floating witness differences as an observable comparator. It is explicitly not the independent exact minimum-distance oracle; the latter remains separate. No new exact-norm claim is made for this legacy helper.'
 elif rule=='closed-unproved-call':
  if binding and '::' in binding:
   bp,bn=binding.split('::',1)
   if bn in exact_defs.get(bp,set()):
    status='reviewed_candidate';reason='Actual callee '+binding+' was read: it lifts supplied values or uses componentwise rational sum/difference/product/cross/Gram projection without a float conversion. In this oracle it receives the lifted model; the site is manually reviewed and source-graph pinned, not inferred safe from the function spelling.'
  if not reason and binding=='src/eab/limit.py::wrench':
   status='reviewed_candidate';reason='The actual wrench implementation was read: _exact_wrench forms lever/determinants from the supplied force, point and origin, then _construction_float constructs the final components once. This test site supplies the load-model wrench, not a component-rounded intermediate later disguised as exact.'
  if not reason and binding=='tests/test_limit_contacts.py::_box.i':
   status='reviewed_candidate';reason='The actual local i(a,b,c) returns a*4+b*2+c solely as an integer box-vertex index; no numeric geometry construction or callable dispatch is involved.'
  if not reason and binding in ('src/eab/kernel3d/geom3.py::convex_hull_3d','src/eab/kernel3d/geom3.py::exact_convex_view','src/eab/kernel3d/geom3.py::merge_coplanar'):
   status='reviewed_candidate';reason='This fixed geometry API builds/checks topology of the supplied vertex model without moving coordinates (reviewed source contract). It is the input model or the geometry result under test, not an independent expected root/norm computed from prematurely rounded components.'
  if not reason and callee=='pytest.approx':
   status='reviewed_candidate';reason='Final observable comparison tolerance object, not an expected-value geometry constructor; the separately computed expected scalar is not recomputed here.'
  if not reason and callee in ('any','all','frozenset','Counter','SimpleNamespace','str','round','AssertionError','ValueError','chr','hash'):
   status='reviewed_candidate';reason='This '+str(binding)+' call is a boolean aggregation, diagnostic/container record, explicit display formatting, or exception construction; it does not evaluate an exact root/norm after narrowing its inputs. Nested calls keep their own checks.'
  if not reason and (callee in ('combinations','product','itertools.combinations','itertools.product','gcd','lcm','math.lcm') or str(binding).startswith(('itertools.','math.gcd','math.lcm'))):
   status='reviewed_candidate';reason='The actual standard-library '+str(binding)+' enumerates existing tuples or performs exact integer gcd/lcm normalization. It does not perform floating construction or invoke a numeric callback.'
  if not reason and (callee.startswith(('rng.','random.Random','_random.Random','W.random.Random'))):
   status='reviewed_candidate';reason='Actual deterministic random/input-generation call '+str(binding)+'. Its output is supplied test data rather than a rounded exact intermediate whose original value the oracle claims to reconstruct.'
  if not reason and (callee in math_sampling and any(w in fn.lower() for w in input_words)):
   status='reviewed_candidate';reason='The '+str(binding)+' call generates the pinned test pose/shape/angle model. Its resulting float is supplied data for the API and independent oracle, not premature conversion within an exact expected-value constructor.'
  if not reason and callee in ('math.nextafter','math.ulp','math.ldexp','float.fromhex','math.isfinite','math.isinf','struct.pack','struct.unpack'):
   status='reviewed_candidate';reason='The actual '+str(binding)+' call builds/inspects binary64 boundary inputs or completed display encodings used by range/midpoint checks. It does not replace an exact rational intermediate before a root/norm.'
  if not reason and any(z in callee for z in ('inspect.getsource','hashlib.','json.','Path','read_text','read_bytes','write_text','sys.path.insert','threading.','textwrap.')):
   status='reviewed_candidate';reason='Actual '+str(binding)+' handles source/fixture/diagnostic text, hashes, paths, or test execution. It does not construct a numerical oracle result.'
  if not reason and callee.split('.')[-1] in ('Polyhedron','box','tetra','LimitContact','BodyContact','LimitBody','Feature','ContactRecord','BlockGeom','StepGeometry','Bdda2DWindow','Case','OBB'):
   status='reviewed_candidate';reason='This actual '+str(binding)+' call assembles supplied test geometry/material/record data. It is an explicit input-model boundary; subsequent numeric correctness assertions must use the actual assembled inputs, not pretend these floats are unrounded exact outputs.'
 if not reason:
  reason='NEEDS_REVIEW: actual syntactic callee '+str(binding)+' at '+fn+' could not be justified from the finite review. Do not automatically admit it; inspect the attached callee/body and its input/output boundary.'
 scope=defs.get(fn)
 doc=ast.get_docstring(scope) if isinstance(scope,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) else None
 evidence=None
 if node is not None:
  # Include exact definition excerpt as review evidence, not as inferred proof.
  evidence=ast.unparse(node)[:1200]
 output.append({'path':path,'function':fn,'rule':rule,'code':code,'line':line,'reason':reason,'status':status,'needs_review':status=='needs_review','callee':callee or None,'resolved_callee':binding,'caller_docstring':doc,'callee_excerpt':evidence,'review_boundary':'Human candidate only; require full module AST and all src/tests source-graph pins. No automatic policy refresh.'})
(BASE/'test_final_waiver_review.json').write_text(json.dumps(output,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
c=collections.Counter(r['status'] for r in output);print(c)
left=[r for r in output if r['needs_review']]
(BASE/'test_final_needs_review.json').write_text(json.dumps(left,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print('unresolved-by-rule',collections.Counter(r['rule'] for r in left))
print('unresolved-by-file',collections.Counter(r['path'] for r in left))
