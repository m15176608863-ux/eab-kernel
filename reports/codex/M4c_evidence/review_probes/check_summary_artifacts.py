"""Independent recount of finished summary artifacts; stdlib only, no replay import.

Does not establish geometric correctness: it checks exact denominators, row
conservation, candidate scope, flag semantics and example reference identity.
"""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
temporary=ROOT/'reports/codex/M4c_evidence/tmp/review_summary'
temporary.mkdir(exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(temporary)
PHASES=('raw_df05','post_df06')

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_ratio(value,numerator,denominator):
    assert value['numerator']==numerator and value['denominator']==denominator
    assert value['exact']==(str(Fraction(numerator,denominator)) if denominator else None)

def main(full,summary,out):
    started=time.perf_counter()
    batch=read(full/'summary.json')
    questions=read(summary/'four_questions.json')
    examples=read(summary/'minimal_examples.json')
    assert batch['complete'] is True and batch['steps']==1810 and len(batch['cases'])==15
    counts={p:Counter() for p in PHASES};secondary={p:Counter() for p in PHASES}
    stats=Counter();independent=Counter();missed=[];steps=0
    pair_level={phase:Counter() for phase in PHASES}
    pair_level_rows=[]
    for case,info in batch['cases'].items():
        assert hash_file(full/case/'audit.json')==info['audit_sha256']
        normalized=full/case/'normalized.jsonl.gz'
        assert hash_file(normalized)==info['normalized_sha256']
        with gzip.open(normalized,'rt',encoding='utf-8') as stream:
            rows=[json.loads(line) for line in stream]
        assert len(rows)==info['steps']
        for position,row in enumerate(rows,1):
            assert row['step']==position and row['endpoint_step']==position+1
            steps+=1;stats.update(row['stats'])
            legacy_pairs=set()
            for phase in PHASES:
                records=row['phases'][phase]['records']
                primary=Counter(r['category'] for r in records)
                second=Counter(r['secondary_category'] for r in records if r['secondary_category'] is not None)
                assert dict(primary)==row['phases'][phase]['counts']
                assert dict(second)==row['phases'][phase]['secondary_counts']
                counts[phase].update(primary);secondary[phase].update(second)
                legacy_pairs.update(tuple(r['pair']) for r in records)
            for pair in row['pairs']:
                state=pair['initial_state'];contact=pair['actual']['status']=='contact'
                absent=tuple(pair['pair']) not in legacy_pairs
                if state==-1 and contact:
                    pair_detail={'case':case,'step':row['step'],'pair':pair['pair'],'phases':{}}
                    for phase in PHASES:
                        references=[r for r in row['phases'][phase]['records'] if r['pair']==pair['pair']]
                        primary_match=any(r['category']=='FIRST_COVER_MATCH' for r in references)
                        any_match=primary_match or any(r['secondary_category']=='FIRST_COVER_MATCH' for r in references)
                        other_primary=sum(r['category'] in ('OTHER_FEATURE_FIRST','FIRST_INCIDENCE_NOT_COVER') for r in references)
                        values=pair_level[phase]
                        values['new_contact_pairs']+=1
                        values['present_in_phase']+=bool(references)
                        values['at_least_one_primary_first_cover']+=primary_match
                        values['at_least_one_primary_or_secondary_first_cover']+=any_match
                        values['no_primary_first_cover']+=not primary_match
                        values['no_primary_or_secondary_first_cover']+=not any_match
                        values['any_first_cover_plus_nonfirst_primary_rows']+=any_match and other_primary>0
                        values['primary_first_cover_plus_nonfirst_primary_rows']+=primary_match and other_primary>0
                        values['nonfirst_primary_rows_on_new_contact_pairs']+=other_primary
                        pair_detail['phases'][phase]={'reference_rows':len(references),
                            'at_least_one_primary_first_cover':primary_match,
                            'at_least_one_primary_or_secondary_first_cover':any_match,
                            'nonfirst_primary_rows':other_primary}
                    pair_level_rows.append(pair_detail)
                new_missing=state==-1 and contact and absent
                assert bool(pair.get('missing_both_legacy_tables'))==new_missing
                assert bool(pair.get('initial_contact_absent_both_legacy_tables'))==(state>=0 and absent)
                if new_missing:
                    depth=pair['depth_witness']
                    assert depth['observable']=='largest_vertex_interior_clearance_at_step_end_not_global_PD'
                    assert (depth['squared'] is not None)==depth['has_strict_vertex_witness']
                    if depth['squared'] is not None: assert Fraction(depth['squared'])>0
                    missed.append({'case':case,'step':row['step'],'pair':pair['pair'],'depth_witness':depth})
                if 'translation' in pair:
                    assert state==-1
                    trans=pair['translation'];other=trans['result']
                    same=pair['actual']['status']==other['status'] and pair['actual']['features']==other['features']
                    assert same==trans['same_first_cover_set']
                    assert (pair['actual']['time']==other['time'])==trans['same_time']
                    certified=Fraction(trans['delta_linf'])==0
                    assert trans['certificate']==('CERTIFIED_IDENTICAL_TRAJECTORY' if certified else 'UNCERTIFIED_NONTRANSLATION')
                    if certified: assert same and trans['same_time']
                    independent['different']+=not same;independent['same']+=same
                    independent['certified']+=certified;independent['uncertified']+=not certified
                    independent['actual_contact']+=contact
                    independent['actual_contact_different']+=contact and not same
                    either=contact or other['status']=='contact'
                    independent['either_contact']+=either
                    independent['either_contact_different']+=either and not same
    assert steps==1810
    assert {p:dict(c) for p,c in counts.items()}==batch['counts']
    assert {p:dict(c) for p,c in secondary.items()}==batch['secondary_counts']
    assert dict(stats)==batch['stats']
    assert sorted(missed,key=lambda r:(r['case'],r['step'],r['pair']))==sorted(questions['new_contact_pairs_missing_both'],key=lambda r:(r['case'],r['step'],r['pair']))
    for bucket,collection in (('legacy_primary',counts),('legacy_secondary',secondary)):
        for phase,c in collection.items():
            q=questions[bucket][phase]
            m,o,i,n=(c[k] for k in ('FIRST_COVER_MATCH','OTHER_FEATURE_FIRST','FIRST_INCIDENCE_NOT_COVER','NO_CONTACT_IN_STEP'))
            assert q['all_reference_rows']==sum(c.values())
            assert q['separated_rows']==m+o+i+n and q['separated_contact_rows']==m+o+i
            verify_ratio(q['first_cover_match_given_contact'],m,m+o+i)
            verify_ratio(q['nonfirst_cover_given_contact'],o+i,m+o+i)
            verify_ratio(q['other_feature_first_given_contact'],o,m+o+i)
            verify_ratio(q['first_incidence_not_cover_given_contact'],i,m+o+i)
            verify_ratio(q['no_contact_given_separated'],n,m+o+i+n)
            verify_ratio(q['first_cover_match_all_separated_rows'],m,m+o+i+n)
            verify_ratio(q['pd_cover_match'],c['INITIAL_OVERLAP_PD_MATCH'],c['INITIAL_OVERLAP_PD_MATCH']+c['INITIAL_OVERLAP_PD_OTHER_FEATURE'])
    trans=questions['translation']
    verify_ratio(trans['descriptive_different_candidate_pairs'],independent['different'],independent['same']+independent['different'])
    verify_ratio(trans['descriptive_different_given_actual_contact'],independent['actual_contact_different'],independent['actual_contact'])
    verify_ratio(trans['descriptive_different_given_either_contact'],independent['either_contact_different'],independent['either_contact'])
    assert trans['certified_identical']==independent['certified']
    assert trans['uncertified']==independent['uncertified']
    for name,item in examples.items():
        info=batch['cases'][item['case']]
        assert item['source_sha256']==info['input_hashes']['snapshot']
        assert item['terminal_source_sha256']==info['input_hashes']['terminal_source']
        if item['reference_role'] is not None:
            row=item['legacy_row']
            if item['reference_role']=='secondary':
                assert ':secondary:' in name and name.endswith(':'+row['secondary_category'])
                assert row['secondary_reference'] is not None
            else: assert name.endswith(':'+row['category']) and ':secondary:' not in name
        if item['step']==1:
            assert item['A_previous'] is None and item['B_previous'] is None
        else: assert item['A_previous'] is not None and item['B_previous'] is not None
    pair_level_examples={}
    for phase in PHASES:
        missing_first=[r for r in pair_level_rows if not r['phases'][phase]['at_least_one_primary_or_secondary_first_cover']]
        pair_level_examples[phase]=min(missing_first,key=lambda r:(r['case'],r['step'],r['pair'])) if missing_first else None
    assert len(pair_level_rows)==stats.get('new_contact_pairs',0)
    result={'complete':True,'steps':steps,'cases':15,'examples':len(examples),'missing_new_contact_pairs':len(missed),
            'independent_translation_counts':dict(independent),'elapsed_seconds':time.perf_counter()-started,
            'new_contact_pair_counts_by_phase':{p:dict(c) for p,c in pair_level.items()},
            'minimum_identity_without_any_first_cover':pair_level_examples,
            'minimum_identity_order':'lexicographic case, step, block IDs; not geometry minimization',
            'all_new_contact_pair_rows':pair_level_rows,
            'full_summary_sha256':hash_file(full/'summary.json'),
            'four_questions_sha256':hash_file(summary/'four_questions.json'),
            'minimal_examples_sha256':hash_file(summary/'minimal_examples.json'),
            'scope':'Independent artifact recount, not a geometry oracle or full G6'}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full',type=Path,required=True)
    parser.add_argument('--summary',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    main(args.full,args.summary,args.out)
