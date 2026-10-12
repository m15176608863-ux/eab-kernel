"""Final confirmed tool/model defects, mutated inside actual decoding/building."""
from pathlib import Path
from fractions import Fraction
import importlib.util
import sys
import traceback
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tests"),str(ROOT/"tools")]
import pytest
import m4_bdda_shadow
from eab.readers.numeric_decode import loads,decode_tree

def load_test(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"tests"/(name+".py"))
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

t=load_test("test_r14_tool_readers")
s=load_test("test_r14_showcase")
base=Path(__file__).parent/"tmp"/"final_mutations"
base.mkdir(parents=True,exist_ok=True)

def red(label,patch,gate,kind,message):
    folder=base/label
    folder.mkdir(exist_ok=True)
    with pytest.MonkeyPatch.context() as mp:
        patch(mp)
        try:gate(folder)
        except kind as error:
            assert message in str(error)
            traceback.print_exc(file=sys.stdout)
            print("VERIFIED_RED",label,"target:",message)
        else:raise AssertionError("NO_TEETH "+label)

red("M4_cs1",lambda mp:mp.setattr(m4_bdda_shadow,"scalar_rational",lambda value,**kw:float(value)),
    t.test_r14_m4_cs1_text_boundary_is_checked_in_actual_compare,pytest.fail.Exception,"DID NOT RAISE")
red("G4_angle",lambda mp:mp.setattr(t.g4_multistep,"check_input",lambda value,quantity:Fraction(value)),
    t.test_r14_g4_angle_domain_rejects_radians_underflow_at_actual_analyze,pytest.fail.Exception,"DID NOT RAISE")
red("tool_decimal_identity",lambda mp:mp.setattr(t.g2_bdda3d,"numeric_loads",lambda text:decode_tree(loads(text),"old")),
    t.test_r14_tool_document_decimal_identity_is_not_rounded,AssertionError,"decimal step must remain exact integer")
mutant=s._builder((('rho = check_input(rho, "showcase.arch.rho")',"rho = Fraction(rho)"),))
red("showcase_density",lambda mp:mp.setattr(s,"_builder",lambda:mutant),
    lambda folder:s.test_r14_showcase_density_input_outside_demo_domain_is_named(Fraction(2)**401),pytest.fail.Exception,"DID NOT RAISE")
mutant=s._builder((("x0, y0 = map(Fraction, P[i])","x0, y0 = P[i]"),("x1, y1 = map(Fraction, P[(i + 1) % len(P)])","x1, y1 = P[(i + 1) % len(P)]")))
red("showcase_shoelace",lambda mp:mp.setattr(s,"_builder",lambda:mutant),
    lambda folder:s.test_r14_showcase_gravity_uses_exact_returned_vertex_area(0),AssertionError,"demo gravity and moment complete exact shoelace expression")
print("NO_SOURCE_WRITES_NO_SIBLING_EXECUTION_NO_GALLERY_RENDER")
