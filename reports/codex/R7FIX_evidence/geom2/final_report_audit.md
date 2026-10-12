# R7FIX 最终报告一致性轻量审计

范围：只读主报告、四分报告、各变异日志/JSON及六个旧测试/辅助oracle差分；未运行测试、未修改 tracked 或 tests 文件。

## 结论

- G6G-01/02/03：三个独立变异日志均有目标 AssertionError 及 `pytest_exit=1, expected_red=true`，分别为首出口 2≠1/2、gap q≠2q、缺盖门错误 passed。
- G6G-04/05/06/08：geom3 mutations.json/log 含四项 KILLED，断言分别为 folded-ridge-slab-distance / signed-gap-final-rounding / exact-local-margin-normal / axis-product-volume。
- G6G-07：Dual mutations.json 中 power 的独立 pytest 为 1 failed，非零导数目标断言与分报告一致，876 格无缩网格。
- G6G-09/10/11：真实受测文档变异均 exit=1，targeted_assertion 具名，restored=true 且有恢复 SHA。G09 数值空腔修前已绿而文档命题红，主报告已明确，没有冒充代码修前红。
- 六个旧测试/辅助oracle文件与差分一致：frozen midpoint、eager EE 证书、normal_noise、变异 kwargs、贯入守卫双层牙、非共面 margin oracle。主报告分别解释前提、保留断言/网格/阈值和增强证据；未见未记账旧测试修改。
- 三次未成功全套分别中止/中止/18 failed，主报告均如实保存，不计绿。最后4-worker全套仍进行中，本审计不升级其状态。
- 全仓扫的力学构造追加在主报告与geom2追加节一致：5修前红、7新门绿、753旧LP选择性回归绿；不冒称改了LP证书算法。

## 轻微呈现建议（已发主执行器，不是缺陷）

1. G05 的 raw mutations.json/log 只记录 facet signed-gap 变异；face_area 变异由永久具名测试 `test_g6g05_internal_mutation_rounding_norm_before_halving_is_caught` 在内部捕获 `area-final-rounding` AssertionError，属于定向/全套绿中的变异证明。主报告可标清两种证据入口，避免读者在JSON中寻找不存在的第二条记录。
2. geom2分报告保留阶段性28格/4文件叙述，后续追加节明确最终34格/5二维文件及limit新7门。它是累积过程记录，最终范围应读末尾追加节，主报告当前汇总正确。

当前未发现需要修改生产源码、测试网格或阈值才能解决的报告一致性问题。
