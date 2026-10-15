# M5a 理论与独立 oracle 专题复核

日期：2026-10-15。范围：`docs/m5a_se2_design.md`、`src/eab/kernel2d/{se2,algebraic}.py`、
`construction.py::scalar_algebraic`、新增 M5a 门及拟合口径。
这是一名与内核实现者分工的协作代理所做的专题检查；设计文档和独立 oracle 同由本复核者编写，
**不是完全独立的第二套理论证明，更不是六路 G6 或里程碑退出批准**。

## 1. 结论及保留意见

本次检查未发现需阻止所声明**受限模型 API**运行的 critical/major 数学错误；这不是全仓无缺陷保证。
必须保留以下范围，任何删掉限定的 README/报告句子均不在此结论内：

1. 轨迹是 `c+s*d+R(s*u)*(x-c)`，不是匀角速度，更不是从快照恢复了 b-DDA 的真实步内轨迹。
2. 每块路径限制 `|u|<=1`（最多 90°）；有限有理旋转函数/固定切片的 chart 本身可更宽，不能混淆这两个域。
3. 材料输入限单一简单环。E 可以有洞的门，不是材料多环支持。
4. `delta=0` 只认证所选刚体模型端点完全相容；不能照搬 M4c 的“相同轨迹”标签。
   非零转动下，精确刚体圆弧与端点弦即使 delta=0 也通常不同。`delta>0` 必须未认证。
5. 初贯入给出的 PD 是**步初冻结的平移** `PD_closed`，不是 SE(2) 最短逃逸，也不是轨迹脱离时刻。
6. 本单未构造全 `R²×S¹` C-障碍曲面安排；运动时刻有效局部盖不能冒称全局曲面边界完备构造。
7. 没有跨 chart、近 pi、多圈、SE(3)、一般非零残差首盖稳定性证书、真实接触力或在线替换结论。

## 2. 实际推导检查

- 核对 `M(u)^T*M(u)=(1+u²)² I` 与正行列式，轨迹端点闭合与各时刻刚体性。
- 核对双体 VE 的 F/G/H 消去分母后统一分母为 `D_A*D_B>0`，不是误乘/漏乘另一层分母；最高次数五。
- 用 `G>=0,H>=0` 核对闭段包含，恒共线改由 G/H 根和 0/1 分割，未将恒零事件忽略。
- 首次接触的紧性、内部重叠稳定性和横交稳定性论证适用于非凸简单实体；共线重叠必含端点—边见证。
- 法锥交叉积的两条旋转分母均正；顶点凸/凹/平直分类可在初始几何精确取得。
- 检查 Sturm 端点计数、平方自由化、指定公共根 gcd 判等；“有公共因子”不等于“指定根相等”。
- `RealAlgebraic` 为非最小多项式表示时不哈希，避免相等不同表示产生不一致 hash。
- 单根隔离区间中平方自由根必简单，`_bisect_root` 用符号一半选择是有效的；不会丢双重原根，因为平方自由化先保留其位置。
- Horner/Bernstein 早排除均是精确包含判据；未通过即回退 Sturm，端点零和重根不能剪除。补证在设计 §4.1。
- `scalar_algebraic` 用精确有理比较器二分 binary64 编码并比较舍入中点；没有以近似显示根参与事件排序。
- 宽阶段 `2|u|*|x-c|_1` 的逐分量界及任意固定方向投影界有直接证明，严格分离才排除，等号保留闭接触。

## 3. 主 oracle 与 import 清单

文件：[独立 helper](../../../tests/m5a_independent_oracle.py)、[门](../../../tests/test_m5a_oracle.py)。
helper 的直接 imports 为：

```text
fractions.Fraction
functools.cmp_to_key
functools.lru_cache
eab.kernel2d.g0_oracle.overlap
```

`g0_oracle.overlap` 实际调用路径为有理公共分母提升后的整数 winding/边交判据，不 import 生产事件、根、法锥、SAT、三角化。
模块加载附带 `eab.oracle_construction`（其 imports：decimal、fractions、functools、math、struct、numeric_domain），
本 helper 不调用它的显示函数，也不调用 `construction.py`。测试 wrapper 另外 import 被测 SE2 API、pytest 和 Random，
这是 SUT 包装，不属于 oracle 几何原语。

独立算法不是复用生产 F/G/H 系数：先在六个有理 s 上用两次复数乘法的 Cayley 旋转重建顶点，
直接计算几何标量，再由 Lagrange 插值恢复五次系数，并在两个额外有理 s 上逐值核对插值恒等式。
插值使用 s=0,...,5 的有理公式延拓；这是为了确定多项式系数，不表示公开路径接受 `[0,1]` 以外的时刻。
自写多项式除法、平方自由化、Sturm、gcd、根区间符号及排序；与生产实现不共用上述函数。
所有有效事件分割出的开区间都取有理点交给独立 G0，检查首接触之前为分离；不是固定时间网格近似。
根证书通过独立唯一根计数和 gcd 比较，不调用 SUT 的 `compare/sign_polynomial` 当 oracle。
完整 incidence、局部盖与 VV 并列集合也独立重建。

初次落盘审计为：[theory_oracle_audit.json](theory_oracle_audit.json)，
[对应 pytest 日志](theory_oracle_pytest.log)：15 passed in 1.90s。
12 个几何样本包括 10 个固定种子双体五次案例（含凹形），一个显式无接触例、一个精确 VV 并列例；
合计 132 个独立有理事件区间探针。后续为减小静态分析未知类型而改为等价显式 Fraction comprehension，
再次运行 15 passed in 1.87s；原 JSON 是其标明哈希时刻的快照，不冒充最终全套代码哈希。

## 4. 有牙与实际源变异

除了进程内真被测函数注入，新工具 [m5a_mutation_evidence.py](../../../tools/m5a_mutation_evidence.py)
把 src/选定测试复制到本树 tmp，每个案例先跑原副本 GREEN，再在副本的实际源码中替换唯一片段，原样运行同一语义 guard。
不选任何文件哈希门，哈希仅用于源证据；不是靠篡改产出后再追加假值。
源文件保持行尾，不改真实工作树，pytest 显式 no-cache/basetemp，TEMP/TMP 都在本树 tmp。

| 内部源变异 | 必须报红的断言 |
|---|---|
| 隔离二分位取反 | `isolation bit retains the selected root` |
| VE 只保留最后实根 | `earliest square-wall real root` |
| 判等改近似 float | `near roots are algebraically distinct` |
| 旋转 x 分量 sine 符号错 | `square-wall complete first feature` |
| 线性退化事件不求根 | `general path must retain translation events` |
| 终点只走半步 | `trajectory final endpoint closure` |
| 去掉双体事件五次项 | `independent first-root identity rejects lost degree-five term` |

首轮 [mutations_r1/summary.json](mutations_r1/summary.json) 7/7 在指定断言报红且七个对照全绿。
工具记录每个源片段前后 SHA256、原树哈希未变、完整异常行与 pytest 末行。
如源码随后调整，应再跑新目录，不得拼接本次日志；最终有效批次由主报告指明。

在 oracle 显式 Fraction 类型整理和随机有理方位元门落定后，重新跑完整独立批次
[mutations_r2/summary.json](mutations_r2/summary.json)：**7/7 指定语义断言报红，7 个原源码对照全绿，实际源文件未变**。
这是重新运行，不是拼接 r1 片段；`hash_guard_selected=false`。

## 5. 主张到门与剩余不足

实际具名索引已追加在设计 §10；T1–T6 均有对应语义门，不用“测试全绿”替代数学条件。
固定切片的独立门目前覆盖凹形和三档尺度，不单独声称已穷举旋转后 E 洞/紧配内缝；这两类已在零旋转一致门覆盖。
旋转方位元门须保留 90° 系列及一般有理角；随机输入不是随机坐标系旋转的同义词，已建议主实现者补固定种子随机有理方位。

不变性只允许同时变换几何、参考点和位移；不允许换参考点但保持 d 不变后宣称是同一轨迹。
同一端点的不同参考点插值也一般是不同步内路径。这一限制必须保留，避免以后“参考点不变性”测试错误。

初次运行发现纯平移返回既有 `QuadraticTime` 的证书格式与 `RealAlgebraic` 不同，独立 helper 已修正读取 rational 证书；
这是 oracle 适配错误，不是内核错误，修复后所有 15 门通过。未把错误日志抹作首次全绿。

全套四片、最终静态 0、1810 步与冻结 450 步的完成性、源哈希和受控性能不在本专题单独批准范围内，
须以主报告中的实际运行结果为准。

### 5.1 影子工具只读源码复核补记

检查 `tools/m5a_se2_replay.py` 的拟合、投影剪枝、初态/PD 复用、时刻对账及序列化参考分类，没有另发现受限合同内的 critical/major。
精确单位协方差分支绕过分母限幅，有理刚体输入能保留零残差；非单位分支只是确定性参数建议，最终 δ 在精确有理数重算。
近塌缩的非刚体端点可使固定绝对 dyadic 精度的范数建议较差，但输出仍为有残差未认证，且未承诺全局最优拟合，不能隐瞒成拟合精度保证。
投影严格分离是充分证书，等号未排除；初态/PD 与旧弦结果复用有完整输入及逐帧绑定，并标 `reexecuted:false`。
“无 prior 就初态分离”的推断依赖历史 M4c 已验证的完整 swept 分类与绑定，不是另一个独立实体 oracle。
`same_time` 对 M4c 二次根先验证多项式再验证根支；legacy 主/次参考从 JSON list 规范成 tuple 后分类。
分类一致只表示模型下几何参考成员关系，不自动推出 legacy 力学错误。
冻结 450 帧门核查全部帧的哈希、计数守恒、认证/未认证分母及 legacy 分类，另重执行每家族一个实际刚体拟合。
这不是 pytest 内重新求解全部 450 帧的 SE2 根；完整计算来自单次完整影子回放，主报告必须如实区分这两个成本与证明层次。

### 5.2 额外非冻结多项式差分

固定种子 30152026，额外生成 120 个 1–5 次整数系数多项式，交替窗口 `[0,1]` 与 `[-2,3]`。
自写 oracle 与生产隔离所得根数和每个指定根独立 gcd/区间身份全部一致，合计 95 个实根，
证据：[algebra_random_independent_review.json](algebra_random_independent_review.json)。
这是已保存参数的专题实验，不替代正式全套 pytest 收集/执行身份审计，也不据此推导一般最坏性能。

## 6. 文献状态

LaValle (2006) Ch.4 相关正文 **已核原文**：SE(2)、C-障碍定义、平移差、旋转 VE/EV 与代数化。
只引用其背景定义，不把本项目的特殊轨迹和五次上界归因于该书：[作者原文](https://lavalle.pl/planning/ch4.pdf)。
Basu–Pollack–Roy (2006) **未核原文**，仅访问作者书目/下载页；Sturm 正确性论证和门由本设计明确给出。
石根华及正本所引历史实现论文 **未核原文**，不作优先性和真实积分方式的外文证据主张。

专题复核结论：受限合同可继续验收；所有上列保留边界仍生效，不等于 M5/G6 DONE。
