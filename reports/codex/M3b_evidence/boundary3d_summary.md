# M3b 三维显式边界子任务冻结摘要

## 处置与理论边界

- 新 `src/eab/kernel3d/boundary.py`：凸片对全部 facet 经全部支撑平面精确加细，双侧闭占据异标筛选，
  输出闭凸片覆盖；原始闭有效 VF/FV/EE 盖与全局暴露片精确裁剪；`shortest_exit` 返回 PD_closed
  的 Fraction 距离平方与全部并列最优点。不是焊接流形网格，点仍相触，不称已严格分离。
- `docs/m3b_boundary3d_design.md`：T3B 对有限认证满维凸片并、不要求一般位置，证明完整；
  T3L 明确跨体面/面、棱/面、棱/棱非平行 GP，证明 GP 导出局部闭盖弱覆盖，继而得裁剪强完备。
  **任意退化凹体原始局部盖弱覆盖仍作为条件 H，并未普遍证明。** 四个退化/一般家族有有限完整证据，
  不升级成所有退化输入的无条件定理。
- `g03.py` 相交/contact 样本不再跳过，原 `skipped_intersecting` 始终为 0；
  新 `g03_exit_oracle.py` 独立原始表面支撑事件超集逐开区间检验闭 E 方向出口，和全局区间端点逐 Fraction 相等。
  该随机门逐样本验证确定性非退化方向，不冒称遍历全部方向或直接验证全局最短出口。
- `local_cover_candidates` 入口也调用精确嵌入认证，拒绝相交 shell，跳过未引用顶点 buffer，保留源索引。
  `explicit_boundary(model)` 接受的手工模型仍须满足已认证凸片合同。

## 冻结全安排探针（不跳样）

命令：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 tools/m3b_boundary3d_evidence.py`。
运行前后全部相关源码 SHA256 一致；最终结果 `boundary3d_scan.json`；中间进度非最终证据。

| 家族 | 凸片对 | 候选 facet | 去重安排片 | 暴露片 | 顶点 | 棱中点 | 面重心 | 双侧事件点 | 独立局部盖原子覆盖 | 时间/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| L | 2 | 12 | 60 | 57 | 50 | 106 | 60 | 119 | 409 | 2.9266 |
| tight | 3 | 18 | 147 | 114 | 91 | 232 | 147 | 293 | 577 | 7.0282 |
| cavity | 6 | 35 | 1054 | 696 | 685 | 1722 | 1054 | 2096 | 868 | 60.2448 |
| general_tetra | 1 | 14 | 14 | 14 | 12 | 24 | 14 | 28 | 14 | 0.0834 |

共 **6733 个类别-坐标探针，0 失配，0 skip**；相同坐标在不同类别出现时分别计执行检查。
另有 **1275 个安排面双侧拓扑判别**和 **1868 个独立投影原子片完整局部盖覆盖检查**。
不仅检测暴露面：所有凸片对 facet 经过完整平面安排形成的内部片也进入 probes。
最大实例有 1366 个含来源重复的安排片；本扫描未触达大型 Xbloc/高分辨率随机网格的规模上限。
朴素安排的最坏增长及精确局部化前提已写设计稿，不声称任意规模可承受。

## Oracle import 清单

1. 三态主裁判：`geom3.polyhedra_overlap -> exact_geom` 原始表面三角分割/奇偶；不调用被测 BSP/SAT/边界裁剪。
2. 出口主裁判：`g03_exit_oracle` 仅 import fractions、itertools、g03_surface_oracle；后者仅
   fractions、functools、math、kernel2d.g0_oracle.sqrt_display。核心几何为独立整数面绕数、射线奇偶、
   线段面检测与有理距离；不 import global_entrance、boundary、covers3、exact_sweep。
3. 强覆盖主裁判：测试自持 `oracle_cover_union`，自写二维行列式、线性插值、凸片包含及投影安排，
   **不调用 B/G 的 hull/clip/cross/split/in_polygon**。边界数据作为待审输出输入 oracle，不借生产原语给期望值。
4. 最短出口及三档构造：Cartesian box 差的 6 面、坐标夹取与手写有理旋转公式；不用基线输出作为真值。
   三档 `2^-400,1,2^400` 各逐值核对全部显式面顶点、距离平方及并列见证；含非轴对齐有理旋转和 1e6 平移。

## 有牙的语义变异

命令：`python -X utf8 tools/m3b_boundary3d_evidence.py --mutations`；独立子进程实际返回 1，
未捕获 AssertionError 的全文红日志保存在下表路径；全程未执行源码 hash 绊线。

| 内部变异 | 预期语义断言 | 证据 |
|---|---|---|
| 删除局部盖裁剪，直接返回原候选 | local cover clipping removes buried polygons | boundary3d_mutation_remove_clipping.txt |
| 用片上物理 0/1 替代双侧闭占据异标 | closed occupancy boundary not physical 0/1 seam | boundary3d_mutation_physical_zero_one_seam.txt |
| 恢复相交样本 continue | intersecting exit sample must execute | boundary3d_mutation_restore_intersecting_skip.txt |

注意：正确完整安排的双侧点在满维开胞中，物理标签只有 -1/1；仅把两侧比较中的 `>=0` 字面换成 `>0`
是等价变异，不能诚实声称杀死。实际误收紧配内缝的错误是把**片上**物理 0 当拓扑边界，第二条精确注入该缺陷。

## 测试与交付状态

最新定向测试（10 个本单新门 + 1 个旧 merged interlock 回归）末行原样：

```text
11 passed in 12.16s
```

旧 g03 20 个定向门首跑为 19 passed + 1 failed，失败发现精确入口新 vertex-link 对合法共线细分的误拒；
由 construction3d 子任务修为多重图后，上述旧 merged 门已复核绿。全套四片与总耗时增量以主报告的最终跑数为准。
新增边界门约 5 s；g03 不再跳相交样本确实增加工作量，不在本子任务用少抽样掩盖。

交叉复核另发现独立 oracle 原 `model` 把未引用顶点 buffer 当作孤立实体分量：半宽 1 盒与
中心 (5,0,0) 盒的真实距离平方 9，A buffer 追加不被 faces 引用的 (5,0,0) 后原 oracle 错回 None。
已在 `g03_surface_oracle.separated_distance` 入口用**自持面索引 remap**移除未引用行，不调用生产几何。
新门同时交换 A/B 核验解析 9，并要求 g03 1 个样本执行且零失配。最后完整扫描和三变异已基于此修复整次重跑。
三维设计的 EE 证明也按 peer 意见补上“反射楔无法无贯入→双方凸切锥→分离平面”的桥接论证。

静态预检：边界/测试新辅助大部可自动证明；已上报剩余 6 条明确上下文 review：EE 分支的已显式 F 的
差点 convex hull/数据类构造两处各两条，以及独立表面 `separated_distance(..., squared=True)` 返回 Fraction/None 两条。
旧 g03 修改后的源码 hash 豁免续期由主任务逐条复核；本摘要不先宣称静态 0 违例。
独立表面 oracle 本次修复另使其原 `sqrt_display(result)` 两个既有 waiver 的 enclosing-function hash 过期；
只需同一显示出口上下文重新复核续签，不增加几何精确性白名单。

边界子任务完成当前明确有限域交付；全域任意退化局部盖普遍弱覆盖及大型模型规模结论保持 PARTIAL。

## 数值全字段补审（后续增补，不覆盖既往跑数）

root 复核指出原三档门只逐值审面坐标及 PD 平方/见证，不足以称“所有新字段差分”。已补
`tests/test_m3b_boundary3d_fields.py`：真实 public 模型，全部完整冗余平面、patch/arrangement 法向/侧点、
局部 VF/FV/EE 原始与裁剪数值、probe 等所有字段在**非对称双盒分支**有测试自持解析参考。
3 档×4 个精确平移模长（含 1e5/1e6）及 seeded 一般 quaternion 旋转共 12 格。
原 10 新门 + 本次 12 格最终完整跑数：`22 passed in 7.09s`；本新文件 static 0 违例。
完整字段范围与未覆盖的一般 BSP/裁剪 Steiner 分支见 `boundary3d_fields_audit.md`，不得无条件外推。
内部侧点 1/2→1/3 与 EE raw normal→2 倍两种数值变异均有真实语义红日志，见 `boundary3d_numeric_mutations.json`。
