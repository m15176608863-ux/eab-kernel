"""Reproduce R13FIXb bdda3d JSON numeric-literal underflow before checked constructor.
Run: python -X utf8 review/repro/support_json_reader.py
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from fractions import Fraction
from eab.readers.bdda3d import load_records
from eab.numeric_domain import ConstructionDomainError

folder=Path(__file__).resolve().parents[1]/"tmp"/"support_json_reader"
folder.mkdir(parents=True,exist_ok=True)
for is_string in (False,True):
    path=folder/("numeric.json" if not is_string else "string.json")
    token='"1e-400"' if is_string else '1e-400'
    path.write_text('{"entrances":[{"bi":1,"bj":2,"etype":"np","area":'+token+'}]}',encoding="utf8")
    try:
        result=load_records(path)[0]
    except ConstructionDomainError as e:
        print(f"{path.name}: correctly rejected: {e}")
        assert is_string
    else:
        print(f"{path.name}: area={result.length_or_area!r}; exact decimal input=1/10**400 (nonzero)")
        assert not is_string and result.length_or_area == 0.0
print("CONFIRMED: actual numeric JSON token bypasses the reader range guard; string-token test alone misses this")
