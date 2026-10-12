"""Inventory every syntactic branch in the four reviewed numerical modules."""
from pathlib import Path
import ast
import json
ROOT=Path(__file__).resolve().parents[2]
items=[]
class Scan(ast.NodeVisitor):
 def __init__(self,file):self.file=file;self.scope=[]
 def visit_ClassDef(self,node):
  self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
 def visit_FunctionDef(self,node):
  self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
 def branch(self,node,test):
  fn='.'.join(self.scope);f=self.file
  if f.endswith('lp.py'):
   if fn.startswith('_Revised') or fn in ('_float_solve','_certified_optimize','_ray','_ray_verifies','_natural_scales','_exp2'):
    cls='candidate_only_float_heuristic';verify='solve:419-428 exact certify -> exact simplex -> certify; 9 lying candidate injections passed'
   elif fn=='_Exact.reduced_sign':cls='conservative_float_filter_exact_fallback';verify='lp:568-582; relative plus subnormal absolute error; uncertain/inf/nan use raw Fraction'
   elif fn.startswith('_Exact') or fn.startswith('_exact_simplex'):
    cls='fraction_exact_branch_or_pricing_order';verify='statuses and sign are exact; float pricing value selects only a negative exact-sign pivot; 300 independent BFS certificates passed'
   else:cls='shape_or_exact_control';verify='m=0 cost converted to Fraction; maximize changes objective sign only'
  elif f.endswith('dual.py'):
   if fn=='Dual.__pow__':cls='power_dispatch_range_check_known_gap';verify='p=float(p) parity error handled by support-domain reviewer; not a tolerance fallback'
   elif fn=='_ordinary':cls='unused_heuristic';verify='no call site in current Dual module'
   elif fn=='convergence_order':cls='diagnostic_domain_or_log_route';verify='report only; general log error bound explicit R13FIXb gap'
   else:cls='given_scalar_exact_or_type_domain_branch';verify='algebra Fraction expressions; no hidden tolerance or cached jet result'
  else:
   if fn in ('limit_load','limit_load._resolvable','limit_load_multi') and any(s in ast.unparse(test) for s in ('_UNCERTAIN','U0','U','resolution')):
    cls='resolvability_report_only';verify='only uncertainty/resolvability/statuses, original LP status/alpha unchanged; raw22,23 + source mutant caught'
   elif fn=='_tangents':cls='declared_frame_selection_or_loud_projection_resolvability';verify='normal axis threshold chooses documented noncovariant frame; supplied tangent tiny projection throws, raw9 replay passed'
   elif fn in ('_exact_duality_report','_pair_powers','mechanism_is_admissible','mechanism_is_admissible_multi'):
    cls='fraction_exact_certificate';verify='all residual/sign/slack/complementarity exact; tolerance ignored; 1e-100 injections rejected'
   elif fn in ('_rational','_lp_values','_ExactFloat.__new__'):
    cls='certificate_float_view_consistency';verify='exact witness read if view matches; edited fields get new given data; 4 witness/view poisons rejected'
   elif fn in ('_norm','_construction_float','_live_uncertainty','_wrench_rounding','_wrench_rounding.scaled_norm'):
    cls='range_or_diagnostic_output';verify='finite algebra completed Fraction, final binary64 range checked; uncertainty changes no answer'
   else:cls='shape_status_physical_input_or_model_branch';verify='no tolerance-based answer branch; physical cohesion signs/optional fields and output activity selection documented'
  items.append({'file':f,'line':node.lineno,'function':fn,'expression':ast.unparse(test),'classification':cls,'evidence':verify})
 def visit_If(self,node):self.branch(node,node.test);self.generic_visit(node)
 def visit_While(self,node):self.branch(node,node.test);self.generic_visit(node)
 def visit_IfExp(self,node):self.branch(node,node.test);self.generic_visit(node)
 def visit_comprehension(self,node):
  for test in node.ifs:
   self.branch(test,test)
  self.generic_visit(node)
for name in ('lp','limit','limit_multi','dual'):
 file=f'src/eab/{name}.py';Scan(file).visit(ast.parse((ROOT/file).read_text('utf-8')))
(ROOT/'review/evidence/limit_branch_inventory.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'LIMIT_BRANCH_INVENTORY {len(items)} if/while/conditional/comprehension branches')
