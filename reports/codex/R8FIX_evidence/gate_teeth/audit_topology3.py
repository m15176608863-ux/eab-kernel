"""Independent rational chamber enumeration check; writes evidence only."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations,product
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from eab.kernel3d import entrance_topology as tested
OUT=Path(__file__).resolve().parent

def solve_unique(columns):
    # Independent elementary row elimination for convex combination weights.
    k=len(columns);matrix=[[F(col[i]) for col in columns]+[F(i==3)] for i in range(4)]
    pivotrow=0;pivots=[]
    for col in range(k):
        pivot=next((r for r in range(pivotrow,4) if matrix[r][col]),None)
        if pivot is None:continue
        matrix[pivotrow],matrix[pivot]=matrix[pivot],matrix[pivotrow]
        factor=matrix[pivotrow][col];matrix[pivotrow]=[v/factor for v in matrix[pivotrow]]
        for r in range(4):
            if r!=pivotrow:
                factor=matrix[r][col];matrix[r]=[a-factor*b for a,b in zip(matrix[r],matrix[pivotrow])]
        pivots.append(col);pivotrow+=1
    if pivotrow!=k or any(not any(row[:-1]) and row[-1] for row in matrix):return None
    answer=[F(0)]*k
    for row,col in enumerate(pivots):answer[col]=matrix[row][-1]
    return tuple(answer)

def feasible_strict(rows):
    # Gordan separation + Caratheodory: strict homogeneous inequalities are
    # feasible iff zero is outside the convex hull of signed normals. Any zero
    # convex combination has a witness on <=4 affinely independent normals.
    for size in range(1,min(4,len(rows))+1):
        for chosen in combinations(rows,size):
            weights=solve_unique([(*n,F(1)) for n in chosen])
            if weights is not None and all(w>=0 for w in weights):return False
    return True

def oracle_signs(normals):
    result=set()
    for signs in product((-1,1),repeat=len(normals)):
        if feasible_strict([tuple(s*c for c in n) for s,n in zip(signs,normals)]):result.add(signs)
    return result

cases=[('rank1',[(1,0,0)]),('rank2',[(1,0,0),(0,1,0),(1,1,0),(1,-1,0)]),
       ('rank3_axes',[(1,0,0),(0,1,0),(0,0,1)]),
       ('general6',[(1,k,k*k) for k in range(6)]),
       ('narrow_200bits',[(1,0,0),(1,F(1,2**200),0),(1,0,F(1,2**200)),(0,1,1),(0,1,-1)])]
rows=[]
source=Path(tested.__file__);before=hashlib.sha256(source.read_bytes()).hexdigest()
for name,normals in cases:
    normals=tuple(tuple(map(F,n)) for n in normals)
    start=time.perf_counter();want=oracle_signs(normals)
    directions=tuple(tested._chamber_directions(normals))
    dots=[tuple(sum(a*b for a,b in zip(n,d)) for n in normals) for d in directions]
    assert all(all(v for v in values) for values in dots),'representative on wall'
    actual={tuple(1 if v>0 else -1 for v in values) for values in dots}
    assert actual==want,(name,want-actual,actual-want)
    assert len(actual)==len(directions),'duplicate chambers'
    row={'case':name,'planes':len(normals),'expected_chambers':len(want),'actual_chambers':len(actual),
         'off_all_planes':True,'duplicate_count':len(directions)-len(actual),'seconds':time.perf_counter()-start}
    rows.append(row);print(row)
# Geometry count/cost is descriptive, not a separate mathematical oracle.
from test_r8fix_initial_state3 import _tight_pair,_extrude
from eab.kernel3d.geom3 import box,Polyhedron
geometry=[]
for name,A,B in [('tight_seam',*_tight_pair()),('ordinary_face_touch',box((0,0,2)),box())]:
    start=time.perf_counter();central,noncentral=tested._configuration_planes(A,B)
    directions=tuple(tested._chamber_directions(central));state=tested.entrance_membership3(A,B)
    geometry.append({'case':name,'central_planes':len(central),'noncentral_directions':len(noncentral),
                     'chambers':len(directions),'state':state,'seconds':time.perf_counter()-start})
    print(geometry[-1])
after=hashlib.sha256(source.read_bytes()).hexdigest();assert before==after
(OUT/'topology3_chamber_audit.json').write_text(json.dumps({'source_sha256':before,'chamber_cases':rows,'geometry_diagnostics':geometry,
 'independence':'Expected signs use elementary Fraction Gaussian elimination, Gordan separation and Caratheodory subsets; no tested angular, plane, cross, dot or overlap primitive.'},indent=2),encoding='utf-8')
