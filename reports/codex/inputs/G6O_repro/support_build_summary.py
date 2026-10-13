from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
R=ROOT/'review'
rows=[
    dict(id='SUPPORT-S01',severity='major',
         file_line='tools/osteomorphic.py:24,48-49,143,147-149; docs/r14fix_design_sync.md:26',
         conclusion='骨形 generic 构造在 Dual 路径中提前逐操作舍入，违反具名完整坐标代数合同，可把支持域内可表达非零坐标或解析导数静默清零。',
         failure_scenario='osteomorphic_block_generic(nx=2,ny=1,lx=2,amp=0,center=(Dual(2**-100,(1,)),0,0)) 在u=.5的x应为2**-100，实际Dual(0,(1,))；D400边界2**-400同错。普通几何lx=Dual(2,(2**60,)),center_x=Dual(0,(1,))同一点精确解析导数1，实际0。',
         how_to_reproduce='python -X utf8 review/repro/support_shape_dual_cancellation.py',
         suggested_fix='仅针对具名骨形构造保留每个完整坐标及完整导数通道的Fraction表达式到最终舍入；不通过全局改变Dual逐操作合同修复。增加generic/raw同模型抵消门，含非对称位置、D400边界及差异种子量级。',
         verified_output=(R/'logs/support_shape_dual_cancellation.txt').read_text(encoding='utf-8'),
         grading='窄Dual生成器构造族静默错误，major；primal与derivative同根只计一条，不要求一般Dual复合表达式最终一次RN。',
         independent_oracle='自写Fraction完整x=cx-lx/2+lx*u及导数；u=.5精确，无生产构造、Dual算术或libm参考。'),
    dict(id='SUPPORT-S02',severity='minor',
         file_line='src/eab/readers/numeric_decode.py:17-20,38-40; docs/r14fix_design_sync.md:24,71',
         conclusion='JSON十进制整数身份在schema分派前受连续输出域拒绝，与整数身份无幅度界及按schema精确保留的分项合同不一致。',
         failure_scenario='ContactRecord.step/block_a或bdda3d.bi=10**400：int、Fraction和普通整数字面量均精确保留；等值有效JSON实数字面量1e400在_decimal中scalar_rational拒绝。真实bdda3d.load_records与工具bdda3d_document.loads亦如此。',
         how_to_reproduce='python -X utf8 review/repro/support_decimal_identity_domain.py',
         suggested_fix='JSON parse_float阶段只保留有限精确Fraction和负零语义；连续字段在schema确定后核RN输出域，整数身份只核分母=1；补巨大decimal整数身份真实入口。',
         verified_output=(R/'logs/support_decimal_identity_domain.txt').read_text(encoding='utf-8'),
         grading='入口过度拒收/非核心整数schema合同不一致，没有静默错误计算结果；minor，不与已修复N03同根重复。'),
    dict(id='SUPPORT-S03',severity='major',
         file_line='src/eab/margin.py:483-486,492-494; docs/exact_predicates_plan.md:60-61',
         conclusion='贯入早返回仍用0.0-delta混合浮点减法，非零margin_gap静默变零且没有文档要求的精确显示证书或域异常。',
         failure_scenario='margin_contacts(box(),box(),delta=Fraction(2)**-2000)：delta正且有限，单位盒同一开放内部贯入，distance=0，因此普通margin_gap=-delta精确非零。返回margin_gap=+0.0、_exact_closed=None、exact_distance_squared=None；closed仍True。',
         how_to_reproduce='python -X utf8 review/repro/support_margin_penetration_domain.py',
         suggested_fix='贯入路径也完成精确-delta并走具名最终边界；若该字段明确允许显示下溢，提供权威exact margin gap/closed证书并列明例外，而非无证书依赖float gap分类。distance=0/normal=None仍是合法哨兵。',
         verified_output=(R/'logs/support_margin_penetration_domain.txt').read_text(encoding='utf-8'),
         grading='极小精确delta窄入口：输出域外应具名拒绝却静默返回普通量错误值，major；未发现普通域内版本，未声称closed状态错。root/geometry提出后本分审独立复核，总报告须去重。',
         contract_reason='完整有限有理输入域加最终RN非零输出边界仍是margin_gap代数合同；margin.py483写-delta，485-486仅允许带exact_distance_squared与单独exact_closed的显示下溢。贯入distance=0是哨兵，但margin_gap未定义为固定哨兵，此路径两证书均None。')
]
(R/'evidence/support_findings.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('SUPPORT_SUMMARY_WRITTEN critical=0 major=2 minor=1; root must deduplicate margin and make final grading')
