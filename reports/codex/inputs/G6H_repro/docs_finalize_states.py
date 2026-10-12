from pathlib import Path
import json
p=Path('review/agents/docs_gates/g6e_replay.json');rows=json.loads(p.read_text(encoding='utf-8'));extra=json.loads(Path('review/agents/docs_gates/g6e_runtime_extra.json').read_text(encoding='utf-8'))
statuses={
1:('文档订正；DDA4.x读取器仍未实现','原错误“无逐接触导出”已撤回；源源码原行只读重核真实有导出。读取器/第二oracle并未因修文案而新增。'),
4:('文档订正；canonical_order_key和三维CoverType退化产出仍未实现','当前四组生命周期齐不等于第五组序维护已落地；实际字段无canonical_order_key，实际枚举VF而合并仅FF标签，当前文案如实写缺口。'),
5:('文档订正且边界跳样已修；普遍±ε双侧构造仍未实现','当前G0真实box门27 samples=1随机+26全部边界，band_skipped=0。原07普遍逐边界±ε探针的缺口当前明确保留。'),
6:('文档订正；正本03仍未回写新口径','当前canon明确03旧82/39/60、订正5/61只在本库；本轮亲读03:86仍旧值，不声称修了只读正本。'),
10:('已修','新增具名test_limit_flat_arch实际执行，刚性竖直台肩平拱μ>0无界、μ=0不可行的原物理声称已有实门，docs_extra同组7 passed。'),
14:('已修','原过期指针换成当前定义行+函数名，并由当前test_doc_pointers实际运行通过；不再以人工校正说法代替门。'),
15:('文档订正；未重跑历史提交整套','历史G6D处置列相关18/36订正现在实际存在；本轮没有声称重新验收旧699f481全套或它错误提交说明。'),
16:('文档订正；首入只称第一版，不称完整','当前二维/三维首入模块/具名门存在而历史“零实现”已撤回；Arch5/7实际枚举容许铰机构10/28已再次运行。不是为新版首入其他问题保证无缺陷。'),
17:('文档订正；Cover3/ContactRecord退化类型产出仍未实现','实际源枚举VF，merge给FF标签，当前文本区分这些层次；不把标签产出当CoverType.FF/FE对象产出。'),
18:('文档订正；07规模/判据缺口仍未完成','G1锁态/滑动符号、15家族、Phase0原件逐字节、G4预登记阈值/迭代次数等均未新增实现，当前第八节明确列缺口，不伪称旧功能已补。'),
19:('已修（现有溯源条目和4份差异文字）；未重新导出','现有48条生成项实际都有input_sha256/nonreproducible，当前明确4份差异；本轮不运行姊妹exe来重新核每个差异数值。'),
32:('已修','已删除无名过期区间并采用具名当前定义行；当前指针门实际通过，历史未读覆盖说明已订正。'),
33:('已修（现有48条条目）；未重新导出','不仅修改未来写入工具：全部现有48条条目实际具备input hash及不可复现列，并实际通过provenance输入门。'),
36:('已修旧隐式带机制；当前边界变动不按理想不变性计错','原几何重放仍有运动后标签差，但当前G0逐给定数据两组均通过。已删除原浮点近线带；本分镜有限重放不独立外推所有标签域。'),
50:('已修','旧三种噪声宽度已撤除；原随机0对baseline通过，真实内部锥交恒true使24个多报极点，当前passed=False、e_vertices_ambiguous=0。')}
for r in rows:
 if r['id']=='G6E-01-external':continue
 id=int(r['id'].split('-')[1]);r['status'],r['resolution_scope']=statuses[id]
 if id in [4,17]:r['additional_runtime_output']=extra['G6E04_17']
 if id==5:r['additional_runtime_output']=extra['G6E05']
 if id==16:r['additional_runtime_output']=extra['G6E16']
 if 'additional_runtime_output' in r:r['additional_runtime_command']='python -X utf8 review/repro/docs_g6e_runtime_extra.py';r['additional_runtime_log']='review/logs/docs_g6e_runtime_extra.log'
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
p=Path('review/agents/docs_gates/claims_inventory.json');rows=json.loads(p.read_text(encoding='utf-8'))
for i,r in enumerate(rows):
 if i in [1,2,3,4,5,6,7,15,16,17,18,19,20,21,37,40]:
  r['judgement']='历史状态/临时标记/撤回语境；不当作当前已通过G6声明。未重跑其历史快照全部数值。'
 elif i in [8,22,24]:r['judgement']='规则或状态词定义，不是实现正确性的新证明。'
 elif i in [0,23,38,39,41]:r['judgement']='当前窗口限定正确；rho/PD_closed区分已修，81门小组实跑与96独立格支持，仍非任意表面全称证明。'
 elif i==9:r['judgement']='当前具名门存在；凸/凹全局界限明确。first_entrance紧配缝初态另由geom2确认major；不把局部最浅出口豁免误用于初态。'
 elif i==10:r['judgement']='具名门存在，G2明确仅手写np清单；G0零豁免/枚举精确窗由几何分镜覆盖。本分镜确认invariance expected共用被测凸化的major，不等同完整G0全逃逸。'
 elif i==11:r['judgement']='正本01/03出处对应真实；定理一非独立与定理三后半未实现如实标记。margin penetration小组实跑，定理二/Lipschitz主门由主审完整套验证。'
 elif i==12:r['judgement']='门存在且平拱具名门已补，docs_extra 7门实跑；精确LP/自校验更细由主审负责，不从文案独立外推全部模型。'
 elif i in [13,14]:r['judgement']='具名门存在，原源码导数/reader细审由主审/相关分镜负责；本分镜未重新算G3收敛数字或reader6716全部原行，列未独立核。'
 elif i in [25,26,29,30,35,36]:r['judgement']='按凸/一般位置/凹弱完备界限有具名测试；映射与正本前提一致。主数值路径交几何分镜；共享被测凸化迁移门问题见confirmed finding。'
 elif i==27:r['judgement']='正本位置无关同形状方向约定正确且专门test_proposition_2i存在；invariance局部facet原断言迁移确有同错漏洞，已确认major。'
 elif i in [28,31,32,34]:r['judgement']='内容在正本01命题3(i)/6或03§1.3有对应（限闭凸）；具名门存在，非全称数学证明。完整数值主门交主审套，本分镜未复算Lipschitz全部点对。'
 elif i==33:r['judgement']='margin closed状态以exact平方裁决与窗口分开；R7微贯入牙当前小组实跑，窗口口径不冒称原体不贯入。'
 else:r['judgement']='已核声明上下文、测试文件存在；实际断言强度如coverage及主审全套，不升级为全域证明。'
p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
p=Path('review/agents/docs_gates/coverage.md');s=p.read_text(encoding='utf-8-sig').split('\n### G6E ')[0];s += '''
### G6E 逐项处置精度补充

编号1/4/6/15/16/17/18是**文档订正**，相关读取器、序维护、退化CoverType对象、只读正本回写、07规模/判据等功能仍有明确缺口；不能合称代码已修。编号5实际新增重核 `27 samples = 1 + 26 boundary`、`band_skipped=0`，所以边界跳样已修，但普遍±ε构造未完成。编号10平拱实门、14/32当前指针门、19/33全部48现有条目确有运行或内容证据，分别判已修。编号16再次实算Arch5/7容许铰10/28，不把第一版首入存在冒充完整正确。细分状态、原输出、当前未实现项都在 g6e_replay.json 的 resolution_scope。

[新增运行脚本](file:///D:/eab-wt/g6h/review/repro/docs_g6e_runtime_extra.py)；[输出](file:///D:/eab-wt/g6h/review/logs/docs_g6e_runtime_extra.log)。

42处清单是候选claim行，不是42行全部子声称形式证明。每行judgement分别写明历史/规则、仅查存在、实际核断言/小组运行或交其他分镜；未复算的G3收敛数、reader普查等明确列为本分镜未独立核。
''';p.write_text(s,encoding='utf-8')
assert not any('?' in r['judgement'] for r in rows)
replay=json.loads(Path('review/agents/docs_gates/g6e_replay.json').read_text(encoding='utf-8'))
assert not any('?' in r['status'] for r in replay)
print('UTF8 判定字段已修，42 claim 行不是全称证明；G6E 已按逐项细分状态。')
