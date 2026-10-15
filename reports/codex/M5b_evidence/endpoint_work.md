# M5b 端点重建与历史中点量：可复现记录

## 结论与边界

- **完整重算**：15 例、1810 步、15220 块帧。最终主记录 `endpoint_full_r2`，125.56658089999837 秒。见 [冻结摘要](endpoint_summary.json)、[自包含输入清单](endpoint_inputs/manifest.json)、[最小例](endpoint_minimal_examples.json)。
- 定义块帧一个舍入单位 `U=ulp(max|coordinate|)`，最大值取该块帧起、终点所有坐标。`ulp` 是正坐标量级处向上的一个 binary64 格距；零处取 `2^-1074`。**不是半 ULP，也不是 max-coordinate×2^-52，也不是每一个小坐标自身的 ULP。**
- 将原 `%.17g` 文本恢复到原 binary64，再提升为 Fraction；精确有理面积形心加明确的 binary64 cos/sin 候选，形成一个精确有理仿射映射。对全部观测终点，最大坐标残差为 `2.257867693845113e-13`，最大归一化残差为 **1.0044227048058703 U**，满足“约 1.1 个单位以内”。两个最大值不在同一帧。
- 另用严格有理 Taylor 区间包住数学实数三角函数：候选函数绝对误差上界的全数据最大为 `6.125351005406442e-17`；以数学实数三角函数为另一模型时，最大归一化端点残差上界为 **1.278351617304262 U**。不把两种三角口径混写。
- 原始精确端点重建与旧 M5a2 轨迹的参数调用已完整复现；历史外部 `1.101`/`2.8e-6` 记录保留，**没有硬凑数值、也没有宣布推翻验收事实**。本次明确全 15 例、L∞、旧 M5a2 对 P3 中点的最大偏离上界为 **9.626408698932884e-6**，历史 `2.8e-6` 的范数/数据范围/轨迹参数口径仍待对齐，列为 PARTIAL。

## 1. 输入、配对与不可变证据

读取 M4c 已冻结的输入 SHA256；先核对并把原 `out.csv`、`geom.csv`、`shadow.jsonl` 复制到本树 ignored tmp，未执行姊妹源码或 exe。

对第 k 步第 b 块：

1. `out.csv(step=k,block=b)` 的六分量为 `(dx,dy,theta,ex,ey,gamma)`；按复合键配对，不按 CSV 行位置。
2. `shadow[k].geometry == geom.step(k-1)` 是区间左端；`geom.step(k)` 是右端；最后一个区间由 `geom.final == geom.stepN` 补齐。
3. 验证步号连续、全部块/顶点身份固定、CSV 无重复键、每一条 z 恰好用一次、初/末几何一致。新门将 CSV 两行倒序，仍须按键正确配对。
4. DDA snapshot 含两个回绕别名；验证其坐标逐值相等后剥掉末两点，保留起终点的同一顶点身份。原环可能顺时针，精确面积公式使用有符号面积；循环重排或反向不会改变精确形心。
5. 冻结 74 个 gzip JSONL 分片，共 4547838 字节，最大单片 94237 字节。每条内嵌 case/step/block/vertex_ids/start/end/z，坐标和 z 全是精确有理数字符串。普通重算不依赖姊妹路径、原始大文件或 exe。

每片与原输入 SHA256 在 manifest；运行前后核对 manifest、每片及所用核心端点/拟合源码。大逐帧输出留在 ignored `tmp/endpoint_full_r2/endpoint_rows.jsonl.gz`，其 hash 入摘要。运行每 100 块帧落盘进度；目录必须新建，不续跑、不拼接。

## 2. 精确仿射映射与三角函数合同

令带符号面积二倍量 `A2=sum cross(p_i,p_(i+1))`，则

`c_k=sum (p_ik+p_(i+1)k)*cross(p_i,p_(i+1))/(3*A2)`。

给定明确候选 `co=Fraction(math.cos(theta))`、`si=Fraction(math.sin(theta))`，定义

`M_DDA=[[co+ex,-si+gamma/2],[si+gamma/2,co+ey]]`，

`q_exact=c+d+M_DDA*(p-c)`。

这是真正的有理仿射映射；`max|q_exact-q_snapshot|` 用 Fraction 逐值计算，不是对浮点差再提升，不把正残差截断。快照可能不落在共同仿射映射上，残差包括实际形心舍入和逐语句运算舍入。

**不无证假定 CRT。** 本机 Python 三角候选不先验视为历史 C++ 内部 bits。Taylor 证明与观测残差都不依赖这个假定。另做源语句分组的 binary64 精确数值佐证：

- 初版辅助诊断按剥别名后环从 `pad_lo=lo-1` 起求面积矩，只匹配 **314252/315760** 个坐标；此历史数保留在主摘要。
- `geom.csv` 的实际 `range` 行证明真实面积矩求和起点为 `lo`，不是 `pad_lo`。独立 [grouped 重放工具](../../../tools/m5b_grouped_probe.py) 冻结 [物理区间](endpoint_physical_ranges.json)，将环循环移一位，仅更正 binary64 求和顺序；逐帧另外断言精确形心不变。
- 正确物理求和次序下，全部 **315760/315760** 个坐标 binary64 精确数值一致，完整 15220 帧、`grouped_full_r2` 的 6.389601 秒，见 [独立分组重放摘要](endpoint_grouped_summary.json)。**Fraction 冻结会合并 +0/-0，因此这不包含符号零 bits 的一致性，不称逐位完全一致。** 本机候选足以完整复现观测端点数值，但这不是从输出唯一反解历史内部 centroid/cos/sin bits 的证明。

主工具和输入在长时程稳健重放启动后保持不动；没有通过改 hash 伪装更正。辅助诊断单独真实运行并冻结。

## 3. Taylor 严格性

对 `|theta|<=1`，sin/cos Maclaurin 级数的项绝对值单调不增。保留 10 项后，实值位于部分和与“部分和＋首个遗漏项”之间；负角也按有符号递推和 min/max 包住。所有项与端点都是 Fraction。线性仿射映射用区间线性组合传播；无需假定 libm 正确舍入，也不把二进制显示值当作判据。

独立主 oracle 用另一构造：40 次 Maclaurin 多项式加 Lagrange 余项 `|theta|^41/41!`；其更紧区间必须落入被测区间。oracle 不调用生产 Taylor、几何、拟合或旋转原语。

## 4. 旧轨迹对 P3 的中点重算

旧族参数严格沿用 `tools/m5a2_affine_replay.py`：

`a=fit_affine(start,end); r=fit_rigid(start,end)`；

`DDAAffineMotion(a.matrix,r.motion.u1,a.translation,a.center)`。

对比 P3 在 `s=1/2` 的数学实数三角位置区间；单位沿用原坐标，主统计为每块每顶点坐标绝对差最大值，即 L∞。另存 L2 最大值平方上界，未把不同范数混用。

最坏完整例：`bbv01_dbv01a / step56 / block10`。不调用生产拟合/形心/三角函数的独立门，以原坐标 3×3 正规方程/Cramer 计算仿射系数、三角剖分积分算面积形心、Decimal 100 位平方根给独立刚体半角候选，再用有理 Lagrange 区间，得到

`9.626408e-6 < discrepancy < 9.626410e-6`。

`bb09` 的最大值 `2.814427923400236e-6` 与外部约 `2.8e-6` 同量级，但不能据此臆测历史只用了该例。尚缺历史可执行定义来完成同口径对齐；这不是中点差上界的全时间版本，也不是物理路径证书。

## 5. 门、变异与数值登记

文件：[tests/test_m5b_endpoint.py](../../../tests/test_m5b_endpoint.py)。最后单文件运行：**27 passed in 0.10s**，0 skip。

主 oracle imports：`fractions.Fraction`、`math.factorial`；中点独立候选另用 `decimal.Decimal/localcontext`。`pytest`、`inspect`、`json`、`Path`、`sys` 为测试/证据设施，不是几何 oracle。生产被测 imports 为 `m5b_endpoint_replay` 与辅助分组工具；不调用姊妹代码。

| 看护 | 独立门/语义 | 内部变异 | 指定红断言 |
|---|---|---|---|
| 精确面积形心 | 扇形三角积分，非中心对称五边形 | 分母 3A2 改 2A2 | `area centroid must equal independent triangle integrals` |
| DDA 加法形式 | 独立位移分量展开 | 矩阵旋转交叉项反号 | `endpoint must match independent displacement oracle` |
| 三角包络 | Lagrange 独立余项 | Taylor 交替符号变同号 | `trig enclosure must contain independent Lagrange certificate` |
| 浮点求和物理起点 | 原完整输入最小失配例 | 起终点一起取消循环移位，保持配对 | `physical lo..hi summation start must replay observed binary64 endpoints` |

以上均在函数执行前编译并注入内部缺陷；只调用指定语义驱动，不运行源码 hash 类绊线；先确认原函数通过。物理起点变异同时撤销 start/end 循环移位，避免误靠顶点错配报红。

元门：有理非轴对齐旋转 `(3/5,4/5)`、平移量级 0/1e3/1e5/1e6、单位 `2^-200/1/2^200`，非对称面积形心与应变张量共变，12 个构造参数格。分别检查精确面积形心和完整 affine 端点协变，不错误要求 ULP 统计在任意平移后不变。

数值合同：binary64 只用于显式外部输入解码、libm 候选和单独源分组佐证；精确重建、残差、面积、Taylor 界、最大值比较全是 Fraction。报告显示才转 float。所有断言型 helper 已迁入真正 `test_` 驱动，输入制作内联测试；不为此扩张共享插桩域或添加数值准入。

## 6. 复跑

```powershell
$env:TEMP=(Resolve-Path reports/codex/M5b_evidence/tmp).Path
$env:TMP=$env:TEMP
$env:PYTHONIOENCODING='utf-8'
python tools/m5b_endpoint_replay.py --run-name endpoint_full_fresh
python tools/m5b_grouped_probe.py --name grouped_full_fresh
python -m pytest tests/test_m5b_endpoint.py -q -p no:cacheprovider --basetemp reports/codex/M5b_evidence/tmp/pytest_endpoint_fresh
```

前两命令从永久输入重算；输出目录必须此前不存在。`--freeze-inputs`/`--freeze-ranges` 仅首次创建输入时使用，会拒绝覆盖现存冻结输入。

## 遗留

1. 历史 1.101 与 2.8e-6 的原可执行定义没有随工单交付；本次定义、结果和差异均已明确，历史中点口径仍需对齐。
2. 仿射端点匹配不证明未知真实物理步内轨迹。本文不给全时段 P1/P2/P3 首盖或扰动证书，相关结论由 M5b 主报告的独立路径给出。
3. 没有把 27 个单文件门替代全套四分片或六路 G6；全套与静态逐站统计由主报告统一登记。
4. 主端点摘要的源码绑定是直接的工具/affine/rigid-fit 文件表，**不是完整传递 import 闭包**；`fit_rigid` 间接使用的 `m4c_motion_replay._exact_poly/require`、`SE2Motion` 等未逐一列入该表。本轮这些间接实现未改，极值另经独立公式门复核；仍将传递绑定硬化列为 minor，不把 direct 表宣传为完整闭包。主全时程稳健回放另有完整 `src/eab` 绑定。
