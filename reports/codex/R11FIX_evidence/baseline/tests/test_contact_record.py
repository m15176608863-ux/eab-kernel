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


# ---------------------------------------------------------------- 审查 C20：canonical_key 的单射性

def _np(v, tri, bi=2, bj=1):
    return {"etype": "np", "bi": bi, "bj": bj, "refs": [[bi, v]] + [[bj, t] for t in tri], "m0init": 1}


def _ee(ea, eb, bi=2, bj=1):
    return {"etype": "ee", "bi": bi, "bj": bj, "refs": [[bi, ea[0]], [bi, ea[1]], [bj, eb[0]], [bj, eb[1]]]}


def test_c20_bdda3d_np_entrances_on_different_triangles_have_distinct_keys():
    """审查复现：同一顶点对同一宿主块的两个不同三角（legacy 面扇形里的两片），旧读取器面下标写死 −1，
    两条记录撞成同一个键。入口 dict 不带面号时，特征身份 = 排序后的顶点三元组。"""
    from eab.readers.bdda3d import record_from_entrance
    r1 = record_from_entrance(_np(0, (4, 7, 6)))
    r2 = record_from_entrance(_np(0, (4, 6, 5)))
    r3 = record_from_entrance(_np(0, (6, 4, 7)))              # 同一三角换序列出
    assert r1.canonical_key() != r2.canonical_key()
    assert r1.canonical_key() == r3.canonical_key()
    assert r1.feature_b.verts == (4, 6, 7)


def test_c20_bdda3d_ee_entrances_key_on_both_edge_endpoints():
    from eab.readers.bdda3d import record_from_entrance
    k = [record_from_entrance(_ee(ea, eb)).canonical_key()
         for ea, eb in (((0, 1), (4, 5)), ((0, 2), (4, 5)), ((1, 0), (5, 4)), ((0, 1), (4, 6)))]
    assert k[0] != k[1] and k[0] != k[3]          # 另一端点不同 → 不同的棱
    assert k[0] == k[2]                           # 同一条棱换向列出 → 同一个键


def test_c20_feature_vertex_identity_survives_json_and_block_swap():
    r1 = _rec(feature_a=Feature(2, "vertex", 3), feature_b=Feature(1, "face", -1, (4, 6, 7)))
    back = records_from_json(records_to_json([r1]))
    assert back == [r1] and back[0].feature_b.verts == (4, 6, 7)
    r2 = _rec(block_a=1, block_b=2, feature_a=Feature(1, "face", -1, (4, 6, 7)), feature_b=Feature(2, "vertex", 3))
    assert r1.canonical_key() == r2.canonical_key()


def test_c20_validate_rejects_unsorted_feature_verts():
    """verts 是集合身份，必须以排序形式存（否则同一特征两种写法、键不唯一）。"""
    validate(_rec(feature_b=Feature(1, "face", -1, (4, 6, 7))))
    with pytest.raises(ValueError):
        validate(_rec(feature_b=Feature(1, "face", -1, (7, 4, 6))))
