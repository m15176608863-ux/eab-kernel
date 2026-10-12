"""R14 physical quantity domains; exact integers/Fractions are the oracle.

No geometry primitive defines expected range/losslessness. The extra angle
cases exercise real public entrances, before implicit mixed float arithmetic.
"""
from fractions import Fraction as F
import pytest
from eab.numeric_domain import ConstructionDomainError, check_mu, MAX_MU

@pytest.mark.parametrize("q", [0, F(1,2**1000), F(1,2), 1, 2**20])
def test_friction_domain_checks_exact_boundaries(q):
    assert check_mu(q, "test.mu") == F(q)
    assert MAX_MU == 2**20

@pytest.mark.parametrize("q", [-1, F(-1,2**2000), 2**20+F(1,2**2000), 1e16, float("inf")])
def test_friction_domain_rejects_before_rounded_bound_comparison(q):
    with pytest.raises(ConstructionDomainError, match="test.mu"):
        check_mu(q, "test.mu")

@pytest.mark.parametrize("tol", [F(1,2**1075), F(1,3)])
def test_angular_window_exact_input_is_checked_before_libm(tol):
    from eab.kernel2d.geom import reflex_vertices
    with pytest.raises(ConstructionDomainError, match="tol"):
        reflex_vertices([(0,0),(1,0),(1,1),(0,1)], tol=tol)

@pytest.mark.parametrize("generic", [False, True])
@pytest.mark.parametrize("phase", [2**54+1, F(1,2**1075)])
def test_shape_phase_is_checked_before_mixed_float_arithmetic(generic, phase):
    from tools.osteomorphic import osteomorphic_block, osteomorphic_block_generic
    function = osteomorphic_block_generic if generic else osteomorphic_block
    with pytest.raises(ConstructionDomainError, match="phase"):
        function(nx=2, ny=2, phase=phase)


def test_angular_window_guard_has_an_internal_mutation_tooth(monkeypatch):
    import inspect
    from eab.kernel2d import geom
    source = inspect.getsource(geom.reflex_vertices)
    needle = '    tol = binary64_argument(tol, "reflex_vertices.tol")\n'
    assert needle in source
    scope = dict(vars(geom))
    exec(source.replace(needle, ""), scope)
    monkeypatch.setattr(geom, "reflex_vertices", scope["reflex_vertices"])
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_angular_window_exact_input_is_checked_before_libm(F(1, 2**1075))


@pytest.mark.parametrize("generic", [False, True])
def test_shape_phase_guard_has_an_internal_mutation_tooth(monkeypatch, generic):
    import inspect
    from tools import osteomorphic as shape
    name = "osteomorphic_block_generic" if generic else "osteomorphic_block"
    source = inspect.getsource(getattr(shape, name))
    needle = '    binary64_argument(val(phase), "osteomorphic.phase")\n'
    assert needle in source
    scope = dict(vars(shape))
    exec(source.replace(needle, ""), scope)
    monkeypatch.setattr(shape, name, scope[name])
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_shape_phase_is_checked_before_mixed_float_arithmetic(generic, 2**54 + 1)


@pytest.mark.parametrize("generic", [False, True])
@pytest.mark.parametrize("parameter", ["lx", "ly", "lz", "amp", "center"])
def test_shape_physical_parameters_are_checked_before_early_arithmetic(generic, parameter):
    from tools.osteomorphic import osteomorphic_block, osteomorphic_block_generic
    function = osteomorphic_block_generic if generic else osteomorphic_block
    tiny = F(1, 2**2000)
    value = (tiny,0,0) if parameter == "center" else tiny
    with pytest.raises(ConstructionDomainError, match="osteomorphic"):
        function(nx=1, ny=1, **{parameter:value})

@pytest.mark.parametrize("generic", [False, True])
def test_shape_raw_exact_coordinate_cancellation_cannot_be_silently_zero(generic):
    from tools.osteomorphic import osteomorphic_block, osteomorphic_block_generic
    function = osteomorphic_block_generic if generic else osteomorphic_block
    # Both supplied parameters are ordinary D400 values. A final nonzero
    # coordinate lies below the RN-zero boundary and must be rejected.
    with pytest.raises(ConstructionDomainError):
        function(nx=1, ny=1, lx=F(2)+F(1,2**2000), center=(1,0,0))



def test_shape_complete_coordinate_rounding_has_an_internal_mutation_tooth(monkeypatch):
    import inspect
    from tools import osteomorphic as shape
    source = inspect.getsource(shape._shape_value)
    needle = "else Fraction(value)"
    assert needle in source
    namespace = dict(vars(shape))
    exec(source.replace(needle,"else float(value)"),namespace)
    monkeypatch.setattr(shape,"_shape_value",namespace["_shape_value"])
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_shape_raw_exact_coordinate_cancellation_cannot_be_silently_zero(False)
