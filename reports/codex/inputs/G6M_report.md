# WO-G6M：G6 第十三轮独立正确性复审

审查对象：新鲜 detached 工作树 `D:/eab-wt/g6m`，HEAD **`fabe303b9d574891094b0b9e86b171343e469bfc`**。审查方与实现方上下文隔离；中文交付；不修生产代码。所有审查新增文件、变异副本和日志只在 [review](file:///D:/eab-wt/g6m/review/) 内。

## 1. 结论与退出判断

**确认：0 critical / 1 major / 2 minor。** 未确认项不计数，同根因三个静态漏网形态合并为一项。

|编号|等级|位置|结论|
|---|---|---|---|
|G6M-01|major|`tools/exact_construction_flow.py:945–979,1013–1021`；`tools/exact_construction_subset.py:124–135`|类生命周期和实例方法的字段副作用漏传播，完全新代码、无例外条目仍可通过默认拒绝门并给出错误范数。|
|G6M-02|minor|`tests/test_entrance3.py:159–165`|首入返回位置字段在测试迁移后与正确事件端点脱钩；真实内部 `x→x0` 缺陷旧门红、新入口数学门全绿；当前静态锁仍能拒绝该源码突变。|
|G6M-03|minor|`docs/canon_map.md:3`|顶部 R12FIX 段仍描述已被 R12FIXb 撤销的整模块／全库依赖锁及整数常量限定，与现行局部锁和 Fraction 数据流证明不同步。|

**M0 是否可以退出：按工单的严格 `0 critical / 0 major` 确认标准，本轮不满足退出门。** 所有者此前已决定 M0 退出、复审并行继续，本报告不擅自撤销该管理决定；但不能用本轮审计作为“独立 G6 零 major”的证明。生产现有数学路径本轮没有确认新的静默错误答案；G6M-01 是新的静态门漏检，按“门无牙使 critical 可能潜入”计 major，而非把审查新增错误 helper 冒称原生产 critical。

**2365 条已声明遗留排除不因“未证明”而列为发现。** G6M-01 的三个新增文件各自 `approved_sites=0`，没有复用、修改或新增豁免；与待消化遗留清单无关。

### 全套自跑

<!-- FULL_SUITE_RESULT -->
**本审查独立串行全套：`11508 passed in 1636.79s (0:27:16)`，退出码0。** runner壁钟 1646.202 s；Python 3.12.10。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:/eab-wt/g6m/review/tmp/full
```

[命令、退出码、壁钟证据](file:///D:/eab-wt/g6m/review/evidence/full_pytest_result.json) · [完整日志](file:///D:/eab-wt/g6m/review/logs/full_pytest.log)。不是引用实现方／Claude旧日志，也没有用定向测试代全套。
<!-- FULL_SUITE_RESULT_END -->

工单里的 `<g6f 内 tmp>` 与其他工作树只读约束冲突，故 basetemp 使用本工作树的 `review/tmp/full`。初次全套已在审查开始时启动；后续定向证据与它并行，但 **pytest 本身串行、不使用 xdist**。各耗时不作为独占机器性能验收。

## 2. G6M-01 — major：新类状态变化可绕过默认拒绝

### 具体输入、错误输出与独立真值

```python
from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational

@dataclass
class Holder:
    points: tuple[Fraction, Fraction]
    def __post_init__(self):
        self.points = tuple(component * 1.0 for component in self.points)

def bad(q: Fraction):
    return norm_rational(Holder((q, q)).points)

q = Fraction(1, 2**1075)
```

正确范数是 `sqrt(2)·q`，最终正确 RN-even binary64 视图为 **`5e-324`**；新 helper 实际返回 **`0.0`**。`1.0` 乘法先把两个有理分量下溢为零。oracle 不调用生产 norm、sqrt 或构造 oracle：令 `u=2**-1074`，独立 Fraction 证书满足 `(u/2)**2 < 2*q*q < (3*u/2)**2`，精确值严格在最小正次正规数的舍入胞内，非平局。

等价漏网形态还有继承自 `Parent` 的 `__init__`，以及显式 `holder.update()` 实例方法。三者共因是记录字段／receiver 的生命周期与副作用未完整传播，不能按三条重复计数。

### 为什么这是门缺陷，而非构造 API 被错误使用就应免责

- 本轮的目标明确是**新代码默认拒绝**，防止有理输入在构造前被舍入；这里是三个新源文件，零批准站点。
- 将同一字段更新改成普通显式 helper `update(holder: Holder)`，当前门会报 `closed-unproved-arithmetic` 和 `closed-rounded-construction`，说明这正是门承诺看护的缺陷类别。
- 类构造分支只总结直接 `Class.__init__`，遗漏 dataclass `__post_init__` 及继承初始化；实例方法分支只归并 `_function` 返回值，未像普通调用一样向 receiver 回写字段／未证明副作用。
- 在只含审查复制源树的 `review/copies/static_lifecycle` 内，加入三个新文件，**完整 src/tests/tools 扫描仍零违例**；原 policy 不变。不是对真实枚举结果事后追加假数据，也不是 monkeypatch 自检遮羞。

### 亲跑输出

```text
dataclass_post_init:       actual=0.0 expected=5e-324 scan_text=[] approved_sites=0
inherited_init:           actual=0.0 expected=5e-324 scan_text=[] approved_sites=0
instance_method_mutation: actual=0.0 expected=5e-324 scan_text=[] approved_sites=0
whole_repository_scan_issues=[]
whole_repository_scan_seconds=58.75643310000305
policy_unchanged=true
```

policy SHA-256：`73fde62383d7064ad94b58523a79586015c056b3bc57cea7ea0dd6d30a0abffe`。原 flow 文件 SHA-256：`24d07687a8103b7fd71ae0ad4956e1b4fb4a3551941d3d6cd5fb05e774b702c6`，复验未改。

**直接复跑（在仓库根，约一分钟）：**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/static_lifecycle_bypass.py
```

[脚本](file:///D:/eab-wt/g6m/review/repro/static_lifecycle_bypass.py) · [主审亲跑日志](file:///D:/eab-wt/g6m/review/logs/root_verified_static_lifecycle.log) · [完整输入、正反对照和输出 JSON](file:///D:/eab-wt/g6m/review/static_logs/lifecycle_bypass.json)。

**建议修复方向（本审查不实施）：** 对 dataclass 后初始化、继承 MRO 初始化、实例方法的字段写及 sink／未证明副作用作统一 receiver 摘要和回写；无法证明的协议默认拒绝，不以注解当值证明。为三个形态加真实源内变异牙，确认红在构造／副作用禁入断言，不是 pin 偶然失效。不可通过添加该站点排除或刷新清单来宣称数学问题已解决。

## 3. G6M-02 — minor：首入返回平移的数学门迁移变弱

旧门要求返回 `e.x` 对应相触状态；精确化后，正确舍入的浮点端点确可能位于真实边界两侧，废掉“回代必相触”的理想化断言是合理的。问题在新门只核“任意返回 `e.x` 的状态与同位置 oracle 一致”，然后在**另行构造的正确事件端点**核相触，未核返回字段本身等于 `RN-even(x0+exact_t*d)`。

在只读 git archive 的旧／新副本中，将真实正事件 `Entrance3` 构造器的返回 `x` 改为 `x0`，不改时刻、候选、法向、标签及内部自检。每次 `finally` 按原字节恢复，核 SHA-256。

具体 seed=0：

- `x0=(-3.017738778724177,3.152165214937428,2.3413999174549023)`；
- `d=(0.8153759443636078,-0.8117489883216957,-0.5161267997792374)`；
- 时刻仍为正确 `t=3.3193317016553476`；
- 应返回 `(-0.3112355578308868,0.45770106421456686,0.6282038688737575)`，变异却返回原起点。

**主审親跑：**

```text
old baseline:   24 passed in 8.32s
old mutant:     23 failed, 1 passed in 8.43s
current baseline: 24 passed in 9.20s
current mutant:   24 passed in 9.15s
current mutant_entrance_domain: 164 passed in 17.26s
HISTORY_X_MIGRATION_CONFIRMED old gate red / new gate green / archives restored
```

旧门红在原返回位置的相触断言，唯一绿格为 none 分支。新六入口文件绿不等于全套绿：主审另外亲跑**同一源码变异**的静态扫描，baseline `0`，mutant **`24`** 诊断（含 6 条 `closed-stale-waiver`）。局部源锁仍是有效冗余屏障，故此项只计 minor，不能夸成完整门无牙 major。原生产 baseline 返回字段正确。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/history_x_migration.py
python -X utf8 review/repro/history_x_exhibit.py
python -X utf8 review/repro/history_x_static_redundancy.py
```

脚本在缺失副本时仅用 read-only `git archive` 生成 `review/copies/history_old` 与 `history_current`，不覆盖未知非空目录；三脚本共享副本，须串行。[迁移复跑](file:///D:/eab-wt/g6m/review/repro/history_x_migration.py) · [主审日志](file:///D:/eab-wt/g6m/review/logs/root_verified_history_x.log) · [具体输入输出](file:///D:/eab-wt/g6m/review/logs/history_x_exhibit.json) · [主审静态冗余复验](file:///D:/eab-wt/g6m/review/logs/root_verified_history_static_redundancy.log)。

**建议：** 保留实际输入边界可变的合法口径，改核独立精确 earliest time 与每个返回坐标的 Fraction midpoint 舍入证书；加 `x→x0` 构造器内部牙。将 E5a2 台账的“不弱于旧门”限定到实际保留的性质，不能以“边界可变”跳过返回字段一致性。

## 4. G6M-03 — minor：canon 顶部仍是已撤销的机制

`docs/canon_map.md:3` 称例外由“完整模块 AST／上下文及全 src/tests/tools 原字节依赖图钉住”，且“自动算术证明仅限纯整数字面量”。当前 policy schema 2 的合同却明确 **Local AST site and minimal enclosing source SHA256 only; No dependency snapshot**，设计同步和 README 已说明可证明的变量／Fraction 子集，撤掉全库快照。

亲跑当前真实 `geom3.py` 的**内存文本**，只加无关尾注，文件内容 hash 改变，但 `approved_sites=88→88`，诊断 `[]→[]`；没有写被审源文件。policy 无 `dependency_snapshot`／`dependencies`。这符合新机制，却反证旧顶部段若当现行说明即错误。

```powershell
python -X utf8 review/repro/root_doc_contract_drift.py
```

[复跑脚本](file:///D:/eab-wt/g6m/review/repro/root_doc_contract_drift.py) · [亲跑输出](file:///D:/eab-wt/g6m/review/logs/root_doc_contract_drift.log) · [机读比较](file:///D:/eab-wt/g6m/review/evidence/root_doc_drift.json)。

**分级与建议：** 最新 README／`r12fix_design_sync.md` 已诚实订正，并非核心数学保证被虚报，故 minor。把该段标为 R12FIX 历史版本并注明 R12FIXb 替代，或同步为局部 source pin／站点 AST 和数据流证明，不恢复已撤销全库锁。

## 5. 优先级审查：R12 回放、新机制与新 diff

1. **R12 原 major 已消解。** 原四形态 `map_norm / map_sqrt / iter_callable / pop_callable` 仍会在错误 helper 中把 `5e-324` 算成 `0.0`，但当前 checker 均报 `closed-*`，不再 `issues=[]`。[原回放运行器](file:///D:/eab-wt/g6m/review/repro/static_r12_replay.py) · [输出](file:///D:/eab-wt/g6m/review/static_logs/r12_replay.log)。
2. **已覆盖的站点局部锁有牙。** 在真实 2365 清单上，`_pair_generic` 只改注释：6 站点失效、2359 不动、9 诊断；`_pair_ve3_wedge`：12 失效、2353 不动、15 诊断。函数内改而不重新批准不能保持 source hash；函数外无关注释保持绿。新增普通危险函数报红。[局部锁脚本](file:///D:/eab-wt/g6m/review/repro/static_real_policy_locality.py) · [机读证据](file:///D:/eab-wt/g6m/review/static_logs/real_policy_locality_probe.json)。这不是对所有可达被调函数语义的依赖闭包证明；G6M-01 是另一个实际漏网。
3. **三道维护门目标断言真红。** 在审查副本内部改 checker：删除局部 source hash 审批／陈旧核对条件 → `only the edited function's sites may expire` 红；存在 policy 就默认放行无站点记录 → `new_forbidden` 断言红；无关 `__init__.py` 注释污染全部 pin → `unrelated comment must not invalidate any review` 红。最后一种过期 3623 格。仅改审查副本，原根 checker／subset／policy SHA不变，不靠不相干脆断言计牙。[脚本](file:///D:/eab-wt/g6m/review/repro/static_maintenance_teeth.py) · [证据](file:///D:/eab-wt/g6m/review/static_logs/maintenance_teeth.json)。
4. 静态新六测试文件定向串行 **252 passed in 197.38s**。首次子审 basetemp 父目录未建立导致 10 setup errors，修正审查环境后全绿；不是生产数学失败。[成功日志](file:///D:/eab-wt/g6m/review/static_logs/pytest_baseline2.log)；保留失败日志以避免挑绿。
5. `git diff 0ce65a4..HEAD -- src tests tools docs` 为 **77 文件、30492 插入／425 删除**，其中 policy 27078 行、flow 1099、subset 536。几何和力学改动主要是明确生成式替代 `map`、闭合源值传播、callback 改显式数据／调用；检查了逐项新路径、源码级行为等价及原门改写。没有把“全绿”代替新静态机制正确性证明。

[静态详细分报告](file:///D:/eab-wt/g6m/review/static_audit.md) 包含全部形态、三道维护门目标红因和限制。

## 6. 九镜头覆盖与证据

### 镜头 1：精确性声称与浮点分支

全 `src/eab` 作 AST／文本候选库存：涉及 tol／eps／noise／window／resolution 或浮点常量的 **325 条条件候选**（条件语句与子比较会重复，不是 325 个独立缺陷）。[原始库存](file:///D:/eab-wt/g6m/review/evidence/branch_inventory_raw.json)；[根审 95 条分类](file:///D:/eab-wt/g6m/review/evidence/root_branch_classification.json)；[几何补齐的257条分类](file:///D:/eab-wt/g6m/review/geometry_branch_classification.json)，另补原关键词未覆盖的 predicates 符号界站点，两分类不能简单相加当不重复数。这是检索辅助，不冒充穷尽所有 Python 控制流。

- `lp.py` 浮点单纯形阈值只产生候选，`solve` 精确核验最优／无界／不可行证书，不过走有理数 simplex；核验原始 `exact=` 派生数据，不信浮点状态。独立对拍及错误候选注入见镜头 7。
- 浮点过滤决定是否可接受已证明的符号，不确定、次正规、非 float 输入、overflow／nonfinite 候选回精确路径；压力覆盖快路与回退，未确认改变数学答案的噪声带。
- `window / t_max / contact_window` 是调用方显式域窗口，`near_labels / resolvability` 是报告，不等于精确 tied set；不能把合法报告阈值列为错误成员判定。
- `Dual` 与旧 frozen 本构普通浮点导数运算有披露的近似口径，零通道跳过／域错误与隐式 float 拒收分别核读；不是“所有导数符号均有理精确”承诺。
- `bdda_geom` 近重复清洗是明确保留的 L5 近似输入模型，原输入短特征可丢失的实测留未确认合同风险，见第 7 节。

### 镜头 2：浮点过滤、舍入构造、缓存与兜底

独立 Fraction 展开行列式／水平射线奇偶／闭线段投影 oracle，对拍 **78600** 次：cross2 27000、dot2 18000、orient2d 18000、orient3d 12000、polygon locate 3600，零错误。指数涵盖 binary64 次正规到最大量级、混合有理数／大整数、相消及非二进制扰动；orient3d 1599 次接受快路、10401 次回精确（2020 纯浮点、8381 混合精确）。[脚本](file:///D:/eab-wt/g6m/review/repro/geometry_numeric_pressure.py) · [结果](file:///D:/eab-wt/g6m/review/geometry/numeric_pressure.json)。

主审新构造 oracle 只用 Fraction 舍入胞／奇偶 tie，核 sqrt **4643**、norm **4244**、unit 分量 **12528**、差向量规范化 **2366** 次；1243 次合法溢出／range 拒收；零错误。[脚本](file:///D:/eab-wt/g6m/review/repro/root_constructor_pressure.py) · [结果](file:///D:/eab-wt/g6m/review/evidence/root_constructor_pressure.json)。

缓存压力包含顶点／面原内容更改、returned view 别名污染、按原内容重建缓存以及强制禁用 SAT／星核／transverse 快路的 arrangement 兜底；**120** 次 box case 独立区间平方距一致。Dual／不可解析输入不拿浮点值碰撞成同一个几何键。覆盖不是每个缓存所有可能对象生命周期的证明。[脚本](file:///D:/eab-wt/g6m/review/repro/geometry_cache_fallback_pressure.py) · [结果](file:///D:/eab-wt/g6m/review/geometry/cache_fallback_pressure.json)。

### 镜头 3：oracle 原语独立性

读 E2–PERF 处置与 oracle：二维独立投影 SAT／Jarvis，三维独立整数 hull／SAT；盖 oracle 独立 Newell／Gram／Gordan；surface oracle 独立耳切／认证 tetra-union；margin/frozen/wall 独立特征平方距和 swept 区间；生产构造整数 significand/isqrt 对照 Decimal 候选＋Fraction midpoint/bit-pattern oracle。文件位于 src 内不自动意味着共享生产原语。

动态毒化 **11 个生产模块、281 函数**，清全部 oracle 缓存后，8 条完整 expected 路径仍与毒化前全等。另亲跑原有 6 条原语毒化／内部牙绿，以及 PERF＋第五轮定向32格绿。[新脚本](file:///D:/eab-wt/g6m/review/repro/history_oracle_poison.py) · [8 路输出](file:///D:/eab-wt/g6m/review/logs/history_oracle_poison.log)。本轮自写各 oracle 的原语见具体脚本 docstring；未用被测 `polyhedra_overlap` 作几何主真值。

### 镜头 4：旧门迁移是否变弱

对 `b6126cf..HEAD -- tests/` 和 E2–PERF 台账作 AST 库存：旧561、现1245个 test 函数，共555，116个同名函数改变；6个旧名消失属于已披露二维精确化改名族。保存旧／新 assert AST 和函数 hash。[库存](file:///D:/eab-wt/g6m/review/logs/history_test_migration_inventory.json)。

正当迁移包括实际 rounded 输入独立核真值、有理理想轨核闭式性质、删除真边界噪声豁免及把牙移到真实谓词路径。**没有逐项变异完 116 个函数**；成对变异确认的 G6M-02 已列，不把台账或参数数量当数学强度证明。边界可变不是任意输出可变，返回字段需要独立不变量。

### 镜头 5：二维／三维、凸／凹、互锁几何压力

独立 exact 圆整／扫描线／区间／tetra-union 模型，覆盖共线、共面、近平行、短棱、凹槽、薄壳、多组件、巨坐标、微尺寸、精确有理刚体运动和单位变换；成员、距离、沿向首入、逃逸高度、盖／G0 主要路径零确认错误。不能把用 float 正弦构造的“理想刚体运动”同已舍入真实输入混为一个模型。

有效凹棱柱首入 **96** case，含32个断开组件；新增非单调多分量逃逸 **48** case，含孤立相触、间隙1e-30和窗口。独立原G6L压力原样重放：2D scanline **240**、tetra **96**、nested shell **48** case。先前随机构造的非法 ring 明确隔离为 invalid generation，不冒充合法反例。原几何历史24脚本与独立等价补验另列镜头9；另定向 **119 passed in 2.72s**。输入及局限见 [几何分报告](file:///D:/eab-wt/g6m/review/geometry_audit.md) 和 [几何证据目录](file:///D:/eab-wt/g6m/review/geometry/)。

这不是任意复杂凹壳的穷尽证明；任意旋转引起的输入舍入、源 ring 与实际处理面片必须分别记录。无效自交／非流形输入不用于指控有明确前置条件的 API。

### 镜头 6：局部贯入厚度／接触窗口证书

核文档的**OR 证书**，而非把所有 ON_BOUNDARY 都解释为正本的闭集分离 `PD_closed≤w`。工单括号里的“PD”必须按现行已订正合同分开：`rho=inf{||d||₂:int(A+d)∩int(B)=∅}`，正本 `PD_closed=inf{||d||₂:(A+d)∩B=∅}`。一般闭壳两者不同，凸盒特例才同下确界：

- 六轴证书：存在长度恰为 w 的有理平移后无严格重叠（闭相触允许），则 **rho≤w，不证明PD_closed≤w**；不是一般旋转证明。
- 核心薄壳证书：同中心有理缩核、位移最大值≤w，若核心不与另一体严格重叠，每个 overlap 点只能落于对应壳内；若走薄壳分支，并不声称单次平移能退出、或完整 overlap 体积很小。

主审亲跑独立 Fraction product-box oracle：精确有理正交 frame、尺度 `1e-9 / 1 / 1e5`、平移到 `1e8`、三个轴和三个贯入比例，**108 cases / 0 mismatches**。逐模型验 shift 全顶点同位移且平方=w²；缩核同中心 factor∈[1/2,1)，最大顶点径向平方≤w²；独立区间分类，与 public margin 的 OR 结果一致。[脚本](file:///D:/eab-wt/g6m/review/repro/root_window_certificates.py) · [证据](file:///D:/eab-wt/g6m/review/logs/root_window_certificates.json)。凹体 shell／union 补验见几何分报告。未找到违反已声明证书命题的具体当前输入，不把“六轴不完整”误报成“充分可靠性失效”。

### 镜头 7：LP、极限分析与可分辨性报告

主审独立 Fraction Gaussian 消元／秩约化／穷举基，recession 可行性判无界（不调用生产 pivot/inverse/certificate）：**1000** LP，239 optimal／356 unbounded／405 infeasible，行列尺度 `10^-400..10^400`、浮点视图可下溢／上溢；三状态全同。239最优 exact_x/exact_y 精确满足原始／对偶、目标相等，浮点视图逐项等于最终转换。另 **15000** reduced-sign 极端相消过滤与 Fraction 真符号全同。[脚本](file:///D:/eab-wt/g6m/review/repro/root_lp_pressure.py) · [结果](file:///D:/eab-wt/g6m/review/evidence/root_lp_pressure.json)。

自写接触静力／倾覆界，非对称工程位置、几何／荷载缩放、黏聚组合：24单体＋24多体。把 alpha 改坏 `1e-3 / 1e-30 / 1e-100`，**144** 次正确拒收；在真实 `maximize` 边界注入 `exact_x / exact_y` 的 `1e-100` 错误并同时改浮点视图，**96** 次实际 limit 调用抛 self-check RuntimeError，不是事后给假日志。[脚本](file:///D:/eab-wt/g6m/review/repro/root_selfcheck_pressure.py) · [结果](file:///D:/eab-wt/g6m/review/evidence/root_selfcheck_pressure.json)。

核读 live uncertainty 为特定对偶机构的一阶估计、非全局扰动界；nearby status / unresolved 报告不改精确 nominal status。第五轮20–23／45／47复验无无关块全局尺度吞噪、次优 alpha 穿透或不可分辨输入被冒称真实自锁的问题。

### 镜头 8：文档、声称、理论正本与 07 对代码

只读必读资料、处置台账、`g6f` 提交说明已纳入；理论01／03／07全文及00定义、§3.3、§4.6等相关段核对。核方向 A动/B定、盖弱完备≠凹块全局成员、非凹裁剪完成、低维法向随平移、LP有理派生模型、窗口证书和 M4a 离线范围。

四份指定仓库文档抽取 **67 条**含 ✔／已完成／已验证／有门等行及测试引用，引用文件存在检查无 missing；保存上下文而非只取漂亮句子。[清单](file:///D:/eab-wt/g6m/review/evidence/document_claim_inventory.json)。该存在检查**不意味着67条均独立数学证明或逐条变异验证**；抽查命名门的实际断言、全部文件通过须与全套结果联合看。本轮确认的文字漂移是 G6M-03。

canon 的第二个“八”《07对代码》明确保留历史缺口：canonical_order_key≠canonical_key，3 readers≠六表示全覆盖，tf抽样≠8 benchmark，G1静态集合≠锁态／滑动／位移同构，G2手写夹具≠探针全同构，M4a15配对45帧≠完整轨迹或在线切换，MLCP／全局凹盖裁剪仍未实现。未将这些**已披露缺口**重新当“未完成就缺陷”，也未发现该表本轮新增核心完成误报。历史声称中的日期、旧计数和“未经G6”不冒称现行结果。

### 镜头 9：G6E 至少20条原／等价回放

本轮实测 **30 个唯一编号**：24 条原脚本字节同源复制及6条等价。编号为 **07、09、11、20、21、22、23、24、25、26、27、28、29、30、31、34、36、37、38、39、40、41、42、43、44、45、47、48、49、50**；其中23/39/47/48/49/50为等价重放。[逐项输入、stdout与处置 JSON](file:///D:/eab-wt/g6m/review/logs/history_g6e_replay_dispositions.json) · [30条中文逐项表](file:///D:/eab-wt/g6m/review/history_audit.md) · [原脚本来源 SHA](file:///D:/eab-wt/g6m/review/logs/history_legacy_manifest.json)。

**没有把脚本 rc0 当作缺陷已关闭。** 特别核清：

- #24 原浮点变换80格实际72内部／8分离／0相触，独立整数 tetra-union SAT 同答；理想相触另用有理刚体轨保留。
- #36 原浮点运动输入确会改标签；精确有理刚体与大平移的18标签完整全等。
- #40 原脚本先 float 做 b−a，40/64差点与精确差点不同，三条 hull anomaly 来源是两模型混用；先 Fraction 做差后 `facet_vote=(0,6,0,0,[])`，public G0绿，默认 eps 无 NameError。
- #39/#50 对真实局部锥内部恒 True 注入，精确 G0顶点票报红；#47任意微贯入／微 alpha 错误不被远体速度吞掉；#48真微台阶不容差合面；#49真活动支持对独立邻点严格支撑。

未实跑剩余20个编号，见完整性批评，不声称第五轮50条全部本轮重审关闭。

## 7. 未确认／不计数项

|事项|实测／疑点|为何不计确认缺陷|
|---|---|---|
|reader短特征清洗|`dup_tol=0`，T=1e8，u=ulp(T)，五顶点凸小尖角与矩形原 strict overlap=1；reader alias 掉尖角后4顶点且 state=-1。独立 Fraction 内点证书。|`bdda_geom.py:44–59` 明示 near-duplicate coordinate floor，L5 输入清洗后的模型已改变；未确认“dup_tol=0 必保原输入”的合同。实际信息损失已证，需所有者明确是否仍接受该模型，非原始数学内核错算。|
|二维G0距离只看浮点根|内部 ev_cover 删除真最近平方1的两标签，保留次近 `(1+2^-60)^2`，tol=atol=0仍绿；改差为2^-45即红。|漏网差落在 upward 1ULP候选搜索窗内，显示distance正确舍入仍为1；未证整个完备门／静态冗余同时绿，也未证该API承诺精确最近标签。不能写显著距离错误major。|
|round(float,ndigits)|静态允许某些 round 路径，次正规显式小数 round 后norm可0。|调用方显式 round 是否定义新模型尚未确认，缺具体原生产错误输入。|
|二维in_cone零方向|`in_cone(((1,0),(0,1)),(0,0))=-1`，数学闭锥原点应在边界。|需确认该有向锥API非零方向前置条件，未发现正常生产非零流程错误。|
|3D首入更早区间覆盖|有raw候选时自检核最早surface event和紧邻前区间，未逐事件证明全部更早区间。|尚无有效输入漏早期孤立碰撞却后续静默成功的反例；96凹prism／48非单调逃逸未找到。只是搜索方向。|

[reader 独立复现](file:///D:/eab-wt/g6m/review/repro/root_reader_feature_loss.py) · [风险输出](file:///D:/eab-wt/g6m/review/evidence/root_reader_risk.json) · [G0 subULP探索](file:///D:/eab-wt/g6m/review/geometry/g0_subulp_probe.json)。这些是保留线索，不算 critical／major 数量，也不等于宣称已证明安全。

## 8. 完整性批评：本轮没有做到什么

1. **不是全仓每行数学形式证明。** 37个 src Python模块被纳入检索／diff／测试，但源码深读聚焦生产几何、construction／predicate、LP／limit／margin及静态新机制。`__init__.py` 导出、全 `readers/bdda_df.py` 和 `readers/bdda3d.py` 旧解析分支、M4／G1–G5所有编排工具没有逐行重新证明；读到改动、现行测试和合同不等于全旧路径精读。geometry团队实际阅读／未读清单见分报告。主审额外全文读 contact_record、tf_probe、bdda_geom和bdda2d adapter。
2. **声明清单不是逐条有牙审验。** 67声称行／116同名迁移函数只作全量检索与重点核读；没有逐条为所有 ✔ 或每个旧断言构造单独源码变异。已确认 G6M-02 恰说明“断言保留或全绿”不足；不能把未发现另外问题等同覆盖完毕。
3. **第五轮50条仅30条实跑。** 未重放01–06、08、10、12–19、32–33、35、46。部分属于来源／文档／删除阈值类别，但未跑就是未覆盖，不以此宣布50条全关。
4. **理论00非全文／原论文未重新求证。** 全读01／03／07；00重点核定义、§3.3、§4.6及相关定位，未阅读全文历史／应用／全部文献尾注；不把本地综述引文当本轮重开论文验证的事实。正本提到付费原文未核的内容继续未核。
5. **几何有限族而非任意凹壳证明。** exact determinants随机、boxes／tetra／scanline prisms／nested shells／断开组件压力均有限；未穷尽任意非流形、自交、洞面片、极多特征、全部旋转下的构造可分辨性。对合法输入也仍可能有未覆盖极端组合。
6. **缓存和oracle毒化有限动态路径。** 清cache＋281函数毒化证明运行的8期望路径不调用这些函数，不证明所有分支、类协议、高阶别名都静态零依赖。120缓存改内容／返回别名格不是每个缓存完整状态机证明。
7. **2365遗留站点不逐项消化。** 它们的未证明性已明示，本轮没有给每站点安全证明；也不以未证明数量冒充发现。R12新门252格仍不能保障任意Python高阶／类协议，G6M-01证明有具体边界漏洞。
8. **数值对拍的真值模型有边界。** LP基穷举仅m≤3/n≤5随机压力、确定contact闭式族和指定自检注入；未穷举大LP退化、pivot预算、全部对偶面／物理接触配置，不把小规模对拍当工程验证。判定精确≠浮点构造理想几何不变。
9. **审查脚本也会出错。** 保留首次 basetemp setup错误、非法随机ring生成、review oracle对`-0.0`符号检查的修正记录；复跑后不计生产发现。PowerShell重定向生成的UTF-16审查日志已按BOM无损转UTF-8，不修改原生产或原历史复现源字节。正式三个发现由主审亲复现，不以代理消息代替证据。

## 9. 被审树完整性与复跑交付

<!-- TRACKED_INTEGRITY_RESULT -->
**4051 个已跟踪文件逐字节 SHA-256 全部与审查前相同，tracked路径集不变、HEAD不变。** `git diff --name-only` 及 tracked status 空；含未跟踪的status仅 `?? review/`。[最终完整性核对](file:///D:/eab-wt/g6m/review/evidence/tracked_integrity_final.json)。
<!-- TRACKED_INTEGRITY_RESULT_END -->

无 git commit／checkout／reset／stash／worktree／branch 操作。所有源码变异发生在 `review/copies` 的审查副本；旧新入口 mutation均按原字节＋SHA恢复。没有写理论正本、姊妹源码或其他审查工作树。

关键文件：[机读正式发现](file:///D:/eab-wt/g6m/review/G6M_findings.json) · [完整交付清单](file:///D:/eab-wt/g6m/review/DELIVERY.md) · [基线SHA](file:///D:/eab-wt/g6m/review/evidence/tracked_baseline.json) · [全套原日志](file:///D:/eab-wt/g6m/review/logs/full_pytest.log)。非独占性能数值仅作运行证据。

G6M_DONE critical=0 major=1 minor=2
