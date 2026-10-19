"""Exact public geometry jets and independent propagation to raw LP columns.

This tool reads original vertex IDs, not family contact-seed shortcuts. It
forms unnormalized edge derivatives and differentiates moments about the
physical anchor; algebraic reference points are frozen.
"""
from fractions import Fraction as Q
from eab.kernel2d.sensitivity import LimitSeed2


def _q(value):
    value = Q(value)
    return str(value.numerator) + "/" + str(value.denominator)


def geometry_seed(assembly, parameter=None, *, vertices=None, dead=None,
                  live=None, anchors=None, mu=0):
    bodies = sorted(assembly.bodies, key=lambda body: body.body_id)
    ids = [[body.body_id, i] for body in bodies
           for i in range(len(body.original_vertices or body.vertices))]
    vertices, dead, live, anchors = (value or {} for value in (vertices, dead, live, anchors))
    result = dict(parameters=[] if parameter is None else [parameter],
                  vertex_ids=ids, body_ids=[body.body_id for body in bodies],
                  vertices=[], dead=[], live=[], dof_anchor=[], mu=[])
    if parameter is not None:
        result["vertices"] = [[[_q(v) for v in vertices.get((name, i), (0, 0))] for name, i in ids]]
        for key, mapping, width in (("dead", dead, 3), ("live", live, 3), ("dof_anchor", anchors, 2)):
            result[key] = [[[_q(v) for v in mapping.get(body.body_id, (0,) * width)] for body in bodies]]
        result["mu"] = [_q(mu)]
    return result


def propagate_geometry_seed(problem, record, index=0):
    """Rebuild dA/db/dc from vertex/load/anchor jets, with exact shared seeds."""
    parameter = record["parameters"][index]
    vertices = {(name, i): tuple(Q(v) for v in value) for (name, i), value
                in zip(record["vertex_ids"], record["vertices"][index])}
    loads = {key: {name: tuple(Q(v) for v in value) for name, value
                  in zip(record["body_ids"], record[key][index])}
             for key in ("dead", "live", "dof_anchor")}
    dmu = Q(record["mu"][index])
    bodies = problem.assembly.bodies
    by_id = {body.body_id: body for body in bodies}
    by_point = {}
    for body in bodies:
        for i, raw in enumerate(body.original_vertices or body.vertices):
            point = tuple(Q(v) for v in raw)
            seed = vertices[(body.body_id, i)]
            if point in by_point and by_point[point] != seed:
                raise ValueError("geometry jet breaks a shared vertex")
            by_point[point] = seed
    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]
    def project(body, value, derivative):
        anchor = body.dof_anchor
        arm = tuple(anchor[k] - body.reference_point[k] for k in (0, 1))
        da = loads["dof_anchor"][body.body_id]
        full = (derivative[0], derivative[1], derivative[2]
                - cross(arm, derivative[:2]) - cross(da, value[:2]))
        return tuple(v for v, keep in zip(full, body.dof_mask) if keep)
    columns = []
    for contact in problem.contact_set.constraints:
        body = by_id[contact.label[3]]
        i, j = contact.label[4]
        raw = body.original_vertices or body.vertices
        edge = tuple(Q(raw[j][k]) - Q(raw[i][k]) for k in (0, 1))
        sense = 1 if edge == contact.tangent else -1
        if tuple(sense * v for v in edge) != contact.tangent:
            raise ValueError("contact tangent is not the original edge vector")
        dt = tuple(sense * (vertices[(body.body_id, j)][k] - vertices[(body.body_id, i)][k]) for k in (0, 1))
        dp = by_point[contact.point]
        tangent = contact.tangent
        normal, dn = (-tangent[1], tangent[0]), (-dt[1], dt[0])
        for sign in (-1, 1):
            force = tuple(normal[k] + sign * problem.mu * tangent[k] for k in (0, 1))
            df = tuple(dn[k] + sign * (dmu * tangent[k] + problem.mu * dt[k]) for k in (0, 1))
            column = []
            for k, target in enumerate(bodies):
                side = int(k == contact.a) - int(k == contact.b)
                arm = tuple(contact.point[a] - target.reference_point[a] for a in (0, 1))
                value = (side * force[0], side * force[1], side * cross(arm, force))
                derivative = (side * df[0], side * df[1], side * (cross(dp, force) + cross(arm, df)))
                column.extend(project(target, value, derivative))
            columns.append(tuple(column))
    columns.append(tuple(v for body in bodies for v in project(body, body.live, loads["live"][body.body_id])))
    db = tuple(-v for body in bodies for v in project(body, body.dead, loads["dead"][body.body_id]))
    return LimitSeed2(tuple(tuple(column[i] for column in columns) for i in range(len(db))),
                      db, (Q(0),) * len(problem.c), parameter)
