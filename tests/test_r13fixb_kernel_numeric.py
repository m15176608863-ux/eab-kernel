"""R13FIX-b public-kernel construction gates.

Oracles use inline Fraction algebra, Cartesian interval endpoints, and Decimal
sqrt; none calls production geometry, constructions, predicates, or G0 helpers.
The scale grids include asymmetric non-dyadic data, not just value-preserving
renaming of tests. Exact-valued APIs retain their all-finite domain.
"""
from fractions import Fraction as F
from decimal import Decimal, localcontext
import math
import random
import pytest

from eab.kernel2d import exact as E2, covers as C2, g0 as G2, g0_oracle as O2
from eab.kernel2d import entrance as EN2
from eab.kernel3d import exact_geom as E3, exact_sweep as SW, g03_exact as O3
from eab.kernel3d import g03_surface_oracle as SO3, g03 as G3, covers3 as C3
from eab.kernel3d import entrance3 as EN3
from eab.kernel3d.geom3 import Polyhedron

SCALES = (F(1, 2**400), F(1), F(2**397))
FACES = ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))

def box(s, shift=(0,0,0)):
    v = ((0,0,0),(1,0,0),(1,2,0),(0,2,0),(0,0,3),(1,0,3),(1,2,3),(0,2,3))
    return Polyhedron([tuple(s*(F(p[k])+F(shift[k])) for k in range(3)) for p in v], list(FACES))

def rect(s, shift=(0,0)):
    return [tuple(s*(F(x)+F(t)) for x,t in zip(p,shift)) for p in ((0,0),(1,0),(1,2),(0,2))]

def qvec(p): return tuple(F(x) for x in p)
def minus(a,b): return tuple(F(x)-F(y) for x,y in zip(a,b))
def scalar(a,b): return sum(F(x)*F(y) for x,y in zip(a,b))
def cross(a,b):
    a,b=qvec(a),qvec(b)
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def root(q):
    with localcontext() as c:
        c.prec=250
        return float((Decimal(q.numerator)/Decimal(q.denominator)).sqrt())

@pytest.mark.parametrize('s',SCALES)
def test_exact_public_vector_arithmetic_matches_inline_rational(s):
    # float coefficients expose early rounding at every scale, exact products
    # differ from Fraction(float_product) even when the final display agrees.
    a=tuple(float(s*v) for v in (F(7,5),F(-11,7),F(13,9)))
    b=tuple(float(s*v) for v in (F(2,3),F(5,11),F(-17,13)))
    qa,qb=qvec(a),qvec(b)
    assert E3.vector(a)==qa
    assert E3.sub(a,b)==tuple(float(x) for x in minus(qa,qb))
    assert E3.add(a,b)==tuple(float(x+y) for x,y in zip(qa,qb))
    assert E3.mul(a,F(5,7))==tuple(float(x*F(5,7)) for x in qa)
    assert E3.dot(a,b)==float(scalar(qa,qb))
    assert E3.cross(a,b)==tuple(float(x) for x in cross(qa,qb))
    assert O3.qpoint(a)==qa
    assert O3.minus(a,b)==minus(qa,qb)
    assert O3.scalar(a,b)==scalar(qa,qb)
    assert O3.wedge(a,b)==cross(qa,qb)
    assert SO3.minus(a,b)==minus(qa,qb)
    assert SO3.dot(a,b)==scalar(qa,qb)
    assert SO3.cross(a,b)==cross(qa,qb)
    c=tuple(float(s*v) for v in (F(3,7),F(17,11),F(23,13)))
    d=tuple(float(s*v) for v in (F(-5,9),F(2,7),F(19,17)))
    assert O3.volume(a,b,c,d)==scalar(cross(minus(b,a),minus(c,a)),minus(d,a))
    triangle=(a,b,c)
    assert E3.normal(triangle)==cross(minus(b,a),minus(c,a))

@pytest.mark.parametrize('s',SCALES)
def test_2d_exact_oracle_quantities_match_independent_formulas(s):
    P=rect(s); Q=rect(s,(4,0))
    assert E2.signed_area2(P)==4*s*s
    raw=tuple((float(x+s*F(1,7)),float(y+s*F(2,9))) for x,y in P)
    qr=tuple(qvec(p) for p in raw)
    assert O2.points(raw)==qr
    delta=(s*F(1,3),-s*F(2,7))
    assert O2.translate(raw,delta)==tuple(tuple(x+t for x,t in zip(p,delta)) for p in qr)
    a,b,c=raw[:3]
    u,v=minus(b,a),minus(c,a)
    assert O2.turn(a,b,c)==u[0]*v[1]-u[1]*v[0]
    p=(float(s*F(1,5)),float(s*F(7,5)))
    a,b=(0.,0.),(float(3*s),0.)
    assert O2.segment_square(p,a,b)==(F(p[1])**2,F(p[0])/(3*s))
    assert O2.sqrt_display(9*s*s)==float(3*s)
    assert O2.distance(P,Q)==(float(3*s),('A-vertex/B-edge',1,0,0.0))
    assert G2.brute_ray_exit(P,P,(s,0))==1
    assert O2.ray_exit(P,P,(s,0))==1
    assert G2.char_length(P)==root(5*s*s)

@pytest.mark.parametrize('s',SCALES)
def test_exact_entrance_block_and_float_vertices_each_component(s):
    A=rect(s); B=rect(s,(4,F(1,3)))
    ex=E2.entrance_block_exact(A,B)
    expected=((3*s,F(-5,3)*s),(5*s,F(-5,3)*s),(5*s,F(7,3)*s),(3*s,F(7,3)*s))
    assert tuple(ex.vertices)==expected
    assert tuple(ex.pairs)==((2,0),(3,1),(0,2),(1,3))
    for k,f in enumerate(ex.facets):
        assert f.start==expected[k]
        assert f.direction==minus(expected[(k+1)%4],expected[k])
        assert f.label==('FF',(2+k)%4,k)
    a0=(s*F(1,7),s*F(-1,11))
    display=C2.convex_entrance_block(A,B,a0)
    assert display.vertices==[tuple(float(x+y) for x,y in zip(p,a0)) for p in expected]
    assert display.facets==[('FF',(2+k)%4,k) for k in range(4)]
    assert display.vv==list(ex.pairs)

@pytest.mark.parametrize('s',SCALES)
def test_exact_surface_constructions_and_intersections(s):
    P=box(s); delta=(s*F(1,7),s*F(-1,11),s*F(2,3))
    moved=SW.translate_exact(P,delta)
    assert moved.verts==[tuple(x+y for x,y in zip(p,delta)) for p in P.verts]
    assert moved.faces==P.faces
    triangles=E3.triangles(P)
    assert len(triangles)==12
    expected_triangles=[(fi,tuple(P.verts[j] for j in ids)) for fi,f in enumerate(P.faces)
        for ids in ((f[-1],f[0],f[1]),(f[1],f[2],f[3]))]
    assert triangles==expected_triangles
    for fi,tri in triangles:
        assert all(p in tuple(P.verts[j] for j in P.faces[fi]) for p in tri)
        assert len(tri)==3
        # Each returned exact coordinate is checked against original coordinates.
        assert all(isinstance(x,F) for p in tri for x in p)
    tri=((0,0,0),(3*s,0,0),(0,3*s,0))
    p=(s/3,s/5,-s); q=(s/3,s/5,2*s)
    assert E3.segment_triangle(p,q,tri)==((s/3,s/5,F(0)),F(1,3))
    rawtri=tuple(tuple(float(x) for x in p) for p in tri)
    assert E3.segment_triangle(tuple(float(x) for x in p),tuple(float(x) for x in q),rawtri)==((F(float(s/3)),F(float(s/5)),F(0)),F(1,3))
    inner=((s/3,s/5,0),(s/2,s/5,0),(s/3,s/2,0))
    assert set(E3.triangle_intersection(tri,inner))==set(inner)
    core=SW.star_core(P,s/2)
    # Box centre=(1/2,1,3/2)*s; L1 radius=3*s, alpha=1/6.
    centre=(s/2,s,3*s/2)
    assert core.verts==[tuple(c+(v-c)*F(5,6) for c,v in zip(centre,p)) for p in P.verts]
    models=SW.contact_models(P,P,s/2)
    assert [m[0] for m in models]==['core_A','core_B','exact','shift_0_-1','shift_0_1','shift_1_-1','shift_1_1','shift_2_-1','shift_2_1']
    for label,a,b in models:
        expected=core.verts if label=='core_A' else P.verts
        if label.startswith('shift_'):
            _,axis,sign=label.split('_'); axis=int(axis); sign=int(sign)
            expected=[tuple(v+(sign*s/2 if k==axis else 0) for k,v in enumerate(p)) for p in P.verts]
        assert a.verts==expected
        assert b.verts==(core.verts if label=='core_B' else P.verts)

@pytest.mark.parametrize('s',SCALES)
def test_surface_events_each_exact_time_and_normal(s):
    A=box(s); B=box(s,(0,0,5))
    events=SW.surface_events(A,B,direction=(0,0,s))
    assert {e.time for e in events}=={F(2),F(5),F(8)}
    for e in events:
        assert isinstance(e.time,F)
        kind,fa,fb=e.label
        if kind=='VF':
            face=B.faces[fb[1]]; verts=[B.verts[i] for i in face]
            expected=cross(minus(verts[1],verts[0]),minus(verts[2],verts[0]))
        elif kind=='FV':
            face=A.faces[fa[1]]; verts=[A.verts[i] for i in face]
            expected=tuple(-x for x in cross(minus(verts[1],verts[0]),minus(verts[2],verts[0])))
        else:
            expected=cross(minus(A.verts[fa[2]],A.verts[fa[1]]),minus(B.verts[fb[2]],B.verts[fb[1]]))
        assert e.normal==expected

@pytest.mark.parametrize('s',SCALES)
def test_oracle_hulls_planes_sat_and_boundary_quantities(s):
    P=box(s); av=tuple(P.verts)
    points,faces,planes=O3.hull(av)
    assert points==tuple(sorted(av))
    expected_planes={((-1,0,0),0),((0,-1,0),0),((0,0,-1),0)}
    for axis,end in enumerate((s,2*s,3*s)):
        n=tuple(end.denominator if k==axis else 0 for k in range(3))
        expected_planes.add((n,end.numerator))
    assert set(planes)==expected_planes
    assert len(faces)==6
    for ring,(n,h) in zip(faces,planes):
        assert set(ring)=={i for i,p in enumerate(points) if scalar(n,p)==h}
    q=O3.plane_key((s,2*s,0),3*s)
    assert q==((1,2,0),3)
    diff,dfaces,dplanes=O3.difference_hull(av,av)
    assert set(diff)=={minus(b,a) for a in av for b in av}
    assert len(dfaces)==6 and len(dplanes)==6
    expected_difference_planes={(tuple(sign*end.denominator if k==axis else 0 for k in range(3)),end.numerator)
        for axis,end in enumerate((s,2*s,3*s)) for sign in (-1,1)}
    assert set(dplanes)==expected_difference_planes
    for ring,(n,h) in zip(dfaces,dplanes):
        assert set(ring)=={i for i,p in enumerate(diff) if scalar(n,p)==h and all(abs(p[k])==v for k,v in enumerate((s,2*s,3*s)))}
    rows=O3.sat_model(av,av)
    expected_axes={n for n,_ in expected_planes} | {tuple(sign if k==axis else 0 for k in range(3)) for axis in range(3) for sign in (-1,1)}
    assert {row[0] for row in rows}==expected_axes
    for n,ln,ld,hn,hd in rows:
        vals=[scalar(n,p) for p in av]
        assert F(ln,ld)==min(vals)-max(vals)
        assert F(hn,hd)==max(vals)-min(vals)
    probes,counts=O3.boundary_probes(av,av)
    assert counts==(8,12,6)
    # Product {-L,0,L} with at least one extreme and excluding edge-centre duplicate patterns.
    import itertools
    expected={tuple(p) for p in itertools.product((-s,0,s),(-2*s,0,2*s),(-3*s,0,3*s)) if any(p)}
    assert set(probes)==expected
    labels,degenerate=O3.support_labels(av,tuple(P.faces),av,tuple(P.faces))
    assert labels==set() and degenerate==6

@pytest.mark.parametrize('s',SCALES)
def test_surface_oracle_exact_distances_and_coordinate_bounds(s):
    A=box(s); B=box(s,(4,0,0))
    assert SO3.bounds(A.verts)==((0,s),(0,2*s),(0,3*s))
    assert SO3.separated_distance(A.verts,A.faces,B.verts,B.faces,squared=True)==9*s*s
    assert SO3.separated_distance(A.verts,A.faces,B.verts,B.faces)==float(3*s)
    assert SO3.face_pieces(tuple(A.verts),A.faces[0])==(A.faces[0],)

@pytest.mark.parametrize('s',SCALES)
def test_random_coordinate_samplers_round_only_final_affine_value(s):
    A=rect(s,(F(1,3),F(1,7))); B=rect(s,(4,F(2,3)))
    rng=random.Random(13); ref=random.Random(13)
    want=[]
    for _ in range(4):
        row=[]
        for k in range(2):
            lo=min(p[k] for p in B)-max(p[k] for p in A)
            hi=max(p[k] for p in B)-min(p[k] for p in A)
            pad=(hi-lo)/4; low,high=lo-pad,hi+pad
            row.append(float(low+F(ref.random())*(high-low)))
        want.append(tuple(row))
    assert G2.sample_translations(A,B,4,rng)==want
    A3=box(s,(F(1,3),F(1,7),F(2,9))); B3=box(s,(4,F(2,3),F(3,7)))
    rng=random.Random(17); ref=random.Random(17); want=[]
    for _ in range(4):
        row=[]
        for k in range(3):
            lo=min(p[k] for p in B3.verts)-max(p[k] for p in A3.verts)
            hi=max(p[k] for p in B3.verts)-min(p[k] for p in A3.verts)
            pad=(hi-lo)/4; low,high=lo-pad,hi+pad
            row.append(float(low+F(ref.random())*(high-low)))
        want.append(tuple(row))
    assert G3.sample_translations3(A3,B3,4,rng)==want

@pytest.mark.parametrize('s',SCALES)
def test_brute_entrance_2d_and_3d_independent_cartesian_time_bound(s):
    # Cartesian interval overlap begins at exactly t=3. Closed-contact scanner
    # returns at most one binary64 ulp above that exact time.
    A=rect(s); B=rect(s,(4,0))
    t2=EN2.first_entrance_brute(A,B,(0,0),(s,0),t_max=7,steps=8)
    A3=box(s); B3=box(s,(4,0,0))
    t3=EN3.first_entrance_brute(A3,B3,(0,0,0),(s,0,0),t_max=7,steps=8)
    assert 3 <= t2 <= math.nextafter(3.,math.inf)
    assert 3 <= t3 <= math.nextafter(3.,math.inf)

@pytest.mark.parametrize('s',SCALES)
def test_g0_success_report_numeric_fields_are_analytic(s):
    from dataclasses import asdict
    P=rect(s)
    rep=G2.g0_convex(P,P,samples=0)
    assert asdict(rep)==dict(samples=16,band_skipped=0,mismatches=[],facet_local=0,facet_global=0,
        facet_symmetric_diff=[],facet_ambiguous=16,hull_vertex_mismatch=0,hull_vertex_ambiguous=0,boundary_probes=16)
    rep=G2.g0_distance_completeness(P,P,[(4*s,0)])
    assert asdict(rep)==dict(draws=1,overlapping=0,touching=0,samples=1,worst_abs_error=0.,failures=[])
    rep=G2.g0_exit_completeness(P,P,[(0,0)],[(s,0)])
    assert asdict(rep)==dict(draws=1,separated=0,touching=0,samples=1,worst_witness=0.,failures=[])
    P3=box(s)
    rep=G3.g0_convex3(P3,P3,samples=0)
    assert asdict(rep)==dict(samples=26,band_skipped=0,mismatches=[],facet_local=0,facet_global=0,
        facet_degenerate=6,facet_ambiguous=0,facet_local_dropped=0,facet_symmetric_diff=[],hull_vertex_mismatch=0,
        hull_vertices=8,e_vertices=8,e_vertices_ambiguous=0,boundary_probes=26,boundary_checked=26,boundary_kinds=(8,12,6))
    rep=G3.g0_distance_completeness3(P3,P3,radius=0,base=(4*s,0,0),samples=1)
    assert asdict(rep)==dict(samples=1,skipped_intersecting=0,worst_abs_error=0.,failures=[],completeness_failures=[],construction_failures=[])

@pytest.mark.parametrize('s',SCALES)
def test_cover_selector_constraints_margin_and_enumeration_numeric_fields(s):
    A2,B2=rect(s),rect(s,(4,0))
    c=C2.first_entrance_for_vertex(A2,1,B2,window=10*s)
    assert (c.kind,c.a_index,c.b_index)==('VE',1,3)
    assert (c.normal,c.gap,c.param,c.point,c.point_a,c.point_b)==((-1.,0.),float(3*s),1.,(float(4*s),0.),(s,0),(float(4*s),0.))
    A,B=box(s),box(s,(4,0,0))
    assert C3.cone_constraints(A,0,B,6)==[(0,0,-3*s),(0,-2*s,0),(-s,0,0),(-s,0,0),(0,-2*s,0),(0,0,-3*s)]
    margin,noise=C3.cone_intersection_margin(A,0,B,6)
    assert margin==root(F(1,3))
    assert noise==float(5*F(64)*F(math.ulp(1.)))
    covers=C3.enumerate_covers3(A,B,window=5*s)
    assert len(covers)==48
    assert {c.kind for c in covers}=={'VF','FV','EE','VE3','EV3'}
    for c in covers:
        pa=pb=None; params=(); area2=None
        if c.kind in ('VF','FV'):
            V,vi,P,fi=(A,c.a_feature[1],B,c.b_feature[1]) if c.kind=='VF' else (B,c.b_feature[1],A,c.a_feature[1])
            verts=[P.verts[k] for k in P.faces[fi]]
            n=tuple(sum(cross(a,b)[k] for a,b in zip(verts,verts[1:]+verts[:1])) for k in range(3))
            point=V.verts[vi]; q=scalar(n,minus(point,verts[0])); nn=scalar(n,n)
            projection=tuple(v-q*x/nn for v,x in zip(point,n))
            pa,pb=(point,projection) if c.kind=='VF' else (projection,point)
            area2=nn/4
            gap_sign=(q>0)-(q<0);gap2=q*q/nn
            if c.kind=='FV': n=tuple(-v for v in n)
        elif c.kind=='EE':
            ai,aj=c.a_feature[1:]; bi,bj=c.b_feature[1:]
            a,b=A.verts[ai],B.verts[bi];u,v=minus(A.verts[aj],a),minus(B.verts[bj],b)
            n=cross(v,u)
            # Independent support-set inequalities, not production edge arcs.
            if not (all(scalar(n,minus(x,b))<=0 for x in B.verts) and all(scalar(n,minus(x,a))>=0 for x in A.verts)):
                n=tuple(-x for x in n)
            nn=scalar(n,n);w=minus(b,a);uv=cross(u,v)
            ta=scalar(cross(w,v),uv)/scalar(uv,uv);tb=scalar(cross(w,u),uv)/scalar(uv,uv)
            params=(ta,tb);pa=tuple(x+ta*y for x,y in zip(a,u));pb=tuple(x+tb*y for x,y in zip(b,v))
            q=scalar(n,minus(pa,pb));gap_sign=(q>0)-(q<0);gap2=q*q/nn
        else:
            V,vi,P,edge=(A,c.a_feature[1],B,c.b_feature[1:]) if c.kind=='VE3' else (B,c.b_feature[1],A,c.a_feature[1:])
            point=V.verts[vi];a=P.verts[edge[0]];d=minus(P.verts[edge[1]],a)
            t=scalar(minus(point,a),d)/scalar(d,d);params=(t,)
            projection=tuple(x+t*y for x,y in zip(a,d));n=minus(point,projection)
            gap2=scalar(n,n);gap_sign=1
            pa,pb=(point,projection) if c.kind=='VE3' else (projection,point)
            if c.kind=='EV3':n=tuple(-x for x in n)
        assert c.point_a==tuple(float(x) for x in pa)
        assert c.point_b==tuple(float(x) for x in pb)
        assert c.params==tuple(float(x) for x in params)
        assert c.exact_params==(params if params else None)
        assert c.exact_normal_direction==n
        nn=scalar(n,n)
        assert c.normal==tuple(math.copysign(root(v*v/nn),v) if v else 0. for v in n)
        assert c.gap==gap_sign*root(gap2)
        assert c.exact_gap_squared==gap2 and c.exact_gap_sign==gap_sign
        assert c.area==(root(area2) if area2 is not None else None)
        assert c.exact_area_squared==area2
        assert c.in_extent

@pytest.mark.parametrize('integer_scale',(1,7,2**397))
def test_integer_surface_model_every_numeric_field(integer_scale):
    # model explicitly consumes an integer payload after denominator clearing;
    # its lowest nonzero input is 1. Rational low-end is covered by separated_distance.
    P=box(F(integer_scale)); verts=tuple(tuple(int(x) for x in p) for p in P.verts)
    model=SO3.model(verts,tuple(P.faces)); vv,rings,edges,bounds,reps=model
    assert vv==verts and reps==(verts[0],)
    assert bounds==((0,integer_scale),(0,2*integer_scale),(0,3*integer_scale))
    expected_normals=((0,0,-1),(0,0,1),(0,-1,0),(1,0,0),(0,1,0),(-1,0,0))
    for face,ring,n in zip(P.faces,rings,expected_normals):
        vertices,normal,height,norm2,axes,bbox=ring
        assert vertices==tuple(verts[i] for i in face)
        assert normal==n and height==scalar(n,vertices[0]) and norm2==1
        assert axes==tuple(k for k in range(3) if not n[k])
        assert bbox==tuple((min(p[k] for p in vertices),max(p[k] for p in vertices)) for k in range(3))
    expected_edges=((0,1),(0,3),(0,4),(1,2),(1,5),(2,3),(2,6),(3,7),(4,5),(4,7),(5,6),(6,7))
    assert edges==tuple((verts[a],verts[b]) for a,b in expected_edges)

@pytest.mark.parametrize('s',SCALES)
def test_random_polygon_constructed_coordinates_have_independent_rng_reference(s):
    ref=random.Random(41)
    points=[(float(-s+2*s*F(ref.random())),float(-s+2*s*F(ref.random()))) for _ in range(8)]
    # An input point is extreme iff it is an endpoint of a support line.
    def det(a,b,c):
        u,v=minus(b,a),minus(c,a)
        return u[0]*v[1]-u[1]*v[0]
    expected=set()
    for a in points:
        for b in points:
            if a==b:continue
            signs=[det(a,b,p) for p in points]
            if min(signs)>=0 or max(signs)<=0:expected.update((a,b))
    got=G2.random_convex_polygon(random.Random(41),scale=s)
    assert set(got)==expected
    assert len(got)==len(expected)

@pytest.mark.parametrize('scale',(F(1,2**401),F(2**401),-F(2**401)))
def test_random_polygon_named_support_domain_rejection(scale):
    from eab.numeric_domain import ConstructionDomainError
    with pytest.raises(ConstructionDomainError,match='random_convex_polygon.scale'):
        G2.random_convex_polygon(random.Random(41),scale=scale)

@pytest.mark.parametrize('api',('char_length','sqrt_display','distance','sample2','sample3','raw_dot','surface_distance'))
def test_extended_full_domain_constructions_reject_unrepresentable_output(api):
    from eab.numeric_domain import ConstructionDomainError
    s=F(2**1100)
    with pytest.raises(ConstructionDomainError):
        if api=='char_length':G2.char_length(rect(s))
        elif api=='sqrt_display':O2.sqrt_display(s*s)
        elif api=='distance':O2.distance(rect(s),rect(s,(4,0)))
        elif api=='sample2':G2.sample_translations(rect(s),rect(s,(4,0)),1,random.Random(1))
        elif api=='sample3':G3.sample_translations3(box(s),box(s,(4,0,0)),1,random.Random(1))
        elif api=='raw_dot':E3.dot((2**1000,0,0),(2.**1000,0,0))
        elif api=='surface_distance':SO3.separated_distance(box(s).verts,FACES,box(s,(4,0,0)).verts,FACES)

@pytest.mark.parametrize('s',(F(1,2**1200),F(2**1200)))
def test_exact_rational_constructions_keep_full_domain_without_artificial_rejection(s):
    a,b=(s,2*s,3*s),(s/3,s/5,s/7)
    assert E3.sub(a,b)==minus(a,b)
    assert E3.dot(a,b)==scalar(a,b)
    assert E3.cross(a,b)==cross(a,b)
    assert O3.scalar(a,b)==scalar(a,b)
    assert O2.segment_square((s,s),(0,0),(3*s,0))==(s*s,F(1,3))
    assert E2.entrance_block_exact(rect(s),rect(s)).vertices==[(-s,-2*s),(s,-2*s),(s,2*s),(-s,2*s)]


def test_scale_grid_has_distinct_public_numeric_products():
    assert len({G2.char_length(rect(s)) for s in SCALES})==3
    assert len({E3.dot((s,s,s),(s,s,s)) for s in SCALES})==3
    assert len({tuple(C2.convex_entrance_block(rect(s),rect(s)).vertices) for s in SCALES})==3

@pytest.mark.parametrize('s',SCALES)
def test_in_domain_raw_dot_cancellation_is_not_erased(s):
    q=math.nextafter(1.,math.inf)
    a=(float(s*q),float(s),0.)
    b=(q,-(1+2**-51),0.)
    expected=scalar(a,b)
    assert expected!=0
    assert E3.dot(a,b)==float(expected)

@pytest.mark.parametrize('s',SCALES)
def test_surface_events_non_dyadic_exact_times(s):
    A=box(s); B=box(s,(0,0,F(11,3)))
    events=SW.surface_events(A,B,direction=(0,0,7*s))
    assert {e.time for e in events}=={F(2,21),F(11,21),F(20,21)}

@pytest.mark.parametrize('s',SCALES)
def test_exact_area_nondyadic_raw_values_match_shoelace(s):
    P=[(s*F(1,7),s*F(2,9)),(s*F(13,11),s*F(5,13)),(s*F(17,19),s*F(23,29))]
    want=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(P,P[1:]+P[:1]))
    assert E2.signed_area2(P)==want

@pytest.mark.parametrize('s',SCALES)
def test_facet_vote_anomaly_numeric_payload_has_independent_plane_reference(s):
    A=box(s)
    # Intentionally supplying the positive-octant body hull instead of B-A
    # makes exactly the three coordinate-zero planes fail h=maxB-minA.
    got=G3.facet_vote3(A,A,set(),A,list(A.verts))
    expected=[('hull_anomaly',n,2,2) for n in ((-1,0,0),(0,-1,0),(0,0,-1))]
    assert got==(0,3,0,0,sorted(expected))


def _install_internal_expression_fault(monkeypatch,module,name,old,new,scale):
    """Change the kernel's expression before records/enumeration, never outputs."""
    import inspect,textwrap
    source=textwrap.dedent(inspect.getsource(getattr(module,name)))
    assert old in source
    namespace=dict(vars(module));namespace['_r13_fault_scale']=scale
    exec(compile(source.replace(old,new,1),'<r13fixb-internal-expression-fault>','exec'),namespace)
    monkeypatch.setattr(module,name,namespace[name])

@pytest.mark.parametrize('s',SCALES)
def test_2d_g0_nonzero_diagnostics_and_failure_payload_are_independent(s,monkeypatch):
    from dataclasses import asdict
    # Inject a real projection construction defect inside _project, before
    # scalar construction and Cover creation. Exact enumeration is untouched.
    _install_internal_expression_fault(monkeypatch,C2,'_project',
        'A[0] + t * e[0]', 'A[0] + t * e[0] - _r13_fault_scale',s)
    A=[(0,s),(s,s),(s,2*s),(0,2*s)]
    B=[(0,0),(s,0),(s,3*s),(0,3*s)]
    # Both A vertices project into B's right edge; no coincident VV exists.
    # True separation is 3s; the defective foot is shifted left s => 4s.
    x=(4*s,0)
    rep=G2.g0_distance_completeness(A,B,[x],atol=0)
    arg=('A-vertex/B-edge',0,1,float(F(1,3)))
    assert asdict(rep)==dict(draws=1,overlapping=0,touching=0,samples=1,
        worst_abs_error=float(s),failures=[(x,float(4*s),float(3*s),arg)])
    assert not rep.passed
    # Independent interval exit parameter=1. Defective foot produces witness s.
    rep=G2.g0_exit_completeness(A,B,[(0,0)],[(s,0)],atol=0)
    assert asdict(rep)==dict(draws=1,separated=0,touching=0,samples=1,
        worst_witness=float(s),failures=[((0,0),(s,0),F(1),float(s),arg)])
    assert not rep.passed

@pytest.mark.parametrize('s',(F(1,2**400),F(1),F(2**395)))
def test_3d_g0_nonzero_diagnostics_and_failure_payload_are_independent(s,monkeypatch):
    from dataclasses import asdict
    # Defect is in the internal coordinate constructor before VF/FV/EE records.
    # No post-enumeration fabricated cover or post-report payload is introduced.
    _install_internal_expression_fault(monkeypatch,C3,'_float_vector',
        'vector_rational(v, allow_underflow=True)',
        'vector_rational((v[0]-_r13_fault_scale,v[1],v[2]), allow_underflow=True)',s)
    P=box(s)
    A=Polyhedron([(x,y+4*s,z+4*s) for x,y,z in P.verts],P.faces)
    B=Polyhedron([(x,8*y,8*z) for x,y,z in P.verts],P.faces)
    # A's yz projection is strictly inside the large face, so all closest
    # exact candidates remain VF at distance 3s. Constructed foot x=s becomes0.
    x=(4*s,F(0),F(0)); failure=(x,float(4*s),float(3*s))
    rep=G3.g0_distance_completeness3(A,B,radius=0,base=x,samples=1,atol=0)
    assert asdict(rep)==dict(samples=1,skipped_intersecting=0,worst_abs_error=float(s),
        failures=[failure],completeness_failures=[],construction_failures=[failure])
    assert not rep.passed

@pytest.mark.parametrize('s',SCALES)
def test_surface_event_label_time_binding_matches_independent_xy_elimination(s):
    """Oracle: scalar x/y elimination plus source box rings; no geometry helper.

    Parallel projected edges are partitioned by endpoint incidences; transversal
    projected edges have a unique 2x2 rational solution. This binds each label
    to its own event times and rejects label/time permutations preserving sets.
    """
    A=box(s);B=box(s,(0,0,F(11,3)));speed=7*s
    expected=set()
    for kind,V,P in (('VF',A,B),('FV',B,A)):
        for vi,p in enumerate(V.verts):
            for fi in (0,1):
                face=[P.verts[i] for i in P.faces[fi]]
                if all(min(v[k] for v in face)<=p[k]<=max(v[k] for v in face) for k in (0,1)):
                    t=((face[0][2]-p[2]) if kind=='VF' else (p[2]-face[0][2]))/speed
                    label=(kind,('vertex',vi),('face',fi)) if kind=='VF' else (kind,('face',fi),('vertex',vi))
                    if t>=0:expected.add((label,t))
    def edges(P):
        tris=[ids for f in P.faces for ids in ((f[-1],f[0],f[1]),(f[1],f[2],f[3]))]
        return sorted({tuple(sorted((a,b))) for tri in tris for a,b in zip(tri,tri[1:]+tri[:1])})
    def endpoint_parameter(point,a,b):
        changed=next((k for k in (0,1) if b[k]!=a[k]),None)
        if changed is None:
            return (F(0),F(1)) if point[:2]==a[:2] else ()
        r=(point[changed]-a[changed])/(b[changed]-a[changed])
        return (r,) if 0<=r<=1 and all(point[k]==a[k]+r*(b[k]-a[k]) for k in (0,1)) else ()
    for ai,aj in edges(A):
        a,c=A.verts[ai],A.verts[aj]
        for bi,bj in edges(B):
            b,d=B.verts[bi],B.verts[bj]
            ux,uy=c[0]-a[0],c[1]-a[1];vx,vy=d[0]-b[0],d[1]-b[1]
            wx,wy=b[0]-a[0],b[1]-a[1];det=ux*vy-uy*vx
            times=set()
            if det:
                r=(wx*vy-wy*vx)/det;q=(wx*uy-wy*ux)/det
                if 0<=r<=1 and 0<=q<=1:
                    times.add((b[2]+q*(d[2]-b[2])-a[2]-r*(c[2]-a[2]))/speed)
            else:
                for p in (a,c):
                    for q in endpoint_parameter(p,b,d):times.add((b[2]+q*(d[2]-b[2])-p[2])/speed)
                for p in (b,d):
                    for r in endpoint_parameter(p,a,c):times.add((p[2]-a[2]-r*(c[2]-a[2]))/speed)
            label=('EE',('edge',ai,aj),('edge',bi,bj))
            expected.update((label,t) for t in times if t>=0)
    actual={(e.label,e.time) for e in SW.surface_events(A,B,direction=(0,0,speed))}
    assert actual==expected
    assert len(actual)>50

@pytest.mark.parametrize('s',(F(1,2**400),F(1),F(2**395)))
def test_3d_g0_nonempty_completeness_payload_matches_omitted_nearest_face(s,monkeypatch):
    from dataclasses import asdict
    # Omit the nearest real VF family at the actual enumeration call site.
    # All remaining covers are generated by production constructors; no fake
    # data is appended, and no report/candidate list is post-edited.
    _install_internal_expression_fault(monkeypatch,C3,'enumerate_covers3',
        'c = vf_cover(A, ia, B, fb, tol, extent_tol)',
        'c = None if fb == 3 else vf_cover(A, ia, B, fb, tol, extent_tol)',s)
    P=box(s)
    A=Polyhedron([(x,y+4*s,z+4*s) for x,y,z in P.verts],P.faces)
    B=Polyhedron([(x,8*y,8*z) for x,y,z in P.verts],P.faces)
    x=(4*s,F(0),F(0))
    # Cartesian true closest face x=s gives 3s. Removing that family leaves
    # the far x=0 face at distance5s; the closest retained boundary edge has
    # components(3s,4s), also5s. Hence minimum2=25s² vs truth2=9s².
    rep=G3.g0_distance_completeness3(A,B,radius=0,base=x,samples=1,atol=0)
    failure=(x,float(5*s),float(3*s))
    assert asdict(rep)==dict(samples=1,skipped_intersecting=0,worst_abs_error=float(2*s),
        failures=[failure],completeness_failures=[(x,25*s*s,9*s*s)],construction_failures=[failure])
    assert not rep.passed
