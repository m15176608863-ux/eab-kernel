# WO-PERF：第二轮 arrangement witness 优化（已应用并验证）

此前 `DRAFT_NOTES.md` 保留的是未应用阶段记录。本文件记录最终已部署版本。

## 改动与等价性

仅修改生产 `exact_geom._surface_interior_witness`：

1. 对体 supporting-plane 去重外提。每个 source triangle 用 `base_unique.copy()`，随后按旧顺序更新 coplanar cuts；字典键顺序与最后代表值完全相同。
2. 原三角形与对体闭 AABB **严格**分离则跳过。此三角形所有 convex cell 在对体 AABB 外，原算法对其必报 `loc=-1`，不可能丢首 witness。
3. cut plane 对原三角形三个顶点同侧时，不再逐 cell 切分。所有 cell 都是原三角形凸包的子集，旧 `_split_polygon` 对它们只可能原样返回。
4. 对体 triangles 按精确支持平面 `(direction_key, plane_offset)` 分组；每个 source triangle 只访问同面列表。列表保持原 qt 顺序，切割平面仍由原 source normal 产生，不改 normal 比例或方向，不改 cell 或首见证顺序。

**无新增缓存、浮点过滤、容差、测试删减或跳过。** 只在 exact Fraction 上做重复构造消除及可证 no-op 排除。

## 新门与突变

`tests/test_perf_surface_witness.py`：40格随机/退化/工程坐标的首 witness tuple（含 None）严格 `==`；不仅比较 bool。冻结未优化函数在 `tests/perf_witness_reference.py`，共享底层精确原语，因此只是优化等价参考，不冒充独立 G0 oracle。

- AABB 严格界改成闭界剔除：同一 box 的共面向内见证被漏，`coplanar witness must survive` 报红。
- 原三角形同侧判据反号：部分交叠 box 的首 Fraction witness 改变，`first exact witness changed` 报红。
- **仅**从 coplanar 分组键去掉 plane offset（不污染 supporting-plane 去重图）：第9格预先钉死原首见证 `(-3/32, -7/16, 1/8)`，`parallel planes are not coplanar` 报红。

新增43门+原surface相关45门最后一行：`88 passed in 2.45s`。JUnit：`targeted.xml`。

## 分项微基准

可复跑 `PYTHONPATH=src python -X utf8 reports/codex/PERF_evidence/witness_draft/benchmark.py`。每项3次中位数；所有变体对同一当前底层原语逐值比较首见证。完整各变体计时：`microbench_variants.json`。

| 输入 | 旧 / s | 去重+AABB+同侧 / s | 最终再加分组 / s | 最终加速 |
|---|---:|---:|---:|---:|
| 同一box | .000367 | .000360 | .000340 | 1.08x |
| 面接触box | .004474 | .003554 | .003129 | 1.43x |
| 分离box | .003339 | .000269 | .000279 | 11.96x |
| nx5互锁就位 | .273684 | .182854 | .160415 | 1.71x |
| nx5互锁贯入 | .027029 | .009696 | .007906 | 3.42x |
| nx5互锁精确逃逸根 | .178880 | .081597 | .070188 | 2.55x |
| 工程坐标就位 | .299773 | .197297 | .174361 | 1.72x |
| 工程坐标贯入 | .030267 | .009792 | .008007 | 3.78x |
| 工程坐标精确根 | .190783 | .085558 | .077375 | 2.47x |

选择保留全部四项；第三项在互锁热点进一步有效，第四项也有稳定收益。小box的细小变动接近计时噪声，不能当作全套加速承诺。最终全套由root独占运行。
