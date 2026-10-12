"""Restore actual HEAD function bodies in-process; never edit production files."""
import ast
from pathlib import Path
import sys
import zipfile

root = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(root/'src'), str(root/'tests')]
import eab.limit as limit
import pytest

name = sys.argv[1]
source = zipfile.ZipFile(Path(__file__).with_name('baseline_HEAD_30ee153.zip')).read('src/eab/limit.py').decode('utf-8')
node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name)
exec(compile(ast.Module(body=[node], type_ignores=[]), '<HEAD internal '+name+'>', 'exec'), vars(limit))
targets = {
    'wrench': 'test_wrench_cancels_overflowing_products_before_final_rounding',
    '_shift_wrench': 'test_shift_wrench_uses_same_final_rounding_contract',
    '_twist_back': 'test_twist_transform_cancels_overflow_before_constructing_velocity[_twist_back]',
    '_twist_forward': 'test_twist_transform_cancels_overflow_before_constructing_velocity[_twist_forward]',
    'mechanism_power': 'test_mechanism_power_cancels_products_before_rounding',
    'contacts_from_covers': 'test_contact_midpoint_cancels_range_before_rounding',
}
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider', 'tests/test_r8fix_wrench.py::'+targets[name],
                             '--basetemp=reports/codex/R8FIX_evidence/tmp/mutant'+name]))
