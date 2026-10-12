"""Independent rational pricing and tiny bounded-LP vertex enumeration."""
import sys, json, random, itertools
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
import eab.lp as L

def gaussian(matrix, rhs):
    m=len(rhs); a=[list(map(F,r))+[F(v)] for r,v in zip(matrix,rhs)]
    for c in range(m):
        k=next((k for k in range(c,m) if a[k][c]),None)
        if k is None: return None
        a[c],a[k]=a[k],a[c]; t=a[c][c]; a[c]=[v/t for v in a[c]]
        for k in range(m):
            if k!=c:
                t=a[k][c]; a[k]=[x-t*y for x,y in zip(a[k],a[c])]
    return [r[-1] for r in a]

def vertex_minimum(A,b,c):
    m,n=len(b),len(c); candidates=[]
    for basis in itertools.combinations(range(n),m):
        x=gaussian([[r[j] for j in basis] for r in A],b)
        if x is not None and min(x)>=0:
            full=[F(0)]*n
            for j,v in zip(basis,x): full[j]=v
            candidates.append((sum(v*w for v,w in zip(full,c)),full))
    return min(candidates,key=lambda p:p[0])

def exact_sign(self,cost,costf,y,yf,j):
    r=cost[j]-sum(y[i]*self.A[i][j] for i in range(self.m))
    return (r>0)-(r<0), L._fl(r)

def main():
    rng=random.Random(7012); old=L._Exact.reduced_sign
    pricing=0
    scales=[F(2)**e for e in (-1100,-1074,-1000,-600,-200,0,200,600,1000,1100)]
    # Direct filter versus an independently formed rational dot product.
    for t in range(8000):
        m=rng.randrange(1,7)
        A=[[rng.choice(scales)*rng.randrange(-9,10)] for _ in range(m)]
        y=[rng.choice(scales)*rng.randrange(-9,10) for _ in range(m)]
        c=[rng.choice(scales)*rng.randrange(-9,10)]
        if t%3==0:
            c=[sum(yi*r[0] for yi,r in zip(y,A))+rng.choice(scales)*rng.choice((-1,0,1))]
        X=L._Exact([[L._fl(v) for v in r] for r in A],[0.0]*m,[L._fl(c[0])],exact=(A,[0]*m,c))
        s,_=X.reduced_sign(c,[L._fl(c[0])],y,[L._fl(v) for v in y],0)
        truth=c[0]-sum(yi*r[0] for yi,r in zip(y,A)); expected=(truth>0)-(truth<0)
        assert s==expected,(t,A,y,c,s,expected)
        pricing+=1
    bounded=0
    for t in range(180):
        # x+y+s0=b0, a*x+b*y+s1=b1, all coefficients positive:
        # feasible origin (with slacks), bounded decision variables.
        row=[F(rng.randrange(1,9))*rng.choice(scales[2:9]) for _ in range(2)]
        rhs=[F(rng.randrange(1,9))*rng.choice(scales[2:9]) for _ in range(2)]
        A=[[F(1),F(1),F(1),F(0)],[row[0],row[1],F(0),F(1)]]
        c=[-F(rng.randrange(1,9))*rng.choice(scales[2:9]),-F(rng.randrange(1,9))*rng.choice(scales[2:9]),F(0),F(0)]
        truth,_=vertex_minimum(A,rhs,c)
        args=([[L._fl(v) for v in r] for r in A],[L._fl(v) for v in rhs],[L._fl(v) for v in c])
        fast=L.solve(*args,exact=(A,rhs,c))
        L._Exact.reduced_sign=exact_sign
        try: pure=L.solve(*args,exact=(A,rhs,c))
        finally: L._Exact.reduced_sign=old
        assert fast.status==pure.status==L.OPTIMAL
        assert sum(v*w for v,w in zip(fast.exact_x,c))==truth
        assert fast.exact_x==pure.exact_x and fast.exact_y==pure.exact_y
        assert fast.x==list(map(L._fl,fast.exact_x)) and fast.y==list(map(L._fl,fast.exact_y))
        bounded+=1
    zero=L.solve([],[],[0.0,1.0])
    print(json.dumps({'pricing_cases':pricing,'bounded_vertex_oracle_cases':bounded,'all_equal':True,'zero_constraint_optimal':{'status':zero.status,'exact_x':zero.exact_x,'exact_y':zero.exact_y}},indent=2))

if __name__=='__main__': main()
