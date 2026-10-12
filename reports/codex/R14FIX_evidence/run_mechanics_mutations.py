"""Re-run in-memory mutations inside production functions; no files changed."""
import inspect
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tests")]
import pytest
from eab import limit as L
from fractions import Fraction
mode=sys.argv[1]
if mode=="mu_guard":
    L.check_mu=lambda value,quantity: Fraction(value)
    test="tests/test_r14_cone.py::test_mu_support_bound_is_checked_at_every_public_entry[contact-1e+16]"
elif mode=="cone_guard":
    source=inspect.getsource(L._certified_friction_direction)
    needle="if _inside_friction_cone(n,g,mu):"
    assert source.count(needle)==1
    scope=dict(vars(L));exec(source.replace(needle,"if True:"),scope)
    L._certified_friction_direction=scope["_certified_friction_direction"]
    test="tests/test_r14_cone.py::test_final_generators_are_exactly_unilateral_and_inside_the_circular_cone[4-0.5-normal0-tangent0]"
elif mode=="selfcheck_guard":
    source=inspect.getsource(L._check_columns)
    needle="if normal_force <= 0 or sum(v*v for v in cross) > Fraction(ct.mu)**2*normal_force**2:"
    assert source.count(needle)==1
    scope=dict(vars(L));exec(source.replace(needle,"if False:"),scope)
    L._check_columns=scope["_check_columns"]
    test="tests/test_r14_cone.py::test_selfcheck_rejects_uncertified_generator_even_when_generator_certificate_lies"
elif mode=="cohesion_projection":
    source=inspect.getsource(L._cohesion_directions)
    needle="projected = tuple(b-normal_part*a for a,b in zip(n,v))"
    assert source.count(needle)==1
    scope=dict(vars(L));exec(source.replace(needle,"projected = tuple(v)"),scope)
    L._cohesion_directions=scope["_cohesion_directions"]
    test="tests/test_r14_cone.py::test_cohesive_columns_are_exactly_tangential_and_in_the_unit_disk[4-3-normal1-tangent1]"
elif mode=="cohesion_selfcheck":
    source=inspect.getsource(L._check_columns)
    needle="if sum(Fraction(n)*v for n,v in zip(ct.normal,unit_force)) != 0 or sum(v*v for v in unit_force) > 1:"
    assert source.count(needle)==1
    scope=dict(vars(L));exec(source.replace(needle,"if False:"),scope)
    L._check_columns=scope["_check_columns"]
    test="tests/test_r14_cone.py::test_cohesion_projection_is_independently_checked_even_if_constructor_lies"
elif mode=="material_recheck":
    L._check_material=lambda *args: None
    test="tests/test_r14_cone.py::test_mutated_material_is_rechecked_before_building_any_lp_columns[-1.0-cohesion]"
elif mode=="noise_constant":
    import textwrap
    from eab.kernel3d import geom3 as G
    source=textwrap.dedent(inspect.getsource(G.Polyhedron.face_noise))
    needle="v = _eg.sqrt_rational(numerator*numerator/_eg.dot(n,n))"
    assert source.count(needle)==1
    replacement="v = scalar_rational(Fraction(_eg.sqrt_rational(numerator*numerator/_eg.dot(n,n)))*(1+Fraction(8,2**53)))"
    scope=dict(vars(G));exec(source.replace(needle,replacement),scope)
    G.Polyhedron.face_noise=scope["face_noise"]
    test="tests/test_r14_claims.py::test_face_noise_obeys_the_documented_two_rounding_relative_bound[0]"
elif mode=="neighbor_2d":
    source=inspect.getsource(L._certified_friction_direction)
    needle="if len(n) == 2:"
    assert source.count(needle)==1
    scope=dict(vars(L));exec(source.replace(needle,"if False:"),scope)
    L._certified_friction_direction=scope["_certified_friction_direction"]
    test="tests/test_lp_certificates.py::test_near_self_locking_is_certified_within_its_reported_uncertainty_or_loud[1e-09-frame1]"
else: raise ValueError(mode)
result=pytest.main(["-q","-p","no:cacheprovider",test,"--basetemp=reports/codex/R14FIX_evidence/tmp/mech_mut_"+mode])
print("MUTATION",mode,"PYTEST_EXIT",result)
assert result==1,"mutation must fail target assertion, not collection/environment"
