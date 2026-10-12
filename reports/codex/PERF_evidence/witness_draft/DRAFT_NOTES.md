# Arrangement witness 等价优化草案（未应用、未测试）

只写 PERF_evidence/witness_draft；src/tests/tools 未更改。草案位置：
- original_function.py.txt：本轮冻结前函数原文。
- optimized_function.py.txt：三项早停/重复构造消除。
- perf_witness_reference.py.txt：可放 tests 的冻结逐值参考。
- test_perf_witness.py.txt：40 格 random/退化/工程坐标精确首见证对拍 + 2 个内部缺陷门。

## 证明

1. 支撑平面 unique 外提：`base_unique` 按原 qp 顺序建立，tri 内 copy。随后只把 coplanar edge cuts 按原顺序插入。Python dict 的既有 key 更新只换值、不换位置，故与原来 qp+edge cuts 一次建立的字典具有完全相同的键顺序及最后代表 `(m,a)`。这也避免错误地更换 cut 朝向而改变子 cell/首见证顺序。
2. 原三角形严格 AABB 分离：三角形及所有切分 cell 都在原三角形凸包内；三角形 AABB 与对体 AABB 沿任一坐标严格分离，则所有原算法生成的 cell 均会 `_point_in_triangles(...) == -1`。跳过它们不可能删掉非 None witness。界只用 `<`/`>`，共面/相切界保留。
3. 原三角形同侧 plane：线性有向距离在三角形凸包上保持同侧，每个后续 cell 是该凸包的子集。原 `_split_polygon` 对这些 cell 必返回原对象的一项列表。跳过它们与原算法的 cell 值、顺序完全相同，不修改首次 witness。

全部比较精确有理，不新增缓存、浮点过滤或容差；因此无需浮点误差界缩小/新缓存删键类突变。

## 预设突变（待真正运行核验）

- AABB `<`/`>` 改 `<=`/`>=`：相同 box 的全部边界三角形被误剔；`coplanar witness must survive` 应报红。
- 原三角形同侧判据反号：部分交叠 box 的切分被误省略；`first exact witness changed` 应报红。

不要将以上预期当作已验证结论。仅在首轮全套结束、允许应用后运行。

## 成本风险

第三项在只有一个 cell、且 plane 确实相交时会额外做三次点面求值，可能拖慢小凸体。因此最终是否保留，应按逐项微基准看：外提+AABB 与再加三角形同侧门分别计时，若无收益则删第三项，保持前两项。
