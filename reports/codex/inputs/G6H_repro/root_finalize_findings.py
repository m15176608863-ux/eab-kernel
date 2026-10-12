"""Collect only root-reproduced, deduplicated findings; never edit production."""
from pathlib import Path
import json, subprocess, time, os

ROOT = Path(__file__).resolve().parents[2]
cases = [
    ("G6H-01", "geom2_tight_fit_initial_state.py", "src/eab/kernel2d/entrance.py:110",
     "凹体紧配内缝位于 topological int(E)，却被首入 API 当成 t=0 的边界首入。",
     "U=[(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)]；A=[(0,1/2),(1,1/2),(1,3/2),(0,3/2)]；x0=(0,0),d=(0,1)。独立矩形并证明 E=[-2,2]×[-5/2,3/2]，x0 严格在 E 内；按模块初态合同应走 exit 策略，实际 entrance/t_exact=0。沿+y的真正边界为3/2。不是要求局部 shortest_exit 解一般凹体的全局 PD。",
     "用可认证的局部补集/拓扑判定区分 E 真边界与仅两体内部不交的紧配缝；增加独立矩形并 oracle 的初态 kind 门。若此 API 不支持该类输入，应清晰拒收并同步合同，不能将内点标成 ∂E。"),
    ("G6H-02", "geom3_frozen_gap_tangent_cancellation.py", "src/eab/kernel3d/frozen.py:209-215; src/eab/kernel3d/interlock.py:352-370; src/eab/margin.py:571-572",
     "冻结盖将已舍入的单位法向重新当精确数据，切向大杠杆污染 gap/导数，零种子 Dual 还能改变逃逸高度 primal。",
     "精确3-4-5旋转的两区间盒，切向跨度M=1e20，真实最近VF间隙1：body_distance=1，冻结裕度gap=6662.338147750939；互换3/5和4/5后gap=-6660.338147750939。切向种子(-8e19,6e19,0)真导数0，实得4440.892098500626。M=1e8,gap=1e-9实得7.66133814775094e-9。另斜面nz=4/5的已选最短出口VF，普通标量lift精确5/8，改零种子Dual offset后primal=-8326.047684688674。",
     "从原始特征的精确未归一化法向/相对向量构造 signed gap 及其 jet，最后才除范数/舍入；逃逸高度的标量与Dual走同一精确比值模型。增加大切向杠杆、符号交换及零Dual种子 primal 等价门。"),
    ("G6H-03", "geom3_dihedral_turn_rounding.py", "src/eab/kernel3d/geom3.py:324-326",
     "dihedral_turn 先分别舍入面单位法向，将合法 binary64 四面体可表达的正转角清成0。",
     "O=(0,0,0),Z=(0,0,1),C=(-M,M+1,0),D=(M-1,-M,0)，M=1e8。全部坐标是精确binary64整数、闭合外向四面体、volume=1/6、manifold_issues=[]。沿实际面遍历方向的精确三重积为1，dot=2M²，真角atan(1/(2M²))=5e-17；dihedral_turn((0,1))返回0。M=1e9、1e12、2^50同样丢正角。is_convex/reflex_edges另走精确符号，未据此声称其错误。",
     "用未归一化的精确法向和棱向量形成 atan2 的同次齐次参数，最终缩放/舍入；不可先舍入两单位法向再相减或叉积。增加薄但非退化四面体的正角与反向面符号门。"),
    ("G6H-04", "root_wrench_intermediate_range.py", "src/eab/limit.py:112-120",
     "公开 wrench helper 对有限输入先算溢出乘积再相减，最终可表达的零力矩却静默返回NaN。",
     "dim=2或3；force=point=(1e160,...),origin=0，另测1e200。每个输入有限binary64，独立Fraction叉积的每个力矩严格0，最终力/矩全可表达。实际返回[force...,nan...]且不抛异常。这里是公开构造helper的错误，不声称有理LP求解器吞NaN后静默给错承载比。",
     "按给定输入精确形成力臂及叉积，最终只舍入可表达结果；至少必须对中间/最终非有限构造响亮拒绝，不能返回NaN。加力与力臂共线、乘积中间越界但最终抵消的2D/3D门。"),
    ("G6H-05", "docs_canonical_oracle_dropvertex.py", "tests/test_invariance_geom.py:325-329",
     "迁移后的 facet 完整性 oracle 先调用被测 exact_convex_view，真实漏极点可让新门同错全绿，而旧断言报红。",
     "tetra_box_vv/generic两格，rot=0,tmag=1000,s=1。正常新旧门都PASS；在 exact_convex_view 原编号保留分支内部对len>=8、|coord|>100的体删最后一个真实极点并缓存错误凸视图。当前迁移门两格仍PASS；从b6126cf取出的旧同名函数两格均在完整facet标签集合不变断言AssertionError。副本恢复SHA已核。另一仅错置源面编号的变异也为新门3绿、旧门3红。只声称该迁移门失牙，不声称9851门全逃逸。",
     "oracle从保存的原始坐标独立构造凸包/支撑集合，不经过被测凸视图；另独立核源编号保留条件。稳定纯平移格保留旧完整标签断言，配删真实极点与源编号错置两类内部变异。"),
    ("G6H-06", "geom3_g0_coordinate_noise_blind.py", "src/eab/kernel3d/g03.py:209-210; src/eab/margin.py:343-346",
     "非凸距离完整性门在atol=0仍用坐标噪声地板验收，平移后可吞真实漏盖导致的10倍错误距离。",
     "q=ulp(1e8)=1.4901161193847656e-8；A为center(T,T,T),half=q的盒；B为两个half=q盒的并，中心(T,T,T-3q)与(T+12q,T,T)。独立区间并距离严格q。只在真实 _outside_dot_band 内部注入拒绝z向盖；T=0时margin报missed nearest pair、G0红，T=1e8时margin返回10q且G0(radius=0,samples=1,tol=0,atol=0) passed=True,err=9q,failures=[]。样本实际核了，oracle正确，错距离不是见证显示舍入。源码仅进程内函数替换并finally复原，tracked字节SHA前后相同。",
     "将精确盖平方距/最近特征完备性票与浮点见证构造误差票分开；前者不加global-coordinate噪声地板，后者保留清晰的显示误差口径。增加同一内部删盖缺陷在原点/工程坐标/短特征下都须红的门。"),
]
rows=[]
env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","PYTHONIOENCODING":"utf-8"}
for fid, script, location, summary, scenario, fix in cases:
    command=["python","-X","utf8",str(ROOT/"review/repro"/script)]
    start=time.perf_counter()
    p=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf8",errors="replace")
    output=p.stdout+p.stderr
    log=ROOT/"review/logs"/("root_final_"+fid+".log")
    log.write_text("command="+json.dumps(command,ensure_ascii=False)+"\nexit_code="+str(p.returncode)+"\n"+output,encoding="utf8")
    assert p.returncode==0,(fid,output)
    rows.append(dict(id=fid,severity="major",**{"file:line":location},summary=summary,
        failure_scenario=scenario,how_to_reproduce="$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 "+str(ROOT/"review/repro"/script),
        suggested_fix=fix,verified_output=output,repro_script="review/repro/"+script,
        verified_log=log.relative_to(ROOT).as_posix(),verified_exit_code=0,
        root_verified=True,verified_seconds=time.perf_counter()-start,confirmed=True))
    print(fid,"major","exit=0",summary)
(ROOT/"review/notes/root_confirmed_findings.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf8")
assert len(rows)==6 and all(r["root_verified"] for r in rows)
print("confirmed critical=0 major=6 minor=0")
