"""R8 gate teeth: faults are compiled INSIDE the tested implementation.

Truth uses interval products or the independent raw-coordinate convex oracle;
no output records are appended or edited after enumeration.
"""
from fractions import Fraction as F
import inspect
import math
import sys

import pytest
from eab.kernel3d import covers3 as C, geom3 as G, g03
import eab.margin as M
import test_invariance_geom as T


def convex_view_mutant(monkeypatch, fault):
    original = G.exact_convex_view
    source = inspect.getsource(original)
    anchor = "        P._convex_view = P\n        return P\n    order ="
    if fault == "drop_vertex":
        body = """        if len(P.verts) >= 8 and max(abs(x) for v in P.verts for x in v) > 100:
            bad = merge_coplanar(convex_hull_3d(P.verts[:-1]), 0.0)
"""
    else:
        body = """        if max(abs(x) for v in P.verts for x in v) > 100:
            bad = Polyhedron(list(P.verts), list(P.faces[1:])+list(P.faces[:1]))
"""
    replacement = "        P._convex_view = P\n" + body + """            bad._sync_geometry_cache()
            bad._convex_view = bad
            P._convex_view = (tuple(bad.verts), tuple(bad.faces), bad.source_vertices, bad.source_faces)
            return bad
        return P
    order ="""
    assert source.count(anchor) == 1
    scope = dict(vars(G))
    exec(compile(source.replace(anchor, replacement), __file__, "exec"), scope)
    for module in (G, g03, T):
        monkeypatch.setattr(module, "exact_convex_view", scope["exact_convex_view"])


def reject_z_inside_cone_filter(monkeypatch):
    source = inspect.getsource(C._outside_dot_band)
    anchor = "    if value <= 0:"
    assert source.count(anchor) == 1
    source = source.replace(anchor, "    if a[0] == a[1] == 0 and a[2] != 0:\n        return True\n" + anchor)
    scope = dict(vars(C))
    exec(compile(source, __file__, "exec"), scope)
    monkeypatch.setattr(C, "_outside_dot_band", scope["_outside_dot_band"])


def interval_union_pair(translation, scale=1):
    q = math.ulp(1e8) * scale
    t = translation
    a = G.box(center=(t,t,t), half=(q,q,q))
    p = G.box(center=(t,t,t-3*q), half=(q,q,q))
    r = G.box(center=(t+12*q,t,t), half=(q,q,q))
    b = G.Polyhedron(p.verts+r.verts, p.faces+[tuple(i+8 for i in f) for f in r.faces])
    def distance2(part):
        return sum(max(F(0), min(F(v[k]) for v in a.verts)-max(F(v[k]) for v in part.verts),
                       min(F(v[k]) for v in part.verts)-max(F(v[k]) for v in a.verts))**2 for k in range(3))
    truth2 = min(distance2(part) for part in (p,r))
    assert truth2 == F(q)**2, "independent interval-product distance"
    return a,b,q


@pytest.mark.parametrize("fault,name", [("drop_vertex","tetra_box_vv"), ("drop_vertex","generic"),
                                       ("source_faces","tetra_box_vv"), ("source_faces","generic"),
                                       ("source_faces","ve3_wedge")])
def test_g6h05_migrated_facet_gate_rejects_internal_convex_view_fault(monkeypatch, fault, name):
    T.test_cover_labels_and_strictness_are_invariant(name,0,1000.,1.)
    convex_view_mutant(monkeypatch, fault)
    with pytest.raises(AssertionError, match="raw-coordinate|stable-source"):
        T.test_cover_labels_and_strictness_are_invariant(name,0,1000.,1.)


@pytest.mark.parametrize("translation,scale", [(0.,1), (1e3,1), (1e8,1), (1e8,8)])
def test_g6h06_g0_detects_internal_missing_cover_without_coordinate_floor(monkeypatch, translation, scale):
    a,b,q = interval_union_pair(translation,scale)
    baseline = g03.g0_distance_completeness3(a,b,radius=0,samples=1,tol=0,atol=0)
    assert baseline.samples == 1 and baseline.passed
    reject_z_inside_cone_filter(monkeypatch)
    result = g03.g0_distance_completeness3(a,b,radius=0,samples=1,tol=0,atol=0)
    assert result.samples == 1 and not result.passed, "exact nearest-cover completeness must reject missing z covers"
    assert result.worst_abs_error == 9*q


@pytest.mark.parametrize("translation,scale", [(0.,1), (1e3,1), (1e8,1), (1e8,8)])
def test_g6h06_margin_detects_internal_missing_cover_without_coordinate_floor(monkeypatch, translation, scale):
    a,b,q = interval_union_pair(translation,scale)
    M._resolved_cached.cache_clear()
    assert M.body_distance(a,b,tol=0)[0] == q
    reject_z_inside_cone_filter(monkeypatch)
    M._resolved_cached.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="missed the nearest pair"):
            M.body_distance(a,b,tol=0)
    finally:
        M._resolved_cached.cache_clear()


@pytest.mark.parametrize("gate,args", [
    ("test_support_gaps_scale_and_membership_is_invariant", ("generic",0,1000.,1.)),
    ("test_g0_three_votes_are_invariant", ("generic",0,1000.,1.)),
    ("test_vote_two_ambiguity_band_is_pinned_on_the_generic_cells", (1e5,0,0,39)),
])
@pytest.mark.parametrize("fault", ["drop_vertex","source_faces"])
def test_r8fix_same_family_migrated_oracles_reject_view_corruption(monkeypatch, gate, args, fault):
    checker = getattr(T,gate)
    checker(*args)
    convex_view_mutant(monkeypatch,fault)
    with pytest.raises(AssertionError):
        checker(*args)



def all_branch_convex_view_mutant(monkeypatch, fault):
    """Mutate the hull construction or canonical face numbering, not its outputs."""
    import test_frozen_ee_sign as frozen_gate
    source = inspect.getsource(G.exact_convex_view)
    if fault == "drop_all":
        anchor = "convex_hull_3d(P.verts)"
        replacement = "convex_hull_3d(P.verts[:-1] if len(P.verts)>=8 and max(abs(x) for v in P.verts for x in v)>100 else P.verts)"
        assert source.count(anchor)==1
        source = source.replace(anchor,replacement)
    else:
        source = source.replace("if (len(source) == len(P.verts)", "if (False and len(source) == len(P.verts)")
        anchor = "    out._sync_geometry_cache()\n    out._convex_view = out"
        assert source.count(anchor)==1
        source = source.replace(anchor,"    out.faces = out.faces[1:] + out.faces[:1]\n"+anchor)
    scope=dict(vars(G));exec(compile(source,__file__,"exec"),scope)
    for module in (G,g03,frozen_gate):
        monkeypatch.setattr(module,"exact_convex_view",scope["exact_convex_view"])


@pytest.mark.parametrize("target,fault", [("yaw","permute_canonical"),("frozen","drop_all")])
def test_r8fix_other_migrated_facet_oracles_keep_raw_source_geometry(monkeypatch,target,fault):
    import test_covers3_g0_vote2 as vote
    import test_frozen_ee_sign as frozen_gate
    if target=="yaw":
        checker=lambda:vote.test_yawed_stack_passes_g0_under_random_rotations(1e-3,1)
    else:
        checker=lambda:frozen_gate.test_frozen_ee_orientation_agrees_with_ee_cover_and_facet_normal3_on_every_ee_pair(1e-3,4,1e3)
    checker()
    all_branch_convex_view_mutant(monkeypatch,fault)
    with pytest.raises(AssertionError,match="raw-coordinate"):
        checker()
