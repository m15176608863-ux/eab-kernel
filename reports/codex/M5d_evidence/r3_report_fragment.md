# M5d A1 / A4 交付片段

## 已验证默认门

- `41 passed in 28.71s`，0 skip；具名耗时见 `r3_pytest.log`。
- 21 个真实内部变异全部在新的具名语义 AssertionError 上判红：12 个实际几何错证反例、2 个公共证书预算合同拒签、7 个 helper 精确预算恒等式。源码哈希和冻结快照不参加判红，不能把 21 个都叫作实际错证。
- 八类主门分别是：早期全窗、EV 竞争者、两侧投影、末段、L1 对偶归一、端点扣费、边长误差预算、不等分母相对向量。
- 端点扣费与边长删项均有实际管内首时刻 `103/200 > 51/100` 的反例；边长另分 A 顶点活动和 B 边端点活动两个输入。
- 额外 `du||W||1` 和混合项仅为证明预算合同拒签，W/V 六个删项及 `ev=ew` 混用端点仅为精确预算恒等式；W/V 长度分别为 8 和 10，不计为已找到物理错签反例。
- 测试和独立 oracle 两个新文件的局部静态扫描均为 0 违例，未增加准入。
- R3 生产公式、旧 M5c R3 数值结果和共享策略未修改；整个工单另有注释订正触及回放闭包，真实重算与发布见主报告，不混称所有旧冻结文件字节未变。

## 独立 oracle 与阈值

主 oracle 只导入 Fraction、lru_cache、comb；辅助平移 oracle 只导入 Fraction。没有生产几何原语导入。每条轨迹都先独立证明初态凸包严格分离，然后用独立多项式和 Sturm 根计数核闭边入射。

默认 P2 构型的两块均有转动、平移、非零对称应变；分母为 `1+s²/100` 与 `1+s²/25`。40 次二分得到保守 rlo，不确定宽度小于边缘偏移的 1/64；在 `rlo*(1-2^-24)` 与 `rlo/2` 检查非刚体逐顶点时变扰动的首标签和首时刻开括区。有限扰动不代替全管定理。

长 runner 已从头完成六个不同名义形状和相对位置，耗时 187.43 秒（不进入默认 pytest）。四个构型在阈值边缘与半阈值处通过，每个 64 条，共 256 条时变非刚体管内轨迹，首标签及首时刻开括区双检查零失配。两个构型连零半径充分条件都未通过，单列未证，不外推。

| 名义构型 | 结果 | 扰动数 | 限制 / 拒签子条件 |
|---|---|---:|---|
| diamond | CERTIFIED | 64 | 尖菱基准 |
| asymmetric_triangle | CERTIFIED | 64 | 非对称三角形 |
| near_corner | UNPROVED | 0 | 四个缩窄括区均 `early_separation` |
| concave_notched | CERTIFIED | 64 | 简单凹环，非凸域 |
| skew_wall | CERTIFIED | 64 | 不同墙体边长与形状 |
| near_tied_tips | UNPROVED | 0 | 宽括区 `competitor_VE`，缩窄后 `early_separation` |

所有认证构型均使用 40 次有理二分，宽度 `1/8796093022208`；每项 rlo、上下界、独立名义根区间、每条扰动根区间和源码摘要均在 JSON。脚本运行首尾摘要一致，完成后再次核当前文件摘要全匹配。证据 JSON 133621 字节，未生成超过 1 MB 的交付日志。

本轮增强 runner 补强并替代 M5c 旧 D=1 审计的“本轮阈值覆盖”角色，但不改写旧脚本或冻结证据，也不声称已把旧 90 个构型全部推进到阈值边缘。

## 编码缺陷说明

原始中文草稿曾被 PowerShell 管道转成问号，独立复核发现后已重写本片段及理论文件为 UTF-8 无 BOM。理论合同在实现前已讨论并沿用既有 M5c 定理，但当前重写字节不声称先于实现。此缺陷不涉及 Python 数值源码或测试结论。

## 文件

- `docs/m5d_r3_theory.md`
- `tests/test_m5d_r3_semantics.py`
- `tests/m5d_r3_oracle.py`
- `tools/m5d_r3_evidence.py`
- `reports/codex/M5d_evidence/r3_semantic_evidence.json`
- `reports/codex/M5d_evidence/r3_pytest.log`

重跑：`python tools/m5d_r3_evidence.py --count 32`。被中断则整次作废重跑，不拼接。
