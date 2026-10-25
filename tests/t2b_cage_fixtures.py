"""Small hand-built exact certificates, independent of the cage proposer.

The enclosure geometry is a rectangle inside four rectangular walls.  The
capped example uses a long rectangle whose rotated vertical span exceeds the
room height.  Witnesses below are supplied explicitly, never found by search.
"""
from fractions import Fraction as F
import json


def exact_copy(value):
    """Copy only the closed exact scalar/list/dict fixture subset."""
    if isinstance(value, dict):
        return {key: exact_copy(value[key]) for key in value}
    if isinstance(value, (list, tuple)):
        return [exact_copy(child) for child in value]
    return value


def json_value(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {key: json_value(value[key]) for key in value}
    if isinstance(value, (list, tuple)):
        return [json_value(child) for child in value]
    return value


def rectangle(x0, y0, x1, y1):
    return [[F(x), F(y)] for x, y in
            ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def square_loop(half):
    ring = rectangle(-F(half), -F(half), F(half), F(half))
    return ring + [ring[0][:]]


def instance_of(certificate):
    return exact_copy({key: certificate[key] for key in ("moving", "obstacles")})


def json_text(value):
    """Serialize exact coordinates canonically without changing integer indices."""
    return json.dumps(json_value(value), ensure_ascii=True, indent=2) + "\n"


def closed_disk_certificate():
    moving = rectangle(-2, -2, 2, 2)
    obstacles = [rectangle(-4, -4, 4, -3), rectangle(3, -3, 4, 3),
                 rectangle(-4, 3, 4, 4), rectangle(-4, -3, -3, 3)]
    loop = square_loop(3)
    interval = {"rho": F(0), "pieces": [{"kind": "disk"}], "loop": loop,
                "witnesses": [[0, index] for index in range(4)]}
    links = [{"at": index, "chain": [exact_copy(loop), exact_copy(loop)],
              "witnesses": [[[['exact', 0], index] for index in range(4)]]}
             for index in (1, 2)]
    return {"format": "eab.t2b.cage/1", "moving": moving,
            "obstacles": obstacles, "center": [F(0), F(0)], "radius": F(3),
            "moving_pieces": [exact_copy(moving)],
            "obstacle_pieces": [{"obstacle": index, "ring": exact_copy(ring)}
                                for index, ring in enumerate(obstacles)],
            "disk": {"radius": F(2), "host": 0,
                     "polygon": rectangle(-1, -1, 1, 1)},
            "chain": {"kind": "closed", "breakpoints": [F(-1), F(1), F(3)]},
            "start_interval": 1, "intervals": [exact_copy(interval), exact_copy(interval)],
            "links": links, "caps": []}


def refined_rotated_certificate():
    certificate = closed_disk_certificate()
    interval = exact_copy(certificate["intervals"][0])
    interval["rho"] = F(3, 2)
    interval["pieces"].append({"kind": "rotated", "piece": 0,
                               "polygon": rectangle(F(-1, 4), F(-1, 4),
                                                    F(1, 4), F(1, 4))})
    certificate["chain"]["breakpoints"] = [F(index, 2) for index in range(-2, 7)]
    certificate["intervals"] = [exact_copy(interval) for _ in range(8)]
    loop = interval["loop"]
    certificate["links"] = [
        {"at": index, "chain": [exact_copy(loop), exact_copy(loop)],
         "witnesses": [[[['disk'], index] for index in range(4)]]}
        for index in range(1, 9)]
    certificate["start_interval"] = 2
    return certificate


def capped_certificate():
    moving = rectangle(F(-3, 2), F(-1, 2), F(3, 2), F(1, 2))
    obstacles = [rectangle(-10, -10, 10, F(-3, 5)),
                 rectangle(-10, F(3, 5), 10, 10),
                 rectangle(-10, F(-3, 5), F(-8, 5), F(3, 5)),
                 rectangle(F(8, 5), F(-3, 5), 10, F(3, 5))]
    loop = square_loop(F(1, 2))
    contraction = [loop, square_loop(F(3, 20)), square_loop(0)]
    witnesses = [[[['exact', 0], index] for index in (0, 3, 1, 2)],
                 [[['exact', 0], 0] for _ in range(4)]]
    return {"format": "eab.t2b.cage/1", "moving": moving,
            "obstacles": obstacles, "center": [F(0), F(0)], "radius": F(8, 5),
            "moving_pieces": [exact_copy(moving)],
            "obstacle_pieces": [{"obstacle": index, "ring": exact_copy(ring)}
                                for index, ring in enumerate(obstacles)],
            "disk": None,
            "chain": {"kind": "capped", "breakpoints": [F(-1, 10), F(1, 10)]},
            "start_interval": 1,
            "intervals": [{"rho": F(1, 3), "pieces": [
                {"kind": "rotated", "piece": 0,
                 "polygon": rectangle(F(-7, 6), F(-1, 6), F(7, 6), F(1, 6))}],
                "loop": exact_copy(loop), "witnesses": [[0, index] for index in (0, 3, 1, 2)]}],
            "links": [], "caps": [
                {"at": index, "chain": exact_copy(contraction), "witnesses": exact_copy(witnesses)}
                for index in (0, 1)]}


def repeat_winding(certificate, repetitions=2):
    """Preserve every homotopy while making the signed winding an even integer."""
    result = exact_copy(certificate)
    for interval in result["intervals"]:
        interval["loop"] = [*[point for _ in range(repetitions) for point in interval["loop"][:-1]], interval["loop"][0]]
        interval["witnesses"] *= repetitions
    for item in (*result["links"], *result["caps"]):
        item["chain"] = [[*[point for _ in range(repetitions) for point in loop[:-1]], loop[0]] for loop in item["chain"]]
        item["witnesses"] = [[entry for _ in range(repetitions) for entry in row] for row in item["witnesses"]]
    return result


def forged_case(name):
    """One defective clause per named input, unless the theorem makes it redundant."""
    capped_names = {"open_cap_polyline", "same_end_caps", "wrong_cap_side",
                    "cap_start_mismatch", "nonconstant_cap", "missing_cap",
                    "short_cap_chain", "cap_witness_truncated", "false_cap_witness"}
    certificate = capped_certificate() if name in capped_names else closed_disk_certificate()
    expected = "V0"
    if name == "negative_radius":
        certificate["radius"] = -certificate["radius"]
    elif name == "undersized_radius":
        certificate["radius"] = F(1, 100)
    elif name == "nonconvex_disk":
        certificate["disk"]["polygon"] = [[F(x), F(y)] for x, y in
                                           ((-1, -1), (1, -1), (0, 0), (1, 1), (-1, 1))]
    elif name == "repeated_disk_vertex":
        certificate["disk"]["polygon"].insert(1, certificate["disk"]["polygon"][0][:])
    elif name == "open_interval_polyline":
        certificate["intervals"][0]["loop"][-1] = [F(-2), F(-3)]
    elif name == "open_link_polyline":
        certificate["links"][0]["chain"][0][-1] = [F(-2), F(-3)]
    elif name == "open_cap_polyline":
        certificate["caps"][0]["chain"][1][-1] = [F(-1, 10), F(-3, 20)]
    elif name == "truncated_barrier_witness":
        certificate["intervals"][0]["witnesses"].pop()
    elif name == "truncated_link_witness":
        certificate["links"][0]["witnesses"][0].pop()
    elif name == "cap_witness_truncated":
        certificate["caps"][0]["witnesses"].pop()
    elif name == "missing_barrier_witness":
        del certificate["intervals"][0]["witnesses"]
    elif name == "missing_obstacle_pieces":
        certificate["obstacle_pieces"][3]["obstacle"] = 2
    elif name == "empty_interval_pieces":
        certificate["intervals"][0]["pieces"] = []
    elif name == "short_link_chain":
        certificate["links"][0]["chain"].pop()
        certificate["links"][0]["witnesses"] = []
    elif name == "short_cap_chain":
        certificate["caps"][0]["chain"] = [certificate["caps"][0]["chain"][0]]
        certificate["caps"][0]["witnesses"] = []
    elif name == "unequal_link_vertices":
        certificate["links"][0]["chain"][1].insert(1, [F(-3), F(-3)])
    elif name == "invalid_start_index":
        certificate["start_interval"] = 0
    elif name == "negative_disk_radius":
        certificate["disk"]["radius"] = F(-2)
    elif name == "unused_bad_disk":
        certificate = refined_rotated_certificate()
        certificate["disk"]["radius"] = F(3)
        for interval in certificate["intervals"]:
            interval["witnesses"] = [[1, index] for index in range(4)]
        for item in certificate["links"]:
            item["witnesses"] = [[[['exact', 0], index] for index in range(4)]]
        expected = "V3"
    elif name == "same_end_caps":
        certificate["caps"][1]["at"] = 0
        expected = "CHAIN"
    elif name == "wrong_cap_side":
        cap = certificate["caps"][0]
        cap["chain"].insert(1, exact_copy(cap["chain"][0]))
        cap["witnesses"].insert(0, [[["right", 0], index] for index in (0, 3, 1, 2)])
        cap["witnesses"][0][0][0] = ["left", 0]
        expected = "V5"
    elif name == "cap_start_mismatch":
        certificate["caps"][0]["chain"][0] = square_loop(F(3, 20))
        expected = "CHAIN"
    elif name == "nonconstant_cap":
        certificate["caps"][0]["chain"][-1] = square_loop(F(1, 10))
        expected = "CHAIN"
    elif name == "missing_cap":
        certificate["caps"].pop()
        expected = "CHAIN"
    elif name == "start_interval_without_zero":
        certificate["start_interval"] = 2
        expected = "CHAIN"
    elif name == "cross_chart_interval":
        certificate["chain"]["breakpoints"][1] = F(3, 2)
        for link in certificate["links"]:
            link["witnesses"] = [[[["disk"], index] for index in range(4)]]
        expected = "CHAIN"
    elif name == "link_endpoint_mismatch":
        certificate["links"][0]["chain"][1] = square_loop(F(13, 4))
        expected = "CHAIN"
    elif name == "invalid_side_index":
        certificate["links"][0]["witnesses"][0][0][0] = ["left", 100]
        expected = "V5"
    elif name == "false_barrier_witness":
        certificate["intervals"][0]["witnesses"][0] = [0, 2]
        expected = "V4"
    elif name == "false_link_witness":
        certificate["links"][0]["witnesses"][0][0] = [["disk"], 2]
        expected = "V5"
    elif name == "false_cap_witness":
        certificate["caps"][0]["witnesses"][0][0][1] = 1
        expected = "V5"
    elif name == "missed_contracted_edge":
        certificate = refined_rotated_certificate()
        u = F(-3, 4)
        cosine, sine = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        polygon = rectangle(F(-3, 4), F(-1, 4), F(-1, 4), F(1, 4))
        certificate["intervals"][0]["pieces"][1]["polygon"] = [
            [cosine*x-sine*y, sine*x+cosine*y] for x, y in polygon]
        expected = "V2"
    elif name == "merely_touching_barrier":
        for interval in certificate["intervals"]:
            interval["loop"] = square_loop(2)
        for link in certificate["links"]:
            link["chain"] = [square_loop(2), square_loop(2)]
        expected = "V4"
    elif name == "initial_overlap":
        obstacle = rectangle(F(-1, 10), F(-1, 10), F(1, 10), F(1, 10))
        certificate["obstacles"].append(obstacle)
        certificate["obstacle_pieces"].append({"obstacle": 4, "ring": exact_copy(obstacle)})
        expected = "V6"
    elif name == "equal_area_outside_partition":
        certificate["moving"] = rectangle(20, -2, 24, 2)
    elif name == "negative_host_halfplane":
        certificate["center"] = [F(10), F(0)]
        certificate["radius"] = F(13)
        for ring in certificate["obstacles"]:
            for point in ring:
                point[0] = F(point[0]) + 10
        for item in certificate["obstacle_pieces"]:
            for point in item["ring"]:
                point[0] = F(point[0]) + 10
        certificate["disk"]["radius"] = F(1, 4)
        certificate["disk"]["polygon"] = rectangle(F(-1, 10), F(-1, 10), F(1, 10), F(1, 10))
        for link in certificate["links"]:
            link["witnesses"] = [[[["disk"], index] for index in range(4)]]
        expected = "V3"
    elif name == "small_rho":
        certificate = refined_rotated_certificate()
        for interval in certificate["intervals"]:
            interval["rho"] = F(5, 4)
        expected = "V1"
    elif name == "negative_rho":
        certificate["intervals"][0]["rho"] = F(-1)
        expected = "V1"
    elif name == "instance_mismatch":
        instance = instance_of(certificate)
        instance["moving"] = [*instance["moving"][1:], *instance["moving"][:1]]
        return instance, certificate, "V0"
    else:
        raise KeyError(name)
    return instance_of(certificate), certificate, expected


FORGERY_NAMES = (
    "negative_radius", "undersized_radius", "nonconvex_disk", "repeated_disk_vertex",
    "open_interval_polyline", "open_link_polyline", "open_cap_polyline",
    "truncated_barrier_witness", "truncated_link_witness", "cap_witness_truncated",
    "missing_barrier_witness", "missing_obstacle_pieces", "empty_interval_pieces",
    "short_link_chain", "short_cap_chain", "unequal_link_vertices", "invalid_start_index",
    "negative_disk_radius", "unused_bad_disk", "same_end_caps", "wrong_cap_side",
    "cap_start_mismatch", "nonconstant_cap", "missing_cap", "start_interval_without_zero",
    "cross_chart_interval", "link_endpoint_mismatch", "invalid_side_index",
    "false_barrier_witness", "false_link_witness", "small_rho", "negative_rho",
    "instance_mismatch", "false_cap_witness", "missed_contracted_edge",
    "merely_touching_barrier", "initial_overlap", "equal_area_outside_partition",
    "negative_host_halfplane",
)
