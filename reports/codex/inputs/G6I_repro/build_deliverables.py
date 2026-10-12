"""Assemble reviewer-only evidence. Never writes outside review/."""
from pathlib import Path
import collections, datetime, hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'review'

def read_json(path):
    return json.loads((OUT/path).read_text(encoding='utf-8-sig'))

def emit(path, value):
    (OUT/path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def link(path, label=None):
    return f'[{label or path}]({(ROOT/path).as_uri()})'

SPECS = [
    ('G6I-01', 'major', 'src/eab/kernel2d/entrance.py:146-175',
     '凸首入只裁剪支撑直线而未核有限特征域，平直链返回错误盖标签及不相触的见证。',
     'A=[(0,0),(1,1),(0,2)]，B=[(0,0),(3,0),(3,1),(1,1),(0,1)]，x0=(0.5,2)，d=(0,-1)。真首入 t=1，唯一接触 A 顶点0与B边3；实际 label=(VE,0,2)，point_a=(0.5,1)，point_b=(1,1)，gap=0，tied还收域外边2。四个尺度/姿态格均复现；同根因的合法初触FF格抛无段重叠异常。',
     '获选与并列标签前，以有理数核VE/EV/FF有限接触域；合并共线支撑时保留实际源特征映射，不能用clamp掩盖域外点。补平直分段内点/端点标签及见证同点门。',
     'geom2_convex_flat_facet_domain.py', 'root_confirm_G6I02d',
     '时刻与整体成员仍正确；范围为允许的平直顶点退化，按窄域major。FF异常与错标签同根因，不重复计数。'),
    ('G6I-02', 'major', 'src/eab/kernel3d/geom3.py:464-480;324-325',
     '声称精确局部凸性的公共API仍只看源面环/Newell方向，漏掉声明折面实体的真实凹对角线。',
     '单位盒顶点6抬至z=3/2，顶环(4,5,6,7)按声明耳切为(7,4,5)+(5,6,7)。实体0<=z<=1+(1/2)max(0,x+y-1)，顶点4、6在实体中而中点(1/2,1/2,5/4)在外，故非凸；对角线(5,7)三重积=-1。实际P.is_convex(0)=True、reflex_edges(0)=[]；exact_surface(P)给False及(5,7)。24格确认。沿源边(4,5)的实际三角面角为pi/2，而源描述符角1.3258176636680326，仅作同根因佐证。',
     '让实体凸性/凹棱接口使用声明三角表面拓扑；或对非平面源面清晰拒收并限定公共契约。不要把单个Newell源描述符宣传为实际折面实体的局部凸性。',
     'geom3_folded_reflex_hidden.py', 'root_confirm_G6I03d',
     '有效域是闭合、朝外、嵌入的声明三角表面。源面环非平面，旧manifold_issues会提示；并未声称它是平面多面体。covers的描述符豁免未覆盖is_convex/reflex_edges的精确声称。'),
    ('G6I-03', 'major', 'src/eab/kernel3d/covers3.py:399-408',
     '锥交裕度先舍入最近点各分量再取范数，将可表达正标量清零或扭曲。',
     'd=2^-1074，A=tetra(O,(1,-1,d),(d,1,-1),(-1,d,1))，B=A.reflected()，ia=ib=0；全部输入为有限binary64。独立投影证书给p=(-d/3)^3、|p|²=d²/3，真裕度d/sqrt(3)正确舍入为5e-324，实际0.0。d换2倍时实际1e-323而应5e-324；24格中10格错。cones_intersect_relint始终True且正确。',
     '在有理最近点上先形成范数平方，再作最终标量构造；不能_float_vector(p)后norm，也不能sqrt(float(d²))。补次正规中点平方证书及布尔/标量分离门。',
     'geom3_cone_margin_subnormal.py', 'root_confirm_cone_margin',
     '窄域数值构造错误，布尔可行性未受影响，不升critical；noise为报告量，不是丢弃可表达标量的许可。'),
    ('G6I-04', 'major', 'tests/e5b_margin_oracle.py:83-84;90-91',
     '默认精确距离oracle先舍有理距离平方再开方，在合法微尺度上错拒正确产物并接受真实内部同类缺陷。',
     's=2^-600，A=[3s,5s]×[-s,s]^2、B=[-s,s]^3，真距2s=4.819839730205768e-181可表达。当前production答对，check_exact_margin却抛default-exact distance construction。把真实body_distance及margin_contacts内部最终距离构造改sqrt(float(d2))，两者答0.0，精确状态/平方证书仍保留；该oracle反而PASS。b6126cf原scale断言在同一新增压力尺度baseline PASS、mutant红；新helper相反。',
     '独立test-owned构造先缩放指数/高精度求最终根，或用相邻float中点平方作RN-even证书；不能import生产sqrt作expected。补平方下溢/上溢但最终根可表达的格，真实内部恢复旧构造时目标距离断言必须红。',
     'docs_margin_oracle_range.py', 'root_confirm_margin_oracle',
     '门失牙major，不是当前body_distance已错。2^-600为新增压力格，不是被删除的原网格；没有跑整套mutant，也没有宣称整套10100都会放行。'),
    ('G6I-05', 'minor', 'src/eab/kernel3d/geom3.py:409-455',
     'manifold_issues的空列表外向认证只查总有向体积，被大外向分量掩盖小内向分量。',
     '分离两立方体：[-2,2]^3外向，及[9,11]×[-1,1]^2全部面反绕。独立有向体积为64和-8，总56>0，整体manifold_issues(tol=0)=[]；单独小分量会报inward。空列表声称“合法闭合定向流形外法向朝外”不成立。',
     '逐连通表面分量核方向/实体嵌套，或把诊断文案收窄为实际检查项目；空腔需按嵌套语义，不能机械要求各分量体积都正。',
     'geom3_manifold_component_orientation.py', 'root_confirm_manifold',
     '输入不满足核心实体判定的外向前提，故只计诊断/文档minor，不将非法输入的核心结果记critical。'),
    ('G6I-06', 'minor', 'docs/canon_map.md:93;README.md:106;tests/test_invariance_2d.py:17-22',
     '三处现态文案仍保留旧口径，与同文件当前实现/核验状态不一致。',
     'canon_map砖二依赖写命题7/8均未实现，但同表命题7及实际first_entrance/first_entrance3已存在；README称canon未经G6，但canon记二至五轮独立核验；invariance_2d模块开头仍说19格只夹区间/隐式tol_eff，当前两门已改逐格精确oracle。',
     '同步现态文案，把历史格子/历史尚未审查状态清楚标为旧HEAD，保留砖二自身未实现等真实限制。',
     'docs_stale_current_contracts.py', 'root_confirm_stale_docs',
     '三处旧口径合并一个文档minor；不是新增学术优先性major，也不据此把未实现的砖二算已实现。'),
]

def main():
    findings=[]
    for ident, severity, location, summary, scenario, fix, script, label, boundary in SPECS:
        meta=read_json('logs/'+label+'.json')
        assert meta['exit_code']==0
        raw=(OUT/'logs'/f'{label}.log').read_bytes()
        assert hashlib.sha256(raw).hexdigest()==meta['log_sha256']
        findings.append(dict(id=ident,severity=severity,**{'file:line':location},
            summary=summary,failure_scenario=scenario,suggested_fix=fix,
            how_to_reproduce="$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 review/repro/"+script,
            repro_script='review/repro/'+script,verified_output=raw.decode('utf-8',errors='strict'),
            verified_log='review/logs/'+label+'.log',verified_exit_code=0,
            verified_log_sha256=meta['log_sha256'],confirmed=True,root_verified=True,
            severity_boundary=boundary))
    # Same square-before-root cause in another independently checked test helper.
    # The new squared=True certificate is correct; do not claim a second escaped
    # mutation or count this as another major.
    meta=read_json('logs/root_near_parallel_oracle.json')
    assert meta['exit_code']==0
    raw=(OUT/'logs/root_near_parallel_oracle.log').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==meta['log_sha256']
    findings[3]['additional_instances']=[dict(
        **{'file:line':'tests/test_near_parallel_edges.py:62'},
        summary='exact_seg_seg默认显示出口仍sqrt(float(best))；间隙1e-200被显示为0，squared=True证书和当前production均正确。',
        repro_script='review/repro/geom3_near_parallel_oracle_display.py',
        how_to_reproduce="$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 review/repro/geom3_near_parallel_oracle_display.py",
        verified_log='review/logs/root_near_parallel_oracle.log',
        verified_output=raw.decode('utf-8'),verified_exit_code=0,
        verified_log_sha256=meta['log_sha256'],root_verified=True,
        scope='同类漏网实例，归并G6I-04；它在旧版本已存在，未证明该新squared门旧红新绿，也不另计数。')]
    counts={k:sum(f['severity']==k for f in findings) for k in ('critical','major','minor')}
    emit('G6I_findings.json',dict(work_order='WO-G6I',HEAD=read_json('full_suite.json')['head'],
        role='独立审查方；未修代码',counts=counts,m0_can_exit=False,
        findings=findings,unconfirmed=[],completeness_limitations='详见G6I_report.md完整性批评；没有把有限检查写成全域正确性证明。'))

    # G6E identifiers are the original raw array's one-based indexes.
    g6e=[]
    for row in read_json('geom2/replays.json')['g6e']:
        g6e.append(dict(raw_index=int(row['raw_id'].split('-')[-1]),status='已消解',
            method='原输入/等价精确门重放',root_log='review/logs/root_G6E_geom2_six.log',output=row))
    for row in read_json('gates_docs/replays.json'):
        g6e.append(dict(raw_index=int(row['id'].split('-')[-1]),status='已消解',
            method='原文/真实内部变异或等价门重放',root_log='review/logs/root_G6E_docs.log',output=row))
    for i in (25,29,31,37,40,42,43,44):
        meta=read_json(f'logs/root_G6E_{i}.json');assert meta['exit_code']==0
        g6e.append(dict(raw_index=i,status='已消解',method='原复现改为正向修复断言',
            root_log=f'review/logs/root_G6E_{i}.log',
            output=(OUT/f'logs/root_G6E_{i}.log').read_text(encoding='utf-8')))
    for i in (9,11,20,21,22,45):
        meta=read_json(f'logs/root_G6E{i:02d}.json')
        assert meta['exit_code']==(1 if i==9 else 0)
        text=(OUT/f'logs/root_G6E{i:02d}.log').read_text(encoding='utf-8')
        if i==9:assert 'ValueError' in text and 'parallel to normal' in text
        g6e.append(dict(raw_index=i,status='已消解',
            method='原复现：09通过响亮拒绝；其他拒绝错误证书/保持局部尺度',
            root_log=f'review/logs/root_G6E{i:02d}.log',output=text))
    g6e.sort(key=lambda r:r['raw_index'])
    assert len(g6e)==len({r['raw_index'] for r in g6e})==31
    emit('G6E_replays.json',dict(count=31,index_policy='原raw数组一基编号，不冒充其自带ID；14/32原条目内容重复但分别溯源。',replays=g6e))
    out=['# G6E 第五轮重放：31条\n','全部由 root 再跑。14/32为原台账重复，非两项独立数学证据。40的旧浮点difference模型与现精确给定数据模型不同，现默认门为0/6/0/0/[]；详见日志及三维专项。\n',
         '| 原raw索引 | 当前状态 | root运行输出 |\n|---|---|---|']
    out += [f"| {r['raw_index']:02d} | {r['status']} | {link(r['root_log'],'日志')} |" for r in g6e]
    (OUT/'G6E_replays.md').write_text('\n'.join(out)+'\n',encoding='utf-8')

    # Root annotations complement the 2-D and 3-D hand review inventories.
    rows=[]
    for row in read_json('branch_inventory.json'):
        file=row['file']
        if file=='src/eab/construction.py':
            cls,why='output_range_guard','最终非零标量不可表达时拒绝；不改变几何/LP真值。'
        elif file in ('src/eab/limit.py','src/eab/limit_multi.py'):
            cls,why='resolvability_report_only','U与_UNCERTAIN区分可分辨性报告/诊断，不取代原数据精确证书；lp_tol只是候选层参数。'
        elif file=='src/eab/lp.py':
            cls,why='heuristic_with_exact_certificate_fallback','浮点候选/基及入基价格仅作启发；有理层核最优、无界、Farkas证书，不通过就精确走完。'
        else:continue
        rows.append(dict(row,classification=cls,explanation=why))
    emit('root_branches.json',dict(inventory_rows=rows,
        supplemental=[
            dict(file='src/eab/predicates.py',classification='certified_filter',explanation='input与派生量有限/正规范围筛查，误差界外符号返回，界内从原Fraction数据兜底；10000 orientation及10000向量对拍通过。'),
            dict(file='src/eab/dual.py',classification='construction_or_primal_branch',explanation='值与jet择支分开；mul/div/atan2相消或中间越界回落精确导数表达，最终范围不够则响亮拒收；有限导数搜索不是全域证明。'),
            dict(file='src/eab/readers/bdda_geom.py',classification='documented_legacy_normalization',explanation='dup_tol被抬坐标舍入地板是明示legacy政策，不是原坐标保真读取；核心精确合同作用于规范化后输入。')],
        limitation='AST按命名检索是导航而非所有比较的形式穷举；全src人工阅读与两个几何专项补录共同构成审查。'))
    emit('newdiff_coverage.json',[dict(file=row['file'],reviewer=(
        'gates_docs: 全部新diff逐行审读' if row['file'].startswith('tests/') else
        'geom2: 全部新diff逐行审读' if '/kernel2d/' in row['file'] else
        'root: 全部新diff逐行审读' if row['file']=='src/eab/limit.py' else
        'geom3: 全部新diff逐行审读')) for row in read_json('gates_docs/newdiff_inventory.json')])
    print(json.dumps(dict(counts=counts,g6e_replays=len(g6e)),ensure_ascii=False))

if __name__=='__main__':main()
