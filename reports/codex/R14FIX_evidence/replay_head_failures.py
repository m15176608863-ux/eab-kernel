"""Read-only git-show replay of N01/N04 on actual baseline module source.

No checkout, source replacement, or sibling access. Uses unchanged current
LP/construction dependencies; records both baseline module blob hashes.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"src"))
OUT = Path(__file__).resolve().parent
rows = []
hashes = {}
for name in ("dual", "limit"):
    raw = subprocess.check_output(["git", "show", f"878d4f0:src/eab/{name}.py"],cwd=ROOT)
    hashes[name] = hashlib.sha256(raw).hexdigest()
    module = types.ModuleType("eab.r14_baseline_"+name)
    module.__package__ = "eab"
    sys.modules[module.__name__] = module
    exec(compile(raw, f"<HEAD878d4f0/{name}.py>", "exec"),module.__dict__)
    if name == "dual":
        for p in (2**54+1,F(2**54+1)):
            answer = module.Dual(-1.,(1.,))**p
            assert answer.v == 1 and answer.e[0] < 0, "actual old sign defect must reproduce"
            row = {"finding":"N01", "input_type":type(p).__name__, "exact_exponent":str(p),
                   "actual":repr(answer), "expected_primal":-1,"expected_derivative":float(p)}
            rows.append(row); print(row)
    else:
        for mu in (1e16,1e17):
            c=module.LimitContact((0,0,0),(1,2,3),mu,tangent=(2,-1,0))
            dead=[-1,-2,-3,0,0,0];live=[2,-1,0,0,0,0]
            r=module.limit_load([c],dead,live,dim=3,k=4)
            directions=module.friction_generators(c.normal,c.mu,3,4,c.tangent)
            normal_works=[sum(F(x)*F(y) for x,y in zip(c.normal,g)) for g in directions]
            row={"finding":"N04","mu":mu,"status":r.status,"alpha":r.alpha if r.status=="optimal" else "inf",
                 "generator_normal_work":[str(q) for q in normal_works]}
            if mu == 1e16:
                ratio=r.alpha.exact**2/(F(mu)**2*F(14,5))
                assert ratio>1,"actual old capacity must exceed the independent raw-normal circle upper bound"
                row["squared_capacity_to_raw_normal_circle_upper_ratio"]=float(ratio)
                row["old_selfcheck_ok"]=module.check_duality(r,[c],dead,live,dim=3,k=4)["ok"]
            else:
                assert r.status=="unbounded" and min(normal_works)<0,"actual old tensile-ray/unbounded defect"
            rows.append(row);print(row)
(OUT/"head_failure_replay.json").write_text(json.dumps({"head":"878d4f0","read_only_git_show":True,
    "module_sha256":hashes,"dependency_note":"LP/construction unchanged by R14; numeric_domain original helpers unchanged",
    "results":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("HEAD_FAILURES_REPRODUCED 4; no worktree source replaced")
