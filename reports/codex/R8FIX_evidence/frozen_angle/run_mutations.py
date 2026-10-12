"""Process-local internal mutations; never alter production files on disk."""
from pathlib import Path
from fractions import Fraction as F
import ast
import sys
import pytest
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tests")]
from eab.dual import Dual
import eab.kernel3d.frozen as frozen
import eab.kernel3d.geom3 as geom

case=sys.argv[1]
with pytest.MonkeyPatch.context() as patch:
    if case=="rounded_raw":
        original=frozen._frozen_raw_normal
        def mutate(*args,**kwargs):
            raw,derivatives=original(*args,**kwargs)
            display=frozen._unit_jet(raw,derivatives)
            return (tuple(F(c.v if isinstance(c,Dual) else c) for c in display),
                    [tuple(F(c.e[k]) for c in display) for k in range(len(derivatives))])
        patch.setattr(frozen,"_frozen_raw_normal",mutate)
        target="tests/test_r8fix_frozen.py"
        selection="do_not_reinterpret_rounded_normals or lift_plain_and_dual"
    elif case=="old_dihedral":
        source=Path(__file__).with_name("geom3_before.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        method=next(x for node in tree.body if isinstance(node,ast.ClassDef) and node.name=="Polyhedron"
                    for x in node.body if isinstance(x,ast.FunctionDef) and x.name=="dihedral_turn")
        namespace=dict(vars(geom))
        exec(compile(ast.Module(body=[method],type_ignores=[]),"BASELINE/geom3.py","exec"),namespace)
        patch.setattr(geom.Polyhedron,"dihedral_turn",namespace["dihedral_turn"])
        target="tests/test_r8fix_dihedral.py"
        selection="preserves_exact_thin"
    elif case=="postround_margin":
        original=frozen._normalized_difference
        def mutate(c,nn,offset):
            return original(c,nn,0)-float(offset)
        patch.setattr(frozen,"_normalized_difference",mutate)
        target="tests/test_r8fix_frozen.py"
        selection="rounds_after_subtracting"
    elif case=="postround_contact":
        import eab.margin as margin
        from eab.construction import sqrt_rational
        def mutate(c,nn,offset,**kwargs):
            root=sqrt_rational(c*c/nn,allow_underflow=True)
            return (-root if c<0 else root)-float(offset)
        patch.setattr(margin,"_normalized_difference",mutate)
        target="tests/test_r8fix_frozen.py"
        selection="contact_difference"
    else:
        raise ValueError(case)
    code=pytest.main(["-q","-p","no:cacheprovider",target,"-k",selection,
                      "--basetemp="+str(ROOT/"reports/codex/R8FIX_evidence/tmp"/case)])
    print("INTERNAL_MUTATION",case,"pytest_exit",code)
    if code!=1:
        raise RuntimeError("mutation did not fail the target gate")
