"""Write G6F reviewer-only artifacts. No tracked file is touched."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'review'
def log(name):return (R/'logs'/name).read_text(encoding='utf-8')
findings=[
 {'id':'G6F-3D-01','severity':'critical','file:line':'src/eab/kernel3d/geom3.py:1118-1120',
  'summary':'可变 canonical convex view 以别名泄漏缓存；只改返回视图，未改变源数据却使源的精确成员与相交静默答错。',
  'failure_scenario':'P 为 [-1,1]^3 的合法朝外三角表面，H=exact_convex_view(P)，H is not P。将 H.verts 原地平移 +100，P 的 verts/faces 原字节内容不变。精确源成员由 1 变 -1，P 与内含半边长0.5盒的 exact_convex_overlap 报 -1；独立区间积真值均为1，新建等效源对象也仍答1。两表面在编辑前后均合法；不是修改源模型后的预期变化。',
  'how_to_reproduce':'cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/solid_convex_cache_alias.py',
  'repro_path':'review/repro/solid_convex_cache_alias.py','log_path':'review/logs/solid_convex_cache_alias.log',
  'suggested_fix':'将缓存 canonical payload 设为不可变、返回隔离副本，或在源取回缓存时同时核验缓存产物内容签名；增加改返回视图但源不变的成员与相交回归及牙。',
  'verified_output':log('solid_convex_cache_alias.log')},
 {'id':'G6F-3D-02','severity':'major','file:line':'src/eab/kernel3d/geom3.py:1125-1129',
  'summary':'凸视图保号捷径只比面顶点集合，不校验面绕向，违背显式凸 API 与面提示无关的 conv(vertices) 契约。',
  'failure_scenario':'P 顶点恰为 [-1,1]^3 八角点，仅将 top 面提示反绕；Q 为原点半边长1/2盒。explicit-convex API 保留 P is exact_convex_view(P)，exact_point_in_convex_polyhedron(0,P)=-1，membership_convex3(Q,P,0)=-1；独立顶点凸包真值均1；同一八顶点用空 faces 提示时两者都答1。一般 surface API 不在复现中调用，反绕面提示不满足一般 surface 朝外前提，但本发现针对明确只按顶点凸包、面为提示的显式凸契约（geom3.py:1155、1170，exact_3d_design §1）。',
  'how_to_reproduce':'cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/solid_convex_face_hint.py',
  'repro_path':'review/repro/solid_convex_face_hint.py','log_path':'review/logs/solid_convex_face_hint.log',
  'suggested_fix':'保号捷径仍应使用已生成 canonical outward supporting ring，或精确核验源面平面、简单环、支撑面及朝外绕向后才能复用；面提示不得改变顶点集凸模型的答案。',
  'verified_output':log('solid_convex_face_hint.log')},
 {'id':'G6F-3D-03','severity':'major','file:line':'src/eab/kernel3d/geom3.py:430-443',
  'summary':'is_convex/reflex_edges 即使调用方 tol=0 仍以隐式二面角噪声带吞掉真实凹棱，返回错误的几何谓词结果。',
  'failure_scenario':'朝外闭合嵌入棱柱的 x-z 截面为 (0,0),(2,0),(2,1),(1,1-eps),(0,1)，y∈[-1,1]。取 eps=2^-50（原点，所有坐标为可精确表达binary64），或 eps=2^-24 且 x 平移1e8（Fraction保持原数）。两 roof 峰中点高1，而精确屋顶中点高1-eps，严格在实体外，故实体非凸且有凹棱。当前 is_convex(tol=0)=True、reflex_edges(tol=0)=[]；manifold_issues=[]。docstring 已说明内部加noise，但它不是调用方显式窗，也没有精确分类兜底。本发现不声称默认 surface_overlap 或 E5b 精确求解走该路径，检索 src 中无生产调用。',
  'how_to_reproduce':'cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/solid_hidden_convexity.py',
  'repro_path':'review/repro/solid_hidden_convexity.py','log_path':'review/logs/solid_hidden_convexity.log',
  'suggested_fix':'按未归一化原数据有理二面角符号/全支撑平面分类；显式 tol 正窗若保留应另报近边界，而不能在 tol=0 把真实凹答为凸；加入binary64微凹及工程坐标元门。',
  'verified_output':log('solid_hidden_convexity.log')},
 {'id':'G6F-3D-04','severity':'minor','file:line':'src/eab/kernel3d/interlock.py:175-181; src/eab/kernel3d/geom3.py:380-381',
  'summary':'精确逃逸前置 nominal 浮点平移拒绝合法 Fraction 微尺度输入；等值零偏移仅 int→float 就造成零长棱错误。',
  'failure_scenario':'两个合法精确盒为原点盒 A 与 z=3/4 盒 B，半边长各1/2；统一scale=1e-9、坐标origin=1e8，以Fraction保存。独立区间积最早竖向脱离根为7/4000000000。offset=(0,0,0)返回该精确根；完全等值的offset=(0.,0.,0.)使 nominal At=A.translated(offset) 将微特征舍成相同float，抛ValueError zero-length edge，精确求解器未运行。没有静默返回错误根，因此按minor计。',
  'how_to_reproduce':'cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/geom3_nominal_translation_loss.py',
  'repro_path':'review/repro/geom3_nominal_translation_loss.py','log_path':'review/logs/geom3_nominal_translation_loss.log',
  'suggested_fix':'nominal 报告构造须保留非Dual原坐标精确仿射值，或让显示候选构造失败不会阻断权威精确求解；增加等值标量类型与混合尺度门。',
  'verified_output':log('geom3_nominal_translation_loss.log')}
]
(R/'notes'/'geom3_findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# WO-G6F 三维 / 凹几何 / 互锁 / 窗口分审结果','',
 '本分审为审查，不修实现代码；HEAD=2f6c518。当前自行确认 **1 critical / 2 major / 1 minor**。分审不能据此批准 M0 退出。所有复现仅写 review/；没有跟踪文件或任何 Git 写操作。', '',
 '## 续做边界','',
 '先读 review/notes/solid_replay_results.json、solid_replay_sources.txt 和全部 solid* 脚本。上次已完成的12条原输入重放（原序号7、24、25、28、29、31、34、37、40、42、43、44）沿用原日志，不重跑；这些是上次运行证据，不冒称当前新实验。当前重新跑并加强此前未完成的三个候选脚本；上次已有脚本名不等于上次已确认结论。极端符号过滤原脚本当前再跑。', '',
 '## 确认发现', '',
 '|ID|级别|位置|一句话结论|复现|','|---|---|---|---|---|']
for f in findings:
    p=f['repro_path'];lines.append(f"|{f['id']}|{f['severity']}|`{f['file:line']}`|{f['summary']}|[脚本](file:///D:/eab-wt/g6f/{p})|")
for f in findings:
    lines.extend(['',f"### {f['id']} — {f['severity']}",'',f['failure_scenario'],'',f"建议：{f['suggested_fix']}",'',f"运行：[脚本](file:///D:/eab-wt/g6f/{f['repro_path']}) · [当前实跑日志](file:///D:/eab-wt/g6f/{f['log_path']})",'', '```text', f['verified_output'].strip(), '```'])
lines.extend(['','## 独立压力测试与窗口可靠性', '',
 '独立 oracle 均由本审查自行书写，不导入被测几何 primitive；只用原坐标/Fraction 标量、确切矩形/盒区间积、投影 winding、自写点段平方距离。source setters/constructors只是输入生成，不作为 oracle。', '',
 '- 一般有效凹 L 柱 + 含内向 cavity 内表面的中空盒：132格、3个精确刚体轴循环姿态/单位尺度，包含1e-9尺度在1e8坐标；成员/相交的区间积并真值全部一致。覆盖的是矩形并类，不冒称任意一般凹表面。',
 '- polygon_locate 区间浮点快路：900格，Fraction指数-2000、-1074、-1022、-600、-100、0、100、600、1020、2000，加1e8偏移；自写winding与3D边距oracle全部一致。超出binary64转换范围会退精确算术，未见快路错号。',
 '- 独立orient3d/cross2/dot2：原脚本当前12,000随机极端指数样本，含次正规/下溢/上溢中间量；三个错误计数均0。不是对所有输入的证明。',
 '- 显式窗口：75个盒对、12个被接受模型；独立区间积检查每个模型的状态，并精确量实际六轴位移平方=w²；对每个通过星核，核对相同homothety比例与全顶点最大径向段平方≤w²。盒面上各点为顶点凸组合，范数凸性因此对连续壳成立，并非只抽查接触点。六轴与薄壳可靠性未找到反例。',
 '- 最早逃逸：中空盒的非单调禁止区间（先脱离进 cavity、随后再碰上壁）24格；20格与自写完整1D禁区间并最早端点一致，4格因G6F-3D-04在nominal前置拒答。此处把同一真实输入保持到Fraction；不以舍入到float后的退化体作为oracle。', '',
 '[完整独立压力脚本](file:///D:/eab-wt/g6f/review/repro/geom3_independent_stress.py) · [压力日志](file:///D:/eab-wt/g6f/review/logs/geom3_independent_stress.log) · [非单调扫掠脚本](file:///D:/eab-wt/g6f/review/repro/geom3_motion_product_oracle.py) · [扫掠日志](file:///D:/eab-wt/g6f/review/logs/geom3_motion_product_oracle.log)', '',
 '窗口证明的代码链（exact_sweep.star_core/contact_models → exact surface overlap → margin/interlock OR）与当前docs/exact_3d_design数学命题一致：星心严格在每个朝外三角平面内侧；原实体的每条径向边界壳段最多alpha*R≤w；六轴成功给一条长度w的刚体脱离证书。仅在有效朝外闭合嵌入表面前提内成立。坐标轴与L1壳旋转依赖、短斜向脱离漏检、薄壳接受而整体PD很大均已明示，是限制，不计缺陷。', '',
 '## 源码与背景覆盖', '',
 '逐函数读过 kernel3d 全部10个模块：__init__.py、geom3.py、covers3.py、exact_geom.py、exact_sweep.py、frozen.py、interlock.py、entrance3.py、g03.py、g03_exact.py。另读 margin.py 的150–440行（缓存、窗口、状态、证据和排序路径）、tests/test_e5b_polyhedron_cache.py、test_perf_contact_window.py、test_entrance3_exact.py。背景读 exact_3d_design 全文，exact_predicates_plan、README 的相关契约段，E3E4相关E3/E4口径与迁移说明，E5b全文与PERF全文。', '',
 '- exact_geom 的interval过滤不确定就回Fraction；清分母整数SAT、parity、距离属于精确代数不是浮点filter；完整arrangement兜底在凸/星核快速证书失败时确实存在。',
 '- interlock 的nz=1e-12/noise、r簇、gtol带只决定nominal导数标签报告，不决定exact_height；_exact_escape有每个根处非贯入及此前全部事件开区间核验。因此未误把这类报告分支算成精确根错。G6F-3D-04是报告构造先失败的问题。',
 '- geom3旧_contact_cone_witness/_gordan_direction/_active_normals等噪声路径已不在polyhedra_overlap决策链，不因静态grep而虚报核心贯入缺陷。is_convex/reflex_edges是仍可公开调用的错误谓词，且没有精确fallback。',
 '- g03_exact原语与被测geom3/covers3无import共享；G0票1先冻结source坐标再canonicalize，票2双向support集合、票3全部extreme点；当前代码已无ambiguous/low_e豁免。旧g0_distance_completeness3仍明确承认shared face_polygon_locate，只对法锥筛选有牙，不能当通用独立主oracle。', '',
 '## 未确认 / 不计数', '',
 '- 没有找到interval过滤、六轴/薄壳可靠性或上述矩形并类一般surface_overlap的静默反例；零错试验不等于普适正确性证明。',
 '- 全局任意凹体最短出口未实现，shortest_exit3当前设计已明示局部facet最浅，不将这一已声明限制重新计为算法缺陷；README未限定的标题文字由文档审查方另核。',
 '- exact_convex_view面提示发现仅适用于显式conv(vertices)契约；不把反绕面当合法一般surface输入。', '',
 '## 完整性批评', '',
 '本分审没读二维、LP/limit、读写器/适配器全部源文件；这由其他镜头负责。未逐格审所有3D测试迁移台账assert AST，未复制仓库做新的大规模变异；保留已有上次重放证据和当前真实数值反例。未对任意自交/非流形/零体积非法输入作结果保证，也未给一般非星形凹面独立体积oracle。未穷举所有64bit谓词输入或任意用户自定义可变numeric对象。理论00/01/03/07正本全量核对由总审/文档镜头负责，本分审只核了当前三维设计的几何语义、星核与窗口证明。全套8582节点结果由总审独立运行记载，不以本分审小脚本替代。', '',
 '[机读发现](file:///D:/eab-wt/g6f/review/notes/geom3_findings.json)','',
 'G6F_GEOM3_DONE critical=1 major=2 minor=1'])
(R/'notes'/'geom3_final.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('WROTE review/notes/geom3_findings.json; review/notes/geom3_final.md')
