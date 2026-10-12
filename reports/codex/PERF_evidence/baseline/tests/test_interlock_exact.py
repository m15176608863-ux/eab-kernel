"""E5b exact earliest-event, certificate, mutation and cache gates.

Main wall oracle uses only test-only integer temporal triangle SAT and parity;
profile oracle uses independently triangulated star tetrahedra with swept SAT.
Neither calls production events, predicate, normal/cone or translation helpers.
"""
from fractions import Fraction as F
import math
import pytest
import test_interlock_walls as W
from e5b_wall_oracle import earliest_wall_escape, earliest_star_escape
from eab.kernel3d import interlock as I
from eab.kernel3d import exact_sweep as S
from eab.kernel3d.geom3 import Polyhedron,box


def _wall(seed=16):
    r=W.random.Random(seed)
    return W._place(W._key(),.7,1e5,r,4),W._place(W._prism_xz(W.U_PROF,-1,1),.7,1e5,r,4)


def _assert_exact_wall(A,B):
    sol=I.escape_height_covers(A,B,(0,0,0))
    assert sol.exact_height==earliest_wall_escape(A,B), 'exact earliest root including near-vertical events'
    return sol


def test_near_vertical_event_removal_is_killed_inside_live_event_path(monkeypatch):
    A,B=_wall();_assert_exact_wall(A,B)
    original=I.surface_events
    def omit(*args,**kw):
        return tuple(e for e in original(*args,**kw) if abs(e.normal[2])>F(1,10**8)*max(map(abs,e.normal)))
    monkeypatch.setattr(I,'surface_events',omit)
    with pytest.raises((AssertionError,ValueError),match='exact earliest root|exact surface event set'):
        _assert_exact_wall(A,B)


def _assert_interval_proof(sol):
    left=F(0)
    for a,b,m,state in sol.interval_certificate:
        assert a==left and a<m<b and state==1,'missing earlier candidate interval proof'
        left=b
    assert left==sol.exact_height,'missing earlier candidate interval proof'


def test_every_prior_candidate_interval_has_an_explicit_proof_and_mutation_is_killed(monkeypatch):
    A,B=_wall();sol=_assert_exact_wall(A,B);_assert_interval_proof(sol)
    original=I._prior_intervals
    def omit(*args):
        intervals=list(original(*args))
        yield from intervals[1:]
    monkeypatch.setattr(I,'_prior_intervals',omit)
    with pytest.raises(AssertionError,match='missing earlier candidate interval proof'):
        _assert_interval_proof(I.escape_height_covers(A,B,(0,0,0)))


def test_return_root_nonpenetration_certificate_cannot_be_omitted(monkeypatch):
    A,B=_wall();_assert_exact_wall(A,B)
    original=I._nonpenetrating_at
    def unchecked(A,B,off,h):
        times={e.time for e in I.surface_events(A,B,start=off)}
        return 0 if h>0 and h in times else original(A,B,off,h)
    monkeypatch.setattr(I,'_nonpenetrating_at',unchecked)
    with pytest.raises(AssertionError,match='exact earliest root|event completeness'):
        _assert_exact_wall(A,B)


def test_exact_sweep_cache_is_content_complete_and_matches_uncached_values():
    A=box();B=box(center=(0,0,-1.5))
    first=S.surface_events(A,B)
    av,af,bv,bf=tuple(A.verts),tuple(A.faces),tuple(B.verts),tuple(B.faces)
    direct=S._events_cached.__wrapped__(tuple(S.G.vector(v) for v in av),af,tuple(S.G.vector(v) for v in bv),bf,(F(0),F(0),F(1)),F(0),None)
    assert first==direct
    altered=Polyhedron([(x,y,z+F(1,8)) for x,y,z in av],af)
    changed=S.surface_events(altered,B)
    assert first!=changed,'source vertex content must be in the event cache key'
    assert S.surface_events(A,B,start=(0,0,F(1,8)))==changed
    assert S.surface_events(A,B,direction=(0,0,2))!=first


@pytest.mark.parametrize('window',[None,0,F(1,10**7)])
def test_explicit_window_contract_and_default_exactness(window):
    A,B=_wall(0)
    sol=I.escape_height_covers(A,B,(0,0,0),contact_window=window)
    if window:
        assert abs(sol.height-.2)<1e-6
        assert sol.window_core=='A'
    else:
        assert sol.exact_height==earliest_wall_escape(A,B)
        assert sol.height>1


def test_invalid_contact_window_is_rejected():
    with pytest.raises(ValueError,match='contact_window'):
        I.escape_height_covers(box(),box(),(0,0,0),contact_window=-1)

@pytest.mark.parametrize('scale,shift',[(F(1),F(0)),(F(1,1024),F(10**6)),(F(1024),F(-10**5))])
def test_first_escape_precedes_a_later_reentry_and_is_not_a_monotone_bisection(scale,shift):
    """Independent analytic interval oracle for two disjoint axis-aligned boxes.

    No production primitive supplies the answer: the lower obstacle's overlap
    interval ends at 3s/2, before a second component reenters at 2s. All geometry
    is exactly dyadic under translation and unit rescaling.
    """
    A=box(center=(shift,0,shift),half=(scale/2,)*3)
    lower=box(center=(shift,0,shift),half=(scale,)*3)
    upper=box(center=(shift,0,shift+3*scale),half=(scale/2,)*3)
    verts=list(lower.verts)+list(upper.verts)
    faces=list(lower.faces)+[tuple(i+len(lower.verts) for i in f) for f in upper.faces]
    B=Polyhedron(verts,faces)
    sol=I.escape_height_covers(A,B,(0,0,0))
    assert sol.exact_height==F(3,2)*scale
    assert I.escape_height_brute(A,B,(0,0,0),hi=5*scale)==float(sol.exact_height)
    _assert_interval_proof(sol)


@pytest.mark.parametrize('seed',[0,7,16,19])
def test_exact_contact_label_frozen_height_equals_the_exact_root(seed):
    A,B=_wall(seed)
    sol=I.escape_height_covers(A,B,(0,0,0))
    assert sol.exact_contact_label is not None
    assert sol.exact_contact_normal[2]>0
    frozen=I.escape_height_from_frozen_cover(A,B,sol.exact_contact_label,(0,0,0))
    assert frozen==sol.exact_height, 'frozen exact source facet must reproduce the rational root'

@pytest.mark.parametrize('scale,shift',[(F(1),F(0)),(F(1,1024),F(10**6)),(F(1024),F(-10**5))])
def test_window_earliest_root_uses_the_same_finite_certificates_as_margin(scale,shift):
    """Independent box projection gives h=1/4-w; checks default and window.

    Coordinate-axis displacement beats the conservative homothetic shell here.
    This gate catches the former mismatch (margin accepted h=.199 while escape
    searched only the star core and reported h about .19975).
    """
    from eab.margin import inflated_membership,ON_BOUNDARY,INSIDE
    A=box(center=(shift,0,shift+F(7,4)*scale),half=(scale/2,)*3)
    B=box(center=(shift,0,shift+scale),half=(scale/2,)*3)
    window=scale/16
    sol=I.escape_height_covers(A,B,(0,0,0),contact_window=window)
    assert sol.exact_height==(F(1,4)*scale-window)
    assert sol.window_core=='shift_2_1'
    at=S.translate_exact(A,sol.exact_offset)
    assert inflated_membership(at,B,delta=0,contact_window=window)==ON_BOUNDARY
    before=S.translate_exact(A,(0,0,sol.exact_height-scale/4096))
    assert inflated_membership(before,B,delta=0,contact_window=window)==INSIDE
