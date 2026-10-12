"""Execute real internal faults; preserve exact assertion traceback and old gate comparison."""
from pathlib import Path
import hashlib,json,sys,traceback
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from fractions import Fraction as F
import pytest
import eab.margin as margin
from eab.kernel3d.geom3 import box
from e5a_cover_oracle import assert_margin_gap_rounding,margin_witness_squared
import test_invariance_geom as T
import test_r8fix_margin_gap_gate as gate

paths=['src/eab/margin.py','tests/e5a_cover_oracle.py','tests/test_invariance_geom.py','tests/test_r8fix_margin_gap_gate.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
before=hashes()

def ordinary():
    _,_,A,B=T._cell('box_box_face',7,0.,.001)
    delta=.001*T.PAIRS['box_box_face'][3]
    label=('EE',('edge',0,1),('edge',5,6))
    row=next(r for r in T.margin_contacts(A,B,delta=delta) if r.label==label)
    return row,margin_witness_squared(A,B,label),delta

def large():
    M=F(10**20)
    A=box((M+2,F(0),F(0)),(F(1),F(1),F(1)))
    B=box((F(-1),F(0),F(0)),(F(1),F(2),F(2)))
    row=margin.margin_contacts(A,B,delta=M,band=2,tol=0)[0]
    return row,(M+1)**2,M

rows=[]; traces=[]
for case,make,run in [('ordinary_1ulp',ordinary,gate._ordinary_gap_gate),('large_cancellation',large,gate._large_gap_gate)]:
    run()
    contact,squared,delta=make()
    assert_margin_gap_rounding(contact.margin_gap,squared,delta)
    rows.append(dict(case=case,implementation='fixed',new_gate='PASS',gap=contact.margin_gap,
                     distance=contact.distance,old_equality=contact.margin_gap==contact.distance-delta))
    for fault in ['old_subtraction','omit_delta','reverse_delta','double_distance']:
        with pytest.MonkeyPatch.context() as patch:
            gate._arithmetic_fault_inside_margin_contacts(patch,fault)
            contact,squared,delta=make()
            assert contact.exact_distance_squared==squared,'mutation must leave the geometric certificate unchanged'
            try:run()
            except AssertionError as exc:
                assert 'exact margin-gap midpoint' in str(exc),str(exc)
                traces.append(f'=== {case}/{fault} ===\n'+traceback.format_exc())
                outcome='AssertionError: exact margin-gap midpoint'
            else:raise AssertionError((case,fault,'gate had no teeth'))
            old_accepts=contact.margin_gap==contact.distance-delta
            assert old_accepts==(fault=='old_subtraction')
            rows.append(dict(case=case,implementation=fault,new_gate=outcome,gap=contact.margin_gap,
                             distance=contact.distance,old_equality=old_accepts))
assert hashes()==before,'source/test edit during evidence run'
(OUT/'margin_gap_mutation_tracebacks.log').write_text('\n'.join(traces),encoding='utf-8')
(OUT/'margin_gap_migration_comparison.json').write_text(json.dumps({
 'scope':'The old equality specified subtraction of display floats, not the mathematical gap. The new certificate deliberately rejects that buggy model. Both catch omit/reverse/double distance; this is semantic strength, not literal logical implication for a changed contract.',
 'rows':rows,'sha256_unchanged':before},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'baselines_passed':2,'real_internal_mutants_rejected':8,'old_model_rejected_only_by_new':2,'old_and_new_arithmetic_faults_rejected':6,'sha256_unchanged':True}))
