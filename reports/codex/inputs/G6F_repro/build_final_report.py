"""Build the Chinese G6F deliverables only after the complete suite finishes."""
import collections
import hashlib
import json
import pathlib
import re
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'review'

def read(path):
    data = (ROOT / path).read_bytes()
    return data.decode('utf-16') if data.startswith((b'\xff\xfe', b'\xfe\xff')) else data.decode('utf-8-sig')

def data(path):
    return json.loads(read(path))

def link(path, title=None):
    return f'[{title or pathlib.Path(path).name}](file:///{(ROOT / path).as_posix()})'

def write(path, value):
    (ROOT / path).write_text(value, encoding='utf-8', newline='\n')

def main():
    suite = data('review/notes/full_suite_resume.json')
    suite_text = read('review/logs/full_suite_resume.log')
    suite['summary'] = suite_text.strip().splitlines()[-1]
    assert suite['exit_code'] == 0 and re.search(r'8582 passed', suite['summary']), suite
    baseline = data('review/baseline_hashes.json')
    changed = [p for p, h in baseline.items() if not (ROOT / p).is_file() or hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    assert not changed, changed
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True)
    assert head.startswith('2f6c518') and not subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).strip()
    integrity = dict(head=head,baseline_file_count=len(baseline),sha256_changed=changed,git_status_short=status,
                     time_utc=datetime.now(timezone.utc).isoformat(),tracked_files_unchanged=True)
    write('review/notes/final_integrity.json', json.dumps(integrity,ensure_ascii=False,indent=2))

    source_paths = ['review/notes/geom3_findings.json','review/notes/geom2_precision_findings.json',
                    'review/notes/root_findings.json','review/notes/gates_docs_findings.json']
    findings = [f for p in source_paths for f in data(p)]
    for f in findings:
        f['source_id'] = f.pop('id')
        f['summary'] = f.get('summary', f.get('conclusion', ''))
        f['file:line'] = f.get('file:line', f.get('file_line', f.get('location')))
        f['repro_paths'] = f.get('repro_paths', [f.get('repro_path',f.get('repro_script'))])
        f['status'] = 'confirmed'
        assert f['severity'] in ('critical','major','minor') and f['file:line']
        for key in ('summary','failure_scenario','how_to_reproduce','suggested_fix'):
            assert f[key] and '??' not in f[key], (f['source_id'],key,f[key])
        assert 'verified_output' in f
        for p in f['repro_paths']:
            assert p and (ROOT / p).is_file(), p
    rank = {'critical':0,'major':1,'minor':2}
    findings.sort(key=lambda f:(rank[f['severity']],f['source_id']))
    for i, f in enumerate(findings,1): f['id']=f'G6F-{i:02d}'
    counts=collections.Counter(f['severity'] for f in findings)
    assert dict(counts)=={'critical':1,'major':7,'minor':4},counts

    gates = data('review/notes/gates_g6e_replay.json')
    solid = data('review/notes/solid_replay_results.json')
    roots = data('review/notes/root_g6e_replay.json')
    replay={}
    for f in gates:
        replay.setdefault(f['raw_1_based'],[]).append(dict(origin='上次中断前运行，直接沿用',evidence='review/notes/gates_g6e_replay.json',detail=f))
    for f in solid:
        replay.setdefault(f['g6e_id'],[]).append(dict(origin='上次中断前运行，直接沿用',evidence='review/notes/solid_replay_results.json',detail=f))
    for f in roots:
        replay.setdefault(f['g6e_id'],[]).append(dict(origin='本次当前 HEAD 亲跑原 Python 复现体',evidence=f['log'],detail=f))
    assert len(replay)>=20
    write('review/notes/g6e_replay_index.json',json.dumps(replay,ensure_ascii=False,indent=2))
    sources=sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'src/eab').rglob('*.py'))
    report_data = dict(work_order='WO-G6F',language='zh-CN',reviewed_head=head,confirmed_counts=dict(counts),
        m0_can_exit=False,full_suite=suite,integrity=integrity,findings=findings,
        replay_unique_raw_count=len(replay),replay_raw_ids=sorted(replay),
        replay_index='review/notes/g6e_replay_index.json',
        limitations=['静态分支库存不等于全部分支的独立动态证明','107个旧改动函数未全部逐断言人工深审，仅4种新增隔离源码变异',
                     '正本00部分章节未逐行精读；没有外部论文/学术优先性核证','一般凹表面独立oracle主要覆盖矩形并/认证星核类，非任意嵌入表面穷举'],
        source_files=sources)
    write('review/G6F_findings.json',json.dumps(report_data,ensure_ascii=False,indent=2,allow_nan=False))

    parts=[f'''# WO-G6F：G6 第六轮独立正确性重审

审查方报告（不修代码） · 2026-10-12 · 被审新鲜 detached 工作树 `D:\\eab-wt\\g6f`

## 1. 结论

**confirmed critical=1 / major=7 / minor=4。M0 不可以退出。** 已去重、已运行；未确认问题不入计数。全套全绿不是退出门的替代品。

核心反例是可变 canonical convex view 泄漏缓存别名：源顶点/面未变，仅编辑返回视图，就让同一源的精确成员与相交从 1 变成 −1。其他 major 包括显式凸模型受面提示绕向影响、旧 G0 跳样无牙/错误 oracle，以及局部出口、导数和凸距离辅助 API 的尺度错误。

严重度口径：普通合法源几何被缓存污染、静默错误为 critical；窄输入范围的错误谓词/数值输出或门无牙为 major；响亮拒答、字段缺口及过时弱文档陈述为 minor。特别说明：反绕面发现只针对 `conv(vertices)` 的显式凸契约，不把它当合法一般闭表面；极端数值输出发现不等同于所有默认状态判定都错误。

机读结果：{link('review/G6F_findings.json','G6F_findings.json')}；全部成果：{link('review/INDEX.md','证据与脚本清单')}。

## 2. 续做、范围与基线

- HEAD：`{head}`。开始/收尾 Git 均仅显示 `?? review/`；**{len(baseline)} 份基线文件 SHA-256 零变化**，没有 commit/checkout/reset/stash/worktree/branch 等 Git 写操作。{link('review/notes/final_integrity.json','收尾完整性证据')}。
- 所有新/改文件仅在 `review/`。缺陷注入要么为进程内 monkeypatch 并 finally 恢复，要么在 `review/copies/gates_docs_mutations/` 副本改一处；副本变异后原字节 SHA-256 恢复。未修任何被审源码；未运行姊妹仓库 exe、未改姊妹仓库或实现方工作树。
- 上次全套日志停在约 20%，**是中断日志，不算完成**。保留 {link('review/logs/full_suite.log','旧全套日志')}。上次完成的 13 条 gates 重放和 12 条 solid 重放直接沿用，去重为 20 条，不为数量重复跑；报告第 7 节逐条标注来源。
- 已有二维 20,000 谓词、144 凸包、1,440 成员、144 射线独立 Fraction 扫描沿用旧证据；已有疑点脚本本次加强并亲跑确认。主审查者又对新确认发现复跑：{link('review/notes/root_confirmations.json','主审重复确认输出')}。
- 范围目标是审查，不是数学修复、性能调优或工程认证。回滚锚为原字节 {link('review/baseline_hashes.json','baseline_hashes.json')}；本树本来就是用户给定的新鲜工作树，审查未新建另一 worktree。

## 3. 自跑全套

环境：`PYTHONDONTWRITEBYTECODE=1`、`PYTHONIOENCODING=utf-8`，Python 3.12。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:\\eab-wt\\g6f\\review\\tmp_full_suite_resume
```

**实际末行：`{suite['summary']}`**；退出码 `{suite['exit_code']}`；进程墙钟 `{suite['elapsed_seconds']:.3f} s`。这是本次审查自己跑出的结果，不引用实现方 870 s 当实测。

{link('review/logs/full_suite_resume.log','完整日志')} · {link('review/notes/full_suite_resume.json','命令/退出码/耗时')} · {link('review/repro/run_full_suite.py','可重跑 runner')}。

另亲跑 LP 证书、E4 自校验和 PERF 接触窗三个文件：**274 passed in 12.29s**；文档镜头独立性/指针/窗口定向门 **30 passed in 0.80s**。这两组是定向补验，不加进 8582。

## 4. 已确认发现表

| ID | 级别 | 位置 | 一句话结论 | 可运行证明 |
|---|---|---|---|---|
''']
    for f in findings:
        proof=' / '.join(link(p) for p in f['repro_paths'])
        parts.append(f"| {f['id']} | {f['severity']} | `{f['file:line']}` | {f['summary']} | {proof} |\n")
    parts.append('\n## 5. 每条复现输入、输出与建议\n\n以下均为确认故障的实跑，不是修复方案已实施。脚本在同一 HEAD 上运行；具体反例中有理数 oracle 不调用被测几何 helper。\n')
    for f in findings:
        v=f['verified_output']
        output=v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)
        parts.append(f"\n### {f['id']} · {f['severity']} · {f['summary']}\n\n位置：`{f['file:line']}`；分审原编号 `{f['source_id']}`。\n\n**输入 → 错误输出：** {f['failure_scenario']}\n\n**重现：** {f['how_to_reproduce']}\n\n"+' · '.join(link(p) for p in f['repro_paths'])+f"\n\n```text\n{output.strip()}\n```\n\n**建议（未修改）：** {f['suggested_fix']}\n")
    parts.append(f'''
## 6. 九个镜头的覆盖与结果

### 镜头 1：精确声称与浮点分支

全 `src/eab/` 的 **30 个模块、1399 个 Compare 节点、161 个容差语法候选**已作 AST 库存并按函数/调用角色分类，见 {link('review/notes/tolerance_inventory.json','分支库存')}。它包括比较符零/非零、名称含 tol/noise/eps/band 等的候选，**不是“1399 个都是浮点容差裁决”**，也不是每点都动态证正确。

- 允许域窗口/报告：covers 的显式长度/角度/枚举窗；`near_labels`、nominal tie 标签；margin 的显式 `contact_window/atol`；limit 的 `uncertainty/resolvability` 和 `tol*fmax` 截断展示 force/active。展示字段不是静力证书，后者从 lambdas 精确核。
- 允许启发式且兜底：LP 浮点选基/缩放/松弛后必须 `_Exact.certify` 或有理 simplex；predicates 的符号过滤与 exact_geom 区间排除不确定时回 Fraction；纯整数代数优化不是浮点过滤。
- 确认有答案影响：`is_convex/reflex_edges` 隐式 noise 分类、旧距离/出口 G0 的 band 跳样及其 oracle。见对应已确认项。
- 活代码与历史代码区分：geom3 的旧 `_contact_cone_witness/_gordan_direction/_active_normals` 不在当前 `polyhedra_overlap → exact_geom.surface_overlap` 决策链，未因 grep 容差而虚报默认贯入错误。读入器 `strip_duplicate_vertices` 的噪声剥点是仍存的 legacy 几何简化口径，不算默认数学内核 exact 已证明。

### 镜头 2：浮点过滤与缓存

上次 20,000 二维谓词极端指数扫描沿用；本次三维 orient/cross/dot 极端过滤 12,000 格、polygon locate 区间快路 900 格、LP reduced-sign 8,000 格独立 Fraction 比较均零错。含次正规、下溢/上溢中间量、巨大坐标、混合指数及 Fraction 转 float 不可表示格。读过过滤误差界与 fallback 链；**没有穷举或完成普适误差界的形式证明**。

缓存检验包含内容替换 warm-vs-clear、Dual 拒收而非静默 primal 命中，找到返回可变 convex view 的别名污染。其他事件/三角化/距离缓存按完整内容与必要实现指针读了键；未穷举任意自定义可变 numeric。{link('review/repro/root_lp_audit.py','LP 独立过滤/顶点 oracle')}。

### 镜头 3：Oracle 独立性

重点核 E2–PERF 的主 oracle：2D 内联 SAT/gift-wrap/support；3D g03_exact 全点整数/有理凸包及 SAT；一般表面、margin/frozen、最早互锁和 PERF 窗口的自有耳切/扫掠/Gram/Gordan/区间积。未发现新主 oracle 直接复用生产几何原语的已确认实例。

不夸大独立性：`test_lp_certificates._exact_limit_lp` 仍共享 `_build_columns` 锥方向/owner 的模型定义，独立重建的是力矩、平移、容量与 simplex；它不能单独证明该共享模型。2D/3D brute、旧凹 G0 等共用几何或事件者仅是佐证。实际错误 oracle 已入发现，不把“函数叫 brute”当独立证明。

### 镜头 4：旧门迁移是否变弱

对 `git diff b6126cf..HEAD -- tests/` 的 **89 个改动测试/辅助文件、107 个改动既有函数**保存旧/新源码和 assert AST；台账核 E2 的35格、E5a41项、E5a2 18项、E5b21项及 E3E4/PERF。{link('review/notes/gates_docs_inventory.json','完整库存')}。

本次额外 **4 种**隔离源码变异，baseline 全绿而 mutant 语义断言红，恢复 SHA：2D 边界错票、3D 保留非极点、棱弧端点标 strict、微台阶误合并。微台阶变异中旧0.5格仍绿，新2^-80/1e-12门红，如实记录。{link('review/notes/gates_docs_mutations.json','红断言及恢复字节')}。

未找到“旧能抓而当前完整新体系漏抓”的另一已确认迁移逃逸；但旧凹 G0 噪声跳过能让真实内核枚举删除仍 pass，已单列 major。**107 个函数没有各自全做人工可达链/变异**，不会把节点数不降当“不弱化”证明。

### 镜头 5：独立几何压力

- 沿用二维 144 hull / 1440 member / 144 ray；新增 **175 凸局部出口 + 150 凹 L 射线首入**，自写 Fraction oracle 均零错。
- 三维一般 L 凹柱/含 cavity 中空盒：**132 格**独立区间积并模型，含尺度1e-9、平移1e8与精确轴循环，成员/相交零错；非单调 cavity 最早抬升 **24 格中20正确，4格响亮拒答**归入同一 minor。
- 相同几何平移/缩放中的反例包括二面角噪声、辅助投影的工程坐标消去、极小尺寸局部出口 gap/距离下溢、Dual 单位缩放。覆盖共线/共面/平直、微尺寸、混合和退化数据；非法自交/非流形/零体积不在一般表面结果保证范围。
- 任意凹对全局最短分离不是已交付 API 契约；局部 shortest_exit/shortest_exit3 不外推为全局问题，未将明确限制重新算缺陷。

### 镜头 6：局部贯入厚度窗口

读 `star_core/contact_models → exact overlap → margin/interlock OR` 证书链，自己另写 **75 盒对、12 个被接受模型**：区间积核六轴非贯入与位移平方=w²；homothety 比例和全顶点最大径向段平方≤w²，加凸范数论证给连续壳上界，不只是抽查碰撞点。未找到可靠性命题反例。

六轴成功推出 PD≤w；星核薄壳仅推出每处严格重叠在径向厚度≤w壳内，**不**推出短刚体脱离。坐标轴/L1 旋转依赖、斜向短脱离漏检、报贯入不推出 PD>w 都已明示。{link('review/repro/geom3_independent_stress.py','独立表面/窗口压力脚本')}。对任意非星形凹表面不是完备 PD 或全壳算法认证。

### 镜头 7：极限分析

本审查自己写 Fraction 高斯消元与有界小 LP 全基顶点枚举：**180 格**目标正确，快过滤与纯有理符号路径答案一致，通常 OPTIMAL `x/y` 与 `exact_x/exact_y` 单次舍入视图一致。仅零约束最优快路漏 exact 见证入 minor，非错误最优值。

单/多体独立闭式滑动/倾覆 **60 对**，荷载2^(-600)..2^600、微尺寸与大平移，精确 alpha 均正确；分别注入 alpha/lambda/机制10^-100误差 **180+180 次全部拒绝**，真实 limit_load 路径4种毒化（float/Fraction alpha、exact_x、exact_y）全抛 self-check。{link('review/repro/root_limit_guard.py','独立构造错误候选脚本')} · {link('review/logs/root_limit_guard.log','输出')}。

旧9/11/20/21/22/45原输入重放均不再给原错误。可分辨报告按文档只报告、不改原 status/alpha；承认一阶 U 和 alpha_min=0 刀刃可能漏筛，不称全不确定性稳定证书。没有另找到精确自校验漏掉错误 optimal 候选。

### 镜头 8：文档、代码、正本

README/canon_map/两设计共库存 **69 条**✔/完成/实现/有门声称，具名测试指针能解析，定向指针门通过；不是逐句定理验证。canon 第八节 “07 对代码” 的 ContactRecord 生命周期/溯源缺口、Phase0 3而非6读取器、G2手写清单、G1锁态缺口、G3/G4/G5/M3剩余项与正本07基本如实映射。canon 命题1行仍错误说 margin 先 float 差点，确认 minor。

正本01/03/07全文读取并核关键数学/设计条目；00主要精读§3/§4/§6.2，其余历史/完整文献未逐行审读。没有借正本文献声称做外部学术优先性认证。README 三维“最短出口”标题未同步局部限定列未确认，不追加 major。

### 镜头 9：第五轮回归重放

**{len(replay)} 条去重原发现**已重放原输入或等价输入；上次20条证据直接沿用，本次新增6条。都只说“该原反例不再成立”，不把选取的26条外推为50条关闭。完整输入/输出与出处：{link('review/notes/g6e_replay_index.json','重放索引')}。

## 7. 原始回归逐条来源

编号为 `g6e_findings_raw.json.findings` 数组 **1 起始**位置，不是过时源码行号。

| 原编号 | 本轮证据来源 | 当前观察与边界 |
|---|---|---|
''')
    for raw, entries in sorted(replay.items()):
        origin=' / '.join(dict.fromkeys(e['origin'] for e in entries))
        ev=' / '.join(link(p) for p in dict.fromkeys(e['evidence'] for e in entries))
        if raw==9:
            observation='原切向不安全值改为 ValueError；这是预期入口拒收，不将退出码1当重放失败。'
        elif raw in (11,20,21,45):
            observation='构造的错承载/贯入/次优解全部被拒绝；未再发生旧放行。'
        elif raw==22:
            observation='单/多体及无关远体下 alpha、U 一致，不再篡改原状态。'
        elif raw==40:
            observation='默认分支不再 NameError；有诊断 hull_anomaly 计数，不据此说所有G0格正确。'
        else:
            observation='沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。'
        parts.append(f'| {raw} | {origin}；{ev} | {observation} |\n')
    parts.append(f'''
## 8. 未确认与不计数

1. README 三维已侵入“最短出口”未当场限定局部，设计与 docstring 已限定；没有另写合法一般凹体新反例证明本次新增核心承诺，未入计数。
2. `_exact_limit_lp` 共享锥方向/owner 模型的共同错误风险，没有独立制造出当前解析门也漏掉的错误，因此仅作独立性覆盖不足，不入 confirmed major。
3. 未找到已查过滤、六轴/薄壳可靠性、矩形并类一般表面的静默反例；零错搜索不是正确性证明。
4. 边界由 float 旋转舍入后变了实际数据，逐格 exact oracle 要核新数据，而非强行保理想计数。没有将此原则作为样本跳过许可；实际 G0 跳样仍计 major。

## 9. 完整性批评（明确不能据此推论的内容）

- `src/eab/` 30 个 Python 模块均至少静态扫描；二维6模块、三维10模块逐函数审读，主审读 LP/limit/limit_multi/Dual/contact_record/rational3/predicates 和4读取器。margin 关键原语、窗口、缓存、闭合、凸投影和冻结路径读过；**不声称每个源码 token 都完成人工形式证明**。没有完全未打开的生产 Python 模块；测试和 tools 远未全逐行读。
- **未逐行审读全部 tests 文件**：重点/执行/静态库存与逐函数深审不等价；107个既有改动函数未各自做全调用链检查与变异，69条具名声称未各自单独隔离运行。详细分审说明见 {link('review/notes/gates_docs_final.md','文档/迁移完整性批评')}。
- 00 正本早期历史、其余应用段、完整参考文献未逐行精读；03需求侧文献及全部外部原论文未核；DDA4.x导出事实沿用既有本地记录，没重新打开导师源码。不能据此提供外部文献、学术优先性或任何法律认证。
- 一般凹表面独立压力主要是矩形并/中空盒及认证星核/测试专用族；未构造覆盖任意非星形凹表面的独立体积 oracle，未穷举任意环耳切退化/随机 SE(3)。非法自交、非流形、零体积和任意自定义可变 numeric 的结果域未认证。
- 浮点过滤采样与手读误差界不是对所有 binary64 输入的穷举证明；缓存源内容/Dual/返回别名已查，任意所有外部别名组合未穷举。几何/力学单位不变性压力不能代替全域证明。
- 根、状态、距离显示与构造/证书的边界分开：未把 float 根显示重新逐顶点平移当同一 exact_motion 证书；没有修姊妹适配器、部署 shadow 开关或进行动力学/岩石标定。
- 本轮已经找到足以阻 M0 的确认缺陷，**完整性边界不会被全套绿补齐**。实现方修复后仍需独立复核，不能由本文 suggested_fix 或本轮重放推断修复已完成。

## 10. 交付与重跑

- {link('review/G6F_report.md','本中文总报告')}
- {link('review/G6F_findings.json','机读发现（含实际输出）')}
- {link('review/INDEX.md','全部证据、复现脚本与目录清单')}
- {link('review/notes/final_integrity.json','被审文件未改证明')}

复现脚本只写 `review/`，不要在姊妹仓库/实现方树执行。确认反例可运行 {link('review/repro/root_confirmations.py','主审确认 runner')}，另运行 `root_dual_scaling.py`、`root_boundary_contracts.py`、`root_margin_projection.py`。源码变异只用 {link('review/repro/gates_docs_mutations.py','副本 runner')}；全套用 `run_full_suite.py`，后者若重跑会更新本次续跑日志/结果。

G6F_DONE critical={counts['critical']} major={counts['major']} minor={counts['minor']}
''')
    write('review/G6F_report.md',''.join(parts))
    index=['# G6F 成果与证据索引\n\n','所有文件在审查专用 `review/`，被审跟踪文件没有修改。上次输出沿用和本次输出的区别见总报告及重放索引。\n\n']
    for p in ('review/G6F_report.md','review/G6F_findings.json','review/baseline_hashes.json'):
        index.append('- '+link(p)+'\n')
    index.append('\n## 文件\n\n')
    for folder in ('notes','repro','logs'):
        index.append(f'\n### {folder}\n\n')
        for p in sorted((REVIEW/folder).glob('*')):
            if p.is_file(): index.append('- '+link(str(p.relative_to(ROOT)))+'\n')
        if folder == 'notes' and not (REVIEW/'notes/deliverable_qa.json').exists():
            index.append('- '+link('review/notes/deliverable_qa.json')+'\n')
    index.append('\n## 目录\n\n')
    for p in sorted(REVIEW.iterdir()):
        if p.is_dir(): index.append('- '+link(str(p.relative_to(ROOT)))+'（副本/临时测试产物按目录交付，不逐文件铺在聊天）\n')
    write('review/INDEX.md',''.join(index))

    # Deliverable read-back and machine-checkable consistency.
    reread=data('review/G6F_findings.json')
    assert len(reread['findings'])==sum(counts.values())
    assert read('review/G6F_report.md').strip().splitlines()[-1]=='G6F_DONE critical=1 major=7 minor=4'
    for p in ('review/G6F_report.md','review/G6F_findings.json','review/INDEX.md'):
        assert '\ufffd' not in read(p) and '????' not in read(p)
    qa=dict(json_parses=True,findings_count=len(findings),confirmed_counts=dict(counts),
            all_repro_paths_exist=True,chinese_text_intact=True,required_final_line=True,
            tracked_baseline_unchanged=True,full_suite_summary=suite['summary'],
            artifact_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('review/G6F_report.md','review/G6F_findings.json','review/INDEX.md')})
    write('review/notes/deliverable_qa.json',json.dumps(qa,ensure_ascii=False,indent=2))
    print(json.dumps(qa,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
