# INT1 第 5 项：仿射理论订正与作者自检查

## 范围与证据边界

- 本项仅修改 [docs/m5a2_affine_theory.md](file:///D:/eab-wt/cx-m4/docs/m5a2_affine_theory.md)；不改生产几何代码、不改历史冻结仿射摘要、不运行 b-DDA、不写姊妹树。
- 基线回退锚为本单新鲜字节副本中的同名文档；仓库原始提交为 f012d6a。本项未执行任何 Git 写操作。
- [机器核对清单](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/theory_work.json) 是作者自检查，不冒充独立 G6 审查。

## 逐项订正

| 要求 | 修改与核对 |
|---|---|
| 内部 d、θ、E 是否可取得 | `driver/main.cpp:76–81` 明确逐步逐块以 %.17g 输出 z1..z6。15 份 out.csv 按 M4c 既有清单复核 SHA256，全部匹配，15220 行。 |
| 从 M 恢复 θ、E | 给出反对称部分的 arcsin 公式、对称 E 与换心后的 d。明确必须固定小转角分支，不能作全局唯一性宣传；数据最大 `abs(z3)` 为 0.005010522223188364。带舍入的拟合 M 只定义拟合参数，不是原 z 逐位恢复。 |
| 端点定量结论 | 15220 端点、误差 ≤1.101 个舍入单位注明来自 WO-INT1 §5 的 Claude 验收；本次未独立复现该重建，未偷换成 coordinate×2^-52 口径。 |
| 轨迹不等价 | 新列顶点均值 vs 面积形心 cent_prev；区分半角时间律、补偿矩阵、换中心以及 DDA 参数化插值。中点最大约 2.8×10⁻⁶ 引用同一 Claude 验收，不冒称全时段上确界。 |
| 次数 | 以 QᵀQ=D²I、det Q=D² 对叉积和点积统一证明分子整除 D_B；一般约消后 ≤6，刚体 ≤5。u_B=0 单独计数，避免按二次因子错误减阶。退出条件改六次实根隔离。 |
| 三角形 | 从冻结 r4 的 15 个原始 gz 表独立重新分组：500 零残差全部且恰好是三角形，bb03/05/06 各100、bb09 200。单列三角形并增加剔除后的14720块帧分布。 |
| r4 | 只读 cx-e2 的 affine_full_r4/summary.json 与入库摘要逐字节一致；秒数 50.122772900009295，不再写 r3/50.01。未在集成树重新执行1810步仿射全程。 |
| 仿射变异门 | §8增加本次 pytest 三项内部变异的精确函数/参数名以及 L∞ vs L1 的新门指针。 |

## 独立输入重聚合（非生产重算）

[theory_data_audit.json](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/theory_data_audit.json) 保存 15 个原始 gz 的路径/哈希、顶点数×零残差分布、15 份 out.csv 的路径/哈希/行数及 z3 最大值，以及只读 b-DDA 三份相关源码的哈希。

读取原始表前逐一核对 `full_rows_sha256`；r4 总摘要与当前入库仿射摘要逐字节相等。使用 Fraction 解析 `delta_affine` 并按冻结工具的 `floor((n−1)q)` 规则重新取分位数。排除三角形后：中位数 5.1957164445665864e-14，P95 1.6208974370532298e-13，最大值 2.5881961360763425e-13。JSON 同时保存精确有理值，未只保留显示数。

## 证明的有限精确系数交叉检查

[theory_polynomial_probe.json](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/theory_polynomial_probe.json)：纯标准库、自写多项式系数运算、无 eab import；固定 seed 20261015。一般仿射（含逐顶点残差）720 格、刚体720格，共1440格，覆盖两个边端点、叉积/投影点积、u_B=0、正负角度和非对称平移。

每格断言 D_B 整除余式为零、约消式逐系数恒等、次数不越界；观察到一般6次与刚体5次各自达到上界。此有限样本检查只是正文代数证明的交叉检查，不以采样代替证明。可在当前交付工作区重跑：

```powershell
$env:TEMP = 'D:\eab-wt\cx-m4\reports\codex\INT1_evidence\tmp'
$env:TMP = $env:TEMP
python reports/codex/INT1_evidence/tmp/theory_polynomial_probe.py
```

临时探针文件在 ignored tmp，JSON 记录其 SHA256；它不进入静态准入清单，也不增加本次准入。

## 文档/历史边界

- UTF-8 无 BOM；相对链接全部存在；文档不再含“八次”；r4 秒数、三角形分层、归属声明和新 pytest 节点通过机器检查。
- `docs/` 的入站链接未发现指向本理论文档固定行号的引用；本次保留节号语义指针。
- 历史 `reports/codex/M5a2_report.md:121,246` 仍是原验收时的 ≤8/八次文字。按 root 决策，不回写已冻结历史报告；INT1 报告应明确这两处被新理论 §4/§9 订正，以免破坏旧审核哈希。
- 所有生产算法、历史仿射摘要、原始 gz 与 out.csv 未写入；全部新文件均小于1 MB。

THEORY_WORK_COMPLETE
