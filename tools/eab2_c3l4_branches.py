"""Deterministic branch regressions; expected slopes are analytic constants.

This module only constructs inputs. Exact proof checking is in the separate
standard-library-only eab2_branch_verify module, not in a geometry generator.
"""
import copy
from dataclasses import replace
from fractions import Fraction as Q
from itertools import combinations

from eab.kernel2d.assembly import Body2
from eab.kernel2d.contacts import assemble_contact_set2
from eab2_c3l4_diff import exact_wire, formal_cases, geometry_jet, refresh_case, require, t1b_cases


def transformed_body(body, name, vertices, offset=(Q(0), Q(0))):
    return Body2.from_vertices(name, vertices, boundary_type=body.boundary_type, dof_mask=body.dof_mask,
        reference_point=tuple(Q(v) + d for v, d in zip(body.reference_point, offset)),
        dof_anchor=tuple(Q(v) + d for v, d in zip(body.dof_anchor, offset)), dead=body.dead, live=body.live)


def specification(source, name, model, channels, expected):
    template = copy.deepcopy(next(q for _, q in source["queries"] if q["result"]["parameter"] == "t"))
    queries = []
    for (parameter, jet), (right, left) in zip(channels, expected):
        query = copy.deepcopy(template)
        query["geometry_seed"] = jet
        query["generated_channel"] = True
        query["result"]["parameter"] = parameter
        query["result"]["differentiability"] = "smooth" if right == left else "one_sided"
        query["result"]["right_derivative"] = query["result"]["directional_derivative"] = exact_wire(right)
        query["result"]["left_derivative"] = exact_wire(left)
        query["result"]["reason"] = None
        query["direction_domain"] = dict(positive=True, negative=True)
        query["analytic_expected"] = dict(right=exact_wire(right), left=exact_wire(left))
        queries.append((len(queries), query))
    case = dict(case_id=name, family="branch", model=model,
                contacts=exact_wire(assemble_contact_set2(model)),
                bases=dict(critical=copy.deepcopy(source["bases"]["critical"])), queries=queries)
    case = refresh_case(case)
    for _, query in case["queries"]:
        truth = query["analytic_expected"]
        require(query["result"]["right_derivative"] == truth["right"] and
                query["result"]["left_derivative"] == truth["left"], "analytic branch referee regression: " + name)
        query["expectation_source"] = "analytic multibranch regression + repaired live Python + independent K checker"
    return case


def branch_cases(selection=None):
    source = next(formal_cases({"g1_unreversed_t2"}))
    jet = next(q["geometry_seed"] for _, q in source["queries"] if q["result"]["parameter"] == "t")
    for tilt, faces in ((Q(1, 4), (2,)), (Q(1, 8), (1, 2, 3, 4, 0))):
        name = "branch/open_" + str(tilt)
        if selection is not None and name not in selection:
            continue
        delta = tilt - Q(1, 4)
        by_id = dict(zip(map(tuple, jet["vertex_ids"]), jet["vertices"][0]))
        bodies = tuple(transformed_body(body, body.body_id,
            [tuple(Q(x) + delta * Q(v) for x, v in zip(point, by_id[body.body_id, i]))
             for i, point in enumerate(body.original_vertices)]) for body in source["model"].bodies)
        model = replace(source["model"], bodies=bodies)
        channels, expected = [], []
        for face in faces:
            parameter = "all" if not face else "face" + str(face)
            value = copy.deepcopy(jet)
            value["parameters"] = [parameter]
            for index, (body, vertex) in enumerate(value["vertex_ids"]):
                body_index = int(body.split("_")[-1]) - 1
                belongs = body_index if vertex in (0, 3) else body_index + 1
                if face and belongs != face:
                    value["vertices"][0][index] = ["0/1", "0/1"]
            channels.append((parameter, value))
            expected.append((Q(1), Q(1)) if not face else (Q(1, 2), Q(0)))
        yield specification(source, name, model, channels, expected)
    for closed in (False, True):
        name = "branch/two_closed" if closed else "branch/two_open"
        if selection is not None and name not in selection:
            continue
        src = next(formal_cases({"g1_slender"})) if closed else source
        original = next(q["geometry_seed"] for _, q in src["queries"] if q["result"]["parameter"] == "t")
        directions = dict(zip(map(tuple, original["vertex_ids"]), original["vertices"][0]))
        bodies, derivatives = [], {}
        for prefix, offset in (("P_", Q(0)), ("Q_", Q(32))):
            for body in src["model"].bodies:
                identity = prefix + body.body_id
                bodies.append(transformed_body(body, identity,
                    [(Q(x) + offset, Q(y)) for x, y in body.original_vertices], (offset, Q(0))))
                derivatives[identity] = [tuple(map(Q, directions[body.body_id, i])) for i in range(len(body.original_vertices))]
        model = replace(src["model"], bodies=tuple(bodies), pairs=tuple(combinations(range(len(bodies)), 2)))
        channels = []
        for parameter, p, q in (("tP", 1, 0), ("tQ", 0, 1), ("tP+2tQ", 1, 2)):
            vertices = [[tuple((p if body.body_id.startswith("P_") else q) * v for v in velocity)
                         for velocity in derivatives[body.body_id]] for body in bodies]
            channels.append((parameter, geometry_jet(model, parameter, vertices)))
        slope = Q(15, 16) if closed else Q(1)
        yield specification(src, name, model, channels, [(slope, Q(0)), (slope, Q(0)), (2 * slope, slope)])
    name = "branch/closed_singleton_t1b03"
    if selection is None or name in selection:
        case = next(t1b_cases({"t1b/03"}))
        case.update(case_id=name, family="branch")
        for _, query in case["queries"]:
            require(query["result"]["right_derivative"] is not None and query["result"]["left_derivative"] is not None,
                    "closed singleton basis requires K certificates")
        yield case
