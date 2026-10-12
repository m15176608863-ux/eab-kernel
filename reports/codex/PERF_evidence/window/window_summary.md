# WO-PERF：局部贯入厚度窗口定稿证据

## 结果

保留 `contact_window` 参数名，仅明确其为**局部贯入厚度窗口，非整体最短分离平移 PD**。未新增兼容别名，因为没有改参数名。README、canon_map、exact_3d_design、exact_predicates_plan 已统一标记“E5 已完成（窗口为局部贯入厚度口径）”，同时明确该状态不冒称独立六路 G6。

相触的精确可靠性为析取：六轴脱离证书证明 PD≤w；星核壳证书证明所有重叠区域位于该体厚度≤w的径向壳内，不能推断整体 PD≤w。报贯入不推出 PD>w。分离侧仍为精确距离平方≤w²。默认 None/0 不采用政策。

## 独立 oracle 与门

新文件 [test_perf_contact_window.py](file:///D:/eab-wt/cx-e2/tests/test_perf_contact_window.py) 共 25 格。oracle 仅用 Fraction 算术、已知精确正交基、区间积、笛卡尔积角点检验与平方范数；不共用生产法向、相交、SAT、三角化、星核或距离原语。

- 六轴 18 格：6 个符号轴×3 组尺度/坐标（1/16、1、64；含非对称平移及1e6工程坐标），都在 PD=w 分界；仅指定轴可解除贯入。
- 双壁键的薄壳可靠性：全部核心顶点是统一比例缩放，边界任意点是面顶点的凸组合，凸范数最大值证明连续的全部径向壳段≤w；两重叠区均由精确区间证实避开内核。平移禁入盒并覆盖[-1,1]^3，故整体 PD>1，w仅1/64。
- 斜向漏检：半长(1,4,4)盒重叠9/40，w=1/4，旋转(cos,sin)=(3/5,4/5)后有限证书全失败，实际PD=9/40<w。
- 六轴坐标依赖与旋转：上述相同位形未旋转相触，旋转后贯入；前者确有短轴证书，后者只表达有限证书失败。
- 薄壳旋转反例：双壁键旋转后 L1 半径变大、内核缩小厚度变小；前者仅core_A通过，后者全失败；两姿态均无短轴证书，隔离了壳自身的坐标依赖。

对应可靠性表与数学表达在 [三维设计 §2a](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md)。

## 突变牙

| 内部突变 | 真正报红的公开路径断言 | 证据 |
| --- | --- | --- |
| star_core 的 α=min(w/R,1/2) 改 α=min(2w/R,1/2) | 两侧3w/2重叠被错报相触；`reject-thicker-than-w-shell` | [log](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/mutation_shell_w_to_2w.log) |
| contact_models 六轴删 +z，变五轴 | 唯有+z能脱离的格错报贯入；`axis-public-report` | [log](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/mutation_six_axes_to_five.log) |

两者都注入生产函数体，不在产出后追加假数据；绕过 margin 已有内容缓存以免旧值遮蔽。执行器仅在进程内命名空间注入，不覆盖磁盘源码，结束即恢复：[可复跑执行器](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/run_window_mutations.py)、[结果 JSON](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/mutation_results.json)。内置 pytest 牙门亦执行同样突变并确认精确断言信息。

## 验证

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q tests/test_perf_contact_window.py --basetemp=reports/codex/PERF_evidence/window/tmp --junitxml=reports/codex/PERF_evidence/window/window_junit.xml
python -X utf8 reports/codex/PERF_evidence/window/run_window_mutations.py
```

最后一行原样：`25 passed in 0.87s`。见 [原测试输出](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/window_tests.log)、[JUnit](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/window_junit.xml)、[摘要 JSON](file:///D:/eab-wt/cx-e2/reports/codex/PERF_evidence/window/window_summary.json)。全套性能及最终全套状态由 WO-PERF 总报告记录，本分项不代其声称。

执行中一次并行开发窗口遇到 covers3.py 临时语法错误，未更改该文件；该负责代理修正后复跑全部25格为绿。一次 PowerShell 输出目录未创建、一次中文脚本管道编码不匹配均在写入前停止；分别创建本树证据目录、显式 UTF-8 管道编码后完成，不影响最终源文件。

WINDOW_CONTRACT_DONE
