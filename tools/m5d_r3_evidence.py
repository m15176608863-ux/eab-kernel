"""Rerun M5d R3 internal mutations and threshold-edge independent adversaries.

No solver, sibling repository, network, or git writes. An interrupted run is
invalid and must restart; there is no append/resume mode. Large output stays in
the explicitly workspace-scoped tmp directory. This script's hashes freeze
provenance only; mutation verdicts use named semantic assertions exclusively.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/codex/M5d_evidence'
TMP=OUT/'tmp'
TMP.mkdir(parents=True,exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(TMP)
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]

import test_m5d_r3_semantics as gates
from mutation_support import mutated_callable


def nominal_variants():
    f=gates.F
    concave=((-2,-1),(-1,-1),(-1,f(-1,2)),(0,0),
             (-1,f(1,2)),(-1,1),(-2,1),(f(-3,2),0))
    configurations=(
        ('diamond',gates.DIAMOND,gates.WALL),
        ('asymmetric_triangle',((-3,-2),(f(1,10),0),(-2,2)),gates.WALL),
        ('near_corner',tuple((x,y+f(17,10)) for x,y in gates.DIAMOND),gates.WALL),
        ('concave_notched',concave,gates.WALL),
        ('skew_wall',gates.DIAMOND,((1,-3),(4,f(-5,2)),(f(7,2),f(3,2)),(1,f(5,2)))),
        ('near_tied_tips',((-2,-1),(0,f(-1,10)),(f(-1,10000),f(1,10)),(-2,1)),gates.WALL),
    )
    answer=[]
    for name,a,b in configurations:
        ma,mb=gates.p2_specs()
        answer.append((name,gates.p2_input_paths(a,*ma),gates.p2_input_paths(b,*mb)))
    assert len({(a,b) for _,a,b in answer})==len(answer)
    return answer


def independent_bracket(a,b):
    first,labels=gates.first_events(a,b)
    if first is None or len(labels)!=1:
        return None,dict(reason='NO_UNIQUE_NOMINAL_FIRST_EVENT',labels=labels)
    while first.hi-first.lo>gates.F(1,2**20):
        first.refine()
    attempts=[]
    for width in (gates.F(1,25),gates.F(1,100),gates.F(1,400),gates.F(1,1600)):
        bracket=max(gates.F(0),first.lo-width),min(gates.F(1),first.hi+width)
        label=labels[0]
        check=gates.cert.single_cover_certificate(a,b,label,bracket)
        if check is not None:
            return (label,bracket),dict(nominal_root=[str(first.lo),str(first.hi)],attempts=attempts)
        diagnosis=gates.cert.diagnose_single_cover(a,b,label,bracket)
        attempts.append(dict(bracket=[str(x) for x in bracket],failed=list(diagnosis['failed'])))
    return None,dict(reason='ZERO_RADIUS_UNCERTIFIED',labels=labels,attempts=attempts)


def threshold_for(a,b,label,bracket):
    lower,upper=gates.F(0),gates.F(1,8)
    assert gates.cert.single_cover_certificate(a,b,label,bracket,upper,upper) is None
    iterations=0
    while iterations<40 or upper-lower>lower*gates.F(1,2**24)/64:
        assert iterations<64, 'threshold precision did not converge'
        middle=(lower+upper)/2
        if gates.cert.single_cover_certificate(a,b,label,bracket,middle,middle) is None:
            upper=middle
        else:
            lower=middle
        iterations+=1
    assert lower>0
    return lower,upper,iterations


def write(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def run(count):
    started=perf_counter()
    sources=('src/eab/kernel2d/m5c_certificates.py','src/eab/kernel2d/model_robustness.py',
             'src/eab/adapters/bdda2d_motion.py','tests/m5d_r3_oracle.py','tests/m5c_teeth_oracle.py',
             'tests/test_m5d_r3_semantics.py','tests/mutation_support.py','tools/m5d_r3_evidence.py')
    source_start={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources}
    progress=OUT/'r3_progress.json'
    write(progress,dict(valid=False,state='RUNNING_FROM_SCRATCH',started=datetime.now(timezone.utc).isoformat()))
    mutations=[]
    for name,function,before,after,gate,args,message in gates.MUTATIONS:
        gate(*args)
        old=getattr(gates.cert,function)
        changed=mutated_callable(gates.cert,function,[(before,after)])
        setattr(gates.cert,function,changed)
        try:
            try:
                gate(*args)
            except AssertionError as error:
                assert message in str(error), 'wrong assertion: '+str(error)
                detail=str(error)
            else:
                raise AssertionError('surviving internal mutant: '+name)
        finally:
            setattr(gates.cert,function,old)
        mutations.append(dict(name=name,internal_function=function,before=before,after=after,gate=gate.__name__,named_assertion=detail,
                              source_hash_tripwire=False,frozen_snapshot_tripwire=False,
                              interpretation=('proof_budget_contract_only' if name in ('omit_w_endpoint_error','omit_mixed_error')
                                              else 'exact_budget_identity' if name=='reuse_wrong_endpoint_budget'
                                              else 'explicit_geometric_counterexample')))
        write(progress,dict(valid=False,state='MUTATIONS',complete=len(mutations),expected=len(gates.MUTATIONS)))
    for which in ('w','v'):
        for term in range(3):
            parts=[f'du*_length1({which}, lo, hi)','dw*_length1(u, lo, hi)','2*du*dw']
            before=f'e{which} = '+'+'.join(parts)
            after=f'e{which} = '+'+'.join(value for index,value in enumerate(parts) if index!=term)
            old=gates.cert._event
            gates.cert._event=mutated_callable(gates.cert,'_event',[(before,after)])
            try:
                try:
                    gates.test_r3_bilinear_budgets_include_both_endpoints_and_all_terms()
                except AssertionError as error:
                    assert f'R3 {which.upper()} endpoint budget' in str(error)
                    detail=str(error)
                else:
                    raise AssertionError('surviving bilinear mutant')
            finally:
                gates.cert._event=old
            mutations.append(dict(name=f'budget_{which}_{term}',internal_function='_event',
                                  gate='test_r3_bilinear_budgets_include_both_endpoints_and_all_terms',
                                  named_assertion=detail,interpretation='exact_budget_identity',
                                  source_hash_tripwire=False,frozen_snapshot_tripwire=False))
    rows=[]
    configurations=[]
    for case_index,(name,a,b) in enumerate(nominal_variants()):
        chosen,details=independent_bracket(a,b)
        record=dict(name=name,independent_nominal=details,
                    input_a=[[[str(c) for c in p] for p in v] for v in a],
                    input_b=[[[str(c) for c in p] for p in v] for v in b])
        if chosen is None:
            record['status']='UNPROVED'
            configurations.append(record)
            continue
        label,bracket=chosen
        write(progress,dict(valid=False,state='THRESHOLD',case=name,case_index=case_index))
        lower,upper,iterations=threshold_for(a,b,label,bracket)
        record.update(status='CERTIFIED',label=label,bracket=[str(x) for x in bracket],
                      threshold=dict(lower=str(lower),upper=str(upper),width=str(upper-lower),bisection_count=iterations),
                      seed=5101626+case_index,perturbation_count=2*count)
        for factor in (gates.F(1,2),1-gates.F(1,2**24)):
            radius=lower*factor
            certificate=gates.cert.single_cover_certificate(a,b,label,bracket,radius,radius)
            assert certificate is not None
            seen=set()
            for index,(aa,bb) in enumerate(gates.perturbations(a,b,radius,seed=5101626+case_index,count=count)):
                first,labels=gates.first_events(aa,bb)
                assert labels==(label,), 'threshold-edge oracle first-label mismatch'
                assert first.sign((-bracket[0],1))>0 and first.sign((-bracket[1],1))<0, 'threshold-edge oracle open-bracket mismatch'
                seen.add((aa,bb))
                rows.append(dict(case=name,factor=str(factor),radius=str(radius),sample=index,labels=labels,
                                 first_time_interval=[str(first.lo),str(first.hi)],open_bracket_checked=True,
                                 independent_vertex_time_varying_errors=True))
                write(progress,dict(valid=False,state='ADVERSARIES',case=name,complete=len(rows)))
            assert len(seen)==count
        configurations.append(record)
    source_end={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources}
    assert source_start==source_end, 'source drift invalidates entire evidence run; restart required'
    result=dict(valid=True,seed=5101626,mutation_count=len(mutations),mutations=mutations,
                production_geometry_imports_in_primary_oracle=[],
                oracle_direct_imports=['fractions.Fraction','functools.lru_cache','math.comb'],
                configurations=configurations,nominal_configuration_count=len(configurations),
                certified_configuration_count=sum(row['status']=='CERTIFIED' for row in configurations),
                unproved_configuration_count=sum(row['status']=='UNPROVED' for row in configurations),
                threshold_note='r_lo is a conservative rational lower bound, not the exact r_star; width <= edge offset / 64',
                perturbation_count=len(rows),mismatches=0,rows=rows,
                seconds=perf_counter()-started,
                sources=source_start,
                limits=['Finite fixed-seed adversaries do not prove all continuous tubes.',
                        'Two omitted conservative-budget terms are killed on proof-contract refusal, not an asserted physical counterexample.'])
    write(OUT/'r3_semantic_evidence.json',result)
    write(progress,dict(valid=True,state='COMPLETE',perturbation_count=len(rows),mutation_count=len(mutations),seconds=result['seconds']))
    print(json.dumps({key:result[key] for key in ('valid','mutation_count','perturbation_count','mismatches','seconds')},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--count',type=int,default=32,help='nonrigid trajectories per radius; default 32')
    args=parser.parse_args()
    if args.count<6:
        parser.error('--count must be at least 6')
    run(args.count)
