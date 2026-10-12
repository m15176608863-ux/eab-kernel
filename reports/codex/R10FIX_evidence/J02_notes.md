# G6J-J02 分报告：闭集初态首入

## 结论与改动

- 修复 `src/eab/kernel3d/entrance3.py::first_entrance3`：先精确判 `initial`。`initial==1` 保留既有局部出口策略；`initial==0` 独立收集**精确零间隙且在有限源特征域内**的全部面型盖，按既有稳定枚举/退化合并返回 `kind=entrance, exact_t=0`，不再过滤运动法向符号；分离态仍用原射线候选/完整事件自检。
- 初态分支两个见证点均经统一 `scalar_rational` 作报告构造，避免同一点一侧为原 Fraction、另一侧为 float。构造值不参与判定。
- 新增 `tests/test_r10_initial_boundary.py`（最终 39 格）。旧测试未修改、删除、放松、skip/xfail 或缩网格。

## 修前红 → 修后绿

[修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J02_red.log) 最后一行：

```text
16 failed, 16 passed in 1.02s
```

复审 12 格的核心初态错误仍是 9 格：三组尺度/位姿各有切向零视窗、切向 1/16 视窗静默 `none`，背离 1/16 视窗抛 `RuntimeError`；进入方向核心 kind/time 为正确对照。新增面/边/点零窗有 6 个相同方向过滤失败。另一个红是微尺度加大坐标的见证点输出不一致：`Fraction(400000000000000001,4000000000) != 100000000.0`，不是另一个几何判定错误。

关键原断言与实出：

```text
assert got.kind == 'entrance', 'closed initial face boundary must not be discarded by motion'
E AssertionError: closed initial face boundary must not be discarded by motion
E assert 'none' == 'entrance'

RuntimeError: first_entrance3: no in-extent facet-cover candidate, yet the bodies touch at t = Fraction(0, 1); the candidate set missed an earlier entrance
```

根因：原代码只将拓扑内部单独分支；边界初态仍进入 `nd>=0` 跳过的“进入型盖”候选。闭集首入已在 t=0 发生，进入方向过滤不适用。`surface_events` 是变化事件划分，并非每个持续相触区间的初点清单，因此切向短窗的末端自检也不能补救。

[最终新门日志](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J02_green.log)：

```text
39 passed in 1.11s
```

[相关旧门定向回归](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J02_targeted.log)：

```text
318 passed in 31.03s
```

定向集合：`test_r10_initial_boundary`（当时 38 格）、`test_r8fix_initial_state3`、`test_entrance3_exact`、`test_entrance3`、`test_entrance3_concave`、`test_kernel2d_entrance`、`test_kernel2d_entrance_e3`、`test_interlock_exact`。最后新增非零 x0 门另随最终 39 格验证。

## 变异牙：生产函数内部，不伪造产物

1. `test_initial_boundary_gate_kills_removal_inside_first_entrance`：通过 `inspect.getsource`/`exec` 仅把生产函数的 `if initial == 0:` 改成 `if False:`，进入真实旧候选路径。切向 1/16 格由 `closed initial face boundary must not be discarded by motion` 断言报红，实际 `none != entrance`。不是被偶然标签选择或脆浮点断言杀死。
2. `test_initial_boundary_gate_kills_removal_of_finite_domain_filter`：仅将生产函数内部 `if c.in_extent and dot(n,p)==0` 改为零间隙检查，令域外零支撑面标签进入真实输出。独立原始坐标区间断言 `initial tied label left its finite source domain` 红，证据 `5/4 <= 1` 不成立。

具体断言随 `-s` 已保存在最终绿日志；两个变异均期待并捕获其看护断言，不修改生产文件。

## 同类扫描与客观覆盖

| API/路径 | 阅读结论与实际门 | 结果 |
|---|---|---|
| 3D `first_entrance3` 普通面/边/点边界 | 原 12 格加面/边/点乘三方向零窗；非对称中心；缩放 1e-9/1/1e8、平移 1e8、精确 3/5-4/5 旋转；非零 x0 | 修复后全绿 |
| 3D 凹体普通外边界 | L 截面挤出体与箱体顶面接触，切向/背离/进入零窗 | 新 3 格全绿 |
| 3D 紧配内缝/出口 | 读取 `entrance_topology`；既有 R8 全文件复跑，含窄外部室/阈值/内缝源内变异 | int(E) 仍 exit，不误降为边界 |
| 2D 凸/凹 `first_entrance` | 凸裁剪主动面包含初态；凹 `_feature_times` 共线在段内显式加 0；独立矩形/L 截面乘四运动/视窗 | 新 8 格全绿，无需改 |
| 2D/3D `shortest_exit` | 本身是显式局部出口操作，不自动替代闭集首入；边界调用返回 exit 且局部 gap=0 | 新 11 格内断言全绿 |
| 2D/3D `first_entrance_brute` | 有初始 `state(0)>=0 -> 0`；共用生产谓词，仅抽样佐证 | 初态控制全绿，不作主 oracle |
| `margin.inflated_membership(delta=0)` | 零显式窗调用拓扑 E 分类，普通边界 0，紧配内缝 1 | 三尺度/姿态默认与 atol=0 控制绿；R8 内缝门绿 |
| `interlock._exact_escape_cached` 与 covers/brute | 初态物理 `state!=1` 即高度 0；求首次不穿透，不是首次离开闭集 E | 三尺度/姿态、None/0 contact_window、hi=0 brute 均高度 0、state=0、空先前区间证书 |
| `escape_candidates`/冻结逃逸 | 候选仅名义报告；冻结路径是固定活动面的解析零间隙高度，不重新择支 | 无同类方向门，未改 |
| `covers.first_entrance_for_vertex` | 无方向的静态局部选择器，已明确不是一般沿路径首入 | 不扩大合同 |

独立 oracle 只用原始 Fraction 笛卡尔区间交、显式可逆仿射变换和盒/L 并集描述；未调用生产重叠、三角化、法锥、盖或事件原语作真值。有限标签验证采用原始源特征的轴向闭区间交。

## 复跑与边界

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -s tests/test_r10_initial_boundary.py --basetemp=reports/codex/R10FIX_evidence/tmp/j02
```

- 仅修改本树 `entrance3.py`、新增测试和报告/日志；无 git 写操作，无姊妹树操作。
- `git diff --check -- src/eab/kernel3d/entrance3.py tests/test_r10_initial_boundary.py` 通过。读取和写入采用 `newline=''`，保留其余内容，仅新改行用 LF。
- 未跑全套、未改 README/canon/外部正本，交主执行者集中完成。文档建议：普通 ∂E 初态 t*=0；拓扑内部含紧配缝仍局部 exit；互锁零高度指物理非穿透，不声称离开 E。
- 不宣称任意凹体局部 facet 完备、全域 G6 已过或里程碑退出。当前无 J02 未修项；全套和新鲜只读独立复审仍由上层交付。
