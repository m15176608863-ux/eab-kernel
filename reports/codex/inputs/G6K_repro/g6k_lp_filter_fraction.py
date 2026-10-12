"""Reduced-cost filter against independent Fraction dot; extremes and cancellation."""
import sys,math,random,json
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
import eab.lp as LP
rng=random.Random(111627)
def fl(v):
 try:return float(v)
 except OverflowError:return float('inf') if v>0 else float('-inf')
def randomq():
 v=F(rng.randrange(-1023,1024),rng.choice([1,3,7]));e=rng.randrange(-1500,1501)
 return v*(F(2)**e)
wrong=[]
for case in range(12000):
 m=1+case%5;A=[[randomq()] for _ in range(m)];b=[F(0)]*m;y=[randomq() for _ in range(m)]
 product=sum(yi*row[0] for yi,row in zip(y,A));delta=F(0) if case%4==0 else randomq();c=[product+delta]
 X=LP._Exact([[fl(v) for v in row] for row in A],[0.]*m,[fl(c[0])],exact=(A,b,c))
 got,_=X.reduced_sign(c,[fl(c[0])],y,[fl(v) for v in y],0);expected=(delta>0)-(delta<0)
 if got!=expected:wrong.append(dict(case=case,expected=expected,got=got))
result=dict(cases=12000,mismatches=wrong);print(json.dumps(result,indent=2));(ROOT/'review/agents/lp_filter_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');assert not wrong
