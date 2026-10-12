from pathlib import Path
import json,hashlib
root=Path('.')
orig=json.loads((root/'review/logs/history_legacy/results.json').read_text(encoding='utf-8'))
notes={
7:'原冻结EE三格gap为正、ee/frozen/facet法向点积=1；符号错误未重现。',
9:'坏切向明确ValueError拒收，有效对照optimal≈10。',
11:'alpha乘0.999等错误候选拒收；三个大恒载黏聚错误候选ok=False。',
20:'无关块速度0/1e3/1e5均不能掩盖穿透，admissible=False及ok=False。',
21:'无关体恒载10/1e6/1e9均不能掩盖alpha=9.99，ok=False。',
22:'无关远体D=1e2/1e4/1e6不改变原精确status/alpha风险报告。',
24:'原float刚体运动实际输入72内部、8分离，不是理想相触；独立integer tetra-union SAT核81格API全同答。',
25:'原微斜顶点的VV真距离≈0.141421，未被绝对锥阈值丢失。',
26:'两条critical原输入分别cover/brute为1/1和-1/-1，G0 2000探针mismatches=0。brute是佐证，G0的Fraction SAT是独立主票。',
27:'四种精确凸短边被接收；微凹另明确reflex拒收。',
28:'三姿态假EE标签均无，G0通过，四探针原始成员与实体状态一致1。',
29:'原尺寸比1000/100/10+yaw组合G0通过，无对称差。',
30:'六个原近平行格未错并FF，strict=8，G0两票绿。',
31:'原独立精确线段距离与_seg_seg_distance逐位同为4.579391932681403e-9。',
34:'原抖动墙covers/brute同答仅佐证；独立有理U墙两格精确高度1/5，保留工程坐标。',
36:'原float运动可真实改变标签；另保留精确有理刚体+大平移后完整18标签全等，lost/extra空。',
37:'三个原首入姿态均entrance、t≈1，无旧跨分辨步误抛。',
38:'原极点保留，worst outside=-0，identity与移缩G0过，ambiguous=0。',
40:'默认eps不再NameError。原先float差点40/64不等于精确差点，原3个hull_anomaly是模型不一致；exact diffs vote=(0,6,0,0,[])且public G0过。',
41:'微凹凸API拒收；一般路径两深度都正确为1。',
42:'原roof G0通过；原源表面真实几何没有噪声豁免。',
43:'倒角五档平移0..1e6 G0全部passed、差异空。',
44:'四个屋脊原极点strict=True；G0通过、ambiguous=0。',
45:'单体远无力接触D=0..1e6，三种错误alpha均ok=False。'}
rows=[]
for x in orig:
 rows.append(dict(id=x['id'],method='original script + specified model corrections where needed',status='old_failure_not_reproduced',analysis=notes[x['id']],returncode=x['returncode'],verified_output=x['verified_output'],source=x['source'],log='review/logs/history_legacy/g6e_%02d_original.log'%x['id']))
extra={23:('history_numeric_equiv.log','原unbounded筛查等价重放四种体编号/邻域状态；每一精确status仍unbounded且risk report准确。'),47:('history_numeric_equiv.log','tiny rational penetration 1e-3..1e-100在真实自检拒收，无关体速度1e20不掩盖。'),48:('history_focused.log','四个exact微台阶高度1/2..2^-80保留两个独立FF面簇。旧tol域宽机制已删除。'),49:('history_focused.log','15格VV活动性逐格对内联Fraction两邻点严格支撑；原方向噪声带机制已删除。'),50:('history_oracle_teeth.log + history_focused.log','G0原ratio/yaw四格零ambiguous/drop/skips；真实局部锥内部恒True缺陷被精确顶点票拒收，无旧400eps宽豁免。'),39:('history_oracle_teeth.log','真实局部cones_intersect_relint恒True，G0 hull_vertex_mismatch>0且passed=False；旧low_e豁免没有继续吞内部假顶点。')}
for id,(log,note) in extra.items():
 rows.append(dict(id=id,method='equivalent current-code reproduction of old failure class',status='old_failure_not_reproduced',analysis=note,log='review/logs/'+log))
rows.sort(key=lambda r:r['id'])
(root/'review/logs/history_g6e_replay_dispositions.json').write_text(json.dumps(dict(unique_replayed_ids=len(rows),original_script_count=len(orig),entries=rows),ensure_ascii=False,indent=2),encoding='utf-8')
print('30 unique g6e IDs:',[r['id'] for r in rows])
exhibit=json.loads((root/'review/logs/history_x_exhibit.json').read_text(encoding='utf-8'))
finding=dict(id='G6M-H01',severity='minor',file='tests/test_entrance3.py',line=159,summary='三维随机首入门迁移后不再约束返回平移x与精确事件时刻的关系：同一个内部x→x0缺陷旧门23红，当前相关164数学门全绿；R12静态函数锁仍报红。',failure_scenario='在review副本first_entrance3正事件Entrance3构造器里，把返回x的exact_x改成x0，候选/时刻/法向/见证及自校验不改。随机seed0 expected_x=(-0.3112355578308868,0.45770106421456686,0.6282038688737575)，mutant返回start=(-3.017738778724177,3.152165214937428,2.3413999174549023)，t=3.3193317016553476仍正确。旧随机24格23 failed，新同名24格及相关六文件164格全passed。现生产baseline的x正确；完整门有静态冗余，不是当前生产数学错误。',how_to_reproduce='PYTHONDONTWRITEBYTECODE=1 python -X utf8 review/repro/history_x_migration.py; python -X utf8 review/repro/history_x_exhibit.py; python -X utf8 review/repro/history_x_static_redundancy.py',suggested_fix='在原随机格直接核result.exact_t==independent_interval[0]，用独立Fraction midpoint证书核每个result.x分量是RN-even(x0+t_exact*d)，不强求将浮点端点回代必相触。加入x→x0真实构造器内部缺陷牙；迁移台账注明旧端点覆盖被此不变量替代。',verified_output='old baseline 24 passed in 8.42s; old mutant 23 failed, 1 passed in 8.41s; current baseline 24 passed in 9.26s; current mutant 24 passed in 9.00s; current 6-file mathematical domain mutant 164 passed in 17.44s; static first_entrance3 baseline=0 / mutant=24 issues (closed-stale-waiver + related expired-site diagnostics). All copied source SHA-256 restored.',evidence=['review/logs/history_x_migration/results.json','review/logs/history_x_static_redundancy.json','review/logs/history_x_exhibit.json'],classification_boundary='recommended minor because static redundancy blocks the actual source mutant; not a critical/major current wrong answer',concrete_exhibit=exhibit)
(root/'review/history_findings.json').write_text(json.dumps([finding],ensure_ascii=False,indent=2),encoding='utf-8')
print('minor confirmed finding saved')
