"""One real internal cone-filter mutation, with independent box-union truth.
Only a compiled in-memory function changes. The source file is never written;
we restore its pointer and verify its SHA-256 in finally. The mutant function
source is saved below review/copies, not in the production tree.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,math,inspect,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from eab.kernel3d.geom3 import Polyhedron,box
from eab.kernel3d.g03 import g0_distance_completeness3
from eab.kernel3d import covers3 as C
import eab.margin as margin
root=Path(__file__).resolve().parents[2]
source_path=Path(C.__file__)
before=hashlib.sha256(source_path.read_bytes()).hexdigest()
original=C._outside_dot_band
source=inspect.getsource(original)
anchor="    if value <= 0:"
assert source.count(anchor)==1
mutant_source=source.replace(anchor,"    if a[0] == a[1] == 0 and a[2] != 0:\n        return True\n"+anchor)
namespace=dict(vars(C));exec(compile(mutant_source,str(source_path),"exec"),namespace)
mutant=namespace["_outside_dot_band"]
copy_dir=root/"review/copies/geom3_g0_noise";copy_dir.mkdir(parents=True,exist_ok=True)
(copy_dir/"_outside_dot_band_mutant.py").write_text(mutant_source,encoding="utf-8")
q=math.ulp(1e8)

def make(T):
    a=box(center=(T,T,T),half=(q,q,q))
    p=box(center=(T,T,T-3*q),half=(q,q,q))
    r=box(center=(T+12*q,T,T),half=(q,q,q))
    b=Polyhedron(p.verts+r.verts,p.faces+[tuple(i+8 for i in f) for f in r.faces])
    return a,b,(p,r)

def independent_gap(A,components):
    # Distance between interval products equals norm of coordinate-interval
    # gaps, and distance to a finite union is the minimum component distance.
    def squared(P):
        total=F(0)
        for k in range(3):
            av=[F(v[k]) for v in A.verts];bv=[F(v[k]) for v in P.verts]
            g=max(F(0),min(av)-max(bv),min(bv)-max(av))
            total+=g*g
        return total
    result=min(map(squared,components))
    assert result==F(q)**2
    return q

def run(A,B):
    margin._resolved_cached.cache_clear()
    try:
        distance,label=margin.body_distance(A,B,tol=0);error=None
    except RuntimeError as exc:
        distance,label,error=None,None,str(exc)
    gate=g0_distance_completeness3(A,B,radius=0,samples=1,tol=0,atol=0)
    return dict(distance=distance,label=label,public_error=error,samples=gate.samples,
                worst_abs_error=gate.worst_abs_error,passed=gate.passed,failures=gate.failures)
rows=[]
try:
    for T in (0.,1e8):
        A,B,parts=make(T);truth=independent_gap(A,parts)
        C._outside_dot_band=original;baseline=run(A,B)
        assert baseline["distance"]==truth and baseline["passed"]
        C._outside_dot_band=mutant;bad=run(A,B)
        assert bad["samples"]==1
        if T:
            assert "missed the nearest pair" in bad["public_error"],bad
        else:
            assert "missed the nearest pair" in bad["public_error"]
        assert not bad["passed"],bad
        rows.append(dict(translation=T,all_inputs_binary64=True,independent_gap=truth,
                         baseline=baseline,mutant=bad))
finally:
    C._outside_dot_band=original;margin._resolved_cached.cache_clear()
    after=hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert after==before
print(json.dumps(dict(result="FIXED",rows=rows,
                     tracked_source_sha256_before=before,tracked_source_sha256_after=after,
                     mutation="real internal cone-band early reject for z-directed normals"),default=str,indent=2))
print("FIXED: at atol=0 the G0 distance-completeness gate rejects missing covers even after large translation")
