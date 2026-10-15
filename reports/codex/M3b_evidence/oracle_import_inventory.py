"""Static import catalog; call-level oracle independence is a separate review."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GROUPS = {
    "2d_sut": ["src/eab/kernel2d/global_entrance.py"],
    "2d_oracle": ["src/eab/kernel2d/g0_oracle.py", "src/eab/oracle_construction.py"],
    "3d_sut": ["src/eab/kernel3d/global_entrance.py", "src/eab/kernel3d/boundary.py"],
    "3d_oracle": ["src/eab/kernel3d/geom3.py", "src/eab/kernel3d/exact_geom.py", "src/eab/rational3.py", "src/eab/kernel3d/g03_surface_oracle.py", "src/eab/kernel3d/g03_exit_oracle.py"],
    "shared_scalar_domains_not_geometric_oracles": ["src/eab/construction.py", "src/eab/numeric_domain.py"],
    "gates_with_input_and_oracle_roles": ["tests/test_m3b_2d.py", "tests/test_m3b_construction3d.py", "tests/test_m3b_boundary3d.py", "tests/test_m3b_boundary3d_fields.py"],
    "scans": ["tools/m3b_scan2d.py", "tools/m3b_boundary3d_evidence.py", "tools/m3b_construction3d_evidence.py", "reports/codex/M3b_evidence/gp_boundary_probe.py"],
}

def main():
    rows = []
    for role, paths in GROUPS.items():
        for relative in paths:
            raw = (ROOT/relative).read_bytes()
            tree = ast.parse(raw.decode("utf-8-sig"))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.append(dict(line=node.lineno, kind="import", names=[dict(name=n.name, alias=n.asname) for n in node.names]))
                elif isinstance(node, ast.ImportFrom):
                    imports.append(dict(line=node.lineno, kind="from", module="."*node.level+(node.module or ""), names=[dict(name=n.name, alias=n.asname) for n in node.names]))
            rows.append(dict(role=role, path=relative, existing_utf8_bom=raw.startswith(bytes.fromhex("efbbbf")), sha256=hashlib.sha256(raw).hexdigest(), imports=sorted(imports, key=lambda x:x["line"])))
    result = dict(schema="eab.m3b-oracle-import-catalog.v1", files=rows,
                  limitations=["Direct AST imports, including nested and conditional imports; not a dynamic import trace or complete transitive closure.",
                               "A test imports both SUT and input builders. Its expected-value independence is established by the gate docstring and reviewed call path, not by import disjointness alone."])
    output = ROOT/"reports/codex/M3b_evidence/oracle_import_inventory.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(len(rows), "files catalogued")

if __name__ == "__main__":
    main()
