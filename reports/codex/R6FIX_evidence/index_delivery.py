"""Validate mutation chains and package tracked AND new worktree changes."""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'reports/codex/R6FIX_evidence'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode_log(raw):
    """Retain historical PowerShell UTF-16 BOM logs; never rewrite evidence."""
    encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    return raw.decode(encoding)


def terminal(log):
    return next((line for line in reversed(log.splitlines()) if line.strip()), '')


def validate_pytest_mutant(record, log, test, guard):
    assert record.get('exit_code') == 1, ('expected pytest failure', record)
    assert record.get('last_line') == terminal(log), 'metadata/log summary mismatch'
    assert re.match(r'^[1-9]\d* failed\b', terminal(log)), 'not a failed-test summary'
    assert re.search(r'^FAILED tests[\\/].*::'+re.escape(test)+r'(?:\[|\s|$)', log, re.M), test
    errors = '\n'.join(line for line in log.splitlines() if line.lstrip().startswith('E '))
    assert guard in errors, ('guard absent from runtime error, source text is insufficient', guard)
    assert 'ERROR collecting' not in log and 'Interrupted:' not in log


def validate_mutations(evidence):
    records = {}
    specs = [
        ('04_2d', 'g0/mutant_classification2d', 'test_g6f04_2d_strict_micro_sample_is_checked', 'strict sample was skipped'),
        ('04_3d', 'g0/mutant_classification3d', 'test_g6f04_3d_strict_micro_gap_is_checked', 'strict sample was skipped'),
        ('05_exit', 'g0/mutant_exit_midpoint', 'test_g6f05_first_exit_preserves_micro_penetration', 'first strict exit'),
        ('05_distance', 'g0/mutant_distance_square', 'test_g6f05_distance_does_not_underflow_or_overflow_its_square', 'closed segment projection'),
        ('06', 'construction/mutant_06', 'test_g6f06_exit_gap_preserves_representable_nonzero_magnitude', 'representable signed gap'),
        ('08', 'construction/mutant_08', 'test_g6f08_distance_and_normal_use_exact_relative_projection', 'exact relative distance'),
        ('10', 'construction/mutant_10', 'test_g6f10_canon_definition_matches_exact_difference_contract', 'stale pre-rounded'),
        ('cover_scan', 'construction/mutant_cover', 'test_cover_construction_exposes_exact_nonzero_gap_and_area', 'round final norm, not its components'),
    ]
    for key, prefix, test, guard in specs:
        log = (evidence/(prefix+'.log')).read_text(encoding='utf-8')
        record = json.loads((evidence/(prefix+'.json')).read_text(encoding='utf-8'))
        validate_pytest_mutant(record, log, test, guard)
        records[key] = dict(log=prefix+'.log', metadata=prefix+'.json', test=test, runtime_guard=guard,
                            exit_code=record['exit_code'], log_sha256=sha((evidence/(prefix+'.log')).read_bytes()))
    dual = json.loads((evidence/'dual_lp/mutations.json').read_text(encoding='utf-8'))
    dual_specs = {
        '07_div': ('test_r6fix07_division_and_reverse_preserve_representable_derivatives', 'inf'),
        '07_atan2': ('test_r6fix07_atan2_matches_independent_fraction_derivative', '-5e-201'),
        '07_mul': ('test_r6fix07_related_product_derivative_avoids_intermediate_range_loss', 'nan'),
        '07_pow': ('test_r6fix07_related_inverse_power_derivative_is_representable', 'OverflowError'),
        '11': ('test_r6fix11_zero_power_is_constant_one_with_same_width', 'ZeroDivisionError'),
        '12': ('test_r6fix12_every_optimal_path_has_complete_exact_witnesses', 'optimal result must carry exact_x'),
        'frozen_gap': ('test_frozen_gap_does_not_overflow_cancelling_dot_products', 'nan'),
        'frozen_unit': ('test_frozen_unit_jet_divides_before_rounding_an_overflowing_tangent_component', 'OverflowError'),
    }
    assert len(dual) == len(dual_specs) and {r['mutation'] for r in dual} == dual_specs.keys()
    for row in dual:
        key = row['mutation']
        test, guard = dual_specs[key]
        path = 'dual_lp/mutation_'+key+'.log'
        log = (evidence/path).read_text(encoding='utf-8')
        validate_pytest_mutant(row, log, test, guard)
        records[key] = dict(log=path, metadata='dual_lp/mutations.json', test=test, runtime_guard=guard,
                            exit_code=row['exit_code'], log_sha256=sha((evidence/path).read_bytes()))
    geom = json.loads((evidence/'geom3/mutations.json').read_text(encoding='utf-8'))
    wrapper = json.loads((evidence/'geom3/mutation_replay.json').read_text(encoding='utf-8'))
    log_path = evidence/'geom3/mutation_replay.log'
    log = log_path.read_text(encoding='utf-8')
    expected = {'G6F-01', 'G6F-01-scan', 'G6F-02', 'G6F-03', 'G6F-09', 'G6F-09-scan',
                'norm-scan', 'near-parallel-existing-gate'}
    assert wrapper['exit_code'] == 0 and wrapper['last_line'] == terminal(log)
    assert terminal(log) == '8 internal mutants killed by the intended assertion'
    assert len(geom) == 8 and {r['finding'] for r in geom} == expected
    assert log.count('\nKILLED_BY_GUARDING_ASSERTION') == 8
    for row in geom:
        marker = '=== INTERNAL MUTANT '+row['finding']+':'
        assert log.count(marker) == 1
        section = log.split(marker, 1)[1].split('=== INTERNAL MUTANT ', 1)[0]
        assert row['exception'] == 'AssertionError' and row['status'] == 'KILLED_BY_GUARDING_ASSERTION'
        assert row['test'].split('::')[-1] in section
        assert '\nAssertionError: '+row['guard'] in section, row
        records[row['finding']] = dict(log='geom3/mutation_replay.log', metadata='geom3/mutation_replay.json',
            structured_metadata='geom3/mutations.json', test=row['test'], runtime_guard=row['guard'],
            wrapper_exit_code=0, internal_status=row['status'], log_sha256=sha(log_path.read_bytes()))
    return records


def archive_eligible(path):
    p = PurePosixPath(path)
    if p.is_absolute() or '..' in p.parts or not path or path.startswith('reports/codex/inputs/'):
        return False
    prefix = 'reports/codex/R6FIX_evidence/'
    if path.startswith(prefix):
        return p.suffix in ('.py', '.md') and p.name != 'INDEX.md' and 'tmp' not in p.parts
    return True


def changed_paths():
    return sorted(set(filter(None, subprocess.check_output(
        ['git', 'ls-files', '--modified', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode('utf-8').split('\0'))))


def package_worktree(paths):
    selected = [p for p in paths if archive_eligible(p)]
    missing = [p for p in selected if not (ROOT/p).is_file()]
    rows = []
    package = E/'working_tree_delivery.zip'
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name in selected:
            if name in missing:
                continue
            data = (ROOT/name).read_bytes()
            rows.append(dict(path=name, bytes=len(data), sha256=sha(data)))
            z.writestr(name, data)
        manifest = dict(files=rows, deleted_paths=missing,
            note='All modified/new worktree files except user inputs and evidence data; evidence Python replay scripts and Markdown subreports included, generated INDEX excluded. Not a standalone repository checkout.')
        z.writestr('DELIVERY_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {r['path'] for r in rows} | {'DELIVERY_MANIFEST.json'}
        assert all(sha(z.read(r['path'])) == r['sha256'] for r in rows)
    return dict(path=package.relative_to(ROOT).as_posix(), files=len(rows), deleted_paths=missing,
                sha256=sha(package.read_bytes()), bytes=package.stat().st_size)


def main():
    import audit_delivery as audit
    checked = json.loads((E/'delivery_audit.json').read_text(encoding='utf-8'))
    assert checked['passed'], 'run the successful final delivery audit first'
    freeze = json.loads((E/'verified_tree_start.json').read_text(encoding='utf-8'))
    assert not any(audit.snapshot_changes(freeze, audit.source_snapshot(ROOT)).values()), 'source changed since full run'
    for key, name in [('full_suite_log_sha256', 'full_suite.log'), ('full_suite_json_sha256', 'full_suite.json'),
                      ('freeze_manifest_sha256', 'verified_tree_start.json')]:
        assert checked[key] == sha((E/name).read_bytes()), ('stale delivery audit', name)
    mutations = validate_mutations(E)
    group = {
        '01': ('critical', 'geom3/before_red.log', ['G6F-01', 'G6F-01-scan']),
        '02': ('major', 'geom3/before_red.log', ['G6F-02']),
        '03': ('major', 'geom3/before_red.log', ['G6F-03']),
        '04': ('major', 'g0/red.log', ['04_2d', '04_3d']),
        '05': ('major', 'g0/red.log', ['05_exit', '05_distance']),
        '06': ('major', 'construction/pre_fix.log', ['06']),
        '07': ('major', 'dual_lp/before.log', ['07_div', '07_atan2']),
        '08': ('major', 'construction/pre_fix.log', ['08']),
        '09': ('minor', 'geom3/before_red.log', ['G6F-09', 'G6F-09-scan']),
        '10': ('minor', 'construction/pre_fix.log', ['10']),
        '11': ('minor', 'dual_lp/before.log', ['11']),
        '12': ('minor', 'dual_lp/before.log', ['12']),
    }
    findings = []
    for number, (severity, red, keys) in group.items():
        assert re.search(r'^FAILED tests[\\/].*::test_(?:g6f|r6fix)'+number,
                         decode_log((E/red).read_bytes()), re.M), ('before-red node missing', number)
        findings.append(dict(id='G6F-'+number, severity=severity, status='FIXED_REGRESSION_GREEN_MUTATION_KILLED',
                             before_log=red, mutations=[mutations[k] for k in keys], final_green_log='full_suite.log'))
    (E/'findings_status.json').write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding='utf-8')
    (E/'mutation_validation.json').write_text(json.dumps(mutations, ensure_ascii=False, indent=2), encoding='utf-8')
    (E/'working_changes.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT))
    package = package_worktree(changed_paths())
    (E/'package_summary.json').write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding='utf-8')
    (E/'git_status_final.txt').write_bytes(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT))
    rows = []
    for name in changed_paths():
        p = ROOT/name
        if not p.is_file() or (p.is_relative_to(E) and (p.name in ('manifest.json', 'INDEX.md') or 'tmp' in p.relative_to(E).parts)):
            continue
        rows.append(dict(path=name, url=p.as_uri(), bytes=p.stat().st_size, sha256=sha(p.read_bytes())))
    (E/'manifest.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    header = '''# R6FIX 交付证据索引

主报告、逐条状态、最终全套及完整性审计是入口。修前及变异红为预期证据，不是最终代码状态。
`working_tree_delivery.zip` 包含修改及新增代码、测试、文档、分项报告与小型重放脚本；不含用户 inputs、证据数据、生成 INDEX 或递归自身。
`working_changes.patch` 仅为已跟踪文件的辅助 diff，不能独自交付新增实现与测试。
G6F 用户输入在任务起点未记录哈希；清单中的当前哈希不冒充任务起点一致性证明。
pytest 临时产物不作为代码交付；首轮失败全套与第二轮全套分别保留。

| 文件 | 大小 | SHA-256 |
|---|---:|---|
'''
    body = '\n'.join(f"| [{r['path']}]({r['url']}) | {r['bytes']} | `{r['sha256']}` |" for r in rows)
    (E/'INDEX.md').write_text(header+body+'\n', encoding='utf-8')
    print(json.dumps(dict(findings=len(findings), mutations=len(mutations), indexed_files=len(rows), package=package), ensure_ascii=False))


def self_test():
    for encoding in ('utf-16', 'utf-16-be', 'utf-8-sig', 'utf-8'):
        raw = 'FAILED tests/test_x.py::test_guard'.encode(encoding)
        if encoding == 'utf-16-be':
            raw = b'\xfe\xff'+raw
        assert decode_log(raw) == 'FAILED tests/test_x.py::test_guard'
    summary = '1 failed in 0.01s'
    log = 'E       AssertionError: intended\nFAILED tests/test_x.py::test_guard - AssertionError\n'+summary
    good = dict(exit_code=1, last_line=summary)
    validate_pytest_mutant(good, log, 'test_guard', 'intended')
    for record, bad_log in [(dict(good, exit_code=0), log), (good, log.replace('E       AssertionError:', '>       assert')),
                            (good, log.replace('::test_guard', '::test_other'))]:
        try:
            validate_pytest_mutant(record, bad_log, 'test_guard', 'intended')
        except AssertionError:
            pass
        else:
            raise AssertionError('invalid mutation evidence accepted')
    assert archive_eligible('src/eab/new.py') and archive_eligible('tests/test_new.py')
    assert archive_eligible('reports/codex/R6FIX_evidence/dual_lp/report.md')
    assert not archive_eligible('reports/codex/R6FIX_evidence/INDEX.md')
    assert not archive_eligible('reports/codex/inputs/G6F_report.md')
    assert not archive_eligible('reports/codex/R6FIX_evidence/baseline_tracked.zip')
    assert not archive_eligible('reports/codex/R6FIX_evidence/working_tree_delivery.zip')
    assert not archive_eligible('reports/codex/R6FIX_evidence/tmp/helper.py')
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        z.writestr('src/eab/new.py', b'new code')
    with zipfile.ZipFile(stream) as z:
        assert sha(z.read('src/eab/new.py')) == sha(b'new code')
    print('index_delivery self-test: 16 checks passed; no final indexing or packaging executed')


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        self_test()
    else:
        main()
