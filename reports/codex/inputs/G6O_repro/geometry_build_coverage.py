from pathlib import Path
import json,ast
ROOT=Path(__file__).resolve().parents[2]
e=ROOT/'review/evidence'
grid=json.loads((e/'geometry_escape_nonfinite.json').read_text(encoding='utf-8'))
finding={
 'id':'G6O-GEOM-01','severity':'minor','file_line':'src/eab/kernel3d/interlock.py:308-310','file':'src/eab/kernel3d/interlock.py','line':310,
 'conclusion':'有限精确逃逸根在上界RN舍入胞内时，height的向上nextafter越过最终构造边界而静默发布inf；权威exact_height与非贯入状态仍正确。',
 'failure_scenario':'设M=sys.float_info.max的精确Fraction，H=M+1。A=[-1/8,1/8]^2×[0,H/2]，B=[-1/4,1/4]^2×[-1/4,H]，offset=(0,0,0)，tol=0。两体均为有限有理、朝外闭合凸盒。独立z区间证明最早非贯入抬升为H。scalar_rational(H)仍为有限M；escape_height_covers却返回height=inf、exact_height=H、nonpenetrating_state=0。H超过最大float，向上有限显示已不可能，应具名拒答或明确标注专属overflow合同，不能把inf当普通有限物理高度发布。',
 'how_to_reproduce':'cd D:/eab-wt/g6o; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/geometry_escape_nonfinite.py  # 输出六格，三格silent_nonfinite；最后目标AssertionError，exit=1',
 'repro_path':'review/repro/geometry_escape_nonfinite.py',
 'suggested_fix':'保持正确的exact_height/exact_offset/状态证书不变；向上nextafter之后重新执行最终有限输出边界检查，超界抛含escape height量名的ConstructionDomainError，或另设计明确标记overflow的显示合同。补M-1、M、M+1和RN溢出中点两侧门，不可把M当H的向上界。',
 'verified_output':json.dumps({'max_plus_1':grid['rows'][2],'silent_nonfinite_count':grid['silent_nonfinite_count'],'test_exit_code':1,'target_assertion':'finite rational escape height must not be silently published as inf; use a named support-domain failure'},ensure_ascii=False,indent=2),
 'severity_rationale':'IEEE扩展向上舍入本身正确，权威exact root/状态正确；现有有限输出/具名异常合同未声明该height infinity例外。按主审第二意见裁为minor接口支持域/文案张力，不声称物理判定或精确根算错。',
 'contract_references':['docs/r14fix_design_sync.md §1：坐标/平移完整有理路径保留全部有限有理数；长度/距离最终量必须位于有限非零RN-even胞。','docs/exact_predicates_plan.md R13FIXb §1–2：输出超界统一ConstructionDomainError；RN-even正上界严格小于(max_binary64+2^1024)/2。','src/eab/kernel3d/interlock.py escape_height_covers docstring：height是rounded upward的binary64显示，并非无界/退化状态哨兵。'],
 'evidence_paths':['review/evidence/geometry_escape_nonfinite.json','review/logs/geometry_escape_nonfinite.txt']
}
(e/'geometry_findings.json').write_text(json.dumps([finding],ensure_ascii=False,indent=2),encoding='utf-8')

files=list((ROOT/'src/eab/kernel2d').glob('*.py'))+list((ROOT/'src/eab/kernel3d').glob('*.py'))+[ROOT/'src/eab/predicates.py',ROOT/'src/eab/margin.py']
caches=[]
for file in files:
    source=file.read_text(encoding='utf-8-sig');tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and any('lru_cache' in ast.unparse(d) for d in node.decorator_list):
            caches.append({'file':str(file.relative_to(ROOT)).replace('\\','/'),'line':node.lineno,'function':node.name,'signature':ast.unparse(node.args),'review':'Content-keyed tuple numeric payload inspected by function family; valid coordinate equality implies identical rational values. Not an exhaustive user-defined scalar/alias proof.'})
(e/'geometry_cache_inventory.json').write_text(json.dumps({'cache_functions':len(caches),'rows':caches,'measured_gate':'57 passed in 1.64s; test_e5b_polyhedron_cache/test_perf_contact_window/test_e5a2_integer_arithmetic/test_e5a2_bilinear_integer','limitations':'All public mutable container/scalar protocols were not exhaustively fuzzed.'},ensure_ascii=False,indent=2),encoding='utf-8')

report='''# WO-G6O 几何 / 过滤 / 缓存 / 接触窗口分审覆盖

对象：当前新鲜树 `D:/eab-wt/g6o`，HEAD `03a41b5`。只写本树 `review/`，未修改已跟踪文件、未做 git 写操作、未运行姊妹 exe。主审负责串行全套；本分审未另跑全套。

## 结论

本分审 **confirmed critical=0 / major=0 / minor=1**。G6O-GEOM-01 是实际生产API最终显示支持域/具名异常合同张力，不是静态门绕过或未经证明的猜测。权威精确逃逸根与非贯入状态正确；IEEE扩展向上舍入成 infinity 本身也正确，只是普通height的finite输出承诺没有声明这一例外。主审听取支持域第二意见后裁minor，不称其为物理判定或根计算错误。此条本身不阻止原0 critical / 0 major退出门，最终结论由主审其他发现决定；不撤销所有者既有M0历史退出决定。

## 已确认：G6O-GEOM-01

- `src/eab/kernel3d/interlock.py:308-310`：`scalar_rational(root)` 先合法返回最大float；随后 `math.nextafter(...,+inf)` 改成 infinity，未再核最终有限输出域。
- 精确 `M=sys.float_info.max`，`H=M+1`；A 为 `[-1/8,1/8]^2 × [0,H/2]`，B 为 `[-1/4,1/4]^2 × [-1/4,H]`，沿+z抬升。独立笛卡尔积与z开区间计算表明：初态严格重叠，所有 `0≤h<H` 重叠，`h=H` 仅相触，`h>H` 分离。都是有限有理输入，不受近似诊断专属 D400 盒限。
- 原输出：`RN_finite=true; returned_height="inf"; exact_height_matches_interval_root=true; nonpenetrating_state=0; n_candidates=0`。
- 六格边界重放：`M-1`、`M` 两格正常有限；`M+1`、`M+2^969`、RN溢出中点减1 三格静默infinity；RN溢出中点正确具名拒答。最终脚本的 `finite rational escape height must not be silently published as inf` 目标断言红，exit=1，不是setup失败。
- 这里**不存在正确有限向上舍入值**；不能建议直接返回M（会小于真根）。应最终具名拒答，或明确新增带overflow标记的显示合同。`exact_height` / `exact_offset` / 状态无需修改。

证据：[机读发现](file:///D:/eab-wt/g6o/review/evidence/geometry_findings.json)、[直接复现](file:///D:/eab-wt/g6o/review/repro/geometry_escape_nonfinite.py)、[六格数据](file:///D:/eab-wt/g6o/review/evidence/geometry_escape_nonfinite.json)、[原输出及断言](file:///D:/eab-wt/g6o/review/logs/geometry_escape_nonfinite.txt)。

## 镜头1：浮点分支 vs 精确声称

几何、margin、predicates 共19模块的 **1115条 AST 比较**按已读函数族分类，详见[逐站点分类](file:///D:/eab-wt/g6o/review/evidence/geometry_branch_inventory.json)。索引不是动态全路径数值证明，比较0.0也不代表左端真是float。

1. **允许的显式政策窗口**：二维法锥/长度/段内与成员报告带；三维法锥、extent、搜索窗、分離侧表面距离窗；接触六轴/薄壳窗口。分支以原输入Fraction或清分母整数的平方式比较；兼容参数不加隐式坐标噪声。`reflex_vertices.tol` 唯一几何新增diff为转换前binary64_argument，libm系数模型范围与分项合同相符。
2. **允许的保守过滤**：二维orient2d、cross2/dot2、三维orient3d；面投影/边窗的nextafter区间过滤。类型门保留混合int/Fraction值；上溢、下溢、不确定区间都退Fraction。72,000个独立符号对拍及1300个新旧投影窗口格零错，不把这称为全域误差界证明。
3. **构造/诊断或具名拒答**：norm/area/volume/normal量程、interior_point候选查找后精确验证、manifold平面度检查、margin见证误差界、near_labels、互锁nominal根/导数标签。exact sweep独立决定权威根，不受1e-12 n_z筛除影响。G6O-GEOM-01是这一层真实最终量程漏洞。
4. **历史私有浮点链，当前不决定公共答案**：geom3 `_gordan_direction` / `_min_norm_on_simplex` / `_contact_cone_witness` / `_active_normals` / `_edge_edge_contacts` / `_inward_vertex_direction` / `_ray_directions`；geom `_tri_axes`。读了相关段及src调用可达性，没有把它们含1e-12/1e-20的旧私有计算冒充现行完整精确实现，也没据此无反例计缺陷。
5. **读取前模型政策另列**：`readers/bdda_geom.strip_duplicate_vertices` 默认legacy去重/舍入地板会改变读入模型；已按主审提示单列，不算几何谓词偷偷使用噪声。

本分审未发现会改变当前默认几何状态答案的隐藏噪声带反例；这不是断言所有动态Python协议已经证明。

## 镜头2：过滤、缓存等价性

读核了完整内容key、Polyhedron顶点/面内容签名、精确凸view独立payload、内部cover记录拷贝、事件缓存的精确start/direction/t范围、互锁nominal候选numeric_types和实现身份key。数学等值的int/float/Fraction转换缓存最终仍为同一Fraction；_polygon_data缓存的区间宽窄可能影响快路效率，不改变Fraction后备结果。没有确认陈旧缓存/跨输入串用答案。

缓存函数索引：[geometry_cache_inventory.json](file:///D:/eab-wt/g6o/review/evidence/geometry_cache_inventory.json)。定向实际 `57 passed in 1.64s`：[日志](file:///D:/eab-wt/g6o/review/logs/geometry_cache_window_target.txt)，含公共Polyhedron可变数据失效、显式窗口证书、整数化原语等价门。没有把所有任意可变自定义标量协议都列为已覆盖。

## 镜头5：独立 Fraction 压力对拍

|脚本/参考路线|本树实测|结果|
|---|---|---|
|geometry_stress：内联有理行列式、二维自行凸包、三维支持面rank极点、面内仿射坐标|72,000符号比较；1,440凸二维成员；110三维极点集；600面内投影|零失配、零异常|
|geometry_union：正交单元实体的区间并、八象限局部拓扑、区间union swept根|126点成员、95相交、25拓扑E、30escape、20first|零失配、零异常|
|geometry_distances：笛卡尔积间隙平方与2D矩形并配置空间|1,080凹二维E、60首入、70距离、280膨胀|零失配、零异常|
|**本轮新写 geometry_fraction_hpoly**：四面体八个H不等式的平面三元组Cramer+有理rank；不使用SAT/hull/LP；线段QP active sets；Cartesian面窗|280 overlap、1,120成员、600线段平方距、700闭窗|零失配、零异常|

包含精确5-12-13/3-4-5旋转、尺度与坐标严重分离、大平移2^1000、特征尺度2^-1100、坐标/参数指数[-1500,1200]、次正规、近平行、共面/共线、重复云点、零长线段、凹L/U/C/ring/cavity、紧配seam。退化实体须仍满足API几何有效性，不以无效曲面要求函数给实体真值。

前四个脚本部分为只读g6n分审已独立编写oracle的当前树重放，报告明示复用，不冒充全为本轮首写；新Hpoly路径参考只用本脚本Fraction代数与独立建模，不共用生产几何原语。

关键日志：[新Hpoly输出](file:///D:/eab-wt/g6o/review/logs/geometry_fraction_hpoly.txt)、[predicate/凸包输出](file:///D:/eab-wt/g6o/review/logs/geometry_stress.txt)、[凹几何输出](file:///D:/eab-wt/g6o/review/logs/geometry_union.txt)、[距离/膨胀输出](file:///D:/eab-wt/g6o/review/logs/geometry_distances.txt)。

## 镜头6：接触窗口可靠性

读核 `star_core/contact_models` 与margin `_penetration_within_window`、interlock各model earliest-root。

- 六轴通过意味着确有某个±w坐标平移使内部不交，因此 **rho≤w**；不是正本01闭集PD。源盒区间参考独立，51个窗口格包括30六轴接受、6薄壳专属接受、15拒绝，零失配。
- 星心严格在每个朝外三角平面内；对有效嵌入曲面，这是star-kernel充分证书。Homothety比例α=min(w/R,1/2)，R=max顶点L1半径；面上凸组合的L1半径≤R，L2≤L1，故每条移除径向段≤αR≤w。核验了67个独立半空间/半径构造检查；双壁专属六格在六轴失败但薄壳通过，参考确证只承诺局部厚度。
- 接受原体/星核/六平移的OR，不把拒绝等价于PD>w。旋转依赖与封闭空腔rho/PD分离的旧门保留；本树test_perf_contact_window定向通过。本轮未给任意非星体必要充分窗口算法新声明。

[窗口自写区间数据](file:///D:/eab-wt/g6o/review/evidence/geometry_window_results.json)、[直接脚本](file:///D:/eab-wt/g6o/review/repro/geometry_window.py)。

## 镜头9：第五轮回归15条

按raw findings[] **0-based原序号**：6、25、26、27、28、29、30、33、36、37、39、40、41、42、43。全部在本树exit0，原始错答案/假盖/误凸化/抛错未再重现。

- 39的默认eps不再NameError；它手工逐点float差生成的rounded hull仍返回hull_anomaly。这是与原精确差点数据不同的输入模型，不是生产g0的漏检；现g0_convex3先冻结输入，独立精确difference_hull。
- 41原roof经刚体float舍入后精确凸性False/True；旧“实际两体都凸”前提不成立。当前g0是显式conv(vertex-set)模型检查，不能把其通过冒充一般折面表面绿。
- 33 covers/brute重放的谓词共享，仅为佐证；另有30个区间并独立escape格和20个独立首入格。

[完整逐条原输出](file:///D:/eab-wt/g6o/review/evidence/geometry_g6e_replay.json)。主审另独立重放同15脚本，不用上轮结果冒充本轮执行。

## 镜头3/4/8的辅助读核与边界

读 E2–PERF 相关oracle/迁移/变异/窗口台账；核2D独立SAT、全投影support、Jarvis票三，3D g03_exact全整数SAT/独立hull与g03_surface_oracle自实现plane/winding/投影耳切。只共享坐标/明确定义模型，不共用生产helper。brute_feature_distance、first_entrance_brute、escape_height_brute共享生产路径已明示佐证，不能算独立主oracle。

`git diff 878d4f0..HEAD` 几何代码只改kernel2d/geom.reflex_vertices转换前binary64_argument；原零tol分支符号没改。新r14_domain相关补门由主审支持域路径执行。本分审**没有逐项旧红新绿重做全部E2–PERF迁移变异**，不据有限索引宣布全部门从未变弱。

已读README/两份exact设计/canon_map的当前几何语义、接触窗、限制及相关历史段；外部01全文核凸输入定义/闭集PD/首入，03相关裕度段。外部00、07全文和canon_map全声称审计由主审另路负责，本分审未自行完整细读，不能据本分工声称正本全闭合。

## 未确认、不计数与完整性批评

1. 巨大Fraction contact_window进入math.isfinite可能原生OverflowError；没有本分审已确认错答案，已交支持域审查，不扩充major。
2. 极小几何body_distance/inflated_membership可先因rounding_floor不可表达具名拒答；当前138项清单也明确下游构造例外边界。不是本轮新静默错误，不据全有限口号再次计入发现。
3. margin_contacts贯入早返回0.0-delta最终胞问题已交支持域分审，避免重复计数；负delta非球半径前提不能拿来报几何critical。
4. 细核主函数族：predicates；kernel2d geom/exact/covers/entrance；kernel3d exact_geom/covers3/exact_sweep/entrance_topology/entrance3/interlock；margin resolved/window/distance；geom3 hull/convex-view/alias/质量/表面入口；g0/g03独立oracle与主票；frozen的方向、原坐标jet、比值路径。**没有重新逐式证明全部frozen Dual导数**，geom3已失去公共可达性的历史私有浮点链只读相关段与调用搜索。
5. 本分审未細读src/eab/dual.py、lp.py、limit.py、limit_multi.py全部实现，ContactRecord/readers/adapters/tools和静态分析器只是相关入口或索引；它们由主审其他路负责。不是39模块全行审计，也不把1115比较索引当全域认证。
6. 任意非星凹体/任意折面/全局E完备性、所有瞬态路径、任意自定义数值协议/可变别名、资源复杂度、跨平台libm均未穷尽。有限对拍零错只证明所列输入族，不是benchmark/工程动力学验证。
7. 审查脚本开发有两类已修输入错误：一次不存在的pytest文件名导致no tests ran；一次PowerShell Python-c引号失败。修正后57格绿；这些不算产品红。最初小A大B溢出探针合法地触发巨大投影参数ConstructionDomainError，改用两长盒才得到现有生产inf复现，不拿前者凑发现。

GEOMETRY_DONE critical=0 major=0 minor=1
'''
(ROOT/'review/evidence/geometry_coverage.md').write_text(report,encoding='utf-8')
print('geometry_findings=1; comparison_rows=1115; cache_functions='+str(len(caches)))
