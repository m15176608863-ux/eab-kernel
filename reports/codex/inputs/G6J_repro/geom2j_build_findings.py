"""Assemble this lane's verified machine-readable findings, from raw outputs."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
def log(name):
    raw=(ROOT/'review/logs'/name).read_bytes()
    return raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')

findings=[
    dict(id='G6J-ENTRANCE3-01',severity='major',
         **{'file:line':'src/eab/kernel3d/entrance3.py:246-255'},
         conclusion='三维闭集首入漏普通边界初态，切向短视窗静默报 none 而非 t*=0',
         failure_scenario=dict(A='[-3/4,5/4] x [-7/8,9/8] x [1,3]',B='[-1,1]^3',
                               x0=[0,0,0],d=[1,0,0],tol=0,t_max='1/16',
                               expected='kind=entrance,exact_t=0',actual='kind=none,exact_t=None'),
         how_to_reproduce='PYTHONDONTWRITEBYTECODE=1 python -X utf8 review/repro/geom2j_initial_boundary3.py',
         repro_path='review/repro/geom2j_initial_boundary3.py',
         verified_output=log('geom2j_initial_boundary3.log'),
         verified_log='review/logs/geom2j_initial_boundary3.log',
         suggested_fix='对初态 E 边界独立收集当前精确有限域零间隙盖，方向无关返回 entrance/exact_t=0；补切向/背离/进入和零/正 t_max 门',
         doc_contract=[
             'src/eab/kernel3d/entrance3.py:34 none 被定义为射线在 t_max 内不触及 E；普通闭集相触初态已经触及 E',
             'src/eab/kernel2d/entrance.py:7 统一闭集首入为 min{t>=0 : x(t) in E}；二维同构路径已含切向/背离初接触',
             'src/eab/kernel3d/entrance3.py first_entrance_brute docstring 明示 x0 已相触/相交时返回0'],
         scope_note='普通凸盒面接触，非紧配内缝；三尺度/姿态共6格静默none、3格背离异常、3格进入控制正确；此旧漏网并非 R9 新引入'),
    dict(id='G6J-GEOM2-01',severity='major',
         **{'file:line':'src/eab/kernel2d/covers.py:145-146'},
         conclusion='公共 in_cone 对允许的微反射 normal_cone 输出把反向薄扇区错误标严格内部',
         failure_scenario=dict(P=[[0,0],[1,0],[2,'-1/100'],[2,1],[0,1]],vertex=1,
                               normal_cone_tol='1/50',direction=['1/200',1],expected=-1,actual=1,
                               independent_certificate='与两条实际报告法向的 Fraction 点积均负，角距均>pi/2，远超1/50 sin窗口'),
         how_to_reproduce='PYTHONDONTWRITEBYTECODE=1 python -X utf8 review/repro/geom2j_reflex_cone_inverse.py',
         repro_path='review/repro/geom2j_reflex_cone_inverse.py',
         verified_output=log('geom2j_reflex_cone_inverse.log'),
         verified_log='review/logs/geom2j_reflex_cone_inverse.log',
         suggested_fix='strict 分支补精确非反射/同侧约束；微反射同向显式窗口最多返回0，反向必须拒绝',
         doc_contract=[
             'src/eab/kernel2d/covers.py:115-117 normal_cone 明示小反射在转角<pi/2且sin不超过窗口时接纳',
             'src/eab/kernel2d/covers.py:143 in_cone 明示对给定向量精确判1严格内部/0边界或显式sin窗口/-1外部',
             'src/eab/kernel2d/covers.py:17-25 局部单盖默认精确，域窗口只放宽有效集，strict始终精确严格性'],
         scope_note='只公共helper组合，不把 ve_cover/vv_cover 计为受影响（它们走别的精确谓词）；三姿态均复现')
]
path=ROOT/'review/notes/geometry_findings.json'
path.write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'ASSEMBLED','confirmed_candidates':len(findings),'path':str(path)},ensure_ascii=False))
