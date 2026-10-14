# M4c 独立核心审查：运动首入与 fast PD_closed

日期：2026-10-14。审查者未参与被审两个模块的实现；只读检查生产代码、理论和门，额外程序只写本树证据目录。不运行外树程序，不修改生产代码/测试，不进行 Git 状态变更。

## 1. 结论与边界

本次 **R1 理论/域/代数数、R2 退化/并列/不变性、R3 fast PD 外侧覆盖/剪枝** 范围内：**0 critical、0 major、0 未关闭 minor**；曾发现的 1 项 minor 已由实现者修复并独立复核。最终新哈希下额外探针全部重跑通过，现有三组组件门 `70 passed in 1.19s`。这是局部独立对抗审查，不是全仓六路 G6、全时程台账验收或物理替换批准。

公共数值类字符串比较问题的原始证据与修复复核见 §4；不能把声明的数值类型合同外推为“任意 Python 对象 equality/hash 合同已证”。非零残差首盖稳定性证书、单环输入的适用域与事后弦轨迹限制仍依设计/主报告披露，审查通过不扩展这些边界。

## 2. 中断恢复与执行证据

所有者报告了约 08:53 和 09:16 的中断、10:37 重启。恢复时检查 `tmp/review_probe` 不存在，未发现可沿用的该审查旧探针/完整结果；本审查未拼接或引用中断结果。初轮新审查位于 `tmp/review_probe_r3`。随后主执行者作废 full_r2，实施 equality 修复并启动 full_r3；本审查据此在**新核心哈希下重新完整执行**所有 750 条探针、比较协议复核和 70 门，不沿用旧版本结果。最终可提交、可复跑文件位于 [review_probes](review_probes/)，每组探针落盘进度，最终 `complete=true`，审查输入起止 SHA256 相同。

- [完整额外探针](review_probes/probe_kernel_pd.py)；[750 条结果及起止哈希](review_probes/probe_results.json)。一次完整最终运行 1.820 秒。
- [组件复跑脚本](review_probes/run_components.py)；[执行元数据](review_probes/component_run.json)；[原始 stdout](review_probes/component_stdout.txt)。退出码 0；70 个组件门，0 skip，墙钟 2.095 秒。
- [minor 修复复核及原缺陷变异](review_probes/probe_equality.py)；[复核结果](review_probes/equality_probe.json)。
- [机器可读审查结论](review_kernel_pd.json) 绑定当前源文件及上述证据的哈希。

运行使用 `PYTHONDONTWRITEBYTECODE=1 python -X utf8`，TEMP/TMP 指向本树 `M4c_evidence/tmp/review_probe_r4`；可提交探针文件均小于 1 MB（最大结果文件约 125 KB）。没有启动全套。可重跑命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/M4c_evidence/review_probes/probe_kernel_pd.py
python -X utf8 reports/codex/M4c_evidence/review_probes/probe_equality.py
python -X utf8 reports/codex/M4c_evidence/review_probes/run_components.py
```

## 3. 三个主题的检查与结果

### R1：理论完备性、域验证和零容差代数数

1. 阅读 T1–T3：在**每个 s 都是简单非退化单环、顶点连续线性运动**的条件下，紧性保证首次接触存在；首接触不可能仅为内点或稳定横交，只能包含顶点—闭边事件。共线持久事件另枚举闭段成员条件根，未被跳过。证明是数学论证，不是实现形式验证。
2. `_validated_motion` 在整段检查零边与非关联顶点—边事件，不仅校验两端；发生翻折/失域即响亮拒绝，不能被扫掠包围盒或初态重叠提前放过。额外 2 个两端有效但中途失效算例均正确报错。
3. 代数数使用最小多项式及根支辨识相等，异域根用有理隔离比较；多项式符号按最小多项式约化后作有符号平方比较，没有 epsilon。另测常数项相差 `2^-1000` 的两正根，精确严格序保持正确。
4. 100 个独立仿射撞水平墙闭式算例：首时刻取两个底顶点的有理零点最小值，包含等时并列，无生产事件/几何原语参与预期值构造，0 失配。
5. 9 个独立二次事件族：A 的顶点为 `(v*s,0)`，B 下边图为 `y=h-k*s*(x+1)/2`，从而首事件满足 `v*s²+s-2*h/k=0`；其余顶点严格处于下边以下，排除了先接触竞争者。变化 v/h 后精确多项式、根支/有理根及特征均一致，0 失配。

### R2：一般路径、平移退化、并列与协变

1. 代码没有直接转发 M3 的纯平移捷径，平移输入仍穿过同一事件根与特征枚举路径。
2. 新增 5×5=25 组不同形状的 M3 对照，包括凹 L、凹槽、共线细分边与三角形；精确时间与闭盖集合全部相等，0 失配。M3 是一致性对照，**不算独立几何 oracle**。
3. 以上每组再作两种有理旋转、`1e-9` 单位缩放、`(1e6,-2e6)` 大平移，共 50 次协变检查，时间、完整 features、完整 incidences 均不变。比较集合/完整元组，不只挑一个代表。
4. 已存在组件门还覆盖 M2 展开后的 FF 并列标签、紧配初态实体/拓扑区别、擦触、闭窗口端点、顺时针原编号、三档数值显示、真实内部错误根/开端点/丢并列/绕开线性事件四类变异。此次确实执行这批门；不能据此声称穷尽所有简单多边形轨迹。

### R3：fast PD_closed 外侧区间与严格 tie 剪枝

1. 在 CCW 全维凸胞边上，对外法向侧的覆盖和只沿边的闭包含必须区分。平行支撑处的外侧符号分支正确保留了此区分；对有限端点先处理正长度开段、最后取闭包，不能把单个余点当外露边。有限全维凸胞并的边界由外露边闭包构成，推理与所用输入域相符。
2. 使用整个原边的最近距离作下界有效；剪枝条件严格 `bound > best` 而非 `>=`，可保留不同等距最优点。
3. 主要新增独立 oracle 是**矩形并集网格占据**：坐标分格后以相邻格占据 XOR 找边界，以逐坐标钳位求点距；不调用被测 cross/dot/clip/三角剖分/边界/点段距离/法锥原语。204 个矩形并集×3 查询=612 次精确平方距离和完整最优点集合比较，0 失配。
4. 612 次含显式带孔并集、仅点接触、两侧内缝、整个胞被遮盖、边界查询及随机多胞。它是内部有限胞并算法的白盒压力测试：通过向真实 `GlobalEntrance2` 对象置入合法 CCW 矩形胞调用公开 query；**不声称每个任意矩形并都能表示单环 A/B 的 E**。真实 A/B 通道另由现有 70 门中的 M3/矩形/紧缝门校验。
5. 既有“忽略闭外侧覆盖”和“等下界也剪枝”内部变异门此次执行通过，断言分别看护内缝 PD 与四向完整最优点，不是碰巧弄红其他断言。

### 独立性清单

额外 PD 几何 oracle 和仿射撞墙 oracle 只使用 `fractions.Fraction`、Python 基础容器/整数算术；二次族另使用标准库 `math.isqrt` 判别有理根。探针脚本为调用被测对象导入 `motion_first_entrance`、`QuadraticTime`、`shortest_exit_fast`；为**另标的一致性通道**导入 `GlobalEntrance2` 和 `g0_oracle.on_segment`。这些生产/旧 oracle 导入不参与上述主要独立预期值的几何构造。JSON 明确区分 independent 与 consistency 计数。

## 4. 已关闭 minor：字符串 equality 与 hash 不相容

原版本位置：`src/eab/kernel2d/motion.py:72–83`，`QuadraticTime.__eq__` 尝试 `Fraction(other)`，允许字符串被当作数值相等对象。下列是**原缺陷复现**，不是最终版本行为：

```python
value = QuadraticTime(Fraction(1, 4))
value == '1/4'                       # True
hash(value) == hash('1/4')           # False（本次复现）
len({value, '1/4'})                  # 2
```

原影响：对字符串混用的集合/字典，违反“相等对象同 hash”的一般 Python 数值类型预期；数值几何路径不触发，因此最初定 minor。实现者随后将比较域限定为 int（含 bool）、Fraction 与有限 float，文本/其他类型不再强制解析；排序遇不支持类型/非有限值响亮报错，构造器仍拒绝 bool。

独立复核最终版本：原复现的 `value == '1/4'` 已为 False；10 个数值等价对的双向 equality、hash、集合和字典查找正确；7 类不支持比较输入、正反向排序、2 个 bool 构造拒绝均符合合同；`Fraction(1,10)` 不与 binary64 `0.1` 冒充精确相等。随后在内存内将 `__eq__` 重新注入原缺陷，专用门确实红在 `parseable text must not be numeric equality`，恢复后再次绿。生产文件未由审查者修改。结论：**M4C-KPD-MINOR-01 已修复并独立关闭**。

## 5. 被审版本

| 文件 | SHA256 |
|---|---|
| `src/eab/kernel2d/motion.py` | `066c29ef0c9b8e5dd73661a4b562788561fc6380d0ac37c4a3719c4005d18e69` |
| `src/eab/kernel2d/motion_exit.py` | `00119fd6d1b6a40b889d2e80d8357e8236caa77ed890c9c05361c847e46d40a1` |

理论与三组测试文件的起止哈希见机器 JSON。此审查不覆盖 replay 的 CSV/快照 fail-closed 协议、1810 步台账数字和全套节点集合；应由其专门审查/最终完成证据负责。
