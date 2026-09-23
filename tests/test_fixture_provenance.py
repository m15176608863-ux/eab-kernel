"""夹具溯源门：fixtures/ 下每个入库文件的 sha256 必须与 PROVENANCE.json 一致。

这道门抓的是"夹具被静默改动"——换行符转换、编辑器重排、误覆盖——任何一个字节变了就红。
"""

import hashlib
import json
from pathlib import Path

import pytest

FIX = Path(__file__).resolve().parents[1] / "fixtures"
PROV = FIX / "PROVENANCE.json"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _entries():
    if not PROV.exists():
        return []
    return [e for e in json.loads(PROV.read_text(encoding="utf-8"))["entries"] if e.get("status") == "ok"]


def _check(entry, root: Path = FIX):
    p = root / entry["dest"]
    assert p.exists(), f"fixture missing: {entry['dest']}"
    assert p.stat().st_size == entry["bytes"]
    assert _sha256(p) == entry["sha256"], f"fixture bytes changed: {entry['dest']}"


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["dest"])
def test_fixture_bytes_match_provenance(entry):
    _check(entry)


def test_provenance_is_not_empty():
    assert len(_entries()) >= 10


def _fixture_files():
    return sorted(p.relative_to(FIX).as_posix() for p in FIX.rglob("*")
                  if p.is_file() and p != PROV and "__pycache__" not in p.parts)


def test_every_fixture_file_is_hash_gated():
    """反向完备：fixtures/ 下每个入库文件都必须在 PROVENANCE.json 里有 ok 条目（审查盲区 3：
    bdda3d 的三个 JSON 曾经零条目——G2 的 legacy 侧整个没有被看护，改一个字节也不会红）。"""
    gated = {e["dest"] for e in _entries()}
    missing = [f for f in _fixture_files() if f not in gated]
    assert missing == [], missing


def test_bdda3d_provenance_states_what_is_and_is_not_known():
    """bdda3d 条目必须写明来源工具，并如实写明姊妹仓库版本未记录（不许冒充已溯源）。"""
    ents = [e for e in _entries() if e["dest"].startswith("bdda3d/")]
    assert len(ents) == 3
    for e in ents:
        assert "tools/ingest_bdda3d.py" in e["source"]
        assert "版本未记录" in e["source"]


def test_bdda3d_gate_has_teeth(tmp_path):
    """门要有牙：bdda3d 夹具改一个字节（同长度），同一个判据必须红。"""
    e = next(e for e in _entries() if e["dest"] == "bdda3d/cb2_locked.json")
    q = tmp_path / e["dest"]
    q.parent.mkdir(parents=True)
    b = bytearray((FIX / e["dest"]).read_bytes())
    i = b.index(b'"nsign": 1.0')
    b[i + len(b'"nsign": ')] = ord("2")                       # nsign 1.0 -> 2.0
    q.write_bytes(bytes(b))
    _check(e, FIX)
    with pytest.raises(AssertionError, match="fixture bytes changed"):
        _check(e, tmp_path)


def test_provenance_writer_matches_gate_and_is_byte_stable(tmp_path):
    """登记工具（tools/ingest_fixtures.py）与门用各自的 sha256 实现，结果必须一致；
    无改动重写 PROVENANCE.json 逐字节不变（CRLF 显式化之后跨平台也成立）。"""
    import sys
    sys.path.insert(0, str(FIX.parent / "tools"))
    from ingest_fixtures import provenance_entry, upsert_provenance
    for e in _entries():
        if e["dest"].startswith("bdda3d/"):
            w = provenance_entry(e["dest"], e["source"], e["ingested"])
            assert (w["bytes"], w["sha256"]) == (e["bytes"], e["sha256"])
    q = tmp_path / "PROVENANCE.json"
    q.write_bytes(PROV.read_bytes())
    upsert_provenance([], q)
    assert q.read_bytes() == PROV.read_bytes()
