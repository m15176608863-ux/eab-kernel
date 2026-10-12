"""Read the actual bytes and reject damaged Chinese deliverables."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
for name in ("geom2_precision_findings.json", "geom2_precision_final.md"):
    path = ROOT / "review/notes" / name
    text = path.read_text(encoding="utf8")
    assert "隐式" in text and "出口" in text
    assert "??" not in text
    if name.endswith(".json"):
        assert len(json.loads(text)) == 3
    print(name, "UTF8_OK", "han_count", sum("\u4e00" <= c <= "\u9fff" for c in text))
    print(text[:200])
inventory = (ROOT / "review/notes/tolerance_inventory.json").read_text(encoding="utf8")
assert "??" not in inventory
data = json.loads(inventory)
assert data["total_comparisons"] == 1399
assert data["tolerance_syntax_candidates"] == 161
assert len(data["comparisons"]) == 1399
print("INVENTORY_ENCODING_OK", data["modules"], data["total_comparisons"], data["tolerance_syntax_candidates"])
