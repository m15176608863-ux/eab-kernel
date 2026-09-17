import json
import math

import pytest

from eab import ContactRecord, CoverType, Feature, Mode, records_from_json, records_to_json, validate


def _rec(**kw):
    base = dict(source="eab", step=1, contact_index=0, block_a=2, block_b=1, cover=CoverType.VF,
                feature_a=Feature(2, "vertex", 3), feature_b=Feature(1, "face", 0),
                ref_points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
                normal=(0.0, 0.0, 1.0), length_or_area=0.5, params=(0.25, 0.25),
                mode=Mode.LOCKED, raw_mode=2, gap=-1e-6, shear=(0.0, 0.0, 0.0),
                mode_init=Mode.SLIDING, raw_mode_init=1, gap_ref=0.0, slip_ref=(0.0, 0.0, 0.0),
                bond_flag=0, extra={"note": "x", "s": [1.0, 2.0]})
    base.update(kw)
    return ContactRecord(**base)


def test_roundtrip_json_identity():
    r = _rec()
    text = records_to_json([r])
    back = records_from_json(text)
    assert back == [r]
    # 二次序列化逐字节相同（确定性）
    assert records_to_json(back) == text


def test_canonical_key_is_block_order_invariant():
    r1 = _rec(block_a=2, block_b=1, feature_a=Feature(2, "vertex", 3), feature_b=Feature(1, "face", 0))
    r2 = _rec(block_a=1, block_b=2, feature_a=Feature(1, "face", 0), feature_b=Feature(2, "vertex", 3))
    assert r1.canonical_key() == r2.canonical_key()


def test_validate_rejects_nonfinite_and_bad_kind():
    validate(_rec())
    with pytest.raises(ValueError):
        validate(_rec(gap=math.nan))
    with pytest.raises(ValueError):
        validate(_rec(feature_a=Feature(2, "corner", 1)))
    with pytest.raises(ValueError):
        validate(_rec(block_a=-1))


def test_raw_codes_survive_even_when_mode_vocabulary_collides():
    # 三家的 "3" 含义不同；统一词汇不同，raw 保留。
    from eab import BDDA_MODE, BDDA3D_MODE, TF_MODE
    assert BDDA_MODE[3] is Mode.VV_CLOSED
    assert BDDA3D_MODE[3] is Mode.BONDED
    assert TF_MODE[3] is Mode.TENSION
    r = _rec(mode=TF_MODE[3], raw_mode=3)
    d = json.loads(records_to_json([r]))[0]
    assert d["mode"] == "TENSION" and d["raw_mode"] == 3
