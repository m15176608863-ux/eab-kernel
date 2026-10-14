# WO-M4c-fix：验收遗留补门与整理

日期：2026-10-14；起点 `codex-work @ 2a7f4d0e46444268401d4851d67ae6edb2c7dd2c`，初始工作树干净。
本单仅补验收遗留，不重开 M4c 范围，不宣称新的 G6 或在线替换批准。

## 1. 逐条处置

| 工单 | 处置与可复核证据 |
|---|---|
| 1 二次重根切触 | 新三角形见证的顶点到运动边有向高度为 `(s-1/2)^2`，只有 `s=1/2` 闭集接触；精确时刻、初态 -1、状态 contact、关联与盖全集均断言为 `VE(0,2)`。独立半平面证明及 G0 前后实体分离。见 [语义门](../../tests/test_m4c_fix_semantics.py)。 |
| 2 PD 全并列并集 | 正方形叠正方形的四个并列最近位移，断言全部 24 个闭盖特征及 raw/post 的 `INITIAL_OVERLAP_PD_MATCH`，不依赖冻结哈希。见 [回放补门](../../tests/test_m4c_fix_replay.py)。 |
| 3 纯 EV 首入 | 单位正方形不动，三角形 `((1/2,2),(7/10,3),(3/10,3))` 竖直下降 2；精确首入 `s=1/2`、唯一关联与盖 `EV(2,0)`。闭式高度及独立 G0 三态佐证。 |
| 4 独立随机差分 | 固定种子 20261014；108 个随机、15 个结构输入，共 123 例。完整比较精确时刻证书、初态、状态、全部关联和盖。63 凹形、11 无理首入、18 多盖并列；1113 个开放事件段各两个有理 G0 三态检查，段三态计数 -1:718 / 0:3 / 1:392。见 [方法与复跑](M4c_evidence/fix_differential/README.md)、[精确输入及分段证据](M4c_evidence/fix_differential/cases.json)。 |
| 5 哈希范围与平台 | 从原 46 文件收窄为实际回放的 23 文件本仓 import 闭包，含 package initializer 及函数内静态 imports，键为 `as_posix()`。AST 门独立重建闭包；实际加载模块也核对无遗漏。无关 LP/3D 文件不再触发冻结重跑。完整从头重跑 450 帧，不拼接。 |
| 6 VV 第二参考 | 只读核对 `D:/b-DDA/bdda2/core/contacts.hpp:80`，`has_second(k)` 为 `m4_[k] > 0`。回放改用同一规则；m5=0、m6=0 两格保留次参考，m4=0 不保留。有旧判定的内部编译变异门。源文件 SHA 见 [核对证据](M4c_evidence/fix_replay/verification.json)。 |
| 7 理论与口径 | [设计 §2 T2a](../../docs/m4c_motion_entrance_design.md) 补首次失去简单性、相邻回折较短边远端证人、面积零不简单的论证；[台账](../../docs/m4c_difference_ledger.md) 明确整步域约束保守拒答，域外不等于首入不存在。1810 步域外计数见下文。原报告“最小同盖异时身份”补明按 case/step/pair 字典序选取，不是时刻差最小。 |
| 8 历史与 Temp | 旧 pilot、变异 r1–r5、两次基线和旧冻结等添加/补充作废或被取代标记，历史不删除。逐字节扫描查到 8 个全 NUL 文件及 1 个截断 gzip，逐一记路径/大小/SHA/原因。见 [完整性扫描](M4c_evidence/fix_history_integrity.json)。[环境偏差](M4c_evidence/environment_deviations.json) 补上 Claude 提供的精确范围。 |

### 独立 oracle 边界

[独立 oracle](../../tests/m4c_independent_oracle.py) 的直接 import 清单仅为
`dataclasses.dataclass`、`fractions.Fraction`、`math.isqrt/lcm`、`eab.kernel2d.g0_oracle.overlap`。
自写二次实代数数及根排序；面积三点插值建立事件超集，代数坐标闭段与邻点半平面独立重建关联/盖。
`motion.py` 只由测试驱动作为被测对象导入，不被 oracle 导入或调用。
随机运动为各块独立的保向仿射非平移（行列式沿步有正下界），不是对任意逐顶点形变的穷尽证明。
另一个代理只读复核并在禁用生产 motion 函数后完成独立计算；[复核记录](M4c_evidence/fix_semantics/differential_review.json)。

## 2. 内部变异：必须红在新语义断言

| 内部改动（compile 进被测函数） | 控制 | 指定变异红断言 | 恢复 |
|---|---|---|---|
| `_roots` 二次判别式 `< 0` 改 `<= 0`，漏掉重根 | 绿 | `quadratic double-root grazing contact time` | 绿 |
| `_pd` 的 `tied_exact_points` 改 `tied_exact_points[:1]` | 绿 | PD 全并列特征并集及类别两条新断言，分别核验 | 绿 |
| `motion_first_entrance` 事件循环移除 `(b,a)` | 绿 | `pure EV first-contact time` | 绿 |
| VV 第二参考回退 `all(m4,m5,m6)` | 绿 | `m5/m6 vertex zero must not suppress VV second reference` | 绿 |

没有在产出后追加假数据，没有用源码哈希失败替代语义失败。
实际断言 traceback、编译源码位置和哈希见 [切触/EV 变异证据](M4c_evidence/fix_semantics/mutation_evidence.json)
与 [PD/VV 证据](M4c_evidence/fix_replay/verification.json)。

## 3. 冻结从头重跑及前后差异

新批次 [fix_frozen_replay](M4c_evidence/fix_frozen_replay/)：15 例 × 30 帧 = **450**，无 PD 工作量截断，
从头完整执行，用时 **177.274538 s**。随后逐例复验输入、端点、audit、gzip、逐帧哈希与计数守恒。
[复验](M4c_evidence/fix_frozen_revalidation.json)、[前后对照](M4c_evidence/fix_freeze_comparison.json)。

- 主参考分类计数、次参考分类计数、stats：全部不变。
- 15 例逐帧摘要、frame-list SHA、normalized gzip SHA：全部不变。
- raw/post VV 次参考各 **1468 → 1468**。
- 仅源码绑定范围/键、冻结产物路径与源审计元数据变化；`expected.json` 指向新批次。
- 中央 `fixtures/PROVENANCE.json` 只更新 `m4c_motion/expected.json` 一条，其他登记保持不变。
- 1810 步另逐行核查新旧 VV 存在性规则，差异行 **0**，raw/post 各 **7768 → 7768**；
  因此无影响已验收全时程计数的变化，不把本次域审计冒称又重跑了全 1810 步 PD。

## 4. 整步域的保守拒答统计

[域审计](M4c_evidence/fix_domain_audit.json) 消费原完整批次绑定的本仓复制输入，
逐顶点核对全部帧与末端 CSV，再对每个块运行全 `[0,1]` 域合同，包括被扫掠盒排除的远块对。
合计 **1810 步、15220 个步—块、64010 个步—无序块对**。

- 整步域外步—块对：**0**。
- 因“首入以后才退化”而保守拒答的步—块对：**0**（总域外为零，故其子集也为零）。
- 域外不是无接触；若有非零拒答，应另求退化前前缀的首入，不能直接计作无接触。本批无需此补算。
- “同盖异时最小身份” `bb03 / step1 / [1,2]` 是 **case/step/pair 字典序最小**，不是时刻差最小。

## 5. 验证记录与限制

首轮全套 `fix_final_suite` 启动后，补充的定向静态检查发现新测试脚手架 44 条违例；
该轮已停止并 [整批作废](M4c_evidence/fix_final_suite/INVALIDATED.json)，不复用任何分片结果。
修复仅把反射/编译/路径扫描脚手架按既有约定放入 `test_` 驱动，不修改静态门、不加豁免。

最终 [四片批次](M4c_evidence/fix_final_suite_r2/summary.json) 由第二个全新字节副本从头执行，全部 GREEN。
四片最后一行原样如下（顺序 1–4）：

```text
3278 passed in 764.74s (0:12:44)
3278 passed in 731.08s (0:12:11)
3277 passed in 761.73s (0:12:41)
3277 passed in 1283.98s (0:21:23)
```

[独立节点与源码复核](M4c_evidence/fix_final_verification.json)：收集 = 执行 = 唯一节点 **13110**，四片互不重叠，**0 failed / 0 skip**；
新增门共 **136** 节点。全套墙钟 **1410.660011 s**。
全仓静态门原样：`exact construction AST gate: 0 violation(s)`。
[静态策略字节核对](M4c_evidence/fix_static_policy_integrity.json)：扫描器、封闭子集策略与 JSON 均未修改，登记豁免 **3103 → 3103**，新增 **0**。

独立差分门本轮 124 节点合计 call **1.369220 s**；全套 call 合计 **3293.264290 s**，同轮比例 **0.0416%**，低于约 1% 预算。
这比较的是节点调用时间之和，不把四片之和冒充墙钟。
新鲜副本中的 **486** 个 src/tests/tools/fixtures 文件逐字节哈希与交付树一致；报告和证据索引另作本地链接与编码检查。
完整新增/修改文件入口见 [交付索引](M4c_evidence/M4c_fix_delivery_index.md)。

运行约束：pytest 均使用 `-p no:cacheprovider` 与显式 `--basetemp`，TEMP/TMP 在本仓
`reports/codex/M4c_evidence/tmp/` 子目录；只读姊妹源码，不运行姊妹程序，不作 Git 写操作。
新鲜验证副本是本树 tmp 内按字节导出，不是新鲜 Git worktree；本单禁止 worktree，未冒称满足那一退出条件。
系统 Temp 的三旧目录/83 文件/533,021 字节是 **Claude 验收侧提供的历史审计事实**，并非本单对已删除文件的现场重计。
约 09:10、09:13、10:43 的写入均来自旧 `tests/test_m4c_replay.py` 的 `tmp_path`；后由验收侧并发全套触发 pytest 轮换删除。
本单未在树外清理。历史完整批次仍保留原适用范围；本报告不借补门扩充物理模型或在线检测承诺。

M4cFIX_DONE
