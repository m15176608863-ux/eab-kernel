# WO-PERF 最终轻量独立审查

## 结论与范围

**本次审查范围内未发现 critical / major。** 这是针对其他执行代理改动的轻量代码与数学审查，**不是正式六路 G6**，不替代最终全套绿、耗时验收或新工作树验证。

审查期间没有运行测试、测试收集或微基准，没有修改 src/tests/tools。审查人曾编写本工单的 interlock、exact_sweep、arrangement witness 优化；这些自己的改动不计入本报告的独立审查结论。

## 1. 二维 VE 方向整数化

阅读 `kernel2d/covers.py::_ve_side_directions` 与 `tests/test_perf_2d_directions.py`。

- 同一个正公分母 D 作用于 lo、hi、e，所有 cross/dot 符号不变；没有逐条归一化，因此最短向量的相对长度保留。
- 隐式角窗 `(length_tol / min_length)^2` 通过 `Fraction(tol) * D` 与向量共同缩放保持不变；显式 cone_tol 仍无量纲且优先于 length_tol。
- strict 与闭界分别保持 `> 0`、`>= 0`，没有新容差或浮点转换。
- 新门使用测试本地 Fraction 参考、3/5 Pythagorean 精确分界、不同最短边长、工程坐标与次正规输入。内部突变分别删除 tol 缩放、把边界改为 strict，目标断言明确。

未见单位、尺度或边界语义改变。

## 2. 三维 edge frame 整数射线

阅读 `covers3.py::_integer_ray / _qedge_contains / _qedge_frame_cached` 与 `tests/test_perf_edge_frame.py`。

- lcm、gcd 不引入负比例；没有强制首非零分量为正，因此不翻转法向或边方向。
- t、h1、h2、d 各自正比例缩放，不改变 axial、s1、s2 的符号和零；归一化 dot 窗口的分子平方与两个范数平方同比例变化。
- convex 三重积仍用原始精确 frame 判定；strict 仍要求两侧为正且 axial 等于零。
- 复用已有内容与实现缓存键，没有新增缓存。新门的参考使用本地面环遍历与 Fraction/Newell 构造；覆盖开面、反向面、共面接缝、折叠、工程坐标、最小次正规尺度及可变几何内容。
- 符号突变与非均匀分量缩放突变都有明确看护断言。

未见符号或阈值语义改变。

## 3. 独立 oracle 仍保持独立路线

阅读 `e5a_cover_oracle.py`、`e5a_escape_oracle.py`、两个冻结 reference 与 `test_perf_oracle_algebra.py`。

- dot/cross 公分母代数独立写在测试文件中，没有导入生产 rational3、几何谓词、法锥或构造 helper。浮点输入仍保留原乘减与 sum 顺序，另有浮点位模式对拍门。
- vertex 对 value 不大于零时不再构造范数；原 outside 在这些情况下必为 false，原 strict 判据仍读取全部 values。
- arc 仅把原有必拒绝条件提前。通过后仍构造投影 generators，显式计算 Gram 系统的 alpha、beta；没有用生产 `_qedge_contains` 答案替代独立 Gram 路线。
- escape.facet 仍使用 Gram determinant 及原参数公式构造 EE witness，只将构造推迟到两侧法锥通过之后。
- 两个冻结参考的 AST 与 baseline 匹配。escape reference 唯一预期导入调整是指向冻结 cover reference。

未见 oracle 与生产代码共享几何原语，也未见把 oracle 期望值替换为生产答案。

## 4. 原门、网格与冻结参考核对

本次直接读取 baseline 和当前文件的轻量核对结果：

```json
{
  "baseline_test_modules_compared": 88,
  "changed_or_missing_old_test_modules": [],
  "frozen_reference_AST_matches_baseline": {
    "perf_cover_oracle_reference.py": true,
    "perf_escape_oracle_reference.py": true
  }
}
```

88 个旧 `test_*.py` 模块逐字节未变，因此其断言、参数网格、skip/xfail 标记没有改变。两个 oracle helper 是受审的等价实现修改，不是减少测试格子。

随后读取 root 已生成的 `audit/retention_audit.json` 和 `audit/oracle_helper_audit.json`：当前收集 **8582** 个节点，baseline **8267** 个节点全部保留；旧测试 AST 保留审计为 PASS。helper 审计确认仅修改 dot、cross、vertex、arc、facet 五个既有定义，导入依赖未变、没有生产几何 import，两个冻结 reference AST 与 baseline 一致。

本审查没有重新运行这些审计或收集命令。最终运行结果与耗时，以 root 的最终全套证据为准。

## 残余边界

这是静态数学及测试结构审查，不能据此宣称最终全套全绿或小于 900 秒。新门的看护路径合理，但本审查没有重新运行突变。复杂浮点异常输入、生成器向量等不属于这些私有 exact helper 的本次内部输入契约。

## 报告编码修复

先前通过 PowerShell 管道写入中文时发生代码页损失。本文件已通过直接 UTF-8 补丁重写，未触碰源码或测试；交付前另行读取并核对中文标题与关键短语。
