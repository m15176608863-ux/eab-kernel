"""Reproduce finding tests/test_limit_multi.py:268 on the saved e1fbbd4 bytes.
Run from repository root; the mutation is compiled in a private subprocess, no source write.
"""
from pathlib import Path
import sys,types
import eab
import pytest
ROOT=Path(__file__).resolve().parents[3]
CURRENT="--current" in sys.argv
BASE=ROOT/"src/eab" if CURRENT else ROOT/"reports/codex/E3E4_evidence/tmp/limit_baseline"
def load(name,src):
    mod=types.ModuleType(name);mod.__package__="eab";mod.__file__=str(BASE/(name.split(".")[-1]+".py"))
    sys.modules[name]=mod;setattr(eab,name.split(".")[-1],mod)
    exec(compile(src,mod.__file__,"exec"),mod.__dict__)
load("eab.limit",(BASE/"limit.py").read_text(encoding="utf-8"))
src=(BASE/"limit_multi.py").read_text(encoding="utf-8")
old="        if rmin.status == OPTIMAL and rmin.x[ia] > 0.0:"
assert src.count(old)==1
load("eab.limit_multi",src.replace(old,"        if False:"))
tests=[str(ROOT/"tests/test_limit_exact_selfcheck.py")+"::test_multi_unbounded_screen_covers_both_rejection_branches_and_nonzero_body"] if CURRENT else [str(BASE/"test_limit_multi.py"),str(BASE/"test_limit_arch.py")]
raise SystemExit(pytest.main(tests+["-q","-p","no:cacheprovider"]))
