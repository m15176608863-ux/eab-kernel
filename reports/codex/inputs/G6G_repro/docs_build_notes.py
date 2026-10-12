"""Build durable documentation/replay coverage notes from this review's outputs."""
from pathlib import Path
import json,hashlib,ast
ROOT=Path(__file__).resolve().parents[2]
NOTE=ROOT/'review/notes'
def read(name):return json.loads((NOTE/name).read_text(encoding='utf-8'))
rows={}
for x in read('root_g6e_replay.json'):
    i=x['g6e_id'];x=dict(x)
    x['status']='已修（原输入失真/错候选现被拒或正确分类）'
    if i==9:x['status']='已修（原错误切向现显式 ValueError；exit 1 是预期拒绝）'
    rows[i]=x
for x in read('solid_replay_results.json'):
    i=x['g6e_id'];x=dict(x)
    x['status']='已修（原输入重放）'
    if i==34:x['status']='原噪声选根已退休；原输入现与共享事件 brute 一致，不算独立最早根证明'
    if i==40:x['status']='NameError 已修；原浮点差点 hull 与 exact E 是不同模型，需精确差点等价复现'
    rows[i]=x
for x in read('gates_g6e_replay.json'):
    i=x['raw_1_based'];x=dict(x)
    x['g6e_id']=i;x['script']='review/repro/gates_replay_g6e.py'
    x['command']='python -X utf8 review/repro/gates_replay_g6e.py'
    x['status']='已修（当前接口等价输入与精确断言；原失败未重现）'
    rows.setdefault(i,x)
    if i in (40,):rows[i]['equivalent_exact_input']=x
for x in read('docs_static_replay.json'):
    for i in x.get('g6e_ids',[]):
        rows[i]={**x,'g6e_id':i,'script':'review/repro/docs_replay_extra.py'}
for x in read('docs_more_mutations.json'):
    i=x['g6e_id'];rows[i]={**x,'status':'旧噪声实现退休；当前同类内部变异被目标语义门捕获','script':'review/repro/docs_more_mutations.py'}
mut=next(x for x in read('gates_docs_mutations.json') if x['id']=='merge_distinct_microplanes')
rows[48]={**mut,'g6e_id':48,'status':'已修：旧0.5台阶门仍保留，新增1e-12和2^-80微台阶杀真实容差回退','script':'review/repro/gates_docs_mutations.py'}
for i,f in ((36,'docs_g6e36.json'),(50,'docs_g6e50.json')):
    x=read(f);rows[i]={'g6e_id':i,'status':x['status'],'verified_output':x,
        'script':f'review/repro/docs_g6e_{i}.py' if i==36 else 'review/repro/docs_g6e50.py'}
result=[rows[i] for i in sorted(rows)]
(NOTE/'docs_g6e_replay_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
inventory=read('gates_docs_inventory.json')
claims=inventory['claim_lines']
history={3,4,5,6,7,8,9,10,19,20,21,22,23,24,25,26,27,28,35,36,56,61,62,65,67}
for i,c in enumerate(claims,1):
    c['review_classification']='历史/范围/状态文字；不能当作当前数学证明' if i in history else '具名门存在；性质内容和范围已对照，执行通过性采用本轮全套记录'
    if c['file']=='README.md' and c['line']==102:c['review_classification']='主干性质有具名门，但旧非凸 G0 oracle 描述过期，minor另列'
    if c['line']==6:c['review_classification']='窗口薄壳范围与限制如实；六轴closed-PD推论被tight-cavity反例否证，major另列'
    if c['file']=='docs/exact_3d_design.md' and c['line']==100:c['review_classification']='六轴closed-PD推论被tight-cavity反例否证；不是默认精确路径的缺陷'
(NOTE/'docs_claim_review.json').write_text(json.dumps(claims,ensure_ascii=False,indent=2),encoding='utf-8')

rows8=[
('378','ContactRecord','四组字段存在；source替代source_engine，canonical_order_key/稳定序映射缺口已明示；FF/FE/EE_PAR不产ContactRecord。'),
('379','读取器','实际bdda_df/bdda3d/tf_probe三入口；bdda2/DDA4缺口明示。只读外部DDAKernel.cpp:6118–6125、19712–19723确有逐接触输出。'),
('380','夹具规模','48生成型bdda_df条目、3份bdda3d、3个tf目录；15家族/8benchmark未实现明示。'),
('381','G0','二维/三维精确三票有具名门；非凸独立oracle已替换。每个边界点普遍±epsilon双侧仍未做，文字未掩盖。'),
('382','G1','bb52集合53条与gap窗口门属实；不比锁态/滑动/位移，文字承认弱于07。'),
('383','G2','只对手写清单，不是detect产出；tf逐接触gap/normal门未做，已明示。'),
('384','G3','Dual+冻结有限差分存在；eab2批量逐位/装配零跳过没有，已明示。'),
('385','G4','5/61钉数与报告一致；03/07外部正本旧82口径未改。'),
('386','G5','未实现；现sibling_observations不是tf05差异逐条台账的替代。'),
('387','Phase2','六种Cover3有产出；FF/FE只在首入标签合并；EEP未实现。'),
('388','Phase3','全局凹E/角覆盖裁剪未做；一般精确表面谓词不冒称该实现。'),
('389','Phase4','Dual+frozen与额外L3极限分析存在；活动集/MLCP未做。'),
('390','Phase5','未部署姊妹开关，依repo只读约束保留。'),
('391','姊妹只读','本子任务只读；整个仓库从未修改姊妹的历史说法无法由单次审查证明，属工作过程声称。'),
('392','风险','顺序同构、o3/o3t口径限制保留；外部remote现状不掌握，未作现状保证。'),
('393','Phase0字节往返','records JSON往返与原件逐字节不同；solver_profile未读，明示。'),
('394','G4缩水','3份dump、无预定阈值及迭代次数，明示；不冒充07完整门。'),
('395','优先性措辞','DDA圈内第一份选项仍错误，minor另列；本课题组/姊妹独立oracle可限定。')]
text=['# WO-G6G 文档/正本、旧发现重放与门迁移分项审查','',
      '被审 HEAD：d44dd78。所有脚本、日志、复制树与本笔记只写 review/。不修代码。',
      '', '## 结论','',
      '本镜头确认 1 major + 2 minor。major是六轴“非贯入”证书被文档错误提升为理论正本01的闭集完全分离PD界。默认精确API在该例报告严格贯入，未被否证。',
      '', '## 运行证据','',
      '- G6F10：旧脚本因旧句消失而 StopIteration；等价核查精确最小差点 19999999999999989/2，浮点早差 9999999999999994，实际凸E保留前者；新doc句准确。',
      '- docs_replay_extra.py：doc pointers / provenance inputs / flat arch 共 7 passed in 0.12s。',
      '- gates_replay_g6e.py：13/13原缺陷未重现。root/solid runner保留逐输入原输出与exit。',
      '- 原G6E合计覆盖 '+str(len(result))+' 个id（本子任务；#23/#47由root的LP审查补）。',
      '- 四项旧门等价变异：boundary→inside 1红；保留非极点1红；edge boundary→strict1红；并微平面2红/3绿。',
      '- 另外旧#8取消候选extent 6红；#35公共extent设0 4红/4绿；#46弱化exact supporting certificate1红；#49将VV active强设True 12红/3绿。',
      '- 每个copy变异finally原字节复原，SHA-256核一致。所有失败均是目标assert，不是collection或语法异常。',
      '', '## 07 第八节逐行核查','', '|当前行|条目|核对结论|','|---|---|---|']
text.extend('|'+ '|'.join(r)+'|' for r in rows8)
text+=['','## 声称与迁移覆盖','',
       '四份仓内文档抽出69处包含✔/已完成/已验证/已实现/有门的行，所有显式具名测试均可定位（missing=0）；详见docs_claim_review.json。无具名门的范围/历史/未实现说明不是数学已通过声明。全套是否全绿由root自己的完整运行记录判定，不用实现方历史日志替代。',
       'b6126cf..HEAD测试96文件变化、113原函数变化；清单保留旧/新源码及assert全文。6个重命名函数不是直接删格。本镜头重点逐行看E2旧噪声带/FF边界迁移、hull自证/非极点迁移、G0错极点不豁免、退化簇微平面门、候选extent两半句。没有找到可确认“旧能抓、新抓不住”的反语义逃逸。',
       'PERF自己并不声称旧test_*函数全新独立oracle，等价对拍可以共享原问题模型；其主窗口独立区间oracle只验证box/双壁样本，不覆盖本次tight-cavity病态。tests零缺失不是全域可靠性证明。',
       '', '## G6E 重放状态','', '|id|状态|复跑脚本|','|---|---|---|']
text.extend('|'+str(x['g6e_id'])+'|'+x['status']+'|`'+x.get('script','')+'`|' for x in result)
text+=['','## 正本与完整性批评','',
       '只读00共501行、01全文、03全文、07全文：E定义方向、距离/PD、一般位置与退化、凸限定、KKT未实现、G0–G5规模、ContactRecord生命周期与溯源、Phase0–5、学术优先性均逐项核。未联网重新审查文献真实性；本轮核“正本写了什么”，不把正本综述题录当重新验证过的学术事实。',
       '直接阅读四份仓内背景文档、AGENTS、六份E2–PERF报告的设计/迁移/状态段、R6FIX描述、g6f b6126cf后提交说明；部分巨型证据目录未逐文件读。',
       '本子任务不独立逐行读src全部模块，也不逐条跑69处声称关联的所有测试；完整测试root在执行，模块正确性及其oracle由二维/三维/LP其他镜头覆盖。没有将这些委派范围说成我方个人穷举。',
       '新PD反例oracle是独立Fraction区间与连通性证明，未使用生产SAT/法向/三角化/距离；构造调用box只生成可检查的输入顶点集合（先核恰为完整笛卡尔角点）。',
       '旧#34的escape_height_brute与生产现在共享事件/谓词，重放相等只能证明原错高度症状不再，不能替代最早根oracle；旧#36的浮点旋转丢边界标签仍可见，当前两份数据各自G0通过，但标签丢失本身不再是精确合同下的反例，不能据此宣称所有extent完备。',
       '没有修改任何已跟踪文件或外部正本；文件哈希全过程完整性由root baseline manifest核验。']
(NOTE/'docs_review.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
print('G6E unique',len(result),'ids',[x['g6e_id'] for x in result])
print('doc claims',len(claims),'missing named refs',inventory['missing_named_tests'])
