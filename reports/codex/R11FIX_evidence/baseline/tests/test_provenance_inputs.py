"""生成型夹具的溯源条目必须记输入哈希与不可复现列（G6 第四轮 #32 / 第五轮复核：此前只改了生成脚本，48 条现存条目没有补记）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def test_every_generated_fixture_records_its_inputs_and_nonreproducible_columns():
    prov = json.loads((ROOT / "fixtures" / "PROVENANCE.json").read_text(encoding="utf-8"))
    gen = [e for e in prov["entries"] if e["source"].startswith("generated:")]
    assert len(gen) >= 48
    for e in gen:
        assert e.get("kernel_sha256"), e["dest"]
        ins = e.get("input_sha256")
        assert isinstance(ins, dict) and len(ins) == 2 and all(len(h) == 64 for h in ins.values()), e["dest"]
        assert any("o3" in x for x in e.get("nonreproducible", [])) and any("wall_clock" in x for x in e["nonreproducible"]), e["dest"]


def test_the_generator_writes_provenance_through_upsert_provenance():
    """与 ingest_fixtures 同一写法（显式 CRLF、按 dest 排序）；不再自己 write_text。"""
    src = (ROOT / "tools" / "run_bdda_kernel.py").read_text(encoding="utf-8")
    assert "upsert_provenance(entries" in src and "prov_path.write_text" not in src
    assert "16 份里 **4 份**" in src
