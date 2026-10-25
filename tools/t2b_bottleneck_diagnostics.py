"""Finite, untrusted diagnostics of cage proposal loss; never a cage proof.

All quantitative feasibility checks use rational arithmetic. Normalized SAT
ranking, angle display and square-root ratios are explicitly diagnostic floats.
The unchanged proposer is observed by temporary in-process helper wrappers.
"""
from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests'), str(ROOT / 'tools')]
import t2b_cage_proposer as proposer


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _winding(loop):
    number = 0
    for a, b in zip(loop, loop[1:]):
        cross = a[0] * b[1] - a[1] * b[0]
        if cross == 0 and _dot(a, b) <= 0:
            return None
        if a[1] <= 0 < b[1] and cross > 0:
            number += 1
        if b[1] <= 0 < a[1] and cross < 0:
            number -= 1
    return number


def pair_margin(moving, obstacle, points):
    """Least Euclidean-normalized SAT overlap over all supplied points.

    Selection is diagnostic float; each returned numerator/norm-squared and
    support feature is exact and sufficient to recompute the selected margin.
    """
    selected = None
    for source, ring in (('moving', moving), ('obstacle', obstacle)):
        for edge, (a, b) in enumerate(proposer._edges(ring)):
            normal = (b[1] - a[1], a[0] - b[0])
            norm2 = _dot(normal, normal)
            if norm2 == 0:
                raise ValueError('zero edge in diagnostic convex ring')
            m = tuple(_dot(normal, p) for p in moving)
            o = tuple(_dot(normal, p) for p in obstacle)
            for point_index, point in enumerate(points):
                shift = _dot(normal, point)
                for side, value, mvalue, ovalue in (
                    ('moving_high_minus_obstacle_low', max(m) + shift - min(o), max(m), min(o)),
                    ('obstacle_high_minus_moving_low', max(o) - min(m) - shift, min(m), max(o)),
                ):
                    normalized = float(value) / math.sqrt(float(norm2))
                    if selected is None or normalized < selected['normalized_overlap_diagnostic']:
                        mi = [i for i, v in enumerate(m) if v == mvalue]
                        oi = [i for i, v in enumerate(o) if v == ovalue]
                        selected = {'normalized_overlap_diagnostic': normalized,
                                    'exact_overlap_numerator': value, 'normal_squared': norm2,
                                    'normal': normal, 'axis_source': source, 'axis_edge': edge,
                                    'inequality': side, 'point_index': point_index,
                                    'moving_support_vertices': mi, 'obstacle_support_vertices': oi,
                                    'feature_type': ('vertex' if len(mi) == 1 else 'edge') + '-' +
                                                    ('vertex' if len(oi) == 1 else 'edge')}
    return selected


def closest_cover(polygons, obstacles, labels, points, kernel_tags=None):
    """Max-min normalized SAT pair; ties retain the original generation order."""
    best = None
    for i, moving in enumerate(polygons):
        for j, obstacle in enumerate(obstacles):
            measure = pair_margin(moving, obstacle['ring'], points)
            if best is None or measure['normalized_overlap_diagnostic'] > best['sat']['normalized_overlap_diagnostic']:
                best = {'moving_kernel_index': i, 'moving_reference': labels[i],
                        'moving_source': None if kernel_tags is None else kernel_tags[i],
                        'obstacle_flat_piece': j, 'obstacle_parent': obstacle['obstacle'],
                        'obstacle_piece_in_parent': sum(q['obstacle'] == obstacle['obstacle'] for q in obstacles[:j]),
                        'sat': measure, 'moving_polygon': moving, 'obstacle_polygon': obstacle['ring']}
    return best


class ProposalTrace(AbstractContextManager):
    """Observe actual failed witness calls, never alter their returned value."""

    def __init__(self):
        self.original_cells = proposer._cells
        self.original_witness = proposer._witness
        self.cell_meta = {}
        self.last_by_stage = {}
        self.failure_count = 0

    def __enter__(self):
        proposer._cells = self.cells
        proposer._witness = self.witness
        return self

    def __exit__(self, *unused):
        proposer._cells = self.original_cells
        proposer._witness = self.original_witness
        return False

    def cells(self, polygons, obstacles, resources, deadline, refs=None):
        result = self.original_cells(polygons, obstacles, resources, deadline, refs)
        frame = sys._getframe(1)
        context = {}
        tags = None
        connection_context = False
        while frame is not None and frame.f_code.co_filename == proposer.__file__:
            local = frame.f_locals
            name = frame.f_code.co_name
            if 'interval' in local and isinstance(local['interval'], dict) and 'pieces' in local['interval']:
                tags = local['interval']['pieces']
                context['rho'] = local['interval']['rho']
            if name == '_capped_candidate' and not connection_context:
                context['knots'] = local['knots']
                if refs is not None and 'value' in local:
                    context['lambda_value'] = local['value']
                    context['lambda_interval'] = (local['a'], local['b'])
                    context['cap_at'] = 0 if local['value'] == local['knots'][0] else len(local['intervals'])
                if tags is not None:
                    index = next((i for i, item in enumerate(local['intervals']) if item['pieces'] is tags), None)
                    context['interval'] = index
                    if index is not None:
                        context['lambda_interval'] = local['knots'][index:index+2]
            if name == '_connection_cells':
                connection_context = True
                context.pop('rho', None)
                context.update(at=local['at'], lambda_value=local['value'])
                context['lambda_interval'] = local['knots'][local['at']-1:local['at']+1]
                context['knots'] = local['knots']
                tags = []
                for reference in refs:
                    if reference[0] == 'exact':
                        tags.append({'kind': 'exact', 'piece': reference[1]})
                    elif reference[0] == 'disk':
                        tags.append({'kind': 'disk', 'host': local['base']['disk']['host']})
                    else:
                        index = local['at'] - 1 if reference[0] == 'left' else local['at']
                        tags.append(local['intervals'][index]['pieces'][reference[1]])
            if name == '_disk_candidate':
                tags = [{'kind': 'disk', 'host': local['base']['disk']['host']}]
            frame = frame.f_back
        labels = list(range(len(polygons))) if refs is None else refs
        if tags is None:
            tags = [{'kind': ref[0], 'piece': ref[1]} if len(ref) == 2 else {'kind': ref[0]}
                    for ref in refs] if refs is not None else None
        self.cell_meta[id(result)] = (result, polygons, obstacles, labels, tags, context)
        return result

    def witness(self, cells, points):
        result = self.original_witness(cells, points)
        if result is not None:
            return result
        self.failure_count += 1
        frame = sys._getframe(1)
        stage = frame.f_code.co_name
        context = {'failure_sequence': self.failure_count}
        for key in ('step', 'steps', 'index', 'at'):
            if key in frame.f_locals and isinstance(frame.f_locals[key], int):
                context[key] = frame.f_locals[key]
        if stage == '_loop_witnesses':
            loop = frame.f_locals['loop']
            context['segment'] = next(i for i, pair in enumerate(zip(loop, loop[1:])) if pair == tuple(points))
        self.last_by_stage[stage] = (cells, tuple(points), context)
        return None

    def report(self):
        rows = []
        for stage, (cells, points, context) in self.last_by_stage.items():
            _, polygons, obstacles, labels, tags, cell_context = self.cell_meta[id(cells)]
            rows.append({'stage': stage, 'context': {**cell_context, **context}, 'points': points,
                         'closest_cover': closest_cover(polygons, obstacles, labels, points, tags)})
        return {'failed_witness_calls': self.failure_count, 'last_failure_per_stage': rows,
                'cover_selection': 'maximize minimum normalized SAT overlap over all query points; ties retain generation order; not a separating proof',
                'timing_boundary': 'observed failed calls include the current attempt interrupted by cooperative time limit; proposer last_geometric_failure only identifies its last completed attempt'}


def rotation_range(candidate):
    """Lift rational orientation endpoints to lambda; float chooses chart only.

    The rational chart choice is checked against its exact half-angle range.
    Path translations/rotation centers are ignored only for this angle range.
    """
    co, si, angle = F(1), F(0), 0.0
    records = [{'piece': -1, 'lambda': F(0), 'angle_radians_diagnostic': 0.0}]
    for i, piece in enumerate(candidate['pieces']):
        value = F(piece['u1'])
        rc, rs = (1-value*value)/(1+value*value), 2*value/(1+value*value)
        co, si = co*rc-si*rs, si*rc+co*rs
        angle += 2 * math.atan(float(value))
        shift = math.floor((angle+math.pi/2)/math.pi)
        sign = 1 if shift % 2 == 0 else -1
        u = sign*si/(1+sign*co)
        if not -1 <= u <= 1:
            raise AssertionError('angle display chose an invalid exact chart')
        records.append({'piece': i, 'lambda': 2*shift+u, 'angle_radians_diagnostic': angle})
    return min(row['lambda'] for row in records), max(row['lambda'] for row in records), records


def sample_intervals(lower, upper, divisions):
    if lower == upper:
        raise ValueError('escape path has no rotation range')
    knots = {lower+(upper-lower)*F(i, divisions) for i in range(divisions+1)}
    first = int(lower//2)-2
    last = int(upper//2)+3
    knots.update(F(2*i+1) for i in range(first, last) if lower < 2*i+1 < upper)
    knots = sorted(knots)
    return tuple(zip(knots, knots[1:]))


def required_rho_squared(radius, lower, upper):
    """V1's minimum sufficient contraction bound, not necessary geometric loss."""
    lo, hi, unused = proposer._chart(lower, upper)
    middle = (lo+hi)/2
    return max(4*radius*radius*(u-middle)**2/((1+u*u)*(1+middle*middle)) for u in (lo, hi))


def _exact_polygons(parts, center, value, lo, hi):
    return tuple(proposer._world(proposer._rotate(proposer._local(part, center), value, lo, hi), center)
                 for part in parts)


def slice_barrier(parts, obstacles, center, value, lo, hi, resources):
    polygons = _exact_polygons(parts, center, value, lo, hi)
    cells = proposer._cells(polygons, obstacles, resources, float('inf'))
    loop = proposer._barrier(tuple(cell[0] for cell in cells))
    if not loop:
        return {'status': 'NO_CANDIDATE_WINDING_LOOP', 'lambda': value}, None
    for refinement in range(resources.max_refinements+1):
        if len(loop) > resources.max_loop_vertices:
            return {'status': 'LOOP_RESOURCE_LIMIT', 'lambda': value, 'vertices': len(loop)}, None
        row = proposer._loop_witnesses(loop, cells)
        if row is not None and _winding(loop) not in (None, 0):
            return {'status': 'STRICT_WINDING_BARRIER_AT_SINGLE_ANGLE', 'lambda': value,
                    'loop': loop, 'witnesses': row, 'winding': _winding(loop),
                    'vertices': len(loop), 'refinements': refinement}, (loop, row)
        loop = proposer._refine_loop(loop)
    return {'status': 'STRICT_WITNESS_OR_WINDING_UNPROVED', 'lambda': value}, None


def erode_rotated(ring, rho):
    """Exact rational conservative Euclidean erosion, same norm bound as proposer."""
    polygon = ring
    for a, b in proposer._edges(ring):
        normal = (b[1]-a[1], a[0]-b[0])
        bound = _dot(normal, a)-rho*proposer._sqrt_rational(_dot(normal, normal), upper=True)
        polygon = proposer._clip(polygon, normal[0], normal[1], bound)
        if len(polygon) < 3:
            return ()
    return polygon


def strict_pair(moving, obstacle, points):
    """Exact all-axis/all-point predicate; never use diagnostic float ranking."""
    for ring in (moving, obstacle):
        for a, b in proposer._edges(ring):
            normal = (b[1]-a[1], a[0]-b[0])
            if normal == (0, 0):
                raise ValueError('zero axis')
            m = tuple(_dot(normal, p) for p in moving)
            o = tuple(_dot(normal, p) for p in obstacle)
            for point in points:
                shift = _dot(normal, point)
                if max(m)+shift <= min(o) or max(o) <= min(m)+shift:
                    return False
    return True


def fixed_witness_margin(polygons, obstacles, loop, witnesses, radius, iterations):
    """Bracket maximum rho preserving this fixed loop and original piece pairs."""
    def feasible(rho):
        contracted = tuple(erode_rotated(ring, rho) for ring in polygons)
        for index, (i, j) in enumerate(witnesses):
            if not contracted[i]:
                return False
            if not strict_pair(contracted[i], obstacles[j]['ring'], loop[index:index+2]):
                return False
        return True
    if not feasible(F(0)):
        raise AssertionError('rho zero fixed witnesses must pass')
    low, high = F(0), 2*radius
    if feasible(high):
        return {'status': 'SINGLE_SIDED_SEARCH_LIMIT', 'successful_rho': high,
                'failed_rho': None, 'iterations': 0,
                'definition': 'fixed loop and witnesses remain strict at search ceiling; no failed upper bound or maximum claimed'}
    for unused in range(iterations):
        middle = (low+high)/2
        if feasible(middle):
            low = middle
        else:
            high = middle
    norm_ratio_max = 1.0
    for ring in polygons:
        for a, b in proposer._edges(ring):
            normal = (b[1]-a[1], a[0]-b[0])
            norm2 = _dot(normal, normal)
            norm_ratio_max = max(norm_ratio_max, float(proposer._sqrt_rational(norm2, upper=True))/math.sqrt(float(norm2)))
    return {'status': 'BRACKETED_FIXED_WITNESS_MARGIN', 'successful_rho': low,
            'failed_rho': high, 'failed_upper_checked': not feasible(high), 'iterations': iterations,
            'norm_upper_relative_factor_max_diagnostic': norm_ratio_max,
            'definition': 'fixed loop, fixed piece-pair witnesses; uniform rho times rational upper Euclidean edge norm; strict all-endpoint SAT; conservative relative to exact Euclidean erosion'}


def diagnose_slices(instance, center, candidate, resources, divisions, iterations, traced):
    parts = proposer._partition(instance['moving'])
    obstacles = tuple({'obstacle': j, 'ring': part} for j, ring in enumerate(instance['obstacles'])
                      for part in proposer._partition(ring))
    radius = proposer._sqrt_rational(max(proposer._norm2(p) for part in parts for p in proposer._local(part, center)), upper=True)
    lower, upper, endpoints = rotation_range(candidate)
    uniform_intervals = sample_intervals(lower, upper, divisions)
    observed = set()
    for failure in traced['last_failure_per_stage']:
        interval = failure['context'].get('lambda_interval')
        if interval is not None:
            observed.add(tuple(interval))
    intervals = tuple(dict.fromkeys((*uniform_intervals, *sorted(observed))))
    samples = {}
    for lo, hi in intervals:
        for value in (lo, (lo+hi)/2, hi):
            if value not in samples:
                samples[value] = slice_barrier(parts, obstacles, center, value, lo, hi, resources)
    measured = []
    for lo, hi in intervals:
        middle = (lo+hi)/2
        row, barrier = samples[middle]
        entry = {'lambda_interval': (lo, hi), 'midpoint': middle, 'rho_zero_status': row['status'],
                 'sample_origin': 'escape_angle_range_grid' if (lo, hi) in uniform_intervals else 'observed_proposal_failure_interval'}
        if barrier is not None:
            polygons = _exact_polygons(parts, center, middle, lo, hi)
            margin = fixed_witness_margin(polygons, obstacles, barrier[0], barrier[1], radius, iterations)
            entry['fixed_witness_margin'] = margin
            ratios = []
            for factor in (1, 2, 4):
                half = (hi-lo)/(2*factor)
                required_squared = required_rho_squared(radius, middle-half, middle+half)
                required = math.sqrt(float(required_squared))
                ratio_low = required/float(margin['failed_rho']) if margin['failed_rho'] is not None else None
                ratio_high = required/float(margin['successful_rho']) if margin['successful_rho'] > 0 else None
                ratios.append({'interval_refinement': factor, 'v1_min_sufficient_rho_squared_exact': required_squared,
                               'v1_min_sufficient_rho_diagnostic': required,
                               'rho_required_over_margin_lower_diagnostic': ratio_low,
                               'rho_required_over_margin_upper_diagnostic': ratio_high,
                               'ratio_upper_unbounded_by_zero_lower_margin': margin['successful_rho'] == 0})
            entry['contraction_ratios'] = ratios
        measured.append(entry)
    return {'source': '诊断', 'angle_range_lambda': (lower, upper), 'path_orientation_endpoints': endpoints,
            'path_delta': candidate['geometry']['delta'], 'radius': radius, 'center': center,
            'sampling': 'range split into rational lambda grid; all chart boundaries split; endpoints and midpoints only',
            'samples': [samples[value][0] for value in sorted(samples)], 'intervals': measured,
            'all_sampled_angles_have_strict_barrier': all(row[0]['status'] == 'STRICT_WINDING_BARRIER_AT_SINGLE_ANGLE' for row in samples.values()),
            'nonclaim': 'finite rho=0 slices do not cover continuous angles, connect barriers or cap either end; not a cage certificate or non-escape proof',
            'ratio_interpretation': 'ratio>1 only means this fixed loop/piece-pair witness set loses margin under this conservative contraction construction, not global failure of the lemma; ratio<=1 only concerns local V2/V4, not links or caps; strict capacity boundary is not counted accepted'}


def measure_case(case_id, delta, candidate, output, resources, divisions, iterations):
    started = time.perf_counter()
    instance, center = proposer.scientific_instance(case_id, delta)
    proposer.write_json(output/'instance.json', instance)
    with ProposalTrace() as trace:
        proposal = proposer.propose_cage(instance, center=center, resources=resources)
    traced = trace.report()
    proposer.write_json(output/'proposal_trace.json', traced)
    proposer.write_json(output/'proposal.json', {k: v for k, v in proposal.items() if k != 'certificate'})
    if proposal['certificate'] is not None:
        proposer.write_json(output/'instance.json', instance)
        proposer.write_json(output/'certificate.json', proposal['certificate'])
        import t2b_independent_cage_verifier as independent
        result = independent._load_result(output/'instance.json', output/'certificate.json')
        proposer.write_json(output/'independent_verification.json', result)
        if not result['valid']:
            raise RuntimeError('dual verifier mismatch: stop all diagnostics')
    slices = diagnose_slices(instance, center, candidate, resources, divisions, iterations, traced)
    proposer.write_json(output/'slice_diagnostics.json', slices)
    summary = {'source': '诊断', 'case_id': case_id, 'delta': delta, 'proposal_status': proposal['status'],
               'proposal_final_failure': proposal['diagnostic'].get('last_geometric_failure'),
               'last_failure_per_stage': traced['last_failure_per_stage'],
               'slice_samples': len(slices['samples']),
               'strict_slice_barriers': sum(row['status'] == 'STRICT_WINDING_BARRIER_AT_SINGLE_ANGLE' for row in slices['samples']),
               'intervals_with_margin': sum('fixed_witness_margin' in row for row in slices['intervals']),
               'elapsed_seconds': time.perf_counter()-started,
               'outside_scope': 'No claim of maximal margin over all possible barriers; no proof of no barrier from failure.'}
    proposer.write_json(output/'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--science', type=Path, required=True)
    parser.add_argument('--escape-source', type=Path,
                        default=Path('D:/eab-evidence/reports/codex/T2a_evidence/certificates'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=20)
    parser.add_argument('--divisions', type=int, default=8)
    parser.add_argument('--margin-iterations', type=int, default=12)
    parser.add_argument('--case', help='optional single case, for a fresh pilot output')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source_paths = [Path(__file__), Path(proposer.__file__), ROOT/'src/eab/kernel2d/se2_cage.py',
                    ROOT/'tests/t2b_independent_cage_verifier.py', args.science/'summary.json']
    sources = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    proposer.write_json(args.output/'source_manifest.json', sources)
    for i, path in enumerate(source_paths):
        destination = args.output/'source_snapshot'/(str(i)+'_'+path.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
    rows = json.loads((args.science/'summary.json').read_text(encoding='utf-8'))['rows']
    resources = proposer.CageResources(max_seconds=args.seconds, max_intervals=32,
                                       max_loop_vertices=1025, max_cap_steps=128)
    results = []
    for row in rows:
        case_id = row['case_id']
        if args.case is not None and case_id != args.case:
            continue
        candidate_path = args.escape_source/(case_id+'.json')
        candidate = json.loads(candidate_path.read_text(encoding='utf-8'))
        sources[str(candidate_path)] = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        (args.output/'source_snapshot'/(case_id+'_escape_candidate.json')).write_bytes(candidate_path.read_bytes())
        proposer.write_json(args.output/'source_manifest.json', sources)
        deltas = [('first_unproved', F(row['cage_scan']['first_unproved_delta']))]
        if case_id == 'd07':
            lo, hi = F(row['delta_disk']), F(row['delta_escape'])
            deltas.extend(('interior_'+str(i), lo+(hi-lo)*F(i, 5)) for i in range(1, 5))
        for name, delta in deltas:
            print(json.dumps({'start': case_id, 'point': name, 'delta': str(delta)}), flush=True)
            result = measure_case(case_id, delta, candidate, args.output/(case_id+'_'+name), resources,
                                  args.divisions, args.margin_iterations)
            result['point_name'] = name
            result['angle_path_source'] = str(candidate_path)
            result['angle_path_delta'] = candidate['geometry']['delta']
            results.append(result)
            proposer.write_json(args.output/'progress.json', {'complete': False, 'rows': results})
            print(json.dumps({'finish': case_id, 'point': name, 'status': result['proposal_status'],
                              'samples': result['slice_samples'], 'strict': result['strict_slice_barriers'],
                              'seconds': result['elapsed_seconds']}), flush=True)
    unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p, sha in sources.items())
    proposer.write_json(args.output/'summary.json', {'complete': True, 'source': '诊断', 'sources_unchanged': unchanged,
                        'resources': vars(resources), 'divisions': args.divisions,
                        'margin_iterations': args.margin_iterations, 'rows': results})
    if not unchanged:
        raise RuntimeError('diagnostic source changed during run')


if __name__ == '__main__':
    main()
