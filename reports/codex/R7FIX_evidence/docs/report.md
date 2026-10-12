# R7FIX 文档组：G6G-09 / G6G-10 / G6G-11

## 边界与回滚

- 范围仅本工作树；未做 Git 写操作。只读核对 `D:/E(A, B)` 的 00 / 01，未更改正本、姊妹源码或审查树。
- 实现政策不改：默认精确三态、六轴和星核薄壳窗口均保持。仅修正窗口的数学主张。
- 回滚锚为总执行方保留的 tracked baseline；三次文档变异额外原字节保存、`finally` 恢复，并核 SHA-256。
- 按工单未创建 worktree；本组定向绿不等于独立 G6 退出。

## 逐条

### G6G-09：六轴证书不能推出一般闭表面闭集完全分离 PD

**修前红**：新增 `test_r7fix_docs.py::test_g6g09_window_documents_distinguish_closed_separation_infimum` 读取 README、canon_map、两设计文档和 PERF 原文，5 格均在 `G6G-09: distinguish closed-set PD from interior nonintersection` 断言报红。完整修前为 `8 failed, 3 passed in 0.25s`，其中 1 个额外失败来自新文档变异辅助测试依赖尚未加入的口径，并不另计缺陷。

**根因**：正本 01 第 5 行限定紧凸块，第 34 行是闭集完全分离的下确界
`PD_closed = inf{||d||₂ : (A+d)∩B=∅}`，不是“存在长度 PD 的严格分离位移”。当前一般闭表面六轴只证
`rho = inf{||d||₂ : int(A+d)∩int(B)=∅} ≤ w`。

**修法**：五文档统一给出上述定义和“不保证 PD_closed≤w”；三维设计完整解释凸情形支撑面与一般非凸的差别，并加封闭恰-fit 空腔。`exact_sweep.contact_models` docstring 同步；margin docstrings 由总执行方同步。没有改薄壳运行政策。

**空腔独立门**：A 半边长 1/2、中心 (-1/8,0,0)，B 为半边长 2 的闭外盒减去半边长 1/2 的开内盒。区间角点集和连通性给 `rho=1/8`、`PD_closed=19/8`；恰好 19/8 处仍接触，任意进一步位移才严格分离，显式检查下确界而非最小值。oracle 只用 Fraction、Cartesian product 和区间，不用生产三角化/SAT/成员/距离。生产默认结果为贯入，显式 w=1/8 为相触。数值政策原本就这样，所以该数值门修前已绿；真正的红是错误文档命题。

**真实变异**：把已修 `exact_3d_design.md` 的 `六轴非贯入证书 ⇒ rho ≤ w` 改回原 `六轴脱离证书 ⇒ PD ≤ w`；目标断言 `axis acceptance does not bound PD_closed`，`1 failed in 0.12s`。不是制造虚假几何输出。

### G6G-10：GAP3 开放/已处置与 README 旧 oracle 矛盾

**修前红**：`test_g6g10_readme_oracle_and_canon_status_are_current` 在 `G6G-10: stale production oracle claim` 报红。

**根因 / 修法**：把 canon 第 19 行第三轮“未打开正本”的历史缺口明确标为历史，说明第四、第五轮已核并逐条处置；不将内容映射已处置偷换成实现缺口或 M0/G6 已关闭。README 当前凹块 G0 改为独立 `kernel2d/g0_oracle.py` 的区间/段距离/事件 oracle。另把生产 `geom.polygons_overlap` 实际 monkeypatch 为抛错，运行当前 G0 单样本仍通过，防止只换文字。

**真实变异**：真实 README 当前 oracle 描述恢复成旧 `仍以暴力 polygons_overlap 检验距离/出口完备性`；同一具名断言报红，`1 failed in 0.14s`。

### G6G-11：撤掉全部现行“第一份”优先性宣传

**修前红**：`test_g6g11_priority_claim_is_withdrawn_instead_of_narrowed` 在 `G6G-11: narrowing priority to DDA is still a false claim` 报红。

**根因 / 修法**：canon 对 07 第 33 行的处理不再说“对外限定为 DDA 圈内 / 本课题组第一份”，直接说明原主张不成立。依据只读 00 已列的 Zheng/Jiao 2016、Zhao 2020、Feng & Tan 2020、Ni 2020 谱系，改称“一份独立实现；姊妹三线独立对账通道”。连 AGENTS 开头和 sibling 台账中对内部通道的序数性宣传也一并撤掉；历史引述只保留明确否定的语境。未联网重查文献，不新增学术优先性判断，未修改只读 07。

**真实变异**：canon 实际行重新插入“对外须限定为 DDA 圈内 / 本课题组第一份”；`narrowing priority` 目标断言报红，`1 failed in 0.13s`。

## 同类扫描

1. `README.md`、`AGENTS.md`、`docs/`、`src/` 和当前 PERF 中的六轴/PD、首次实现/第一份、GAP3、oracle 描述作全量关键词扫描；发现并同步四份复制的 banner、三维设计正文和表格、PERF 表格、`exact_sweep` docstring、margin 中文模块/函数 docstring（后者转总执行方）、AGENTS 和 sibling 内部通道序数。当前优先性关键词只剩 AGENTS 订正和 canon 两条明确否定的历史引文。
2. 未重写历史审查输入、历史性能数字或历史失败证据；当前口径在各自现行说明中明确修正，不将历史报告冒充本轮结果。
3. 另按总执行方请求只读核 `g03.py` / `g03_surface_oracle.py`：生产 `enumerate_covers3` 内部六个 `out.append(c)` 改为 `pass`（仅临时内存 namespace，不写源码）。普通单位盒 `atol=1e-9` 时缺盖会红，但 `atol=NaN/inf/有限1e308` 时 `worst_abs_error=inf` 仍 `passed=True`。修前独立结果见 [扫描证据](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/scan/g03_scan.json)。总执行方已增加有限非负 atol 验证、非有限失败独立拒绝、Fraction 阈值比较，另存 [修前](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/dual/g03_red.log) / [修后](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/dual/g03_green.log)。大有限坐标 float AABB 相减原可产 L=inf，但后继有理构造响亮 OverflowError；未把它误报为默认窗口下静默通过。geom3 组随后已将 metrics 差向量改为精确相减，提前响亮拒绝不可表达特征长度。
4. `g03_surface_oracle` 没有把非共面源环当平面：`face_pieces` 独立 Newell 投影耳切，`model` 从切片收集全部边。原 G6G-04 折面屋脊输入返回 2.0，两条内部棱均在模型中。此项没有确认同类遗漏。
5. `g03.py` 候选距离仍反减全局显示见证点；其现行 docstring 明示只审计浮点见证构造、使用噪声 allowance。该路径不是精确 cover distance 的独立验证；风险已交总执行方，不把“noise 下绿”提升成局部构造正确性证明。

## 三维修复交叉只读复核

- 对 G6G-04 / 05 / 06 / 08 的 `geom3.py`、`covers3.py`、`margin.py` 当前 diff 作逐项只读复核。VF/FV/EE 的精确法向方向乘 gap 符号，以及 VE/EV 互换、VV 和 folded repair 的 delta 朝向均与 B→A 一致；`_resolved_cached` 按 `fields(Cover3)` 冻结并重建，包含新增方向证书，没有丢字段。
- `_repair_folded_construction` 删除早先 `4*rounding` 早退，但仅对 VF/FV + 原二元源面标签 + 实际有非平面三角 pieces 的分支重建。平面源面和默认已展开三角标签仍直接返回，未扩大为“所有错误见证都修成真值”的无牙自校验。
- G6G-04 的 `exact_surface` 保留原顶点编号；所有非平面面片的内部棱参与距离。质量积分用实际源面三角化后的 exact 有符号四面体体积和相对一阶矩，不把首点扇形填入凹面。Newell `face_area` 明确仍是 Newell 面积，不冒称折面三角面积之和。
- 实跑旧 bad-witness、自校验阈值等 7 格，旧 folded 源面距离 1 格，新三维组 35 格，最后一行原样 `43 passed in 0.82s`；[交叉复核日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/scan/geom_review.log)。本次未确认新三维错误；这不是完整独立 G6 或全域正确性证明。

## 测试改写台账与定向结果

- 未删除或改写任何原测试函数、断言、参数网格；只新增 `tests/test_r7fix_docs.py`。既有 PERF 六轴凸盒门全部原格运行。
- 最后定向命令：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r7fix_docs.py tests/test_perf_contact_window.py --basetemp=reports/codex/R7FIX_evidence/tmp/docs_post_complete`。
- 最后一行原样：`39 passed in 1.06s`。其中新文档门 14 格，既有 PERF 门 25 格。全套、指针修复由总执行方统一运行，本报告不声称已执行。
- 初次批量替换尝试受 PowerShell 管道默认编码影响而在首个断言失败；当次未写任何文件。显式 UTF-8 后完成，原文换行保留。

## 证据链接

- [新增回归门](file:///D:/eab-wt/cx-e2/tests/test_r7fix_docs.py)
- [修前红](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/pre_red.log) / [修后绿](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/post_green.log)
- [变异元数据及恢复 SHA](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/document_mutations.json) / [可复跑真实文件变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/run_document_mutations.py)
- [只读正本行证据与 SHA](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/read_only_canon_evidence.json)
- [G03 同类扫描脚本](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/scan/scan_g03.py)
