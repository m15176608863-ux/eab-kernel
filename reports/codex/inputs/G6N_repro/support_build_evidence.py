"""Rebuild the child audit with native UTF-8 source, not a PowerShell text pipe."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / "review/evidence"

def log(name):
    b = (ROOT / "review/logs" / name).read_bytes()
    return b.decode("utf-16") if b[:2] in (b"\xff\xfe", b"\xfe\xff") else b.decode("utf-8-sig")

report = json.loads((E / "support_findings.json").read_text(encoding="utf-8"))
report["scope"] = "WO-G6N 子任务 A：支持域合同、remaining_138 的 29 项非构造证明、入口漏网及有理参考独立性"
f1, f2 = report["findings"]
f1.update(
    conclusion="Dual.__pow__ 在进入精确整数幂之前把整数/Fraction 指数转成 binary64，丢奇偶性并静默返回 primal 与导数的相反符号。",
    failure_scenario="Dual(-1.0,(1.0,)) ** (2**54+1)：正确 primal=-1.0、导数 RN(2**54+1)=+2**54，当前结果 Dual(+1.0,(-2**54,))；同指数换成 Fraction 仍错。输入有限、指数小于 2**400、最终输出可表达。",
    suggested_fix="保持指数的 int/Fraction 精确值，先按精确整数性/分母分派代数路径，完整表达式完成后舍入；非代数分支另核支持域。本审查不实施修复。",
    grading="巨大整数/Fraction 指数的窄输入族，按错误答案但范围窄计 major；不是静态绕过，也不是一般非整数幂缺口本身。",
)
f2.update(
    conclusion="公开 sin/cos/atan2 在 libm 调用前把精确 int/Fraction 转成 binary64，D400内产生宏观相位错；域外同比小参数 atan2 又静默变0。",
    failure_scenario="D400内 q=2**54+1：sin 返回0.8973347529975925，独立有理Machin/Taylor界真值约0.11344832269377987，误差>0.783886；cos和Dual版也错。另 q=2**54+1/3 同错。域外 x=Fraction(2)**-1075（另测 -1100/-2000），atan2(x,x)及Dual primal返回0，而独立有理积分界真角在(1/2,1)，sin(x)也静默0。",
    suggested_fix="所有近似公共标量/Dual 入口先核精确原始输入支持域，域外抛含量名的 ConstructionDomainError；或以精确齐次比例缩放支持 atan2。一般 libm 舍入缺口不豁免已证明的错误零角。",
    grading="巨大精确实数和极小Fraction的窄输入族，计 major；已有D400内宏观错误，不是一般libm相差一ulp或缺口未证明。域外响亮报错不计。",
)
f2["additional_repro"] = "python -X utf8 review/repro/root_trig_exact_argument.py"
f2["additional_verified_output"] = log("support_trig_cross_review.txt")
f2["oracle_cross_review"] = "独立读并复跑root参考：atan(1/5)、atan(1/239)交错级数界组成Machin π区间；任意整数2π约减的区间由exact Fraction得；点Taylor尾项与全局Lipschitz常数1覆盖区间偏移。初始项不必单调，42项之后尾项比<1足够交错尾界。未使用被测libm/构造作为参考。"
report["corroborations_not_separately_counted"][0]["conclusion"] = "JSON 默认 parse_float 在 checked constructor 前把 1e-400 变 0；交 root 与 ContactRecord JSON 读取边界发现合并去重。"
report["verification"]["first_attempt_environment_error"] = "第一次 review/tmp 父目录不存在：236 passed,39 setup errors。创建本树 review/tmp 后相同 275 节点重跑全绿，未改被审源码。"
report["oracle_independence"] = "生产 construction 与参考 oracle_construction 仅共用异常类，没有共用构造/几何原语；生产 isqrt/significand 与参考 Fraction 中点认证及位搜索不同。四个 R13FIXb 门的内联有理/Decimal/解析盒参考没有调用被测几何原语算 expected；有限输入族不是全域定理。"
report["coverage_limitations"] = [
    "没有逐行审查全部 915 API 或 2674 静态例外；未证明未列问题入口全部正确。",
    "29 项只确认对外无派生浮点构造量，不替代内部全域判定正确性证明；inflated_membership 清单承认下游构造异常限制。",
    "未证明一般非整数幂及一般 libm 误差界；不把已声明缺口或遗留未证明本身算发现。",
    "50 条 G6E 回归、接触窗口及 LP 全面审查由 root 和其他子任务负责。",
    "长背景 README/canon_map/exact_3d 在本子任务聚焦合同与源码映射；理论正本 00/01/03/07 未在本子任务单独全面逐条核验。",
]
(E / "support_findings.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
rows = json.loads((E / "support_nonconstructive_29.json").read_text(encoding="utf-8"))
for row in rows:
    row["audit_conclusion"] = "成立：对外不产生派生浮点构造量；不据此替代内部精确判定正确性证明。"
(E / "support_nonconstructive_29.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

md = """# G6N 支持域专审（子任务 A）

被审 HEAD：`878d4f0a260cc703eab7d883ab574fddc2ec2f3d`。独立审查、不修生产代码，只写本树 `review/`。

## 结论

本子任务确认 **0 critical / 2 major / 0 minor**。另确认 bdda3d JSON 读取同类漏网，交 root 与 ContactRecord JSON 发现去重，不重复计数。M0 与总计以 root 汇总为准。

## 支持域定义与推导

- D400 输入条件没有被当作充分输出条件。差值401、双线性800、三次1200的指数推导成立；任意 Fraction 相消/接近零分母无法靠输入盒保证可表达，该限制明确保留。
- 默认输出胞 `(2^-1075,(max_binary64+2^1024)/2)` 的两端 RN-even 分别为0/inf，应拒绝。独立4364次 Fraction 胞核验（精确中点、次正规、±2400指数、上溢端点）0差异；接受2844、正确拒绝1520。有限探针不是一般证明。
- face_noise 的正边长/正周长相对误差≤u，最终 RN 再≤u，组合界2u+u²、次正规绝对加半minsub的推导未见不自洽。无限指数53位中间近似没有对可表达最终比值作错误限幅。
- 根/范数/单位分量最终边界和有理输出不人为缩到D400的结构未发现错误；域外响亮错误不计。
- 入口没有全部闭合：整数幂提前强转、atan2/sin 参数转换及 JSON 解析有下面可运行的真实错误，不因报告 PARTIAL 而豁免。

## 已确认发现
"""
for f in report["findings"]:
    md += f"\n### {f['id']} — {f['severity']}\n\n"
    for key, title in [("file", "位置"), ("conclusion", "结论"), ("failure_scenario", "场景"), ("grading", "分级"), ("suggested_fix", "建议")]:
        md += f"- **{title}**：{f[key]}\n"
    md += f"- **重放**：[{f['repro_path']}](file:///D:/eab-wt/g6n/{f['repro_path']})\n\n```text\n{f['verified_output'].strip()}\n```\n"
    if "additional_verified_output" in f:
        md += "\nD400内增强反例已独立读参考数学并复跑：[root有理相位脚本](file:///D:/eab-wt/g6n/review/repro/root_trig_exact_argument.py)。不新增计数，合并同一早转float根因。\n\n```text\n" + f["additional_verified_output"].strip() + "\n```\n"
md += """
## 29 项非构造证明逐项核验

逐个定位后读完整函数与返回链。20 kernel / 2 dual_margin / 7 reader_oracle项均成立：公共返回为离散标签/计数/布尔、原对象/原输入坐标、索引结构或None。这不自动证明内部算术/判定无错。

[29 项机读源码/返回形式清单](file:///D:/eab-wt/g6n/review/evidence/support_nonconstructive_29.json)。

| API | 核验 |
|---|---|
"""
for x in rows:
    md += f"| `{x['api']}` | 成立；`{x['path']}:{x['lines'][0]}-{x['lines'][1]}` |\n"
md += """
## oracle 与运行证据

参考 oracle_construction 不 import 生产构造/几何，只共用异常类；Decimal/float 候选须通过独立有理中点胞认证，否则退位搜索。生产根为isqrt/significand路径。门的内联有理代数、解析盒/区间、原文本字段未以被测几何helper构造真值；此结论仅限读过的门及输入族。

四个 R13FIXb 新门自跑，标准单pytest进程（不是全套）：

```text
""" + log("support_targeted_rerun.txt").strip() + "\n```\n"
md += """
初跑 review/tmp 父目录不存在，236 passed/39 setup errors（FileNotFoundError），保留[失败日志](file:///D:/eab-wt/g6n/review/logs/support_targeted.txt)。新建本树tmp后同275节点重跑全绿，没有改源码或断言。

独立构造边界探针：

```text
""" + log("support_constructor_probe.txt").strip() + "\n```\n"
md += """
## JSON 同类佐证（交 root 去重）

bdda3d.load_records 默认JSON解析使数值literal `area=1e-400`先变0；同值字符串被正确拒绝。当前门在test_r13fixb_readers_oracles.py:281-283直接调record_from_entrance(area=Fraction(bad))，没有穿JSON输入路径。

[脚本](file:///D:/eab-wt/g6n/review/repro/support_json_reader.py) / [输出](file:///D:/eab-wt/g6n/review/logs/support_json_reader.txt)。

```text
""" + log("support_json_reader.txt").strip() + "\n```\n"
md += """
## 完整性批评

深入逐行读：numeric_domain、construction、dual、oracle_construction、g0_oracle、ContactRecord、bdda3d/tf_probe/adapter入口及29项对应函数；读剩余138全条映射、额外31项/全915表相关分类、R13FIX/R13FIXb报告、支持域数学节和四个R13FIXb新门。几何/力学只读相关段，不冒充全仓逐行审计。

未读/未证明：全部915 API、2674静态例外逐条；一般凹体、一般libm/非整数幂、全力学活跃集；50条旧回归和九镜头总体由root/其他子任务负责。长README/canon_map/exact_3d聚焦合同与映射，未在子任务单独逐条核理论正本00/01/03/07。没有做生产文件磁盘变异；新缺陷直接跑现有代码。未改任何已跟踪文件。
"""
(E / "support_audit.md").write_text(md, encoding="utf-8")
for path in [E / "support_audit.md", E / "support_findings.json", E / "support_nonconstructive_29.json"]:
    data = path.read_text(encoding="utf-8")
    assert "????" not in data, path
    assert any("\u4e00" <= c <= "\u9fff" for c in data), path
print("UTF8_SUPPORT_ARTIFACTS_VERIFIED 3 files; Chinese preserved; no question-mark replacement runs")
