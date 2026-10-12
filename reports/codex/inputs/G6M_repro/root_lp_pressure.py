"""G6M 独立 LP 对拍。Oracle: Fraction Gaussian elimination + basis enumeration;
不调用 eab 求逆、主元、证书或约化成本算法。输入浮点视图仅被测侧使用。"""
from pathlib import Path
import sys, itertools, random, json, time, math
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab import lp

def independent_rows(A,b):
    if not A:return [],[],True
    n=len(A[0]); M=[list(row)+[bb] for row,bb in zip(A,b)]; rank=0
    for j in range(n):
        piv=next((i for i in range(rank,len(M)) if M[i][j]),None)
        if piv is None:continue
        M[rank],M[piv]=M[piv],M[rank]; q=M[rank][j];M[rank]=[v/q for v in M[rank]]
        for i in range(len(M)):
            if i!=rank:
                q=M[i][j];M[i]=[v-q*w for v,w in zip(M[i],M[rank])]
        rank+=1
    return [r[:-1] for r in M[:rank]],[r[-1] for r in M[:rank]],not any(r[-1] for r in M[rank:])

def basic_points(A,b,n):
    R,d,consistent=independent_rows(A,b)
    if not consistent:return []
    rank=len(R)
    if rank==0:return [[F(0)]*n]
    out=[]
    for basis in itertools.combinations(range(n),rank):
        M=[[row[j] for j in basis] for row in R]
        B,z,ok=independent_rows(M,d)
        if not ok or len(B)!=rank:continue
        if any(v<0 for v in z):continue
        x=[F(0)]*n
        for j,v in zip(basis,z):x[j]=v
        assert all(sum(a*v for a,v in zip(row,x))==bb for row,bb in zip(A,b))
        out.append(x)
    return out

def oracle(A,b,c):
    vs=basic_points(A,b,len(c))
    if not vs:return 'infeasible',None
    ray=basic_points(A+[c],[F(0)]*len(A)+[F(-1)],len(c))
    if ray:return 'unbounded',None
    return 'optimal',min(sum(a*v for a,v in zip(c,x)) for x in vs)

def fl(q):
    try:return float(q)
    except OverflowError:return math.copysign(math.inf,q>0 or -1)

def main():
    rng=random.Random(130013); counts={'lp_cases':0,'exact_views':0,'reduced_sign_cases':0,'status':{},'poison_checks':0};t0=time.time()
    exponents=(-400,-200,-20,0,20,200,400)
    for case in range(1000):
        m=rng.randrange(0,4);n=rng.randrange(1,6)
        A=[[F(rng.randrange(-3,4)) for j in range(n)] for i in range(m)]
        b=[F(rng.randrange(-4,5)) for i in range(m)];c=[F(rng.randrange(-4,5)) for j in range(n)]
        if case%2:
            rows=[F(10)**rng.choice(exponents) for i in range(m)];cols=[F(10)**rng.choice(exponents) for j in range(n)]
            A=[[v*rows[i]*cols[j] for j,v in enumerate(row)] for i,row in enumerate(A)];b=[v*s for v,s in zip(b,rows)];c=[v*s for v,s in zip(c,cols)]
        want, obj=oracle(A,b,c)
        r=lp.solve([[fl(q) for q in row] for row in A],[fl(q) for q in b],[fl(q) for q in c],exact=(A,b,c))
        assert r.status==want, (case,A,b,c,want,r)
        if want=='optimal':
            assert r.exact_x is not None and r.exact_y is not None
            assert all(v>=0 for v in r.exact_x)
            assert all(sum(a*v for a,v in zip(row,r.exact_x))==bb for row,bb in zip(A,b))
            assert sum(a*v for a,v in zip(c,r.exact_x))==obj
            assert all(sum(r.exact_y[i]*A[i][j] for i in range(m))<=c[j] for j in range(n))
            assert sum(bb*y for bb,y in zip(b,r.exact_y))==obj
            assert r.x==[fl(q) for q in r.exact_x] and r.y==[fl(q) for q in r.exact_y] and r.obj==fl(obj)
        counts['lp_cases']+=1;counts['exact_views']+=want=='optimal';counts['status'][want]=counts['status'].get(want,0)+1
    # Direct filtered dot-product stress: constructed close cancellation,
    # arbitrary rational conversion, subnormal and overflow views.
    for case in range(15000):
        m=rng.randrange(1,5)
        A=[[F(rng.randrange(-9,10),rng.randrange(1,10))*F(2)**rng.randrange(-1100,1100)] for i in range(m)]
        y=[F(rng.randrange(-9,10),rng.randrange(1,10))*F(2)**rng.randrange(-1100,1100) for i in range(m)]
        dot=sum(v[0]*w for v,w in zip(A,y));eps=F(rng.choice((-1,0,1)))*F(2)**rng.randrange(-2200,2200)
        c=[dot+eps]
        X=lp._Exact([[fl(q) for q in row] for row in A],[0.0]*m,[fl(c[0])],exact=(A,[F(0)]*m,c))
        got,_=X.reduced_sign(c,[fl(c[0])],y,[fl(q) for q in y],0)
        assert got==(eps>0)-(eps<0),(case,A,y,c,got,eps)
        counts['reduced_sign_cases']+=1
    counts['seconds']=time.time()-t0
    print(json.dumps(counts,indent=2));(ROOT/'review/evidence/root_lp_pressure.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
if __name__=='__main__':main()
