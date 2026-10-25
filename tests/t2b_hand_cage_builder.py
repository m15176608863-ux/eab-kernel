"""Construct hand-specified closed cages without production code or floats.

Only lemma section 5's four invariant-disk examples are used.  A barrier
vertex is the rational centroid of the full-dimensional intersection of two
adjacent open penetration regions.  Region construction uses Minkowski
differences, while a separate exact SAT check validates every output segment.
This is a certificate proposer, not the independent cage verifier.
"""

import json
import sys
from fractions import Fraction as F
from pathlib import Path

from t2b_truth_geometry import (
    diamond_plates,
    doorway,
    instance_json,
    json_ring,
    low_room,
    midpoint_wedges,
    rectangle,
    windmill,
)


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def convex_hull(points):
    """Monotone-chain hull; all returned corners are strict CCW corners."""
    ordered = sorted(set(points))
    lower = []
    for point in ordered:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(ordered):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    result = lower[:-1] + upper[:-1]
    if len(result) < 3:
        raise ValueError("no full-dimensional convex hull")
    return result


def penetration_closure(moving, obstacle):
    """Closure of M(moving, obstacle), constructed as obstacle - moving."""
    points = []
    for y in obstacle:
        for x in moving:
            points.append((y[0] - x[0], y[1] - x[1]))
    return convex_hull(points)


def clip_left(polygon, a, b):
    """Clip a convex polygon by the closed left half-plane of a -> b."""
    clipped = []
    if not polygon:
        return clipped
    previous = polygon[-1]
    previous_side = cross(a, b, previous)
    for current in polygon:
        current_side = cross(a, b, current)
        if (current_side >= 0) != (previous_side >= 0):
            alpha = previous_side / (previous_side - current_side)
            clipped.append((previous[0] + alpha * (current[0] - previous[0]),
                            previous[1] + alpha * (current[1] - previous[1])))
        if current_side >= 0:
            clipped.append(current)
        previous = current
        previous_side = current_side
    return clipped


def convex_intersection(first, second):
    result = list(first)
    for index, a in enumerate(second):
        b = second[(index + 1) % len(second)]
        result = clip_left(result, a, b)
    return convex_hull(result)


def centroid_vertices(ring):
    x_total = F(0)
    y_total = F(0)
    for x, y in ring:
        x_total += x
        y_total += y
    return x_total / len(ring), y_total / len(ring)


def projection(ring, axis, translation):
    values = []
    for x, y in ring:
        values.append(axis[0] * (x + translation[0]) +
                      axis[1] * (y + translation[1]))
    low = values[0]
    high = values[0]
    for value in values[1:]:
        if value < low:
            low = value
        if value > high:
            high = value
    return low, high


def strictly_penetrates(moving, obstacle, translation):
    """Section 1 strict SAT, independent of the Minkowski construction."""
    zero = (F(0), F(0))
    for ring in (moving, obstacle):
        for index, a in enumerate(ring):
            b = ring[(index + 1) % len(ring)]
            axis = (b[1] - a[1], a[0] - b[0])
            if axis == zero:
                raise ValueError("zero separation axis")
            first_low, first_high = projection(moving, axis, translation)
            second_low, second_high = projection(obstacle, axis, zero)
            if first_high <= second_low or second_high <= first_low:
                return False
    return True


def barrier_from_cycle(disk, center, obstacles, cycle):
    """Join exact interior overlap points following the stated obstacle cycle."""
    world_disk = []
    for x, y in disk:
        world_disk.append((x + center[0], y + center[1]))
    regions = []
    for obstacle in obstacles:
        regions.append(penetration_closure(world_disk, obstacle))
    vertices = []
    for position, index in enumerate(cycle):
        following = cycle[(position + 1) % len(cycle)]
        overlap = convex_intersection(regions[index], regions[following])
        point = centroid_vertices(overlap)
        if not strictly_penetrates(world_disk, obstacles[index], point):
            raise ValueError("overlap centroid not strictly in first region")
        if not strictly_penetrates(world_disk, obstacles[following], point):
            raise ValueError("overlap centroid not strictly in second region")
        vertices.append(point)
    vertices.append(vertices[0])
    witnesses = []
    for index in range(len(vertices) - 1):
        witness = None
        for obstacle_index, obstacle in enumerate(obstacles):
            if (strictly_penetrates(world_disk, obstacle, vertices[index]) and
                    strictly_penetrates(world_disk, obstacle, vertices[index + 1])):
                witness = [0, obstacle_index]
                break
        if witness is None:
            raise ValueError("no common strict witness for barrier segment")
        witnesses.append(witness)
    return vertices, witnesses


def rational_twenty_gon():
    """Exactly the 20-gon specified in lemma section 5, example 2."""
    quarter = ((F(1), F(0)), (F(12, 13), F(5, 13)),
               (F(4, 5), F(3, 5)), (F(3, 5), F(4, 5)),
               (F(5, 13), F(12, 13)))
    result = []
    for _ in range(4):
        result.extend(quarter)
        next_quarter = []
        for x, y in quarter:
            next_quarter.append((-y, x))
        quarter = tuple(next_quarter)
    return tuple(result)


def closed_certificate(moving, obstacles, center, disk_radius, disk, cycle):
    """Make the two-interval, disk-only certificate required by WO-T2b-V."""
    instance = instance_json(moving, obstacles)
    loop, witnesses = barrier_from_cycle(disk, center, obstacles, cycle)
    obstacle_pieces = []
    encoded_obstacles = []
    for index, obstacle in enumerate(obstacles):
        obstacle_pieces.append({"obstacle": index, "ring": json_ring(obstacle)})
        encoded_obstacles.append(json_ring(obstacle))
    intervals = []
    for _ in range(2):
        interval_witnesses = []
        for piece_index, obstacle_index in witnesses:
            interval_witnesses.append([piece_index, obstacle_index])
        intervals.append({"rho": "0", "pieces": [{"kind": "disk"}],
                          "loop": json_ring(loop), "witnesses": interval_witnesses})
    links = []
    for at in (1, 2):
        link_witnesses = []
        for _, obstacle_index in witnesses:
            link_witnesses.append([["disk"], obstacle_index])
        links.append({"at": at, "chain": [json_ring(loop), json_ring(loop)],
                      "witnesses": [link_witnesses]})
    certificate = {
        "format": "eab.t2b.cage/1",
        "moving": json_ring(moving),
        "obstacles": encoded_obstacles,
        "center": [str(center[0]), str(center[1])],
        "radius": "2",
        "moving_pieces": [json_ring(moving)],
        "obstacle_pieces": obstacle_pieces,
        "disk": {"radius": str(disk_radius), "host": 0, "polygon": json_ring(disk)},
        "chain": {"kind": "closed", "breakpoints": ["-1", "1", "3"]},
        "start_interval": 1,
        "intervals": intervals,
        "links": links,
        "caps": [],
    }
    return instance, certificate


def build_hand_cages():
    """Return all four named, exactly specified positive examples."""
    result = {}
    delta = F(1, 8) - F(1, 1024)
    radius = F(3, 8) + F(1, 1024)
    diamond = ((radius, F(0)), (F(0), radius),
               (-radius, F(0)), (F(0), -radius))
    moving, obstacles = doorway(delta)
    result["doorway"] = closed_certificate(
        moving, obstacles, (F(0), F(1, 2)), radius, diamond, (0, 2, 4, 3, 1))
    twenty = rational_twenty_gon()
    moving, obstacles = windmill()
    result["windmill"] = closed_certificate(
        moving, obstacles, (F(0), F(0)), F(1), twenty, (0, 1, 2, 3))
    moving, obstacles = midpoint_wedges()
    result["midpoint_wedges"] = closed_certificate(
        moving, obstacles, (F(0), F(0)), F(1), twenty, (0, 1, 2, 3))
    moving, obstacles = diamond_plates()
    square = rectangle(F(-49, 100), F(-49, 100), F(49, 100), F(49, 100))
    result["diamond_plates"] = closed_certificate(
        moving, obstacles, (F(0), F(0)), F(7, 10), square, (0, 1, 2, 3))
    return result


def rotate_ring(ring, parameter):
    """Section 1's chart-0 Cayley matrix, with exact rational entries."""
    square = parameter * parameter
    denominator = 1 + square
    cosine = (1 - square) / denominator
    sine = 2 * parameter / denominator
    rotated = []
    for x, y in ring:
        rotated.append((cosine * x - sine * y, sine * x + cosine * y))
    return rotated


def subdivide_loop(loop, count):
    result = []
    for index in range(len(loop) - 1):
        a = loop[index]
        b = loop[index + 1]
        for step in range(count):
            weight = F(step, count)
            result.append((a[0] + weight * (b[0] - a[0]),
                           a[1] + weight * (b[1] - a[1])))
    result.append(result[0])
    return result


def segment_witnesses(moving, obstacles, loop):
    witnesses = []
    for index in range(len(loop) - 1):
        witness = None
        for obstacle_index, obstacle in enumerate(obstacles):
            if (strictly_penetrates(moving, obstacle, loop[index]) and
                    strictly_penetrates(moving, obstacle, loop[index + 1])):
                witness = [0, obstacle_index]
                break
        if witness is None:
            return None
        witnesses.append(witness)
    return witnesses


def scaled_loop(loop, scale):
    result = []
    for x, y in loop:
        result.append((scale * x, scale * y))
    return result


def contraction_chain(moving, obstacles, loop, count):
    """Try the explicitly prescribed radial homotopy with exact witnesses."""
    chain = [loop]
    witnesses = []
    for step in range(1, count + 1):
        following = scaled_loop(loop, F(count - step, count))
        previous = chain[-1]
        group = []
        for index in range(len(loop) - 1):
            points = (previous[index], previous[index + 1],
                      following[index + 1], following[index])
            witness = None
            for obstacle_index, obstacle in enumerate(obstacles):
                common = True
                for point in points:
                    if not strictly_penetrates(moving, obstacle, point):
                        common = False
                        break
                if common:
                    witness = [["exact", 0], obstacle_index]
                    break
            if witness is None:
                return None
            group.append(witness)
        chain.append(following)
        witnesses.append(group)
    encoded_chain = []
    for line in chain:
        encoded_chain.append(json_ring(line))
    return {"chain": encoded_chain, "witnesses": witnesses}


def build_low_room_cage():
    """One-interval capped cage at Cayley endpoints +/-1/23 (lemma ex. 5)."""
    moving, obstacles = low_room()
    instance = instance_json(moving, obstacles)
    rho = F(7, 50)
    core = rectangle(F(-3, 2) + rho, F(-1, 2) + rho,
                     F(3, 2) - rho, F(1, 2) - rho)
    loop, _ = barrier_from_cycle(core, (F(0), F(0)), obstacles, (0, 2, 4, 3, 1))
    negative = rotate_ring(moving, F(-1, 23))
    positive = rotate_ring(moving, F(1, 23))
    caps = None
    for refinement in (1, 2, 4, 8, 16, 32):
        refined_loop = subdivide_loop(loop, refinement)
        left = contraction_chain(negative, obstacles, refined_loop, refinement)
        right = contraction_chain(positive, obstacles, refined_loop, refinement)
        if left is not None and right is not None:
            left["at"] = 0
            right["at"] = 1
            caps = [left, right]
            loop = refined_loop
            break
    if caps is None:
        raise ValueError("prescribed low-room radial contraction did not certify")
    witnesses = segment_witnesses(core, obstacles, loop)
    if witnesses is None:
        raise ValueError("low-room subdivided barrier lost a segment witness")
    obstacle_pieces = []
    encoded_obstacles = []
    for index, obstacle in enumerate(obstacles):
        obstacle_pieces.append({"obstacle": index, "ring": json_ring(obstacle)})
        encoded_obstacles.append(json_ring(obstacle))
    certificate = {
        "format": "eab.t2b.cage/1", "moving": json_ring(moving),
        "obstacles": encoded_obstacles, "center": ["0", "0"],
        "radius": "8/5", "moving_pieces": [json_ring(moving)],
        "obstacle_pieces": obstacle_pieces, "disk": None,
        "chain": {"kind": "capped", "breakpoints": ["-1/23", "1/23"]},
        "start_interval": 1,
        "intervals": [{"rho": str(rho),
                       "pieces": [{"kind": "rotated", "piece": 0,
                                   "polygon": json_ring(core)}],
                       "loop": json_ring(loop), "witnesses": witnesses}],
        "links": [], "caps": caps,
    }
    return instance, certificate


def build_large_closed_cage(interval_count=2000):
    """Disk-only stress case: 16 geometric loop vertices, explicit closure.

    An even interval count puts the chart boundary lambda=1 at a breakpoint.
    The final repeated point makes the serialized closed polyline length 17.
    """
    if (not isinstance(interval_count, int) or isinstance(interval_count, bool)
            or interval_count < 2 or interval_count % 2):
        raise ValueError("interval count must be a positive even integer >= 2")
    instance, certificate = build_hand_cages()["diamond_plates"]
    old_line = certificate["intervals"][0]["loop"]
    rational_line = []
    for x, y in old_line:
        rational_line.append((F(x), F(y)))
    loop = subdivide_loop(rational_line, 4)
    moving, obstacles = diamond_plates()
    disk = rectangle(F(-49, 100), F(-49, 100), F(49, 100), F(49, 100))
    witnesses = segment_witnesses(disk, obstacles, loop)
    if witnesses is None:
        raise ValueError("large cage lost a strict segment witness")
    encoded_loop = json_ring(loop)
    breakpoints = []
    for index in range(interval_count + 1):
        breakpoints.append(str(F(-1) + F(4 * index, interval_count)))
    certificate["chain"]["breakpoints"] = breakpoints
    certificate["start_interval"] = (interval_count + 3) // 4
    intervals = []
    links = []
    link_witnesses = []
    for _, obstacle_index in witnesses:
        link_witnesses.append([["disk"], obstacle_index])
    for index in range(interval_count):
        intervals.append({"rho": "0", "pieces": [{"kind": "disk"}],
                          "loop": encoded_loop, "witnesses": witnesses})
        links.append({"at": index + 1, "chain": [encoded_loop, encoded_loop],
                      "witnesses": [link_witnesses]})
    certificate["intervals"] = intervals
    certificate["links"] = links
    return instance, certificate


def write_hand_cages(destination, include_low_room=False):
    """Write into an existing output directory; never create directories."""
    destination = Path(destination)
    paths = []
    cases = build_hand_cages()
    if include_low_room:
        cases["low_room"] = build_low_room_cage()
    for name, pair in cases.items():
        instance, certificate = pair
        for suffix, data in (("instance", instance), ("cert", certificate)):
            path = destination / (name + "." + suffix + ".json")
            content = json.dumps(data, ensure_ascii=True, indent=2) + "\n"
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
            paths.append(path)
    return paths


def generate_hand_cage_files():
    destination = Path(__file__).parent / "data" / "t2b_hand_cages"
    include_low_room = False
    args = list(sys.argv[1:])
    while args:
        option = args.pop(0)
        if option == "--include-low-room":
            include_low_room = True
        elif option == "--output-dir" and args:
            destination = Path(args.pop(0))
        else:
            raise ValueError("expected --include-low-room or --output-dir PATH")
    paths = write_hand_cages(destination, include_low_room)
    with open(1, "w", encoding="utf-8", closefd=False) as output:
        for path in paths:
            output.write(str(path) + "\n")
    return 0


STATUS = generate_hand_cage_files() if __name__ == "__main__" else 0
if STATUS:
    raise ValueError("hand-cage generation failed")
