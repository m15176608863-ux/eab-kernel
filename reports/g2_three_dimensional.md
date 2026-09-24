# G2：三维接触枚举的第一次 legacy 对账（2026-09-20）

二维有对账（bb52 legacy 53/53），**三维到今天为止只有 G0 自证、一次都没跟任何既有实现比过**。
这是整套门里唯一一道从没跑过的。今天跑了。

## 结论先行

| 对象 | 结果 |
|---|---|
| **bdda3d**（三例，几何齐全） | **通过**。legacy 4 条 / 内核 4 条，两个方向零差异，间隙与法向逐条吻合 |
| **tf.cpp**（3DDA） | **跑不了**。探针与 stage 文件都不带块体顶点坐标，无法独立枚举 |

> **限定（2026-09-24）："两个方向零差异"只对 np ↔ VF/FV 这一类成立。** 09-20 的门只拿 legacy 的 `np` 入口去对内核的
> VF/FV 盖；legacy 的其他入口（含 `ee`）进一个"不支持"桶、内核的 EE/VE3/EV3/VV3 盖进 detail 桶，**都不参与判定**——
> 伪造一条 `ee` 入口或多注入一个内核 EE 盖，门照样绿（审查 C17）。所以当时的"零差异"是在一种几何、一类接触上的零差异，
> 而且 legacy 侧的三个 JSON 当时没有哈希看护（审查盲区 3）。现在的门见下文"对账口径"。
> （本文"审查 Cn"用 `reports/audit_20260921.json` 里 `confirmed[n]` 的编号；"里程碑 M2"指 `docs/plan_20260921.md` 的里程碑。）

## 通过的那一半：bdda3d

`cb2_locked` / `cb2_sliding` / `cb_bond` 三个算例：上块（2×2×1）坐落下块（4×4×1）顶面，零间隙。

- legacy 给出 **4 条 `np` 入口**（上块四个底角 × 下块顶面）
- 盖内核给出 **4 个 VF 盖**，`legacy_only = []`，`mine_only = []`
- 间隙 0（< 1e-12）、法向 (0,0,1)、`strict = False`

最后那条要解释一下：`strict = False` **不是缺陷**，是命题 4 的面-面退化情形——轴对齐使
分离方向恰好落在顶点法锥的**边界**上。DDA 与 bdda3d 正是用这 4 个 n-p 入口表达一个面-面接触。

### 对账口径

legacy 的 `np` 入口用**顶点三元组**指代一个平面，而且同一个平面会被不同三元组表示——
cb2 里 (4,7,6) 与 (4,6,5) 并存。所以匹配必须把三元组归约到"它所在的几何面"，
不能比顶点号。这正是 AGENTS.md 要求的"守同构、不守逐字节"。

**门现在的样子（2026-09-24 起，`tools/g2_bdda3d.py`）。** 每个块对要同时满足四条，否则红：

1. **对账窗口 `G2_WINDOW = 1e-6`**（长度单位）内，np ↔ VF/FV 两个方向零差异（`legacy_only`、`mine_only` 都空）。
   窗口原来是 1.0。取 1e-6 的理由已钉成门：三份夹具里 legacy 的 np 间隙全部恰为 0，而离得最近的"非面接触"特征对
   （上块底角到下块顶棱）是 1.0——窗口装得下全部 legacy、又远小于 1.0
   （`test_g2_window_contains_every_legacy_gap_and_nothing_else`，断言 legacy 间隙 ≤ 窗口、非面特征距离 = 1.0、窗口 ≤ 1e-3 × 1.0）。
2. **`violations` 为空**：legacy 有门不认识的入口类（目前 np 以外全部，**包括 ee**）即红；窗口内出现 VF/FV 以外的内核盖、
   或两个盖归到同一个键，也红。不再有静默的"不支持"桶
   （`test_g2_gate_red_on_fabricated_ee_legacy_entrance`、`test_g2_gate_red_on_extra_kernel_ee_cover`）。
3. **VF/FV 带必须空**：`G2_WINDOW < |gap| ≤ G2_BAND = 1.0` 的 VF/FV 盖一律进 `band`，非空即红——这就是旧窗口 1.0 时代那颗牙，
   窗口收窄后单独保留。带必须空的理由是几何的：一个只用内联算术的长方体 oracle 表明，|gap| ≤ 1.0 内只有 4 个零间隙坐落，
   下一个 VF/FV 在 2.0（`test_g2_band_is_geometrically_empty`）。带只收 VF/FV：gap 恰为 1.0 的 VE3/EV3/VV3 是合法的，不触发
   （`test_g2_band_ignores_low_dim_covers_at_gap_one`）。**带宽是夹具几何的量**，几何缩放时要按同一比例传 `band`。
4. **枚举窗口必须伸到带宽**（`enumerated_window ≥ band`）。这一条是第二轮复核逼出来的，见下。

**C17 的第二轮复核判"无牙"，已补（6f157ac；合并后直接进 main，未经独立复核者复核）。** 第一轮修好后，g4 组合并（b1bbd27）时的第二轮复核发现带内检测只在"枚举完再追加的假盖"上测过：
把 `compare()` 里枚举那一行的窗口从 `max(window, band)` 改回 `window`，真实的带内内核盖就根本枚举不出来，而全套测试照绿。
现在加了一颗穿过枚举器的牙：让内核的顶点法锥判据恒返回"边界"（一个真实的内核缺陷），它会在 |gap| = 1.0 处产出假 VF 盖，
门必须红（`test_g2_band_catches_a_real_kernel_defect_through_enumeration`，三个夹具各一例）。
我用复核者的那个变异复跑过：枚举窗口改回 `window` 后，这三例红、`tests/test_g2_bdda3d.py` 其余 55 例照绿（未变异时 58 例全绿）。

## 跑这道门立刻逼出来的一个真问题：三角化会让盖过计数

夹具只给顶点，所以我用凸包重建几何——**凸包是三角化的**，4×4 的顶面被拆成两个三角形。
于是上块四个底角给出了 **6 个**有效盖：投影落在公共对角线上的两个角，各被数了两次。

这不是数值误差，是**枚举口径错了**：一个顶点对**同一个平面**只应该有一个盖，
盖数必须由几何决定，不能由网格划分决定。

所以顺手把共面归并做成了内核能力 `merge_coplanar`：按支撑平面分组 → 组内有向边相消
（内部边正反成对出现）→ 剩余边串成边界环，朝向自动正确。

| 输入 | 面数 | 体积 | 流形自检 |
|---|---|---|---|
| 四面体 | 4 → 4 | 0.1666666667 → 不变 | clean |
| 方块（四边形面） | 6 → 6 | 8.0 → 不变 | clean |
| 方块（凸包三角化） | 12 → **6** | 8.0 → 不变 | clean |
| 起伏互锁块 amp=0.25 | 28 → 10 | 2.0 → 不变 | clean |
| 同上 amp=0（退化成方块） | 28 → **6** | 2.0 → 不变 | clean |

归并后 cb2 的有效盖从 6 变成 **4**，与 legacy 一致。体积精确保持是归并的不变量，已钉成门。

**任何三角化输入（凸包、STL、多数网格导出）都需要先归并**，否则盖数随网格划分变化。
这条已固化为回归测试。

> **订正（2026-09-24）：上面"按支撑平面分组 → 边相消 → 串环"的写法有缺陷，而且"归并"的含义要说准。**
> - 只按平面分组、不看邻接时：两个共面面只在一个顶点相触（pinch）会让走环**死循环**；共面但不共棱的面（U 形棱柱两个端面）
>   被强行归并后报错（审查 C8）。现在**只归并共棱连通的共面面**（组内按共棱做并查集），不共棱的各自保留。
> - 归并出的面**可以是非凸的**——骨形块归并后的侧面就是凹十边形（上表"起伏互锁块 28 → 10"里就有）。因此所有
>   "点是否在面内"的判定都改走 `geom3.face_polygon_locate` 这一个实现（环绕数；`point_in_face_polygon` 是它的布尔包装），
>   不再用只对凸面正确的半平面核或扇形三角化（审查 C6/C7）。
> - 一组**共棱连通**的共面面若带洞、或其边界在某顶点自相接触（组内 pinch），Polyhedron 表示不了，**明确抛 `ValueError`**，不会挂死
>   （`test_pinch_inside_an_edge_connected_group_raises_clearly`、`test_hole_inside_an_edge_connected_group_raises_clearly`）；
>   只在顶点相触、不共棱的两片按第一条各自保留，不报错（`test_vertex_pinched_coplanar_faces_do_not_hang`：输出与输入逐面相同）。
>
> 依据：`tests/test_geom3_merge.py`（`test_vertex_pinched_coplanar_faces_do_not_hang`、`test_u_prism_prong_ends_stay_separate`、
> `test_pinch_inside_an_edge_connected_group_raises_clearly`、`test_hole_inside_an_edge_connected_group_raises_clearly`）、
> `tests/test_geom3_face_polygon.py::test_probe_in_front_of_merged_concave_side_face_has_a_face_cover`（归并后最大面 10 个顶点、面前探针恰得 4 个 VF 盖）、
> `::test_all_five_call_sites_route_through_the_single_helper`。

## 跑不了的那一半：tf.cpp，以及它暴露的东西

探针 `retry_contact_pair_probe.tsv` 有接触点、法向、gap、contact_type；
`contact_pair_stage.tsv` 有逐块对的 nn/ne/np/ee 计数。**两者都没有块体顶点坐标**，
所以无法独立枚举，G2 对 tf.cpp 这一半做不了。

能榨出来的只有类型普查，而它给出一个值得注意的数：

```
smoke_cpu      stage : 5296 条   n-p 100.00%   n-n / n-e / e-e 各 0
sandstone_fine probe :  864 条   n-p 100.00%   其余 0
sandstone_med  probe :  556 条   n-p 100.00%   其余 0
                      ------------------------------------------
合计                   6716 条   e-e 一条都没有
```

**两种可能，在拿到几何之前无法区分**：

(a) 这几个算例的几何就是如此。轴对齐块体的面-面接触在 DDA 里正是用多个 n-p 表达，
    eab-kernel 在 cb2 上复现的也恰恰是 4 个 VF 盖、零 EE——完全自洽。
    sandstone 的探针还是**抽样的**（只在重试事件、且只写涉及触发块/顶压板的接触），
    顶压板与试件之间本来就以顶点-面为主。

(b) tf05 的展开**漏掉了交叉棱-棱**。若如此，这是 legacy 三维枚举的一处实质缺陷。

**不下结论**，但这条把"请 3DDA 补一份顶点导出"的优先级抬高了——eab-kernel 在真正非轴对齐的
位形上**能**产出严格 EE 盖（`test_wedge_on_wedge_gives_strict_crossing_edge_cover` 看着），
所以一旦拿到几何就能判。请求已写进 `docs/sibling_observations.md`：
HeavyProbe 里加一份逐块顶点导出（块号 + 顶点号 + 坐标，步初一次即可）。

> **补注（2026-09-24）：拿到几何以后，现在这道 G2 门也回答不了 (b)。** 门只对账 np ↔ VF/FV；legacy 若出现 `ee` 入口，
> 门会**变红**（见"对账口径"第 2 条），而不是去对账它——ee ↔ EE 的键还没有实现。所以要判 (a)/(b)，先得把 G2 扩到棱-棱，
> 这件事随入口选择一起列入里程碑 M2。

## 门

| 门 | 结果 |
|---|---|
| G2 同构（三例 × 两个方向） | 零差异（**限定 2026-09-24**：只指 np ↔ VF/FV；其余类别现在一出现就红，见"对账口径"） |
| G2 几何细节（间隙、法向、退化标记、nsign 约定） | 逐条吻合 |
| 共面归并：面数、体积不变、流形自检（四组几何） | 全过 |
| 三角化过计数反例（6 → 4） | 钉定 |
| 顶点编号经凸包重建后保持 | 过 |
| **有牙**：让枚举漏掉一个 VF 盖 | 门报出 `legacy_only` |

全仓 **199 个测试全绿**（09-20 当时）。

> **补注（2026-09-24）**：M0 之后本文件对应的 `tests/test_g2_bdda3d.py` 共 58 例（新增的有：ee 入口必红、多余 EE 盖必红、
> VF/FV 带内假盖必红、带边分界、低维盖不触发、带的几何空性、窗口理由、重复顶点别名、T 形顶点报错、穿过枚举器的带牙），
> 测试基线 8376ec2 全仓 1209 passed（77600c9 时 1174；main 现为 094861c，只改 `src/eab/limit.py` 第 41 行模块文档，
> 在它上面全套仍 1209 passed）。其中穿过枚举器的带牙来自 6f157ac，它是合并之后直接进 main 的，
> 没有经过独立复核者复核（见下文 C17 那段）；以上都还没有经过 G6 独立重审。

## 一个自己踩的坑，记下来

牙测试第一版没红。原因不在门，在测试：`vf_cover` 会对**全部** 8×6 = 48 个顶点-面组合被调用，
我"丢掉第一个 in_extent 盖"丢中的是一个间隙很大、本来就会被距离窗口滤掉的盖——
当然不会影响最终清单。**判断"这个盖会不会进最终清单"必须同时看 in_extent 与窗口。**

## 诚实边界

- bdda3d 的三个算例是**同一个位形**（只有接触状态 locked/sliding/bond 不同），
  所以 G2 目前只验了**一种**几何构型。更多构型需要 3-b-dda 那边再导出算例。
- 退化盖（FF 平行贴面、FE、平行 EE）仍**只标记不合并**——cb2 的 4 个 VF 盖就是一个面-面接触
  的四个入口，这与 DDA 的表达一致所以下游可用，但"把退化族收成一个 FF 盖"还没写。
- tf.cpp 一侧完全阻塞，等几何导出。
- **补充（2026-09-24）**：
  - G2 **只对账 np ↔ VF/FV**。`ee` 入口、窗口内的非 VF/FV 内核盖，现在会让门**变红**，而不是静默通过；但它们也没有被对账。
  - 对账窗口是 `G2_WINDOW = 1e-6`，不是 1.0。理由（legacy 的 np 间隙全为 0；最近的非面特征对 = 1.0）由
    `test_g2_window_contains_every_legacy_gap_and_nothing_else` 看着；1.0 那一段由 VF/FV 带接住（`test_g2_band_is_geometrically_empty`），
    带宽随夹具几何缩放。
  - legacy 侧三个 JSON 已进 `fixtures/PROVENANCE.json`，受 `tests/test_fixture_provenance.py` 逐字节看护
    （`test_every_fixture_file_is_hash_gated`、`test_bdda3d_gate_has_teeth`；审查盲区 3，提交 c1326a0）。
  - 输入顶点里的精确/近似重复点登记为 alias；不是凸包角点的顶点（棱中点、面中点这类 T 形顶点、内点）构造时就报错，
    不再静默保留（审查 C18；`test_g2_duplicate_vertices_are_aliased_and_reconcile`、`test_g2_non_corner_vertex_is_a_clear_error`）。
  - 前面 (a)/(b) 那个开放问题，这道门仍然回答不了（见该处补注）。
