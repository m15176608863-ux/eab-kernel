"""Remove exact_surface inside actual public cone function bodies, in memory."""
import sys, inspect, textwrap
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
import pytest
from eab.kernel3d import covers3 as C
for name in ('edge_arc_contains','vertex_cone_contains','cone_constraints'):
    source=textwrap.dedent(inspect.getsource(getattr(C,name)))
    source=source.replace('geom3.exact_surface(P)','P').replace('geom3.exact_surface(A)','A').replace('geom3.exact_surface(B)','B')
    namespace=dict(vars(C))
    exec(compile(source,'<r9-solid-cone-source-mutant>','exec'),namespace)
    setattr(C,name,namespace[name])
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','tests/test_r9fix_solid_cones.py',
    '-k','not rejects_internal','--basetemp=reports/codex/R9FIX_evidence/tmp/geom2/solid_mutant']))
