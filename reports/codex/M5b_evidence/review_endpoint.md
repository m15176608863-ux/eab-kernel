# M5b 独立协作审查 R1：端点与中点口径

审查对象由 endpoint_replay 代理实现；本审查者没有参与该工具编写。自己的 P2 核心代码不列入本域独立审查。范围是源代码、冻结输入与极值、口径、既有门；**不是重跑 15220 帧数值计算，也不是独立六路 G6 的总体退出声明**。

## 结论

- **critical：0。major：0。minor：2（范围明确后不阻止当前有限主张）。**
- 严格有理端点映射、面积形心、z配对、明确块ULP口径下的 `<1.1 U` 结论有当前仓内证据支持。
- `2.8e-6` 的历史全范围/范数/参数口径仍未对齐，必须保留 **PARTIAL**；当前明确全数据旧族对P3的中点顶点L∞最大是 `9.626408698932884e-6`，不能替换成`2.8e-6`作为同义结果。

## 只读与独立核验

读过 `tools/m5b_endpoint_replay.py`、`tools/m5b_grouped_probe.py`、`tests/test_m5b_endpoint.py`、当前 M5a2 订正文档和端点摘要/最小例。

独立程序只导入 Fraction、math.factorial（Taylor系数）、标准库JSON/哈希。math.cos/sin只提供**被核对的候选输入**，不当几何oracle。关键原语独立于端点生产代码：

1. 以首点为锚的扇形三角有向面积加权形心，不调用生产shoelace函数。
2. 直接展开位移 `p+d+E(p-c)+(R-I)(p-c)`，不调用生产endpoint_map。
3. 用有理数分子/分母位长确定二进制指数并构造ULP，不调用`math.ulp`。
4. 用32项显式阶乘Taylor及严格余项包围数学sin/cos，不调用生产交错递推。

独立数据记录见 [review_endpoint_checks.json](review_endpoint_checks.json)。核对结果：

| 最小极值例 | 独立结果 | 解释 |
|---|---:|---|
| binary候选最大 `bb09/step88/block5` | 精确比值与冻结Fraction逐值相同；显示`1.0044227048058703 U` | 严格小于1.1 U，输入U明确 |
| 数学三角最大 `bb10`（完整定位见JSON） | 独立严格下界已经约`1.278351617304262 U` | 与binary候选不同不是Taylor包围过松造成，不能偷换模型 |
| 旧族/P3中点全局例 `bbv01_dbv01a/step56/block10` | 独立3×3/Cramer门将真差夹于`(9.626408,9.626410)e-6` | 原调用、原单位、顶点L∞明确；不是全时程上确界 |
| `bb09`单例中点最大 | `2.814427923400236e-6` | 与历史2.8e-6近，但只能提示可能范围差别，不足以擅自认定历史范围 |

运行命令：`python -m pytest tests/test_m5b_endpoint.py -q -p no:cacheprovider --basetemp=reports/codex/M5b_evidence/tmp/endpoint_independent_review`；TEMP/TMP均在M5b本树tmp。最后一行：

```text
27 passed in 0.10s
```

这里的27门包含作者已有门；独立性来自上述另写的极值核验和人工审查，不把“再跑作者的测试”单独当独立oracle。

## minor 与处置

### R1-m1：binary64分组重放的“逐位”措辞

`grouped_binary64_replay` 使用`Fraction(predicted)==observed`计数，冻结Fraction合并+0和-0。315760/315760可称“精确binary64数值一致”，不能单靠该检验声称signed-zero位也一致。另，端点摘要原始padding起点重放314252/315760、物理lo..hi起点重放315760/315760是两条不同诊断，必须分别保留，不能悄悄覆盖旧数。

处置：已通知作者/主线程；当前`m5b_grouped_probe`已将数值一致、signed-zero边界与旧计数说明写入模块和解释字段；主报告应引用新鲜配套分组摘要，而不是把原endpoint摘要的旧计数改写。独立有理端点残差不受此措辞问题影响。

### R1-m2：端点摘要是直接源码绑定，不是完整传递闭包

`endpoint.run`绑定自身、`affine_motion.py`、`m5a_se2_replay.py`及manifest；中点路径还间接调用`m4c_motion_replay._exact_poly/require`、`se2.SE2Motion`。这些文件没有进入该摘要的四项hash表。当前这些间接依赖本轮未修改，最坏例另有独立核验，因此未发现当前数值失真；但不能将这张表称完整传递源码闭包。

处置：主报告披露直接绑定范围；完整传递闭包的启动/结束绑定与变异拒绝门留待专门硬化。不要为修说明而只改历史摘要hash，也不要把本审查补算两例包装成全量重跑。

## 需求缺口（不是新发现的静默数值错误）

1. 未取得历史C++ CRT每次sin/cos的内部位；当前候选有数学三角误差界、观测端点精确残差与物理顺序数值重放佐证，不据此声称唯一恢复内部位。
2. 历史2.8e-6与当前明确全数据9.6264e-6的口径等同未证明；M5b必须PARTIAL。
3. 本审查只检查端点/指定中点，不认证任何未知连续DDA真实路径或首盖。
