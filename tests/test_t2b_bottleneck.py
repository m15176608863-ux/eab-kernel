"""Diagnostic boundaries: fixed witnesses and finite slices are not cage claims."""
from fractions import Fraction as F

from t2b_bottleneck_diagnostics import (
    ProposalTrace, fixed_witness_margin, pair_margin, required_rho_squared,
    rotation_range, sample_intervals, strict_pair,
)
import t2b_cage_proposer as proposer
from t2b_cage_fixtures import capped_certificate


def _square(radius):
    return ((-radius, -radius), (radius, -radius), (radius, radius), (-radius, radius))


def test_diagnostic_fixed_witness_margin_has_checked_failed_upper():
    moving = _square(F(2))
    obstacle = {'obstacle': 0, 'ring': _square(F(1))}
    loop = ((F(2), F(0)), (F(2), F(0)))
    result = fixed_witness_margin((moving,), (obstacle,), loop, ((0, 0),), F(3), 8)
    assert result['status'] == 'BRACKETED_FIXED_WITNESS_MARGIN'
    assert result['failed_upper_checked']
    assert result['successful_rho'] < 1 <= result['failed_rho']
    assert result['failed_rho'] - result['successful_rho'] == F(6, 256)


def test_diagnostic_margin_search_ceiling_is_one_sided_not_fake_maximum():
    moving = _square(F(2))
    obstacle = {'obstacle': 0, 'ring': _square(F(1))}
    loop = ((F(0), F(0)), (F(0), F(0)))
    result = fixed_witness_margin((moving,), (obstacle,), loop, ((0, 0),), F(1, 100), 8)
    assert result['status'] == 'SINGLE_SIDED_SEARCH_LIMIT'
    assert result['successful_rho'] == F(1, 50)
    assert result['failed_rho'] is None


def test_diagnostic_sat_contact_is_not_strict_and_features_are_recomputable():
    moving, obstacle = _square(F(1)), _square(F(1))
    points = ((F(2), F(0)),)
    assert not strict_pair(moving, obstacle, points)
    measure = pair_margin(moving, obstacle, points)
    assert measure['exact_overlap_numerator'] == 0
    assert measure['normal_squared'] == 4
    assert measure['feature_type'] == 'edge-edge'
    assert len(measure['moving_support_vertices']) == 2
    assert len(measure['obstacle_support_vertices']) == 2


def test_diagnostic_refinement_lowers_rho_requirement_not_a_whole_angle_claim():
    broad = required_rho_squared(F(2), F(-1, 4), F(1, 4))
    narrow = required_rho_squared(F(2), F(-1, 8), F(1, 8))
    assert 0 < narrow < broad
    intervals = sample_intervals(F(0), F(2), 3)
    assert any(hi == 1 for lo, hi in intervals)
    assert any(lo == 1 for lo, hi in intervals)
    assert all(not lo < 1 < hi for lo, hi in intervals)


def test_trace_connection_angle_is_not_overwritten_by_outer_cap_endpoint():
    """Execute the real nested helper stack that exposed the trace-only defect."""
    base = capped_certificate()
    base['moving_pieces'] = tuple(tuple(tuple(p) for p in ring) for ring in base['moving_pieces'])
    base['obstacle_pieces'] = tuple({'obstacle': p['obstacle'], 'ring': tuple(tuple(v) for v in p['ring'])}
                                    for p in base['obstacle_pieces'])
    resources = proposer.CageResources(max_refinements=0, max_loop_vertices=100, max_cap_steps=8)
    knots = (F(-1, 10), F(0), F(1, 10))
    with ProposalTrace() as trace:
        candidate, unused = proposer._capped_candidate(base, F(1, 10), 2, resources,
                                                       float('inf'), knots=knots, individual_only=True)
    assert candidate is not None
    contexts = [entry[-1] for entry in trace.cell_meta.values() if 'at' in entry[-1]]
    assert len(contexts) == 1
    assert contexts[0]['at'] == 1
    assert contexts[0]['lambda_value'] == knots[1] == 0
    assert contexts[0]['lambda_interval'] == knots[:2]
    assert 'cap_at' not in contexts[0]


def test_rotation_range_composes_two_turns_and_reversal_exactly():
    candidate = {'pieces': [{'u1': '1/10'}, {'u1': '1/5'}, {'u1': '-1/5'}]}
    low, high, endpoints = rotation_range(candidate)
    assert [p['lambda'] for p in endpoints] == [0, F(1, 10), F(15, 49), F(1, 10)]
    assert low == 0 and high == F(15, 49)
