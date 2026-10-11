# 三个沿 y 滑动“应严格零高度”失败的独立诊断

## 结论

全套中的三个 `test_brute_oracle_is_exact_zero_at_rest_and_scales` 失败，都不是凭 brute 非零反推贯入。对**原测试实际 float 输入**（先旋转/缩放/平移，再用原 `_vec` 位移调用 `A.translated`）分别找到了一个严格位于两体内部的有理点。

| rot | t | s | final.log 的 brute 返回值 | 独立结论 |
|---|---:|---:|---:|---|
| z0.7 | 1e5 | 1 | 2.3283064365386963e-10 | 初始 y 向滑动后真实内部相交，不能要求严格返回 0 |
| z0.7 | 1e5 | 1e3 | 2.3283064365386963e-7 | 同上 |
| z0.7 | 1e3 | 1e-3 | 2.3283064365386963e-13 | 同上 |

这是旧门把“理想互补挤出体沿 y 滑动”强加给分别舍入后的浮点表面的语义冲突。它与墙门 7 格实际遗漏最早逃逸根不同：此处独立证据只否定严格零期望，不声称 brute 返回值就是精确最小根。

## 证书与独立性

- 每体按原 face-ring 规定的确定三角化解释，共 68 个源三角形。
- 候选点仅由 raw 顶点/独立三角形质心向 raw 顶点均值偏移 `2^-80` 构造；没有向生产 membership 请求答案，也不消费 production witness。
- 用测试侧独立 ear triangulation 与 `walls_diagnostic.py` 内 Fraction 射线奇偶法核验两个实体内部。
- 逐点另外确认**不在两体任何一个源三角形的所在平面上**，排除边界点被当内部。
- 不调用生产 normal、triangulation、ray、SAT、membership、cover、surface intersection 或 arrangement；不使用 star-shaped 假设，不把 brute 当 oracle。
- JSON 保存 3 个完整有理坐标与每项验证结果。扫描用时约 0.255 s。

## 状态和交接

只写本目录诊断脚本/证据，生产与测试源码未改。三个失败仍保留在最终 `49 failed / 7953 passed` 中，不能把事后诊断冒称测试已绿。

若后续迁移该旧门：须保留原完整参数网格与所有调用，对每格实际原始表面是否贯入采用独立精确 oracle；严格非贯入才保留返回零要求。还须另外保留精确有理互补理想轨道的零逃逸门。不能改成统一绝对近零容差吞掉真内部。

## 文件

- `invariance_brute_slide_diagnostic.py`：复现与独立证书核验脚本。
- `invariance_brute_slide_diagnostic.json`：3 个严格共同内部有理点。
- `invariance_brute_slide_diagnostic.log`：运行结果。

此为开发期零生产几何原语共用诊断，不是 G6。
