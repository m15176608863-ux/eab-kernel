"""Merge subtask ledgers, preserve failed-node inventory, and index evidence.

No source changes. Rerun after final verification and report edits.
"""
from pathlib import Path
import ast
import collections
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    dispositions = dict(read('covers_dispositions.json'), **read('limit_dispositions.json'))
    expected = {f"{v['file']}:{v['line']}" for v in read('selected_findings.json')}
    assert set(dispositions) == expected
    write('g6e_dispositions.json', dispositions)
    ledgers = {}
    for name in ('entrance_changes.json', 'covers_test_changes.json',
                 'limit_test_changes.json', 'screen_policy_test_changes.json'):
        if (OUT / name).exists():
            ledgers[name] = read(name)
    write('test_changes.json', ledgers)

    inventory = []
    for p in sorted(OUT.rglob('*')):
        if 'tmp' in p.relative_to(OUT).parts or p.suffix not in ('.log', '.txt'):
            continue
        s = p.read_text(encoding='utf-8-sig', errors='replace')
        failures = re.findall(r'^(FAILED|ERROR) (tests/[^\r\n]+)', s, re.M)
        if not failures:
            continue
        name = p.relative_to(OUT).as_posix()
        stage = ('source_mutation' if 'mutation' in name else
                 'baseline_new_gates' if 'baseline' in name or 'red_before' in name or 'frozen_old' in name else
                 'implementation_or_old_contract_iteration')
        inventory.append(dict(log=name, stage=stage, last_line=s.rstrip().splitlines()[-1],
                              failures=[dict(kind=k, node_and_summary=v) for k,v in failures],
                              count=len(failures)))
    write('failure_inventory.json', dict(
        note='Failed invocations are retained, not deduplicated numerical defects. Missing new fields in frozen-source reruns are interface failures, not new defect counts. Per-test contract dispositions live in test_changes.json.',
        verification_incidents=[dict(
            kind='verification_error',
            issue='bb52 ledger claimed two added assertions but CRLF replacement matched zero times in an LF file; root readback caught the discrepancy.',
            action='Stopped the 190.110 s full-suite run before editing; retained its log/result, inserted count and per-case cause assertions, reran targeted gate and restarted full suite.',
            evidence=['full_interrupted_for_missing_gate_result.json','bb52_readback_gate_result.json'],
            resolution='Final full-suite result is a fresh rerun after the correction, not the interrupted run.')],
        runs=inventory))

    mutations = []
    if (OUT/'mutations_entrance/results.json').exists():
        for d in read('mutations_entrance/results.json'):
            d['byte_restored'] = d['source_before_sha256'] == d['source_restored_sha256']
            d['log'] = 'mutations_entrance/'+d['id']+'.log'
            mutations.append(d)
    for p in sorted((OUT/'mutations').glob('D*_result.json')):
        d = read(p.relative_to(OUT))
        d['log'] = 'mutations/'+d['id']+'.log'
        mutations.append(d)
    mutations.sort(key=lambda d:int(d['id'][1:]))
    reviews={
        'D1': '语义门预期有效输入精确返回t=32；变异误判t=0相触，候选前保护抛RuntimeError，因此未到最终t断言。不是类型错误或偶然顶点选择。',
        'D2': '精确根被float舍入后漏候选，事件保护抛RuntimeError；有效输入本应返回精确时刻，73个时刻门拒绝此错误拒答。不是新字段缺失。',
        'D3': '两道pytest.raises(RuntimeError)实际DID NOT RAISE，直接证明漏更早首入的自检有牙。',
        'D4': '最浅出口法向和gap断言红：变异选反向深盖gap=-1.9999999999999716，而非正确的微负浅盖。',
        'D5': 've_cover(...no-window) is None断言红；真实微反射顶点被旧噪声窗错误接纳。',
        'D6': 'c.strict == strict_vv_oracle断言红；边界被>=错误标strict。',
        'D7': '(1e-15,-.001) in hull断言红，直接抓失真极点。',
        'D8': 'assert not d[static_ok]为22格实际红断言；未借对偶/互补的其他拒绝冒充静力牙。',
        'D9': '良性冗余逃逸：12格仍被精确互补拒绝；精确静力与对偶可行时，间隙等于各互补乘积之和，不能仅放宽间隙绕过互补。',
        'D10': '加入无关远体前后uncertainty相等断言6格全红；不是原问题status被改变才抓住。',
    }
    for d in mutations:
        d['semantic_review']=reviews[d['id']]
        d['disposition']='benign_redundancy' if d['id']=='D9' else 'caught_semantic_gate'
    write('mutation_results.json', dict(results=mutations,
        review='See E3E4_report.md for semantic assertion review and D9 complementarity redundancy proof.'))

    changed = subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode('utf-8').splitlines()
    ast_changes=[]
    added_functions=[]
    removed_functions=[]
    for name in changed:
        if not name.startswith('tests/') or not name.endswith('.py'):
            continue
        old=ast.parse(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT).decode('utf-8-sig'))
        new=ast.parse((ROOT/name).read_text(encoding='utf-8-sig'))
        originals={n.name:ast.dump(n) for n in old.body if isinstance(n,ast.FunctionDef)}
        newnames={n.name for n in new.body if isinstance(n,ast.FunctionDef)}
        added_functions.extend(name+'::'+n for n in sorted(newnames-originals.keys()))
        removed_functions.extend(name+'::'+n for n in sorted(originals.keys()-newnames))
        for n in new.body:
            if isinstance(n,ast.FunctionDef) and n.name in originals and ast.dump(n)!=originals[n.name]:
                ast_changes.append(name+'::'+n.name)
    write('changed_test_functions.json', ast_changes)
    combined=json.dumps(ledgers,ensure_ascii=False)
    coverage={node:node in combined for node in ast_changes+removed_functions}
    write('test_function_audit.json',dict(changed_existing=ast_changes,
        removed_or_renamed=removed_functions,added_in_modified_files=added_functions,
        ledger_coverage=coverage,
        note='Renamed hull test retains all 3000 input sets and strengthens count-only assertion to independent exact support-set equality. Helpers are also checked, not just test_ functions.'))

    index=[]
    for p in sorted(OUT.rglob('*')):
        rel=p.relative_to(OUT)
        if not p.is_file() or 'tmp' in rel.parts or p.name in ('evidence_index.json','INDEX.md'):
            continue
        index.append(dict(path=rel.as_posix(), bytes=p.stat().st_size,
                          sha256=hashlib.sha256(p.read_bytes()).hexdigest(), url=p.as_uri()))
    write('evidence_index.json', index)
    lines=['# WO-E3E4 证据索引','',
           f"[工单报告]({(ROOT/'reports/codex/E3E4_report.md').as_uri()}) · [临时备份目录]({(OUT/'tmp').as_uri()}/)", '',
           '临时源备份与隔离运行位于 tmp/（忽略入库）；此清单索引持久证据，不是独立 G6。','',
           '## 工作树改动（未提交）','',
           '| 文件 | 链接 |','|---|---|']
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT).decode('utf-8').splitlines()
    touched=sorted(set(changed+[p for p in untracked if p.startswith(('src/','tests/','tools/'))]))
    lines += [f"| {p} | [打开]({(ROOT/p).as_uri()}) |" for p in touched]
    lines += ['', '## 持久证据','',
           '| 文件 | 字节 | SHA-256 |','|---|---:|---|']
    lines += [f"| [{d['path']}]({d['url']}) | {d['bytes']} | `{d['sha256']}` |" for d in index]
    (OUT/'INDEX.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(dispositions=len(dispositions),ledger_files=len(ledgers),
                         failed_runs=len(inventory),mutations=len(mutations),
                         changed_test_functions=len(ast_changes),evidence_files=len(index))))


if __name__=='__main__':
    main()
