"""Index the retained M4b delivery without deleting or rewriting evidence."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BDDA = Path('D:/bdda-wt/shadow')


def link(label, path):
    return f'[{label}]({path.as_uri()})'


def main():
    changes = json.loads((HERE / 'change_inventory.json').read_text(encoding='utf-8'))
    paths = {ROOT / 'reports/codex/M4b_report.md'}
    for repo, root in (('eab', ROOT), ('bdda', BDDA)):
        paths.update(root / row['path'] for row in changes[repo])
    paths.update(p for p in HERE.rglob('*') if p.is_file() and p.name not in {
        'delivery_manifest.json', 'DELIVERY_INDEX.md', 'final_delivery_qa.json'})
    entries = []
    for path in sorted(paths, key=lambda p: str(p).lower()):
        data = path.read_bytes()
        entries.append({'path': str(path), 'uri': path.as_uri(), 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})
    manifest = {'scope': 'M4b code, fixtures, report and retained eab evidence; build trees linked separately',
                'files': entries,
                'self_hash_exclusions': ['delivery_manifest.json', 'DELIVERY_INDEX.md', 'final_delivery_qa.json']}
    (HERE / 'delivery_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    lines = ['# WO-M4b 交付索引', '',
             '两个专用工作树保持未提交；未批准真正 eab 替换。此索引覆盖代码、夹具、报告、审查与运行证据。', '',
             '## 主要入口', '']
    for label, path in [
        ('中文完成报告', ROOT / 'reports/codex/M4b_report.md'),
        ('两侧逐文件变更与哈希', HERE / 'change_inventory.json'),
        ('15 例三模式逐字节矩阵', ROOT / 'fixtures/m4b_shadow/byte_matrix.json'),
        ('全时程差异台账', ROOT / 'docs/m4b_difference_ledger.md'),
        ('最终 eab 全套与静态门', HERE / 'full_suite_r2/summary.json'),
        ('b-DDA 全套验证摘要', HERE / 'bdda_verification_summary.json'),
        ('交付文件哈希清单', HERE / 'delivery_manifest.json'),
        ('最终交付 QA（生成后）', HERE / 'final_delivery_qa.json')]:
        lines.append('- ' + link(label, path))
    lines += ['', '## 保留的目录与大体积证据', '']
    for label, path in [
        ('eab 专用工作树', ROOT), ('b-DDA 专用工作树', BDDA),
        ('紧凑 30 步回归夹具', ROOT / 'fixtures/m4b_shadow'),
        ('完整 1810 步逐记录回放', HERE / 'full_replay'),
        ('450 帧冻结前缀回放', HERE / 'replay'),
        ('本次全部 eab 证据', HERE),
        ('eab 最终新鲜导出（无 Git 元数据）', ROOT / 'build/m4b_fresh_r2'),
        ('首轮环境失败日志（不计为通过）', HERE / 'full_suite_r1'),
        ('b-DDA 原始运行/构建/复算证据', BDDA / 'bdda2/build/m4b'),
        ('改前源码/二进制回退锚', BDDA / 'bdda2/build/m4b/baseline'),
        ('改前拟改文件副本', BDDA / 'bdda2/build/m4b_source_before'),
        ('最终安静计时全部样本', BDDA / 'bdda2/build/m4b/timing.json')]:
        lines.append('- ' + link(label, path))
    lines += ['', '## 两侧改动文件', '']
    for repo, root in (('bdda', BDDA), ('eab', ROOT)):
        lines += [f'### {repo}', '']
        for row in changes[repo]:
            lines.append(f"- {link(row['path'], root / row['path'])} — {row['status']}，+{row['added']}/−{row['removed']}")
        lines.append('')
    lines += ['## 报告与证据文件逐项链接', '',
              '以下不逐列 build 中的编译中间文件；其目录已给出。哈希清单不自哈希，最终 QA 另绑定报告哈希。', '']
    for row in entries:
        path = Path(row['path'])
        if path.is_relative_to(HERE):
            lines.append('- ' + link(str(path.relative_to(HERE)).replace('\\', '/'), path))
    lines += ['', '所有原始失败、变异、修后复核和空 junction 负门布局均保留；没有自动清理或隐藏失败。', '']
    (HERE / 'DELIVERY_INDEX.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Indexed {len(entries)} files; no build evidence was changed.')


if __name__ == '__main__':
    main()
