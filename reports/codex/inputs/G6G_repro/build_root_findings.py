"""Assemble root-reviewed findings from preserved, successful run logs."""
from pathlib import Path
import json

R=Path(__file__).resolve().parents[1]
def output(name):
    meta=json.loads((R/'logs'/f'{name}.json').read_text(encoding='utf-8'))
    assert meta['exit_code']==0, meta
    return (R/'logs'/f'{name}.log').read_text(encoding='utf-8')

findings=[
 {
  'id':'root-dual-power-range','severity':'major','file:line':'src/eab/dual.py:106-131',
  'summary':'Dual 幂的快路仅检查输入范围，不检查派生幂系数，先下溢再乘种子会静默抹掉可表示的导数。',
  'failure_scenario':'x=2**200；Dual(x,(x,))**-5 的 primal=2**-1000 正确，但导数返回 -0.0；独立 Fraction 真值 -5*2**-1000=-4.666318092516094e-301，所有输入和最终输出均有限、可表示。876 个满足可表示条件的指数格中发现13个静默错，另14个响亮拒绝不计作静默错。',
  'how_to_reproduce':'python -X utf8 review/repro/root_power_range.py',
  'suggested_fix':'按派生指数和种子乘积的范围选择快路，或对整数幂用精确有理导数后最终舍入；非整数使用保留指数的构造。补输入仍在 _ordinary 框内而派生系数越界的门。',
  'verified_output':output('root_confirm_power_final'),
  'verified_log':'review/logs/root_confirm_power_final.log',
  'oracle_independence':'Fraction 二的整数/半整数幂闭式，不调用被测 Dual 或构造 helper。',
  'classification_basis':'极端幂指数的窄范围算术错误，归 major；不是普通 primal 计算失效。'
 },
 {
  'id':'root-polyhedron-mass-range','severity':'major','file:line':'src/eab/kernel3d/geom3.py:329-356',
  'summary':'Polyhedron.volume/centroid 的浮点叉积中间下溢破坏体积、体心，甚至使循环重排同一面环改变答案。',
  'failure_scenario':'全 binary64、闭合平面外向面盒，半宽 x=y=2**-600，半高 z=2**600。区间积分真体积1.9279358920823073e-180、体心(0,0,0)；返回体积1.2852905947215381e-180（2/3）和(-2**-600,-2**-600,-2**598)。同尺度四面体真体积4.0165331085048066e-182；面环(1,2,3)返回0，循环改为(2,3,1)返回真值。',
  'how_to_reproduce':'python -X utf8 review/repro/root_polyhedron_mass_range.py',
  'suggested_fix':'以精确相对三重积及一阶矩累计，最后才构造浮点体积和体心；或使用经证实保守的缩放快路并保留精确兜底，不能让中间零触发零体积体心替代。',
  'verified_output':output('root_confirm_mass_final'),
  'verified_log':'review/logs/root_confirm_mass_final.log',
  'oracle_independence':'盒区间乘积和对称中心、四面体坐标积/6，未使用生产叉积、三角化或质量函数。',
  'classification_basis':'混合极端尺度的有效输入窄域；独立构造 API 错误，不声称默认成员谓词同错。'
 }
]
(R/'notes'/'root_findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
print('root findings:',len(findings))
