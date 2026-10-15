"""M3c public-output call-order gate; exact field equality, not a hash oracle.

Imports: fractions, inspect, textwrap, pytest, and the SUT module/class.
This is a deterministic API contract, not a geometric truth oracle: two fresh
objects receive the same exact input and different public operation orders.
Every dataclass field is compared; no SUT geometry primitive is reused to
manufacture an expected geometric answer.
"""
from fractions import Fraction as F
import inspect
import textwrap

import pytest

from eab.kernel2d import global_entrance as module
from eab.kernel2d.global_entrance import GlobalEntrance2


PLUG = ((1, 1), (5, 1), (5, 5), (1, 5))
POCKET = ((0, 0), (6, 0), (6, 2), (5, 2), (5, 1), (1, 1),
          (1, 5), (5, 5), (5, 4), (6, 4), (6, 6), (F(10, 3), 6), (0, 6))


def _model(exponent):
    scale = F(2)**exponent
    # General rational rotation and different large translations; the
    # tight-fit pocket remains exact at all three geometric scales.
    A = tuple((scale*(3*x-4*y)/5+1000, scale*(4*x+3*y)/5-3000) for x, y in PLUG)
    B = tuple((scale*(3*x-4*y)/5-2000, scale*(4*x+3*y)/5+4000) for x, y in POCKET)
    return GlobalEntrance2(A, B, merge_convex=True, compact_subdivision=True)


def _assert_call_order_fields(exponent, output):
    cold, warm = _model(exponent), _model(exponent)
    subdivision = warm.subdivision
    if output == "side_probes":
        expected = tuple(warm.side_probes(*edge.vertices) for edge in subdivision.edges)
        actual = tuple(cold.side_probes(*edge.vertices) for edge in subdivision.edges)
        assert actual == expected, "compact side_probes fields depend on public call order"
        assert tuple(cold.side_probes(*edge.vertices) for edge in cold.subdivision.edges) == expected
    else:
        actual = cold.clipped_covers
        expected = warm.clipped_covers
        # Frozen CoverPiece2 equality covers label/start/end/exposed/body_state/
        # side_points/side_states, not only labels or exposed flags.
        assert actual == expected, "compact clipped_covers fields depend on public call order"
        assert cold.subdivision == subdivision
        assert cold.clipped_covers == expected
    assert cold.subdivision == subdivision


@pytest.mark.parametrize("exponent", [-4, 0, 4])
@pytest.mark.parametrize("output", ["side_probes", "clipped_covers"])
def test_compact_public_output_fields_are_independent_of_call_order(exponent, output):
    _assert_call_order_fields(exponent, output)


def test_determinism_scale_parameters_have_distinct_public_probe_products():
    products = []
    for exponent in (-4, 0, 4):
        model = _model(exponent)
        products.append(tuple(piece.side_points for piece in model.clipped_covers))
    assert len(set(products)) == 3, "scale parameters must produce distinct public side-point fields"


@pytest.mark.parametrize("output", ["side_probes", "clipped_covers"])
def test_old_lazy_order_internal_mutant_fails_semantic_fields_without_hash_gate(monkeypatch, output):
    """Restore the real old SUT branch before outputs; never append fake data."""
    source = textwrap.dedent(inspect.getsource(GlobalEntrance2.side_probes))
    old = "    if self._compact_subdivision and self._subdivision_cache is None:\n        self.subdivision\n"
    assert old in source, "real lazy-construction mutation site must exist"
    namespace = dict(module.__dict__)
    exec(compile(source.replace(old, "", 1), "<M3c old lazy order>", "exec"), namespace)
    with monkeypatch.context() as patch:
        patch.setattr(GlobalEntrance2, "side_probes", namespace["side_probes"])
        with pytest.raises(AssertionError, match=f"compact {output} fields depend on public call order"):
            _assert_call_order_fields(0, output)
    _assert_call_order_fields(0, output)
