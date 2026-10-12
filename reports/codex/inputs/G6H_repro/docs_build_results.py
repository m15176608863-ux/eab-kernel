from pathlib import Path
import json,ast,re,hashlib
ROOT=Path('D:/eab-wt/g6h');OUT=ROOT/'review/agents/docs_gates'
for script in ['docs_canonical_oracle_mutation.py','docs_canonical_oracle_dropvertex.py']:
 p=ROOT/'review/repro'/script;s=p.read_text(encoding='utf-8-sig');anchor="p.write_bytes(raw);assert hashlib.sha256(p.read_bytes()).hexdigest()==h\n"
 replacement=anchor+"assert baseline.returncode == mutant.returncode == 0\nassert all(r['new_gate']=='PASS' and r['old_gate']=='PASS' for r in json.loads(baseline.stdout))\nassert all(r['new_gate']=='PASS' and r['old_gate'].startswith('AssertionError:') for r in json.loads(mutant.stdout))\n"
 if 'assert baseline.returncode' not in s:p.write_text(s.replace(anchor,replacement),encoding='utf-8')
raw=json.loads((OUT/'replay_raw.json').read_text(encoding='utf-8'));current=json.loads((OUT/'current_gates.json').read_text(encoding='utf-8'))
by={Path(r['script']).name:r for r in raw}
replay=[]
for id in [9,10,11]:
 r=by['docs_tight_cavity_pd.py' if id==9 else 'docs_residual_claims.py']
 replay.append({'id':f'G6G-{id:02d}','status':'已修','original_script':r['script'],'original_command':'python -X utf8 '+r['script'],'original_exit_code':r['exit_code'],'verified_output':r['verified_output'],'log':r['log'],'additional_verification':current,'explanation':('原几何反例仍成立，但当前文档明确six-axis仅证rho而不证PD_closed，这是已修而非政策改变。' if id==9 else '原脚本以必须存在旧坏句为前提，旧坏句已删除而StopIteration；当前具名文档门（含真实运行禁用生产oracle）实际通过，非把崩溃冒充修复。')})
(OUT/'g6g_replay.json').write_text(json.dumps(replay,ensure_ascii=False,indent=2),encoding='utf-8')
static=json.loads((OUT/'docs_static_replay.json').read_text(encoding='utf-8'));r6=[]
for row in static:
 for id in row.get('g6e_ids',[]):
  if id in (12,13):continue
  r6.append({'id':f'G6E-{id:02d}','status':'已修或按当前合同明确缺口','kind':'文档等价复放/现有条目审计','how_to_reproduce':'python -X utf8 review/repro/docs_replay_extra.py','verified_output':row['verified_output'],'log':'review/logs/docs_replay_docs_replay_extra.log'})
for name,id in [('docs_g6e50.py',50),('docs_g6e_36.py',36)]:
 r=by[name];r6.append({'id':f'G6E-{id:02d}','status':'已修旧噪声机制（有限复放范围）','how_to_reproduce':'python -X utf8 '+r['script'],'verified_output':r['verified_output'],'log':r['log']})
r6.append({'id':'G6E-01-external','status':'独立只读重核外部原始源码支持当前订正','verified_output':json.loads((OUT/'dda4_external_readonly.json').read_text(encoding='utf-8')),'scope':'仅读取三处原代码，未启动姊妹exe'})
if not (OUT/'g6e_replay.json').exists():
 (OUT/'g6e_replay.json').write_text(json.dumps(r6,ensure_ascii=False,indent=2),encoding='utf-8')
proof=json.loads((OUT/'canonical_oracle_dropvertex.json').read_text(encoding='utf-8'))
finding={'component_id':'docs-gates-shared-convex-view','severity':'major','file:line':'tests/test_invariance_geom.py:325-329','file':'tests/test_invariance_geom.py','line':325,'summary':'迁移后的局部facet完整性门先以被测exact_convex_view生成expected，删真极点可让actual与oracle同错，而旧门会报红。','failure_scenario':'原tetra_box_vv/generic两格（rot=0,tmag=1000,s=1）正常新旧门均通过。在被测exact_convex_view的原编号保留分支内部引入单处缺陷：对len>=8、|coord|>100的输入删最后一个真极点并缓存错凸视图。当前迁移门两格仍PASS；b6126cf同名原函数两格均在facet标签集合不变断言AssertionError。另一只改source-face编号的同类变异三格也有相同结果。','how_to_reproduce':'$env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/docs_canonical_oracle_dropvertex.py','repro_script':'review/repro/docs_canonical_oracle_dropvertex.py','verified_log':'review/logs/docs_canonical_oracle_dropvertex.log','verified_output':'BASELINE\n'+proof['baseline']+'\nMUTANT\n'+proof['mutant'],'suggested_fix':'expected从保存的原始输入独立构造凸包/支持集，并独立核源编号保留条件；禁止调用被测exact_convex_view作为oracle前处理。在精确支持环且纯平移稳定格保留原facet标签不变断言，配删原始真极点及源face编号错置的内部变异。','oracle_independence':'新oracle的support_labels本身独立，但测试先调用被测exact_convex_view输入它，因此其几何模型前处理不独立；旧函数通过git show读取到隔离copy，用同一现行模块空间运行，不改测试断言。','classification_basis':'纪律A violation且可运行证明旧能抓新不能抓；变异是几何缺陷，不是输出后拼假标签。仅确认该迁移门失牙，不声称完整9851门全逃逸；G0保存原输入的其他门仍可能抓住。','copy_sha256_restored':proof['sha256_before_restored'],'confirmed':True}
(OUT/'findings.json').write_text(json.dumps({'confirmed':[finding],'unconfirmed':[{'summary':'canon砖二“命题7/8均未实现”及entrance文档“全部区间中点”残余描述差异','counted':False,'reason':'未证明计算错误，前者受历史HEAD段口径影响；后者全部原事件已核，闭集首次碰撞可由事件捕获，未冒称算法错误。'}]},ensure_ascii=False,indent=2),encoding='utf-8')
files=['README.md','AGENTS.md','docs/canon_map.md','docs/exact_predicates_plan.md','docs/exact_3d_design.md']
rows=[]
known={p.name for p in (ROOT/'tests').glob('*.py')}
for fn in files:
 p=ROOT/fn; txt=p.read_text(encoding='utf-8-sig')
 for i,line in enumerate(txt.splitlines(),1):
  if any(t in line for t in ['✔','已完成','已验证','已实现+有门']):
   refs=re.findall(r'(test_[A-Za-z0-9_]+\.py)',line)
   rows.append({'file':fn,'line':i,'claim':line,'test_files':refs,'missing_files':[r for r in refs if r not in known]})
(OUT/'claims_inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('g6g',len(replay),'g6e rows',len(r6),'claim lines',len(rows),'missing referenced test files',sum(bool(x['missing_files']) for x in rows))
