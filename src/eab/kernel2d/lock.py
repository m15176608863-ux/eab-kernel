"""Exact local certificates for translation against specified fixed neighbors.

The four states describe arbitrarily small strict separation, not finite rigid
motion and not load capacity. In particular, a contact seam may lie in int(E)
without lying in the strict overlap set O. A nonzero nonpenetrating direction
is only a local translation witness; this API does not certify a finite exit.
All certificates use rational data, including a radius strictly below every
nonincident convex-cell edge. Gates: tests/test_tia2d_lock.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from .global_entrance import (
    GlobalEntrance2, _angular_compare, _cell_state, _cross, _edges, _on, _ring,
    _sub,
)


@dataclass(frozen=True)
class LocalCell2:
    """A closed product cell containing zero and its exact tangent halfplanes.

For each active edge (a,b), the tangent inequality is cross(b-a,d)>=0;
strict inequalities characterize directions entering that open product cell.
The cell index identifies the pair in the Cartesian product of ear pieces.
"""
    neighbor_index: int
    cell_index: int
    piece_a: int
    piece_b: int
    vertices: tuple[tuple[F, F], ...]
    active_edges: tuple[tuple[tuple[F, F], tuple[F, F]], ...]


@dataclass(frozen=True)
class RadiusBound2:
    """Exact squared distance from zero to a nonincident closed cell edge."""
    neighbor_index: int
    cell_index: int
    edge_index: int
    start: tuple[F, F]
    end: tuple[F, F]
    squared_distance: F


@dataclass(frozen=True)
class ContactSource2:
    """Unfiltered zero-window association in the normalized input rings."""
    neighbor_index: int
    label: tuple[str, int, int]
    point: tuple[F, F]


@dataclass(frozen=True)
class LockArc2:
    """A ray or open CCW arc; rational representatives have L1 norm one.

RAY has start=end=sample. OPEN_ARC excludes both endpoints, which have their
own RAY records. State is PENETRATING, CONTACT or SEPARATING. Blockers identify
open product cells, and hence the exact pieces and active feature edges in
local_cells. Scaling any representative to an Euclidean unit vector is not
needed: S1 here denotes the set of oriented rays.
"""
    kind: str
    start: tuple[F, F]
    end: tuple[F, F]
    sample: tuple[F, F]
    state: str
    blockers: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class LockCertificate:
    """Translation result with exact witnesses, never an assembly lock claim.

OVERLAP rejects signing: status/refinement are None, call_status is OK and
mathematical_status is OVERLAP. Invalid numerical or polygon input instead
has call_status INVALID_INPUT and no mathematical conclusion. The supplied
neighbor set is explicit; no omitted body is assumed absent or fixed.
"""
    status: str | None
    refinement: str | None = None
    reason: str | None = None
    local_cells: tuple[LocalCell2, ...] = ()
    arcs: tuple[LockArc2, ...] = ()
    radius: F | None = None
    separation_ray: tuple[F, F] | None = None
    seam_ray: tuple[F, F] | None = None
    call_status: str = "OK"
    mathematical_status: str | None = None
    display_status: str = "EXACT"
    radius_bounds: tuple[RadiusBound2, ...] = ()
    pair_states: tuple[int, ...] = ()
    contact_sources: tuple[ContactSource2, ...] = ()


def _input_ring(poly):
    values = tuple(tuple(p) for p in poly)
    if any(len(p) != 2 for p in values):
        raise ValueError("expected two coordinates per point")
    if any(isinstance(v, bool) or not isinstance(v, (int, float, F))
           for p in values for v in p):
        raise ValueError("coordinates must be finite real numbers or rationals")
    return _ring(values)


def _neighbor_rings(neighbors):
    values = tuple(neighbors)
    if not values:
        return ()
    first = tuple(values[0])
    if len(first) == 2 and all(isinstance(v, (int, float, F)) for v in first):
        return (_input_ring((first, *values[1:])),)
    return tuple(_input_ring(p) for p in values)


def _unit_l1(direction):
    size = abs(direction[0]) + abs(direction[1])
    return direction[0] / size, direction[1] / size


def _distance_squared(a, b):
    e = _sub(b, a)
    size = e[0] * e[0] + e[1] * e[1]
    along = -(a[0] * e[0] + a[1] * e[1]) / size
    along = min(F(1), max(F(0), along))
    p = a[0] + along * e[0], a[1] + along * e[1]
    return p[0] * p[0] + p[1] * p[1]


def _local_data(pairs):
    cells, bounds = [], []
    zero = (F(0), F(0))
    for neighbor_index, pair in enumerate(pairs):
        for cell_index, cell in enumerate(pair.cells):
            edges = tuple(_edges(cell))
            if _cell_state(cell, zero) == 0:
                active = tuple((a, b) for a, b in edges if _on(zero, a, b))
                cells.append(LocalCell2(neighbor_index, cell_index,
                                       cell_index // len(pair.parts_b),
                                       cell_index % len(pair.parts_b), cell, active))
            for edge_index, (a, b) in enumerate(edges):
                if not _on(zero, a, b):
                    bounds.append(RadiusBound2(neighbor_index, cell_index, edge_index,
                                               a, b, _distance_squared(a, b)))
    return tuple(cells), tuple(bounds)


def _contact_sources(pairs, states):
    sources = []
    for neighbor_index, (pair, state) in enumerate(zip(pairs, states)):
        if state != 0:
            continue
        for i, a in enumerate(pair.A):
            for j, (b, c) in enumerate(_edges(pair.B)):
                if _on(a, b, c):
                    sources.append(ContactSource2(neighbor_index, ("VE", i, j), a))
        for j, b in enumerate(pair.B):
            for i, (a, c) in enumerate(_edges(pair.A)):
                if _on(b, a, c):
                    sources.append(ContactSource2(neighbor_index, ("EV", i, j), b))
    return tuple(sources)


def _classify(cells, direction):
    contact = False
    blockers = []
    for cell in cells:
        signs = tuple(_cross(_sub(b, a), direction) for a, b in cell.active_edges)
        if all(value > 0 for value in signs):
            blockers.append((cell.neighbor_index, cell.cell_index))
        elif all(value >= 0 for value in signs):
            contact = True
    if blockers:
        return "PENETRATING", tuple(blockers)
    return ("CONTACT" if contact else "SEPARATING"), ()


def _angular_cover(cells):
    rays = {(F(1), F(0)), (F(0), F(1)), (F(-1), F(0)), (F(0), F(-1))}
    for cell in cells:
        for a, b in cell.active_edges:
            ray = _unit_l1(_sub(b, a))
            rays.update((ray, (-ray[0], -ray[1])))
    ordered = []
    for ray in sorted(rays):
        index = len(ordered)
        while index and _angular_compare(ordered[index - 1], ray) > 0:
            index -= 1
        ordered.insert(index, ray)
    ordered = tuple(ordered)
    arcs = []
    for start, end in _edges(ordered):
        state, blockers = _classify(cells, start)
        arcs.append(LockArc2("RAY", start, start, start, state, blockers))
        middle = start[0] + end[0], start[1] + end[1]
        if middle == (0, 0):
            middle = -start[1], start[0]
        middle = _unit_l1(middle)
        state, blockers = _classify(cells, middle)
        arcs.append(LockArc2("OPEN_ARC", start, end, middle, state, blockers))
    return tuple(arcs)


def translation_lock_certificate(A, neighbors):
    """Certify local translation for one polygon and specified fixed neighbors.

neighbors accepts either one polygon or a sequence of polygons; an empty
sequence gives NOT_CONTACT. The pair and combined forms use exactly the same
path. All input coordinates are interpreted as exact rationals of the given
binary64/int/Fraction values. No tolerance, cover filter or body-overlap oracle
participates in the production classification.

For each product cell containing zero, only its active supporting edges can
change sign inside the certified ball. Every other edge has distance squared
q>0. Choosing r=q/(1+q) for the least q gives r*r<q, without an irrational or
rounded square root. OUTSIDE neighbors are included in these exclusion bounds.
The local open-cell union is O, the closed-cell union is E; all angular strata
are tested, including the boundary rays. NOT_SEPARABLE_TRANSLATION is refined
only into TRANSLATION_IMMOBILE or SEAM_SLIDING; neither is a finite-motion test.

Gates: test_lock_all_states_and_refinements, test_lock_independent_sector_oracle,
test_lock_radius_is_strict_and_excludes_outside_neighbors, and the internal
strict-to-closed mutation gate in tests/test_tia2d_lock.py.
"""
    try:
        moving = _input_ring(A)
        fixed = _neighbor_rings(neighbors)
        pairs = tuple(GlobalEntrance2(moving, p) for p in fixed)
    except (TypeError, ValueError, OverflowError, ZeroDivisionError) as error:
        return LockCertificate(None, reason=str(error), call_status="INVALID_INPUT", display_status="NOT_APPLICABLE")
    states = tuple(pair.membership((0, 0)) for pair in pairs)
    if 1 in states:
        return LockCertificate(None, reason="overlap_initial_state", pair_states=states,
                               mathematical_status="OVERLAP", display_status="NOT_APPLICABLE")
    cells, bounds = _local_data(pairs)
    least = min((bound.squared_distance for bound in bounds), default=None)
    radius = F(1) if least is None else least / (1 + least)
    arcs = _angular_cover(cells)
    separated = next((arc.sample for arc in arcs if arc.state == "SEPARATING"), None)
    touching = next((arc.sample for arc in arcs if arc.state == "CONTACT"), None)
    refinement = None
    separation_ray = seam_ray = None
    if 0 not in states:
        status = "NOT_CONTACT"
    elif separated is not None:
        status = "REMOVABLE_TRANSLATION"
        separation_ray = separated
    else:
        status = "NOT_SEPARABLE_TRANSLATION"
        refinement = "TRANSLATION_IMMOBILE" if touching is None else "SEAM_SLIDING"
        seam_ray = touching
    return LockCertificate(status, refinement=refinement, local_cells=cells, arcs=arcs,
                           radius=radius, separation_ray=separation_ray, seam_ray=seam_ray,
                           mathematical_status=status, radius_bounds=bounds,
                           pair_states=states, contact_sources=_contact_sources(pairs, states))
