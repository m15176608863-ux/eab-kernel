"""WO-G6L M4 independent raw-column, alias and monotonic-window probes.

Writes only the audit subdirectory. It does not run a sibling executable.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import replace
from fractions import Fraction as F
import csv
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools'), str(ROOT / 'tests')]
from eab.adapters.bdda2d import Bdda2DWindow, detect_step
from eab.readers import bdda_df
from eab.readers.bdda_geom import BlockGeom, StepGeometry, load_step_geometries
import test_m4_bdda_shadow as gate
import m4_bdda_shadow as shadow


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def identity_audit():
    totals = Counter()
    for case in gate.CASES:
        folder = ROOT / 'fixtures/bdda_df' / case
        contacts = read_csv(folder / 'bdda_debug_contacts.csv')
        geometries = load_step_geometries(folder / 'bdda_debug_verts.csv')
        original = {(int(r['step']), int(r['block']), int(r['vidx'])):
                    (F(float(r['x'])), F(float(r['y'])))
                    for r in read_csv(folder / 'bdda_debug_verts.csv')}
        by_id = {(s, v): (b, p) for (s, b, v), p in original.items()}
        raw = {(int(r['step']), int(r['contact'])): r for r in contacts}
        assert len(raw) == len(contacts), 'duplicate raw CSV row identity'
        records = bdda_df.load_records(folder)
        assert len(records) == len(contacts), (case, 'record loss')
        for step, sg in geometries.items():
            for v, target in sg.alias.items():
                assert by_id[step, v] == by_id[step, target], (case, step, 'nonidentical alias')
                totals['exact_coordinate_aliases'] += 1
        judgments = {}
        for row in read_csv(folder / 'bdda_debug_df22.csv'):
            key = (int(row['step']), int(row['contact']))
            if key not in judgments or int(row['oc_iter']) >= int(judgments[key]['oc_iter']):
                judgments[key] = row
        for record in records:
            key = (record.step, record.contact_index)
            c, sg = raw[key], geometries[record.step]
            for field, actual in [('p1', record.extra['raw_p1']), ('p2', record.extra['raw_p2']),
                                  ('p3', record.extra['p3']), ('m4', record.extra['m4']),
                                  ('m5', record.extra['m5']), ('m6', record.extra['m6'])]:
                assert actual == int(c[field]), (case, key, field)
                totals['raw_identity_columns_checked'] += 1
            assert record.raw_cover == int(c['mtype'])
            assert record.bond_flag == int(c['m0_0'])
            assert record.raw_mode_init == int(c['m0_2'])
            assert record.lock_position == float(c['o2'])
            assert record.gap_ref == float(c['o3'])
            assert record.slip_ref == (float(c['o4']),)
            assert record.extra['o5_length'] == float(c['o5'])
            totals['raw_other_columns_checked'] += 7
            if key in judgments:
                j = judgments[key]
                assert record.raw_mode == int(j['m0_new'])
                assert record.raw_mode_prev == int(j['m0_prev'])
                assert record.gap == float(j['o3'])
                assert record.shear == (float(j['o4']),)
                totals['last_oc_fields_checked'] += 4
            else:
                assert record.raw_mode is None and record.gap is None and record.shear is None
            # VV oracle: exact coordinate identity, with the corners declared by
            # double-reference intersection, independent of reader helper code.
            if c['mtype'] == '1':
                corners = []
                for triple in [('p1', 'p2', 'p3'), ('m4', 'm5', 'm6')]:
                    corners.append({by_id[record.step, int(c[n])] for n in triple})
                common = corners[0] & corners[1]
                assert len(common) == 2
                actual = {by_id[record.step, record.feature_a.index],
                          by_id[record.step, record.feature_b.index]}
                assert actual == common, (case, key, 'VV coordinates mismatch')
                totals['vv_exact_coordinate_pairs_checked'] += 1
        totals['contacts'] += len(contacts)
    return dict(totals)


def classification_audit():
    counts, frames = Counter(), 0
    for case in gate.CASES:
        rows = gate._gate_case(case)
        for row in rows:
            common = row['counts'].get('MATCH', 0) + row['counts'].get('VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL', 0)
            assert sum(row['counts'].values()) == row['legacy'] + row['eab'] - common
            assert row['legacy'] - row['legacy_unique'] == row['counts'].get('LEGACY_DUPLICATE_PRIMARY_REFERENCE', 0)
            counts.update(row['counts'])
            frames += 1
    for unclassified in ['UNCLASSIFIED_NEW', 'ARBITRARY_ESCAPE_HATCH', '']:
        try:
            shadow.assert_classified([dict(step=1, counts={unclassified: 1})])
        except AssertionError:
            pass
        else:
            raise AssertionError('closed classification accepts unknown name')
    return dict(frames=frames, classifications=dict(counts), unknown_name_probes_rejected=3)


def window_monotonicity():
    rng = random.Random(6201212)
    checked = 0
    for i in range(45):
        scale = F(1, 10**9) if i % 3 == 0 else F(10**3) if i % 3 == 1 else F(1)
        translation = F(10**8) if i % 2 else F(0)
        A = [(F(0), F(0)), (F(2), F(0)), (F(1), F(2))]
        B = [(F(-3), F(-1)), (F(3), F(-1)), (F(3), F(0)), (F(-3), F(0))]
        tangent = F(rng.randrange(-23, 24), 29)
        cosine, sine = (1-tangent*tangent)/(1+tangent*tangent), 2*tangent/(1+tangent*tangent)
        shift = (F(rng.randrange(-20, 21), 11), F(rng.randrange(-20, 21), 13))
        def transform(poly, offset=(0, 0)):
            return [(scale*(cosine*(x+offset[0])-sine*(y+offset[1]))+translation,
                     scale*(sine*(x+offset[0])+cosine*(y+offset[1]))-translation) for x,y in poly]
        sg = StepGeometry(1, {
            1: BlockGeom(1, transform(A, shift), [10,11,12], False),
            2: BlockGeom(2, transform(B), [20,21,22,23], False),
        })
        keys = lambda w: {r.canonical_key() for r in detect_step(sg, w)}
        previous = set()
        for h1 in (0, 3, 10, 45, 89):
            current = keys(Bdda2DWindow(1, 5*scale, h1, seg_tol=scale/F(10**9)))
            assert previous <= current, (i, 'angle window narrowed eligible set', h1)
            previous = current
            checked += 1
        previous = set()
        for distance in (0, F(1, 16), F(1, 8), F(1), F(5)):
            current = keys(Bdda2DWindow(1, distance*scale, 3, seg_tol=scale/F(10**9)))
            assert previous <= current, (i, 'distance window narrowed eligible set', distance)
            previous = current
            checked += 1
    return dict(membership_comparisons=checked, scales=['1e-9','1','1e3'], translations=['0','1e8'], mismatches=0)


if __name__ == '__main__':
    result = dict(identity=identity_audit(), classification=classification_audit(), window=window_monotonicity())
    out = ROOT / 'review/m4/deep_probe.json'
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
