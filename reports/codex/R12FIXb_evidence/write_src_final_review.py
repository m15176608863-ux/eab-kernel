"""Readonly source-site supplement after stronger CFG taint propagation.

No approvals. Final site metadata comes from raw_frozen.json when available.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
KEY=('path','function','rule','node')


def key(v):
    return tuple(v[k] for k in KEY)


def classify(v):
    p=v['path'].removeprefix('src/eab/');f=v['function'];s=v['source']
    if v['rule'] in {'closed-syntax','closed-context-protocol'} and ('with localcontext()' in s or s.startswith('with ')):
        if p=='dual.py':
            return 'APPROXIMATE_TRANSCENDENTAL_MODEL_NOT_EXACT','此 with localcontext 块只设置 Decimal80 上下文和下溢 trap，ctx.power 给一般非半整数幂导数的近似系数；无 exact midpoint certificate。必须按一般指数近似范围排除，不能因 with 已知上下文就宣称原系数正确舍入。'
        if p=='oracle_construction.py':
            return 'CANDIDATE_CERTIFIED_BY_EXACT_INPUT','with localcontext 设置的 Decimal80 sqrt 仅给 _candidate_positive 近似候选；_round_positive 对原 Fraction value 完整中点 cell 核验后才可返回，不通过则 exact bit-search。此局部 with 不改变原输入真值，不批准任意上下文管理器。'
    if p=='adapters/bdda2d.py':
        return 'REPORTED_OUTPUT_AND_EXACT_LENGTH','_record 中 c.normal/c.gap/param 是已完成构造的输出字段，仅转成 ContactRecord，未再被开方/归一。唯一新的 length_or_area 来自 A/B 原 poly 顶点分别 Fraction(q[k])-Fraction(p[k]) 后 norm_rational；不是从 c 的舍入 normal/gap 派生。需要对象字段/实参敏感摘要，而非把整个 c taint 洗白。'
    if p=='contact_record.py':
        return 'DATA_SERIALIZATION_PUBLIC_FACTORY','cls(**kw) 是 from_dict 的公开 dataclass 工厂，kw 由声明字段 _decode 得到给定 binary64/枚举/tuple 数据；该实例装配本身不做派生几何构造。任意外部 subclass 的 __init__ 不可静态证明，只能局部公开工厂边界，不能批准通用未知数值 callable。'
    if p=='dual.py':
        if f in {'Dual.__mul__','Dual.__truediv__','Dual.__rtruediv__'}:
            return 'ORDINARY_DUAL_ARITHMETIC_NOT_EXACT','直接 helper 保留普通非抵消输入的 float 导数快路径；范围/抵消风险分支才使用原值 Fraction 完整公式。现行普通 Dual 算术不是全表达式正确舍入算术，不可把已产生的 float 运算一律当 exact-input reset；这种通用算术/model边界需 caller-sensitive 检查，不自动批准。'
        if f in {'sin','cos'}:
            return 'APPROXIMATE_TRANSCENDENTAL_MODEL_NOT_EXACT','c 是 libm cos/sin 的浮点超越系数，Fraction(c)*Fraction(a) 只保证这个给定近似系数与种子的完整乘积最后舍入/范围检查。它不证明理想超越导数正确舍入；不能以“Fraction出现”抹除前面的系数近似。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','atan2 明确 angular=True，_ratio_derivative 不走普通 quotient float 快路径；对给定 xv/yv 和原种子独立 Fraction，完成有理分子/平方和分母后最终舍入。导数不使用已舍入 math.atan2 primal，不能因 primal 同处 return 的 taint 污染该确切依赖。'
    if p=='kernel2d/entrance.py':
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','_first_entrance_concave 的 x=_at(X,D,t)，X/D 来自 _frpoint 且 t 为 Fraction 事件；_contact_report 的参数/参考点/平方 gap 都从这些 exact 源和原坐标构造，最后才 vector_rational/sqrt_rational。浮点 ctol 只作 near 报告选择，不先作用在 x 的几何构造上。'
    if p=='kernel2d/g0.py':
        if '.append(' in s:
            return 'ORDINARY_DATA_OPERATION','rep.failures.append 只保存退出时刻/显示见证/独立 oracle 标签的报告数据；内层 brute_polygon_distance 已独立按原 Fraction 几何求值，这个列表 append 不重算或构造任何数值。'
        return 'DIAGNOSTIC_NOT_EXACT_TRUTH','_minimum_witness_distance 度量被测 cover 已输出 point_a/point_b 的显示间距，专门用来暴露坏见证。它不是原几何真值，退出真时刻 t 另由独立 exact event oracle 计算；有意检查舍入输出的范围排除不能叫无提前舍入证明。'
    if p=='kernel2d/g0_oracle.py':
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','distance 的 A/B 入口 points->F，best 是 segment_square 返回的最小 Fraction 完整平方距；sqrt_display 只调用独立 oracle_construction.sqrt_exact，Decimal 候选必须以原 best 中点证书核验。中间 scalar_exact(t) 仅 arg 显示，不反馈 best。'
    if p=='kernel2d/geom.py':
        return 'LEGACY_APPROX_NOT_EXACT','_tri_axes 对浮点顶点先 sub，再 norm(e)，最后各分量除该 rounded length，确有提前舍入。当前 exact triangle SAT 不调用此旧 helper；保留是未清理的旧近似边界，不给予“无先舍入”或 exact 构造批准。'
    if p=='kernel3d/covers3.py':
        if f=='_orth':
            return 'LEGACY_APPROX_NOT_EXACT','_orth 两遍 float Gram-Schmidt 的 sub/mul/dot 之后才 unit(v)，确实是先舍入正交残量再归一化。当前 src 未见调用（保留旧 helper）；该技术债不能用已有测试全绿或单位化名字作正确性证明。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','ee_cover 的 pa0/pb0/dA/dB 各从原顶点 Fraction；candidate=cross(dB,dA)、s/t、qa/qb 均有理。numerator=dot(candidate,sub(qa,qb))、nn=dot(candidate,candidate)，_signed_gap 一次 sqrt_rational(numerator²/nn)。前一行 unit_normal 已舍入但不流入 numerator/nn；需局部依赖敏感分析。'
    if p=='kernel3d/entrance3.py':
        if f=='first_entrance_brute':
            return 'APPROXIMATE_DIAGNOSTIC_NOT_EXACT','first_entrance_brute 是共享生产 overlap 谓词的浮点扫描/二分佐证，At=A.translated(x0) 和后续样本会舍入；effective_geom_tol/characteristic_length 仅该近似扫描的步长/容差，不是理想仿射首入证书。保留明确非主 oracle 边界，不批准 exact 构造。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','生产 first/shortest 入口的 At/Ax 来自 Fraction _ray_shift/_translated_exact。_cover_at 只按标签显式 vf/fv/ee 分派并从原坐标重建；merge_degenerate 由 _facet_plane_on_views 的 exact raw 平面与 _coplanar_face_with_normal 逐原顶点 Fraction 判共面，c.normal 只查是否 None，不用其舍入分量作平面关系。'
    if p=='kernel3d/exact_geom.py':
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','_surface_interior_witness 的 a/m 来自 triangles/planes 的逐坐标 F 模型，key=_direction_key(m) 保持有理比例；dot(key,a) 在 Fraction/int 上建立平面字典键。不存在归一后的 float 法向输入，caller summary 的整体 taint 不能代替此真实来源。'
    if p=='kernel3d/frozen.py':
        if f=='_unit_jet':
            return 'OUTPUT_WRAPPER_WITH_EXACT_JET','value 已经是每个完整 n_i/sqrt(nn) 的最终显示；_FrozenNormal 只 tuple 包装该 value 并另存原 raw jet，未对 value 再归一。后续 frozen_gap 读 raw/derivatives 而非反解显示；附加属性可重绑，证明限当前源码构造后无额外写，不声称防任意外部篡改。'
        return 'SOURCE_PROOF_GAP_EXACT_JET','默认/带 _FrozenNormal 的 frozen_gap 使用 raw Fraction jet，_frozen_gap_polynomial 保持原坐标和导数，nn=dot(raw,raw)。_gap_difference 把 delta 及其通道各先 Fraction，再 normalized_difference_rational 完整差构造；绝不以 rounded unit normal/gap 作默认 exact 源。普通外部 n 明确是新的给定输入模型。'
    if p=='kernel3d/g03.py':
        if '.append(' in s:
            return 'ORDINARY_DATA_OPERATION','rep.completeness_failures.append 保存 (x,minimum2,truth2) 精确差异证据，没有数值变换或构造；不因报告对象别处有显示误差字段而把这里当作数值函数。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','truth2 是独立整数/有理 surface oracle 的完整平方距；sqrt_display 仅最终独立中点证书构造。_witness_squared 只读 va/vb 原特征坐标和 c.label 身份，逐 Fraction 后重建平方距，不使用 c 的 rounded witness/normal。随机采样模型与原几何 completeness 证书分开。'
    if p=='kernel3d/g03_surface_oracle.py':
        return 'SOURCE_PROOF_GAP_EXACT_FLOW','separated_distance 先清输入 Fraction 的共同正分母，best 在整数/有理完整投影平方上比较；result=best/F(den*den)，squared=False 时才 sqrt_display(result)。循环/keep 闭包没有把 best 改为 float，需 CFG/source 摘要保持这个不变量。'
    if p=='kernel3d/geom3.py':
        if f=='Polyhedron._find_interior_point':
            return 'APPROXIMATE_CANDIDATE_GENERATION_NOT_EXACT','scale 的 norm(sub(p,first)) 先浮点相减，后续 float 形心/法向偏移确为近似候选。最终 point_in_polyhedron(...,0)==1 只认证返回的实际点在内，不使搜索方向/距离成为理想精确构造，也不证明一定找到。保留候选边界，不能称无提前舍入。'
        if f=='Polyhedron.manifold_issues':
            return 'APPROXIMATE_DIAGNOSTIC_NOT_EXACT','所报 norm(float vertex difference) 作为源面平面度诊断的相对尺度，确有先舍入；该诊断带 tol/noise，不用于实体 branch。精确 component orientation 是另条路径，不能将这份诊断报告冒充有效闭壳完整证书。'
        return 'LEGACY_APPROX_NOT_EXACT','_inward_vertex_direction/_active_normals/_gordan_direction/_contact_cone_witness 旧链使用 rounded face normals、float 差/求和与阈值聚类，再 norm/unit，确有提前舍入。当前主 polyhedra_overlap 直连 exact_geom.surface_overlap；旧链的最终内点复验最多证实某实际候选，不证明近似搜索完备或构造精确。保留技术债范围，非正确性批准。'
    if p=='kernel3d/interlock.py':
        if 'effective_geom_tol' in s or 'rounding_floor' in s:
            return 'NOMINAL_REPORT_BUDGET_NOT_EXACT_EVENT_SET','effective_geom_tol/rounding_floor 只定义 nominal cover/extent/并列报告窗口；初始几何平移仍 translate_exact，且权威高度由 _exact_escape 的原输入精确全事件与前区间证书判定。预算自身是浮点报告模型，不能当理想几何距离/完备性阈值。'
        return 'NOMINAL_REPORT_NOT_EXACT_EVENT_SET','_candidates_uncached 经 rounded cover gap/normal 提名 z，浮点 z-z_prev 聚类后在这个 nominal 位姿复验 extent；它只输出标签/导数报告，不是 exact events 全集。escape_height_covers 另用 surface_events/_exact_escape 求权威根，不能据缓存直调就称候选链无先舍入。'
    if p=='limit.py':
        return 'OUTPUT_WRAPPER_WITH_EXACT_WITNESS','_ExactFloat.__new__ 先 Fraction(exact)，super().__new__(cls,_fl(exact)) 分配已最终显示值，object.__setattr__(obj,"_exact",exact) 原样附证书。两个调用不对显示再开方/几何差分；_rational 核对显示一致后取 exact，普通 float 运算不继承 witness。仅此源码限定的包装协议，不是任意 dunder 可信。'
    if p=='margin.py':
        if f=='cover_witness':
            return 'DIAGNOSTIC_NOT_EXACT_TRUTH','cover_witness 对已经舍入 point_a/point_b 做 float sub 后 norm/unit，确有提前舍入，但用途就是测坏的显示见证而非原特征真值；最终标量/分类来自原坐标 exact_distance_squared。保留诊断范围排除，不承诺该方向是理想精确最近点方向。'
        if f=='characteristic_length':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','每条差为 _exact.sub(_exact.vector(v),_exact.vector(v0))，原点各分量先 F 再差；geom3.norm 直接 norm_rational 在完整 Fraction 向量上构造，min/max 仅选取已构造长度。未用 float v-v0，不能因变量 out 是 float 就污染传入 norm 的表达式。'
        if f=='_repair_folded_construction':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','direction 来自 _qclosest_triangle 在原点/原面片 Fraction 相对坐标得到的 delta，仅 exact.mul 换向；a/b 已构造显示但不参与 direction。unit(direction) 直接 unit_rational，逐完整分量平方比求根，避免从 rounded projection 相减；输入 w/n 只在不修复分支原样返回。'
        if f=='_resolve':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','_surface_feature_squared 从原 A/B 和 c.label 索引算有理平方距；brute_feature_distance(squared=True) 同样原 surface 逐 F 后完整求最小平方；_repair_folded_construction 的修复方向使用 raw Fraction triangle residual，已有 w/n 只是显示。需要实参/字段/squared=True 敏感摘要，不是把这些 helper 返回 float 视为所有分支都 rounded。'
        if f=='margin_contacts':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','d2 保持原特征 exact Fraction 平方距（被接触模型接受时显式设 F(0)）；_normalized_difference(d2,d2 or F(1),F(delta)) 完整构造 sqrt(d2)-delta，并用原数代数中点证书。前面 w=sqrt_rational(d2) 的显示值从未流入 gap；同作用域两个构造不应混为依赖。'
        if f=='inflated_normal':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW','nearest_point_on_convex_entrance(...,exact=True) 返回有理投影，v=_exact.vector(x)-该投影是完整 Fraction 相对差，scale 仅择零分支；unit(v) 直接最终 unit_rational，未用 rounded global projection 反减。'
    raise AssertionError((p,f,v['rule'],s))


def main():
    old_files=['src_numerical_review.json','src_structural_review.json','src_round5_supplement_review.json']
    covered=set()
    for name in old_files:
        payload=json.loads((HERE/name).read_text(encoding='utf8'))
        covered.update(key(v) for v in payload['items'])
    released=json.loads((HERE/'release_candidate_unreviewed_sites.json').read_text(encoding='utf8'))
    released={key(v):v for v in released if v['path'].startswith('src/')}
    frozen=HERE/'raw_frozen.json'
    if frozen.exists():
        full=json.loads(frozen.read_text(encoding='utf8'))
        src=[v for v in full if v['path'].startswith('src/')]
        values=[v for v in src if key(v) not in covered]
        source='raw_frozen.json'
    else:
        values=list(released.values());src=None;source='release_candidate_unreviewed_sites.json (raw_frozen pending)'
    snapshots={}
    for p in {v['path'] for v in values}:
        data=(ROOT/p).read_bytes()
        snapshots[p]=(hashlib.sha256(data).hexdigest(),{ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(data.decode('utf-8-sig')))})
    items=[]
    for v in values:
        category,reason=classify(v)
        items.append({**v,'reason':'具体节点：'+v['source']+'。'+reason,
                      'category':category,'disposition':category,'formal_exception_approved':False,
                      'source_sha256_at_review':snapshots[v['path']][0],
                      'current_ast_node_present':v['node'] in snapshots[v['path']][1],
                      'was_in_release_candidate_unreviewed':key(v) in released})
    assert all(v['current_ast_node_present'] for v in items)
    remaining=[] if src is None else [v for v in src if key(v) not in covered|{key(w) for w in items}]
    payload={'input':source,'final_metadata_from_raw_frozen':src is not None,
             'reviewed_prior_artifacts':old_files,'count':len(items),
             'unique_site_fingerprint_count':len({key(v) for v in items}),
             'count_note':'Count preserves every raw_frozen occurrence; identical node fingerprint repeated within one scope may occur on multiple lines.',
             'src_files':len(snapshots),
             'by_disposition':dict(sorted(Counter(v['disposition'] for v in items).items())),
             'by_rule':dict(sorted(Counter(v['rule'] for v in items).items())),
             'remaining_unreviewed_src_against_raw_frozen':remaining,
             'formal_exception_approval_count':0,
             'review_note':'Source read-only and frozen. Categories are source-level explanations or explicit scope exclusions, NOT approvals. Legacy approximate construction remains a genuine incomplete requirement; stronger CFG taint is not presumed a false positive.',
             'items':items}
    (HERE/'src_final_supplement_review.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in payload.items() if k!='items'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
