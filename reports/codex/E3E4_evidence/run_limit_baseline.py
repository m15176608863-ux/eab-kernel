"""Compile saved e1fbbd4 limit sources in a private process and run a repro with real assertions."""
from pathlib import Path
import sys,types,runpy,eab
out=Path(__file__).resolve().parent
for leaf in ("limit","limit_multi"):
    p=out/"tmp/limit_baseline"/(leaf+".py")
    name="eab."+leaf;mod=types.ModuleType(name);mod.__package__="eab";mod.__file__=str(p)
    sys.modules[name]=mod;setattr(eab,leaf,mod)
    exec(compile(p.read_text(encoding="utf-8"),str(p),"exec"),mod.__dict__)
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name="__main__")
