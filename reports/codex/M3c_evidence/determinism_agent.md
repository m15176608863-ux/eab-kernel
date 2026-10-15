# WO-M3c：确定性与文档分项证据

## 第 6 项：compact 公开输出确定性

- `src/eab/kernel2d/global_entrance.py::GlobalEntrance2.side_probes` 在首次 compact 侧探针查询前构造最终剖分；默认非 compact 路径不变。
- `_contact_subdivision` 只依赖 membership、接触骨架和切分工具，不访问 side_probes / boundary / clipped_covers，无递归求值环。
- `tests/test_m3c_determinism.py` 比较冷对象直接取探针/裁剪盖与热对象先取 subdivision 的公开字段。`CoverPiece2` 的 dataclass 等号逐字段核对，包括标签、起终点、exposed、body_state、side_points 和 side_states。
- 样本为恰填凹口袋的块、额外平直顶点、一般有理旋转、不同大平移、几何尺度 2^-4 / 1 / 2^4；另断言三组实际 side_points 产物互异。
- 独立性边界：这是调用顺序不变性的 API 元门，不是额外的几何真值 oracle，不复用被测几何原语来制造预期答案。imports：fractions、inspect、textwrap、pytest，以及被测 kernel2d.global_entrance 模块和 GlobalEntrance2 类。

### 真实红 → 绿证据

1. 先对未修改的 M3b 生产方法运行新语义门，6 条全部失败。日志：[determinism_baseline_red.txt](determinism_baseline_red.txt)。失败断言分别为 `compact side_probes fields depend on public call order` 和 `compact clipped_covers fields depend on public call order`；后者差异实际在 side_points，标签不需要改变。
2. 源码修复后：[determinism_green.txt](determinism_green.txt)，`9 passed in 1.80s`。
3. 新门内部两条变异直接重编译被测 `side_probes`，删掉强制剖分分支，恢复旧惰性路径；只接受上述对应语义 AssertionError，随后恢复方法并再次逐字段核对为绿。未调用任何源码哈希类检查，也未在输出之后注入假数据。
4. 现有 M3b 邻面侧点与内部语义变异回归：[determinism_existing.txt](determinism_existing.txt)，`11 passed, 19 deselected in 0.28s`。这是定向回归，不冒充全套 0 deselection；全套由根代理统一执行。

## 第 8 项：文档与历史证据

- T3L：增加共面覆盖引理。非共面相交及共面零面积交有限且至多一维，不能覆盖暴露二维开片的稠密子集；有限闭正面积共面交由闭包覆盖全片。
- VF/FV：明确源关联棱非正点积测试只是局部闭支撑的必要条件，候选是闭有效集的超集。真正有效子集保证不漏，独立全局边界裁剪保证几何可靠性；不把冗余标签升级成局部充分有效的证明。生产 docstring 同步订正，不改三维算法。
- T2：二维按全局凸胞边切分即可，无需局部盖互切；T2b：每条相对开原子边标签恒定，各顶点各自取标签，不要求端点标签与边内标签相同。
- `M3b_evidence/final_suite_r3/VOID.md` 明确作废，指向 r4，不改写历史日志。
- `M3b_evidence/static_review.json` 的 23 条续签均补 `old_review_evidence`。逐条以 `R12FIXb_evidence/local_review_decisions_release.json` 的同 ID 记录核对 path、old_context，并确认所指原审查文件存在；未新加豁免，也未改变上下文哈希。
- BOM 已实证：`git show 5f87ebd^:src/eab/kernel3d/g03_surface_oracle.py` 原字节以 EF BB BF 开头，当前文件不含 BOM。**M3b 已移除 g03_surface_oracle.py 原有 UTF-8 BOM；本单仅补报告说明，不声称本单再次改动它。**

## 协同边界

本分项最后生产源码改动为 global_entrance.py 的确定性修复及 boundary.py 的 docstring 订正。二者已通知根代理冻结；M4c 源绑定须由根代理真实重放 450 帧后更新，不能只刷新哈希。静态构造门和全套四分片由根代理统一执行，此分项不替其宣告通过。
