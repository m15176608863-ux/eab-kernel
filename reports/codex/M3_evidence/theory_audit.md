# WO-M3：独立理论、语义与文献审计

日期：2026-10-14（开始读取时为 2026-10-13）。本文件是实施前审计及证明草稿，不是 G6 退出结论；尚不评价最后实现和全套门。只读核查了工单指定的计划 M3/诚实条款、canon_map 第四节 (d)/附录/完备性条目、正本 00 §3.2–3.3/§4、01 全文、03 K1–K5，以及现有二维/三维谓词、首入、逃逸的相关路径。

## 1. 最重要的结论

1. `E = ∪ Cij`、`O = ∪ int(Cij)` 成立，但必须写出条件：**有限个全维闭凸片精确覆盖原实体**，`Cij = Bj + (−Ai)`。不能把后一式误换成 `O = int(∪ Cij)`。
2. 当前仓库已经刻意保留两种三态，紧配位形得到不同标签不是新发现的实现 bug：实体相交三态基于 `O`；入口块拓扑三态基于 `int E`。M3 必须并存命名，不能静默统一为一种数值。
3. 裁剪必须按邻接全维胞的 **E 内/外占据** 判断。仅保留“盖内部探针相触”的片段错误，会保留位于 `int E \ O` 的紧配内缝。
4. 强完备需要保留非严格有效的退化盖；只枚举 `strict=True` 的盖在平行贴边处就会漏边界。
5. 当前三维 `polyhedra_overlap(..., tol=0)` 对应 `O` 贯入合同。正 `tol` 是额外的分离侧距离报告带，不能拿来做零容差新构造的 oracle。
6. 新二维凸分解如共用 `geom.triangulate`，则 `polygons_overlap_exact` 与新构造不独立。主 oracle 应用 `g0_oracle`；三维如共享 `exact_geom.triangulate`、点内或凸 SAT，也必须降级为佐证或补独立 oracle。

## 2. 对象与三态：已有代码实际合同

定义紧正则闭实体 `A=closure(int A)`、`B=closure(int B)`，只平移：

- `E={t:(A+t)∩B≠∅}=B+(−A)`，紧且闭；
- `O={t:int(A+t)∩int(B)≠∅}=int B+(−int A)`，开；
- 实体相触集合为 `E\O`，不是一般凹块的 `∂E`。

| 路径 | 实际合同 |
|---|---|
| `kernel2d.exact.polygons_overlap_exact` | `−1: t∉E`；`0: t∈E\O`；`1: t∈O`。逐耳切三角形的严格/闭 SAT。 |
| `kernel2d.g0_oracle.overlap` | 同上；简单 CCW 环，独立整数绕数、边交/共线同侧证书。 |
| `kernel2d.exact.entrance_membership_exact` | `−1: t∉E`；`0: t∈∂E`；`1: t∈int E`。遇实体相触后，检查包含该点的凸片切锥是否覆盖所有方向。 |
| `kernel2d.g0_oracle.boundary_has_exterior` | 相触处检查局部安排的外部扇区；紧配内缝没有外部扇区。 |
| `kernel2d.entrance.first_entrance` | 初态使用入口块拓扑；初态在 `int E` 时现行是局部出口，包含紧配内缝。 |
| `kernel3d.geom3.polyhedra_overlap` / `exact_geom.surface_overlap` | `tol=0` 对应实体 `O` 三态；输入须是合法向外定向嵌入闭表面，不静默凸化。 |
| `kernel3d.interlock` 原逃逸裁决 | 求沿给定方向第一个非贯入状态，依据 `O`，不是离开闭 `E` 的全局出口。 |

`E=closure(O)` 也成立：每个 `b−a` 可由内点 `bn−an` 逼近；反向包含由 `E` 闭而 `O⊂E` 得到。因此 `E` 正则闭，但 `O` 可以漏掉 `int E` 内的低维缝。二维标记结构的相触标签可能出现在 0/1 维胞中，不能只保存 E 的外边界和洞。

### 2.1 最小可读紧配反例与本轮实跑

取 CCW 环：

```python
A = ((-1,0),(1,0),(1,1),(-1,1))
B = ((-2,-1),(2,-1),(2,3),(1,3),(1,0),(-1,0),(-1,3),(-2,3))
```

`B` 为 U 槽，`A` 是宽度恰好等于槽宽的销。B 可精确分成三个闭矩形：底 `[-2,2]×[-1,0]`，左 `[-2,-1]×[0,3]`，右 `[1,2]×[0,3]`。它们与 `−A` 的 Minkowski 和为：

```text
C_bottom = [-3,3] × [-2,0]
C_left   = [-3,0] × [-1,3]
C_right  = [0,3]  × [-1,3]
E = [-3,3] × [-2,3]
O = int(C_bottom) ∪ int(C_left) ∪ int(C_right)
int(E) \ O = {0} × [0,3)
```

本轮 `PYTHONDONTWRITEBYTECODE=1; PYTHONPATH=src; python -X utf8 -` 执行原函数，逐点结果：

| 平移 t | polygons_overlap_exact | g0_oracle.overlap | entrance_membership_exact | 相触点有外部扇区 |
|---|---:|---:|---:|---|
| `(0,1)` | 0 | 0 | 1 | False |
| `(1/8,1)` | 1 | 1 | 1 | 不适用 |
| `(-1/8,1)` | 1 | 1 | 1 | 不适用 |
| `(0,9/8)` | 0 | 0 | 1 | False |
| `(0,7/8)` | 0 | 0 | 1 | False |
| `(0,3)` | 0 | 0 | 0 | True |
| `(0,25/8)` | −1 | −1 | −1 | 不适用 |

这是 R8FIX 已处理类别的新简洁实例，不应写成 M3 才发现代码语义矛盾。对 `t=(1/8,1)`，停止实体贯入的最小距离 `rho=1/8`；严格分离闭实体的距离下确界 `PD_closed=2`。达到上边界 `(1/8,3)` 时仍相触，严格分离的距离下确界不达到；这个差异不是数值容差。

### 2.2 正本的限定

01 引言明确 A、B 紧凸，提及“凹块情形单独说明”但正文未补。其命题 1 注 3 的 `int E⇔重叠` 与 `∂E⇔相触` 在全维凸情形成立，不可原样外推。命题 3(ii) 明确定义闭集严格分离的下确界，故推广凹块时仍对应 `PD_closed=d(t,∂E)`，不是 `rho`。现有 03 的 K1/K2/K3/K5 可映射到构造与语义标签；K4 力学互补不由 M3 几何门证明。

## 3. 有限凸片并构造：自包含证明

### T1. E 与 O 的两个并公式（已给证明）

条件：`A=∪i Ai`、`B=∪j Bj`，片数有限，每片非空、全维、紧凸；不要求片内部两两不交，但应能精确验证覆盖。令 `Cij=Bj−Ai`。

`E=∪ij Cij` 由存在量词对有限并分配立即得到。

先证对全维凸体 C、D，`int(C+D)=int C+int D`：右侧开且包含于 C+D，所以在其内部。反向取 `z∈int(C+D)` 与 `c0∈int C,d0∈int D`。足够小的 `λ>0` 使 `y=(z−λ(c0+d0))/(1−λ)∈C+D`。写 `y=c+d`，则 `z=((1−λ)c+λc0)+((1−λ)d+λd0)`；两个凸组合均在对应内部。这证明等式，不借未核文献。

因此 `t∈int Cij` 当且仅当 `int(Ai+t)∩int Bj≠∅`，从而属于 O。反向若 `t∈O`，则 `U=int(A+t)∩int B` 是非空开集。有限个片边界的并没有内部，U 中可取一个点避开所有 `∂(Ai+t)` 与 `∂Bj`；该点由两组覆盖分别落在某个片中，避开边界即在两个片的内部，于是 `t∈int Cij`。结论 `O=∪ij int Cij`。

正则闭条件本身不产生有限凸分解；本定理使用的是多边形/多面体的有限凸分解。不能对无限片覆盖直接援引“有限边界并无内部”。

### T2. 精确 BSP 分解的充分条件（证明草稿，须对实现核验）

三维可将包围盒依次按所有输入面的支撑平面切分。每个保留全维胞是有理半空间交，凸；全体面平面安排使每个开胞避开输入边界，因此同一开胞内实体内/外标签恒定。所有顶点平均是该全维有界胞的严格内点：每个真 facet 至少有一个顶点严格在内，故全点平均严格满足该 facet。用不调用实体两两相交的精确射线奇偶分类中心，保留实体内部胞的闭包；正则闭性保证其并恢复原实体。该算法允许由平面交形成 Steiner 点，不以“原顶点无 Steiner 四面体剖分”存在为前提，因此不会被 Schönhardt 例原则性阻断。

要审计的缺口：输入非平面多边形面的既有三角化合同、空腔定向、共面面拆分、严格内点的独立核验、射线撞棱的确定性处理、全部胞的覆盖证书。只实现星核锥化而失败时抛错不等于一般凹体 BSP 已完成。

## 4. 盖裁剪与强完备：精确陈述

### T3. 条件式裁剪定理（已给证明；原局部盖弱完备另需核验）

设 E 为有限全维闭凸多面体并，候选 (d−1) 维多面片 L 有限，且 `∂E⊂∪L`。以片与所有凸片边界的交集共同加细 L。保留每个相对内部小片，当且仅当其两个邻接全维开胞恰一侧属于 E、另一侧不属于 E。所得暴露开片之并的闭包恰为 `∂E`。

证明：标签不同的一侧提供任意近的外点，另一侧提供内点，小片在闭 E 内，故在边界；取闭包仍在闭边界。反向，有限正则闭多面体并的边界是纯余维一的多面复形；边界每个余维一片的相对内部只有一侧被 E 占据、另一侧不被占据。弱覆盖保证它被 L 覆盖，故被保留；更低维边界均是这些片的极限。无需一般位置假设。重合共面、共线和交点须先加细，不能靠浮点小量选侧。

二维更直接：对 E 的全部凸片边界段作完整线段安排；每条原子开段中点与两侧的成员标签恒定；分离/非分离两侧异号即 ∂E 段。端点独立分类，因为不暴露开段的闭端点仍可能属于真边界。输出时用闭段并自动包含这些端点。

### 原有 VE/EV 与 reduced convolution 的关系

对 CCW A、B，反射 `−A` 保持二维方向。VE 候选的平移段是 `[b_j−a_i,b_{j+1}−a_i]`；EV 为 `[b_j−a_i,b_j−a_{i+1}]`。凸顶点的局部支撑方向条件，等价于对应边的有向方向落在反射顶点的相邻边转角扇区；这就是去掉凹顶点贡献后的 edge+vertex reduced-convolution 候选条件。严格局部支撑对应扇区内部；平行/平直退化需要扇区闭边界，标签可重复。

**不是无条件宣称两套实现逐标签相等**：当前实现的平直顶点、索引别名、FF 合并及枚举方向还须单独门对齐。上述几何等价是本审计的证明草稿。全维 simple-polygon 的真边界一般点必由原边-顶接触或平行边接触产生；后者可由非严格 VE/EV 覆盖。VV 事件是有限个点，可由暴露段闭包补足。因此只做严格有效筛选不能支持一般退化强完备。

00 §3.3 的“裁剪”本轮只能称为**本仓库给出的一种严格化**。00 自己将石根华编号命题的对应标为未核实，不能提升为已核原定理；00 还提到圆柱面/裕度语境，不宜直接等同本单只平移的多面体裁剪全部细节。

## 5. 距离、出口、首入与开区间端点

- 任意紧实体均有 `d(t,E)=inf(a,b)||t−(b−a)||=d(A+t,B)`，不需要凸性。
- `PD_closed(t)=inf{||h||:t+h∉E}`；t 在 `int E` 时等于到 `∂E` 距离。边界点位移是距离下确界证书，不是已经严格分离的证书。
- `rho(t)=min{||h||:t+h∉O}`；O 开而有界，补集闭非空，最小值达到；t∈O 时等于到 `∂O` 距离，t∉O 时为 0。
- 初态在 E 外，闭 E 首触可由射线和所有 Cij 的闭区间相交取最小下端点给出；无需相交谓词。切触保留闭端点。初态在 `int E` 的“首入”应另按 API 既有出口合同处理。
- 逃逸非贯入高度用射线与所有 `int Cij` 的**开区间**并。区间只在严格交叠时合并；`(a,b)` 与 `(b,c)` 不能合并，b 可能是第一个恰相触、非贯入根。若别的开区间跨过 b，b 才仍贯入。平行方向某个约束恒等为 0 时，这片的开区间为空，但闭区间可非空。
- 精确双侧探针：沿法向求与所有相关支撑线/平面的正事件参数，以最近正事件的一半取点；不存在正事件时可取任意显式有理参数。不能用固定 epsilon。顶点需要所有角扇区/三维局部锥检查，而非单个法向两点。

## 6. oracle 独立性的读取证据

`src/eab/kernel2d/g0_oracle.py` 的 import 清单：

```text
from eab.oracle_construction import sqrt_exact, scalar_exact
from fractions import Fraction as F
from math import lcm
```

其几何原语为自身 `inside` 整数绕数、`turn`、`on_segment`、相交与有理线事件；不 import 盖、卷积、全局构造。`oracle_construction` 是显示数值出口，不是被测几何原语。用于 ∂E 确认时必须将 overlap=0 与独立 `boundary_has_exterior` 合用，不能只看 overlap=0。

当前生产 `polygons_overlap_exact` 动态 import `.geom.triangulate`。与新构造共用该耳切时，纵使 SAT 与 Minkowski 构造不同也违反纪律 A。三维同理，应把共享 import 图和辅助函数明确列入主报告，不能只宣称顶层函数名不同就独立。

## 7. 文献逐条核验状态

本节仅记录本轮实际读到的一手材料，不继承正本中的“亲核”标签，也不借未核原文证明 T1–T3。

| 文献 | 本轮状态 | 确切可用范围 |
|---|---|---|
| Guibas–Ramshaw–Stolfi, 1983, *A Kinetic Framework for Computational Geometry* | **未核原文**；作者 Stolfi 的出版目录题录已核 | 作者目录确认 FOCS 1983, pp.100–111；不能用作本单定理证明来源。[作者题录](https://www.ic.unicamp.br/~stolfi/EXPORT/bibliography/stolfi.html) |
| Kaul–O'Connor–Srinivasan, 1991, *Computing Minkowski Sums of Regular Polygons* | **未核完整原文**；官方会议 PDF 的搜索抽取首页已核，全文打开被 14.7MB 限制阻断 | 首页明确 regular/path-connected/bounded 输入与 0/1/2 胞分解；不能冒称核查其后算法或定理证明。[会议原稿](https://cccg.ca/proceedings/1991/paper19.pdf) |
| Wein, 2006, *Exact and Efficient Construction of Planar Minkowski Sums using the Convolution Method* | **已核原文**（同名 ACS 技术报告版本，14 页，§2/§3） | 明确 edge+vertex 卷积条件、完整循环的绕数、DCEL 安排遍历与非零绕数区域。注意论文低维 tight-passage 讨论的集合标记，不能据其“边界”一词将本单闭 E 的内缝抹掉。[原文 PDF](https://www.cs.jhu.edu/~misha/Spring20/Wein06.pdf) |
| Behar–Lien, 2011, *Fast and robust 2D Minkowski sum using reduced convolution* | **未核原文**；作者 CV 的题录已核 | 2010 同作者技术报告的摘要可读取，但正文网址现 404，不能当 2011 定稿已核。[作者 CV](https://cs.gmu.edu/~jmlien/lib/exe/fetch.php?media=lien-cv.pdf&rev=1468804835)、[2010 报告原链接](https://cs.gmu.edu/media/techreports/GMU-CS-TR-2010-11.pdf) |
| Hachenberger, 2009, *Exact Minkowski sums of polyhedra and exact and efficient decomposition of polyhedra in convex pieces*, Algorithmica 55,329–345 | **未核论文完整原文**；作者机构的题录/摘要已核 | 机构页确认凸分解、凸片和、并的路线；PDF fetch 失败，不能冒称证明已核。[作者机构页](https://research.tue.nl/en/publications/exact-minkowski-sums-of-polyhedra-and-exact-and-efficient-decompo-2/) |
| Hachenberger, CGAL *3D Minkowski Sum of Polyhedra* 官方手册 | **已核原文**（Decomposition Method / Features and Restrictions） | 分解+并、每维胞选择标记、tight passage 需保留低维排除；明确开放和闭合输入的区别。本单不引入 CGAL 依赖。[官方手册](https://doc.cgal.org/latest/Minkowski_sum_3/index.html) |

选择凸片并而不先实现完整卷积循环的理由：T1 可自证并天然保留 O 与 E 两份信息；闭/开 H 区间可直接服务逃逸；纯标准库可实现。代价是片数及安排规模，不能把卷积文献中的较优复杂度套在简单凸分解实现上。仅用 reduced-convolution 候选还不能给每胞标签；如靠暴力 overlap 清理，违反本单目标。

## 8. Xbloc：找到公开尺寸，但尚未完成可审计几何转写

已核一手来源：Bakker、Klabbers、Reedijk，*Introduction of the Xbloc Breakwater Armour Unit*，Terra et Aqua 94，2004-03，**Figure 7（PDF 第 5 页、刊页 7）**给出 D、D/3 与圆角 `r=D/19`。[作者原文 PDF](https://www.iadc-dredging.com/wp-content/uploads/2017/03/article-introduction-of-the-xbloc-breakwater-armour-unit-94-01.pdf)

厂商官方 [下载页](https://xbloc.com/en/downloads) 另提供概念设计手册；检索所得 [2023 手册](https://www.xbloc.com/sites/bamc/files/2022-11/Guidelines%202023.pdf) 提供主尺寸表，但本轮网页工具未成功完整读取该大 PDF。

因此不能写“没有可靠公开尺寸”。目前正确状态是：**已定位可靠尺寸图，尚未把三维拓扑与圆角离散策略转写成可审计有理多面体，未做 Xbloc 零失配门**。有圆角的实际实体不属于精确多面体域；若未来将圆角省略或有理网格化，必须明确“根据 Figure 7 构造的多面体近似”，附偏差与转换合同，不能用猜测的三正交柱体冒称真实 Xbloc。

## 9. 对实施前设计的修正建议

1. 第一次读取 `docs/m3_global_entrance_design.md` 时中文实际变成问号，已通知主代理。需要修复 UTF-8 写入并建可读性检查，不能将乱码文件作为理论先行证据。
2. 应在设计中独立列出 `closure(O)=E`，以及 `int E\O` 可非空；说明只有 E 边界的标准 polygon-with-holes 不能完整表达实体三态。
3. T2 必须明确“相对内部被暴露”的判定；未暴露闭段的端点可在 ∂E，所以端点需独立标签。
4. 强完备应先以凸片边界候选证明；要升级为“旧有效局部盖裁剪强完备”，还须一条带退化的覆盖/标签门或完整证明。旧距离/出口随机门不自动等于普遍弱完备定理。
5. `PD_closed` 与 `rho` 用各自名称；不允许将 O 的区间末端叫成离开 E 的证明。
6. 当前语义双合同是已有设计，不记成新 bug；新发现可以是文档泛化风险和最小反例。

后续独立审查应核查上述数学条件实际进入实现/门，而不是仅有文档。

## 10. 实施后的独立定向审查（不等于六路 G6）

### 10.1 理论合同门

新增 `tests/test_m3_theory.py`：24 个测试，命令
`PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests/test_m3_theory.py`，末行原样：

```text
24 passed in 0.12s
```

其中 U 槽 7 个状态 × 3 个精确尺度/大平移/90°旋转格，用独立 Cartesian 区间同时看护实体 O 三态与入口块拓扑三态；另检查闭/开凸片并的区别、rho/PD_closed 的闭式区别与中文设计文档 UTF-8。主代理后续已修复设计编码并明确 `E=closure(O)`。

### 10.2 三维首版代码与额外扭转体

读取 `kernel3d/global_entrance.py` 后，闭/开 SAT slab、严格开区间合并、BSP 凸胞裁剪、有理中心严格内点的路径未发现已复现错误。已有新门本审计独立运行的末行：

```text
20 passed in 7.16s
```

额外测试有理扭转三角棱柱：底三角 `(0,0),(4,0),(1,3)`，中心 `(5/3,1)`，顶三角相对中心旋转矩阵 `[[15/17,-8/17],[8/17,15/17]]`，底顶 z 分别 0、2；侧面固定拆为 `(i,i+1,top(i+1))` 与 `(i,top(i+1),top(i))`。另一实体为半宽 `(1/3,1/4,1/5)` 的盒。`Random(831)` 生成 180 个三轴 `randrange(-12,30)/6` 平移：全局三态与现行精确表面 oracle **180/180 相等**；8 个凸片的每个中心由原表面点内 oracle 核为严格内点。总耗时 0.2424 s。该数据只证明这个扭转体，未证明它具有 Schönhardt 的无原顶点四面体剖分性质，不命名为已验证 Schönhardt。

首版限制已通知主代理：全凸片顶点/棱/面/两侧的穷尽探针仅在 L 家族；TIA、零配、空腔、随机凹块尚不是每个家族的完整剖分探针。对原始网格只查局部边 incidence 和正定向体积，不完整认证任意自交，`embedded` 仍是输入前提。不得把此审查读成所有非法输入都已响亮拒收。后续代理可能补门，最终数字须以冻结证据为准。

### 10.3 二维带洞剖分额外加密

本审计独立使用 `g0_oracle.overlap` 查询每个 0/1/2 维胞的 sample；每个 face 另查询其顶点平均中心与每个顶点的中点。这些点真正进入生产剖分的整个相对内部，而不只是复制一个样本。结果：

| 家族 | 顶点/棱/面 | Euler V−E+F | 独立实体探针 | 失配 | 各 face 绝对面积和 = bbox 面积 |
|---|---|---:|---:|---:|---|
| thin_L | 71/140/70 | 1 | 535 | 0 | 精确相等 |
| slot_wedge | 105/208/104 | 1 | 803 | 0 | 精确相等 |
| interlock_section | 149/303/155 | 1 | 1171 | 0 | 精确相等 |
| tight_fit | 106/218/113 | 1 | 839 | 0 | 精确相等 |
| pocket_hole | 410/837/428 | 1 | 3270 | 0 | 精确相等 |
| collinear | 268/539/272 | 1 | 2096 | 0 | 精确相等 |

合计 **8714/8714**；本轮加密运行总耗时约 7.53 s。二维 local/global boundary 的完整区间覆盖门与射线 oracle 门已读取；目前未发现带洞安排或盖裁剪算法的具体错误。这是额外交互审计，不冒称该加密脚本已经单独冻结为可重跑命令文件；若作最终退出证据，应由主证据脚本纳入。

### 10.4 实际发现：多最近点的单值出口见证不可能普遍旋转协变

首版 `_nearest_boundary` 采用 `min((square, point))`，在最优值并列时选择全局坐标字典序点。精确复现：

```python
A = ((-1,-1),(1,-1),(1,1),(-1,1))
# A == B, x == (0,0)
g.shortest_exit((0,0))  # squared=4, exact_point=(-2,0)
# 将 A、B 的每个点旋转 90 度以后：
h.shortest_exit((0,0))  # squared=4, exact_point仍为(-2,0)
# 原见证的旋转却是 (0,-2)。
```

这不是距离值错误，而是未限定的**输出见证不变性合同**失败。完全对称输入下，没有额外结构的单点选择一般不能与全部对称旋转交换。修法不应寻找另一种“万能”排序，而应返回全部并列最优点（本多边形边界距离的有限最优集合）、对该集合要求协变，同时保留明确声明不保证旋转协变的字典序代表；唯一最近点时代表当然协变。已把精确反例发给主代理和二维代理；主代理决定追加并列最优点集合。

**修复复核**：现实现 `Distance2.tied_exact_points` 收集并去重全部达到最小平方距离的线段投影；`exact_point` 仍取字典序代表，注释明确其在并列时不保证旋转协变。新门 `test_shortest_exit_tied_minimizer_set_not_lex_representative_is_covariant` 以本例核验四个最优点的集合协变，并特意核验字典序单点不协变。因此该发现已修复为明确的集值合同；不能再将其记成未修复 major，也不能删去单点代表的限制。

本审计读取修复实现及门后，独立运行二维全局门、理论合同门、主代理新加的独立闭式出口 oracle 门（L 并形六边，Cartesian clamp，无生产几何原语）：

```text
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_m3_global2d.py tests/test_m3_theory.py tests/test_m3_exit_oracle.py
75 passed in 7.51s
```

以上定向审查不替代六路 G6。整体理论合同仍以有限满维凸分解、有效嵌入的多面体输入与显式选择的 O/E 语义为前提；旧有效局部盖的普遍弱覆盖不能仅由有限样本升级为无条件定理，三维显式边界裁剪/强完备未在此审查中完成。
