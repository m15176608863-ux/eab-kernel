"""Materialize the readonly, source-reviewed round-4 structural-site ledger.

This is NOT a policy builder or an exception approval. Explicit classifications
below were written after reading each relevant source scope/callee. Do not use
them as a rule-name or file-name allowlist for new or changed source.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def classify(v):
    p, f, r, s = v['path'], v['function'], v['rule'], v['source']
    file = p.removeprefix('src/eab/')
    if f == '<module>' and s in {'tuple', 'list', 'Fraction'}:
        return 'DECLARATION_OR_TYPE_DATA', '模块级 Vec/Point/Poly 等类型别名的泛型参数；此 Name 节点不是函数调用，没有数值计算、开方或派生坐标输入。只针对所示声明节点，不按名字豁免运行时调用。'
    if f == '<module>' and s == 'sys.float_info.epsilon':
        return 'DECLARATION_OR_TYPE_DATA', '读取 CPython binary64 machine epsilon 常数供误差/诊断阈值；这里没有动态数值 callable 或几何构造。使用该预算的下游仍须单独分析，不能用常数声明批准整函数。'
    if file == 'adapters/bdda2d.py':
        return 'DATA_COLLECTION_OR_LABELING', 'out 是刚生成的 ContactRecord 列表；canonical_key 只比较排序后的块号、cover.value 与 Feature.as_tuple 标签。该排序不计算或重新构造法向/距离，也不通过 key 选择数值函数；需要限定此接收者与方法源码。'
    if file == 'construction.py':
        return 'IEEE_BITCAST_CONSTRUCTION_BOUNDARY', 'normalized_difference_rational 的局部 from_bits 用 >Q/>d 固定宽度 pack/unpack 重解释 binary64 编码，非近似算术。正数有序 bit 搜索的候选只经精确代数 compare 与 RN-even 中点判断选出最终结果；打包 lower 得到相邻浮点编号不会把舍入后的差值当原始几何。范围仅此已核证构造实现，非任意 struct 调用。'
    if file == 'contact_record.py':
        if f == 'ContactRecord.to_dict':
            return 'DATA_SERIALIZATION_REFLECTION', 'fields(self) 给 dataclass 字段名；getattr 只取字段值并交 _encode，后者递归转换 Enum/Feature/tuple/dict。无取出值后作为 callable 执行、无构造几何；此解释只覆盖 ContactRecord 数据序列化契约，不为恶意 subclass 属性执行提供数值证明。'
        if f == 'ContactRecord.from_dict':
            return 'DATA_SERIALIZATION_REFLECTION', 'fields(cls) 限定可接受字段，_decode 将来源值转换为枚举/特征/给定 binary64 数据；cls(**kw) 是公开 classmethod 的 dataclass 工厂，保留 subclass API。它不做几何差分/范数，无法静态证明任意外部 subclass 的 __init__；必要兼容边界必须明确而非称任意 callable 安全。'
        if f == '_encode':
            return 'DATA_SERIALIZATION_REFLECTION', '递归仅遍历 tuple/dict 数据，在 Enum/Feature 分支提取字段；不运行容器中的 callable、不形成平方根/几何差分。递归结果用于 JSON 输出。'
        if f == 'validate':
            return 'DATA_SERIALIZATION_REFLECTION', 'name 来自两个固定字符串字段元组；getattr 的结果仅传 math.isfinite 作结构有限性校验，既不执行字段值，也不构造几何量。禁止把此局部有限性读取拓展为任意数值 getattr 豁免。'
        if f == 'records_from_json':
            return 'DATA_SERIALIZATION_REFLECTION', 'json.loads 提供来源记录数据，直接调用本类 from_dict 作契约解码；几何字段是输入数据，不是本路径先算出的 float 差分。需保留 from_dict 的 subclass/API 边界，不推导为通用类调用可证。'
    if file == 'dual.py':
        if f == 'Dual':
            return 'SCALAR_PROTOCOL_DECLARATION', '__radd__/__rmul__ 类体赋值引用同类已声明 __add__/__mul__，这是 Python 左右算术协议对称别名，不是从未知容器取数值函数执行。原算术方法本身的精度契约并未因别名得到额外批准。'
        if f == 'Dual.__rsub__':
            return 'REMAINING_SIMPLE_NUMERIC_DYNAMIC_REWRITE_REQUIRED', '(-self).__add__(o) 直接访问已知 Dual 临时对象的 dunder，实际仅反向减法，未调用平方根；但仍触发运行时方法取值，完全可写为 -self + o。要求 3 应继续机械简单化而不是例外；本轮仅审不改，不正式批准。'
        if f in {'central_difference', 'convergence_order'}:
            return 'REQUIRED_PUBLIC_DIAGNOSTIC_CALLBACK', 'central_difference 是公开 G3 中心差分诊断 API，f(tp)/f(tm) 的外部 callable 无法静态证明，convergence_order 仅用其结果作 h 扫描误差/阶数报告。此处有意先用浮点扰动并差分，不宣称精确构造或独立主 oracle；移除 callable 会破坏公开功能，只能局部明确必要边界，不能声称 f 内部无禁止模式。'
        if 'FloatingPointError(' in s:
            return 'VALIDATION_ERROR_PATH', '构造并抛出 FloatingPointError 的失败分支，防止非零导数/幂的无声下溢；异常对象没有数值结果流入任何几何构造。'
        if f == 'Dual.__pow__':
            if s == 'p.is_integer()':
                return 'DECLARATION_OR_TYPE_DATA', 'p 已经由本函数入口 float(p) 规范化，is_integer 只择整数/非整数分支，无几何数据构造；不支持任意对象同名方法的默认放行。'
            if s == 'Underflow':
                return 'DECLARATION_OR_TYPE_DATA', 'Underflow 是 Decimal 异常类，作为 ctx.traps 的字典键开启失败检测，不作为数值函数调用。'
            if s == '_derivative_float(c * Fraction(a))':
                return 'SOURCE_PROOF_GAP_EXACT_FLOW', '本节点在 p.is_integer 分支；c=Fraction(p)*Fraction(self.v)**(int(p)-1)，再与 Fraction(seed) 完整相乘后仅由 _derivative_float 最终舍入。不能与后面的 Decimal 一般指数近似系数混淆。'
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', '仅一般非半整数幂分支采用 localcontext.prec=80 与 Decimal ctx.power；指数/底数来源 binary64，系数 c 是 80 位超越近似，随后 Fraction(c) 只精确保存该近似，不是精确原函数导数。范围/下溢检测有效，但绝不批准为精确/正确舍入幂构造。'
        if f in {'Dual.__mul__', 'Dual.__truediv__', 'Dual.__rtruediv__'}:
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', '直接调用命名 _product_derivative/_ratio_derivative；这些 helper 普通非抵消输入保留 float 快路径，风险分支才全 Fraction 并最终舍入。没有隐藏 callable 分派，但不能据 helper 名字把普通 Dual 运算宣称为全表达式精确构造；泛型下游仍需 caller-sensitive 数据流。'
        if f in {'_ratio_derivative', '_product_derivative'}:
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', '此被报节点在有理数慢路径：先将原 primal/seed 分别 Fraction，再完成积和或幂二缩放的商，仅 _derivative_float 作最终转换。这个具体调用无提前舍入；不批准同 helper 的普通 float 快路径作为精确算术。'
        if f == 'sqrt':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'sqrt(x.v) 是同模块直接递归进入非 Dual 标量分支，原始 primal 值直接给 sqrt_rational；导数独立由 _sqrt_derivative 在 Fraction(seed)^2/(4*Fraction(value)) 上开方，不把这个已舍入 primal root 再用于导数除法。'
        if f in {'sin', 'cos'}:
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', 'libm sin/cos 给定 primal 的系数 c 是浮点超越模型；此处 Fraction(c)*Fraction(seed) 完整乘积最后舍入，但 c 本身无正确舍入超越函数保证。不得把“最终乘积范围检查”冒充原超越导数精确。'
        if f == 'atan2':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', '明确 angular=True，_ratio_derivative 跳过普通 quotient float 快路径，用给定 xv/yv/seed 的 Fraction 完整分母与分子后最终舍入；atan2 primal 本身仍是 libm 模型，这条导数调用不先使用已舍入 primal。'
    if file == 'kernel2d/covers.py':
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'membership_convex 直接调用精确入口拓扑函数；第二处 X 与 dx/dy 都来自 Fraction 坐标/精确扩窗，几何平移先有理后判定。该 call 的未证明来自传递调用/比较器摘要，不是发现 float 平移先舍入；不要以 waiver 代替类型恢复。'
    if file == 'kernel2d/entrance.py':
        if f == '_candidate_labels':
            return 'DATA_COLLECTION_OR_LABELING', 'Cover.label() 返回类型/特征索引身份 tuple，yield 只枚举这些标签；数值距离不参与此方法，不是 yield callable 或动态几何构造。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'first_entrance 的初态直接给 entrance_membership_exact(A,B,x0)，函数在原坐标分别 Fraction 后构造相对位姿/拓扑；x0 是 API 给定数据，不是此节点生成的舍入差量。仍需分析 callee，不按 exact 名字批准。'
    if file in {'kernel2d/exact.py', 'kernel2d/g0_oracle.py', 'kernel3d/entrance_topology.py'}:
        if ('cmp_to_key' in s or s in {'compare', '_angular_compare'}):
            return 'REMAINING_NUMERIC_CALLBACK_REWRITE_REQUIRED', '比较器源码只做半平面整数分类和 Fraction/int 叉积符号，输入 rays/lines 从逐坐标 Fraction 几何产生，不含提前舍入。可是 cmp_to_key 把数值比较 callable 传给 sorted，当前门不能分析；可改显式命名比较的稳定插入排序，要求 3 不应以豁免取代简单化。本审核不正式批准。'
        if file == 'kernel2d/g0_oracle.py':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'distance/ray_exit 的 A/B/u 在入口逐项 F 转换；投影平方、事件 t、平移及局部扇区探针都保持 Fraction。sqrt_display 仅对最终距离平方走独立 midpoint-certified oracle；boundary_has_exterior 返回精确拓扑布尔。需要源摘要处理比较回调，不得因传递 unknown 整函数豁免。'
        if file == 'kernel3d/entrance_topology.py':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', '_configuration_planes 使用 exact_geom.vector 的 Fraction 顶点；_chamber_directions 的法向/叉积/步长保持 Fraction，yield 传递有理方向而非 callable。G.mul(-1) 只是精确换号；入口 probe 的顶点先 exact add 再直接 polyhedra_overlap(…,0)，无先 float 平移。迭代器/精确比较摘要缺口不可整体豁免。'
    if file == 'kernel2d/g0.py':
        if '.append(' in s:
            return 'DATA_COLLECTION_OR_LABELING', '只向 G0Report/DistanceReport/ExitReport 的列表追加已经完成判定的失败证据 tuple；append 本身不计算几何。即便 tuple 内有 brute_polygon_distance 调用，其正确性由独立 oracle 路径单独审查，不能因是报告容器跳过该调用。'
        if f == 'random_convex_polygon':
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', 'rng 是 Random 实例，uniform 生成随机测试输入模型，凸包以返回的 binary64 坐标为给定数据；不声称该有限样本是理想连续分布或精确随机实数构造。不是从既有几何差量先舍入再精确化。'
        if '_minimum_witness_distance' in s:
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', '这里度量被测程序已经输出的浮点见证差，专门用于检测其构造误差；真值另由独立 Fraction oracle 计算。它是待审产物的诊断，不被当作精确真值或几何谓词。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', '本路径调用独立 g0_oracle：给定坐标/平移先 Fraction，完整平方距离/事件时间精确计算；sqrt_display 是只在最终输出做独立中点证书的开方。g0_convex 中 membership_convex 是被测方而非共享主 oracle，需跟进其源调用摘要。'
    if file == 'kernel2d/geom.py':
        return 'DECLARATION_OR_TYPE_DATA', 'float 在 type(x) is float/type(i) is float 的类型判别中作身份对象，而不是函数别名执行；择精确谓词快/慢路径本身没有派生几何构造。'
    if file == 'kernel3d/covers3.py':
        if f == '_float_vector':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', '该实际声明是 return vector_rational(v,allow_underflow=True) 的薄包装，非外部同名函数冒名顶替。必须按本源码及 caller 的 v 来源分析，不能凭 _float_vector 名字信任未知定义，也不能将收到的已舍入派生 v 洗成 exact。'
        if r in {'closed-callable-value', 'closed-namespace-value'}:
            return 'CACHE_IDENTITY_NOT_DISPATCH', '此函数对象仅放入 lru_cache 参数/implementation 身份元组以使 monkeypatch 缺陷注入失效旧缓存。已检查 _cone_relint_cached/_local_facets_cached/_support_planes_cached：实际计算通过命名函数直接调用，implementation 未被下标取出后执行。允许 key 数据不等于允许未知 callable 调用。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'exact_convex_view 保留给定顶点并用 exact_geom Fraction/int 判据得到 hull；facet_plane3 从 _qnormal/_qedge 原坐标精确法向与平面再构造最终显示。此调用未把已舍入 face_normal 当原精确平面；主要未证明根源是 hull/control-flow 摘要，须恢复源推理而非整函数豁免。'
    if file == 'kernel3d/entrance3.py':
        if f.startswith('first_entrance_brute'):
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', '该公开 helper 明示“共用生产重叠谓词的抽样佐证，非独立主 oracle”；state 以 float add/mul 生成采样平移再判 supplied pose，扫描与二分均近似。不能宣称理想仿射射线的精确首入；仅保留诊断边界，不是精确构造批准。'
        if f == '_coplanar_face_with_normal' and 'intersection' in s:
            return 'DATA_COLLECTION_OR_LABELING', 'verts 是特征顶点索引 set，f 是当前面环索引；intersection 只检查特征关联，再另由 exact_face_normal/_same_plane 做 Fraction 几何判据，不是容器 callable 分派。'
        if '.label()' in s and ('lambda' in s or 'sort(' in s or s in {'c.label()', 'q.label()', 'cc.label()', 'best.label()'}):
            return 'DATA_COLLECTION_OR_LABELING', 'Cover3.label() 只返回 kind/a_feature/b_feature 身份，排序 lambda 的 0/1 仅把已选同标签盖稳定置前；没有捕获数值 callable、也无重算几何距离。精确事件/候选选择发生在该显示标签排序之前。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', '此生产入口路径用 _ray_shift 逐项 Fraction(x0)+Fraction(d)*Fraction(t)，再 _translated_exact；polyhedra_overlap 在该有理位姿精确判定。merge_degenerate 通过原坐标精确 facet_plane 分组而非 rounded cover normal；被报 direct call 的传递摘要仍需补足。'
    if file == 'kernel3d/exact_geom.py':
        if s == 'count(1)':
            return 'PROOF_CONTROL_FLOW_GAP', 'itertools.count(1) 枚举整数 k，射线 (1,k,k*k) 的所有后续 parity 判据在清正分母后的整数坐标执行；无浮点计数与随机射线。需允许明确 integer iterator 语义，不是运行未知生成器/数值函数。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'exact_geom 在 vector/triangles 入口逐坐标 F 转换；被报的 dot/point-in-triangles/面片分割 witness 调用只做 Fraction/int 代数，_point_in_triangles 还清正分母为整数。样本与平面相交不先变 float，count/递归传递摘要不足不应靠豁免伪装证明。'
    if file == 'kernel3d/frozen.py':
        if f == '_FrozenNormal.__new__':
            return 'TUPLE_DISPLAY_JET_PROTOCOL', 'super().__new__(cls,values) 是 tuple subclass 的分配协议；values 只是显示分量，raw/derivatives 另外原样 tuple 保存精确归一前 jet。未取出任意数值函数执行，frozen_gap 优先使用保留的 exact jet；转普通 tuple 才显式定义新的给定 rounded normal 模型。附加属性可重绑定，不能声称不可篡改；当前 src 只在 __new__ 赋值，局部审核不覆盖任意外部反射修改。'
        if r == 'closed-data-attribute':
            return 'TYPE_GUARDED_FIELD_DATA', '该字段读取有 isinstance(c/delta,Dual) 或 isinstance(n,_FrozenNormal) 守卫；v/e 是 primal/导数给定通道，各自先 Fraction，raw/derivatives 是归一前 exact jet。它读取数值数据不执行属性值，不能扩成任意对象同名属性可信。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'frozen_lift 的 value/raw/dn 均来自 _frozen_raw_normal/_frozen_gap_polynomial 的原坐标 Fraction jet；先求完整 -value/raw[2] 以及 (-dg-result*d[2])/raw[2] 后只在 _derivative_float 最终转换。没有先单位化 rounded normal 再求高度。'
    if file == 'kernel3d/g03.py':
        if '.append(' in s:
            return 'DATA_COLLECTION_OR_LABELING', '仅向 G0 报告 dataclass 的失败/差异列表追加结果；不把这些报告值回馈几何判据。节点内其他数值调用不能因此免于独立检查。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'g0_convex3 在被测凸包规范化前冻结 source_av/source_bv，独立 g03_exact oracle 用 Fraction/int 原坐标；距离门先精确构造平移，surface_oracle 的 truth2 为精确平方，sqrt_display 仅最终显示并有独立中点证书。_witness_squared 从原特征 Fraction 重建，不是 rounded witness 自证。'
    if file == 'kernel3d/g03_exact.py':
        if f == 'support_labels':
            return 'DATA_COLLECTION_OR_LABELING', 'iter(ia/ib) 是内建集合迭代，ia/ib 由精确投影极值产生的顶点索引 frozenset；next 仅取零维支撑集的唯一顶点身份。没有容器内 callable，也未以 index 构造浮点几何。'
        if f == 'sat_model':
            return 'DATA_COLLECTION_OR_LABELING', 'axes 是 set，add 接收由精确法向 plane_key 规范出的 tuple；F(0) 是精确零偏移。集合去重不是动态函数分派，法向代数在此之前有理执行。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'sat_model 把 av/bv 逐项 qpoint(Fraction)，支持面、棱差和轴投影均精确，overlap 直接复用其模型。未证明由源模型摘要欠缺导致，不是容许浮点差分。'
    if file == 'kernel3d/g03_surface_oracle.py':
        if f.endswith('.keep'):
            return 'PROOF_CONTROL_FLOW_GAP', 'nonlocal best 只更新外层 Fraction 平方距离最小值；keep 用 num*denominator 与 numerator*den 交叉整数比较，不接收/捕获 numerical callable。需分析这个标量闭包写入，不能全局放开 nonlocal。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'separated_distance 首先把所有坐标 F 转換并清共同正分母为整数，best 通过完整精确投影/边边距离比较更新，result=best/F(den*den)。squared=False 才在最终 sqrt_display 独立证书构造；不存在先 rounded 差再开方。'
    if file == 'kernel3d/geom3.py':
        if f == '_ray_directions':
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', 'global _RAY_DIRS 仅旧黄金角采样序列的缓存声明，缓存内容确有 float sqrt/unit 近似。当前主 point_in_polyhedron/polyhedra_overlap 改走 exact_geom，不调用此序列；这里不能据“缓存”批准其数值为 exact，遗留近似范围须显式保留。'
        if f == '_quickhull_once' and (s == 'off_line' or 'key=off_line' in s):
            return 'REMAINING_NUMERIC_CALLBACK_REWRITE_REQUIRED', 'off_line 是本函数局部命名 helper，对 v=_eg.vector(pts) 的 Fraction 差/cross/dot 返回精确平方距离；本身无舍入。但 max(cand,key=off_line) 仍传数值 callable，可改预计算 (off_line(i),-index,i) 保留 first tie，按要求 3 不宜豁免。'
        if f == '_merge_component_ring':
            return 'DATA_COLLECTION_OR_LABELING', 'boundary 是面环边界 int->int 字典；next(iter(boundary)) 保留既有插入序起点，随后只走离散索引环。此 builtin iter 不执行取出值，无数值构造。'
        if f == 'exact_convex_view' and (r in {'closed-callback', 'closed-syntax', 'closed-method-call'}):
            return 'DATA_COLLECTION_OR_LABELING', 'lambda 只把源面环的顶点索引排序为 canonical tuple；set(ring).issubset(hint) 检查源面编号关联。两处无数值 callable 或几何距离重算，convex_hull 的数值正确性仍独立分析。'
        if f == 'Polyhedron._find_interior_point':
            return 'CANDIDATE_CHECKED_PREDICATE_ONLY', 'p/c 是 float 生成的内点候选，但该节点以 point_in_polyhedron(candidate,self,0) 的精确给定坐标分类批准“此点在内”后才返回。它不是精确形心/理想偏移构造；候选生成仍可能失败，不能将这条 exact predicate 洗白整个近似生成函数。'
        if f == '_contact_cone_witness':
            return 'CANDIDATE_CHECKED_PREDICATE_ONLY', '此遗留 helper 用近似方向和 eps 提出 q，只有两个 point_in_polyhedron(q,body,tol)==1 才返回该实际点。支持的只是候选为内点的证书，未证明候选搜索完备或位移精确；当前主 polyhedra_overlap 直接 exact_geom.surface_overlap，未用该遗留链。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', '该 direct call 通往 exact_geom Fraction/int 原坐标谓词、精确 hull/共面环合并或 exact_convex_view；_quickhull_once 在 v=_eg.vector(pts) 上选基/判可见性，返回原 pts 而不构造舍入点。必须补足 count/iterator/local-key 的源传递摘要，不能按“exact”命名或整个 geom3 模块批准。'
    if file == 'kernel3d/interlock.py':
        if f == '_candidates' and r in {'closed-callable-value', 'closed-namespace-value'}:
            return 'CACHE_IDENTITY_NOT_DISPATCH', '_candidates 的 implementations 元组仅进入 _CandidateSnapshot.signature 作缓存身份；_candidates_cached 现直接调用 _candidates_uncached，未从 signature 取 callable 执行。保持身份是为了 monkeypatch 注入可穿透缓存，不是后门数值 dispatcher。'
        if f == '_prior_intervals':
            return 'PROOF_CONTROL_FLOW_GAP', 'times/height 是 surface_events 的 Fraction 时间，left 从 F(0) 起，yield (left,right,(left+right)/2) 精确表示每个先前开区间的中点。没有 float 时间聚类或 yield callable。'
        if r == 'closed-data-attribute':
            return 'TYPE_GUARDED_FIELD_DATA', 'event/e 来自 surface_events 返回的 SurfaceEvent 数据对象，time 是精确 Fraction 根，label 是来源特征 tuple。这里读属性作分组/输出标签，不执行属性值；不能把任意同名外部对象视为该类型。'
        if s == 'FACET_KINDS':
            return 'DECLARATION_OR_TYPE_DATA', 'FACET_KINDS 是 VF/FV/EE 字符串集合/元组常量，此处只检验 label[0] 成员资格，拒绝非仿射低维距离盖；不是 callable。'
        if f == '_exact_escape':
            return 'CACHE_IDENTITY_NOT_DISPATCH', '_exact_escape_cached 的最后三个函数对象参数只作缓存身份，body 直接调用 _nonpenetrating_at/_prior_intervals/surface_events。offset 逐项 F 转换，不能把未知函数返回值作为 exact input；此调用需参数敏感摘要而不是把 callable data 误作执行。'
        if f == 'dilatancy_profile':
            return 'APPROXIMATE_MODEL_OR_DIAGNOSTIC_NO_EXACT_APPROVAL', 'dilatancy_profile 以 cos/sin 和 s 的 float 采样 offset 作为新的给定模型，再求该模型的精确逃逸；不宣称理想连续方向/曲线的精确采样。直接调用本身不是动态执行，近似模型边界必须保留。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'escape_height 生产判定使用 Fraction offset/root、surface_events 全候选和每个先前开区间的 exact overlap 证书；frozen_lift 同样在 raw plane 完整有理 ratio 上构造。nominal cands/向上显示不替代 exact_height 进入判据，callee 的结构摘要缺口不应整体 waiver。'
    if file in {'limit.py', 'limit_multi.py'}:
        if f == '_ExactFloat.__new__':
            return 'IMMUTABLE_WITNESS_PROTOCOL', '先 Fraction(exact)，super().__new__ 只分配其 _fl(exact) 显示 float，object.__setattr__ 是绕过只读拦截完成一次 _exact 原值初始化；没有反射查找数值函数。精确证书与显示分开，后续 _rational 会核对显示一致性；普通 float 运算不继承见证。'
        if f == '_ExactFloat.__reduce__':
            return 'IMMUTABLE_WITNESS_PROTOCOL', '返回 (_ExactFloat,(self.exact,)) 是 Python copy/pickle 重建协议，保留精确见证而非只复制 rounded display。此 callable data 由序列化协议使用，不是数值算法任意高阶参数；不能推广为容器 callable 调度安全。'
        if f == '_ExactFloat.__setattr__':
            return 'VALIDATION_ERROR_PATH', 'AttributeError 阻止构造后更改 exact witness，是失败对象不是数值结果；不流入任何构造。'
        if f == '_rational':
            return 'TYPE_GUARDED_FIELD_DATA', 'v.exact 仅在 isinstance(v,_ExactFloat) 守卫且 float(v)==_fl(v.exact) 一致检查后返回，保留已有精确见证而非 Fraction(rounded_display) 伪造真值。外部普通 float 明确按新的给定数处理。'
        if f == '_lp_values':
            return 'DECLARATION_OR_TYPE_DATA', 'float 是 type(v) is float 的身份比较，未作为 callable 参数执行；显示值未改时沿用 exact 向量，否则显式 _rational 新数据。'
        if r == 'closed-callable-value':
            return 'DECLARATION_OR_TYPE_DATA', '本站点 OPTIMAL/UNBOUNDED 为 LP 状态字符串，_FLIP/_UNCERTAIN/_SELF_CHECK 为有限性/回查预算常数；作为条件比较或参数数据而非被调用函数。不得按“大写名字”普遍豁免，限定这些源码绑定。'
        if f.endswith('._solve'):
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'row 初值 Fraction(0)，Cx/live_v/dead_x/capx 为原派生量精确模型；row[j]+=/-= 是确切有理矩阵装配。maximise 的 **kw 只由 {} 或 {tol:lp_tol} 构造，exact=(AX,bX,c) 另行提交有理证书，浮点 A/b 仅候选。不是传 callable 或把浮点候选装成原数据。'
        if 'label()' in s:
            return 'DATA_COLLECTION_OR_LABELING', 'Cover3.label 只封装类型和特征编号供接触身份；法向/力矩派生量由独立精确构造处理，标签方法没有数值函数分派。'
        if f == 'contacts_from_covers_multi':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', '直接复用 contacts_from_covers，输入是 covers 的模型和给定 mu/side；该函数沿各 cover 原精确法向/面积见证与明确模型边界构造接触，不通过动态 callable。需分析 callee 的具体数据来源，不能把所有浮点 cover 自动当原始精确几何。'
    if file == 'lp.py':
        if f == '_exact_simplex.run':
            return 'PROOF_CONTROL_FLOW_GAP', 'nonlocal pivots 是整数枢轴计数器，闭包 run 中只 +=1，返回迭代统计/限制；矩阵和证书依旧 Fraction。没有捕获数值 callable 或在计数上构造几何。'
        if f == 'maximize':
            return 'PUBLIC_OPTION_FORWARDING', 'maximize 公开 **kw 原样转发 solve 支持的选项，先 pop exact 并精确换目标符号；不从 kw 取数值 callable 执行。solve 签名限定 tol/max_iter/exact 等数据；未知键由 Python TypeError 拒绝。保持 wrapper API，不能将任意 **kw call 作为通用安全形态。'
    if file == 'margin.py':
        if f in {'_resolved', '_resolved_cached'}:
            return 'CACHE_IDENTITY_NOT_DISPATCH', '_resolved_cached implementation/covers/predicate/... 参数仅缓存身份，实际只直接 _resolve；缓存数据以明确 Cover3 字段 tuple 冻结，返回新记录防止污染。该身份机制不是 callable dispatcher；_resolve 数值路径仍需独立源摘要。'
        if f in {'_witness_squared', '_surface_feature_squared'}:
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'FV/EV3 递归只交换 A/B 特征标签为 VF/VE3；_exact.vector 在原坐标各分量 Fraction 后才差分，完整面/棱/点平方距离保持有理，非 rounded Cover3 显示的平方。应支持有限递归摘要而非按函数名豁免。'
        if f == 'entrance_block_convex':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'pts 明确由 _exact.sub(_exact.vector(b),_exact.vector(a)) 构造，有理差点再送精确 hull，未先做 float b-a；此 direct call 仅因 hull 的结构摘要欠缺被报。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'margin 主判定使用原输入 exact overlap/特征平方；_penetration_within_window 对有理 contact_models 做 exact overlap，显示 witness 与预算仅报告。ctol/window 是显式查询模型并非隐藏派生几何输入，不能用 scope waiver 抹掉新的 rounded sink。'
    if file == 'oracle_construction.py':
        if r == 'closed-shadowed-intrinsic':
            return 'SOURCE_PROOF_GAP_EXACT_FLOW', '这是独立 oracle 本身 scalar/ratio/vector/sqrt/norm/unit_exact 的实际源码定义，不 import 生产构造或几何；完整 Fraction 表达式走独立 RN-even 中点证书/bit-search。必须按定义来源及调用实参推理，不能只信任名字（shadowed-intrinsic 防线对新同名函数仍须红）。'
        if f in {'_from_bits', '_bits', '_candidate_is_certified', 'assert_sqrt_rounding'}:
            return 'IEEE_BITCAST_CONSTRUCTION_BOUNDARY', '固定 >Q/>d 的 struct 位重解释读取相邻 binary64/尾位 parity；无舍入算术。中点上下界先 Fraction(nextafter/result)，再 exact 比较完整输入，边界 ties-even 用 bit parity，非将候选近似当真值。'
        if f in {'_candidate_positive', '_round_positive'}:
            return 'CANDIDATE_CERTIFIED_BY_EXACT_INPUT', 'Decimal80 sqrt/float(value) 只生成候选；_round_positive 每个返回前调用 _candidate_is_certified 对原 Fraction value 的完整 RN-even cell 作 exact 比较。未通过即 ordered bit-search（含溢/下溢处理），所以 Decimal 近似不决定答案。与 Dual.__pow__ 无该证书的近似分支不同。'
        if s == 'float':
            return 'DECLARATION_OR_TYPE_DATA', 'type(value) is float 的类型身份检查；有限 binary64 输入已经可精确表示，本分支直接返回原给定数，没有先派生再舍入。对 caller 已舍入派生输入仍须保留 taint，不能用该 identity path 洗白。'
        return 'SOURCE_PROOF_GAP_EXACT_FLOW', 'scalar_exact/sqrt_exact 分别将完整 Fraction 输入送 _round_positive(power=1/2)；该实现候选必须通过原 rational 输入中点证书，否则精确 bit-search。仅此已阅读的源调用边界，不是对所有名字带 exact 的函数豁免。'
    if file in {'predicates.py', 'rational3.py'}:
        return 'DECLARATION_OR_TYPE_DATA', 'Fraction/float 仅用于 isinstance/type identity 的类型分支；rational3 已是 Fraction 元素时保留原值，否则转换原给定分量。没有引用后执行的 callable，也未据类型名允许先 rounded 几何差分。'
    if file == 'readers/bdda3d.py':
        return 'DATA_SERIALIZATION_REFLECTION', 'record_from_entrance 按导出的字典逐字段解析 int/float/枚举/Feature 身份并保留 extra，来源数值定义输入模型；不先算几何差值/开方，也不把外部代码当 callable 执行。'
    if file == 'readers/bdda_df.py':
        if f == 'read_verts_csv':
            return 'DATA_COLLECTION_OR_LABELING', 'out 是显式 {} 构造的三级 int-key 字典，setdefault 仅建立 step/block/vertex 分组；x/y 从 CSV 解析作为给定坐标，没有派生数值 callable。'
        return 'DATA_COLLECTION_OR_LABELING', 'load_step_geometries 读取给定 CSV，按 step/block 建索引、去重复并规范环向；此 direct loader call 不执行传入数值 callable，坐标是外部数据模型。其内部数值判断仍单独分析，不能因是读取器全文件豁免。'
    if file == 'readers/bdda_geom.py':
        if 'update' in s:
            return 'DATA_COLLECTION_OR_LABELING', 'sg.alias 明确为 int 顶点别名 dict，alias 来自 strip_duplicate_vertices 的编号映射；update 合并身份元数据，不运行值或构造数值。'
        return 'DATA_CONTAINER_FACTORY', 'defaultdict(lambda:defaultdict(list)) 的 lambda 只分配容器，list 是零参数空列表工厂；没有捕获/调用数值函数、无算术返回值。读取的 float x/y 是新的输入坐标数据，不能将此容器工厂扩成任意 callback 豁免。'
    raise AssertionError((p, f, r, s))


def main():
    values = json.loads((HERE/'src_structural_candidates.json').read_text(encoding='utf8'))
    sources, node_sets = {}, {}
    for p in sorted({v['path'] for v in values}):
        data = (ROOT/p).read_bytes()
        text = data.decode('utf-8-sig')
        tree = ast.parse(text, filename=p)
        sources[p] = hashlib.sha256(data).hexdigest()
        # Skip attributes; exactly matches the scanner's site node encoding.
        node_sets[p] = {ast.dump(n, include_attributes=False) for n in ast.walk(tree)}
    items = []
    for v in values:
        disposition, reason = classify(v)
        items.append({
            **{k:v[k] for k in ('path','function','line','rule','node','source')},
            'reason': '具体节点：'+v['source']+'。'+reason,
            'disposition': disposition,
            'current_ast_node_present': v['node'] in node_sets[v['path']],
            'source_sha256_at_review': sources[v['path']],
            'formal_exception_approved': False,
            'scope_boundary': 'One recorded AST site and its inspected source scope only; no file/function/rule blanket allowlist.',
        })
    missing = [v for v in items if not v['current_ast_node_present']]
    counts = dict(sorted(Counter(v['disposition'] for v in items).items()))
    payload = {
        'input':'raw_scan_round4.json',
        'input_subset':'src_structural_candidates.json',
        'filter':'path starts src/eab/, rule starts closed-, excluding closed-rounded-construction / closed-unproved-arithmetic / closed-reduction / closed-rounded-call',
        'review_scope':'Read-only review of each recorded site against actual source and relevant callees; NOT approval or policy generation.',
        'count':len(items), 'by_disposition':counts,
        'by_rule':dict(sorted(Counter(v['rule'] for v in items).items())),
        'reviewed_source_files':len(sources),
        'current_ast_missing_count':len(missing),
        'missing_ast_sites':[{k:v[k] for k in ('path','function','line','rule','source')} for v in missing],
        'independence_note':'Reviewer earlier performed mechanical dynamic-call rewrites; this is a source-site review, not independent G6. Former 16936 waivers were not consulted.',
        'approval_note':'No formal exceptions approved. SOURCE_PROOF_GAP requires analyzer repair; remaining numerical callbacks require rewrite; approximate/diagnostic categories explicitly carry no exactness approval.',
        'source_hash_use':'Evidence snapshot only, never a dependency_snapshot or cross-file waiver lock.',
        'items':items,
    }
    (HERE/'src_structural_review.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    lines = ['# R12FIXb：src structural 逐站点只读复核','',
             f'- 输入：`raw_scan_round4.json`；非 numerical `closed-*` 共 **{len(items)}** 项 / **{len(sources)}** 个源码文件。',
             '- 每项包含实际 path/function/rule/node/source、局部理由与 disposition；**正式例外批准数为 0**。',
             '- 未读取旧 16936 豁免作为审批依据；不是独立 G6（本审查者此前负责机械简单化）。',
             '- 文件哈希仅是当时核证证据，不作 policy 依赖快照；函数/节点改变后须重新对照审查，不连带锁定无关文件。',
             f'- 当前 AST 不再存在：{len(missing)} 项（若并行已改写，详见 JSON，不能移植旧节点理由）。','',
             '## 分类计数','', '| 分类 | 数量 |','|---|---:|']
    lines += [f'| {k} | {n} |' for k,n in counts.items()]
    lines += ['', '## 未完成的必要边界', '',
              '- SOURCE_PROOF_GAP：已沿源追踪的 Fraction/int、类型守卫、迭代器/递归摘要缺口应修分析器，不以成批 waiver 代替。',
              '- 三处 cmp_to_key 数值角序比较、geom3._quickhull_once 的 off_line key、Dual.__rsub__ dunder 直接访问均可继续机械简单化；此轮只读没有改数学算法。',
              '- central_difference 的外部 f 是公开 G3 诊断 API；不能证明任意 f 内部无禁止模式，必要边界不得叙述成全程序保证。',
              '- Dual 一般非半整数 power 使用 Decimal80 近似，与 oracle_construction 的候选+原输入 exact midpoint certificate 不同；不得合并为“Decimal 安全”。',
              '- legacy/随机采样/首入 brute 只批准其诊断或候选身份，没有精确构造/搜索完备性批准。',
              '- 缓存 implementation 函数身份已核查不被执行；新插入容器 callable 调度仍须红。',
              '', '## 可复核文件','',
              '- `src_structural_review.json`：每节点完整记录。',
              '- `write_src_structural_review.py`：固定的逐范围人工分类映射 + AST 存在性核查；**不是生成允许策略的工具**。',
              '- 主报告与最终 static policy 是否采用/拒绝记录由根代理负责。','']
    (HERE/'src_structural_review.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps({k:payload[k] for k in ('count','by_disposition','reviewed_source_files','current_ast_missing_count')},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
