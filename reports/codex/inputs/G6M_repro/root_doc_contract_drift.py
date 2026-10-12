"""G6M 文档不同步复现：canon_map 顶部仍宣称全库依赖钉住、仅整数常量自动证明。
不改任何根树文件，以当前扫描API验证同一受检模块的无关尾注不失效。
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
spec=importlib.util.spec_from_file_location('g6m_doc_gate',ROOT/'tools/check_exact_construction.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
canon=(ROOT/'docs/canon_map.md').read_text(encoding='utf-8-sig').splitlines()[2]
sync=(ROOT/'docs/r12fix_design_sync.md').read_text(encoding='utf-8-sig')
policy=json.loads((ROOT/'tools/exact_construction_policy.json').read_text(encoding='utf-8-sig'))
assert '全 src/tests/tools 原字节依赖图钉住' in canon and '自动算术证明仅限纯整数字面量子集' in canon
assert '全部 Python 文件依赖快照被撤下' in sync and '变量/Fraction' in canon
assert 'dependency_snapshot' not in policy and 'dependencies' not in policy
path='src/eab/kernel3d/geom3.py';source=(ROOT/path).read_text(encoding='utf-8-sig');edited=source+'\n# G6M unrelated tail comment probe; no function changes.\n'
before=gate._subset.approved_sites(source,path);after=gate._subset.approved_sites(edited,path)
assert before==after and before
bi=gate.scan_text(source,path);ai=gate.scan_text(edited,path);assert bi==ai==[],(bi,ai)
output={'confirmed_minor_document_drift':True,'location':'docs/canon_map.md:3','old_current_intro':canon,'policy_review_contract':policy['review_contract'],'module':'src/eab/kernel3d/geom3.py','approved_sites_before':len(before),'approved_sites_after_unrelated_comment':len(after),'diagnostics_before':bi,'diagnostics_after':ai,'source_hash_changed':hashlib.sha256(source.encode()).hexdigest()!=hashlib.sha256(edited.encode()).hexdigest(),'tracked_source_written':False,'note':'Latest README and r12fix_design_sync explicitly supersede this historical design; not a mathematical-core false promise major.'}
print(json.dumps(output,ensure_ascii=False,indent=2));(ROOT/'review/evidence/root_doc_drift.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
