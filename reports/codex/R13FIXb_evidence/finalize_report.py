"""Generate the Chinese report from completed run receipts; never fabricate green."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main():
    suite = read("full_suite_verified/summary.json")
    assert suite["status"] == "PASS" and all(suite["checks"].values())
    static_bytes = (HERE / "root/static_release.log").read_bytes()
    static_text = static_bytes.decode("utf-16" if static_bytes.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    assert static_text.strip().splitlines()[-1] == "exact construction AST gate: 0 violation(s)"
    coverage = read("coverage_summary.json")
    old = read("root/before/tools/exact_construction_policy.json")
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    identity = lambda r: (r["path"], r["function"], r["rule"], r["node"])
    a, b = {identity(r): r for r in old["waivers"]}, {identity(r): r for r in policy["waivers"]}
    ledger = dict(before=len(old["waivers"]), after=len(policy["waivers"]),
                  removed=[a[k] for k in sorted(a.keys()-b.keys())], added=[b[k] for k in sorted(b.keys()-a.keys())],
                  renewed=[b[k] for k in sorted(a.keys() & b.keys()) if a[k]["context"] != b[k]["context"]],
                  imports_added=sorted(set(policy["imports"])-set(old["imports"])))
    (HERE / "root/policy_delta_final.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = read("remaining_138.json")
    groups = {g: Counter(r["status"] for r in rows if r["review_group"] == g)
              for g in ("root", "kernel", "dual_margin", "readers_oracles")}
    table = "\n".join(f"| {g} | {sum(c.values())} | {c['differential']} | {c['nonconstructive']} | {c['gap']} |" for g, c in groups.items())
    shards = "\n".join(f"| {r['name']} | `{r['last_line']}` | {r['exit_code']} |" for r in suite["runs"])
    mutation_rows = []
    for group in ("kernel", "dual_margin", "readers_oracles"):
        for row in read(group+"/mutations.json"):
            name = row.get("mutant", row.get("mutation", row.get("construction_class")))
            evidence = row.get("tail", row.get("observed_assertion", row.get("expected_failure_message")))
            mutation_rows.append(f"| {group} / {name} | {evidence} |")
    for name, evidence in [("mixed raw早强转", "mixed integer exact residual"),
                           ("input域检查移除", "DID NOT RAISE"),
                           ("scalar下溢检查移除", "DID NOT RAISE"),
                           ("face_noise恢复中间norm", "本应支持的最终比值被中间范围错误阻断")]:
        mutation_rows.append(f"| root / {name} | {evidence} |")
    mutations = "\n".join(mutation_rows)
    report = f"""# WO-R13FIX-b：数值支持域与公开构造差分门收尾报告

日期：2026-10-13。工作树 `D:/eab-wt/cx-e2`，分支 `codex-work`，基线 `92788cd86d93c4134439804d22d438946d3cadb9`。

## 结论

**PARTIAL；全套绿。** 原138项已逐项处置：**107项三档独立逐值门、29项不产生派生构造量证明、2项缺口**。
缺口为 `Dual.__pow__` 一般非整数幂、`convergence_order.large_h_order` 通用误差界。
另在原138之外明确记录 `Bdda2DWindow.cone_tol/metadata` 两项平台有限门，未冒充通用libm证明。
不能据此声称全公开API都已经满足新数值合同，不能报缺口0或DONE。

核心交付：[支持域定义](../../docs/exact_predicates_plan.md#r13fixb-numeric-domain)、
[逐项可读表](../../docs/r13fix_construction_inventory.md)、[138项机读表](R13FIXb_evidence/remaining_138.json)、
[全量原915行增量表](R13FIXb_evidence/public_api_inventory.json)、[额外31项审查](R13FIXb_evidence/additional_review.json)。

## 1. 范围、回滚与验收

- 初始tracked工作树干净。只改本树；无commit/push/reset/checkout/stash/worktree操作，无姊妹仓库或其他工作树写入，无fixtures改动。
- 回滚锚点为只读HEAD和[修改前字节/哈希](R13FIXb_evidence/root/baseline.json)；没有执行回滚。
- Python采用 `PYTHONDONTWRITEBYTECODE=1 python -X utf8`；进程TEMP/TMP及测试basetemp位于 `R13FIXb_evidence/tmp/`。
  最终全套禁用pytest cacheprovider；较早子任务默认pytest曾更新本树已有`.pytest_cache`，没有删除它或操作其他树。
- 工单禁止新worktree，故不宣称新鲜树门或独立六路G6。三代理分工与组间复核只是本任务交叉核验。
- 目标是声明支持域、响亮失败、三档独立逐值门与内部变异、完整节点全套绿。前四者仍有上面明确残余，不以最后一项替代。

## 2. 支持域定义与推导

1. **判定不变**：在各API既有几何有效性与定义域前提下，给定任意有限binary64/int/Fraction均按精确值判定。工程限幅不装在几何容器或成员/相交/凸性分支上。
2. **精确有理输出/搬运数据**保留全有限输入；**最终一次舍入的代数构造**也不人为缩至±400。
   Fraction中间量可超过binary64，最终RN-even须有限；默认精确非零量不得静默为0。
3. **需限定的近似入口**使用 `D400 = {{0}} ∪ {{x: 2^-400≤|x|≤2^400}}`，以Fraction精确比界。
   支持条件还包括该API输出/声明中间量可表达，并有正确舍入或明确误差模型；单纯过输入盒不够。
4. 推导：差值可到2^401，双线性项2^800，常数项和仍在binary64指数范围内；体积三次项却可达2^±1200。
   Fraction输入还可在普通坐标上相差2^-2000。因此不能只检坐标，也不能按条件数扩大容差。
   默认正非零输出胞为 `(2^-1075, (max_binary64+2^1024)/2)`，两端RN分别为0/inf而拒绝，负数对称。
5. `face_noise`采用53位尾数、无指数限制的逐边根式模型；正周长的相对误差≤u，最终舍入再贡献≤u，
   故正规结果相对界为 `2u+u²`（u=2^-53），次正规加绝对2^-1075。不声称多根式正确舍入。
6. LP/exact证书支持的显示字段、无界状态和退化几何哨兵有单独语义；不是普通有限物理量。
   私有margin通道只在独立精确平方落入RN-zero胞时保留0显示及exact证书；公共裸距离仍抛专门异常。

集中实现：[numeric_domain.py](../../src/eab/numeric_domain.py) 的 `ConstructionDomainError`、`exact_input`、
`check_input/check_inputs`；[construction.py](../../src/eab/construction.py) 的最终RN与范围边界。
模块文档及README引用支持域正本。raw向量、Dual代数、精确oracle、reader数字转换保留更大的可表达域；
有限差分/随机造型/adapter角度等近似入口分别接集中检查。

## 3. 138项逐项汇总

| 分组 | 原缺口项 | 独立三档差分 | 非构造证明 | 未闭合 |
|---|---:|---:|---:|---:|
{table}
| 合计 | 138 | 107 | 29 | 2 |

不是靠函数名/grep/全套绿匹配覆盖。每行有API、具体nodeid、尺度、参考公式/返回域证明及限制；
机器生成器只核节点存在与集合完整，不伪造独立性。低/普通/高使用±400附近的有效几何（高端按系数留余量）；
三维失败报告采用2^395以保证最大坐标24s仍小于2^400；精确integer-payload oracle的1/7/2^397注明其类型下界。
纯统计计数/布尔/输入转发不冒称新的几何构造。原249字段及表外旧107映射没有自动变成全域已证明。

组间复核曾发现3个G0报告仅测零值、surface_events缺标签—时刻绑定；补入真实内部投影/枚举缺陷后的完整
非零failure、construction_failure、completeness_failure逐值记录，及独立xy消元的完整(label,time)集合。
[最终交叉复核](R13FIXb_evidence/readers_oracles/kernel_cross_review_final.json)关闭这4项，不等于全G6。

## 4. 域内真错及两项旧遗留

| 问题 | 处理与证据 |
|---|---|
| int/float raw向量相消 | `(2^54+1)+(-2^54)`旧0、新1；完整有理多项式后RN；超输出范围旧inf改专门异常。 |
| 超长边face_noise | 旧中间norm拒绝最终可表达比值；新扩展尾数长度不受中间指数限制，2^±1200补充复核也通过。 |
| Dual混合标量及普通导数 | `_pair`早强转丢低位，乘积/商导数快捷路早舍入；改完整有理primal/jet。 |
| 判断入口float强转 | `val/is_exact_zero`与Dual比较曾把2^-2000 Fraction当零；改精确访问/比较。 |
| exact/oracle原始float代数 | 公开raw dot/交点参数早乘法，2^-400或2^397三角交点可能报None；显式lift或最终RN并保持旧float/Dual协议。 |
| 三维brute首入 | 隐式加厚与长度对时间的停止条件令t=3变2.999999996或3.5；改精确平移/有理二分；仍只是佐证oracle。 |
| margin噪声报告 | contact_resolution普通输入差1ulp；完整声明模型有理表达式后RN。 |
| reader与重复顶点 | 数值文本静默上下溢、整数ID经float丢位、1-(-2^-53)早舍入导致错并；分别最终验界、直接整数、精确差与窗。 |
| convergence_order中间比值 | 2^800/2^-800溢出改整数对数差，保留有限误差字段门；一般对数误差界仍gap。 |

根组[修前/修后](R13FIXb_evidence/root/root_before_after.json)；
[Dual/margin详细证据](R13FIXb_evidence/dual_margin/summary.md)；
[kernel证据](R13FIXb_evidence/kernel/summary.md)；[reader证据](R13FIXb_evidence/readers_oracles/summary.md)。
不是所有新增门都代表生产原来错：未改算法的API只称补门。独立补充复核1600次raw运算与120个不对称face_noise，0失败，
最大相对误差约1.21e-16；见[复核JSON](R13FIXb_evidence/readers_oracles/root_crosscheck.json)，这是观察不是一般证明。

## 5. 内部变异表

所有变异进入实际函数/枚举路径；不在返回产物后追加假盖。以下{len(mutation_rows)}项含早舍入、域检查删除及绑定错配，
目标失败均已核其断言/范围原因，不用偶然顶点选择或语法错误算“杀死”。

| 内部变异 | 实际失败/指定断言 |
|---|---|
{mutations}

完整注入、日志与尺度：[kernel](R13FIXb_evidence/kernel/mutations.json)、
[Dual/margin](R13FIXb_evidence/dual_margin/mutations.json)、[reader/oracle](R13FIXb_evidence/readers_oracles/mutations.json)、
[root永久门](../../tests/test_r13fixb_domain.py)。根组变异随最终全套再次执行。

## 6. 旧门迁移及静态辅助账

- R6 Dual的两格非零primal下溢按所有者新合同改测专门异常；旧导数逐值参考保留并直接核内部导数表达式。
  参数、nodeid未删，未skip/xfail。
- R7/R10的旧源码变异锚点随真实实现迁移，继续打内部早舍入/范围缺陷，原目标断言不放宽；
  不以缩进语法错误冒充数值门有牙。完整列表见Dual分报告。
- 首轮全套保留了5处失败：1处真实次正规逃逸报告回归（内部阈值过早强制构造成float），4处旧变异工具失配。
  逃逸内部阈值改为精确Fraction传递/比较，公共浮点报告仍严格拒绝不可表达值；没有以静默0绕开。
  reader旧注入器转发新增关键字；R6/R7/R9旧变异恢复真正的原始早乘/早平方语句，保留原数值断言，
  不以新范围守卫碰巧报错当作原目标断言通过。原节点、参数、断言未删；首轮完整11994节点记录见
  [失败审计](R13FIXb_evidence/full_suite_final/summary.json)，墙钟600.330s、运行期源码漂移0。修复后重新全套。
  [阈值独立复核](R13FIXb_evidence/kernel/threshold_review/review.md)另核极端有理判定、精确非零阈值、公共量名异常与暖缓存内部变异；
  [旧几何变异迁移](R13FIXb_evidence/kernel/legacy_mutations_migration.json)及[reader helper迁移](R13FIXb_evidence/readers_oracles/shadow_helper_compatibility.json)保留备份和哈希。
- 静态分析器代码未新增形态，最后一行：`exact construction AST gate: 0 violation(s)`。
- 人工局部站点账：**{len(old['waivers'])} − {len(ledger['removed'])} + {len(ledger['added'])} = {len(policy['waivers'])}**，
  另续审{len(ledger['renewed'])}个保留站点的最小源码pin；新增{len(ledger['imports_added'])}个显式命名import准入。
  仅审查列明的域边界/代数分支/报告模型/独立测试oracle与变异工具，不是自动扫描后全部放行。
  [逐站点delta](R13FIXb_evidence/root/policy_delta_final.json)、[理由/源码pin](R13FIXb_evidence/root/static_review.json)。
- 初次维护脚本错误把24个Call节点pin成同源码的Expr包装，门仍报红，后按真实Call更正；
  [纠正账](R13FIXb_evidence/root/static_pin_node_corrections.json)。未放宽分析器来消除诊断。

## 7. 全套与耗时

新增{suite['tests_executed']-11723}个节点；原11723个全部保留，当前**{suite['tests_executed']} passed**。
四个独立标准pytest进程，完整文件分片，无-k/漏格；每片末行原样：

| 分片 | pytest最后一行 | 退出码 |
|---|---|---:|
{shards}

运行器末行原样：

```text
R13FIXb_FULL_SUITE PASS: {suite['tests_executed']} calls; wall={suite['wall_seconds']:.3f}s; failures_or_skips=0; source_drift=0
```

执行墙钟 **{suite['wall_seconds']:.3f}s**，收集 **{suite['collection_seconds']:.3f}s**；总约
**{suite['wall_seconds']+suite['collection_seconds']:.3f}s**。四进程墙钟之和不当CPU基准。
收集与执行nodeid多重集合一致、无重复；所有setup/call/teardown通过，进程退出0，冻结运行期间源码/测试/政策/文档无漂移。
[summary.json](R13FIXb_evidence/full_suite_verified/summary.json)、[完整节点](R13FIXb_evidence/full_suite_verified/collection_nodes.json)、
[运行器日志](R13FIXb_evidence/full_suite_verified_runner.log)、[分片证据目录](R13FIXb_evidence/full_suite_verified/)。

此外：修复后的新门、全部首轮失败所属文件及文档门定向 `435 passed in 12.45s`；此前相关Dual组合2456、reader组合308、kernel补强76各自通过，
它们不是重复累加到全套测试数。指针工具首次 `--apply` 为 **22 rewritten; 0 kept**；修复后再次为 **11 rewritten; 0 kept**，最终复核 **0 rewritten; 0 kept**。

最终全套前已纠正清单中四行说明的UTF-8问号乱码、失败子族尺度标注与支持域数学措辞。
全套后没有改生产/测试/政策/冻结文档；单独核清单集合、引用节点、逐类尺度产物互异、文件链接与hash；证据见
[最终交付核验](R13FIXb_evidence/artifact_verification.json)。

## 8. 可重跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Resolve-Path reports/codex/R13FIXb_evidence/tmp).Path
$env:TMP=$env:TEMP
python -X utf8 tools/check_exact_construction.py
python -X utf8 reports/codex/R13FIXb_evidence/build_inventory.py
python -X utf8 reports/codex/R13FIXb_evidence/verify_artifacts.py
$env:R13B_RUN_NAME='full_suite_rerun_01' # 必须用新目录，不覆盖既有日志
python -X utf8 reports/codex/R13FIXb_evidence/run_full_suite.py
python -X utf8 tools/fix_canon_ptrs.py --apply
```

## 9. 必须保留的遗留

1. 原138范围内缺口=**2**：一般非整数 `Dual.__pow__` 误差界/完整专门异常审查；`convergence_order.large_h_order` 通用log误差界。
2. 原138之外：adapter `cone_tol/metadata` 的有限平台误差门不是跨平台libm定理；此前sin/cos/一般角度、一般凹体/力学活跃集的旧限制未自动消失。
3. 新支持合同是所有者要求，未实现到全仓每一个近似调用点；上述未闭合路径不能声称已保证域外统一专门异常或域内通用误差界。
4. {len(policy['waivers'])}条静态人工排除仍非任意Python安全证明；第三方标量协议、动态调用、资源耗尽等不由本合同兜底。
5. 未执行新worktree/独立G6，未写回外部只读设计正本，不改变M0所有者决定与M4a边界。

R13FIXb_PARTIAL：原138项剩2项（一般非整数Dual.__pow__、convergence_order对数阶数误差界）；额外adapter角度通用libm界及全仓近似入口合同未闭合
"""
    (ROOT / "reports/codex/R13FIXb_report.md").write_text(report, encoding="utf-8")
    print("Report generated from verified receipts; final status PARTIAL, original gap count 2.")


if __name__ == "__main__":
    main()
