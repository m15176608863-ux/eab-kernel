"""Explicit review ledger; coverage is assigned only after reading the return contract."""
import ast,json
from pathlib import Path
ROOT=Path.cwd(); out=ROOT/'reports/codex/R13FIXb_evidence/kernel'
old=json.loads((ROOT/'reports/codex/R13FIX_evidence/construction/public_api_inventory.json').read_text(encoding='utf8'))
rows=[r for r in old if r['public'] and r['kind']=='callable' and r['status'].startswith('未确认') and r['api'].startswith(('eab.kernel2d.','eab.kernel3d.')) and r['path'] not in ('src/eab/kernel2d/geom.py','src/eab/kernel3d/geom3.py')]
mapping={};proofs={}
def assign(test,names,description):
 for n in names.split():
  assert n not in mapping,n
  mapping[n]=(test,description)
def proof(name,text):proofs[name]=text
assign('test_cover_selector_constraints_margin_and_enumeration_numeric_fields', 'kernel2d.covers.first_entrance_for_vertex kernel3d.covers3.cone_constraints kernel3d.covers3.cone_intersection_margin kernel3d.covers3.enumerate_covers3', '非立方盒：独立支持集确定方向；Fraction投影/线交叉；每个见证分量、参数、gap、面积和精确证书逐值；48个枚举盖，三档。锥约束六向量逐分量；margin=sqrt(1/3)，noise=5*64*eps。')
assign('test_exact_entrance_block_and_float_vertices_each_component','kernel2d.covers.convex_entrance_block kernel2d.exact.entrance_block_exact','解析矩形Minkowski端点和FF配对；每个start/direction坐标逐值；有理非对称a0平移后只最终RN。')
assign('test_brute_entrance_2d_and_3d_independent_cartesian_time_bound','kernel2d.entrance.first_entrance_brute kernel3d.entrance3.first_entrance_brute','独立坐标区间重叠首时刻t=3；最终有理二分上界最多高于真值一ulp，三档；仅抽样佐证，孤立切触/未分辨窄窗口仍可能漏。')
assign('test_exact_area_nondyadic_raw_values_match_shoelace','kernel2d.exact.signed_area2','非二进制有理三角形，用独立shoelace逐值核对双面积。')
assign('test_2d_exact_oracle_quantities_match_independent_formulas','kernel2d.g0.char_length kernel2d.g0.brute_ray_exit kernel2d.g0_oracle.sqrt_display kernel2d.g0_oracle.points kernel2d.g0_oracle.translate kernel2d.g0_oracle.turn kernel2d.g0_oracle.segment_square kernel2d.g0_oracle.distance kernel2d.g0_oracle.ray_exit','内联Fraction差/积/投影；解析矩形距离=3s、出口t=1、包围盒对角=sqrt(5)s，逐分量和索引参数比较；sqrt参考Decimal250位。')
assign('test_random_coordinate_samplers_round_only_final_affine_value','kernel2d.g0.sample_translations kernel3d.g03.sample_translations3','使用相同已声明PRNG的独立序列；每个draw视为精确binary64系数；Fraction包围盒、padding、仿射表达式只最终RN。')
assign('test_g0_success_report_numeric_fields_are_analytic','kernel2d.g0.g0_convex kernel2d.g0.g0_distance_completeness kernel2d.g0.g0_exit_completeness kernel3d.g03.g0_convex3 kernel3d.g03.g0_distance_completeness3','解析矩形/非立方盒正常审计返回完整dataclass字典逐字段；counts按4边/6面/8顶点/12棱推导；该族witness误差=0，不外推所有失效报告分支。')
assign('test_random_polygon_constructed_coordinates_have_independent_rng_reference','kernel2d.g0.random_convex_polygon','独立RNG系数的精确仿射坐标；不用生产凸包，以全点支撑线检验极点集合逐坐标。scale独立集中检查，正数[2^-400,2^400]。')
assign('test_exact_public_vector_arithmetic_matches_inline_rational','kernel3d.exact_geom.vector kernel3d.exact_geom.sub kernel3d.exact_geom.add kernel3d.exact_geom.mul kernel3d.exact_geom.dot kernel3d.exact_geom.cross kernel3d.exact_geom.normal kernel3d.g03_exact.qpoint kernel3d.g03_exact.minus kernel3d.g03_exact.scalar kernel3d.g03_exact.wedge kernel3d.g03_exact.volume kernel3d.g03_surface_oracle.minus kernel3d.g03_surface_oracle.dot kernel3d.g03_surface_oracle.cross','非二进制系数转float后，以其精确Fraction值内联加减点积叉积行列式；exact_geom raw float结果按既有协议最终RN，其余有理结果精确逐值；normal先精确化输入。')
assign('test_exact_surface_constructions_and_intersections','kernel3d.exact_geom.triangles kernel3d.exact_geom.segment_triangle kernel3d.exact_geom.triangle_intersection kernel3d.exact_sweep.translate_exact kernel3d.exact_sweep.star_core kernel3d.exact_sweep.contact_models','解析盒逐三角形原坐标；平面线交点和t=1/3；嵌套三角交集；star_core解析中心及alpha=1/6；所有9种contact_models逐坐标/偏移/保留面索引。')
assign('test_surface_events_each_exact_time_and_normal','kernel3d.exact_sweep.surface_events','盒z向事件全集t={2,5,8}，每条事件normal由标签源点内联叉积；另有非二进制时刻{2/21,11/21,20/21}门。')
assign('test_facet_vote_anomaly_numeric_payload_has_independent_plane_reference','kernel3d.g03.facet_vote3','故意提供正卦限盒hull代替差体，三个坐标零平面h不等于maxB-minA；逐值核对返回3个primitive integer法向及计数；正常报告另测。')
assign('test_oracle_hulls_planes_sat_and_boundary_quantities','kernel3d.g03_exact.plane_key kernel3d.g03_exact.hull kernel3d.g03_exact.difference_hull kernel3d.g03_exact.sat_model kernel3d.g03_exact.boundary_probes','独立盒解析边界：所有点、源面环索引、primitive planes、SAT轴全集和有理上下界、26个边界点逐值核对。')
assign('test_surface_oracle_exact_distances_and_coordinate_bounds','kernel3d.g03_surface_oracle.bounds kernel3d.g03_surface_oracle.separated_distance','非立方盒独立坐标范围逐值；分离距离=3s、square=9s²，浮点及精确返回各测。')
assign('test_integer_surface_model_every_numeric_field','kernel3d.g03_surface_oracle.model','该API明确消费已清分母integer payload；最低非零1、普通7、高2^397三档。每个环、primitive normal、height、norm²、axes、bounds、12棱坐标、连通分量代表逐值；有理低端由separated_distance入口门覆盖。')
for n in ('kernel2d.g0.G0Report.passed','kernel2d.g0.DistanceReport.passed','kernel2d.g0.ExitReport.passed','kernel3d.g03.G0Report3.passed','kernel3d.g03.DistanceReport3.passed'):
 proof(n,'property仅读报告错误列表、整数计数的真假/相等，return为bool；不产生距离、坐标或报告数值。')
for n,text in {
'kernel2d.g0_oracle.on_segment':'return为turn==0与坐标有序比较的bool；无数值返回。',
'kernel2d.g0_oracle.inside':'整数winding只裁决return -1/0/1离散成员标签。',
'kernel2d.g0_oracle.overlap':'交叉/绕数/共线判据后只return -1/0/1；内部倍增坐标不作为构造输出。',
'kernel2d.g0_oracle.boundary_has_exterior':'内部有理配置线/探针用于拓扑；return True/False，无构造输出。',
'kernel3d.entrance3.merge_degenerate':'只返回(代表label,成员labels)，标签由kind字符串及原始面/边/顶点整数索引拼接；内部精确平面不返回。',
'kernel3d.entrance_topology.entrance_membership3':'全部返回点只有state或0/1；state来自-1/0/1；内部配置空间探针不输出。',
'kernel3d.g03_exact.dimension':'仿射秩分类return 0/1/2/3；内部有理方向不返回。',
'kernel3d.g03_exact.planar_ring':'返回输入indices的有序子集tuple(ring)，无新坐标或量值。',
'kernel3d.g03_exact.overlap':'整数SAT比较只返回-1/0/1离散相交状态。',
'kernel3d.g03_exact.support_labels':'返回源特征索引标签集合与退化面计数；法向/投影中间量不返回。',
'kernel3d.g03_surface_oracle.boxes_disjoint':'仅区间端点比较的any(bool)，无数值输出。',
'kernel3d.g03_surface_oracle.face_pieces':'返回源face或其三角化索引tuple；不创建数值坐标，折面计算仅择支。',
'kernel3d.g03_surface_oracle.in_face':'齐次有理成员判据只return -1/0/1。',
'kernel3d.g03_surface_oracle.contains':'integer generic-ray parity只return -1/0/1。',
'kernel3d.g03_surface_oracle.segment_face_hits':'端点/面判据return bool；齐次交点只用于内部成员判断，不返回。',
}.items():proof(n,text)

result=[]
for row in rows:
 name=row['api'][4:]
 source=Path(row['path']).read_text(encoding='utf-8-sig'); tree=ast.parse(source)
 # Exact qualified location, not name-search inference of coverage.
 suffix=name.split('.',2)[2]
 def locate(nodes,prefix=''):
  for node in nodes:
   if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
    qual=prefix+node.name
    if qual==suffix:return node
    hit=locate(node.body,qual+'.')
    if hit:return hit
 node=locate(tree.body); assert node is not None,name
 entry=dict(api=row['api'],path=row['path'],source_lines=[node.lineno,node.end_lineno],tests=[],scales=[],proof='',limits='')
 if name in mapping:
  test,desc=mapping[name]
  entry.update(status='differential',tests=['tests/test_r13fixb_kernel_numeric.py::'+test],scales=['2^-400','1','2^397'],proof=desc,limits='有限解析输入族的逐值差分门；不以此替代全输入域数学证明或G6独立审查。')
  if name=='kernel3d.g03_surface_oracle.model':entry['scales']=['integer 1','integer 7','integer 2^397']
  if name=='kernel3d.exact_sweep.surface_events':entry['tests'].append('tests/test_r13fixb_kernel_numeric.py::test_surface_events_non_dyadic_exact_times')
  if name=='kernel3d.exact_geom.dot':entry['tests'].append('tests/test_r13fixb_kernel_numeric.py::test_in_domain_raw_dot_cancellation_is_not_erased')
 elif name in proofs:
  entry.update(status='nonconstructive',proof=proofs[name],limits='此项豁免仅指无数值构造输出，不宣称谓词正确性由源码审查代替测试。')
 else:entry.update(status='gap',proof='未完成逐项证据。',limits='必须如实保留缺口。')
 extra={
 'kernel2d.g0.g0_distance_completeness': 'test_2d_g0_nonzero_diagnostics_and_failure_payload_are_independent',
 'kernel2d.g0.g0_exit_completeness': 'test_2d_g0_nonzero_diagnostics_and_failure_payload_are_independent',
 'kernel3d.g03.g0_distance_completeness3': 'test_3d_g0_nonzero_diagnostics_and_failure_payload_are_independent',
 'kernel3d.exact_sweep.surface_events': 'test_surface_event_label_time_binding_matches_independent_xy_elimination',
 }
 if name in extra:
  entry['tests'].append('tests/test_r13fixb_kernel_numeric.py::'+extra[name])
  if name=='kernel3d.exact_sweep.surface_events':
   entry['proof']+=' ?????????xy????????????(label,t)????????????????'
  else:
   entry['proof']+=' ?????????????/?????????x??-s??????????????worst=s?distance got=4s/truth=3s?exit t=1/witness=s???failure/construction_failure??payload?'
   entry['limits']='????????????????????????????3D??????2^-400/1/2^395?????<=24s<2^400?'
   if name=='kernel3d.g03.g0_distance_completeness3':
    entry['tests'].append('tests/test_r13fixb_kernel_numeric.py::test_3d_g0_nonempty_completeness_payload_matches_omitted_nearest_face')
    entry['proof']+=' ????vf_cover?????????face3???????????Cartesian????????5s?????completeness_failures=(x,25s?,9s?)???error/failures?????'
 result.append(entry)
assert len(result)==77
counts={x:sum(r['status']==x for r in result) for x in ('differential','nonconstructive','gap')}
(out/'coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(out/'coverage_counts.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(counts)
print('gaps',[r['api'] for r in result if r['status']=='gap'])
