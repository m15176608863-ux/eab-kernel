# 后续性能建议：仅研究候选，未部署

本轮不再改生产源码或现有测试。以下原型仅在 `E5a2_evidence/tmp/`，**没有进入最终全套运行的代码，也没有证明全套 ≤900 s**；它们不解决已被独立分离证书确认的 interlock 候选集缺口。

## 1. 优先：布尔三角相交与单次调用内几何量复用

候选只服务 `_triangles_near` 的布尔消费，不替换公开 `triangle_intersection` 返回交点集合的契约：

1. 预计算本次调用每个三角形的精确面法向与 AABB；没有持久缓存。
2. 精确严格同侧即可排除：另一三角三个顶点的有理面值全部 >0 或全部 <0。
3. 非共面时，比较两三角与对方面相交所得线段在交线非零分量上的闭区间。
4. 共面时，投影到精确非退化二维平面，使用三角形边轴 SAT；端点/共边接触保持闭集语义。

证据范围：**1300 对非退化三角形**（随机有理数，加共面/接触/工程坐标/尺度关系）与现生产 Fraction 交点算法的 `bool` 逐对相同；不是新的独立几何 oracle。微基准 0.278→0.056 s。

另有 interlock **5 个位移 × 2 个 tol = 10 格**，与原 `_triangles_near` 状态逐格相同：两个分离、tol=0 格约 0.075→0.012 s（约6倍）；但一个贴触格 0.0054→0.0100 s 反而变慢。**小快路6倍不能外推全套**。

正 tol 的附加研究变体：若某一面上所有有理面值严格同号且最小绝对面值 h 满足 `h² > tol² * (n·n)`，则真实三角距离必大于 tol，可整对排除。这只是严格的距离下界拒绝，不能把支撑平面距离当成完整欧氏距离、不能据其接受“近”。该变体同10格状态相等，远距正tol格 0.407→0.090 s；尚未部署或系统验收。

- [布尔候选脚本](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/tmp/triangle_algorithm_candidates.py)
- [1300对与10格结果](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/triangle_algorithm_candidates.json)
- [正tol面距离下界变体](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/tmp/triangle_plane_bound_candidate.py)
- [下界变体结果](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/triangle_plane_bound_candidate.json)

## 2. 次优先：真正横穿的内部交叠正证书

对非平行三角形，若两者严格跨过对方平面、交线区间有内点 p 且 p 在双方三角的相对内部，构造

`d = (n·m - m·m)n + (n·m - n·n)m`。

有 `n·d = m·d = (n·m)² - (n·n)(m·m) < 0`。沿 d 在全体面平面的首个正截距之前取有理样点 w，并仍用两实体精确点成员判据确认 w 都在内部，才给出正证书。没有证书必须回退原完整 arrangement；共面分支不能删除。

仅验证了 **3 个刚体变换/工程坐标/尺度格**的 L 凹块与横穿细梁：双方顶点都不在对方内部，候选 w 通过独立矩形并集与梁不等式验算。旧 arrangement 约0.0025–0.0030 s，候选约0.0012–0.0015 s；只证明这些格的正证书与成本，不能外推一般非凸闭表面。

- [横穿证书候选](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/tmp/proper_transverse_candidate.py)
- [独立见证核验结果](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/proper_transverse_candidate.json)

## 集成前的退出条件

- 先针对最终冻结源码重新 profile 剩余慢文件，确认 `_triangles_near` / arrangement 仍是真实热点。
- 新增随机、边界、微小特征、工程坐标的独立精确 oracle；本研究中的旧生产算法对拍只作优化等价佐证。
- 闭集端点、严格同侧符号、横穿见证复验分别打真实内部突变；原共面分支突变牙仍须保留。
- 维持所有原测试与参数格，重新冻结源码、完整全套、独占墙钟验收。不得把这些未部署候选写成现有提速成果。
