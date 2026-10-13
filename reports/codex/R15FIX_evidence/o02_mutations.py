"""Rerun internal O02 mutations without editing production source files."""
from pathlib import Path
import importlib.util
import inspect
import json
import sys
from fractions import Fraction as F

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/"src")]
import pytest
from tools import osteomorphic as shape
spec=importlib.util.spec_from_file_location("r15_shape_gates",ROOT/"tests/test_r15fix_shape.py")
gates=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)
rows=[]

def record(name,mutation,gate,wanted):
    with pytest.MonkeyPatch.context() as mp:
        mutation(mp)
        try:
            gate()
        except (AssertionError,pytest.fail.Exception) as exc:
            detail=str(exc)
            assert wanted in detail,(name,detail)
            rows.append(dict(mutation=name,status="EXPECTED_ASSERTION_RED",assertion=detail))
        else:
            raise AssertionError(f"mutation survived: {name}")

original=shape._ShapeJet.__add__
def rounded_add(self,other):
    exact=original(self,other)
    return shape._ShapeJet(F(float(exact.v)),tuple(F(float(a)) for a in exact.e))
for name,gate,wanted in (
    ("round_local_add_primal",lambda:gates.test_shape_dual_complete_coordinate_keeps_midpoint_residual(0,-100,F(1)),"complete coordinate residual"),
    ("round_local_add_jet",lambda:gates.test_shape_dual_complete_jet_keeps_midpoint_residual(0,F(2)**60),"complete jet residual"),
    ("round_local_add_height",gates.test_shape_dual_complete_z_keeps_height_and_jet_residuals,"complete height residual")):
    record(name,lambda mp:mp.setattr(shape._ShapeJet,"__add__",rounded_add),gate,wanted)

def mutate_pair(mp):
    source=inspect.getsource(shape.interlocking_pair_generic)
    needle="_shape_value(c[2]) + _shape_value(lz)"
    replacement="_shape_value(_shape_coordinate(_shape_value(c[2]) + _shape_value(lz)))"
    assert needle in source
    scope=dict(vars(shape))
    exec(source.replace(needle,replacement),scope)
    mp.setattr(shape,"interlocking_pair_generic",scope["interlocking_pair_generic"])
record("round_pair_center_before_vertices",mutate_pair,
       gates.test_shape_generic_pair_translation_stays_exact_until_final_vertices,
       "complete pair translation residual")

def mutate_sample(mp):
    mp.setattr(shape,"_shape_sin",lambda base,phase,callback:
               shape._shape_value(callback(base+phase)))
record("multiply_original_seed_in_sin_before_amp",mutate_sample,
       lambda:gates.test_shape_phase_jet_is_scaled_before_final_range_check(F(2)**-1074,F(2)**400),
       "representable complete phase jet rejected")
result=dict(scope="real in-memory production functions; no source writes; patches restored",mutations=rows)
Path(__file__).with_suffix(".json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(result,indent=2,ensure_ascii=False))
