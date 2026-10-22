# C1 精确差分口径与首轮订正

## 可重跑入口

`python tools/eab2_diff_c1.py --dll D:/eab-wt/cx-c0/eab2/build/eab2_test.dll --output reports/codex/C1E_evidence/diff_final.json --metamorphic`

脚本不进入默认 pytest 收集。`--dll` 缺失由 argparse 以退出码 2 拒绝；非绝对路径、文件不存在、ABI 尺寸不符、能力不足、选择为空、选中例未执行或任何差分不符均失败。库分配的每个 JSON result 都在 `finally` 中由库销毁；入口、body 和 context 同样释放。

## 双方共同规范化，不信任 C++ 预制规范形

1. Python 导出来自现存 `GlobalEntrance2`、全部原始 VE/EV 段、Python `_split_segments` 与 membership；不经 DLL 取得期望、谓词、舍入或任何精确 helper。此路径是 **Python 生产裁判差分**，不冒充 G0 独立几何 oracle。
2. 两份 JSON 进入同一纯 Python `Fraction` 规范化器。直线按整数齐次系数的 gcd/符号归一；同线全部区间端点精确排序、区间覆盖合并。输出无来源切分的极大 CONTACT 段，以及保留来源标签改变的分层区间。没有几何容差、浮点比较或中点近似相等。
3. 每条 CONTACT 段/点的来源集合必须等于所有原始段的精确关联；原始 VE/EV 列表另外整体精确比较，包括完全在重叠区内部的无效盖来源。端点必须显式存在；保留分支、交叉、来源变化端点和全部孤立点，删除的仅是同一直线同标签中的人工冗余切点。
4. 对每个二维面，核样本严格位于其精确凸边界内部。按 body/topology 状态归组后，将有向面边界在全部共线端点处再切分并求整数重数；人工内部竖直边相消，物理区域边界保留。重数不丢弃，重复覆盖不能仅靠去重通过。不比较有限外包围盒的 OUTSIDE 面形状，但仍逐面复核样本状态。正面积区域边界与完整 E\\O 层共同比较，因而不是只比面样本、面积或 cell 序号。
5. C++ 导出的全部顶点、开边与面样本由 Python `membership/topology` 精确复查。反向将 Python 全部层样本通过 **仅测试用有理查询** 送入 DLL，逐项比较两套三态；不把有理样本舍入为 binary64。0 处发布批量查询在导出前后都比较。
6. 小命名例外边界另对现存 Python `boundary`；正式语料外边界由 Python CONTACT 开段的 topology 组成。C++ 生产侧不调用 Python 或复制 `side_probes` 慢路线。
7. 所有例核输入原始 bits、CW/CCW 规范化顶点与原始顶点/边 ID 映射，先 local origin 再 global，并要求 local 不强制物化全局 subdivision。local 的排除/半径/原始关联/独立扇区复核由 `eab2_c1_local.verify_local` 执行。
8. 零窗 covers 对 Python `enumerate_covers` 的完整 label/strict 集；param、point_a/b、gap_squared、gap_sign 从原始 Fraction 顶点独立投影重建，不拿 Python 浮点显示当精确原值。E3 例另执行有限窗口、无界窗口及显式非零 tol/cone_tol/seg_tol。

## 输入域与语料

M3 六族，M3b 基础、孤立点/内缝、尺度/变换、矩形与三个 bb52 冻结输入，M3c 三档，E3 binary64 例，以及 tia2d-2 正式归档 assembly 块对。正式数据逐文件核压缩与解压 SHA-256；相同**有序输入 bits**只执行一次并保留每个归档来源 alias，去重不跨 body 顺序、不按几何近似去重。

含 `1/10`、`1/3` 等原有理坐标时，先对双方共同 RN 成 binary64，再对新输入精确比较，不宣称舍入前的共线/紧配关系保持。M3b 的三项 `2^-400 + 大平移` 输入在 RN 后出现零长边，不属于 C1 合法 binary64 简单环；作为明确的 Python-only 输入域排除保存在差分报告，不作为跳过的合法差分例。

## 首轮 harness 订正（未改 Python 数学合同）

`m3/tight_fit` 的 raw CONTACT 段 `(-1,-5/2)→(1,-5/2)` 不是完整竖直剖分里的单条开边。直接将它交给 compact `side_probes`，正侧有限点为 `(0,-1/2)`，恰落到后续内缝端点，body state 为 CONTACT；但原段的相邻开面实际为 OVERLAP。C++ 无穷小扇区标签 `[1,-1]` 正确，初版 harness 与不在同一局部层的有限 probe 作体态等同比较是策略错误。

订正后，harness 用全部凸胞 supporting-line 事件给出严格局部步长，再调用现存 Python membership 分类，逐条复核 C++ 的邻近开面 body state。`clipped_covers` 比较相同物理语义（来源、片中 body state、exposed、两侧闭 E 占据）；不要求两端不同采样坐标具有相同 body state。C++ 的 side state 另受严格局部采样核验，不是简单忽略差异。没有移植慢路线进入 C++，也没有修改裁判去迎合产物。

初始失败记录在 `diff_m3_initial.json`；其后 M3 六族复跑末行：

`C1_DIFF selected=6 completed=6 mismatches=0 layer_queries=776`

## 元门边界

对非对称二进有理 L / 含平直点矩形执行环循环起点、CW/CCW、body 顺序交换、先查询/先导出、merge/compact/cache 选项；另有 90° 旋转、反射、二进大小尺度、2^10 独立平移和 2^17 整体平移。每个变换先逐坐标检查 RN 恒等，再将全部规范几何及来源特征标签精确拉回基准坐标比较。有限测试不构成全输入域定理，也不替代 Claude 指派的非作者对抗核查或所有者安排的新鲜树复现。
