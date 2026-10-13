"""WO-G6O schema-first identity contract mismatch, not a silent result error.

Both integer spelling and decimal spelling denote exactly the same finite
integer identity. Direct Fraction/int inputs and integer JSON spelling pass;
decimal JSON spelling hits the continuous-output gate before schema dispatch.
"""
from pathlib import Path
from fractions import Fraction as F
import json, sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT)]
sys.dont_write_bytecode = True
from eab.contact_record import records_from_json, ContactRecord
from eab.numeric_domain import ConstructionDomainError
from eab.readers.bdda3d import load_records
from tools.bdda3d_document import loads as tool_loads

identifier = 10**400
base = dict(source='g6o', step=0, contact_index=0, block_a=1, block_b=2)
folder = ROOT/'review/tmp/support_decimal_identity'; folder.mkdir(parents=True, exist_ok=True)
cases = []
for name in ('step', 'block_a'):
    raw = dict(base, **{name: identifier})
    as_int, = records_from_json(json.dumps([raw]))
    assert getattr(as_int, name) == identifier
    as_fraction = ContactRecord.from_dict(dict(base, **{name: F(identifier)}))
    assert getattr(as_fraction, name) == identifier
    text = json.dumps([dict(base, **{name: 'TOKEN'})]).replace('"TOKEN"', '1e400')
    try: records_from_json(text)
    except ConstructionDomainError as error:
        cases.append(f'ContactRecord.{name}: int/Fraction/integer JSON accepted exactly; decimal JSON rejected: {error}')
    else: raise AssertionError('setup changed: decimal identity no longer rejected')

raw = {'entrances': [{'bi':identifier, 'bj':2, 'etype':'np'}]}
integer_path = folder/'integer.json'; integer_path.write_text(json.dumps(raw), encoding='utf-8')
rec, = load_records(integer_path); assert rec.block_a == identifier
assert tool_loads(json.dumps(raw))['entrances'][0]['bi'] == identifier
text = json.dumps({'entrances':[{'bi':'TOKEN','bj':2,'etype':'np'}]}).replace('"TOKEN"', '1e400')
decimal_path = folder/'decimal.json'; decimal_path.write_text(text, encoding='utf-8')
for api, fn in (('bdda3d.load_records', lambda: load_records(decimal_path)),
                ('bdda3d_document.loads', lambda: tool_loads(text))):
    try: fn()
    except ConstructionDomainError as error:
        cases.append(f'{api}.bi: integer JSON accepted exactly; decimal JSON rejected: {error}')
    else: raise AssertionError('setup changed: decimal identity no longer rejected')
print('\n'.join(cases))
print('CONFIRMED CONTRACT MISMATCH: decimal spelling constrains otherwise unbounded exact integer identities')
