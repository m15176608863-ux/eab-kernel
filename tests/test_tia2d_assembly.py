"""Exact record/frame checks independent of geometry or mechanical solving."""
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as Q
import struct

import pytest

from eab.kernel2d.assembly import Assembly2, Body2, free_dofs, wrench_at_anchor
from h1_kernel_purity import DOMAIN_WORDS, ORDINARY_COMPONENTS, words


def test_body_factory_preserves_bits_ids_and_normalizes_clockwise():
    raw = ((-0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0))
    body = Body2.from_vertices("moving", raw)
    assert body.vertex_ids == (3, 2, 1, 0)
    assert struct.pack(">d", body.original_vertices[0][0]).hex() == "8000000000000000"
    assert all(isinstance(x, Q) for p in body.vertices for x in p)
    with pytest.raises(FrozenInstanceError):
        body.live = (0, 0, 1)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_input_is_rejected(bad):
    with pytest.raises((ValueError, OverflowError)):
        Body2.from_vertices("bad", ((0, 0), (bad, 0), (0, 1)))


def test_boundary_anchor_does_not_follow_algebraic_reference():
    plate = Body2.from_vertices("plate", ((3, 0), (4, 0), (4, 1), (3, 1)),
        reference_point=(Q(5, 8), Q(-3, 8)), boundary_type="FORCE_CONTROLLED_PLATE",
        dof_mask=(1, 0, 1), dof_anchor=(3, Q(1, 2)))
    assert wrench_at_anchor(plate, (-1, 0, Q(7, 8))) == (-1, 0)
    assert free_dofs(Assembly2((plate,))) == ((0, 0), (0, 2))
    with pytest.raises(ValueError):
        Body2.from_vertices("plate", plate.vertices, boundary_type="FORCE_CONTROLLED_PLATE")


@pytest.mark.parametrize("mask", [(1, 0, 1), (1, 1, 0), (0, 1, 0), (0, 0, 1), (0, 0, 0)])
def test_partly_constrained_free_body_requires_explicit_dof_anchor(mask):
    """Changing the algebraic origin must not silently change a boundary."""
    vertices = ((0, 0), (1, 0), (1, 1), (0, 1))
    with pytest.raises(ValueError, match="explicit dof_anchor"):
        Body2.from_vertices("free", vertices, dof_mask=mask)
    body = Body2.from_vertices("free", vertices, dof_mask=mask, dof_anchor=(7, 11))
    assert body.boundary_type is None and body.dof_anchor == (7, 11)


def test_free_body_anchor_stays_fixed_when_reference_and_wrench_change_together():
    """Independent moment shift checks actual normal and equilibrium matrices."""
    from eab.kernel2d.contacts import assemble_contact_set2, constraint_matrix
    from eab.kernel2d.statics import limit_load_ideal_exact_2d

    moving = Body2.from_vertices("free", ((1, 0), (2, 0), (2, 1), (1, 1)),
        dof_mask=(1, 0, 1), dof_anchor=(7, 11), dead=(-1, 0, Q(1, 2)),
        live=(0, -1, -Q(3, 2)))
    wall = Body2.from_vertices("wall", ((0, 0), (1, 0), (1, 1), (0, 1)),
        boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    old = Assembly2((moving, wall), ((0, 1),), "complete", mu=Q(2))
    # M_new = M_old - dx * Fy + dy * Fx, for delta o = (13,-5).
    changed = replace(moving, reference_point=(Q(13), Q(-5)),
                      dead=(-Q(1), Q(0), Q(11, 2)), live=(Q(0), -Q(1), Q(23, 2)))
    new = replace(old, bodies=(changed, wall))
    before, after = (assemble_contact_set2(model) for model in (old, new))
    assert constraint_matrix(old, before.constraints) == constraint_matrix(new, after.constraints)
    assert set(constraint_matrix(old, before.constraints)[0]) == {(1, 11), (1, 10)}
    a, b = (limit_load_ideal_exact_2d(model, cs).problem for model, cs in ((old, before), (new, after)))
    assert (a.A, a.b, a.c) == (b.A, b.b, b.c)


def test_omitted_neighbors_and_boundaries_are_not_fixed_or_complete():
    body = Body2.from_vertices("moving", ((0, 0), (1, 0), (0, 1)))
    assembly = Assembly2((body,))
    assert assembly.completeness == "completeness_unknown"
    assert body.boundary_type is None and body.dof_mask == (1, 1, 1)
    with pytest.raises(ValueError):
        Assembly2((body,), completeness="complete")


def test_only_approved_ordinary_component_is_added_domain_words_still_rejected():
    previous = set("initial partial potential spatial tangential exponential differential".split())
    assert ORDINARY_COMPONENTS == previous | {"differentiability"}
    assert not DOMAIN_WORDS & words("differentiability")
    for spelling in ("tia_block", "tiaprism", "TiaAssembly", "differentiability_tia"):
        assert "tia" in DOMAIN_WORDS & words(spelling)


def test_original_sources_are_immutable_and_ids_match_actual_geometry():
    body = Body2.from_vertices("body", ((0, 0), (1, 0), (1, 1), (0, 1)))
    with pytest.raises(ValueError, match="immutable"):
        replace(body, original_vertices=list(body.original_vertices))
    with pytest.raises(ValueError, match="immutable"):
        replace(body, vertex_ids=list(body.vertex_ids))
    with pytest.raises(ValueError, match="identify"):
        replace(body, vertex_ids=tuple(reversed(body.vertex_ids)))
    with pytest.raises(ValueError, match="invalid"):
        replace(body, vertex_ids=(0, 0, 0, 0))
