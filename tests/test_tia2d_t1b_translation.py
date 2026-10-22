"""Global topology gates; oracles are explicit rational paths and hand boxes.

The oracle neither calls GlobalEntrance2 nor constructs production obstacles:
its path/barrier certificates are checked by independent input-polygon SAT.
"""
from fractions import Fraction as Q
import inspect
import random

import pytest

from eab.adapters.tia2d import tolerance_dovetail
from eab.kernel2d import translation_space as space
from eab.kernel2d.erosion import erode_polygon_exact, square_element
from eab.kernel2d.translation_certificates import verify_escape_certificate, verify_trapping_certificate


def rect(x0, y0, x1, y1):
    return tuple((Q(x), Q(y)) for x, y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)))


def test_large_clearance_remains_trapped_with_certified_wobble_bounds():
    moving = rect(-1,-1,1,1)
    fixed = (rect(-5,-5,5,-4), rect(-5,4,5,5), rect(-5,-4,-4,4), rect(4,-4,5,4))
    result = space.translation_component(moving, fixed)
    assert result.status == "TRAPPED_TRANSLATION"
    assert result.verification.valid and result.bounds_verification.valid
    # Exact component is [-3,3]^2 (the corner contacts cannot fit the square).
    assert result.area_bounds[0] <= 36 <= result.area_bounds[1]
    assert result.diameter_squared_bounds[0] <= 72 <= result.diameter_squared_bounds[1]
    assert result.inner_square_radius == 3


def bent_exit():
    moving = rect(Q(-1,8),Q(-1,8),Q(1,8),Q(1,8))
    # Three sides and a top baffle; exit requires a bend around x=2.
    fixed = (rect(-4,-4,4,-3),rect(-4,-3,-3,4),rect(3,-3,4,4),rect(-3,1,2,2))
    return moving, fixed


def assert_bent_exit():
    moving, fixed = bent_exit()
    independent = ((0,0),(Q(5,2),0),(Q(5,2),20))
    assert verify_escape_certificate(moving,fixed,independent).valid
    result = space.translation_component(moving,fixed)
    assert result.status == "ESCAPABLE_TRANSLATION"
    assert result.reason == "arrangement_free_path"
    assert result.verification.valid and len(result.path) >= 3


def test_nonconvex_obstacle_union_requires_bent_escape_not_hull():
    assert_bent_exit()


def test_mutation_hull_obstruction_is_detected_by_semantic_escape_gate(monkeypatch):
    # Real internal source mutation, not a fake result appended after execution.
    source = inspect.getsource(space.translation_component)
    old = "cells = tuple(dict.fromkeys(c for model in models for c in model.cells))"
    new = "cells = (__import__('eab.kernel2d.global_entrance', fromlist=['_hull'])._hull(p for model in models for c in model.cells for p in c),)"
    assert source.count(old) == 1
    namespace = dict(space.__dict__)
    exec(compile(source.replace(old,new), '<hull_mutant>', 'exec'),namespace)
    monkeypatch.setattr(space,'translation_component',namespace['translation_component'])
    with pytest.raises(AssertionError):
        assert_bent_exit()


def test_zero_tolerance_seam_is_not_confused_with_closed_obstacle():
    moving = rect(0,0,1,1)
    fixed = (rect(-2,-5,0,5),rect(1,-5,3,5))
    result = space.translation_component(moving,fixed)
    assert result.status == "ESCAPABLE_TRANSLATION"
    assert result.verification.valid


def test_dovetail_threshold_bracket_keeps_both_independent_certificates():
    data = tolerance_dovetail()
    result = space.critical_tolerance(data['moving'],data['obstacles'],0,Q(1,4),iterations=5)
    assert result['status'] == 'CERTIFIED_BRACKET'
    assert result['low'] < Q(1,6) <= result['high']
    assert result['high']-result['low'] == Q(1,128)
    assert result['low_result'].verification.valid
    assert result['high_result'].verification.valid
    assert result['attained'] is None


def test_invalid_erosion_and_resource_limits_never_claim_escape():
    data=tolerance_dovetail()
    result=space.tolerance_component(data['moving'],data['obstacles'],2)
    assert result.status == 'UNPROVED' and 'erosion_rejected' in result.reason
    assert space.translation_component(data['moving'],data['obstacles'],max_cells=0).status=='UNPROVED'
    assert space.translation_component(rect(0,0,1,1),(rect(0,0,2,2),)).reason=='origin_in_open_obstacle'
    bracket=space.critical_tolerance(data['moving'],data['obstacles'],0,2,iterations=2)
    assert bracket['status']=='UNPROVED' and bracket['attained'] is None


@pytest.mark.parametrize('scale',[Q(1,1024),Q(1),Q(8)])
@pytest.mark.parametrize('translation',[0,1000,100000])
def test_exact_rotation_large_translation_and_units(scale,translation):
    rng=random.Random(823)
    u=Q(rng.randrange(1,12),rng.randrange(13,25))
    c,s=(1-u*u)/(1+u*u),2*u/(1+u*u)
    def rotate(p): return (c*p[0]-s*p[1],s*p[0]+c*p[1])
    def physical(poly):
        return tuple((scale*rotate(p)[0]+translation,scale*rotate(p)[1]-2*translation) for p in poly)
    data=tolerance_dovetail()
    delta=Q(1,16)
    original=space.tolerance_component(data['moving'],data['obstacles'],delta)
    moving=physical(data['moving']); fixed=tuple(physical(p) for p in data['obstacles'])
    element=tuple(rotate(p) for p in square_element())
    actual=space.tolerance_component(moving,fixed,scale*delta,element=element)
    assert original.status==actual.status=='TRAPPED_TRANSLATION'
    a=erode_polygon_exact(moving,scale*delta,element).polygon
    bs=tuple(erode_polygon_exact(p,scale*delta,element).polygon for p in fixed)
    transformed_path=tuple((scale*rotate(p)[0],scale*rotate(p)[1]) for p in original.path)
    assert verify_trapping_certificate(a,bs,transformed_path).valid
    assert actual.bounds_verification.valid


@pytest.mark.parametrize('scale',[Q(1,1024),Q(8)])
def test_bounds_scale_exactly_when_axes_do_not_rotate(scale):
    data=tolerance_dovetail()
    result=space.tolerance_component(data['moving'],data['obstacles'],Q(1,16))
    scaled=lambda p: tuple((scale*x+100000,scale*y-170003) for x,y in p)
    actual=space.tolerance_component(scaled(data['moving']),tuple(scaled(p) for p in data['obstacles']),scale/16)
    assert actual.area_bounds==tuple(scale**2*x for x in result.area_bounds)
    assert actual.diameter_squared_bounds==tuple(scale**2*x for x in result.diameter_squared_bounds)
