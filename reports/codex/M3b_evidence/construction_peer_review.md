# M3b 三维边界/出口独立交叉审阅（非 G6）

审阅者：construction3d 子任务；只读 `boundary.py`、`g03_exit_oracle.py`、`g03_surface_oracle.py`、
`g03.py`、`test_m3b_boundary3d.py`、`m3b_boundary3d_design.md`。本审阅不是六路 G6，
不把“未找到反例”写成算法全域正确性认证。

## 一致性核查

- T3B 的有限满维凸胞并/全支撑平面安排/两侧闭占据证明与实现相符。低/高支撑面统一法向后，
  `side_states` 决定向外法向；相触内缝不以物理 0 当外部。返回为闭片覆盖而非焊接网格，范围表述明确。
- 独立的局部盖覆盖裁判在全局片内再次按局部边支撑线划分，每原子片中心核包含；它没有调用被测
  `_hull/_clip_polygon/_split/_in_polygon`。全部顶点/棱中点/面心/事件双侧计数无按状态跳样。
- `shortest_exit` 的面正交投影及所有边投影枚举覆盖闭凸片距离极小点；输出全部等距点集合而不宣称
  字典序单点普遍旋转协变。闭 E 最短出口下确界与离开 O 的第一非贯入根没有混同。
- `g03_exit_oracle` 的源表面接触平面超集与 moment-curve 非平行方向独立于被测 BSP/SAT/局部法锥；
  对所有正事件间开区间判原表面闭分离，最后一个无界区间也执行，没有恢复旧 intersecting skip。

## 发现 1：未引用顶点缓冲误入独立出口 oracle（已送实现者修复）

精确复现，不使用新生产几何原语计算期望：

```python
A = box(half=(Fraction(1),)*3)                 # [-1,1]^3
B = box(center=(5,0,0), half=(Fraction(1),)*3) # [4,6] x [-1,1]^2
extra = Polyhedron(list(A.verts)+[(Fraction(5),0,0)], A.faces)
```

两实体面定义不变，解析平方距离仍为 `3^2=9`。
审阅时实测：

```text
original separated_distance(..., squared=True) = 9
buffered separated_distance(..., squared=True) = None
original g03(radius=0,samples=1).failures = []
buffered g03(...).failures = [(x=(0,0,0), actual=None, expected=Fraction(1,1))]
```

根因：`g03_surface_oracle.model` 的 adjacency/representatives 用全部顶点，包括未被 face 引用的缓冲坐标，
把 `(5,0,0)` 错当 A 的独立实体分量。新 global3d 已剔除未引用坐标，故两条通道模型合同不一致。
这不是生产全局几何错误，也不是可忽略的随机失败；是独立裁判对输入模型的错误解释。
建议 oracle 自己按 faces 引用做索引重映射，不能借用被测 G 的规范化函数以免破坏独立性。
修复与重跑状态以后续附记为准。

## 建议 2：T3L 的 EE 证明补足“局部非贯入 ⇒ 可分离”的桥梁

正文直接从局部 EE 不贯入跳到分离平面。对非凸体，应先解释该接触不能在反射棱发生：
若 A 的局部实体二面楔角大于 π，其补楔角小于 π，不能容纳 B 的非平行棱在 A 横截面内的两向投影；
否则接触线某一侧邻近的实体内点贯入。GP 已排除棱平行，故合法 EE 的局部楔必须为凸楔。
此后用两个凸开楔不交的分离定理，结合两条棱的 ±方向，才得到分离平面同时含两条线、法向为叉积符号之一。
这是一处证明展开建议，不是当前代码的已复现反例。任意退化原始局部盖弱覆盖仍明确保留条件 H，不能删去。

## 修复后复核附记

boundary 子任务在独立 `g03_surface_oracle.separated_distance` 入口增加了自持面引用重映射，
不 import 被测 G 的规范化逻辑。审阅者再次独立执行上面的原例及 buffered 例：两者平方距离均为 9、
g03 都执行 1 个样本且 failures=[]，记录 `construction_peer_recheck.json`。
T3L EE 段也已补充反射楔排除和凸切锥分离桥梁。本审阅发现 1 已修复，不再作为未解决问题；
仍不升级为六路 G6 或任意退化局部盖无条件定理。
