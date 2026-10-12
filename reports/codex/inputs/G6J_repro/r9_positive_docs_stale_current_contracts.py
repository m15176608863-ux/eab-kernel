from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from test_r9fix_docs import CASES,_assert_current_contract
rows=[]
for path,current,stale,required,meaning in CASES:
    text=(ROOT/path).read_text(encoding='utf-8-sig')
    _assert_current_contract(text,stale,required,meaning)
    rows.append(dict(path=path,meaning=meaning,result='FIXED',current=current))
print(json.dumps(rows,ensure_ascii=False,indent=2))
