"""Persist the root reviewer's fully read old/new LP migration adjudications."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / 'review/gates_docs/changed_existing_tests.json').read_text(encoding='utf-8'))
selected = [r for r in rows if 'limit' in r['file'] or 'lp_' in r['file']]
notes = [
    ('加强独立求解', '独立4阶Gauss从float绝对主元地板改Fraction精确零；原闭式输入与平衡断言保留，不共用LP原语。'),
    ('给定数据合同订正，未确认弱化', '原近似sin/cos平面机构不一定是给定二进制数据的可行机构；新门保留alpha/行耗散核验，拒绝drive!=1的近似手工候选，并增加轴对齐精确手工机构及错行序候选。不是仅跳过边界态。'),
    ('给定数据合同订正，未确认弱化', '原把sin(pi)的非零给定数据答案强制成理想物理不可行；新门要求exact alpha*sin(pi)=1、nearby_infeasible风险报告，另保留精确水平荷载不可行格。'),
    ('给定数据逐格真值替代，未确认弱化', '原全部小分量网格保留；每格exact alpha*v=1与self_check，分别核resolved/unresolved/nearby_infeasible，移除的是答案强行改成理想状态，不是oracle跳过。'),
    ('保留报告敏感性，未确认弱化', '原monkeypatch一阶U=1仍在；稳定alpha=5须resolved，不稳定格须精确alpha及nearby_infeasible，不再把给定数据可行答案改报不可行。'),
    ('风险口径订正并加强拒答约束', '原随机1000格不变，旧允许<=10个响亮拒答改为raised为空；极大alpha须unresolved并由独立精确LP组装核状态/答案。普通格仍主要self_check，未声称独立穷举所有物理摩擦模型。'),
    ('加强真路径微小注入', '旧float*.999改Fraction(1-10^-digits)，digits=3/9/30/100，同UTM输入与必须抛RuntimeError目标保留；root另亲跑float及精确候选污染。'),
    ('加强精确非零缺陷检查', '原远body各D格及静力/机构/真实LP三条注入保留；精确delta和残差!=0替代任意>1e-5门，避免小信号被地板吞掉。spfloat仅控制注入幅值而非真值。'),
    ('给定数据逐格真值替代，未确认弱化', '原三风险区网格保留且增加loaded body位置/额外body格；核exact alpha*v、对偶与self_check，风险报告不得改变答案或跳过当前数据状态。'),
    ('加强精确错误答案检查', '原错误factor格保留，精确Fraction因子替代float相乘，先确认正确候选ok再断言错候选false；增加极小错误尺度。'),
    ('加强真实LP输出污染', '旧真实maximize alpha*.999变成四个digits的精确Fraction tiny污染；异常类型及真实limit_load路径不变，避免浮点注入先舍入为原答案。'),
    ('仅合同文字变化，原牙未弱化', '函数正文和断言不变；穿透倾倒机构的拒绝及不同工程坐标网格保留。doc不再冒称容差会把当前问题答案改成理想机构。'),
    ('独立当前数据LP替代理想状态', '原六个dead-load量级和2D/3D网格保留；逐格独立exact LP状态/答案比对，风险报告在适用时强制核验，不以nearby状态替代当前状态。'),
    ('加强精确状态约束', '原28近自锁网格不变，旧margin<1e-9可响亮拒答改为必须返回给定数据精确LP答案；大margin须resolved，resolved格保留闭式误差核验，小margin风险报告强制检查。'),
    ('派生黏聚上限独立精确化；共享模型锚需限定', '旧上限X(C.cap)复用已经舍入的生产乘积，新为Fraction(cohesion)*Fraction(area)，力矩/荷载移位独立组装；仍读取生产_build_columns给出的浮点摩擦射线，不能当该射线模型自身的零共用oracle。'),
    ('给定数据逐格真值替代，未确认弱化', '原24组W/H/a/T/press网格保留；旧理想摩擦无界/不可行强制态改为独立exact LP逐帧核验，每帧风险状态按实际报告检查，不因边界可变跳过当前状态。'),
    ('给定数据逐格真值替代，未确认弱化', '原五个帧输入保留；当前精确LP逐格核，近邻风险单列且强制检查，旧把舍入驱动无界强制拒答的合同退出，不是允许错答。'),
    ('保留近邻风险触发格，未确认弱化', '原给定无界点及八角点有限证书保留；新要求当前exact无界并unresolved且风险候选含optimal，替代强制抛错。八角点构造本身不是所有报告扰动域的独立形式证明。'),
]
assert len(selected) == len(notes) == 18
result = []
for r, (verdict, reason) in zip(selected, notes):
    result.append({
        'file': r['file'], 'function': r['name'], 'line': r['line'],
        'full_old_new_text_read': True, 'verdict': verdict, 'reason': reason,
        'old_assert_count': r['assert_old'], 'new_assert_count': r['assert_new'],
        'decorators_identical': r['decorators_same'],
        'source_sha256': {'old_function': hashlib.sha256(r['old'].encode()).hexdigest(),
                          'new_function': hashlib.sha256(r['new'].encode()).hexdigest()},
        'new_confirmed_finding': False,
        'verification_limit': '逐函数两版正文全文已读；额外实跑为root_limit_guard、root_lp_audit及G6E原输入重放，不声称每项所有可能变异都执行。',
    })
(ROOT / 'review/root_migration_final_pass.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'items': len(result), 'fully_read': all(r['full_old_new_text_read'] for r in result)}, ensure_ascii=False))
