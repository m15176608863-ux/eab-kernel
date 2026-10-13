"""O02: independent completed Fraction coordinate/jet oracles.

References use scalar Fraction formulas and sampled math sin/cos coefficients;
no production Dual arithmetic, shape helper, geometry predicate or constructor
calculates an expected value. Sampling/libm is the documented approximate model,
not a claim of correctly rounded transcendental functions.
"""
from fractions import Fraction as F
import math

import pytest

from eab.dual import Dual
from eab.numeric_domain import ConstructionDomainError
from tools import osteomorphic as shape


@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("exponent", [-100, -400])
@pytest.mark.parametrize("scale", [F(1), F(2)**-100, F(2)**100])
def test_shape_dual_complete_coordinate_keeps_midpoint_residual(axis, exponent, scale):
    center = [0, 0, 0]
    residual = F(2)**exponent
    center[axis] = Dual(residual, (1.0, -3.0))
    kwargs = dict(nx=2, ny=2, lx=2*scale, ly=2*scale, amp=0)
    result = shape.osteomorphic_block_generic(center=center, **kwargs)
    raw_center = list(center)
    raw_center[axis] = residual
    raw = shape.osteomorphic_block(center=raw_center, **kwargs)
    # i=j=1, top: index 2*((ny+1)*i+j).
    actual = result.verts[8][axis]
    expected = float(residual - scale + 2*scale*F(1,2))
    assert actual.v == expected == raw.verts[8][axis], "complete coordinate residual"
    assert actual.e == (1.0, -3.0), "complete coordinate channels"


@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("length_seed", [F(2)**60, F(2)**1000])
def test_shape_dual_complete_jet_keeps_midpoint_residual(axis, length_seed):
    center = [0, 0, 0]
    center[axis] = Dual(0.0, (1.0, -3.0))
    kwargs = dict(nx=2, ny=2, lx=2, ly=2, amp=0)
    kwargs[("lx", "ly")[axis]] = Dual(2.0, (length_seed, -length_seed))
    actual = shape.osteomorphic_block_generic(center=center, **kwargs).verts[8][axis]
    expected = tuple(float(c - s/2 + s*F(1,2))
                     for c, s in zip((F(1), F(-3)), (length_seed, -length_seed)))
    assert actual.e == expected, "complete jet residual"


def test_shape_dual_complete_z_keeps_height_and_jet_residuals():
    residual = F(2)**-100
    actual = shape.osteomorphic_block_generic(nx=1, ny=1,
        center=(0, 0, Dual(residual, (1.0,))),
        lz=Dual(2.0, (F(2)**60,)), amp=Dual(-1.0, (-F(2)**59,)),
        phase=math.pi/2).verts[0][2]
    assert actual.v == float(residual), "complete height residual"
    assert actual.e == (1.0,), "complete height jet residual"


def test_shape_generic_pair_translation_stays_exact_until_final_vertices():
    residual = F(2)**-100
    upper, lower = shape.interlocking_pair_generic(nx=1, ny=1, lz=2, amp=0,
        center=(0,0,Dual(-1+residual,(F(1),))))
    assert upper.verts[1][2].v == float(residual), "complete pair translation residual"
    assert upper.verts[1][2] == lower.verts[0][2], "pair interface and jet agree"


@pytest.mark.parametrize("seed,amp", [(F(2)**-1074,F(2)**400),
                                      (F(2)**1200,F(2)**-400)])
def test_shape_phase_jet_is_scaled_before_final_range_check(seed, amp):
    # cos(pi/2) is a tiny nonzero libm coefficient, not mathematical zero.
    expected = float(amp*F(math.cos(math.pi/2))*seed)
    assert expected != 0 and math.isfinite(expected)
    try:
        actual = shape.osteomorphic_block_generic(nx=1, ny=1, amp=amp,
            phase=Dual(math.pi/2, (seed,))).verts[0][2]
    except ConstructionDomainError as exc:
        pytest.fail("representable complete phase jet rejected: " + str(exc))
    assert actual.e == (expected,), "complete phase jet"


@pytest.mark.parametrize("seed", [F(2)**-2000, F(2)**2000])
def test_shape_complete_jet_outside_output_domain_fails_by_name(seed):
    with pytest.raises(ConstructionDomainError, match="osteomorphic.*jet"):
        shape.osteomorphic_block_generic(nx=1, ny=1,
            center=(Dual(0.0,(seed,)),0,0), amp=0)


@pytest.mark.parametrize("scale", [F(2)**-100, F(1), F(2)**100])
def test_shape_general_position_all_vertices_and_channels_round_once(scale):
    nx, ny, phase = 5, 3, 0.4
    values = [F(2)*scale, F(3)*scale, F(5)*scale, F(1,8)*scale]
    seeds = [(F(7),F(-9)),(F(4),F(8)),(F(2)**60,F(11)),(F(-6),F(5))]
    center = [Dual(F(c)*scale,(F(d),F(e)))
              for c,d,e in ((7,1,3),(-9,2,-4),(11,-3,8))]
    result = shape.osteomorphic_block_generic(nx=nx,ny=ny,
        lx=Dual(values[0],seeds[0]), ly=Dual(values[1],seeds[1]),
        lz=Dual(values[2],seeds[2]), amp=Dual(values[3],seeds[3]),
        center=center,phase=Dual(phase,(F(13),F(-15))))
    for i in range(nx+1):
        u=F(i/nx)
        s=F(math.sin(2*math.pi*float(u)+phase))
        c=F(math.cos(2*math.pi*float(u)+phase))
        for j in range(ny+1):
            v=F(j/ny)
            for side in (0,1):
                sign=1-2*side
                actual=result.verts[2*((ny+1)*i+j)+side]
                want_v=(center[0].v+values[0]*(u-F(1,2)),
                        center[1].v+values[1]*(v-F(1,2)),
                        center[2].v+sign*values[2]/2+values[3]*s)
                want_e=tuple((center[0].e[k]+seeds[0][k]*(u-F(1,2)),
                              center[1].e[k]+seeds[1][k]*(v-F(1,2)),
                              center[2].e[k]+sign*seeds[2][k]/2
                              +seeds[3][k]*s+values[3]*c*(13,-15)[k])
                             for k in range(2))
                assert tuple(q.v for q in actual)==tuple(float(q) for q in want_v)
                assert tuple(q.e for q in actual)==tuple(
                    tuple(float(want_e[k][axis]) for k in range(2)) for axis in range(3))


@pytest.mark.parametrize("component", ["coordinate", "jet", "height"])
def test_shape_internal_rounded_addition_mutation_has_teeth(monkeypatch, component):
    original=shape._ShapeJet.__add__
    def rounded_addition(self,other):
        exact=original(self,other)
        return shape._ShapeJet(F(float(exact.v)),tuple(F(float(a)) for a in exact.e))
    monkeypatch.setattr(shape._ShapeJet,"__add__",rounded_addition)
    # Mutation is inside actual coordinate evaluation, not post-hoc fake output.
    if component=="coordinate":
        with pytest.raises(AssertionError,match="complete coordinate residual"):
            test_shape_dual_complete_coordinate_keeps_midpoint_residual(0,-100,F(1))
    elif component=="jet":
        with pytest.raises(AssertionError,match="complete jet residual"):
            test_shape_dual_complete_jet_keeps_midpoint_residual(0,F(2)**60)
    else:
        with pytest.raises(AssertionError,match="complete height residual"):
            test_shape_dual_complete_z_keeps_height_and_jet_residuals()


def test_shape_pair_internal_premature_center_rounding_mutation_has_teeth(monkeypatch):
    import inspect
    source=inspect.getsource(shape.interlocking_pair_generic)
    needle="_shape_value(c[2]) + _shape_value(lz)"
    assert needle in source
    scope=dict(vars(shape))
    replacement="_shape_value(_shape_coordinate(_shape_value(c[2]) + _shape_value(lz)))"
    exec(source.replace(needle,replacement),scope)
    monkeypatch.setattr(shape,"interlocking_pair_generic",scope["interlocking_pair_generic"])
    with pytest.raises(AssertionError,match="complete pair translation residual"):
        test_shape_generic_pair_translation_stays_exact_until_final_vertices()


def test_shape_phase_internal_early_seed_scaling_mutation_has_teeth(monkeypatch):
    def prematurely_scaled_sample(base_angle,phase,sin_fn):
        return shape._shape_value(sin_fn(base_angle+phase))
    monkeypatch.setattr(shape,"_shape_sin",prematurely_scaled_sample)
    with pytest.raises(pytest.fail.Exception,match="representable complete phase jet rejected"):
        test_shape_phase_jet_is_scaled_before_final_range_check(F(2)**-1074,F(2)**400)
