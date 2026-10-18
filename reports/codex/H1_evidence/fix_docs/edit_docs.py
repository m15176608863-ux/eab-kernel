"""WO-H1-fix documentation-only corrections; no archive or Git writes."""
from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CHANGES = []


def write(relative, before, after):
    assert before != after, relative
    path = ROOT / relative
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(after)
    delta = list(difflib.ndiff(before.splitlines(), after.splitlines()))
    CHANGES.append(dict(path=relative,
                        before_sha256=hashlib.sha256(before.encode()).hexdigest(),
                        after_sha256=hashlib.sha256(after.encode()).hexdigest(),
                        removed_lines=sum(line.startswith('- ') for line in delta),
                        added_lines=sum(line.startswith('+ ') for line in delta)))


def read(relative):
    with (ROOT / relative).open(encoding="utf-8", newline="") as stream:
        return stream.read()


def replace(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


relative = "docs/shi_attribution.md"
before = text = read(relative)
text = replace(text, "**唯一分类规则。** 每行仅用一类：", "**唯一分类规则。** 原文关系分为")
text = replace(text, "**原文缺口**。复合结论拆行", "**原文缺口**；A36 按验收订正单独归为**已有标准结果**，不强塞进“本仓库新结果”。每行仅用一类。复合结论拆行")
rows = {}
for line in text.splitlines():
    if line.startswith("| A"):
        cells = [part.strip() for part in line.strip('|').split('|')]
        rows[cells[0]] = cells
rows['A10'][4] += "；手算补充 `tests/test_m3_theory.py::test_m3_open_pair_sum_union_is_not_the_interior_of_closed_union` 仅为算例，不是生产门"
rows['A10'][5] = "`tests/test_m3_theory.py::test_m3_tight_fit_distinguishes_body_relation_from_entrance_topology`；`tests/test_m3_global3d.py::test_zero_clearance_contact_is_not_silently_regularized_to_open_union`"
rows['A14'][5] = "主门：`tests/test_m3_global2d.py::test_clipped_covers_are_exactly_boundary_and_cover_oracle_ray_exits`；包含方向 ∂E⊆暴露片并：`tests/test_m3_global2d.py::test_local_clipping_covers_the_independently_built_cell_boundary`（后者的参照边界由生产构造）"
rows['A28'][4] += "；`tests/test_m3_theory.py::test_m3_closed_separation_depth_and_nonpenetration_depth_are_different` 仅为手算算例，不跑生产 rho API"
rows['A28'][5] = "无门（仅文档算例）"
rows['A36'][2] = "已有标准结果"
rows['A36'][3] = "一般公式为标准 Minkowski 结合律推论；二维特例见 Shi 2015 §6.3–6.4 / 2021 §5.3（A35），不列为本仓库新结果"
rows['A39'][1] = "对称关系的位移形式 E_d(A,B)=−E_d(B,A)；参考点形式再加 a0+b0"
rows['A39'][3] = "Shi 2015 §4.5；2021 §7.2；生产接口接收位移 d，逐点检查 d↔−d，不把测试内部参考点抵消当作额外覆盖"
rows['A39'][5] = "`tests/test_h1_entrance_symmetry.py::test_shi_displacement_reflection_matches_independent_oracle_for_nonconvex_entrance`（逐点对独立 oracle 检：凹口/凹缝/紧配缝、顺逆环、刚体与单位格；参数格互异检查另属 test-of-test）"
text = '\n'.join(' | '.join([''] + rows[line.split('|')[1].strip()] + ['']).strip() if line.startswith('| A') else line for line in text.splitlines()) + '\n'
write(relative, before, text)

relative = "README.md"
before = text = read(relative)
mapping = {'A01/A04': ['A01', 'A04'], 'A08': ['A08'], 'A10': ['A10'],
           'A12': ['A12'], 'A14': ['A14'], 'A16': ['A16'], 'A18': ['A18'],
           'A20': ['A20'], 'A25': ['A25'], 'A27': ['A27'], 'A29': ['A29'],
           'A30': ['A30'], 'A31–A33': ['A31', 'A32', 'A33']}
new_lines = []
for line in text.splitlines():
    if line.startswith('| ') and any('（'+key+'）' in line for key in mapping):
        key = next(key for key in mapping if '（'+key+'）' in line)
        cells = [part.strip() for part in line.strip('|').split('|')]
        cells[3] = '；'.join(rows[item][5] for item in mapping[key]).replace('tests/', '')
        line = ' | '.join([''] + cells + ['']).strip()
    new_lines.append(line)
text = '\n'.join(new_lines) + '\n'
text = replace(text, '## 未证明 / 不保证', '## 未证明 / 无门 / 不保证')
text = replace(text, '- `PD_closed` 是闭集完全分离的', '- A28 的 rho 形式化仅有文档算例、无生产门；A36 是已有标准膨胀恒等式、无独立门，均不列入上方已证明清单。\n- `PD_closed` 是闭集完全分离的')
write(relative, before, text)

relative = "docs/canon_map.md"
before = text = read(relative)
text = replace(text, '## 六、"代码有、正本无"', '## 六、代码中的补充、严格化与二手正本的遗漏（不等于原文没有）')
text = replace(text, '订正见 `AGENTS.md:5-7`', '订正见 [历史纪律副本第 5–7 行](history/AGENTS_through_20261019.md)；当前归属见 [归属总表](shi_attribution.md)')
write(relative, before, text)

relative = "docs/m3_global_entrance_design.md"
before = text = read(relative)
text = replace(text, '本地只读正本00§3.2–3.3/§4、01命题1–8、03 K1–K5已核其文字，不等于外文原文已核。', '本地只读正本00§3.2–3.3/§4、01命题1–8、03 K1–K5已核其文字；2026-10-19 已另核石根华 2015/2021 原文，现行归属以 [归属总表](shi_attribution.md) 与 [二手转述勘误](canon_errata_20261019.md) 为准，不再以 00/01/03 代替原文。')
text = replace(text, '文献最终核验与链接见 `reports/codex/M3_evidence/theory_audit.md` §7：', 'M3 时点的文献核验与链接见 [外归档 theory_audit.md](file:///D:/eab-evidence/reports/codex/M3_evidence/theory_audit.md) §7（其文首旧相对链接的可审阅勘误全文见 [归档例外说明](../reports/EVIDENCE_ARCHIVE.md#theory_auditmd-唯一字节例外与勘误全文)）：')
text = replace(text, 'Wein同名ACS原稿及Hachenberger官方CGAL手册相关节已核，其余保持未核完整原文。', 'Wein同名ACS原稿及Hachenberger官方CGAL手册相关节已核；该历史报告其余“未核”状态不覆盖上段 2026-10-19 的 Shi 原文核验。')
write(relative, before, text)

relative = "docs/plan_20260921.md"
before = text = read(relative)
text = replace(text, '实现命题 7 的三维版（集值点上的确定性裁决），', '实现命题 7 的三维版（勘误 2026-10-19：首入是参考点从 E 外首次到达 ∂E 的事件；本仓库沿运动方向精确计算并报全部并列，原文没有选一个的规则，见 [归属总表 A24/A25](shi_attribution.md)），')
write(relative, before, text)

relative = "docs/m5d_c1_theory.md"
before = text = read(relative)
text = replace(text, '以下是封存提交 `5e3ba68` 中既有量化结果的口径订正，不是 H1 新回放，也不把封存工作合入主线。', '以下是**已封存但未验收的 WIP 提交 `5e3ba68`** 中既有量化结果的口径订正，不是 H1 新回放，也不把封存工作合入主线。2728 / 44（26+18）来自该 WIP 的量化产物；当时独立校验只作近似测量（约 2728 / 44），并未把这些历史数值升级成已验收的连续时间结论。')
text = replace(text, '这些小反例门不为上表的历史全量计数充当新验证。', '这些小反例门不为上表的历史全量计数充当新验证。H1-fix 另补角色互换门 `test_c1_a_ring_convexity_uses_a_radius_when_b_is_exact`，守护 A 环凸性使用 A 半径；它不是从 WIP 摘取的第四道门。')
write(relative, before, text)

relative = "AGENTS.md"
before = text = read(relative)
text = replace(text, '- 纯度门按下划线、驼峰与大小写不敏感切词，起始禁词至少为 `dda bdda tia tf rock joint mtype df04 df05 df06 df07`；只可增补，不可删减。', '- 纯度门 `tests/test_kernel_purity.py` 按下划线、驼峰与大小写不敏感切词，保留字母数字串，并检查复数、小写拼接、bytes 常量与模块路径；起始禁词至少为 `dda bdda tia tf rock joint mtype df04 df05 df06 df07`，另含 legacy/槽位类词；只可增补，不可删减。词法扫描同时包含每次内核导入执行的 `eab/__init__.py`、`contact_record.py`、`numeric_decode.py`；保留的公共契约字段须有精确白名单及理由，不作整模块豁免。')
text = replace(text, '--basetemp reports/codex/H1_evidence/tmp/pytest_fast', '--basetemp <本单证据目录>/tmp/pytest_fast')
text = replace(text, '普通 pytest 的 `--runslow` 同样包含快慢全档；', '普通 pytest 的 `--runslow` 同样包含快慢全档；单跑慢档时 `-m slow` 必须配 `--runslow`（否则默认过滤后可能收集为 0），且不能代替快慢全档；')
text = replace(text, '- **C · 先门后文**：README/reports 的已证/已实现性质陈述与 docstring 性质声明须指向具名测试；未配门明确写“无门”，不虚配；有限测试不冒充全输入域证明。', '- **C · 先门后文**：README/reports 的已证/已实现性质陈述与 docstring 性质声明须指向具名测试；指不出就不写。README 的“已证明清单”只收有门守护的命题；无门命题只能进入“未证明 / 无门”栏，或在归属/证明表明确记“无门”，不得强凑手算算例作生产门。有限测试不冒充全输入域证明。')
text = replace(text, '另覆盖特征尺度远小于坐标量级的输入。', '另覆盖特征尺度远小于坐标量级的输入。具名元门：`tests/test_invariance_geom.py`、`tests/test_invariance_2d.py`、`tests/test_invariance_limit.py`、`tests/test_invariance_interlock.py`；分辨率角落门：`tests/test_margin_resolution.py`。')
text = replace(text, '- 输出自报 `source`/`observable`；', '- **阈值先测后钉**；输出自报 `source`/`observable`；')
write(relative, before, text)

relative = "reports/EVIDENCE_ARCHIVE.md"
before = text = read(relative)
text = replace(text, '历史报告正文不逐个改链接。路径映射：旧 `reports/codex/<名称>_evidence/<相对文件>` 对应 `D:/eab-evidence/reports/codex/<名称>_evidence/<相对文件>`；H1 当前运行目录不归档。\n测试实际读取的输入优先映射到 `fixtures/frozen/<去掉 reports/ 的原路径>`；输入原字节保留，嵌入的历史路径/哈希不重写。', '历史报告正文不逐个改链接；同一映射规则也适用于当前 docs/README/AGENTS 与工具中残留的历史路径。对旧 `reports/<相对路径>`，**先查**仓库内 `fixtures/frozen/<去掉 reports/ 的原路径>`，存在则作为冻结输入使用；**否则再查** `D:/eab-evidence/<完整旧路径>`。例如 `reports/codex/M5b_evidence/endpoint_inputs/…` 优先解析到 `fixtures/frozen/codex/M5b_evidence/endpoint_inputs/…`，而 `reports/codex/M3_evidence/theory_audit.md` 解析到外归档。H1 当前运行目录不归档；仍在仓库的当前文件不走历史映射。\n该规则是路径迁移说明，不声称所有旧 CLI 都自动回退到外归档；测试固定输入由 `tools/frozen_evidence.py` 解析，旧全量命令如需历史输出应由所有者按映射准备，不在本单重跑。冻结输入原字节保留，嵌入的历史路径/哈希不重写。')
text = replace(text, '其中 Git 跟踪 5,551 文件、521,250,702 字节。', '其中已归档的 Git 跟踪文件 5,551 个，归档现场字节 521,250,702；`1ce9a91` 原 blob 字节 521,250,505（相差下述勘误行 197 B）。')
text = replace(text, '同卷目录 rename 保留原字节；', '同卷目录 rename 保留归档时字节（相对 `1ce9a91` 的唯一例外见下节）；')
text = replace(text, '其中原 Git 跟踪 6,047 文件、523,274,109 字节。', '其中已归档的原 Git 跟踪文件 6,047 个；**Git 真值（`1ce9a91` 原 blob）为 523,273,912 B**，归档现场为 523,274,109 B（+197 B 勘误行）。')
text = text.replace('| 跟踪文件数 | 跟踪字节 | SHA256 逐文件清单 |', '| 已归档跟踪文件数 | 归档现场跟踪字节 | 转入 fixture | SHA256 逐文件清单 |')
text = text.replace('|---|---:|---:|---:|---:|---|', '|---|---:|---:|---:|---:|---:|---|')
counts = {'M4a_evidence': '1', 'M4c_evidence': '32', 'M5b_evidence': '95',
          'M5c_evidence': '3 搬迁 + 1 复制', 'M5d_evidence': '3'}
lines = []
for line in text.splitlines():
    if line.startswith('| `reports/'):
        cells = [part.strip() for part in line.strip('|').split('|')]
        folder = cells[0].strip('`').rsplit('/', 1)[-1]
        cells.insert(5, counts.get(folder, '0'))
        line = ' | '.join([''] + cells + ['']).strip()
    lines.append(line)
text = '\n'.join(lines)+'\n'
exception = '''## theory_audit.md 唯一字节例外与勘误全文

6047 个已归档跟踪文件中，6046 个与 `1ce9a91` 原 blob 逐字节一致；唯一例外是 [theory_audit.md](file:///D:/eab-evidence/reports/codex/M3_evidence/theory_audit.md)，依 WO-H1 P0.3 在正文前加了 197 B 的勘误行，正文未改。原件可只读 `git show 1ce9a91:reports/codex/M3_evidence/theory_audit.md` 恢复；本轮不改外归档文件或清单。两种总字节口径不可混用。

归档中该行的**原样全文**如下；其历史相对链接会错指外归档根下不存在的 docs，因此在此保留可提交、可审阅的全文并给出当前有效的 [归属总表](../docs/shi_attribution.md)，不偷偷修外部字节：

```markdown
> 勘误（2026-10-19）：石根华两篇原文已核；本报告正文保留历史状态，现行理论归属与 cutting/转动范围订正见 [归属总表](../../../docs/shi_attribution.md)。
```

“转入 fixture”列中的搬迁项不包含在“已归档跟踪文件数”中：表内 134 项为搬迁，表外根级 `reports/bb52_g0_first_look.json` 与 `reports/g2_bdda3d.json` 另搬迁 2 项；另 1 项 `M5c_evidence/research_diagnostics.json` 为复制，仍计入外归档原件。合计 136 搬迁 + 1 复制，总数以 [137 项清单](codex/H1_evidence/frozen_inputs_manifest.json) 为准。

'''
text = replace(text, '## 验证与回退\n', exception+'## 验证与回退\n')
write(relative, before, text)

(OUT / 'documentation_edits.json').write_text(json.dumps(CHANGES, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(CHANGES, ensure_ascii=False, indent=2))
