"""Re-run exact decoder removal through real export-tool entry paths."""
from pathlib import Path
import importlib.util
import json
import sys
import traceback

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests"), str(ROOT / "tools")]
import pytest
spec = importlib.util.spec_from_file_location("r14_tool_gates", ROOT / "tests/test_r14_tool_readers.py")
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)
modules = {"g2_geometry":gates.g2_bdda3d, "bb_vertices":gates.bb52_g0, "bb_contacts":gates.bb52_g0,
           "g4_contacts":gates.g4_multistep, "g4_params":gates.g4_multistep,
           "m4_summary":gates.m4_capture_family, "ingest_json":gates.ingest_bdda3d}
for api, module in modules.items():
    folder = Path(__file__).parent / "tmp" / "tool_mutation_inputs" / api
    folder.mkdir(parents=True, exist_ok=True)
    with pytest.MonkeyPatch.context() as mp:
        if api in ("g2_geometry", "ingest_json"):
            mp.setattr(module, "numeric_loads", json.loads)
        else:
            mp.setattr(module, "scalar_rational", lambda v, **kw: float(v))
        try:
            gates.test_r14_tool_physical_literal_cannot_silently_lose_range(api, "1e-400", folder, mp)
        except pytest.fail.Exception as error:
            assert "DID NOT RAISE" in str(error)
            traceback.print_exc(file=sys.stdout)
            print("VERIFIED_RED", api, "target assertion: DID NOT RAISE ConstructionDomainError")
        else:
            raise AssertionError("mutation has no teeth: " + api)
with pytest.MonkeyPatch.context() as mp:
    mp.setattr(gates.ingest_bdda3d, "CHILD", gates.ingest_bdda3d.CHILD.replace("list(map(checked_vertex, v))", "list(map(float, v))"))
    try:
        gates.test_r14_ingest_child_checks_before_vertex_float("1e-400", mp)
    except pytest.fail.Exception as error:
        assert "DID NOT RAISE" in str(error)
        traceback.print_exc(file=sys.stdout)
        print("VERIFIED_RED export_child target assertion: DID NOT RAISE vertex OverflowError")
    else:
        raise AssertionError("mutation has no teeth: export_child")
print("NO_EXTERNAL_PROCESSES_OR_SIBLING_CODE_EXECUTED")
