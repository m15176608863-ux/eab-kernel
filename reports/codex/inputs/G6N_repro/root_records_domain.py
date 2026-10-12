"""Finite JSON numbers silently underflow/overflow at ContactRecord entry.

Independent reference uses Fraction(decimal-token) and exact RN-even endpoint
cells only; no production construction or reader helper serves as the oracle.
"""
from pathlib import Path
from fractions import Fraction as F
import json, math, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from eab.contact_record import records_from_json, ContactRecord, validate

low = F(1, 2**1075)
high = (F(sys.float_info.max)+2**1024)/2
base = {'source':'eab','step':0,'contact_index':0,'block_a':0,'block_b':1}
rows = []
for field in ('ref_points', 'normal', 'params', 'shear', 'slip_ref'):
    for token in ('1e-400', '-1e-400', '1e400', '-1e400'):
        q = F(token)
        assert q != 0 and (abs(q) <= low or abs(q) >= high)
        encoded = '['+token+',0]'
        if field == 'ref_points': encoded = '['+encoded+']'
        text = json.dumps([base])[:-2]+',"'+field+'":'+encoded+'}]'
        records = records_from_json(text)  # Must reject, but does not.
        value = getattr(records[0], field)
        actual = value[0][0] if field == 'ref_points' else value[0]
        assert actual == 0.0 if abs(q) <= low else math.isinf(actual)
        validation = 'accepted'
        try: validate(records[0])
        except ValueError as error: validation = str(error)
        rows.append({'api':'records_from_json','field':field,'finite_decimal_token':token,
                     'expected':'ConstructionDomainError (nonzero RN-zero or RN-inf)',
                     'actual':repr(actual),'entry_raised':False,'separate_validate':validation})

# Direct exact finite input avoids any question about JSON parser provenance.
q = F(1, 2**2000)
r = ContactRecord.from_dict(dict(base, ref_points=[[q,0]], normal=[q,0]))
assert r.ref_points == ((0.0,0.0),) and r.normal == (0.0,0.0)
validate(r)  # Even explicit structure/finite validation cannot detect this loss.
rows.append({'api':'ContactRecord.from_dict','input':'Fraction(1, 2**2000)',
             'fields':['ref_points','normal'],'actual':repr((r.ref_points,r.normal)),
             'expected':'ConstructionDomainError','separate_validate':'accepted'})
out={'confirmed':True,'cases':len(rows),'results':rows,
     'location':'src/eab/contact_record.py:_decode;records_from_json',
     'independent_oracle':'Fraction token and exact RN-even zero/infinity cell boundaries'}
(ROOT/'review/evidence/root_records_domain.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
