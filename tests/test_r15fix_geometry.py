"""R15 output certificates: independent rational interval/affine oracles.

Expected answers use only Fraction arithmetic on explicitly listed Cartesian
bounds (or a tilted top plane); no production geometric primitive is shared.
Mutation gates replace code inside the actual API, never its returned data.
"""
from fractions import Fraction as F
import inspect
import math
import sys

import pytest

from eab import margin as M
from eab.kernel3d import interlock as I
from eab.kernel3d.geom3 import Polyhedron
from eab.numeric_domain import ConstructionDomainError


FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
MAX = F(sys.float_info.max)


def _box(x0=-1, x1=1, y0=-1, y1=1, z0=-1, z1=1):
    return Polyhedron([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                       (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
                      list(FACES))


def _escape_boxes(root):
    # A's lowest z is zero and its xy projection lies strictly inside B.
    # Strict overlap ends exactly at h = B.zmax = root.
    return (_box(F(-1, 8), F(1, 8), F(-1, 8), F(1, 8), 0, root/2),
            _box(F(-1, 4), F(1, 4), F(-1, 4), F(1, 4), F(-1, 4), root))


def _assert_penetration_certificate(delta):
    contact, = M.margin_contacts(_box(), _box(), delta=delta)
    actual = (contact.margin_gap, contact._exact_closed, contact.exact_distance_squared)
    assert contact.exact_distance_squared == F(0) and contact._exact_closed is (delta >= 0), (
        'penetration output must carry exact distance/closed certificates', actual)
    assert contact.margin_gap == float(-delta), ('complete exact negative delta must be rounded once', actual)
    if delta:
        assert math.copysign(1.0, contact.margin_gap) == (-1 if delta > 0 else 1), (
            'underflow display must retain exact gap sign', actual)
    assert contact.label == (M.PENETRATING,) and contact.distance == 0 and contact.normal is None


@pytest.mark.parametrize('delta', [F(2)**-2000, F(2)**-1075, F(2)**-1074,
                                    F(1, 8), F(0), -F(2)**-2000])
def test_r15_o03_penetration_early_return_has_exact_display_certificate(delta):
    _assert_penetration_certificate(delta)


@pytest.mark.parametrize('delta', [math.inf, -math.inf, math.nan, F(2)**2000])
def test_r15_o03_penetration_early_return_rejects_nonfinite_or_overflow_gap(delta):
    with pytest.raises(ConstructionDomainError, match='margin_contacts'):
        M.margin_contacts(_box(), _box(), delta=delta)


def _assert_escape_display(root):
    result = I.escape_height_covers(*_escape_boxes(root), (0, 0, 0), tol=0)
    assert result.exact_height == root and result.nonpenetrating_state == 0, 'independent z-interval root'
    assert getattr(result, 'height_display_overflow', None) is (root > MAX), (
        'finite exact root needs explicit upward-display overflow marker', result.height, root - MAX)
    if root > MAX:
        assert result.height == math.inf, 'upward bound cannot be replaced by maxfloat'
    else:
        assert math.isfinite(result.height) and F(result.height) >= root
        assert F(math.nextafter(result.height, -math.inf)) < root
    return result


@pytest.mark.parametrize('root', [MAX-1, MAX, MAX+1, MAX+F(2)**969, MAX+F(2)**970-1])
def test_r15_o05_finite_escape_root_marks_upward_display_overflow(root):
    _assert_escape_display(root)


def test_r15_o05_rn_overflow_still_has_named_domain_failure():
    with pytest.raises(ConstructionDomainError):
        I.escape_height_covers(*_escape_boxes(MAX+F(2)**970), (0, 0, 0), tol=0)


def test_r15_scan_bare_escape_reference_cannot_drop_overflow_marker():
    root = MAX+1
    with pytest.raises(ConstructionDomainError, match='escape_height_brute.height'):
        I.escape_height_brute(*_escape_boxes(root), (0, 0, 0), hi=root)


def test_r15_scan_profile_keeps_exact_root_and_overflow_certificate():
    root = MAX+1
    profile = I.dilatancy_profile(*_escape_boxes(root), deltas=[F(-1, 16), F(0), F(1, 16)], tol=0)
    for row in profile:
        assert row.get('exact_height') == root and row.get('height_display_overflow') is True, (
            'profile must propagate exact root and overflow certificate', row)
    assert profile[1]['tan_psi'] == 0.0, 'equal exact roots have zero slope, not inf-minus-inf'


def _tilted_profile(deltas=None):
    root = F(2)**60
    a, b = _escape_boxes(root)
    # B's upper plane is z=root+x. A's rightmost x is offset+1/8;
    # hence its first nonpenetrating root is root+offset+1/8 exactly.
    b = Polyhedron([(x, y, z+x if i >= 4 else z) for i, (x, y, z) in enumerate(b.verts)], b.faces)
    return I.dilatancy_profile(a, b, deltas=([F(-1, 16), F(0), F(1, 16)] if deltas is None else deltas), tol=0)


def test_r15_scan_profile_differences_exact_roots_before_rounding():
    profile = _tilted_profile()
    assert profile[1]['tan_psi'] == 1.0, ('affine top-plane slope survives common-height cancellation', profile)


def test_r15_scan_profile_offset_retains_complete_exact_product():
    tiny = F(2)**-100
    profile = _tilted_profile([F(1, 16)-tiny, F(1, 16), F(1, 16)+tiny])
    assert profile[1]['tan_psi'] == 1.0, ('exact offset product must not collapse distinct sample points', profile)


def _mutate(monkeypatch, module, name, before, after):
    original = getattr(module, name)
    source = inspect.getsource(original)
    assert source.count(before) == 1, 'mutation must hit exactly one live internal construction'
    namespace = dict(original.__globals__)
    exec(compile(source.replace(before, after), original.__code__.co_filename, 'exec'), namespace)
    monkeypatch.setattr(module, name, namespace[name])


def test_r15_o03_reintroduced_float_early_return_is_killed(monkeypatch):
    _assert_penetration_certificate(F(2)**-2000)
    _mutate(monkeypatch, M, 'margin_contacts',
            'return [MarginContact((PENETRATING,), 0.0, gap, None, None, None,\n'
            '                              delta >= 0, Fraction(0))]',
            'return [MarginContact((PENETRATING,), 0.0, 0.0 - delta, None, None, None)]')
    with pytest.raises(AssertionError, match='penetration output must carry exact distance/closed certificates'):
        _assert_penetration_certificate(F(2)**-2000)


def test_r15_o05_removed_live_overflow_marker_is_killed(monkeypatch):
    _assert_escape_display(MAX+1)
    _mutate(monkeypatch, I, 'escape_height_covers',
            'height_display_overflow=math.isinf(display)', 'height_display_overflow=False')
    with pytest.raises(AssertionError, match='finite exact root needs explicit upward-display overflow marker'):
        _assert_escape_display(MAX+1)


def test_r15_scan_profile_rounded_root_difference_is_killed(monkeypatch):
    assert _tilted_profile()[1]['tan_psi'] == 1.0
    _mutate(monkeypatch, I, 'dilatancy_profile',
            "F(out[i + 1]['exact_height']) - F(out[i - 1]['exact_height'])",
            "F(out[i + 1]['h']) - F(out[i - 1]['h'])")
    with pytest.raises(AssertionError, match='affine top-plane slope survives common-height cancellation'):
        test_r15_scan_profile_differences_exact_roots_before_rounding()


def test_r15_scan_profile_early_offset_rounding_is_killed(monkeypatch):
    test_r15_scan_profile_offset_retains_complete_exact_product()
    _mutate(monkeypatch, I, 'dilatancy_profile',
            'off = tuple(F(d) * F(component) for component in direction)',
            'off = tuple(d * component for component in direction)')
    with pytest.raises(AssertionError, match='exact offset product must not collapse distinct sample points'):
        test_r15_scan_profile_offset_retains_complete_exact_product()


def test_r15_scan_bare_reference_removed_overflow_check_is_killed(monkeypatch):
    test_r15_scan_bare_escape_reference_cannot_drop_overflow_marker()
    _mutate(monkeypatch, I, 'escape_height_brute',
            'if result.height_display_overflow:', 'if False:')
    # Reuse the production-level contract gate: the mutation must escape its
    # named-error assertion, not fail on another root/label assertion.
    with pytest.raises(pytest.fail.Exception, match='DID NOT RAISE'):
        test_r15_scan_bare_escape_reference_cannot_drop_overflow_marker()


def test_r15_scan_profile_removed_certificate_is_killed(monkeypatch):
    test_r15_scan_profile_keeps_exact_root_and_overflow_certificate()
    _mutate(monkeypatch, I, 'dilatancy_profile',
            '"height_display_overflow": sol.height_display_overflow',
            '"height_display_overflow": False')
    with pytest.raises(AssertionError, match='profile must propagate exact root and overflow certificate'):
        test_r15_scan_profile_keeps_exact_root_and_overflow_certificate()
