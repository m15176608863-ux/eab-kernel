"""Complete G6N N01--N05 replay with current-contract success criteria.

All generated files stay in review. Old originals were separately replayed
unchanged except copied path anchoring, see support_r14_old_replays.json.
"""
from pathlib import Path
from fractions import Fraction as F
import json, math, subprocess, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'), str(ROOT)]
sys.dont_write_bytecode=True
from eab.dual import Dual, sin, cos, atan2
from eab.numeric_domain import ConstructionDomainError
from eab.contact_record import records_from_json, ContactRecord
from eab.readers.bdda3d import load_records
from eab.limit import LimitContact

rows=[]
def passrow(name, detail):
    rows.append(dict(id=name,result='resolved',detail=detail));print(name,detail)
def rejects(name, call):
    try:call()
    except ConstructionDomainError as error: return str(error)
    raise AssertionError(name+' failed to reject outside-current-domain input')

for p in (2**54+1, -(2**54+1), 2**400+1):
    for wrapper in (int,F):
        r=Dual(-1.0,(1.0,))**wrapper(p)
        assert r.v==-1.0 and r.e==(float(p),)
passrow('G6N-N01', '6 integer/Fraction exponent cases preserve exact odd parity and derivative signs')

details=[]
for q in (F(2**54+1),F(2**54)+F(1,3),F(2)**-1075,F(2)**-1100,F(2)**-2000):
    for fun in (sin,cos):
        for x in (q,Dual(q,(F(1),))):details.append(rejects('N02',lambda fun=fun,x=x:fun(x)))
    for y,x in ((q,q),(Dual(q,(q,)),Dual(q,(F(0),)))):
        details.append(rejects('N02',lambda y=y,x=x:atan2(y,x)))
tiny=math.ulp(0.0)
jet=atan2(Dual(tiny,(tiny,)),Dual(tiny,(0.,)))
assert F(1,2)<F(jet.v)<1 and jet.e==(0.5,)
passrow('G6N-N02',f'{len(details)} previously lossy angle cases now named rejection; supported min-subnormal tiny/tiny retains angle in (1/2,1) and derivative .5')

base=dict(source='g6o',step=0,contact_index=0,block_a=0,block_b=1)
details=[]
for field in ('ref_points','normal','params','shear','slip_ref','gap','length_or_area','normal_force','gap_ref','lock_position'):
    for token in ('1e-400','-1e-400','1e400','-1e400'):
        v=token
        if field=='ref_points':v='[['+token+',0]]'
        elif field in ('normal','params','shear','slip_ref'):v='['+token+',0]'
        text=json.dumps([base])[:-2]+',"'+field+'":'+v+'}]'
        details.append(rejects('N03',lambda text=text:records_from_json(text)))
details.append(rejects('N03',lambda:ContactRecord.from_dict(dict(base,ref_points=[[F(2)**-2000,0]],normal=[F(2)**-2000,0]))))
folder=ROOT/'review/tmp/support_r14_replay';folder.mkdir(parents=True,exist_ok=True)
for token in ('1e-400','"1e-400"'):
    p=folder/('numeric.json' if not token.startswith('"') else 'string.json')
    p.write_text('{"entrances":[{"bi":1,"bj":2,"etype":"np","area":'+token+'}]}',encoding='utf-8')
    details.append(rejects('N03',lambda p=p:load_records(p)))
passrow('G6N-N03',f'{len(details)} ContactRecord vector/scalar, direct rational, real reader numeric/string cases now named rejection')

for mu in (1e16,1e17):
    rejects('N04',lambda mu=mu:LimitContact((0.,0.,0.),(1.,2.,3.),mu,tangent=(2.,-1.,0.)))
passrow('G6N-N04','both original high-mu unsafe-cone inputs lie outside explicit new mu domain and are rejected at contact construction')

p=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'review/repro/support_r14old_support_cone_interlock_relative_bound.py')],cwd=ROOT,text=True,capture_output=True,encoding='utf-8')
assert p.returncode==0,p.stderr
readme=(ROOT/'README.md').read_text(encoding='utf-8')
design=(ROOT/'docs/r14fix_design_sync.md').read_text(encoding='utf-8')
assert '不推出' in design and 'C_k(μ) ≥ cos(π/k) C(μ)' in design
assert 'C(μ·cos(π/k))' in readme
passrow('G6N-N05','same geometric counterexample still numerically holds; current README/design retract unqualified capacity-relative bound, retaining correct capacity-function inclusion')
(ROOT/'review/evidence/support_r14_replay.json').write_text(json.dumps({'confirmed_new_findings':0,'replay':rows,'N05_output':p.stdout},ensure_ascii=False,indent=2),encoding='utf-8')
print('R14_REPLAY_PASS: all five original root causes resolved under stated current contracts')
