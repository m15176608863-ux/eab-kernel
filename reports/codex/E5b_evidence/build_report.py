"""Build the Chinese delivery report only from completed, source-bound evidence."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


def link(name, title=None):
    return f'[{title or name}]({(ROOT / name).as_uri()})'


final = read('final.json')
audit = read('delivery_audit.json')
inventory = read('test_inventory_audit.json')
disposition = read('49_disposition.json')
findings = read('g6e_3d_disposition.json')
rewrites = read('test_rewrites.json')
assert final['exit_code'] == 0 and final['sources_unchanged_during_run']
assert len(disposition) == 49 and all(r['final_status'] == 'passed' for r in disposition)
assert not any(audit.get(k) for k in ('removed_tests', 'changed_decorators', 'missing_nodes', 'failed_nodes', 'skipped_nodes', 'changed_fixtures', 'unresolved_g6e_gate_references', 'source_drift_since_final'))
assert audit['branch']=='codex-work' and audit['head'].startswith('3566708')
assert not inventory['increased_skip_xfail_references']

mutations = []
for row in read('interlock/mutations.json'):
    mutations.append(dict(component='interlock', mutation=row['mutation'], target_assertion=row['message'], status='KILLED' if row['killed'] else 'ESCAPED', evidence='interlock/mutations.json'))
for row in read('margin/mutations.json'):
    mutations.append(dict(component='margin', mutation=row['id'], target_assertion=row['killed_by'], status=row['status'], evidence='margin/mutations.json'))
for row in read('entrance/mutations.json')['mutations']:
    mutations.append(dict(component='entrance/frozen', mutation=row['name'], target_assertion=row['target_assertion'], status='KILLED' if row['killed'] else 'ESCAPED', evidence='entrance/mutations.json'))
mutations.append(dict(component='exact_geom', mutation='plane distance bound > changed to >=', target_assertion='closed boundary equality must not be rejected', status='KILLED', evidence='tests/test_e5b_triangle_near.py'))
mutations.append(dict(component='geom3', mutation='cache signature drops vertex content', target_assertion='vertex-content invalidation', status='KILLED', evidence='tests/test_e5b_polyhedron_cache.py::test_cache_vertex_signature_mutation_is_caught'))
(OUT/'mutation_table.json').write_text(json.dumps(mutations,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

passed_target = final['wall_seconds'] <= 900
status = 'E5b_PARTIAL：显式窗口完整贯入深度契约未完成' + ('' if passed_target else '；全套独占墙钟耗时仍超过 900 秒目标')
perf = dict(baseline=dict(head='3566708',pytest_seconds=1578.67,passed=7953,failed=49,total=8002),
            final=dict(wall_seconds=final['wall_seconds'],last_line=final['last_nonempty_line'],nodes=audit['current_nodes'],sources_unchanged=True),
            wall_target_seconds=900,target_met=passed_target,contact_window_full_depth_contract_met=False,
            caution='Baseline was red, and final has additive gates. Not a same-workload benchmark. Microbenchmarks are separate exact-value comparisons.')
(OUT/'performance_summary.json').write_text(json.dumps(perf,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

rows = []
def put(text=''):
    rows.append(text)

put('# WO-E5b 执行报告')
put('\n## 结论与信任边界')
put(f'工作树全套 **{final["last_nonempty_line"]}**；独占进程墙钟 **{final["wall_seconds"]:.2f} s**。49 个原失败节点全部通过。原 8002 个收集节点全部仍在，当前 {audit["current_nodes"]} 个；没有 skip/xfail、删测试、缩装饰器网格或 fixture 改动。')
put(f'\n基线 HEAD 仍为 `{audit["head"]}`，分支 `codex-work`，仅交付工作树，未 commit/push/reset/checkout/stash/worktree。{audit["fixture_count"]} 个 fixture 的字节哈希不变。运行前后 src/tests/tools 哈希逐项一致，日志哈希 `{final["log_sha256"]}`。')
put('\n**未完成项：显式 contact_window 当前仅实现六轴刚性脱离证书 OR 局部径向薄壳政策，不等价于完整贯入深度≤w判定。此前局部/全局深度口径澄清未收到确认，不能将替代政策算成工单契约完成。** 全套绿只证明下列已明确界定的实现与门，不消除此差距。')
put('\n这是本树开发验证，不是独立六路 G6、全新 worktree 退出、DDA/TIA 工程标定或生产部署。工单禁止创建 worktree，因此没有伪称满足常驻纪律 D/G6 的里程碑退出。')
put('\n关键证据：'+ ' · '.join(link('reports/codex/E5b_evidence/'+p,t) for p,t in [('final.log','全套日志'),('final.json','命令、时间与源码哈希'),('final.xml','JUnit'),('delivery_audit.json','交付审计'),('INDEX.md','完整证据索引'),('changed_files.md','改动文件链接清单')]))

put('\n## 1. 契约实现与范围')
put('''
### 默认精确 + 显式接触窗口

L1/L2 按给定数值的精确有理值判定；`None`/0 不再启用旧 ctol。真微贯入返回 PENETRATING / INSIDE，真正间隙不钳零。默认距离、δ、关注带、closed 状态以精确平方量判定；即使显示值下溢为 0，closed 状态仍按精确量。`entrance_block_convex` 先有理化原坐标，再构造差点。

显式窗口 w 是调用方的报告政策：分离侧比较距离平方与 w²；贯入侧用共享 `contact_models` 的六轴刚性脱离充分证书 OR 局部径向薄壳政策——原实体对、A 的六个 ±w 轴平移、可认证星核的 A/B 内核收缩。收缩壳径向厚度严格不超过 w；任何证书模型非贯入则报相触。margin 和 interlock 使用同一集合，盒闭式门验证根处 ON、稍低 INSIDE。

**重要限定：该窗口不是任意方向完整欧氏穿透深度算法。** 六方向证书有坐标系依赖；星核证明是局部薄壳，不是整块最短刚性逃逸。证书失败不证明真实深度大于 w。它能处理原双壁微夹持窗口，但不能把“有限充分证书”宣传成旋转不变、全空间必要充分的欧氏偏置。旧 ctol 仅由调用方显式取 `contact_resolution(...)` 后传入。

### 互锁最早根

完整三角表面 VF/FV/EE、对角棱、持续共面端点事件全部按有理数枚举；近竖直非零事件保留。根处精确非贯入，每个此前候选开区间的有理中点必须贯入。`exact_height/exact_offset` 为权威数据；`interval_certificate` 为胜出模型的逐区间证明。窗口还通过其他模型的有界完整事件排除更早根，但输出证书不冒充全部模型的序列化证明。

`height` 仅向上舍入显示；逐顶点重新浮点相加是不同数据，须重新判定。`exact_contact_label/normal` 属于精确事件；旧 `cover_label/tied_labels` 仅保留名义报告与导数带。窗口 core/shift winner 的精确 label 属于其证书模型。非 Dual 冻结逃逸用原有理平面比值，不将归一化法向舍入放大；4 个近竖直冻结门逐值等于精确根。

`escape_height_brute` 保留接口但不再用会错过先逃逸再重入的单调二分；它共享精确事件引擎，只是佐证，**独立 oracle 在测试专用扫掠 SAT / 射线包含排除中**。

### 首入、冻结、缓存

首入根/时序/t_max/并列/深度平方与 t* 前有理区间中点自校验全部精确。`merge_degenerate` 仅合并精确共面簇；微台阶杀死恢复容差突变。非共面源环通过 `surface_label/surface_members` 明确三角片；冻结 EE 与 facet 在同视图、同选择时角窗下共用同一精确方向裁决且保留 Dual 导数（facet 默认 tol=0，冻结默认 1e-9，不宣称二者默认选择参数相同）。FF/FE 合并标签须取 surface_members 中原始 VF/FV/EE 成员再冻结。交叉检查另外发现并修复三角对角 EE 取源拓扑导致的真实正负号错误，镜像/尺度/大平移和内部突变看护。

Polyhedron 采用用户允许的**内容签名失效**方案，而非破坏既有可变外层 API；Polyhedron 持有的派生缓存由完整顶点和面内容签名失效。原地顶点替换后不得复用旧 convex view；内部删除顶点签名突变被目标断言捕获。

### 适配器含义

DDA/TIA 必须明确选择严格数据语义或显式厚度政策；不能库内猜测 ctol，也不能把窗口相触当作原实体严格非贯入。精确运动根/特征应保留；舍入导出必须再次检查。姊妹三线只读，本单没有修改它们的适配器或切换开关。
''')
put('数学定义、API 字段和全部限定见 '+link('docs/exact_3d_design.md','三维设计 E5b 节')+'；'+link('reports/codex/E5b_evidence/window_contract_gap.md','窗口未完成项与无法绿色回退的说明')+'。')

put('\n## 2. 49 红逐条处置')
put('41 个 margin 不变性失败：原断言逐字保留到显式旧窗口，原始输入默认精确另对独立整数四面体并集 SAT。3 个 brute 零高度失败：原始抖动数据对独立扫掠 SAT 最早根零错；不抖动有理同构数据保留原静止恰零断言。4 个墙失败节点各含 20 seed：全部 80 原输入对独立最早根；新增 80 间隙后抖动和 4 理想格，显式旧窗口保留原 0.2/冻结断言。1 个 steep 牙：全部 72 原格和旧断言保留，新增带内漏支义务，同一内部竖向窗突变命中该断言。')
put('\n逐节点可复查：'+link('reports/codex/E5b_evidence/49_disposition.json','49 条机读台账')+'。')
put('首轮集成诊断另外暴露 155 红：127 个几何不变性旧源环/窗口域门、24 个近平行旧隐式钳零门、3 个冻结旧源边 oracle 门，以及 1 个优化后突变注入路径过时门。该轮源码曾发生后续编辑，不作最终验收或独占性能成绩；全部逐条映射到最终结果见 '+link('reports/codex/E5b_evidence/integration1_disposition.json','首轮集成 155 条处置')+'。')
put('\n| # | 原失败节点 | 最终 |\n|---|---|---|')
for i,row in enumerate(disposition,1):
    put(f'| {i} | `{row["node"]}` | PASS |')

put('\n## 3. 第五轮剩余三维发现')
put('以下为原 g6e JSON 的 **0 起始数组索引**。E5a/E5a2 已修的项目本单复验，不冒称本单新实现；每条命名门均由最终 JUnit 核对存在且通过。')
put('\n| 原索引 | 范围/级别 | 处置 |\n|---|---|---|')
for row in findings:
    put(f'| {row["array_index_zero_based"]} | `{row["file"]}:{row["line"]}` / {row["severity"]} | {row["resolution"]} |')
put('\n原文、逐项门名及最终匹配节点数量见 '+link('reports/codex/E5b_evidence/g6e_3d_disposition.json','第五轮三维发现台账')+'。')

put('\n## 4. 测试改写台账与强度审计')
put(f'基线 {inventory["old_test_functions"]} 个测试函数，当前 {inventory["current_test_functions"]} 个；原函数无删除、原参数装饰器无改变、新 skip/xfail 引用为零。原节点集合全保留，但这不是单靠数量证明强度：机读台账另外保存每个改动函数旧/新源代码、完整 assert AST、哈希和语义理由。')
put('\nmargin 三文件原 128 条 assert 文本全部仍在（52+44+32）；brute 的两条零断言移动到有理理想输入，原抖动输入另以更强独立精确根检验。首轮集成额外发现 3 个 frozen EE 标签 oracle 域迁移遗漏：旧 oracle 仅枚举源环边，而默认 margin 已能选折面真实对角边。没有改生产来选择错误源边；原 32 条 assert 与 6 工程坐标格全保留到显式旧窗口，同一原输入另外核对独立耳切的完整标签/strict 集合、精确表面最小距离及冻结符号。旧 float 逐顶点加法安全断言不谎称与精确仿射运动等价：一般输入核对权威精确根/端点，并在新增恰可表示根保留原浮点端点安全门。旧源码字符串“向上修补”突变随实现删除，改为省掉当前根精确核验的内部突变。')
put('\n| 文件 | 改写函数/辅助函数 | 处理 |\n|---|---|---|')
for row in rewrites['rewrites']:
    put(f'| `{row["file"]}` | `{row["function"]}` | {row["reason"]} |')
put('\n'+ ' · '.join(link('reports/codex/E5b_evidence/'+p,t) for p,t in [('test_rewrites.json','逐函数完整机读台账'),('test_inventory_audit.json','函数/网格/跳过审计'),('margin/assertion_retention.json','原断言保留'),('margin/integration_assertion_retention.json','追加两文件55条原断言保留'),('interlock/test_rewrites.json','互锁原格说明'),('entrance/test_ledger.json','首入冻结台账'),('face_routing_retention.json','路由门52条原断言保留')]))

put('\n## 5. 突变表')
put('所有列出的牙都修改被测内部路径，不在产出之后拼假数据；检查的是对应几何/根/区间/符号断言，而不是碰巧的标签排列。早期两个 entrance 外部突变曾临时改文件并还原，只有恢复后冻结源码的全套计入交付；其余为内存编译/monkeypatch。新增完整全套运行不与突变进程并发。')
put('\n| 组件 | 内部突变 | 报红原因/目标断言 | 结果 |\n|---|---|---|---|')
for row in mutations:
    put(f'| {row["component"]} | {row["mutation"]} | `{row["target_assertion"].replace("|","/")}` | {row["status"]} |')
put('\n'+link('reports/codex/E5b_evidence/mutation_table.json','合并机读突变表')+'；各组件 JSON 保留具体注入、日志和原断言。三个首入外部突变另以最终源码重新在隔离命名空间运行，见 '+link('reports/codex/E5b_evidence/entrance/final_mutants.json','最终源码突变复验')+'。额外布尔三角相交闭端点/同侧、整数 parity 边界、冻结对角拓扑突变也在最终全套中执行。')

put('\n## 6. 等价优化与性能')
put('部署优化：精确布尔三角交取代交点集合构造；精确横截严格内点正证书（失败保留完整 arrangement）；可认证星核四面体并集整数 SAT；清分母整数射线 parity；按完整内容与可注入实现键的事件/margin 缓存；正窗口三角距离先以精确支撑平面下界拒绝（严格 >，等号保留）。没有容差回退、减网格或删除原语义门。布尔路径 1300 对旧值对拍，另有独立重心可行性；整数射线与旧 Fraction 对拍并对独立 L 型集合判定；星核与独立 SAT 及关闭快路对拍；缓存逐值禁用对拍。')
put('\n| 测量 | 结果 | 解释 |\n|---|---|---|')
put('| E5a2 基线全套 | 7953 passed, 49 failed；1578.67 s | 红基线，8002 节点 |')
put(f'| E5b 冻结全套 | {final["last_nonempty_line"]} | {audit["current_nodes"]} 节点，原网格全留且加门 |')
put(f'| E5b 独占进程墙钟 | {final["wall_seconds"]:.2f} s | ≤900 s 目标：{"达成" if passed_target else "未达成"} |')
put('| margin 最终完整子组 | 641 passed, 50 deselected；92.85 s | 仅开发子组，不能替代全套 |')
put('| 互锁墙 + 完整 sensitivity | 53 passed；161.58 s | 每节点内部仍执行完整原 seed 网格 |')
put('| 最后两文件迁移完整复验 | 2454 passed；185.27 s | 原网格、原55条断言保留，151个集成红闭合 |')
put('基线是红的，且本单新增门，不能把两个全套耗时差当成同一工作量的微基准加速比。详细热点来自最终 JUnit，微基准有 before/after 输出逐值相等断言。')
put('\n'+ ' · '.join(link('reports/codex/E5b_evidence/'+p,t) for p,t in [('performance_summary.json','性能汇总'),('performance_by_file.json','最终按文件耗时'),('optimization_benchmarks.json','独立微基准原始记录'),('interlock/profile_plane_bound.json','平面下界逐值性能对拍')]))

put('\n## 7. 文档、复跑与回滚锚点')
put('README、canon_map、exact_predicates_plan、exact_3d_design 已标明当前契约与历史 E5a2 红状态的区别。`tools/fix_canon_ptrs.py --apply` 已执行，19 处指针更新，再执行为 0 处待改。仅写已验证范围，不宣称任意凹体全局 E 或完整折面法锥。')
put('\n```powershell\n$env:PYTHONDONTWRITEBYTECODE="1"\npython -X utf8 reports/codex/E5b_evidence/verify_run.py run rerun -- -m pytest -q -p no:cacheprovider --basetemp=reports/codex/E5b_evidence/tmp/rerun --junitxml=reports/codex/E5b_evidence/rerun.xml --durations=30 --tb=short\npython -X utf8 tools/fix_canon_ptrs.py --apply\npython -X utf8 reports/codex/E5b_evidence/verify_run.py inventory\npython -X utf8 reports/codex/E5b_evidence/audit_delivery.py\n```')
put('回滚锚点为只读 HEAD 3566708 和本树 byte-exact baseline 源码快照/manifest；本单未执行任何回滚 git 命令。基线本身是 49 红，不把它说成“上一个全绿版”。已实现子集留在经全套验证的实现，未以回退功能换绿。没有已验证且同时满足新默认精确语义、旧窗口全部原门的历史绿色窗口实现可直接回退；未执行该未完成项的绿色回退，不能声称这条回退要求也已满足。')

put('\n## 8. 独立交叉检查与遗留边界')
put('同组异作者检查了 root 几何优化与缓存；新增 64 三角对、249 点包含、32 折面星核对、96 横截、4 轮缓存操作未发现未闭合 critical/major；发现的缓存文案过度承诺已修复。margin 对 interlock 审查确认公开 certificate 仅包含 winner，这一限制已写明。此范围和人数不满足六路独立 G6，不能冒称通过正式审查。')
put('\n'+link('reports/codex/E5b_evidence/entrance/review_root.md','几何/缓存交叉审查')+' · '+link('reports/codex/E5b_evidence/margin/review_interlock.md','互锁交叉审查'))
put('''
- 有效闭合外向嵌入表面是输入前提；自交、非流形、非法面环不在证明域。
- **未完成项：显式窗口完整贯入深度契约。** 当前是六轴刚性脱离充分证书 OR 局部径向薄壳政策，不是完整欧氏深度/偏置；未给任意旋转下该有限政策等价的保证。局部壳可接纳整块最短脱离较大的夹持，六轴搜索也可能漏掉较短的斜向脱离，不能把二者合称刚性深度上界。默认严格几何不采用此政策。需所有者明确批准局部报告政策，或继续实现所指定深度的必要充分算法；没有用聊天未回复视为批准。
- exact root 与逐顶点重新舍入的 float 平移是不同输入；适配器不能混淆。
- 凹体全局 E 构造、完整一般折面法锥、姊妹线部署/工程验证与正式 G6 均未新增声称。
''')
if not passed_target:
    put('- **未完成项：≤900 s 总耗时目标。** 保留已逐值验证的等价优化与绿色功能，未为过时限削弱测试；性能目标不以回滚到 49 红的基线解决。')
put('\n## 全套最后一行（原样）\n\n```text\n'+final['last_nonempty_line']+'\n```')
put(f'独占进程墙钟：{final["wall_seconds"]:.6f} 秒。')
put('\n'+status)
(ROOT/'reports/codex/E5b_report.md').write_text('\n'.join(rows)+'\n',encoding='utf8')

index = ['# E5b 证据索引', '', '当前报告：'+link('reports/codex/E5b_report.md','中文总报告'), '', '## 验收证据']
for name in ['final.log','final.json','final.xml','delivery_audit.json','49_disposition.json','g6e_3d_disposition.json','integration1_disposition.json','test_rewrites.json','test_inventory_audit.json','mutation_table.json','performance_summary.json','performance_by_file.json','optimization_benchmarks.json','baseline_manifest.json','contract.md','canon_ptrs.log','canon_ptrs_final.log','final_docs.log','final_artifact_audit.json','window_contract_gap.md','changed_files.md']:
    index.append('- '+link('reports/codex/E5b_evidence/'+name))
index += ['', '## 组件证据与复跑工具']
for name in ['entrance/design_and_results.md','entrance/test_ledger.json','entrance/mutations.json','entrance/final_mutants.json','entrance/frozen_migration_assertions.json','entrance/review_root.md','entrance/review_root_probes.json','interlock/implementation_notes.md','interlock/test_rewrites.json','interlock/mutations.json','interlock/wall_oracle_160.json','interlock/profile_plane_bound.json','margin/notes.md','margin/test_rewrites.json','margin/assertion_retention.json','margin/mutations.json','margin/integration_summary.json','margin/integration_test_rewrites.json','margin/integration_assertion_retention.json','margin/integration_mutations.json','margin/review_interlock.md','face_routing_retention.json','verify_run.py','audit_delivery.py','benchmark_exact.py','build_report.py']:
    index.append('- '+link('reports/codex/E5b_evidence/'+name))
index += ['', '## 开发日志解释', '除 final.* 外，日志是阶段性诊断；其中保留失败、源修改过程和不同分组，不用于冒充最终验收。baseline/ 是只读 HEAD 源码字节快照；tmp/ 是 pytest 临时产物。源/测试不在冻结全套期间编辑。']
(OUT/'INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf8')
changed=set()
for args in (['diff','--name-only','-z'],['ls-files','--others','--exclude-standard','-z']):
    changed.update(p for p in subprocess.check_output(['git',*args],cwd=ROOT).decode('utf8').split('\0') if p)
files=['# E5b 改动文件链接清单','','不提交；基线 HEAD 3566708。证据目录中的 baseline/ 为基线快照，tmp/ 为本树测试临时产物。','']
files.append('- '+link('reports/codex/E5b_evidence','全部证据目录'))
for name in sorted(changed):
    if not name.startswith('reports/codex/E5b_evidence/'):
        files.append('- '+link(name))
(OUT/'changed_files.md').write_text('\n'.join(files)+'\n',encoding='utf8')
print(status)
print(final['last_nonempty_line'])
