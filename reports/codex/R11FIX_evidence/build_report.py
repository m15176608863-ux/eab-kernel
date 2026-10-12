"""Create the final Chinese report only after the frozen full suite and audit pass."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8-sig"))


full = read("full_suite.json")
audit = read("delivery_audit.json")
k01 = read("k01/result.json")
k02 = read("k02/final_green.json")
integration = read("integration.json")
full_lines = (HERE / "full_suite.log").read_text(encoding="utf-8").splitlines()
slowest = [line for line in full_lines if " tests/" in line and (" call " in line or " setup " in line)][:5]
slowest_text = "\n".join(slowest)
assert full["exit_code"] == 0 and not full["code_drift"]
assert audit["passed"] and integration["exit_code"] == 0
assert k01["targeted"]["exit_code"] == 0 and k02["pytest_returncode"] == 0
assert k01["exceptions_equal"] and k01["new_exception_entries"] == 0
assert all(row["exit_code"] == 1 for row in k01["mutations"])
assert all(row["caught"] for row in read("k02/mutation.json")["semantic_failures"])
for name, expected in read("scan/final_independent_summary.json")["sha256"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
assert "exact construction AST gate: 0 violation(s)" in (HERE / "static_gate_final.log").read_text(encoding="utf-8")
assert "0 rewritten; 0 kept" in (HERE / "canon_final.log").read_text(encoding="utf-8")
collection = read("collection.json")
assert collection["exit_code"] == 0 and collection["duplicate_nodeids"] == 0
assert str(collection["total_nodes"]) + " passed" in full["last_line"]
baseline = k01["baseline_semantic_tests"]
extra_time = read("interrupted_assert_full_suite.json")["wall_seconds"]
report = f'''# WO-R11FIX 修复报告（2026-10-12，工作树交付，不提交）

## 0. 结论、输入计数与信任边界

输入 [G6K_findings.json](inputs/G6K_findings.json) 实际只有 **G6K-K01、G6K-K02 两条 major**，
不是六条，也不是十一条。本文逐条修复这两条，另以十一项工单验收清单对账；不虚造九条发现。
基线为 `codex-work / c6ac67cfafbfa4540213215101401186b5284612`，已包含 M4a。
两条均已完成修前红、修后绿、被测路径内部变异及同类扫描，最终完整 pytest exit 0。

**M0 已于 2026-10-12 按所有者决定退出；独立正确性复审继续。** 本单不改变该决定，
不把本树测试通过等同独立 G6 的 0 critical / 0 major，也没有违反禁令新建 worktree。
没有 commit / push / reset / checkout / stash / worktree 操作；没有写姊妹仓库、其他工作树或外部设计正本。

修前原字节 [副本](R11FIX_evidence/baseline/) 与 [SHA-256 清单](R11FIX_evidence/baseline_manifest.json)
为回滚锚；未自动回滚任何用户内容。所有 Python 执行使用 `PYTHONDONTWRITEBYTECODE=1` 和 `-X utf8`。

## 1. G6K-K01：静态构造门完整本地数据流合流

### 修前红与真实数值错误

新增门：[test_r11fix_static_flow.py](../../tests/test_r11fix_static_flow.py)。先在修前 scanner 上运行，
开发结束再将最终语义门逐字重放到保存的原始 scanner，结果为
**{baseline['failed']} failed / {baseline['passed']} passed / {baseline['mutation_harness_deselected']} mutation harness deselected**。
[最终修前完整日志](R11FIX_evidence/k01/final_baseline_red.log) 保留全部失败源码及断言；
`-k not removing` 只用于修前重放，排除依赖“修复已存在”的变异装载测试，最终全套未排除任何测试。

三种审查形态 `for _ in ()`、`for _ in range(0)`、`while False` 都植入完整真实
`cone_intersection_margin` 函数，而不是输出后追加假数据：

```python
root = norm_rational
for _ in ():
    root = abs
return root(vector_rational(p, allow_underflow=True)), noise
```

独立 Fraction KKT 及平方中点证书得到 `u=2^-1074`、`p=(-u/3,)*3`；原核返回 `5e-324`，
内部错误构造返回 `0.0`，修前 scanner 返回 `[]`。真正报红的断言为
`K01 real cone rounded-vector assertion`：必须在 `cone_intersection_margin` 报 `rounded-vector`。

### 根因与治根改法

原实现把 rounded 集合合流，却覆盖 callable aliases/bindings；绑定又保存可被后续 rebind
污染的活 AST Name。循环体按文本走一次、异常路径串行扫、推导式零次出口覆盖外层绑定，
都可能让门静默漏检。现改为有限 may-state：**舍入来源 + callable 标签 + 抽象对象引用**的
不可变值快照，环境与对象摘要一起按集合并集合流；对象节点/输入名/源码可调用标签是有限域，
循环与推导式到不动点停止，不设可能漏解的迭代上限，也不递归拼出不断增长的 AST。

覆盖零次循环、回边、break/continue/else、if/条件表达式/短路/比较链、推导式与海象、
异常的中间前缀与独立 handler/else/finally、with 异常抑制、match guard 的失败出口、
词法导入、默认参数、局部容器别名、partial 预绑定和可识别 GeneratorExp 的延迟消费。
最终还修正 `assert` 成功路径不得执行 message、字典 key/value 必须逐对求值、
增量赋值左值不得在写回时二次求值的相同本地绑定次序漏洞。

字段不敏感的对象摘要只从所有者向包含值传播，不能把参数/内部成员的改变反向污染来源对象；
已修复开发中暴露的九处旧代码误报，**原 EXCEPTIONS 表逐字节保持，新增豁免 0**。
未知跨过程返回、反射和任意自定义对象协议仍非证明范围；不是 Python 形式化验证器。

### 修后绿与变异牙

新增 K01 共 **{k01['new_tests_count']} 项**，连同原 R9/R10 静态门的最终结果：
`{k01['targeted']['last_line']}`，见 [日志](R11FIX_evidence/k01/targeted_green.log)。

| 源内撤回 | 指定报红断言 | 结果 |
|---|---|---|
| 删除循环入口/零次路径合流 | `K01 real cone rounded-vector assertion`，真实 cone 植入漏检 | [exit 1](R11FIX_evidence/k01/mutation_zero_path_red.log) |
| 删除回边迭代 | `K01 loop-internal callable fixed-point assertion`，循环内部第 5 行 | [exit 1](R11FIX_evidence/k01/mutation_backedge_red.log) |

后者结束后把 root/saved 明确重绑为 abs；断言钉循环内部行号，不能靠尾部另一个危险调用“代报红”。
两种变异只在内存重编译真实 scanner，不写磁盘源、不伪造输出；pytest 门自身也保留这些杀伤检查。
[机读结果](R11FIX_evidence/k01/result.json) / [专项备忘](R11FIX_evidence/k01/SUMMARY.md)。

## 2. G6K-K02：任意大小整数／浮点混合的精确谓词

新增门：[test_r11fix_numeric_types.py](../../tests/test_r11fix_numeric_types.py)。
原始代码已先跑红；最终测试再次指向冻结 `baseline/src` 重放：
**6 failed, 39 passed, 1 deselected in 0.69s**，见 [完整日志](R11FIX_evidence/k02/final_baseline.log)。

| 真实语义门 | 修前输出／报红 | 修后要求 |
|---|---|---|
| `test_mixed_integer_orientation_keeps_exact_negative_sign` | 精确 det=-3，却 `1 == -1` 失败 | orient2d=-1 |
| `test_mixed_integer_orientation_keeps_exact_zero` | 精确 det=0，却 `1 == 0` 失败 | orient2d=0 |
| `test_all_3072_review_integer_float_orientations_have_exact_signs` | 3072 格中 102 错：82 反号、20 零误判 | 全格与独立 Fraction 行列式一致，正/零/负都出现 |
| `test_mixed_nondegenerate_triangle_is_not_silently_triangulated_to_empty` | 精确两倍面积 1，耳切 `[] != [(0,1,2)]` | 非退化三角保留且精确面积守恒 |
| 大整数 1024/4096 两格 | 混合减法抛 `OverflowError: int too large to convert to float` | 直接精确求符号，不要求谓词输入可显示为 binary64 |

根因：Shewchuk float-only 误差界只计浮点算术误差；原入口只排除 Fraction，
`int - float` 中大整数的先行换算误差未入界。改为仅所有坐标 `type(v) is float`
才走原快路，其余先从原值转 Fraction。没有把调用方数据预先舍入后再声称精确。

同类防守：cross2/dot2 保留纯 Fraction 共同分母整数快算，其他非普通 float 组合直接精确；
orient3d 对 int 等其他类型直接精确，保留原已显式计入转换误差的普通 float/Fraction 快路，
原 `test_orient3d_filter_has_a_real_fast_path` 的两种类型要求未改弱。
构造量合同未改，没有新增静默 0、Inf 或错号路径。

最终新增数值门：**{k02['last_line']}**。整数至 `2**4096`，尺度 `1e-400 / 1 / 1e400`，
3072 个二维格及其三维提升、97 组双线性混合数值、解析二维/三维盒的成员/SAT、区间包含性全部执行。
oracle 自行用 Fraction 展开行列式和解析盒几何，不调用生产的符号、向量、三角化或 SAT 原语。

**变异**：把真实 orient2d 类型门恢复为“仅识别 Fraction”，再次击中上述前四条真实语义断言，
重新出现恰好 `102 / 82 / 20` 和真实耳切空列表。[每条 AssertionError 与调用栈](R11FIX_evidence/k02/mutation.json)。
早期日志的 `source.count(repaired)==1` 是修复尚未存在的装载断言，不计数值证据或变异杀伤。
[专项备忘](R11FIX_evidence/k02/K02_memo.md) / [修后日志](R11FIX_evidence/k02/final_green.log)。

## 3. 同类全仓扫描与十一项验收对账

完整库存、原错及闭环见 [独立扫描备忘](R11FIX_evidence/scan/readonly_scan_memo.md)。
数值独立压力 **10,025 次检查，0 错**：cross2/dot2 各2800、orient2d/orient3d各448、
区间9、polygon_locate 2520、LP reduced cost 1000。基线同探针的7个错均为 K02；
它与审查3072格是不同网格，不混用统计。

| 路径 | 扫描/处置 |
|---|---|
| 2D orient2d 及直接耳切/凸性/线段调用者 | 确认错误，统一类型入口修复；不是只修复审特定数字 |
| cross2/dot2、orient3d | 原界已含转换误差，未把“未找到错误”说成新缺陷；保守收紧其他类型路由 |
| 2D 点在多边形、三角/多边形 SAT | 原入口先 Fraction 化；解析成员、接触、分离/重叠门复跑 |
| 3D `_iv`、边距窗、polygon_locate | 非 float 向两侧 nextafter 包围转换；溢出不确定、精确回退；极端混合输入无错，未无因改写 |
| 3D convex membership/SAT、整数四面体/星并、exact_sweep | 原向量先精确化或正公共分母整数提升；补三维解析盒格 |
| LP `_Exact.reduced_sign` | 模型原先 Fraction 化，转换/乘积/下溢项入界，不确定回退；独立1000格及原证书门 |
| 静态门全部局部 CFG 与已知消费形态 | 多路径完整状态合流、求值次序、迟绑定和别名快照；审查形态及扫描追加反例均落门 |

以下 **11 行是验收事项，不是11条复审发现**：

| 项 | 状态和证据 |
|---|---|
| 01 · K01 | 本报告第1节红→绿、两种内部变异 |
| 02 · K02 | 第2节红→绿、内部回退四条语义断言 |
| 03 · 所有新增门有牙 | 真实构造植入、明确失败行/断言；不以来源定位 guard 代替数学断言 |
| 04 · 数值过滤全仓库存 | 上表 + 独立10,025检查 |
| 05 · 静态控制流全仓库存 | 专项门及独立正/反探针，见扫描备忘与最终摘要 |
| 06 · 第十轮五条保留 | 原五个 `test_r10_*.py` 全部纳入定向及完整套件，未伪造为本轮重修 |
| 07 · M4a 保留 | 三个 `test_m4_*.py` 全部纳入；原adapter/reader/fixtures/expected均未改 |
| 08 · 最终全套 | 第5节原样末行、退出码、墙钟、冻结哈希 |
| 09 · 原门不弱化 | {audit['baseline_test_files_checked']} 个旧测试文件原字节一致，新增门另列；0删、0放松、0skip/xfail、0缩网格 |
| 10 · 文档同步 | README/canon/二维计划/三维设计链接本树设计补充；canon --apply及指针门通过 |
| 11 · 操作范围与回滚 | 原HEAD/分支、{audit['baseline_fixture_files_checked']}夹具、{audit['review_inputs_checked']}输入不变；基线副本、哈希及范围审计 |

## 4. 测试改写、文档与过程台账

- **既有测试文件改写 0**，fixture 改写/删除 0，输入漂移 0。tracked 删除 0，越界 tracked 修改 0。
- 新增 `test_r11fix_static_flow.py` 与 `test_r11fix_numeric_types.py`；开发时将静态断言进一步钉到
  目标行、补足条件表达式与延迟消费；没有缩原网格。数值测试原4处 `float(2**e)` 改为数学值相同的
  `math.ldexp(1.,e)` / `2.**53`，避免以新白名单绕过构造门。
- 改动2个生产模块、1个静态工具、4个既有文档；新增2个测试、本树设计补充、报告与证据。
- scanner 保持原 CRLF，geom.py 原混合换行块保留；`git -c core.whitespace=cr-at-eol diff --check`通过，
  仅命令级参数，没有修改 Git 配置。EXCEPTIONS 原表未变。
- 已执行 `python -X utf8 tools/fix_canon_ptrs.py --apply`：**0 rewritten; 0 kept**；本次移动的定义未触及现有指针，
  不是跳过该要求。canon门同时通过定向/全套。
- 文档同步：[r11fix_design_sync.md](../../docs/r11fix_design_sync.md)。外部 `D:/E(A, B)/07 ...md`
  按工单只读；待所有者纳入补充，不声称已回写。历史M0/G6状态保留，以当前顶部说明区分所有者退出决定。
- 过程环境错误：Windows证据runner的反斜杠 ini pythonpath初次导致收集失败，改POSIX路径后正常；
  PowerShell ASCII管道损坏了刚生成的新中文说明行，UTF-8 readback即发现并修复；旧文件内容未因此丢失。
  这些不计语义红灯。开发中保留的日志是过程证据，不是最终通过依据。

## 5. 最终完整测试、计时与冻结

完整串行命令（没有安装新依赖，没有分片拼接汇总，没有删格）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 reports/codex/R11FIX_evidence/run_full_suite.py
# runner 实际执行：
python -X utf8 -m pytest -q --durations=20 -p no:cacheprovider --basetemp=reports/codex/R11FIX_evidence/tmp/full_suite
```

**最终完整日志最后一行原样：**

```text
{full['last_line']}
```

退出码 **0**；墙钟 **{full['wall_seconds']:.3f} s**。
{('达到 ≤900 s 目标。' if full['within_900_seconds'] else '未达到 ≤900 s 目标。没有为速度弱化门；本机没有 xdist，采用完整串行运行。')}
最慢20项详见 [完整日志](R11FIX_evidence/full_suite.log)；[命令/耗时/代码稳定性 JSON](R11FIX_evidence/full_suite.json)。
{full['code_files_checked']} 个源/测试/工具 Python 文件运行前后 SHA-256 一致，**code_drift=[]**。

最慢5项原样：

```text
{slowest_text}
```

新增124门的独立定向运行只需 `1.25s`，但这不是隔离测量新实现对全部旧门的间接耗时。
README保留的M4a历史全套为1191.84s（不是本次HEAD的受控性能基线）；不同运行时负载未受控，
不能据本次计时宣称性能提升或退化。

最终独立收集核验：`{collection['last_line']}`，重复nodeid为0；M4a共109项，R10共209项，
两个新文件分别78/46项。完整 [按文件收集清单](R11FIX_evidence/collection.json) 与全套通过数量一致。
静态CLI为 [0 violation(s)](R11FIX_evidence/static_gate_final.log)，canon再核为
[0 rewritten; 0 kept](R11FIX_evidence/canon_final.log)。

定向整合的最终原样末行：`{integration['last_line']}`，含新门、所有R10、R9静态、M4a、
filter、canon与fixture门，见 [整合日志](R11FIX_evidence/integration.log)。定向不替代完整全套。

一次较早完整运行在 **{extra_time:.3f} s** 时主动中止：冻结后的最后复看发现 `assert` message
成功路径求值遗漏，随后同时补字典/增量赋值的同根因顺序门。中止前源码无漂移，不能计作绿；
[中止元数据](R11FIX_evidence/interrupted_assert_full_suite.json)及日志保留。修后重新冻结并从头完整运行。
本节最终计时不包含这次中止、逐条红绿、变异、扫描、写报告的额外时间。

## 6. 遗留与交付

本轮两条已确认发现无待修项；有限数值网格不是任意数值子类/非有限输入的形式化证明，
静态 may-analysis 也不证明任意反射、跨过程返回、自定义协议、任意协程/生成器函数。
已有局部/窗口/显示构造的几何信任边界不升级。M4a仍是离线影子对账，不是工程标定或生产切换。

未执行、仍需所有者安排：新的只读 fresh-tree 六路独立G6，以及外部设计正本回写。
这两项受本工单范围禁止，不以本树绿冒充已完成；本单实现和验证交付已完成。

[交付索引](R11FIX_DELIVERY_INDEX.md) / [最终范围审计](R11FIX_evidence/delivery_audit.json) /
[交付文件哈希清单](R11FIX_evidence/delivery_manifest.json)。

R11FIX_DONE
'''
report_path = ROOT / "reports/codex/R11FIX_report.md"
report_path.write_text(report, encoding="utf-8")
modified = audit["modified_tracked"] + ["tests/test_r11fix_static_flow.py", "tests/test_r11fix_numeric_types.py",
                                       "docs/r11fix_design_sync.md", "reports/codex/R11FIX_report.md"]
index_path = ROOT / "reports/codex/R11FIX_DELIVERY_INDEX.md"
lines = ["# R11FIX 交付索引", "", "工作树未提交；本索引给出全部实现/测试/文档及关键证据链接。", "",
         "## 实现、门和文档", ""]
lines += [f"- [{name}]({(ROOT / name).as_uri()})" for name in modified]
lines += ["", "## 证据与复跑", ""]
for name in ["PLAN.md", "baseline_manifest.json", "input_manifest.json", "full_suite.log", "full_suite.json",
             "integration.log", "delivery_audit.json", "delivery_manifest.json", "run_full_suite.py",
             "run_integration.py", "verify_delivery.py", "verify_artifacts.py", "artifact_qa.json",
             "collection.json", "build_report.py", "k01/result.json",
             "k01/SUMMARY.md", "k01/run_final_baseline.py", "k01/run_mutation.py", "k02/K02_memo.md",
             "k02/run_evidence.py", "scan/readonly_scan_memo.md", "scan/final_independent_summary.json"]:
    lines.append(f"- [{name}]({(HERE / name).as_uri()})")
lines += [f"- [全部证据目录]({HERE.as_uri()}/)", f"- [修前原字节副本]({(HERE / 'baseline').as_uri()}/)",
          "", "baseline 为回滚锚；tmp 为pytest临时夹具；dev/new_scan 为开发过程证据，不是生产入口。",
          "正式源入口仅 tools/check_exact_construction.py 与 src/eab 下的已列模块。"]
index_path.write_text("\n".join(lines)+"\n", encoding="utf-8")
files = {ROOT / p for p in modified} | {index_path}
for path in HERE.rglob("*"):
    if path.is_file() and not any(part == "baseline" or part.startswith("tmp") for part in path.relative_to(HERE).parts):
        if path.name != "delivery_manifest.json":
            files.add(path)
manifest = {p.relative_to(ROOT).as_posix(): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                                         "bytes": p.stat().st_size, "link": p.as_uri()}
            for p in sorted(files)}
(HERE / "delivery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(report_path)
print(index_path)
print(f"Manifest entries: {len(manifest)}")
