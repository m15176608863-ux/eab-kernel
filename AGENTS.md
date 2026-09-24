# AGENTS.md — eab-kernel 常驻纪律

本仓库是"统一接触内核"（石根华入口块 E(A,B) 理论的一份独立实现，兼姊妹三线里三维接触枚举的第一份独立 oracle）。设计文档正本：`D:\E(A, B)\07 程序设计·统一接触内核方案.md`。

> **订正（2026-09-24）**：原文写"E(A,B) 理论的**第一份实现**"，不成立——`D:\E(A, B)\00` §3.3（及第七节"替代入口"第 3 条）
> 引的 Zhao et al. 2020（DDA + 4D-LSM 耦合），以及第八节文献清单"圈内实现与批评"里的 Zheng, Jiao et al. 2016
> （该表标为"首个三维入口块实现"）、Feng & Tan 2020、Ni et al. 2020 等，都是更早或同期的实现
> （`docs/canon_map.md` 第七节第三层已指出）。"第一份独立 oracle"
> 只指姊妹三线之间的对账通道（`docs/sibling_observations.md` 2026-09-18 节），不涉及学术优先性。

## 1. 红线：第四个独立仓库，姊妹三线只读

1. **零代码依赖**：`src/eab` 不 import `D:\b-DDA`、`C:\3DDA`、`D:\3-b-dda` 的任何模块，也不 import 导师线 DDA4.x。对账只消费它们的**导出文件**（dump/探针/快照），快照入库 `fixtures/` 后回归不依赖任何 exe 或姊妹源码。
2. **对姊妹仓库一律只读**：不写入、不删除、不 git 操作。需要它们生成新导出时，在本仓库 `tools/` 里写编排脚本，把 exe 与输入**复制**到 scratchpad 沙箱运行，产物再复制回 `fixtures/`。
3. **现有内核语义零修改**：本仓库以影子运行（shadow-run）挂到三条线；切换开关只在各线自己的仓库、由所有者决定。
4. 姊妹仓库的缺陷记入 `docs/sibling_observations.md`，不代为修改。

## 2. 门（改动必跑）

- `python -m pytest -q`（契约往返 + 读取器确定性）
- 阶段门见设计文档第五节：G0 自证（暴力成员谓词）/ G1 二维同构 / G2 三维同构 / G3 对偶 / G4 活动集 / G5 差异台账。
- **门要有牙**：新加看护算例必须把缺陷重新引入一次、确认它会报红；参数化的门加"产物互异"断言。
  （2026-09-24 补）**牙要穿过被测路径**：缺陷注入到被测代码内部，不要在它的产出之后追加假数据。
  反例：G2 的 VF/FV 带内检测起初只在"枚举之后追加的假盖"上测过，把 `compare()` 的枚举窗口改回去，
  整套照绿（第二轮验证判 NO_TEETH）；6f157ac 改成在内核里打缺陷
  （`tests/test_g2_bdda3d.py::test_g2_band_catches_a_real_kernel_defect_through_enumeration`）。
  （2026-09-24 补）**变异报红后要看是哪条断言红、为什么红**：红的必须是看护该缺陷的断言，而不是一条碰巧依赖求解器取哪个顶点的脆断言。
  反例：b26d7f5 的"力矩反号"变异在对称参考点上只是接触列重排（同一个 LP），它弄红的 2 格是"滑动机构无转动"这条非不变量断言，
  提交说明却把它记成"其余全绿"；8376ec2 删掉该断言、改读对偶最优面的不变量
  （`tests/test_end_to_end_cb2.py::test_failure_mode_is_read_off_invariants_of_the_dual_face`）。
  上面两例里的 6f157ac、b26d7f5、8376ec2 都是 b1bbd27 合并之后直接进 main 的，**未经独立验证者复核**，待 G6。
- **新路径守同构门，不守逐字节门**：盖枚举顺序天然不同于 legacy（df04 候选序 / df05 平局 / df06 匹配序"即物理"）。

## 2a. 审查后的常驻纪律（2026-09-21 定 A/B/C 与 G6，2026-09-24 补 D/E）

出处：`docs/plan_20260921.md` 第一节、`reports/audit_20260921.md`。每个里程碑都受它们约束。

- **A · oracle 不得与被测代码共用几何原语。** 每道 G0 类门在 docstring 里写明"oracle 用了哪些原语、与被测对象不重合"。
  做不到零共用的对照（例如暴力二分逃逸高度与被测路径共用 `polyhedra_overlap`）只能当佐证，不能当主 oracle。
- **B · 参数化按构造覆盖三类格子**：至少一个分界点（如 μ = w/2h）、一个非对称/一般位置输入（如 nx=5 而不只 nx=4）、
  一个尺度变化输入（荷载与几何各自缩放）。09-21 的 critical 与多条 major 都是"参数恰好避开了失败格子"。
- **C · 声称先门后文。** README/reports 里任何带 ✔ 的句子、docstring 里的任何性质陈述，都要指向一个以该声称命名的测试；
  指不出来就不写。
- **D · 里程碑的绿以新鲜 git worktree 为准，主树的绿不算数。** 每个里程碑收尾、每次合并之后，在新建的 worktree
  （或全新克隆）里跑全套，必须全绿。缘由（cc5d7cf）：10 个 Phase 0 夹具入库时被系统级 `core.autocrlf=true`
  规范成 LF，而 `fixtures/PROVENANCE.json` 记的是 CRLF 原件的哈希；主树的工作副本还是 CRLF、git 的 stat 缓存让
  `git status` 显示干净，所以溯源门只在这台机器的主树上是绿的，GitHub 克隆下来自己的溯源门就是红的。
  09-21 的六路审查全在主树里跑，一路都没发现。现在仓库有 `.gitattributes`（`* -text`）并在本地设 `core.autocrlf=false`。
- **E · 镜像/中心对称位形会藏住符号错误。** 凡涉及力矩、参考点、法向朝向、接触侧的门，参数化必须含一个
  **非对称参考点**（或打破对称的位形）。缘由（b26d7f5）：cb2 的四个接触点关于原点中心对称，"接触列力矩反号"
  与"接触列忘减参考点"两种缺陷在原点取对称中心时不可见；
  `tests/test_end_to_end_cb2.py::test_capacity_is_independent_of_the_moment_reference_point`
  把原点挪到 (5,−3,2)、(−0.7,0.4,−11) 后两种变异都报红。
- **G6 · 独立对抗审查是里程碑唯一的退出门。** 每个里程碑收尾跑一次与 09-21 同构的六路审查，
  **0 critical、0 major 才算过**；声称在 G6 之后才许进 README。"测试全绿"不是退出判据。

## 3. 数值纪律（从 bdda2 继承）

- 标量泛型 `S ∈ {float, Dual}`：`val()` 只用于择支（开闭判定、主元、钳位），`is_exact_zero()` 看**全部**通道后才可跳过恒等更新；**禁止 `!= 0` 零跳过**（会静默丢导数，任何门都抓不到）。
- 判据函数（primal-only）与本构函数（dual-through）在**签名上区分**。
- （2026-09-24 补）**`Dual` 没有隐式 float 转换**：`float(d)`、`math.sin(d)` 等 `math.*`、`%` 格式化一律抛 TypeError，
  响亮地失败，不再静默丢导数。择支用 `val()`，算术用 `eab.dual.sin / cos / sqrt / atan2`。
  `Dual ** p` 在负底且 p 非整数时抛错（不再返回复数）；`atan2` 两个参数的导数通道宽度不同时抛错（不再静默截断）。
  缘由：`Dual.__float__` 曾让 `math.sin(Dual)` 静默降成 float，`osteomorphic_block_generic` 默认 `sin_fn=math.sin`，
  不传 `sin_fn` 时 ∂h/∂phase 被清零而数值逐位不变，任何值门都抓不到。
  门：`tests/test_dual.py` 的 `test_implicit_float_conversion_of_a_dual_is_a_type_error`、
  `test_percent_formatting_of_a_dual_is_a_type_error`、`test_pow_of_a_negative_base_to_a_fractional_power_is_an_error`、
  `test_atan2_width_mismatch_is_an_error`；`tests/test_interlock_sensitivity.py::test_generic_block_default_sin_keeps_the_phase_derivative`。
- （2026-09-24 补）**LP 求解器：要么答对，要么抛 RuntimeError，绝不静默给错。** 显式传很紧的 `lp_tol` 时允许抛错；
  默认容差下审查算例必须答出来。门：`tests/test_lp_fail_loud.py`（8376ec2，直接进 main、未经独立复核，待 G6）。
- 浮点运算次序即契约；批量改文本以保留换行符方式读写（`newline=''`）。
- 阈值先测后钉；产物自报口径（`source`/`observable` 字段）。

## 4. 术语（与设计文档一致）

- **盖 cover**：∂E(A,B) 的一片，带模态标签（谁碰谁）。类型枚举见 `src/eab/contact_record.py::CoverType`。
- **首入 first entrance**：集值点上的确定性裁决。
- **ContactRecord**：六种现有表示的公共语言，字段按生命周期分四组（身份 / 步内冻结 / 状态 / 转移）。
