"""Generate the Chinese work-order report from reviewed persistent evidence."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent

def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8-sig'))

def link(name, label=None):
    p=ROOT/name
    return f'[{label or p.name}]({p.as_uri()})'

def ev(name,label=None):
    return link('reports/codex/E3E4_evidence/'+name,label)

def cell(v):
    return str(v).replace('|','\\|').replace('\n',' ')

def main():
    final=read('final_full_result.json')
    scope=read('scope_audit.json')
    dispositions=read('g6e_dispositions.json')
    mutations=read('mutation_results.json')['results']
    assert final['returncode']==0 and final['source_unchanged']
    assert len(dispositions)==14 and len(mutations)==10 and all(d['byte_restored'] for d in mutations)
    lines=['# WO-E3E4：二维收尾精确化与极限分析有理数自校验','',
           '执行日期：2026-10-12；工作树：`D:\\eab-wt\\cx-e2`；分支：`codex-work`；基线及交付 HEAD：`e1fbbd4`。未提交。','',
           '## 1. 结论与验收边界','',
           f"- 本单负责的 14 条第五轮发现全部逐条处置：5 条已由后续提交消解，9 条在本单修复或加强（含测试盲区）；不把旧审查对象 `b6126cf` 的全部 50 条发现都宣称关闭。机读表：{ev('g6e_dispositions.json')}。",
           '- E3 默认数学判定用给定浮点数的精确有理值；显式 legacy 域窗口只放宽。E4 静力、对偶、互补及机构容许性在同一精确模型上核验；可分辨性只报告，不再篡改原问题状态或承载因子。',
           '- 10 项一次性真实源码突变：9 项被语义门抓住（D1/D2 是有效输入不应出现的拒答异常，其余为目标断言）；D9 被精确互补冗余保护，单独放宽间隙不改变最终拒绝。所有项均恢复原字节 SHA-256。详见第 5 节。',
           f"- 全套原样末行：`{final['last_line']}`；进程墙钟 **{final['elapsed_seconds']:.3f} s**；运行期间 src/tests 哈希不变。{ev('final_full.log','完整日志')} / {ev('final_full_result.json','命令、耗时与源码哈希')}。",
           '- 用户禁止新建 worktree/clone，故仅当前树验证，不能声称满足纪律 D 的新鲜树验收；三路协作和只读交叉检查也不等于六路独立 G6。本单 DONE 不等于里程碑/G6 退出。','',
           '## 2. 第五轮 14 条处置表','',
           '行号均为原始发现的键，不是新源码行号。baseline 证据指本单开始的 `e1fbbd4`；current 指本工作树。没有按 `verdicts_raw` 的不可靠顺序配对。','',
           '| 原发现键 | 处置 | 当前基线复现与处理依据 | 修前红门 / 修后门 |','|---|---|---|---|']
    for key,d in sorted(dispositions.items()):
        status=d['status']
        if status=='already_resolved': status='已由 '+d['resolved_by']+' 消解'
        if status=='fixed_this_work_order': status='本单修复'
        before=d.get('baseline_reproduction',d.get('baseline_output'))
        after=d.get('final_reproduction',d.get('current_output'))
        evidence=d.get('evidence',d.get('summary',''))
        refs=' '.join(link(p,lab) for p,lab in ((before,'基线输出'),(after,'当前输出')) if p)
        red=d.get('red_before')
        if isinstance(red,dict): red=json.dumps(red,ensure_ascii=False)
        gate=d.get('gate') or '已消解项不重复制造缺陷；原复现如表'
        assertion=d.get('red_assertion',d.get('assertion',''))
        lines.append('| '+ ' | '.join(map(cell,[key,status,evidence+' '+refs,(str(red or '')+' '+str(assertion)+' '+gate).strip()]))+' |')
    lines += ['',
        '关键语义红断言：geom:434 是真极点必须在凸包；covers:238 是 `strict == 独立邻点支持真值`，不是盖后追加假标签；limit:729/732 是 `not static_ok`；multi:147 是贯入机构不可容许；multi:177 是加入无关远体后 uncertainty 必须与孤立体相同；multi:348 是精确静力可行的次优插值仍 `not ok`；测试238是非零有理残差与微小贯入必须拒绝；测试268关闭无界筛查时，四条 `resolvability` 报告断言确实红。',
        '', '## 3. E3 / E4 实现摘要与精确性口径','',
        '### E3','',
        '- 凹首入的初态、时刻裁决、候选前自检使用 `polygons_overlap_exact(A,B,X)`；X 在 Fraction 上相加，不先浮点平移。VE/EV 间隙分子沿运动仿射，根 `-g/slope` 精确；共线滑移的端点事件另计，各自时刻投影边内也精确。',
        '- 候选前自检不仅探一步，还核此前全部原始顶点—边事件，捕获“更早撞入又分离”的窄区间；无候选也核事件，漏候选不静默。`tied_labels` 只含精确同时项，`near_labels` 单独报告；`t_exact` 保存精确时刻。',
        '- `shortest_exit` 在精确有效/边内的非正 gap 中比较有理平方距离，取最浅局部盖（最大非正 gap）。它不是一般凹对的全局最小分离算法。brute 的 Fraction 扫描/二分仍会漏孤立切触，且共用精确相交，只能作佐证。',
        '- 局部 VE/EV/VV 默认无噪声带；VV 锥交与严格活跃取精确符号，边界不标 strict。显式窗口另报 `window_active`，不冒充严格性。距离/投影窗口精确平方比较，无舍入地板。',
        '- `convex_hull` 始终接 `hull_exact` 保留真极点；tol 仅兼容签名，不隐式简化。全仓没有需要非零简化窗的调用。删 `_angle_tols` 等死噪声代码；geom 的浮点对照/统计函数仍有调用，文档明确不是生产精确判定。',
        '- 追踪精确相交依赖链时补修 triangulate 的浮点面积朝向、Fraction orient 的浮点过滤；极小/极大尺度朝向门先红后绿。G0 诊断重建出口点保持被测浮点加法次序 `(A+x)+t*u`，避免拿另一份舍入数据归因。',
        f"- 独立主门：闭式、测试内 Fraction 分片 SAT / winding / 邻点支持、VV Fourier–Motzkin；不调用生产几何原语。细节见 {ev('notes_entrance.md')} / {ev('notes_covers.md')}。",'',
        '### E4','',
        '- LP 算法不变，`LPResult.exact_x/exact_y` 保留证书的有理数见证。返回 alpha/lambdas/mechanism/row_duals 是带不可变 exact 的 float 视图；自检独立重建物理力矩和精确 c·A，不复用 LP 力矩/荷载平移原语；锥方向/列序仍是双方共用的模型定义，不声称模型定义零共用。',
        '- 精确核验逐体平衡、λ/α非负、黏聚上限、各列相对功率、drive≥1、强对偶及逐项互补。α>0 时互补强制 drive=1；α=0 不额外错误强制等号。tol 与 *_rel 都不参与通过判定。',
        '- “任意 k”是有理数算法性质；门覆盖 k=3,5,9,15,30,100，并覆盖 μ=1e-5、ΣcA/W=1e-5、远体1e4、h/L量级1e3及三维多体。Fraction 保留误差；若 float(1−10^-100) 已舍回1，输入根本未变，不可能识别未表达的信息。',
        '- `contact_forces`/`active` 是按 tol 截断的展示，不是静力证书；静力来自完整 lambdas。复制保留 exact，普通算术/float()/JSON 往返会丢见证，之后按新给定数核；如需重用证书应显式保存有理分子分母。',
        '- 多体可分辨性用每个体自己的接触形心与臂长；保留本体调用方构造力矩的原点距离噪声项，不借其他体跨度。局部舍入扰动精确移回 LP 公共原点。',
        '- 新 `resolvability` / `resolvability_statuses` 分别报告 resolved、nearby_infeasible、unresolved、not_applicable 与±扰动状态。即使邻域不可行或由无界变有限，原问题精确 status/alpha 不变。resolved 只是单机构筛查未见超阈变化，不是稳定性/工程误差保证。',
        f"- 只读交叉探针把 exact 加1e-100、保持float读数相同，仍拒绝被改alpha/λ/机构/行对偶；见 {ev('cross_review_limit_probe.json')}。这不替代 G6。",'',
        '## 4. 旧测试改写台账与失败保留','',
        f"总机读账：{ev('test_changes.json')}；每次失败节点：{ev('failure_inventory.json')}；AST 实际变化函数清单：{ev('changed_test_functions.json')}。原失败日志全部保留，不将预期修前红、接口字段缺失或重复运行计成独立数值缺陷。",'',
        '| 测试 / 辅助函数 | 旧口径 | 新口径 | 为什么不更弱 |','|---|---|---|---|']
    records=[]
    def add(d):
        node=d.get('nodeid',d.get('node',d.get('test',d.get('function',''))))
        old=d.get('old_contract',d.get('old',''))
        new=d.get('new_contract',d.get('new',''))
        why=d.get('not_weaker',d.get('why',d.get('reason','')))
        if node and old and new: records.append((node,old,new,why))
    for d in read('entrance_changes.json')['modified_old_tests']: add(d)
    cv=read('covers_test_changes.json')
    for group in cv.values():
        if isinstance(group,list):
            for d in group:
                if isinstance(d,dict): add(d)
    for d in read('limit_test_changes.json'): add(d)
    sp=read('screen_policy_test_changes.json')
    for d in sp['changes']: add(d)
    oracle=dict(sp['oracle_correction']); oracle['function']='tests/test_lp_certificates.py::'+oracle['function']; add(oracle)
    seen=set()
    for row in records:
        # Parameter-level rows remain in JSON; table groups identical contracts, preserving function names.
        base=row[0].split('[')[0]
        key=(base,*row[1:])
        if key in seen: continue
        seen.add(key)
        lines.append('| '+' | '.join(map(cell,key))+' |')
    lines += ['',
        '补充辅助函数：`test_limit_arch.py::_solve4` 改独立有理数消元；`test_invariance_2d.py::_covers` 去历史噪声传参并另用独立 oracle。所有原几何/参数输入保留；没有通过删格、skip、xfail或扩大容差来换绿。bb52 strict-only 变异的旧废弃投票计数从110/106变为640/630，是精确strict后的新固定结果；距离/出口红牙断言仍保留精确核对，非改成“任意计数”。',
        '收尾读回纠错：bb52 台账曾称已加584/603与逐距离归因断言，但CRLF模板在LF文件静默零匹配。主代理发现后中止190.110 s的首次全套，保留中止日志；真正补入两条断言并定向核验后，从头运行本报告的最终全套。先前27.58 s绿日志不冒充新增两条的验证。此为验证/编辑错误，不是新的几何缺陷。',
        '', '## 5. 十项源码突变与实际报红断言','',
        f"机读结果、补丁、命令、JUnit失败全文、前后SHA：{ev('mutation_results.json')}。所有变异均落到生产被测路径，非产出后追加假数据；串行执行，每项 finally 恢复原字节。",'',
        '| 项 | 变异 | 实际结果 | 目标断言审读 |','|---|---|---|']
    descriptions={
        'D1':'凹首入精确相交改回浮点平移+polygons_overlap(ctol)',
        'D2':'凹候选根改原始gap分子/仿射斜率的浮点商后转Fraction',
        'D3':'删除候选之前的精确漏候选自检',
        'D4':'局部出口平方距离取max（等价取最小负gap）',
        'D5':'局部无窗口VE退回旧角度/坐标噪声带',
        'D6':'VV开锥边界 > 改 >=',
        'D7':'二维凸包改回浮点容差pop',
        'D8':'静力残差退回浮点全力尺度相对带',
        'D9':'多体共用核的对偶间隙退回全局尺度带',
        'D10':'多体筛查退回全局形心/臂长'}
    for d in mutations:
        failures=d.get('failures',[])
        if failures:
            f=failures[0]
            detail=f.get('assertion',f.get('message',''))
            detail=str(detail).splitlines()[0]
        else:
            detail='良性冗余：精确静力可行+对偶可行+逐项互补仍拒绝次优；见下式。'
        detail += '；'+d.get('semantic_review','')
        lines.append('| '+' | '.join(map(cell,[d['id'],descriptions[d['id']],d['last_line']+' '+ev(d['log'],'日志'),detail]))+' |')
    lines += ['',
        'D9 不是漏抓：在静力平衡成立时，`upper−alpha = Σ(lambda_j*power_j) + Σ(slack_r*row_dual_r) + alpha*(drive−1)`。精确可行性与逐项互补为零已经蕴含强对偶。D9 仅放宽 gap，互补检查仍按精确非零拒绝静力可行的次优插值；不能为强行造红删除第二道独立保护。D8 则直接看 `static_ok`，即使其它子检查也拒绝，仍证明静力子门自身有牙。','',
        '## 6. 全仓调用点分类','',
        f"以下逐调用点来自 src/tools/tests AST 扫描（含别名函数名）；历史报告中复制脚本不是生产调用。完整机读信息含调用表达式：{ev('callsite_classification.json')}。默认数学路径与真实 legacy 域窗严格区分。",'',
        '| 调用点 | 函数 | 归类 | 理由 |','|---|---|---|']
    for d in read('callsite_classification.json')['calls']:
        lines.append('| '+' | '.join(map(cell,[f"{d['file']}:{d['line']}",d['callee'],d['classification'],d['reason']]))+' |')
    lines += ['', '## 7. 验证、范围审计与重跑','',
        f"- 最终全套命令：`{' '.join(final['command'])}`。环境 `PYTHONDONTWRITEBYTECODE=1`，`TEMP/TMP=reports/codex/E3E4_evidence/tmp/`，关闭 pytest cache。",
        f"- **原样末行：** `{final['last_line']}`。进程墙钟 `{final['elapsed_seconds']:.6f} s`；上一单用户提供400 s / 7500条，只作背景，不当同环境性能基准。",
        f"- 已运行 `python -X utf8 tools/fix_canon_ptrs.py --apply`；文档指针门在最终全套中通过。{ev('fix_canon_ptrs.log','指针修复日志')}。",
        f"- HEAD/分支未变、暂存区无修改；{scope['tracked_fixture_count']} 个基线跟踪 fixture 哈希不变、无删除；`git diff --check` 通过。{ev('scope_audit.json','范围审计')}。所有写入限当前工作树，无姊妹仓库写入、无 Git 写操作。",
        f"- 初始回滚锚：{ev('initial_manifest.json')}；各次变异与基线源字节备份在忽略目录 tmp/。持久证据索引：{ev('INDEX.md')}。",'',
        '重跑（PowerShell，在当前工作树）：','',
        '```powershell',
        "$env:PYTHONDONTWRITEBYTECODE='1'",
        "$env:TEMP=$env:TMP=(Resolve-Path 'reports/codex/E3E4_evidence/tmp').Path",
        'python -X utf8 reports/codex/E3E4_evidence/run_pytest.py final_full tests',
        'python -X utf8 reports/codex/E3E4_evidence/audit_scope.py',
        '```','',
        '突变仅在没有编辑/其它pytest进程时重跑：先run_entrance_mutations.py，再run_mutations.py covers_mutations.json，再limit_mutations.json；均使用上述环境和python -X utf8。', '',
        '## 8. 遗留与非目标','',
        '1. 未做用户禁止的新鲜 worktree 验证；未做六路独立 G6。需所有者后续验收，README没有把本单全绿替代G6。',
        '2. 未实现一般凹块全局入口块/盖裁剪；最浅局部出口不保证一次移动清除所有接触。brute非完备独立oracle。',
        '3. 三维几何E5、其余第五轮发现、工程标定/动力学/几何非线性均不在本单。三维锥仍是给定浮点方向的离散模型；精确算术不消除模型误差。',
        '4. 极端指数浮点输出构造可舍入/下溢；本单保证分支对给定数据精确，不宣称所有float输出任意指数准确。非有限或任意巨大角域窗口未扩为完整保证；legacy sin3°等实际域窗已测。',
        '5. 显示序列化不是精确证书序列化；输入可分辨性筛查并非全对偶面/全不确定性界。', '',
        'E3E4_DONE']
    (ROOT/'reports/codex/E3E4_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('wrote reports/codex/E3E4_report.md')

if __name__=='__main__': main()
