import sys,inspect,traceback
from pathlib import Path
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
import eab.kernel3d.entrance3 as E
import test_entrance3 as T
from e5a2_entrance_oracle import convex_ray_interval
from r13_event_oracle import assert_event_binding
source=inspect.getsource(E.first_entrance3);needle='tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x)'
namespace=dict(vars(E));exec(compile(source.replace(needle,'tuple(scalar_rational(_mapped_value) for _mapped_value in x0)'),'<r13-return-start-mutant>','exec'),namespace)
rng=T.random.Random(900)
A=T.convex_hull_3d([(rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)) for _ in range(8)])
B=T.convex_hull_3d([(rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)) for _ in range(8)])
start=tuple(rng.uniform(-1,1)+4*c for c in (rng.gauss(0,1),rng.gauss(0,1),rng.gauss(0,1)))
d=tuple(-c/4+.1*rng.gauss(0,1) for c in start)
e=namespace['first_entrance3'](A,B,start,d,t_max=8)
print('actual_position=',e.x, 'exact_time=',e.exact_t, flush=True)
assert_event_binding(e.t,e.exact_t,e.x,start,d,convex_ray_interval(A.verts,B.verts,start,d,8)[0])
