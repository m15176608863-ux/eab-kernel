"""R13FIXb reader/reference gates with independent Fraction certificates.

Oracle primitives: Python Fraction, binary64 adjacent values, test-owned exact
CSV values, rational shoelace/topology. No production geometry or construction
routine constructs expected values. Every numeric reader field is checked.
"""
import csv
import dataclasses
from fractions import Fraction as F
import inspect
import json
import math
import struct
import sys
import types

import pytest

from eab import oracle_construction as oracle
from eab.adapters import bdda2d as adapter
from eab.numeric_domain import ConstructionDomainError
from eab.readers import bdda3d, bdda_df, bdda_geom, tf_probe


SCALES = [F(2)**-390, F(1), F(2)**390]


def _cell(actual, exact, power=1):
    """Independent rational RN-even cell, including signed scalar values."""
    assert math.isfinite(actual), "finite certificate"
    if exact < 0:
        actual, exact = -actual, -exact
    assert actual >= 0, "sign certificate"
    even = struct.unpack(">Q", struct.pack(">d", actual))[0] % 2 == 0
    middle = F(actual)
    if actual:
        lower = ((F(math.nextafter(actual, 0))+middle)/2)**power
        assert exact > lower or (exact == lower and even), "lower midpoint certificate"
    upper = ((middle+F(math.nextafter(actual, math.inf)))/2)**power
    assert exact < upper or (exact == upper and even), "upper midpoint certificate"


def _write(path, row, delimiter=","):
    with path.open("w", encoding="utf8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row), delimiter=delimiter)
        writer.writeheader()
        writer.writerow(row)
    return path


def _text(q):
    # Exact finite decimal token, not an early binary64 conversion.
    from decimal import Decimal, localcontext
    with localcontext() as ctx:
        ctx.prec = 1600
        return str(Decimal(q.numerator)/Decimal(q.denominator))


@pytest.mark.parametrize("scale", SCALES)
def test_oracle_all_numeric_constructors_have_independent_midpoint_certificates(scale):
    a, b = scale*(F(1)+F(1, 2**54)), scale*F(13, 16)
    _cell(oracle.scalar_exact(a), a)
    _cell(oracle.ratio_exact(a, 3), a/3)
    for actual, exact in zip(oracle.vector_exact([a, -b]), [a, -b]):
        _cell(actual, exact)
    _cell(oracle.sqrt_exact(a), a, 2)
    _cell(oracle.norm_exact([a, b]), a*a+b*b, 2)
    for actual, component in zip(oracle.unit_exact([a, -b]), [a, -b]):
        assert actual*component > 0
        _cell(abs(actual), component*component/(a*a+b*b), 2)


@pytest.mark.parametrize("scale", SCALES)
def test_assert_sqrt_rounding_is_a_checker_not_a_constructor(scale):
    # Powers of two are exact; a wrong adjacent float must fail its own cell.
    actual = float(scale)
    assert oracle.assert_sqrt_rounding(actual, scale*scale) is None
    with pytest.raises(AssertionError, match="midpoint certificate"):
        oracle.assert_sqrt_rounding(math.nextafter(actual, math.inf), scale*scale)


@pytest.mark.parametrize("call", [
    lambda: oracle.scalar_exact(F(2)**1200),
    lambda: oracle.scalar_exact(F(2)**-1200),
    lambda: oracle.ratio_exact(1, 2**1200),
    lambda: oracle.vector_exact([1, F(2)**1200]),
    lambda: oracle.sqrt_exact(F(2)**-2400),
    lambda: oracle.norm_exact([F(2)**1200, 1]),
    lambda: oracle.unit_exact([1, F(2)**-1200]),
])
def test_oracle_unrepresentable_outputs_raise_dedicated_domain_error(call):
    with pytest.raises(ConstructionDomainError, match="oracle construction"):
        call()


@pytest.mark.parametrize("scale", [F(2)**-1074, F(2)**900])
def test_oracle_retains_full_representable_domain(scale):
    assert oracle.scalar_exact(scale) == float(scale)
    assert oracle.norm_exact([scale, 0]) == float(scale)
    assert oracle.unit_exact([scale, scale]) == (math.sqrt(.5), math.sqrt(.5))


def _entrance(scale):
    vals = [float(scale*F(k, 16)) for k in range(1, 16)]
    c = dict(etype="np", bi=2, bj=7, refs=[[2, 0], [7, 0], [7, 1], [7, 2]],
             owner=[0, 1, 1, 1], nsign=-1, t1=vals[0], t2=vals[1], d1=vals[2],
             area=vals[3], fa=vals[4], coh=vals[5], tens=vals[6], m0init=2,
             m0_0=2, o3t=-vals[7], slip_ref=vals[8:11], extra_numeric=vals[11])
    verts = {"2": [vals[0:3]], "7": [vals[3:6], vals[6:9], vals[9:12]]}
    return c, verts


def _check_entrance(rec, c, verts, step, index):
    expected_points = tuple(tuple(verts[str(b)][k]) for b, k in c["refs"])
    assert rec.ref_points == expected_points, "ref_points preservation"
    assert rec.length_or_area == c["area"], "area preservation"
    assert rec.params == (c["t1"], c["t2"]), "params preservation"
    assert rec.gap_ref == c["o3t"], "gap_ref preservation"
    assert rec.slip_ref == tuple(c["slip_ref"]), "slip_ref preservation"
    assert (rec.step, rec.contact_index, rec.block_a, rec.block_b) == (step, index, 2, 7)
    assert dataclasses.asdict(rec.feature_a) == dict(block=2, kind="vertex", index=0, verts=())
    assert dataclasses.asdict(rec.feature_b) == dict(block=7, kind="face", index=-1, verts=(0, 1, 2))
    assert rec.bond_flag == 2 and rec.raw_mode_init == 2 and rec.raw_mode is None
    assert rec.gap is None and rec.normal is None and rec.shear is None
    assert rec.extra == {"extra_numeric": c["extra_numeric"], "owner": c["owner"],
                         "nsign": -1, "d1": c["d1"], "refs": c["refs"],
                         "joint_fa": c["fa"], "joint_coh": c["coh"], "joint_tens": c["tens"]}, "extra preservation"


@pytest.mark.parametrize("scale", SCALES)
def test_bdda3d_both_public_readers_preserve_every_numeric_field(tmp_path, scale):
    c, verts = _entrance(scale)
    _check_entrance(bdda3d.record_from_entrance(c, step=13, index=5, verts=verts), c, verts, 13, 5)
    path = tmp_path/"entrances.json"
    path.write_text(json.dumps(dict(case="synthetic", step=13, verts=verts, entrances=[c])), encoding="utf8")
    rec, = bdda3d.load_records(path)
    assert rec.extra.pop("case") == "synthetic"
    _check_entrance(rec, c, verts, 13, 0)


def _df_files(tmp_path, scale):
    # All values exact dyadic decimal tokens. All 30 df18 coefficients are distinct.
    c = dict(step=13, contact=5, mtype=0, p1=101, p2=203, p3=202,
             m4=11, m5=12, m6=13, m0_0=1, m0_2=2,
             **{k: _text(scale*F(i, 16)) for i, k in enumerate(["o2", "o3", "o4", "o5"], 1)})
    g = dict(step=13, contact=5, jj=7, block_i=2, block_j=7, mtype=0,
             **{k: _text(scale*F(i, 16)) for i, k in enumerate(
                 ["q01", "q02", "b1", "cs1", "cs2", "cs3", "x1", "y1", "x2", "y2", "x3", "y3"], 1)},
             **{f"s{i}": _text(scale*F(i, 32)) for i in range(1, 31)})
    j = dict(step=13, contact=5, oc_iter=3, mtype=0, m0_0=1, m0_prev=1, m0_new=2,
             **{k: _text(-scale*F(i, 16)) for i, k in enumerate(["o3", "o4", "t3", "w0"], 1)})
    for name, row in [("contacts", c), ("df18", g), ("df22", j)]:
        _write(tmp_path/f"bdda_debug_{name}.csv", row)
    return c, g, j


@pytest.mark.parametrize("scale", SCALES)
def test_bdda_df_all_numeric_and_raw_fields_match_independent_rationals(tmp_path, scale):
    c, g, j = _df_files(tmp_path, scale)
    contacts = bdda_df.read_contacts_csv(tmp_path/"bdda_debug_contacts.csv")
    assert contacts == {(13, 5): {k: float(F(v)) for k, v in c.items() if k not in ("step", "contact")}}
    raw_g = bdda_df.read_df18_csv(tmp_path/"bdda_debug_df18.csv")
    assert raw_g == {(13, 5): {**{k: str(v) for k, v in g.items()}, "_df18_rows": "1"}}
    judgments = bdda_df.read_df22_csv(tmp_path/"bdda_debug_df22.csv")
    assert dataclasses.asdict(judgments[0]) == {k: float(F(v)) for k, v in j.items()}
    assert bdda_df.last_oc_judgments(judgments)[13, 5] is judgments[0]
    rec, = bdda_df.load_records(tmp_path)
    assert (rec.step, rec.contact_index, rec.block_a, rec.block_b) == (13, 5, 2, 7)
    assert dataclasses.asdict(rec.feature_a) == dict(block=2, kind="vertex", index=101, verts=())
    assert dataclasses.asdict(rec.feature_b) == dict(block=7, kind="edge", index=202, verts=())
    assert rec.ref_points == tuple((float(F(g[f"x{i}"])), float(F(g[f"y{i}"]))) for i in range(1, 4)), "ref_points preservation"
    assert rec.params == (float(F(g["cs3"])),), "params preservation"
    assert rec.length_or_area == float(F(g["b1"])), "length preservation"
    assert rec.gap == float(F(j["o3"])) and rec.shear == (float(F(j["o4"])),), "state preservation"
    assert rec.gap_ref == float(F(c["o3"])) and rec.slip_ref == (float(F(c["o4"])),), "reference preservation"
    assert rec.lock_position == float(F(c["o2"])), "lock_position preservation"
    assert (rec.raw_mode, rec.raw_mode_prev, rec.raw_mode_init, rec.bond_flag) == (2, 1, 2, 1)
    expected_extra = dict(raw_p1=101, raw_p2=203, p3=202,
                          **{f"c_m{i}": float(c[f"m{i}"]) for i in (4, 5, 6)},
                          **{f"m{i}": float(c[f"m{i}"]) for i in (4, 5, 6)},
                          **{f"df18_{k}": str(g[k]) for k in ("jj", "q01", "q02", "cs1", "cs2")},
                          df18__df18_rows="1", df18_s=[float(F(g[f"s{i}"])) for i in range(1, 31)],
                          df22_oc_iter=3, df22_t3=float(F(j["t3"])), df22_w0=float(F(j["w0"])),
                          df22_m0_0=1, o5_length=float(F(c["o5"])))
    assert rec.extra == expected_extra, "all extra fields preservation"


@pytest.mark.parametrize("scale", SCALES)
def test_geometry_readers_and_identity_accessors_preserve_values(tmp_path, scale):
    poly = [(scale, scale), (scale*4, scale), (scale*2, scale*3)]
    vids = [101, 102, 103, 104]
    kp = poly+[poly[0]]
    kept, points, aliases = bdda_geom.strip_duplicate_vertices(vids, kp, dup_tol=0)
    assert (kept, points, aliases) == ([101, 102, 103], poly, {104: 101})
    path = tmp_path/"verts.csv"
    with path.open("w", encoding="utf8", newline="") as fh:
        fh.write("step,block,vidx,x,y\n")
        for vid, (x, y) in zip(vids, kp):
            fh.write(f"13,2,{vid},{_text(x)},{_text(y)}\n")
    raw = bdda_df.read_verts_csv(path)
    assert raw == {13: {2: {vid: tuple(float(x) for x in p) for vid, p in zip(vids, kp)}}}
    geom = bdda_geom.load_step_geometries(path, dup_tol=0)[13]
    block = geom.blocks[2]
    assert block.poly == [tuple(float(x) for x in p) for p in poly]
    assert block.vidx == [101, 102, 103] and block.flipped is False
    assert geom.canon(104) == 101 and geom.canon(105) == 105
    assert geom.vertex_block() == {101: 2, 102: 2, 103: 2}
    assert geom.vertex_pos() == dict(zip(block.vidx, block.poly))


@pytest.mark.parametrize("scale", SCALES)
def test_duplicate_vertex_branch_compares_exact_raw_differences(scale):
    # (1 - -2^-53) rounds to 1 if the subtraction precedes exact lifting.
    poly = [(scale, 0.), (-scale/F(2**53), 0.), (-scale*3, scale*3), (scale*3, scale*3)]
    # Use binary64 coordinates so the restored raw subtraction really rounds.
    poly = [tuple(float(x) for x in p) for p in poly]
    actual = bdda_geom.strip_duplicate_vertices([1, 2, 3, 4], poly, dup_tol=float(scale))
    assert actual == ([1, 2, 3, 4], poly, {}), "exact duplicate branch"


@pytest.mark.parametrize("scale", SCALES)
def test_tf_both_readers_preserve_all_numeric_fields(tmp_path, scale):
    keys = ["time", "gap", "area", "normal_force", "px", "py", "pz", "nx", "ny", "nz", "shear_dx", "shear_dy", "shear_dz"]
    values = {k: _text(scale*F(i, 16)) for i, k in enumerate(keys, 1)}
    r = dict(step=13, block_a=2, block_b=7, contact_index=5, contact_state=2,
             previous_contact_state=1, contact_entry=9, contact_type=2, **values,
             shear_norm=_text(scale*2), mr=3, event="retry")
    rec, = tf_probe.load_records(_write(tmp_path/"probe.tsv", r, "\t"))
    f = {k: float(F(v)) for k, v in values.items()}
    assert (rec.step, rec.block_a, rec.block_b, rec.contact_index, rec.entrance_index) == (13, 2, 7, 5, 9)
    assert (rec.raw_cover, rec.raw_mode, rec.raw_mode_prev) == (2, 2, 1)
    assert rec.ref_points == ((f["px"], f["py"], f["pz"]),), "ref_points preservation"
    assert rec.normal == (f["nx"], f["ny"], f["nz"]), "normal preservation"
    assert rec.gap == f["gap"] and rec.length_or_area == f["area"] and rec.normal_force == f["normal_force"], "scalar preservation"
    assert rec.shear == (f["shear_dx"], f["shear_dy"], f["shear_dz"]), "shear preservation"
    assert rec.extra == dict(time=f["time"], shear_norm=r["shear_norm"], mr="3", event="retry"), "extra preservation"
    stage = dict(step=13, time=values["time"], block_i=2, block_j=7, contact_start=1, contact_end=8,
                 total_contacts=8, nn_count=1, ne_count=2, np_count=3, ee_count=2, load_bucket="loading")
    got, = tf_probe.read_pair_stage(_write(tmp_path/"stage.tsv", stage, "\t"))
    assert dataclasses.asdict(got) == {**stage, "time": f["time"]}


@pytest.mark.parametrize("scale", SCALES)
def test_adapter_detection_and_window_have_independent_rational_values(tmp_path, scale):
    _write(tmp_path/"bdda_debug_detparams.csv", dict(step=13, d0=_text(scale/8), h1="0", coefficient=_text(scale*3)))
    window = adapter.load_window(tmp_path, 13)
    assert window.d0 == float(scale/8) and window.h1_degrees == 0
    assert window.raw_parameters == {"d0": float(scale/8), "h1": 0., "coefficient": float(scale*3)}
    window = dataclasses.replace(window, seg_tol=0, fit_tol=0)
    tip = [(0, scale/16), (scale, scale*F(17, 16)), (-scale, scale*F(17, 16))]
    slab = [(-scale*3, -scale), (scale*3, -scale), (scale*3, 0), (-scale*3, 0)]
    geom = bdda_geom.StepGeometry(13, {
        2: bdda_geom.BlockGeom(2, tip, [101, 102, 103], False),
        7: bdda_geom.BlockGeom(7, slab, [201, 202, 203, 204], False)})
    rec, = adapter.detect_step(geom, window)
    assert rec.normal == (0., 1.) and rec.gap == float(scale/16), "normal and gap rational reference"
    assert rec.params == (.5,) and rec.length_or_area == float(scale*6), "param and length rational reference"
    assert rec.ref_points == (tip[0], slab[2], slab[3]), "ref_points preservation"
    assert rec.extra["window"] == dict(d0=float(scale/8), h1_degrees=0., cone_sin=0., seg_tol=0, fit_tol=0,
                                       source="detparams", fallback_fields=[])
    assert (rec.contact_index, rec.step, rec.block_a, rec.block_b) == (1, 13, 2, 7)


@pytest.mark.parametrize("bad", ["1e400", "1e-400"])
@pytest.mark.parametrize("reader", ["contacts", "df22", "df18", "verts", "tf_probe", "tf_stage", "bdda3d", "geometry", "window"])
def test_reader_unrepresentable_numeric_fields_raise_quantity_named_error(tmp_path, bad, reader):
    if reader in ("contacts", "df22", "df18"):
        c, g, j = _df_files(tmp_path, F(1))
        name, row, field = {"contacts": ("contacts", c, "o3"), "df22": ("df22", j, "o3"), "df18": ("df18", g, "x1")}[reader]
        row[field] = bad
        path = _write(tmp_path/f"bdda_debug_{name}.csv", row)
        call = (lambda: bdda_df.load_records(tmp_path)) if reader == "df18" else lambda: getattr(bdda_df, f"read_{reader}_csv")(path)
    elif reader in ("verts", "geometry"):
        field = "x"
        path = _write(tmp_path/"verts.csv", dict(step=1, block=1, vidx=1, x=bad, y="0"))
        call = lambda: (bdda_df.read_verts_csv(path) if reader == "verts" else bdda_geom.load_step_geometries(path))
    elif reader in ("tf_probe", "tf_stage"):
        field = "time"
        path = _write(tmp_path/"tf.tsv", dict(time=bad), "\t")
        call = lambda: (tf_probe.load_records(path) if reader == "tf_probe" else tf_probe.read_pair_stage(path))
    elif reader == "bdda3d":
        field = "area"
        call = lambda: bdda3d.record_from_entrance(dict(bi=1, bj=2, area=F(bad)))
    else:
        field = "d0"
        _write(tmp_path/"bdda_debug_detparams.csv", dict(step=1, d0=bad, h1="0"))
        call = lambda: adapter.load_window(tmp_path, 1)
    with pytest.raises(ConstructionDomainError, match=field):
        call()


def _mutate(monkeypatch, module, old, new):
    source = inspect.getsource(module)
    assert source.count(old) == 1
    name = module.__name__+"_r13fixb_mutant"
    mutant = types.ModuleType(name)
    mutant.__package__ = module.__package__
    monkeypatch.setitem(sys.modules, name, mutant)
    exec(compile(source.replace(old, new), module.__file__, "exec"), mutant.__dict__)
    return mutant


def test_oracle_early_rounding_mutation_is_rejected_inside_ratio(monkeypatch):
    mutant = _mutate(monkeypatch, oracle,
                     "return scalar_exact(Fraction(numerator)/Fraction(denominator),",
                     "return scalar_exact(Fraction(float(numerator)/float(denominator)),")
    a, b = F(2**54+1, 2**54), F(3)
    _cell(oracle.ratio_exact(a, b), a/b)
    with pytest.raises(AssertionError, match="midpoint certificate"):
        _cell(mutant.ratio_exact(a, b), a/b)


@pytest.mark.parametrize("scale", SCALES)
def test_oracle_root_near_midpoint_is_not_rounded_before_sqrt(scale):
    midpoint = F(1)+F(1, 2**53)
    squared = (midpoint*midpoint+F(1, 2**120))*scale
    _cell(oracle.sqrt_exact(squared), squared, 2)


def test_oracle_root_early_rounding_mutation_fails_the_rational_cell(monkeypatch):
    mutant = _mutate(monkeypatch, oracle,
                     "return _round_positive(value, 2, allow_underflow)",
                     "return math.sqrt(float(value))")
    midpoint = F(1)+F(1, 2**53)
    squared = midpoint*midpoint+F(1, 2**120)
    with pytest.raises(AssertionError, match="midpoint certificate"):
        _cell(mutant.sqrt_exact(squared), squared, 2)


def test_reader_range_validation_mutation_is_rejected(tmp_path, monkeypatch):
    mutant = _mutate(monkeypatch, tf_probe,
                     'scalar_rational(row[name], quantity=f"{path.name}.{name}")',
                     'float(row[name])  # restored unchecked reader conversion')
    path = _write(tmp_path/"stage.tsv", dict(step=1, time="1e400", block_i=1, block_j=2,
                  contact_start=1, contact_end=1, total_contacts=1, nn_count=0, ne_count=0,
                  np_count=1, ee_count=0, load_bucket="load"), "\t")
    with pytest.raises(ConstructionDomainError, match="time"):
        tf_probe.read_pair_stage(path)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        with pytest.raises(ConstructionDomainError):
            mutant.read_pair_stage(path)


def test_duplicate_branch_early_rounding_mutation_has_the_right_teeth(monkeypatch):
    mutant = _mutate(monkeypatch, bdda_geom,
                     "return (abs(Fraction(p[0]) - Fraction(q[0])) <= Fraction(dup_tol)\n"
                     "                and abs(Fraction(p[1]) - Fraction(q[1])) <= Fraction(dup_tol))",
                     "return abs(p[0]-q[0]) <= dup_tol and abs(p[1]-q[1]) <= dup_tol")
    with monkeypatch.context() as patch:
        patch.setattr(bdda_geom, "strip_duplicate_vertices", mutant.strip_duplicate_vertices)
        with pytest.raises(AssertionError, match="exact duplicate branch"):
            test_duplicate_vertex_branch_compares_exact_raw_differences(F(1))


def _adapter_mixed_coordinate_gate(module):
    t = 2**54
    tip = [(t+2, F(1, 16)), (t+3, F(17, 16)), (t+1, F(17, 16))]
    slab = [(t, -1), (t+5, -1), (t+5, 0), (float(t), 0)]
    geom = bdda_geom.StepGeometry(13, {
        2: bdda_geom.BlockGeom(2, tip, [101, 102, 103], False),
        7: bdda_geom.BlockGeom(7, slab, [201, 202, 203, 204], False)})
    rec, = module.detect_step(geom, adapter.Bdda2DWindow(13, F(1, 8), 0, seg_tol=0, fit_tol=0))
    assert rec.length_or_area == 5., "exact adapter edge length"
    assert rec.params == (.6,) and rec.gap == .0625


def test_adapter_mixed_raw_coordinates_never_round_before_subtracting():
    _adapter_mixed_coordinate_gate(adapter)


def test_adapter_early_rounding_mutation_hits_its_numeric_assertion(monkeypatch):
    mutant = _mutate(monkeypatch, adapter,
                     "norm_rational(Fraction(q[k])-Fraction(p[k]) for k in (0, 1))",
                     "norm_rational(q[k]-p[k] for k in (0, 1))")
    _adapter_mixed_coordinate_gate(adapter)
    with pytest.raises(AssertionError, match="exact adapter edge length"):
        _adapter_mixed_coordinate_gate(mutant)


@pytest.mark.parametrize("angle", [F(2)**-400, F(3), F(89)])
def test_cone_coefficient_has_a_rational_series_gate(angle):
    # Independent rational Taylor sum; a 100-digit pi decimal bounds its
    # absolute argument error below 1e-99, and the next series term bounds the
    # truncation error. This is a platform qualification, not a libm theorem.
    pi = F("3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679")
    x = angle*pi/180
    term = x
    total = x
    for k in range(1, 70):
        term *= -x*x/F((2*k)*(2*k+1))
        total += term
    actual = adapter.Bdda2DWindow(1, 0., angle).cone_tol
    assert abs(F(actual)-total) <= 4*F(math.ulp(actual)), "cone coefficient platform error"
    metadata = adapter.Bdda2DWindow(1, 0., angle).metadata()
    assert metadata == dict(d0=0., h1_degrees=angle, cone_sin=actual,
                            seg_tol=1e-9, fit_tol=1e-6, source="explicit", fallback_fields=[])


@pytest.mark.parametrize("angle", [F(2)**-401, F(2)**-1074])
def test_cone_coefficient_outside_declared_angle_domain_is_loud(angle):
    with pytest.raises(ConstructionDomainError, match="cone_tol.h1_degrees"):
        adapter.Bdda2DWindow(1, 0., angle).cone_tol


def test_cone_coefficient_domain_guard_has_teeth(monkeypatch):
    mutant = _mutate(monkeypatch, adapter,
                     'check_input(self.h1_degrees, "bdda2d.cone_tol.h1_degrees")',
                     'pass  # restored unchecked radians underflow')
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        with pytest.raises(ConstructionDomainError):
            mutant.Bdda2DWindow(1, 0., F(2)**-1074).cone_tol


def test_contact_integer_identity_fields_do_not_pass_through_binary64(tmp_path):
    big = 2**54+1
    row = dict(step=1, contact=1, mtype=0, p1=big, p2=big+1, p3=big+2,
               m4=big+3, m5=big+4, m6=big+5, m0_0=1, m0_2=2)
    actual = bdda_df.read_contacts_csv(_write(tmp_path/"contacts.csv", row))[1, 1]
    assert actual == {k: v for k, v in row.items() if k not in ("step", "contact")}, "exact integer identity"


@pytest.mark.parametrize("scale", [F(2)**-1000, F(2)**900])
def test_readers_do_not_narrow_already_representable_full_domain(tmp_path, scale):
    test_bdda3d_both_public_readers_preserve_every_numeric_field(tmp_path, scale)
    test_bdda_df_all_numeric_and_raw_fields_match_independent_rationals(tmp_path, scale)
    test_tf_both_readers_preserve_all_numeric_fields(tmp_path, scale)


@pytest.mark.parametrize("scale", [F(2)**-1200, F(2)**1200])
def test_nonconstructing_passthrough_and_duplicate_predicate_keep_unbounded_exact_inputs(tmp_path, scale):
    raw = dict(step=1, contact=1, x1=_text(scale))
    data = bdda_df.read_df18_csv(_write(tmp_path/"raw.csv", raw))
    assert data == {(1, 1): {"step": "1", "contact": "1", "x1": _text(scale), "_df18_rows": "1"}}
    poly = [(scale, scale), (scale*4, scale), (scale*2, scale*3)]
    got = bdda_geom.strip_duplicate_vertices([1, 2, 3, 4], poly+[poly[0]], dup_tol=0)
    assert got == ([1, 2, 3], poly, {4: 1})


@pytest.mark.parametrize("scale", [F(2)**-1200, F(2)**1200])
def test_adapter_unrepresentable_record_length_is_a_dedicated_domain_error(scale):
    # Contact is exactly touching, so selection does not need a huge window;
    # only the reported edge length is out of the representable output domain.
    tip = [(0, 0), (scale, scale), (-scale, scale)]
    slab = [(-3*scale, -scale), (3*scale, -scale), (3*scale, 0), (-3*scale, 0)]
    geom = bdda_geom.StepGeometry(1, {
        2: bdda_geom.BlockGeom(2, tip, [101, 102, 103], False),
        7: bdda_geom.BlockGeom(7, slab, [201, 202, 203, 204], False)})
    with pytest.raises(ConstructionDomainError):
        adapter.detect_step(geom, adapter.Bdda2DWindow(1, 0, 0, seg_tol=0, fit_tol=0))
