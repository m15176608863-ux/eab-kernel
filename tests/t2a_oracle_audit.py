"""Independent finite-path audit, with geometry separated from JSON metadata.

All poses are constructed with the private M5a rational motion evaluator before
any report rows are accumulated. Each pair is then independently checked by the
contact-allowed interval oracle. No production motion or root solver is imported.
"""
from fractions import Fraction as F
from m5a_independent_oracle import ring_at
from t2a_independent_oracle import first_penetration, _exact_point, _exact_motion

def root_certificate(root):
    """JSON-compatible independent exact value; no floating display field."""
    if root is None:
        return None
    return dict(rational=str(root.lo) if root.lo == root.hi else None,
                polynomial=[str(value) for value in root.p],
                interval=[str(root.lo), str(root.hi)])



def _pair_row(result, index, obstacle_index, kind):
    return dict(kind=kind, segment=index, obstacle=obstacle_index,
                status=result['status'], initial_state=result['initial_state'],
                exact_time=root_certificate(result['root']),
                immediate=result['immediate'], end_state=result['end_state'],
                touches_end=result['touches_end'],
                incidences=sorted(result['incidences']),
                features=sorted(result['features']),
                first_contact_status=result['contact_status'],
                probes=[(str(s), state) for s, state in result['probes']])

def _check_piece(current, obstacles, index, spec, kind):
    return tuple(_pair_row(first_penetration(current, obstacles[i], spec), index, i, kind)
                 for i in range(len(obstacles)))

def validate_escape_segments(moving, obstacles, motion_specs, ray_path=None):
    """Audit every finite piece; this helper makes no infinite-ray claim.

    Motion specifications contain (u1, translation, center) exact tuples. The
    first pose is exactly the supplied moving ring; the optional translation
    tail starts at exact zero after the finite rigid path. JSON field names,
    row ordering, pair counts, and the list-valued ``pairs`` match the audit
    contract. The existing exact translation verifier owns the infinite ray.
    """
    current = tuple(_exact_point(point) for point in moving)
    obstacles = tuple(tuple(_exact_point(point) for point in ring) for ring in obstacles)
    specs = tuple(_exact_motion(spec) for spec in motion_specs)
    for spec in specs:
        if abs(spec[0]) > 1:
            raise ValueError('oracle path piece exceeds the quarter-turn contract')
    motions = list(specs)
    tail_count = 0
    if ray_path is not None:
        ray_path = tuple(_exact_point(point) for point in ray_path)
        if len(ray_path) < 2 or ray_path[0] != (0, 0):
            raise ValueError('oracle tail polyline must start at exact zero and contain a segment')
        for start, end in zip(ray_path, ray_path[1:]):
            motions.append((F(0), (end[0]-start[0], end[1]-start[1]), (F(0), F(0))))
            tail_count += 1
    poses = [current]
    for spec in motions:
        current = ring_at(current, spec, F(1))
        poses.append(current)
    se2_endpoint = poses[len(specs)]
    groups = tuple(_check_piece(poses[i], obstacles, i if i < len(specs) else i-len(specs),
                               motions[i], 'se2' if i < len(specs) else 'ray_prefix')
                   for i in range(len(motions)))
    rows = [row for group in groups for row in group]
    return dict(valid=all(row["status"] == "FREE" for row in rows),
                se2_segments=len(specs), ray_prefix_segments=tail_count,
                se2_pair_checks=len(specs)*len(obstacles),
                ray_prefix_pair_checks=tail_count*len(obstacles),
                first_contact_calls=len(rows),
                overlapping_probe_count=sum(state == 1 for row in rows for _, state in row["probes"]),
                infinite_ray_verified=False, pairs=rows,
                se2_endpoint=[[str(value) for value in point] for point in se2_endpoint],
                final_endpoint=[[str(value) for value in point] for point in current])
