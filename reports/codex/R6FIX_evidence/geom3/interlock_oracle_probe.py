"""Locate the full-suite candidate mismatch before changing the test oracle."""
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'src')]
import test_invariance_interlock as T
import e5a_escape_oracle as O
from eab.kernel3d.interlock import escape_candidates

original=O.move
def rounded_move(vertices,offset):
    return tuple(tuple(p[k]+offset[k] for k in range(3)) for p in vertices)
def exact_move(vertices,offset):
    return tuple(tuple(F(p[k])+F(offset[k]) for k in range(3)) for p in vertices)
cells=((0.,.001,1),(0.,1.,3),(0.,1000.,0),(1000.,1000.,1))
for translation,scale,index in cells:
    a,b=T._ilock('z0.7',translation,scale)
    off=T._vec(T.ROT_Z['z0.7'],scale,T.OFFSETS[index])
    got={lab for _,lab in escape_candidates(a,b,off)}
    O.move=rounded_move;O._candidates.cache_clear()
    old={lab for _,lab,_,_ in O.candidates(a,b,off)[0]}
    O.move=exact_move;O._candidates.cache_clear()
    corrected={lab for _,lab,_,_ in O.candidates(a,b,off)[0]}
    print('cell',translation,scale,'offset',T.OFFSETS[index],flush=True)
    print('original oracle minus production:',sorted(old-got),flush=True)
    print('production minus original oracle:',sorted(got-old),flush=True)
    print('exact affine independent oracle symmetric difference:',sorted(got^corrected),flush=True)
    moved0=rounded_move(a.verts,off);moved1=exact_move(a.verts,off)
    print('vertices with unequal exact coordinates:',sum(p!=q for p,q in zip(moved0,moved1)),flush=True)
    assert old!=got
    assert corrected==got
O.move=original;O._candidates.cache_clear()
print('MISMATCH_ROOT_CAUSE_CONFIRMED: rounded-vs-exact affine input, independent geometric primitives unchanged')
