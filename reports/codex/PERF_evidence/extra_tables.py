"""Assemble second-round exact optimization evidence without rerunning workloads."""
from pathlib import Path
import json

E = Path(__file__).resolve().parent
def read(path):
    return json.loads((E/path).read_text(encoding='utf8'))

rows = []
def row(name, count, old, new, gate):
    rows.append([name, count, f'{old:.6f}', f'{new:.6f}', f'{old/new:.2f}×', gate])

v = read('edge_draft/edge_benchmark.json')
row('3D edge frame正比例整数化', v['cases'], v['baseline_seconds'], v['optimized_seconds'], 'test_perf_edge_frame.py')
v = read('profile/directions_benchmark.json')
for key, label in [('micro', '2D VE共分母整数化'), ('bb52', '2D优化/BB52端到端')]:
    r = v[key]
    row(label, r.get('cases', 'samples_per_pair=3, seed=0'), r['baseline_seconds'], r['optimized_seconds'], 'test_perf_2d_directions.py')
for v in read('witness_draft/microbench_variants.json'):
    row('精确arrangement/'+v['case'], '相同首Fraction witness/None', v['baseline_seconds'], v['all_three_grouped_seconds'], 'test_perf_surface_witness.py')
v = read('profile_round2/oracle_benchmark.json')
row('独立测试oracle（非生产）', '6个互锁完整候选集', v['before_total_seconds'], v['after_total_seconds'], 'test_perf_oracle_algebra.py')
(E/'extra_optimization_rows.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

mutations = [
    ['3D整数方向丢符号', '_integer_ray 对各分量取abs', 'test_integer_edge_direction_sign_mutation_has_teeth', 'analytic edge direction/window state'],
    ['3D整数方向漏分母', '_integer_ray 遗漏分量分母，非等比缩放', 'test_integer_edge_anisotropic_rescaling_mutation_has_teeth', 'analytic edge direction/window state'],
    ['2D长度阈值漏缩放', '_ve_side_directions 内tol省略乘D', 'test_integer_ve_length_rescaling_mutation_has_teeth', 'length window retains exact scale and boundary'],
    ['2D严格性错收边界', '_ve_side_directions 内strict >改为>=', 'test_integer_ve_strict_boundary_mutation_has_teeth', 'exact boundary cannot become strict'],
    ['arrangement错删AABB闭边界', '_surface_interior_witness 中严格不交改为闭界剔除', 'test_arrangement_aabb_is_closed_and_mutation_removing_boundary_has_teeth', 'coplanar witness must survive'],
    ['arrangement同侧符号错', '_surface_interior_witness 原三角形同侧判据反号', 'test_arrangement_source_plane_sign_mutation_is_caught_by_first_witness', 'first exact witness changed'],
    ['arrangement平面分组丢offset', '仅从coplanar分组键去掉offset，支持平面去重不改', 'test_coplanar_grouping_keeps_the_plane_offset_not_only_its_direction', 'parallel planes are not coplanar; pinned (-3/32,-7/16,1/8)'],
]
(E/'extra_mutations.json').write_text(json.dumps(mutations, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(f'{len(rows)} optimization rows; {len(mutations)} mutations')
