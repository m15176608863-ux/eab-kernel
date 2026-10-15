"""Read-only equivalence of the fresh replay, final r4 export, and workspace."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT/'reports/codex/M3b_evidence'
FROZEN = EVIDENCE/'tmp/construction3d_frozen_r4_export'
SUITE = EVIDENCE/'tmp/final_suite_r4_export'
PREFIX = 'construction3d_frozen_r4'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((EVIDENCE/name).read_text(encoding='utf-8'))


def source_names(root):
    return {p.relative_to(root).as_posix() for p in (root/'src').rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def main():
    attestation = load(PREFIX+'_replay_attestation.json')
    imports = load(PREFIX+'_actual_imports.json')
    assert attestation['complete'] and attestation['source_unchanged']
    assert attestation['actual_imports_sha256'] == digest(EVIDENCE/(PREFIX+'_actual_imports.json'))
    assert attestation['output_sha256'] == digest(EVIDENCE/(PREFIX+'_replay.json'))
    assert imports['complete'] and imports['module_count'] == len(imports['modules']) == 29
    names = source_names(FROZEN)
    assert names == source_names(ROOT) == source_names(SUITE), 'production source file sets differ'
    rows = []
    used = {row['path'] for row in imports['modules'].values()} | {imports['driver']['path']}
    assert len(used) == 30, 'actual import or driver path repeated or absent'
    for name in sorted(names | used):
        hashes = {label: digest(root/name) for label, root in
                  (('replay_sha256', FROZEN), ('current_sha256', ROOT), ('final_suite_r4_sha256', SUITE))}
        assert len(set(hashes.values())) == 1, ('source/import/driver changed', name)
        assert hashes['replay_sha256'] == attestation['before_sha256'][name]
        rows.append(dict(path=name, production_source=name in names,
                         actual_import_or_driver=name in used, **hashes))
    differences = {}
    for label, root in (('workspace', ROOT), ('final_suite_r4', SUITE)):
        differences[label] = [name for name, frozen_hash in attestation['before_sha256'].items()
                              if not (root/name).is_file() or digest(root/name) != frozen_hash]
        assert not (set(differences[label]) & (names | used))
    data = {
        'complete': True, 'replay_root': str(FROZEN), 'final_suite_r4_root': str(SUITE),
        'workspace_root': str(ROOT), 'production_src_file_count': len(names),
        'production_src_equal_workspace': True, 'production_src_equal_final_suite_r4': True,
        'actual_import_module_count': imports['module_count'], 'actual_import_and_driver_count': len(used),
        'actual_imports_and_driver_equal_workspace': True,
        'actual_imports_and_driver_equal_final_suite_r4': True,
        'checked_files': rows,
        'other_producer_snapshot_differences': differences,
        'scope': 'all production bytes and same-run actually imported local modules/driver equal; other unimported tests/tools differences disclosed',
        'bound_artifacts': {name: digest(EVIDENCE/name) for name in (
            PREFIX+'_replay_attestation.json', PREFIX+'_actual_imports.json', PREFIX+'_replay.json',
            PREFIX+'_comparison.json', PREFIX+'_prem3_comparison.json')},
    }
    destination = EVIDENCE/(PREFIX+'_equivalence.json')
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: data[k] for k in ('complete', 'production_src_file_count',
          'actual_import_module_count', 'actual_import_and_driver_count', 'other_producer_snapshot_differences')}))


if __name__ == '__main__':
    main()
