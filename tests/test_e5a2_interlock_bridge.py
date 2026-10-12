"""Minimal interlock bridge gates: independent rational extruded-profile oracle.

The oracle reads raw (x,y,z) coordinates only, reconstructs the two piecewise
linear height envelopes and solves strict affine interval inequalities. It
uses no production membership, normals, covers, ray, distance or triangulation.
"""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import inspect
import math
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from osteomorphic import interlocking_pair
from eab.kernel3d import interlock as I
from eab.kernel3d.geom3 import Polyhedron,box,polyhedra_overlap
from eab.kernel3d.exact_sweep import translate_exact


def _profile(P):
    data={}
    for x,y,z in P.verts:
        data.setdefault(F(x),[]).append(F(z))
    return [(x,min(z),max(z)) for x,z in sorted(data.items())]


def _at(profile,x,side):
    for a,b in zip(profile,profile[1:]):
        if a[0]<=x<=b[0]:
            return a[side]+(b[side]-a[side])*(x-a[0])/(b[0]-a[0])
    raise AssertionError('oracle x is outside its profile')


def _profile_data(A,B):
    a,b=_profile(A),_profile(B)
    lo,hi=max(a[0][0],b[0][0]),min(a[-1][0],b[-1][0])
    ys=[(min(F(p[1]) for p in P.verts),max(F(p[1]) for p in P.verts)) for P in (A,B)]
    if lo>=hi or max(v[0] for v in ys)>=min(v[1] for v in ys):
        return a,b,[]
    xs=sorted({lo,hi}|{v[0] for v in a+b if lo<v[0]<hi})
    return a,b,xs


def _intrudes(A,B):
    a,b,xs=_profile_data(A,B)
    for x0,x1 in zip(xs,xs[1:]):
        lower,upper=F(0),F(1)
        for first,second in ((a,b),(b,a)):
            d0=_at(first,x0,2)-_at(second,x0,1)
            d1=_at(first,x1,2)-_at(second,x1,1)
            if d0<=0 and d1<=0:
                upper=lower
                break
            if d0<=0:
                lower=max(lower,-d0/(d1-d0))
            if d1<=0:
                upper=min(upper,d0/(d0-d1))
        if lower<upper:
            return True
    return False


def _root(A,B):
    a,b,xs=_profile_data(A,B)
    return max([F(0)]+[_at(b,x,2)-_at(a,x,1) for x in xs])


def _pair(scale,translation):
    A,B=interlocking_pair(nx=5,ny=2,amp=.3*scale,phase=1.,lx=2*scale,ly=scale,lz=scale)
    return tuple(P.translated((translation,-translation,2*translation)) for P in (A,B))


@pytest.mark.parametrize('scale,translation',[(1.,0.),(1e-3,0.),(1e3,0.),(1.,1e6)])
@pytest.mark.parametrize('offset',[(0.,0.,0.),(-.21140068220020514,-.20949049564529884,0.),
                                    (.04305840516802706,-.08058664985244868,0.)])
def test_returned_lift_is_safe_for_actual_float_translation_against_independent_profile(scale,translation,offset):
    A,B=_pair(scale,translation);off=tuple(v*scale for v in offset)
    nominal=_root(translate_exact(A,off),B)
    sol=I.escape_height_covers(A,B,off)
    actual=translate_exact(A,sol.exact_offset)
    assert sol.exact_height==nominal, "exact affine root against independent profile"
    assert not _intrudes(actual,B), 'returned height, not a higher probe, must be safe'
    C=max(abs(v) for P in (A,B) for p in P.verts for v in p)
    assert abs(sol.height-scalar_exact(nominal)) <= 4e-12*scale+128*math.ulp(C), "constructed height must approximate the independent profile root"
    if _intrudes(translate_exact(A,off),B):
        assert sol.height>0, 'a true tiny initial intrusion cannot be reported as zero'


def test_positive_surface_report_band_never_changes_intruding_boolean():
    A=box(center=(F(0),)*3,half=(F(1),)*3)
    for d in (F(-1,2**80),F(0),F(1,2**80),F(1,10)):
        B=box(center=(F(2)+d,F(0),F(0)),half=(F(1),)*3)
        want=d<0
        assert (polyhedra_overlap(A,B,0)==1)==want
        assert (polyhedra_overlap(A,B,F(1,5))==1)==want


def test_disabling_upward_construction_is_caught_by_the_original_profile_error(monkeypatch):
    """E5a2 upward-float repair is superseded by exact root acceptance.

    The same original profile error is now guarded by a stronger mutation:
    bypassing the live exact nonpenetration certificate returns an earlier,
    penetrating event and the independent exact-root assertion catches it.
    """
    original=I._nonpenetrating_at
    def unchecked(A,B,offset,height):
        event_times={e.time for e in I.surface_events(A,B,start=offset)}
        return 0 if height>0 and height in event_times else original(A,B,offset,height)
    monkeypatch.setattr(I,'_nonpenetrating_at',unchecked)
    with pytest.raises(AssertionError,match="exact affine root"):
        test_returned_lift_is_safe_for_actual_float_translation_against_independent_profile(
            1.,0.,(-.21140068220020514,-.20949049564529884,0.))


@pytest.mark.parametrize('scale,shift',[(1.,0.),(2.,1024.),(.5,-2048.)])
def test_representable_root_preserves_actual_float_translation_safety(scale,shift):
    A=box(center=(shift,0.,1.75*scale),half=(.5*scale,)*3)
    B=box(center=(shift,0.,1.*scale),half=(.5*scale,)*3)
    sol=I.escape_height_covers(A,B,(0.,0.,0.))
    assert F(sol.height)==sol.exact_height==F(.25*scale)
    actual=A.translated((0.,0.,sol.height))
    assert not _intrudes(actual,B), 'returned height, not a higher probe, must be safe'
