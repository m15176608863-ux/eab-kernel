"""Whole-src AST inventory + independent rational3/predicate/LP probes."""
from pathlib import Path
import ast,sys,json,random,math,itertools
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import eab.lp as lp
import eab.predicates as pred
import eab.rational3 as r3

inventory=[]
for path in (ROOT/'src/eab').rglob('*.py'):
    source=path.read_text(encoding='utf-8-sig'); tree=ast.parse(source)
    parents={child:node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        if not isinstance(node,(ast.If,ast.Compare,ast.IfExp)): continue
        s=ast.get_source_segment(source,node.test if isinstance(node,(ast.If,ast.IfExp)) else node) or ''
        if not any(t in s.lower() for t in ('tol','noise','band','window','eps','_feas','_piv','_uncertain','_flip','_tiny','bound','ordinary','1e-')): continue
        p=node
        while p in parents and not isinstance(p,(ast.FunctionDef,ast.AsyncFunctionDef)):
            p=parents[p]
        inventory.append(dict(file=str(path.relative_to(ROOT)).replace('\\','/'),line=node.lineno,
                              function=p.name if isinstance(p,ast.FunctionDef) else '<module>',condition=s))
(ROOT/'review/notes/whole_src_branches.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding='utf8')

rng=random.Random(20261012)
scales=[-1150,-1075,-1074,-1050,-600,-200,-1,0,1,200,600,1000,1100]
rc=0
for _ in range(1500):
    a,b=[tuple(F(rng.randrange(-11,12),rng.randrange(1,13))*F(2)**rng.choice(scales) for i in range(3)) for j in range(2)]
    assert r3.dot(a,b)==sum(x*y for x,y in zip(a,b))
    assert r3.cross(a,b)==(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    rc+=1
pc=0
for _ in range(4000):
    a,b=[tuple(F(rng.randrange(-11,12),rng.randrange(1,13))*F(2)**rng.choice(scales) for i in range(2)) for j in range(2)]
    # Mix operand types to actually traverse the float conversion filter.
    b=tuple(float(x) if abs(x)<=F(2)**1023 and rng.randrange(2) else x for x in b)
    cross=F(a[0])*F(b[1])-F(a[1])*F(b[0]); dot=F(a[0])*F(b[0])+F(a[1])*F(b[1])
    assert pred.cross2_sign(a,b)==(cross>0)-(cross<0)
    assert pred.dot2_sign(a,b)==(dot>0)-(dot<0)
    pc+=1
oc=0
for _ in range(1500):
    points=[tuple(F(rng.randrange(-11,12),rng.randrange(1,13))*F(2)**rng.choice(scales) for i in range(3)) for j in range(4)]
    # The oracle expands the determinant by permutations, not production formula.
    a,b,c,p=points
    cols=[[q[k]-a[k] for k in range(3)] for q in (b,c,p)]
    det=sum(((-1)**sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3)))*
            cols[0][perm[0]]*cols[1][perm[1]]*cols[2][perm[2]] for perm in itertools.permutations(range(3)))
    assert pred.orient3d(*points)==(det>0)-(det<0)
    oc+=1
print(json.dumps(dict(src_files=len(list((ROOT/'src/eab').rglob('*.py'))),branch_inventory=len(inventory),
                      rational3_pairs=rc,mixed_2d_filter_pairs=pc,orient3d_permutation_oracle=oc,all_equal=True),indent=2))
