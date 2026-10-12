# 通用结构证明与 PERF helper 直接化

## 结构证明（非站点白名单）

- `struct.pack/unpack`：仅解析固定格式字符串的有限已知代码；未知格式/原生 `@` 格式仍拒绝。`pack('>d', float)` 不虚构新舍入，`Fraction→d`、`f/e` 窄化及既有污染保持 bad，`unpack` 不擦除 bad。不是将任意二进制转换宣称无损。
- `itertools.count`：只有所有实际 start/step 为已证明 int/bool 时给出整型流；float 步长仍 unknown。
- 本地源码导入的常量：读取实际赋值摘要，字符串/数值/数据容器与 callable 分开；函数名和未知值不获此证明。
- `c = covers3` 等直接模块别名：以唯一静态 module 值解析；容器中取出模块、重绑定、模块属性写及有未知执行副作用的 callee 仍拒绝。没有关闭 `last_unproved_effects` 向调用者传播。
- 未增加 tuple/dataclass 泛型别名的宽泛推断，避免扩大不明确的 Python 类型协议边界。

永久门：`tests/test_r12fixb_structure_flow.py` 新增 23 节点，涵盖阳性及 pack 舍入进入 root、未知格式、float count、模块写/重绑定/容器/未知 callee 阴性。

验证：

- `flow_structure_verified.log`：`94 passed in 0.37s`（新增 23 + 既有 safe/adversarial 71）。
- `flow_structure_old_teeth.log`：`110 passed, 2 deselected in 12.16s`（两项全仓/旧 policy 依赖由主流程处理）。
- `_eager_ee` 单文件扫描 0.42 秒，只余 4 项 `_qedge_contains` 下游方法/调用未证明；没有采用函数级免检。

## 四个 PERF 文件的机械直接化

- `test_perf_2d_directions.py`：`map(F, vector)` 改直接 `F(component)` 生成式。
- `test_perf_integer_geometry.py`：helper 内 `map(scalar_exact)`、`map(G.vector)` 改直接生成式。普通 test driver 与内部故障注入保持原样。
- `test_perf_edge_frame.py`：两个数值 map 直接化；`_outcome(func,*args)` 改成分别直接调用生产/独立参考的两个异常结果包装器。零长棱错误断言与原来一致。
- `test_perf_covers.py`：数值 lambda key 改 `(key,index,candidate)` 稳定装饰；segment/triangle 容器 callable 分派拆成先二点、再三点的直接循环，候选及平局次序不变。

修改前内容保存在 `perf_dynamic_before/`；`perf_dynamic_rewrite_manifest.json` 记录前后 SHA-256、替换数及保留 LF。`perf_dynamic_node_preservation.json` 自动核对所有 test 定义名称、参数、参数化装饰器，以及所有 mutation/teeth 测试 AST 未变。

定向四文件：`perf_dynamic_rewrite.log` 最后一行 **`140 passed in 1.95s`**。测试输出中原本内部变异牙全部执行，不移除节点、不降低断言。

这些结果不代替主报告的全套测试、最终例外逐站点审查或独立 G6 退出审查。
