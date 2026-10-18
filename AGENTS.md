# AGENTS.md — eab 接触引擎常驻纪律

本仓库实现域无关接触引擎；Python 版是参照实现兼裁判，C++ 引擎 eab2 规划中。它是石根华入口块理论的一份独立实现，不作实现优先性或姊妹对账通道序数宣传。原文归属见 [归属总表](docs/shi_attribution.md)，二手正本订正见 [勘误](docs/canon_errata_20261019.md)。
设计正本 `D:/E(A, B)/07 程序设计·统一接触内核方案.md` 只读；旧纪律及事故叙事完整保存在 [历史副本](docs/history/AGENTS_through_20261019.md)，不再反复堆进当前入口。

## 1. 范围与只读红线

1. **零姊妹代码依赖**：`src/eab` 不导入 `D:/b-DDA`、`C:/3DDA`、`D:/3-b-dda` 或导师 DDA4.x。对账只读导出文件；入库 `fixtures/` 后回归不依赖任何姊妹 exe 或源码。
2. **姊妹仓库只读**：不写、不删、不作 Git 操作。确需新导出时，在本仓库 `tools/` 写编排，把 exe 与输入复制到获准 scratch 沙箱运行，再复制产物到 `fixtures/`。姊妹缺陷只记 `docs/sibling_observations.md`。
3. **影子边界**：本仓库的几何结果不等于姊妹力学轨迹等价；切换开关与现有求解器修改只能由各线所有者决定。
4. **按工单限定写域**：不擅自 commit / push / reset / checkout / stash / worktree / branch；需要新鲜树验证时由所有者安排，未经执行不得宣称已做。
5. **文件交付**：凡生成、修改、导出、归档的文件或目录，回复给可点击 Markdown 链接；Windows 使用 `file:///D:/...`。多项列关键 3–8 链接，其余给清单链接。

## 2. 内核纯度与分层

**内核范围**：`src/eab/` 下的 `predicates`、`construction`、`numeric_domain`、`rational3`、`dual`、`lp`、`margin`、`limit`、`limit_multi`、`oracle_construction`、`kernel2d`、`kernel3d` 及其全部子模块。

- 内核不得出现域语义标识符或非 docstring 字符串：DDA/BDDA/TIA/TF、岩石/节理，以及 legacy 接触表语义（`mtype`、`m4/m6` 槽位、`df04/df05/df06/df07`、`out.csv` 的 z 格式）。docstring 可以把 DDA 作为适配器示例提及。
- 纯度门 `tests/test_kernel_purity.py` 按下划线、驼峰与大小写不敏感切词，保留字母数字串，并检查复数、小写拼接、bytes 常量与模块路径；起始禁词至少为 `dda bdda tia tf rock joint mtype df04 df05 df06 df07`，增补 `legacy zsto lock_second bolt m4 m6 csv slot tuple7 岩体 围岩 断层 岩爆`；只可增补，不可删减。词法扫描同时包含每次内核导入执行的 `eab/__init__.py`、`contact_record.py`、`numeric_decode.py`，不作整模块豁免。
- 窄白名单及理由随门保存：`contact_record` 的现有 `joint_material` 仅允许记录字段与解码键两个 AST 站点（保留序列化合同，不是引擎码）；`dataclass(slots=...)` 仅属语言关键字；`initial/partial/potential/spatial/tangential/exponential/differential` 等普通数学词不因含 `tia` 子串误报。白名单不豁免同名新增变量或字符串。
- 内核的静态 import 图不得到达 `eab.adapters` / `eab.readers`。禁止在旧内核位置留下导入适配器的兼容转发模块；调用方和测试使用新路径。
- L5 域问题放在 `adapters/`：TIA 逃逸/剪胀剖面、各引擎状态码和接触表映射、DDA 锚定与 z/槽位解析。通用路径代数、精确几何和证书数学留在内核。
- `contact_record.py` 只留域无关枚举与记录；适配器消费契约，不把引擎码倒灌进公共契约。
- 新路径守**同构语义门**而不是逐字节/盖枚举序门；原 legacy 的候选序、平局序、匹配序属于适配器解释。

## 3. 验证与成本

- 日常改动跑快档：`python tools/h1_run_gates.py --name <新的快档名>`；也可用 `python -m pytest -q -p no:cacheprovider --basetemp <本单证据目录>/tmp/pytest_fast`。默认不执行 `slow`；目标单进程约 5 分钟以内，每个 `src/eab` 模块至少由一个快档测试导入并执行。
- 全档包含快档和慢档：`python tools/h1_run_gates.py --name final --runslow`，由运行器固定四分片；普通 pytest 的 `--runslow` 同样包含快慢全档；单跑慢档时 `-m slow` 必须配 `--runslow`（否则默认过滤后可能收集为 0），且不能代替快慢全档；执行节点多重集合必须等于收集节点，0 skip、0 failed。
- 带逐模块实际执行核对的 H1 运行器需 Python 3.12+；缺少运行时监测能力必须失败，不得伪报覆盖。
- pytest 均禁 cacheprovider 并显式指定 basetemp。运行器把 TEMP/TMP 指向本单证据 tmp；测试本身不得依赖 TEMP 的具体位置。
- **成本上限**：一单一线；长跑先估时。全档只在开工基线与收尾各跑一次，中间用定向门；禁止为文档整理重算全量冻结证据或全量回放。运行被中断则该次作废重跑，不拼接日志。超过工单时间预算按 PARTIAL 明列未完成项。
- **静态构造准入冻结**：工具继续跑且保持 0 违例；H1 起不新增准入。搬家只机械重键，须证明旧新键一一对应、同一 AST 站点与同一函数源码、仅模块路径变化，条目总数不变，保存脚本与映射。静态零诊断不是数值安全证明。
- **冻结证据不钉当前源码**：保存数据、产生它的 Git 提交号与工具版本；回归用固定小子集实际重跑比较状态、标签、精确时间和计数。不准仅改记录哈希让搬家过门。数据文件的完整性哈希与来源元数据仍保留。
- 测试输入放 `fixtures/` 或 `tests/data/`；大型历史证据放仓库外，映射及逐文件 SHA256 见 `reports/EVIDENCE_ARCHIVE.md`。被跟踪单文件不得超过 1 MB，明确理由的允许列表除外。
- 阶段门保留 G0 独立自证、G1 二维同构、G2 三维同构、G3 对偶、G4 活动集、G5 差异台账。
- **门要有牙**：缺陷须注入被测代码内部，不得在产出后追加假数据；确认是守护目标缺陷的语义断言报红，不是源码哈希或偶然解序。参数化门另核产物互异。

## 4. A–F 实质纪律与里程碑核查

- **A · oracle 独立**：G0 类门的 docstring 写出 oracle 的原语及与被测对象不重合之处；共用生产几何原语的对照只能作佐证，不能当主 oracle。
- **B · 参数化覆盖**：至少一个分界点、一个非对称/一般位置输入、一个尺度变化输入；荷载与几何各自缩放，不以原点轴对齐的整齐格子代替覆盖。
- **C · 先门后文**：README/reports 的已证/已实现性质陈述与 docstring 性质声明须指向具名测试；指不出就不写。README 的“已证明清单”只收有门守护的命题；无门命题只能进入“未证明 / 无门”栏，或在归属/证明表明确记“无门”，不得强凑手算算例作生产门。有限测试不冒充全输入域证明。
- **D · 新鲜树可复现**：里程碑和合并后的最终绿须由所有者安排的新鲜 worktree/克隆核验；主树绿不能代替。工单禁止 Git 写时不自行建树，准确记录实际采用的字节副本/导出及其局限。保持 `.gitattributes` 与 `core.autocrlf=false` 的字节合同，不擅改设置。
- **E · 打破对称**：力矩、参考点、法向和接触侧门必须含非对称参考点或位形；非对称要落在 LP **实际使用**的参考点上。接触形心求解时需整体平移使形心离开原点，并用独立构造列核平衡。
- **F · 刚体与单位元门**：每个几何/力学 API 覆盖随机旋转、大平移（|t|∈{0,1e3,1e5}；三维另含 1e6）及单位缩放；距离按 s、承载比/状态不变、标签一致置换；另覆盖特征尺度远小于坐标量级的输入。具名元门：`tests/test_invariance_geom.py`、`tests/test_invariance_2d.py`、`tests/test_invariance_limit.py`、`tests/test_invariance_interlock.py`；分辨率角落门：`tests/test_margin_resolution.py`。
  - 阈值只能为 `max(问题尺度相对量, 舍入量级噪声量)`，不得用无关绝对数、条件数 κ 膨胀量或跨行全局噪声吞掉小尺度真信号。
  - 必须可证正确的小规模判定采用浮点候选 + 原始数据有理精确核验，派生量亦精确；阈值修补经两轮仍静默错时改策略，不无限加容差。
- **里程碑对抗核查**：旧 G6 多路复审制退役；每个里程碑由 Claude 安排**一路**独立对抗核查。测试全绿本身不替代核查；核查 0 critical、0 major 才默认退出，若所有者另定例外须单独记录，不冒称核查通过或自动升级声称。

## 5. 数值合同（不得因搬家改变）

- 泛型标量 `S∈{float,Dual}`：`val()` 只用于择支；仅 `is_exact_zero()` 检查全部通道后可跳过恒等更新。禁止用 `!=0` 作零跳过而丢导数。
- 判据（primal-only）与本构（dual-through）在签名区分。`Dual` 无隐式 float 转换，`float(d)`、`math.*(d)`、`%` 数值格式化抛 TypeError；用 `eab.dual.sin/cos/sqrt/atan2` 做泛型算术。
- `Dual**p` 的负底非整数幂报错；`atan2` 导数宽度不等报错，不截断。门见 `tests/test_dual.py` 四项转换/幂/宽度门及 `tests/test_interlock_sensitivity.py::test_generic_block_default_sin_keeps_the_phase_derivative`。
- **LP 对给定数据精确成立**：浮点只给状态/基候选；有理层在原始模型核最优（原/对偶可行）、无界（可行 + 下降射线）、不可行（Farkas）证书，未通过则有理单纯形继续。数值失败只算无候选。力矩、荷载平移、黏聚上限等派生量经 `lp.solve(..., exact=)` 精确提供。门 `tests/test_lp_certificates.py` 包含浮点说谎注入。
- 浮点运算次序即合同；读取已有文件后再编辑，UTF-8 无 BOM、不混换行，批量编辑用 `newline=''`。不覆盖无关用户修改。
- **阈值先测后钉**；输出自报 `source`/`observable`；精确证书与浮点显示分层，不拿显示舍入结果再当原证书。

## 6. 术语与归属

- **盖 cover**：带模态标签的接触候选片；一般凹块未裁剪盖可落在 E 内部，不能一概称为 ∂E 的一片。凸等号、一般包含及裁剪前提见 [归属总表](docs/shi_attribution.md)。
- **首入 first entrance**：参考点从 E 外首次到达 ∂E 的事件（2015 摘要第 (2) 条、§10、§13）；本仓库沿运动方向精确计算并报出全部并列；原文没有选一个的规则。
- **ContactRecord**：域无关公共记录，字段按生命周期分身份、步内冻结、状态、转移；各引擎码和表槽位留在适配器。
