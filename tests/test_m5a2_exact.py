"""M5a2 exact-boundary regressions with independent numerical expectations.

Oracle imports: fractions.Fraction and m5a_independent_oracle (whose explicit
inventory is fractions, functools and independent g0_oracle.overlap). Expected
rational roots are direct integer factorizations; the lever uses y=2*L*s /
(1+s*s), not production rotation/polynomial helpers. Mutation instrumentation
(inspect, textwrap, unittest.mock) is not a numerical oracle. No hash or frozen
code manifest participates in these assertions.
"""
from fractions import Fraction as F
from pathlib import Path
from random import Random
import sys
from unittest.mock import patch

import pytest
from mutation_support import mutated_function

from eab.kernel2d import algebraic as alg
from eab.kernel2d import se2
from eab.kernel2d.algebraic import RealAlgebraic
from eab.kernel2d.motion import QuadraticTime
from eab.kernel2d.se2 import SE2Motion, se2_first_entrance
import m5a_independent_oracle as oracle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m5a_se2_replay as replay


@pytest.mark.parametrize("delta", (F(1, 2**1074), F(1, 10**100), F(1, 2**52)))
def test_every_exact_positive_residual_stays_uncertified(delta):
    start = ((0, 0), (1, 0), (1, 1), (0, 1))
    end = tuple(((1+2*delta)*x, F(y)) for x, y in start)
    fit = replay.fit_rigid(start, end)
    assert fit.delta == delta, "exact tiny endpoint residual is not rounded to zero"
    assert fit.certificate == "UNCERTIFIED_NONRIGID_ENDPOINTS", \
        "strictly positive exact residual must remain UNCERTIFIED"
    assert replay.RigidFit(SE2Motion(), delta).certificate == "UNCERTIFIED_NONRIGID_ENDPOINTS", \
        "strictly positive exact residual must remain UNCERTIFIED"


def _lever(scale=F(1), shift=0):
    def point(x, y):
        return shift+scale*x, -3*shift+scale*y
    a = tuple(point(x, y) for x, y in ((0, 0), (5, 0), (0, F(1, 4))))
    b = tuple(point(x, y) for x, y in ((-1, 3), (6, 3), (6, 4), (-1, 4)))
    return a, b, SE2Motion(1, center=point(0, 0))


def test_rational_lever_time_has_one_container_mixed_equality_hash_and_sorting():
    a, b, motion = _lever()
    result = se2.se2_first_entrance(a, b, motion)
    t = result.exact_time
    expected = QuadraticTime(F(1, 3))
    # 2*5*s/(1+s*s)=3 gives (3*s-1)*(s-3)=0. The second
    # root is outside [0,1], and all other vertices stay strictly below y=3.
    assert result.status == "contact" and result.features == (("VE", 1, 0),)
    assert t == expected and expected == t, "rational SE2 time equals the rational QuadraticTime protocol"
    assert isinstance(t, QuadraticTime) and t.rational == F(1, 3)
    assert hash(t) == hash(expected) == hash(F(1, 3)), "rational SE2 time has the numeric hash"
    assert len({t, expected, F(1, 3)}) == 1
    items = [QuadraticTime(F(2, 3)), t, F(1, 4), expected, 1]
    assert sorted(items) == [F(1, 4), F(1, 3), F(1, 3), F(2, 3), 1], \
        "rational SE2 times sort with legacy rational times and Fractions"
    assert 0 < t < QuadraticTime(F(2, 3)) and expected <= t <= expected


@pytest.mark.parametrize("scale,shift", ((F(1, 10**9), 10**6), (F(1), 10**3), (F(10**8), 0)))
def test_rational_time_container_is_scale_and_translation_invariant(scale, shift):
    a, b, motion = _lever(scale, shift)
    frame = F(Random(20261015).randrange(1, 19), 23)
    c, s = (1-frame*frame)/(1+frame*frame), 2*frame/(1+frame*frame)
    def point(p):
        return c*p[0]-s*p[1], s*p[0]+c*p[1]
    t = se2_first_entrance(tuple(map(point, a)), tuple(map(point, b)),
                          SE2Motion(1, center=point(motion.center))).exact_time
    assert isinstance(t, QuadraticTime) and t == QuadraticTime(F(1, 3)), \
        "rational time container does not depend on unit or global origin"


@pytest.mark.parametrize("root", (F(1, 3), F(1, 100000000000000000039)))
def test_rational_reconstruction_recognizes_nondyadic_roots(root):
    # (x-root)*(x*x+1)*(x*x+2): the only real root is root.
    p = (-2*root, F(2), -3*root, F(3), -root, F(1))
    value = RealAlgebraic(p, 0, 1)
    assert value.rational is None, "fixture must require rational reconstruction"
    assert value.as_rational() == root, "exact rational reconstruction returns the factored root"
    assert value == root


@pytest.mark.parametrize("p", ((-1, 0, 2), (-2, 0, 0, 3), (1, -5, 0, 0, 0, 1)))
def test_rational_reconstruction_does_not_rationalize_irrational_roots(p):
    # Quadratic nonsquare; 3*x^3-2 rational-root theorem; x^5-5*x+1
    # rational candidates +/-1 are not roots. These are independent proofs.
    root = RealAlgebraic(p, 0, 1)
    assert root.as_rational() is None, "irrational root is not assigned a rational container"



def test_rational_reconstruction_selects_only_the_root_in_the_closed_interval():
    # (x-1)*(x*x-2); leading integer coefficient B=1. Nearest rational
    # reconstruction may find the other rational root 1, outside this bracket.
    value = RealAlgebraic((2, -2, -1, 1), F(11, 10), F(3, 2))
    assert value.as_rational() is None, "rational reconstruction must stay inside the selected root interval"


def test_public_algebraic_constructor_retains_closed_lower_endpoint_root():
    # (3*x-1)*(x-2), closed isolation [1/3,1] includes only x=1/3.
    root = RealAlgebraic((2, -7, 3), F(1, 3), 1)
    assert root == F(1, 3), "closed lower endpoint root denotes that exact endpoint"
    assert root.rational == root.lower == root.upper == F(1, 3), \
        "closed lower endpoint root has a degenerate rational certificate"
    assert root.refine() == root and root.sign_polynomial(-1, 3) == 0
    with pytest.raises(ValueError, match="exactly one real root"):
        RealAlgebraic((2, -7, 3), F(1, 3), 2)


@pytest.mark.parametrize("where", ("vertex", "parameter", "translation", "center"))
def test_independent_oracle_rejects_nonexact_inputs_at_first_contact(where):
    a = ((0, 0), (1, 0), (0, 1))
    b = ((3, 0), (4, 0), (3, 1))
    ma = (0, (0, 0), (0, 0))
    mb = ma
    if where == "vertex":
        a = ((0.0, 0), *a[1:])
    elif where == "parameter":
        ma = (False, ma[1], ma[2])
    elif where == "translation":
        ma = (0, (0.0, 0), ma[2])
    else:
        ma = (0, ma[1], (0, "0"))
    with pytest.raises(AssertionError, match="oracle inputs must be exact int/Fraction values"):
        oracle.first_contact(a, b, ma, mb)
    assert oracle.first_contact(((0, 0), (1, 0), (0, 1)), b, mb, mb)["status"] == "no_contact"


EXACT_MUTATIONS = (
    ("tiny_residual_zero", "strictly positive exact residual must remain UNCERTIFIED"),
    ("rational_container_bypass", "rational SE2 time equals the rational QuadraticTime protocol"),
    ("rational_reconstruction_bypass", "exact rational reconstruction returns the factored root"),
    ("rational_reconstruction_outside_interval", "rational reconstruction must stay inside the selected root interval"),
    ("closed_lower_endpoint_lost", "closed lower endpoint root denotes that exact endpoint"),
    ("oracle_input_guard_removed", "DID NOT RAISE"),
)


def exact_mutation_guard(kind):
    if kind == "tiny_residual_zero":
        test_every_exact_positive_residual_stays_uncertified(F(1, 2**1074))
    elif kind == "rational_container_bypass":
        test_rational_lever_time_has_one_container_mixed_equality_hash_and_sorting()
    elif kind == "rational_reconstruction_bypass":
        test_rational_reconstruction_recognizes_nondyadic_roots(F(1, 3))
    elif kind == "rational_reconstruction_outside_interval":
        test_rational_reconstruction_selects_only_the_root_in_the_closed_interval()
    elif kind == "closed_lower_endpoint_lost":
        test_public_algebraic_constructor_retains_closed_lower_endpoint_root()
    elif kind == "oracle_input_guard_removed":
        test_independent_oracle_rejects_nonexact_inputs_at_first_contact("parameter")
    else:
        raise AssertionError("unknown exact-boundary mutation")


def exact_mutation(kind):
    """Compile a real function-body defect; never append fake output data."""
    if kind == "tiny_residual_zero":
        original, owner, name = replay.RigidFit.certificate.fget, replay.RigidFit, "certificate"
        before, after = "self.delta == 0", "self.delta <= F(1, 2**52)"
        module = replay
    elif kind == "rational_container_bypass":
        original, owner, name = se2.se2_first_entrance, se2, "se2_first_entrance"
        before, after = "rational = time.as_rational()", "rational = time.rational"
        module = se2
    elif kind == "rational_reconstruction_bypass":
        original, owner, name = RealAlgebraic.as_rational, RealAlgebraic, "as_rational"
        before, after = "if self.rational is not None:", "if True:"
        module = alg
    elif kind == "rational_reconstruction_outside_interval":
        original, owner, name = RealAlgebraic.as_rational, RealAlgebraic, "as_rational"
        before, after = "lower <= candidate <= upper and ", ""
        module = alg
    elif kind == "closed_lower_endpoint_lost":
        original, owner, name = RealAlgebraic.__post_init__, RealAlgebraic, "__post_init__"
        before, after = "upper = lower", "lower = upper"
        module = alg
    else:
        original, owner, name = oracle.first_contact, oracle, "first_contact"
        before = "assert all(isinstance(x, (int, F)) and not isinstance(x, bool) for x in inputs)"
        after = "assert True"
        module = oracle
    changed = mutated_function(original, module, [(before, after)])
    return patch.object(owner, name, property(changed) if kind == "tiny_residual_zero" else changed)


@pytest.mark.parametrize("kind,message", EXACT_MUTATIONS)
def test_internal_exact_mutations_hit_the_named_semantic_guard(kind, message):
    exact_mutation_guard(kind)
    # Hash checks are explicitly unavailable while the altered production
    # path is exercised: even an accidental invocation cannot kill a mutant.
    with patch.object(replay, "code_hashes", return_value={}), patch.object(replay, "file_hash", return_value="disabled"):
        with exact_mutation(kind):
            with pytest.raises((AssertionError, pytest.fail.Exception), match=message):
                exact_mutation_guard(kind)
