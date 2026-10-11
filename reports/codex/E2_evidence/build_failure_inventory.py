"""Extract every original failing node and its explicit WO-E2 disposition."""
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
raw = (HERE / 'baseline_full.log').read_bytes()
log = raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
nodes = re.findall(r'^FAILED (\S+)', log, re.MULTILINE)
actions = {
    'test_every_code_pointer_in_canon_map_names_a_function_at_its_current_line':
        ('文档指针', '更新已删除方向窗/链法向的说明与指针；运行 fix_canon_ptrs.py --apply，保留原指针断言。'),
    'test_convex_g0_is_invariant':
        ('a 旧边界不变口径', '每个变换的完整标签集对独立 Fraction 支撑投影 oracle；每个成员对精确 SAT 零错；带外仍守刚体不变，边界不再强求 FF 标签不变。'),
    'test_a_t_vertex_one_ulp_above_the_lowest_edge_is_still_convex':
        ('a 旧微凹接收', '改为 test_a_t_vertex_one_ulp_above_the_lowest_edge_uses_the_concave_path；四朝向凸路径均拒收，保留平直对照与300点，凹回退对独立闭式缺口 oracle。'),
    'test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation':
        ('a 旧近似平行合并', '改为 test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation；FF 标签逐一对独立 Fraction 反平行边对，保留10种子，G0零豁免。'),
    'test_a_vertex_fifty_tolerances_inside_the_hull_is_rejected':
        ('a 旧容差内凸', '原50t拒收及0.5t接收两输入保留，改成二者均精确拒收；平直接受由96格旧门继续看护。'),
    'test_the_length_tolerance_is_the_slack_for_the_long_edge_rotation':
        ('a 旧tol决定FF', '改为 test_length_tolerance_never_changes_exact_parallel_merging；保留两倾角，增0分界和三种tol，完整产物不依tol且三种几何产物互异。'),
    'test_r7_third_vote_hull_vertices_match_and_catch_sign_flip':
        ('a 旧注入路径失效', '保留法向反号对独立边法向构造公式的看护；另在真实 membership_exact 内部注入边界丢失，要求G0精确报告16个边界错判，非随机变红。'),
    'test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start':
        ('a 旧微凹阈值/诊断', '两个原深度均在所有tol下拒收；每格2000随机+3定向点的凹成员对独立闭式 oracle；不再带内豁免。'),
}
rows = []
for node in nodes:
    name = node.split('::')[-1].split('[')[0]
    category, action = actions[name]
    rows.append(dict(node=node, category=category, disposition=action))
assert len(rows) == 35 and len({r['node'] for r in rows}) == 35
(HERE / 'failure_inventory.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# 原始全套35个失败：逐节点处置', '', '| # | 原失败节点 | 分类 | 处置 |', '|---:|---|---|---|']
lines += [f"| {i} | `{r['node']}` | {r['category']} | {r['disposition']} |" for i, r in enumerate(rows, 1)]
(HERE / 'failure_inventory.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(len(rows), 'failures accounted for')
