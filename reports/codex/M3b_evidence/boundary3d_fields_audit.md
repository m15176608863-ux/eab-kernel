# 三维边界构造字段：审计收窄与补门

## 发现及纠正

原 `test_boundary_fraction_constructions_transform_under_exact_rotation_units_translation`
三档独立逐值只覆盖 `patches[*].polygon` 的坐标集合及 `BoundaryDistance3D.squared/tied_exact_points`。
它**没有**逐值核对法向、侧点、完整平面表、安排字段和局部盖数值。普通尺度的状态 oracle 零失配不能
替代这些构造量的独立逐值差分，因此原先任何“不限字段/分支的全数值覆盖”措辞都应撤回。

新增 `tests/test_m3b_boundary3d_fields.py` 后，下表字段在**非对称 Cartesian 双盒的真实 public
global_entrance 路径**上有完整独立参考；不是手工六面模型旁路。凸体入口生成的三角对角棱所带来的
冗余 SAT 平面也全部由手列源四边形首耳三角、测试自持 edge cross 和 canonical 算式独立构造。

| 字段 | 独立期望来源与检查 |
|---|---|
| `ExplicitBoundary3D.planes` | 原始两盒顶点/手列三角棱、自持叉积、分量比归一及整数 lcm；全部法向与两侧高度逐项相等 |
| `patches/arrangement[*].polygon` | 原盒差的 6 个解析矩形，手写有理 quaternion SO(3)；全部坐标，另用独立面积向量检查有向环 |
| `patches/arrangement[*].normal` | 已知 Cartesian 外向轴旋转后 canonical 整数向量；安排保留正首分量，暴露片保留外向符号 |
| `patches/arrangement[*].side_points` | 独立完整平面表和解析面中心求所有非零事件，取最小绝对事件的 1/2；逐坐标相等 |
| `side_states/sources` | 解析盒内外及唯一凸片对 `(0,0)`；按字段精确相等 |
| `candidate_facets/arranged_patches` | 解析 6/6，两个片集合均为 6；model 字段仅核对输入 identity，不冒称递归审计其所有 G 构造字段 |
| `probes()` | 解析角点、12 条棱的中点、6 个面中心及上述全部事件侧点；四类别坐标表完整相等 |
| `LocalCoverPatch3D` 全字段 | 原始 box min/max 支撑判据独立枚举所有 VF/FV/EE label；VF/FV 的 raw normal 为 2×源面面积，EE 为两棱叉积；全部三角/平行四边形坐标与 raw normal 相等 |
| 裁剪后的 `LocalCoverPatch3D` | 此凸盒分支所有有效盖已位于唯一全局支持面，解析裁剪不改坐标，只转为 canonical 外法向；全部 label/坐标/法向相等 |
| `BoundaryDistance3D` | 解析点到 6 个支持面的最小距离平方及全最优点集合，有理旋转和单位缩放后的逐值比较 |

多边形按所有坐标值比较并核有向面积，不要求同一 cyclic 起点或索引字节序；这是几何合同，不是字节门。

## 参数与边界

三档 `2^-400、1、2^400` 与公共大平移模长 `0、1e3、1e5、1e6` 做 **12 格笛卡尔积**。
公共平移为 `(3,4,12)/13*t`，由 3-4-12-13 勾股关系使欧氏模长恰为 t；双方原点另有非对称差。
每档位置使用 seeded 小整数 quaternion，排除旋转矩阵任何零分量，得到一般三维精确有理 SO(3)，
不是只有绕 z 轴转动。

**仍不得外推的分支**：这组逐值参考不覆盖一般凹体 BSP 的新增 Steiner 面/棱，不覆盖相互切片后新交点的
全部一般构型，也不覆盖多凸片来源组合的全部 metadata。那些分支仍依赖已有独立状态、完整覆盖、
三档部分构造门及其他子任务审计；不能把本盒分支的“所有字段”写成所有输入分支均已独立逐值穷尽。

## 冻结结果及数值门的牙

原 10 个新门加新增 12 格，独立完整运行：`22 passed in 7.09s`。
`boundary3d_all_fields_tests.json` 保存命令、前后不变源码哈希（含新增测试）和 static 新文件 0 违例。
生产代码、旧测试、tools 与 policy 在这次补门中均未修改；旧四家族扫描与 3 个几何语义变异也整次重跑。

另由 `boundary3d_numeric_mutations.py` 在独立子进程实际执行两个内部变异，均未调用源码 hash 绊线：

1. `_sides` 最近事件 `1/2 → 1/3`：实体标签可以仍然正确，但红在
   `independent exact canonical-plane side points`，证明新门真正审查侧点构造值。
2. `local_cover_candidates` 的 EE `exact_normal → 2*exact_normal`：几何点与法向方向均不变，但红在
   `independent every local VF/FV/EE label coordinate normal`，证明 raw 法向数值并非只查方向。

真实未捕获 AssertionError、returncode=1 和期望断言见 `boundary3d_numeric_mutations.json` 及对应两份 UTF-8 红日志。
同一证据脚本另从真实 public 路径构造全部 12 个参数格，仅对实际 planes/patches/arrangement/probes/local/clipped
字段序列化做指纹（排除输入、model 储存、参数标签和路径）；断言 **12/12 指纹互异**。
JSON 已记录 `parameter_outputs_distinct=true`、12 个输出 SHA256 和源码前后不变检查。
