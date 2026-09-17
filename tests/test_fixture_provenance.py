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


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["dest"])
def test_fixture_bytes_match_provenance(entry):
    p = FIX / entry["dest"]
    assert p.exists(), f"fixture missing: {entry['dest']}"
    assert p.stat().st_size == entry["bytes"]
    assert _sha256(p) == entry["sha256"], f"fixture bytes changed: {entry['dest']}"


def test_provenance_is_not_empty():
    assert len(_entries()) >= 10
