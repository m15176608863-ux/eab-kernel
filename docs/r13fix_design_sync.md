# R13FIX 设计同步（2026-10-13）

## 1. 当前定位：运行时差分为主，静态检查为辅

所有者决定：`tools/check_exact_construction.py`、数据流分析与子集准入是**辅助的代码检查，不是安全保证**。
任意 Python 的完全可靠静态数据流分析不可实现，连续四轮出现的新形态绕过说明不能以“零诊断”代替数学正确性。
今后的复审中，“检查被绕过但没有现有生产代码错误实例”按 minor 处理；本轮输入 G6M-01 的原 major 分级仍如实保留。

“没有先舍入再构造”的主保证改为公开构造量与**独立有理参考**的运行时差分门：
给定浮点数按其精确二进有理数解释；源坐标/参数先进入完整有理表达式，再构造最终数值。
距离、法向、面积、体积、间隙、见证点及导数都需要逐字段绑定真值，不能只测试返回值在自己位置上的自洽性。
网格须包含次正规、普通、上溢边缘、相消、非对称输入及合法的范围拒绝；单位法向/面积等其他同时返回量的可表达域也须核对。
有理平方或平方中点证书用于根式；独立参考不能调用生产几何或生产构造函数。
有限网格和变异牙不是全域形式证明。

本轮并未把上述要求虚报为“全部实现”：公开 API 库存、已覆盖/新增/未覆盖分类见
[构造 API 清单](r13fix_construction_inventory.md)。最终完成状态与残余项见 [R13FIX 报告](../reports/codex/R13FIX_report.md)。
M0 的所有者退出决定不变，本轮不是独立六路 G6，也没有新鲜 worktree 验证。

## 2. 静态辅助检查的补强与边界

已知源码类的 `self` 字段写、普通实例方法、单继承 `__init__`、dataclass `__post_init__`、显式属性 setter
纳入 receiver 字段摘要。构造前的混合浮点运算必须传播到 sink；注解不是来源证明。
定向门：[生命周期回归](../tests/test_r13fix_static_lifecycle.py)，含原审查三种形态及字段传播内部变异。

无法据此承诺识别全部：动态安装的方法/描述符、元类、运行时 monkeypatch、未知扩展代码、任意别名、重入协议、
复杂/多继承 MRO 等。识别到的未知形态可保守拒绝，“没有报告”不能推导“没有问题”。

R12FIXb 的**局部**例外仍锁 AST 站点与最小封闭源码 SHA-256；不恢复整库依赖快照。
int/Fraction 变量和受支持容器/调用的数据流可准入，不再是“纯整数字面量”限定。
人工排除不是证明。数值修复使旧作用域失效时，应逐条删除或审阅；不能批量刷新 hash 来掩盖新诊断。

本轮清单为 2451 条：原 2365 条删除 22 个失效站点，逐 AST 人工审阅 108 条近似输入/诊断/结构摘要范围；
另续审 11 个已改坐标函数的原泛型回退节点（不增加条数）。这些排除及混合类型范围遗留均不属于机器证明；
没有给 G6M 的三个新错误 helper 增加例外。逐站点证据见报告，不能单看“零诊断”。

## 3. 事件显示必须绑定独立事件

G6M-02 修正 `test_entrance3.py` 的 24 格随机门，并补二维同类 30 格：
保留实际返回点的状态核验，额外由独立 Fraction SAT/区间求首事件并核 `exact_t` 与每个返回坐标。
每个显示坐标必须满足 `RN-even(x0 + t_exact*d)` 的独立中点胞证书。
不能用“浮点边界可能变”来放过 `x -> x0`。

其他首入/出口/逃逸门的盘点、极端尺度、法向/见证/显示高度绑定与真实内部变异见
[事件门](../tests/test_r13fix_event_bindings.py) 及证据摘要。
`escape_candidates` 是名义报告，`dilatancy_profile` 是显示高度差分；它们不是精确运动候选全集或精确解析导数。

## 4. 同类生产修复

- 二/三维 public dot/cross 的全 float 路径：完整积和/行列式先 Fraction 后最终构造，避免次正规丢失与 `inf-inf -> NaN`。
  Fraction/其他泛型路径不被转换成 float；见 [几何差分门](../tests/test_r13fix_geometry_differential.py)。
- 相对噪声报告：不要先构造一个下溢的绝对噪声地板再除短棱；比值采用精确分子与精确平方。
  面噪声的周长模型明确为“逐棱最终舍入长度的精确和”，不是多根式精确舍入保证。
- `limit.friction_generators`：每个分量完整有理表达式后舍入。三维角度与 sin/cos 仍是给定 libm 系数模型，
  不声称理想圆锥或超越函数精确化。见 [力学差分门](../tests/test_r13fix_mechanics_differential.py)。
- frozen 六种盖的值/法向/导数与 margin 距离/间隙/见证点采用独立闭式逐值门；见
  [冻结与裕度差分门](../tests/test_r13fix_frozen_margin_differential.py)。

## 5. 范围、回滚与验证

只写 `D:/eab-wt/cx-e2`；基线 `fabe303`，原有未跟踪复审输入保留。无 commit/push/reset/checkout/stash/worktree 操作。
外部理论正本 `D:/E(A, B)` 只读；本文件是本工作树对设计正本的同步补遗，不声称已写回正本。
M4a 的冻结导出、适配器语义和三组门保留，不改姊妹仓库或 fixtures。

可重跑命令（PowerShell）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/check_exact_construction.py
python -X utf8 tools/fix_canon_ptrs.py --apply
python -X utf8 reports/codex/R13FIX_evidence/run_full_suite.py
# 等价串行全套；先建立 basetemp 的父目录，且只使用本树内新目录
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=reports/codex/R13FIX_evidence/tmp/manual_full
```

全套运行器采用四个原生 pytest 进程、完整文件分片，核对收集/执行 nodeid 并集无缺失无重复，
核验原 11508 节点未删、无 skip/xfail、运行期间源码/配置/政策哈希不变。
900 s 是尽量达到的全套墙钟目标，不用减少格子或排除慢门达标；实测值在报告中。
