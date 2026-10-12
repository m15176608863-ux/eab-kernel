from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
findings=[
    {'id':'G6G-G2-01','severity':'major','file:line':'src/eab/kernel2d/g0_oracle.py:136-141',
     'conclusion':'first-exit oracle 只查事件区间中点，跳过前后均重叠的瞬时相触事件，出口完备性门会漏检真正的第一出口。',
     'failure_scenario':'B 为 L 形 [(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]；A=[(1/2,3/2),(1,3/2),(1,2),(1/2,2)] 沿 u=(1,-1)。两矩形并集独立 oracle 证明 t<1/2 时内部重叠，t=1/2 仅沿 x=1、y=1 接触。对任意 eps>0，平移 (1/2+eps,-1/2+eps) 后 min(x)=min(y)=1+eps，严格分离，故 t=1/2 真在拓扑 ∂E，不是 E 内部接缝。brute_ray_exit 返回 2。内核法锥路径删除第一出口全部盖，G0 仍 samples=1、passed=True。',
     'how_to_reproduce':'python -X utf8 review/repro/g6g_geom2_first_exit_pinch.py',
     'suggested_fix':'事件本身也必须检查。明确 first-exit 是首次实体非内部重叠，还是拓扑 int E 的出口（两者对非凸对不总等价）；后一口径需精确识别事件邻域是否有 E 外方向，不能只看射线上邻接两个区间。补 L 形反角独立门要求 t=1/2，且真首出口缺盖变异必须报红。',
     'verified_output':(ROOT/'review/logs/g6g_geom2_first_exit_pinch.log').read_text(encoding='utf8')},
    {'id':'G6G-G2-02','severity':'major','file:line':'src/eab/kernel2d/covers.py:238-239; src/eab/kernel2d/geom.py:63-71',
     'conclusion':'2D VV 仍先舍入精确差分量再 norm/unit，次正规与巨大有限输入给错误单位法向，且可表示的最终 gap 也会错。',
     'failure_scenario':'q=2^-1074；浮点 d=(q,q) 给 normal=(1,1)，而应为 (1/sqrt2,1/sqrt2)；精确 d=(149q/100,49q/100) 给 gap=q，而精确平方介于 (1.5q)^2 和 (2.5q)^2，正确舍入 gap=2q；浮点 d=(maxfinite,maxfinite) 给 normal=(0,0)、gap=inf。全部 vv.strict=True。',
     'how_to_reproduce':'python -X utf8 review/repro/g6g_geom2_vv_extremes.py',
     'suggested_fix':'保持 Fraction 相对向量，最终 gap 由精确平方构造根；单位法向独立缩放或精确分量平方比，不用已舍入 gap 作分母。与 3D 一致明确不可表示 gap 的报错/精确证据政策。补 2D 次正规、混合标量、巨大有限方向门。',
     'verified_output':(ROOT/'review/logs/g6g_geom2_vv_extremes.log').read_text(encoding='utf8')},
    {'id':'G6G-G2-03','severity':'major','file:line':'src/eab/kernel2d/g0.py:56-63,205-206',
     'conclusion':'有限坐标的特征长度显示上溢后变成无限验收阈值，二维 G0 在实际全部漏盖、误差为 inf 时仍报告 passed=True。',
     'failure_scenario':'m=maxfinite、h=m/2、k=m/4；B 为 L 形 [(-h,-h),(h,-h),(h,0),(0,0),(0,h),(-h,h)]，A 为上右凹槽内 [k,5k/4]^2。独立区间积距离为可表示的 k=4.4942328371557893e307，正常 G0 samples=1、passed=True、error=0；char_length 却为 inf。真实 _ve_side 全部改成 -1、VV 删除后无盖，G0 仍 samples=1、passed=True、worst_abs_error=inf、failures=[]。',
     'how_to_reproduce':'python -X utf8 review/repro/g6g_geom2_g0_infinite_scale.py',
     'suggested_fix':'缺盖/非有限候选或误差必须独立拒绝，不能靠 inf>threshold；有理或缩放形式评估特征尺度与验收界，任何不可表示验收界须 fail loud，而非自动通过。补纯有限大坐标控制组和真实全盖删除变异。',
     'verified_output':(ROOT/'review/logs/g6g_geom2_g0_infinite_scale.log').read_text(encoding='utf8')}
]
(ROOT/'review/notes/geom2_findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf8')
print('wrote',len(findings),'findings; unicode preservation confirmed')
assert '?' not in (ROOT/'review/notes/geom2_findings.json').read_text(encoding='utf8')
