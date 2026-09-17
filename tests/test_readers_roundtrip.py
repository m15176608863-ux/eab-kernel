"""读取器门：对入库夹具 (1) 解析非空 (2) 两次解析逐字节同一 (3) JSON 往返恒等 (4) 契约校验全过。

夹具缺失时 skip（夹具由 tools/ingest_fixtures.py / tools/ingest_bdda3d.py 生成）。
"""

from pathlib import Path

import pytest

from eab import records_from_json, records_to_json, validate
from eab.readers import bdda3d, bdda_df, tf_probe

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def _gate(records, parse_again):
    assert len(records) > 0
    text = records_to_json(records)
    assert records_to_json(parse_again()) == text          # 确定性
    assert records_from_json(text) == records              # 往返恒等
    for r in records:
        validate(r)
    keys = [r.canonical_key() for r in records]
    assert len(keys) == len(records)
    return text


@pytest.mark.parametrize("case_dir", sorted((FIX / "bdda_df").glob("*")) if (FIX / "bdda_df").exists() else [])
def test_bdda_df_fixture(case_dir):
    recs = bdda_df.load_records(case_dir)
    _gate(recs, lambda: bdda_df.load_records(case_dir))
    # 主表每步每接触一行 → (step, contact) 唯一
    assert len({(r.step, r.contact_index) for r in recs}) == len(recs)
    # 块号全部可解析（verts.csv 在时靠顶点号补全），且 verts 与 df18 两路块号零冲突
    if (case_dir / "bdda_debug_verts.csv").exists():
        assert not any(r.extra.get("_blocks_unknown") for r in recs)
    assert not any(r.extra.get("_block_mismatch") for r in recs)


@pytest.mark.parametrize("probe", sorted((FIX / "tf").glob("*/retry_contact_pair_probe.tsv")) if (FIX / "tf").exists() else [])
def test_tf_probe_fixture(probe):
    recs = tf_probe.load_records(probe)
    _gate(recs, lambda: tf_probe.load_records(probe))
    assert all(r.cover.value in ("VF", "EE", "NN", "NE") for r in recs)


@pytest.mark.parametrize("stage", sorted((FIX / "tf").glob("*/contact_pair_stage.tsv")) if (FIX / "tf").exists() else [])
def test_tf_pair_stage_fixture(stage):
    rows = tf_probe.read_pair_stage(stage)
    assert rows
    for r in rows:
        assert r.total_contacts == r.nn_count + r.ne_count + r.np_count + r.ee_count
        assert r.contact_end - r.contact_start == r.total_contacts


@pytest.mark.parametrize("js", sorted((FIX / "bdda3d").glob("*.json")) if (FIX / "bdda3d").exists() else [])
def test_bdda3d_fixture(js):
    recs = bdda3d.load_records(js)
    _gate(recs, lambda: bdda3d.load_records(js))
    assert all(r.cover.value in ("VF", "EE") for r in recs)
