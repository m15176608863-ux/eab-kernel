"""Immutable planar bodies and explicitly constrained assemblies.

No omitted boundary is a fixed body. Wrenches are about constant reference
points; masks constrain velocities at their independent constant anchors.
Tests: test_tia2d_assembly.py covers numeric input, ring IDs and anchor maps.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from .global_entrance import _ring


def point2(value):
    if len(value) != 2:
        raise ValueError("point must have two coordinates")
    return tuple(Q(v) for v in value)


def wrench3(value):
    if len(value) != 3:
        raise ValueError("wrench must have three coordinates")
    return tuple(Q(v) for v in value)


def cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def wrench_at_anchor(body, wrench):
    """Transform a wrench and then retain the explicitly free rows."""
    fx, fy, moment = wrench3(wrench)
    dx, dy = (body.dof_anchor[k] - body.reference_point[k] for k in (0, 1))
    full = (fx, fy, moment - dx * fy + dy * fx)
    return tuple(v for v, free in zip(full, body.dof_mask) if free)


@dataclass(frozen=True)
class Body2:
    body_id: str
    vertices: tuple
    reference_point: tuple = (Q(0), Q(0))
    boundary_type: str | None = None
    dof_mask: tuple = (1, 1, 1)
    dof_anchor: tuple | None = None
    dead: tuple = (Q(0), Q(0), Q(0))
    live: tuple = (Q(0), Q(0), Q(0))
    original_vertices: tuple = ()
    vertex_ids: tuple = ()
    _reference_input: tuple = ()
    _anchor_input: tuple = ()
    _dead_input: tuple = ()
    _live_input: tuple = ()

    def __post_init__(self):
        if not isinstance(self.body_id, str) or not self.body_id:
            raise ValueError("body_id must be a nonempty string")
        if not isinstance(self.vertices, tuple) or any(not isinstance(p, tuple) for p in self.vertices):
            raise ValueError("body record vertices must be immutable; use from_vertices")
        if any(not isinstance(v, (int, Q)) for p in self.vertices for v in p):
            raise ValueError("body record coordinates must be exact; use from_vertices")
        if _ring(self.vertices) != self.vertices:
            raise ValueError("body record must be CCW; use from_vertices")
        if self.boundary_type not in (None, "FIXED_BODY", "FORCE_CONTROLLED_PLATE"):
            raise ValueError("unknown boundary_type")
        mask = self.dof_mask
        if not isinstance(mask, tuple) or len(mask) != 3 or any(v not in (0, 1) for v in mask):
            raise ValueError("dof_mask must contain three binary integers")
        if self.boundary_type == "FIXED_BODY" and mask != (0, 0, 0):
            raise ValueError("fixed body needs an explicit zero mask")
        if self.boundary_type == "FORCE_CONTROLLED_PLATE" and self.dof_anchor is None:
            raise ValueError("controlled boundary needs an explicit dof_anchor")
        if self.dof_anchor is None:
            raise ValueError("body record requires a fixed dof_anchor; use from_vertices")
        for point in (self.reference_point, self.dof_anchor):
            if not isinstance(point, tuple) or len(point) != 2 or any(not isinstance(v, (int, Q)) for v in point):
                raise ValueError("reference points must be immutable exact pairs")
        for load in (self.dead, self.live):
            if not isinstance(load, tuple) or len(load) != 3 or any(not isinstance(v, (int, Q)) for v in load):
                raise ValueError("loads must be immutable exact triples")
        if (not isinstance(self.original_vertices, tuple)
                or any(not isinstance(p, tuple) or len(p) != 2 for p in self.original_vertices)
                or not isinstance(self.vertex_ids, tuple)
                or any(not isinstance(i, int) or isinstance(i, bool) for i in self.vertex_ids)):
            raise ValueError("original geometry and IDs must be immutable")
        if self.original_vertices:
            if (len(self.vertex_ids) != len(self.vertices)
                    or len(set(self.vertex_ids)) != len(self.vertex_ids)
                    or any(not 0 <= i < len(self.original_vertices) for i in self.vertex_ids)):
                raise ValueError("original vertex ID map is invalid")
            raw = tuple(point2(p) for p in self.original_vertices)
            if tuple(raw[i] for i in self.vertex_ids) != self.vertices:
                raise ValueError("original vertex IDs do not identify current vertices")
        elif self.vertex_ids:
            raise ValueError("vertex IDs require original vertices")
        for raw, exact in ((self._reference_input, self.reference_point),
                           (self._anchor_input, self.dof_anchor),
                           (self._dead_input, self.dead), (self._live_input, self.live)):
            if not isinstance(raw, tuple):
                raise ValueError("input numbers must be immutable")
            if raw and len(raw) != len(exact):
                raise ValueError("input number shape mismatch")
            # These private input snapshots preserve signed zero. dataclass
            # replacement may change a wrench/frame; exporters must compare
            # the snapshot with the current exact value before reusing bits.
            tuple(Q(v) for v in raw)

    @staticmethod
    def from_vertices(body_id, vertices, *, reference_point=(0, 0), boundary_type=None,
                      dof_mask=(1, 1, 1), dof_anchor=None, dead=(0, 0, 0), live=(0, 0, 0)):
        raw = tuple(tuple(p) for p in vertices)
        exact = tuple(point2(p) for p in raw)
        ring = _ring(exact)
        ids = tuple(exact.index(p) for p in ring)
        raw_origin = tuple(reference_point)
        raw_dead, raw_live = tuple(dead), tuple(live)
        mask = tuple(dof_mask)
        origin = point2(raw_origin)
        if boundary_type == "FORCE_CONTROLLED_PLATE" and dof_anchor is None:
            raise ValueError("controlled boundary needs an explicit dof_anchor")
        if boundary_type != "FIXED_BODY" and mask != (1, 1, 1) and dof_anchor is None:
            raise ValueError("a partly constrained body needs an explicit dof_anchor")
        raw_anchor = raw_origin if dof_anchor is None else tuple(dof_anchor)
        anchor = point2(raw_anchor)
        return Body2(body_id, ring, origin, boundary_type, mask, anchor,
                     wrench3(raw_dead), wrench3(raw_live), raw, ids,
                     raw_origin, raw_anchor, raw_dead, raw_live)


@dataclass(frozen=True)
class Assembly2:
    bodies: tuple[Body2, ...]
    pairs: tuple | None = None
    completeness: str = "completeness_unknown"
    profile: str = "profile1"
    mu: Q = Q(0)

    def __post_init__(self):
        bodies = self.bodies
        if not isinstance(bodies, tuple):
            raise ValueError("assembly bodies must be immutable")
        if not bodies or any(not isinstance(body, Body2) for body in bodies):
            raise ValueError("assembly needs Body2 inputs")
        if len({body.body_id for body in bodies}) != len(bodies):
            raise ValueError("body IDs must be unique")
        if self.profile != "profile1":
            raise ValueError("unsupported profile")
        if self.completeness not in ("complete", "completeness_unknown"):
            raise ValueError("unknown completeness")
        pairs = self.pairs
        if pairs is None and self.completeness == "complete":
            raise ValueError("complete assembly requires explicit candidate pairs")
        if pairs is not None:
            if not isinstance(pairs, tuple) or any(not isinstance(pair, tuple) for pair in pairs):
                raise ValueError("candidate pairs must be immutable")
            for pair in pairs:
                if (len(pair) != 2 or any(not isinstance(i, int) or not 0 <= i < len(bodies) for i in pair)
                        or pair[0] == pair[1]):
                    raise ValueError("invalid candidate pair")
            if self.completeness == "complete":
                expected = {(i, j) for i in range(len(bodies)) for j in range(i + 1, len(bodies))}
                if {tuple(sorted(pair)) for pair in pairs} != expected:
                    raise ValueError("complete candidate list must include all pairs")
        mu = Q(self.mu)
        if mu < 0:
            raise ValueError("mu must be nonnegative")


def free_dofs(assembly):
    return tuple((i, k) for i, body in enumerate(assembly.bodies)
                 for k, free in enumerate(body.dof_mask) if free)
