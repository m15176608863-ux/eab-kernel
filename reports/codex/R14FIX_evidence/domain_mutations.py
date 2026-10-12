"""Rerunnable real-source and README mutations; restore byte-identically."""
from pathlib import Path
from fractions import Fraction as F
import hashlib, inspect, json, subprocess, sys, traceback
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/"src"),str(ROOT/"tests")]
HERE=Path(__file__).resolve().parent
from eab.kernel2d import geom
from tools import osteomorphic
import test_r14_domain as gates
rows=[]
for module,name,needle,run in [
 (osteomorphic,"_shape_value","else Fraction(value)", lambda: gates.test_shape_raw_exact_coordinate_cancellation_cannot_be_silently_zero(False)),
 (geom,"reflex_vertices",'    tol = binary64_argument(tol, "reflex_vertices.tol")\n', lambda: gates.test_angular_window_exact_input_is_checked_before_libm(F(1,2**1075))),
 (osteomorphic,"osteomorphic_block",'    binary64_argument(val(phase), "osteomorphic.phase")\n',lambda: gates.test_shape_phase_is_checked_before_mixed_float_arithmetic(False,2**54+1)),
 (osteomorphic,"osteomorphic_block_generic",'    binary64_argument(val(phase), "osteomorphic.phase")\n',lambda: gates.test_shape_phase_is_checked_before_mixed_float_arithmetic(True,2**54+1))]:
 original=getattr(module,name); source=inspect.getsource(original);assert source.count(needle)==1
 ns=dict(vars(module));exec(source.replace(needle,"else float(value)" if name=="_shape_value" else ""),ns);setattr(module,name,ns[name])
 try:
  try: run()
  except BaseException as exc:
   assert "DID NOT RAISE" in str(exc), repr(exc)
   detail=traceback.format_exc();print(name,detail);rows.append({"mutation":name,"target_assertion":"DID NOT RAISE ConstructionDomainError","caught":True,"traceback":detail})
  else: raise AssertionError("mutation survived")
 finally:setattr(module,name,original)
p=ROOT/"README.md";data=p.read_bytes();before=hashlib.sha256(data).hexdigest()
try:
 p.write_bytes((HERE/"baseline/README.md").read_bytes())  # Restore the actual pre-fix document, not synthetic output.
 command=[sys.executable,"-X","utf8","-m","pytest","-q","-p","no:cacheprovider","tests/test_r14_cone.py::test_readme_does_not_assert_the_false_unqualified_relative_capacity_bound","--basetemp="+str(HERE/"tmp/doc_mutation")]
 result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (HERE/"n05_document_mutation.log").write_bytes(result.stdout)
 output=result.stdout.decode("utf8");print(output)
 assert result.returncode==1 and "N05 unqualified nonlinear capacity bound" in output
 rows.append({"mutation":"README old mathematical claim restored","caught":True,"target_assertion":"N05 unqualified nonlinear capacity bound"})
finally:p.write_bytes(data)
assert hashlib.sha256(p.read_bytes()).hexdigest()==before
(HERE/"domain_mutations.json").write_text(json.dumps({"mutations":rows,"readme_restored_sha256":before},indent=2),encoding="utf8")
print("DOMAIN_DOCUMENT_MUTATIONS_CAUGHT 5; README byte restoration verified")
