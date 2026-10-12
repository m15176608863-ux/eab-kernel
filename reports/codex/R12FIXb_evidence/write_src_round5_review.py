"""Source-reviewed round-5 supplement; zero automatic policy approvals."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def review(v):
    p=v['path'].removeprefix('src/eab/');f=v['function'];s=v['source'];r=v['rule']
    if p=='adapters/bdda2d.py':
        return 'INPUT_PARSE_GIVEN_BINARY64_MODEL','value 来自 csv.DictReader 的 detparams 字符串；这里只解析给定窗口/角度输入，Bdda2DWindow.__post_init__ 另检有限性/范围，后续 boxes 以 Fraction(window) 构造。不是 float(几何派生差)；CSV 十进制到 binary64 的输入建模本身不宣称十进制无损。'
    if p=='construction.py':
        if f=='scalar_rational':
            return 'EXACT_FINAL_CONSTRUCTION_BOUNDARY','exact=Fraction(value)，本站 float(exact) 是最终 Fraction->binary64 边界，不是中间几何量；随后检查非有限/不允许的非零下溢。RN-even 依赖 Python Fraction.__float__ 与既有 midpoint 测试，不是函数内额外逐次中点证明；caller 仍必须供给完整未先舍入表达式。'
        if f=='sqrt_rational':
            return 'EXACT_FINAL_CONSTRUCTION_BOUNDARY','significand 由 isqrt(numerator//denominator) 和精确 4*n 与 d*(2*k+1)^2 比较/ties-even 得到。quantum=max(root_exponent-52,-1074) 保证 significand<=2**53，cast 可精确表示；ldexp 只移动最终输出幂二尺度，没有先 sqrt(nn) 再除的中间舍入。'
        return 'CANDIDATE_CERTIFIED_BY_EXACT_INPUT','确有两个已舍入量相减，但它仅是不可信 candidate。compare 通过原 Fraction(c,nn,offset) 的带符号平方比较判断真实代数数；候选不精确时必须 bracket 相邻 floats 并检查 exact midpoint，否则完整有序 bit-search。没有用 candidate 决定未核验的精确结果，不能把此例扩成普通 subtract-rounded 安全。'
    if p=='contact_record.py':
        return 'INPUT_PARSE_GIVEN_BINARY64_MODEL','_decode 按字段名把 JSON ref_points/normal/params 等已序列化标量转换为给定 binary64 模型；无本函数内派生几何差分。它不保证 JSON 十进制精确可表示或自动有限，validate 是另一个契约步骤。'
    if p=='dual.py':
        if r=='direct-float':
            if f in {'Dual.const','Dual.seed','Dual._pair','Dual.__pow__'}:
                return 'PUBLIC_GIVEN_PRIMAL_MODEL','这是公开 Number(int/float/Dual) API 的 primal/指数模型入口；const/seed 建 binary64 值，_pair 对非 Dual 操作数建立常量通道，__pow__ 拒绝 Dual 指数后规范 p。可能把大整数/实参数舍入为该显式 binary64 模型，不能称原整数/理想实数无损，也不能据此批准 caller 的已舍入几何派生值。'
            return 'PRIMAL_COMPARISON_NOT_CONSTRUCTION','__lt__/le/gt/ge、val/is_exact_zero 中的 float 只规范支持的非 Dual Number；比较/val 择支不生成几何构造。Dual 分支直接检查 primal 或全部导数通道，未隐式丢 Dual 导数；不把未经支持的任意 Fraction/自定义对象纳入零判定保证。'
        if f=='Dual.__pow__' and 'Fraction(c)' in s:
            return 'APPROXIMATE_TRANSCENDENTAL_MODEL_NOT_EXACT','该 c 来自一般非半整数幂的 Decimal80 ctx.power，Fraction(c) 仅保存近似系数。完整系数×seed 最终 _derivative_float 的范围检测不能证明理想超越导数正确舍入；必须保留明确近似范围排除，不能称无先舍入。'
        if f=='Dual.__pow__':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','此节点位于 p.is_integer 分支，c=Fraction(p)*Fraction(self.v)**(int(p)-1)，a 为给定导数通道，完整 c*Fraction(a) 后才 _derivative_float；不读取上方已舍入 primal value。对规范后的给定 p/v/a 模型没有提前舍入。'
        if f=='_ratio_derivative':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','被报节点是慢路径：scale=Fraction(2)**frexp指数，un/vn 由各原值 Fraction 后除精确 scale；q=(Fraction(a)*vn-un*Fraction(b))/den/scale 完整有理式，再最终 _derivative_float。普通 float 快路径不是该节点，不能一并批准为 exact。'
    if p=='kernel2d/entrance.py':
        return 'ORDINARY_DATA_OPERATION','groups 的每个元素是由 [facet] 创建/append 的列表；groups[-1]+groups[0] 是两个源 facet 列表的环缝拼接，不是标量加法。精确平行测试在 parallel 内，拼接保留全部标签，没有 float 几何派生。'
    if p=='kernel2d/g0.py':
        if r=='closed-unproved-arithmetic':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','t 来自 brute_ray_exit->independent.ray_exit，原 A/B/u 分别 F 转换后计算有理 vertex-edge 事件，返回 Fraction t。t*Fraction(u[k]) 构造精确事件平移；后面 independent.translate 又逐项 F 加法，没有先浮点 t*u。'
        if '.append(' in s:
            return 'ORDINARY_DATA_OPERATION','rep.mismatches/failures 是报告列表，追加的 x/brute/cov/got/truth/arg 只记录既有比较结果，不对数值做构造，也不把报告值反馈几何。错误传播标记不能把 append 本身变成 rounded-construction。'
        return 'DIAGNOSTIC_NOT_EXACT_TRUTH','_minimum_witness_distance 对被测程序已经输出的 point_a/point_b 做 Fraction(a)-Fraction(b)，测量的是显示见证间距而非原特征的理想距离；只作为 got 与独立原坐标 oracle truth 比较。它有意检查已舍入产物，不是精确真值来源。'
    if p=='kernel3d/exact_geom.py':
        return 'OUTWARD_FILTER_NOT_GEOMETRY','_iv 把原 Fraction/float 变为 outward interval：float 输入是 singleton，非 float 的 cast 向上下 nextafter 扩张，溢出给 [-inf,inf]。_edge_window_filter 只在区间可证全正/全非正时判定，否则返回 None 由 Fraction 路径计算；f 不作为精确几何点或中间 root。'
    if p=='kernel3d/frozen.py':
        if f=='_unit_jet':
            return 'OUTPUT_WRAPPER_WITH_EXACT_JET','_unit_jet 的 n/dn 来源 _exact_jet_points 分别 Fraction 后的 face/edge/residual jet；normalized 先完成 c²/nn 再 sqrt_rational，导数先完成 dn[i]-n[i]*dot(n,dn)/nn。_FrozenNormal 只 tuple 包装已构造显示 value/result，并另存未归一 raw 与 derivatives。frozen_gap 读取原 jet，不用 rounded display 重建法向。附加属性可重绑定，本证明只限当前源码无额外赋值，不声称防任意外部篡改。'
        return 'SOURCE_PROOF_GAP_EXACT_JET_WRAPPER','face_normal_generic/ee_normal_generic/frozen_normal 直接把 _face_raw_jet/_ee_raw_jet/_frozen_raw_normal 返回的 Fraction raw 与导数交给 _unit_jet；入口逐 primal/seed F 转换先于任何坐标差/cross，sign 也先 Fraction。star unpack 的是已知二元 jet 数据，不是 callable；返回 _FrozenNormal 保留原 exact jet，未知自定义包装器不可套用。'
    if p=='kernel3d/g03.py':
        if '.append(' in s:
            return 'ORDINARY_DATA_OPERATION','rep.failures.append((x,got,truth)) 仅保存精确 completeness 或显示构造检查的失败证据；got/truth 是显示值不作为此 append 的几何输入。'
        return 'GIVEN_PROBE_MODEL_EXACT_PREDICATE','x 枚举 sample_translations3 给出的浮点随机探针和 oracle.boundary_probes 给出的 Fraction 精确边界，两者分别是当前查询的给定平移。membership_convex3 被测方与 oracle.overlap 独立方各对该给定 x 精确判定；原 source_av/bv 在被测凸包前冻结。不声称浮点随机探针对应理想连续随机实数，边界 Fraction 不先舍入。'
    if p=='kernel3d/geom3.py':
        return 'LEGACY_APPROX_NOT_EXACT','_ray_directions 黄金角样本先计算 float z、1-z*z，再 sqrt 和 unit，确有多次近似；旧 previous_reason 的 bounded seed 只能支持“另行定义的采样模型”，不能证明无提前舍入或理想球面方向精确。当前主 surface/point 谓词直连 exact_geom，不调用该旧序列；保留旧 helper 是明确范围性技术债，不是正确性批准。'
    if p=='kernel3d/interlock.py':
        return 'NOMINAL_REPORT_NOT_EXACT_EVENT_SET','该调用属于 _candidates->_candidates_cached->_candidates_uncached 的 nominal report 链。At 初始平移确实 translate_exact，但 z/nz 从已构造 cover 显示得来，存在浮点 z-z_prev 分组、z 位姿的 extent 报告。因此不能称它是理想逃逸高度的精确候选全集；escape_candidates 明示报告用途，escape_height_covers 的权威 root 另由 _exact_escape/surface_events 的 exact 全事件与区间证书决定。这是范围排除，不是“无提前舍入”证明。'
    if p in {'limit.py','limit_multi.py'}:
        if f=='_tangents':
            return 'EXPLICIT_ROUNDED_FRAME_MODEL','n 已逐分量 Fraction；first=Fraction(t1[k])，其中 t1 是已最终单位化返回的 binary64。源码明确新模型 t2=n×返回的 t1，而非理想未舍入 t1；所报每项减法实际是 Fraction 乘差，再 scalar_rational 一次输出，且 t2 不再范数归一。仅此既定基架模型可证，不声称与理想 orthonormal frame 完全相同。'
        if s.startswith('_ExactFloat('):
            component=('alpha：rx[ia] 来自 _lp_values(r.x,r.exact_x)' if s=='_ExactFloat(rx[ia])' else
                       'lambda：raw=rx 的精确列解，capx=Fraction(cohesion)*Fraction(area)，按行做完整有理除法' if 'capx[rj]' in s else
                       'row_duals：ry 经 _lp_values 保留精确 LP 对偶，乘精确 capx 后包装' if 'yv * cap' in s else
                       'mechanism：_twist_back 输入精确对偶与 Fraction(oc)-Fraction(origin)，完整有理参考点变换后包装')
            return 'OUTPUT_WRAPPER_WITH_EXACT_WITNESS', component+'。_ExactFloat.__new__ 先 Fraction(exact)，_fl 只产生显示 float，_exact 原值另存且普通 __setattr__ 禁止重写；_rational 读回前检查显示一致。不是从 rounded result 重新猜精确证书；check_duality/check_duality_multi 在返回前以原输入核验。不推广到任意 __new__/__float__ 协议，普通后续 float 算术也不继承 exact 见证。'
        if f=='_norm':
            return 'NONFINITE_REPORT_BRANCH','math.hypot(*v) 只在 any(not isfinite(x)) 分支传播报告 inf/nan；全部有限输入另行 sum(Fraction(x)**2)->sqrt_rational，没有按浮点缩放后开方。该非有限报告不被作为 LP exact 证书；这不是任意 finite hypot 豁免。'
        if f=='_rational':
            return 'OUTPUT_WITNESS_READBACK','在 isinstance(v,_ExactFloat) 守卫内，float(v) 只读取已有 binary64 视图并与 _fl(v.exact) 核对；成功后返回 v.exact 而非 Fraction(float(v))。无新增派生构造，也不假定所有 float subclass 都可信。'
    if p=='margin.py':
        return 'DIAGNOSTIC_NOT_EXACT_TRUTH','dmin 与 truth 是已经输出的距离显示，dmin-truth 是有意计算的构造误差残差，只与 4*rnd 比較决定抛错。精确 completeness 另由 minimum2!=truth2 强制检查，返回接触由 minimum2<=ctol² 决定；残差不输入 root/norm/几何差分构造，不冒充原距离真值。'
    if p=='oracle_construction.py':
        return 'CANDIDATE_CERTIFIED_BY_EXACT_INPUT','_candidate_positive 的 float(value)/Decimal80 sqrt 仅候选；_round_positive 必经对原 Fraction value 的 exact RN-even midpoint-cell certificate，失败转完整 ordered-bit 搜索（溢/下溢显式报错）。不同于无该证书的 Dual 一般指数近似，此处候选舍入不决定答案。'
    if p=='predicates.py':
        return 'OUTWARD_FILTER_NOT_GEOMETRY','_float_value 只给 cross2_sign/dot2_sign/orient3d 的快滤波输入，溢出返回符号 inf 迫使不确定；完整误差界含转换/underflow，结论不确定回到原坐标 Fraction。其 f 不作为几何构造输出或替代原精确坐标；仅支持已核证的 float/Fraction filter source 路径。'
    if p.startswith('readers/'):
        if r=='closed-rounded-call':
            return 'ORDINARY_DATA_OPERATION','sg.alias 是 StepGeometry 的顶点编号字典，alias 由 strip_duplicate_vertices 返回 int->int 映射；update 只合并离散数据，没有浮点算术。已有 duplicate/环向的输入规范化属于另行 reader 契约，不在这个 update 节点重算几何。'
        detail={'readers/bdda3d.py':'来源 entrance JSON 的 vertex/area/t1/t2/o3t/slip 字段',
                'readers/bdda_df.py':'df07/df18/df22/verts CSV 原始字符串或先前已解析的字段',
                'readers/bdda_geom.py':'csv.DictReader 的 x/y 字符串',
                'readers/tf_probe.py':'TSV _rows 的 time/point/normal/area/gap/shear/force 字符串'}[p]
        return 'INPUT_PARSE_GIVEN_BINARY64_MODEL',detail+'，所报 float 只做输入解码/身份规范，形成外部给定 binary64 模型，没有本函数先计算 rational 几何量再截断。不能声称十进制无损，且这些 reader cast 自身并非全都检查有限性；物理/有限性校验与来源语义是另外契约。'
    raise AssertionError((p,f,r,s))


def main():
    values=[v for v in json.loads((HERE/'round5_unreviewed_sites.json').read_text(encoding='utf8')) if v['path'].startswith('src/')]
    legacy=json.loads((HERE/'legacy_sites_before_review.json').read_text(encoding='utf8'))
    snapshots={}
    for p in {v['path'] for v in values}:
        data=(ROOT/p).read_bytes()
        snapshots[p]=(hashlib.sha256(data).hexdigest(),{ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(data.decode('utf-8-sig')))})
    items=[]
    for v in values:
        disposition,reason=review(v)
        old=[o for o in legacy if all(o.get(k)==v.get(k) for k in ('path','function','rule','source'))]
        items.append({**v,'reason':'具体节点：'+v['source']+'。'+reason,
                      'disposition':disposition,'formal_exception_approved':False,
                      'previous_reason':[o['previous_reason'] for o in old],
                      'legacy_scope_rechecked':bool(old),
                      'previous_reason_limit':'Historical rationale checked against current source, not approval; present reason is authoritative and may narrow/correct its guarantee.',
                      'source_sha256_at_review':snapshots[v['path']][0],
                      'current_ast_node_present':v['node'] in snapshots[v['path']][1]})
    payload={'input':'round5_unreviewed_sites.json','legacy_reference':'legacy_sites_before_review.json',
             'count':len(items),'src_files':len(snapshots),
             'by_disposition':dict(sorted(Counter(v['disposition'] for v in items).items())),
             'by_rule':dict(sorted(Counter(v['rule'] for v in items).items())),
             'legacy_site_entries_rechecked':sum(v['legacy_scope_rechecked'] for v in items),
             'formal_exception_approval_count':0,
             'review_note':'Read-only source review. Legacy scope reasons checked, not copied blindly. Approximate/model/report classifications are explicit scope exclusions, not proof of no premature rounding. Source unchanged.',
             'important_qualification':'_FrozenNormal is tuple display + raw jet data, not an immutable/tamper-proof witness: attributes can be rebound. Current src writes them only in __new__. _ExactFloat blocks ordinary rebinding but no claim is made against arbitrary Python reflection.',
             'items':items}
    assert all(v['current_ast_node_present'] for v in items)
    (HERE/'src_round5_supplement_review.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in payload.items() if k!='items'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
