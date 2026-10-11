"""Read-only source/test/fixture audits and the final consolidated rewrite ledger."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
BASE = EVIDENCE / 'tmp/profile_baseline'


def text_file(path):
    raw = path.read_bytes()
    return raw.decode('utf-16') if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else raw.decode('utf-8-sig')


def save(name, value):
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def node_ids(path):
    return {line for line in text_file(path).splitlines() if line.startswith('tests/') and '::' in line}


old_ids = node_ids(EVIDENCE / 'baseline_collection_complete.log')
new_ids = node_ids(EVIDENCE / 'collection_current.log')
collection = dict(baseline_count=len(old_ids), current_count=len(new_ids),
                  missing_original_nodes=sorted(old_ids-new_ids), added_nodes=sorted(new_ids-old_ids))
assert not collection['missing_original_nodes']
save('collection_audit.json', collection)

reasons = {(entry['file'], entry['function']): entry['reason_not_weaker']
           for entry in json.loads((EVIDENCE/'root_test_rewrites.json').read_text(encoding='utf-8'))}
reasons.update({
    ('tests/test_kernel3d_geom.py', 'test_face_touching_stack_is_touching_under_rigid_motion'):
        '原32格及原escape调用保留；舍入源表面由独立整数tetra SAT/欧氏距离核验，返回高度或未括住根异常由独立状态证实；另外添加同系数有理仿射理想接触门，不替换原输入。',
    ('tests/test_kernel3d_geom.py', 'test_overlap_coplanar_crossing_gate_has_teeth'):
        '原X交几何及贯入断言保留；已不被调用的旧helper突变移到实际凸SAT内部最终状态表达式，专门共面arrangement分支删除牙另外覆盖。',
    ('tests/test_geom3_face_polygon.py', 'test_all_five_call_sites_route_through_the_single_helper'):
        '原五路几何及断言目标保留；构造侧仍测原投影helper，表面侧注入实际triangle_locate路径，不允许伪造枚举结果。',
    ('tests/test_geom3_overlap_witness.py', 'test_thin_notch_bite_is_detected'):
        '所有原bite/gap稳定格闭式不变；exact_fill原输入逐格对独立原表面星形tetra并集oracle，另外保持轴对齐精确接触为0。',
    ('tests/test_geom3_overlap_witness.py', 'test_x_crossing_lifted_boundaries'):
        '所有原抬升深度/刚体变换格保留；稳定分离闭式不变，原边界格用独立实际表面oracle替代舍入后硬判理想0。',
    ('tests/test_geom3_overlap_witness.py', 'test_overlap_resolution_is_documented'):
        '原四深度及旧参数want原样保留；独立Fraction原始区间证明四格均真内部，要求1而不吞成0。',
    ('tests/test_g03_two_rulers.py', 'test_a_plate_thinner_than_the_coordinate_resolution_fails_loudly_with_the_reason'):
        '原工程/原点输入不变；真实可表达分离由独立整数tetra SAT证实，改要求正确-1和正距离/非哨兵而非旧内点resolution异常；原点1e-6距离断言保留。',
})
for entry in json.loads((EVIDENCE/'a3/test_rewrites.json').read_text(encoding='utf-8')):
    file, function = entry['test'].split('::')
    if function != 'test_g2_gate_is_invariant_under_rigid_motion_and_units':
        reasons[(file, function)] = entry['reason_not_weaker'] + ' ' + entry['new']
reasons[('tests/e5a_g2_oracle.py', 'construction')] = '原独立Gram/Newell表达式新增精确距离平方输出模式；原浮点构造输出不变，用于把枚举域窗核验从舍入gap迁到原值。'
reasons[('tests/e5a_g2_oracle.py', 'assert_comparison')] = '全部27原格/完整字典字段/adapter分组断言不变；仅枚举入口以独立有理距离平方比较window，禁止因sqrt舍入误纳入。'


def segment(path, function):
    source = text_file(path)
    node = next(node for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.FunctionDef) and node.name == function)
    return ast.get_source_segment(source, node), [ast.dump(x) for x in node.decorator_list]


ledger = []
for (file, function), reason in sorted(reasons.items()):
    before, old_decorators = segment(BASE/file, function)
    after, new_decorators = segment(ROOT/file, function)
    assert old_decorators == new_decorators, (file, function)
    prefix = file+'::'+function
    cells = lambda ids: sorted(x for x in ids if x == prefix or x.startswith(prefix+'['))
    assert cells(old_ids) == cells(new_ids), prefix
    ledger.append(dict(file=file, function=function, old=before, new=after,
                       original_cells=len(cells(old_ids)), current_cells=len(cells(new_ids)),
                       decorators_unchanged=True, reason_not_weaker=reason,
                       current_function_sha256=hashlib.sha256(after.encode()).hexdigest()))
save('test_rewrites.json', ledger)

fixture_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted((ROOT/'fixtures').rglob('*')) if p.is_file()}
assert all((BASE/path).read_bytes() == (ROOT/path).read_bytes() for path in fixture_hashes)
save('fixture_unchanged.json', dict(count=len(fixture_hashes), all_equal_baseline=True, sha256=fixture_hashes))


def executable_tree(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
    return ast.dump(tree)


assert executable_tree(text_file(BASE/'src/eab/margin.py')) == executable_tree(text_file(ROOT/'src/eab/margin.py'))
state = dict(head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
             branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
             diff_name_status=subprocess.check_output(['git', 'diff', '--name-status'], cwd=ROOT, text=True),
             margin_executable_ast_unchanged=True,
             source_tests_frozen_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                        for top in ('src', 'tests', 'tools') for p in sorted((ROOT/top).rglob('*.py'))})
save('delivery_audit.json', state)
print(json.dumps(dict(original_nodes=len(old_ids), current_nodes=len(new_ids), missing=0,
                      ledger_entries=len(ledger), fixtures_unchanged=len(fixture_hashes),
                      head=state['head'], margin_executable_ast_unchanged=True), ensure_ascii=False))
