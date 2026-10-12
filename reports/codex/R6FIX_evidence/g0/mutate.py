"""Rerunnable internal-path mutations; process-local only, no source overwrite."""
from pathlib import Path
import sys, math
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
import pytest
from eab.kernel2d import g0_oracle as oracle, geom
from eab.kernel3d import g03_surface_oracle as surface

mode=sys.argv[1]
if mode in ('classification2d','exit_midpoint'):
    oracle.overlap=lambda a,b: geom.polygons_overlap(a,b,1e-12)
    selected='test_g6f04_2d_strict_micro_sample_is_checked' if mode=='classification2d' else 'test_g6f05_first_exit_preserves_micro_penetration'
elif mode=='classification3d':
    real=surface.separated_distance
    def band(*args):
        distance=real(*args)
        return None if distance is not None and distance<1e-12 else distance
    surface.separated_distance=band
    selected='test_g6f04_3d_strict_micro_gap_is_checked'
elif mode=='distance_square':
    oracle.sqrt_display=lambda q: math.sqrt(float(q))
    selected='test_g6f05_distance_does_not_underflow_or_overflow_its_square'
else:raise ValueError(mode)
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',str(ROOT/'tests/test_r6fix_g0.py'),'-k',selected,
                              '--basetemp',str(ROOT/'reports/codex/R6FIX_evidence/tmp'/('mutant_'+mode))]))
