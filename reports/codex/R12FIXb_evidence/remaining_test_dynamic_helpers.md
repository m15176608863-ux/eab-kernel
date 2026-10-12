# R12FIXb：测试数值 helper 直接化清单

本清单不是例外批准。依据 round4 逐站点审查与随后实际源码改写；最终应与最新扫描相交，不沿用旧函数哈希。

## 已做的最小直接化

- 22 个测试文件、25 个已知数值 `map` 改为显式 generator；只处理 `F` / `Fraction` / `scalar_exact` / `_fv` / `exact_oracle.qpoint` / `E.vector`，不放开未知 callable。
- 17 个数值 lambda 改为同名局部 `def`；表达式文本、运算次序、默认参数定义时捕获保持不变。
- 未动测试驱动中的故障注入；237 个原测试函数的完整 AST（含装饰器与参数化表达式）已核对相同。
- 改动清单及原字节回滚锚点：`test_helper_rewrite_changes.json`、`test_helper_rewrite_backup/tests/`。新的 generator 临时名字 `_r12_item` 只处于 comprehension 局部作用域，改写前已断言原文件没有该名字。
- 第二轮：`PAIRS` / `MARGIN_CASES` 只留数据标签，实际工厂改成固定显式分支；22 个工厂的顶点、面、元数据及排列与改前逐项相同。
- 第二轮：Lipschitz 数值 helper 改收 `(x,y,nx,ny)`，正常/变异函数仅由既有测试驱动计算样本；6 类正常/错误法向的调用次序和最终结果与改前完全相同。原 mutant lambda/bump 体、测试参数化均未改。证据：`test_factory_data_equivalence.json`。

## 仍集中的高阶形态（不可混入纯测试架构例外）

|优先级|源 scope|真实用途与建议|
|---|---|---|
|1|`test_invariance_2d.py::_T`、`_floor_in_reference_units`|返回捕获姿态的 `pt/vec/poly` 三个 callable，后续解包调用。建议返回明确姿态参数，由三个一阶 helper 接收参数，不能只为注册表/函数元组放行。|
|1|`test_invariance_2d.py::_g0_exact_affine`、`.poly`|返回 `vec/poly`，内部仍 `map(vec,P)`。数值在 Fraction 域但结构仍高阶；保留有理系数与运算次序，改为显式参数的一阶变换。|
|1|`test_invariance_limit.py::_transform`、`_map_back`|前者返回 `P` closure、后者接受并调用它。可直接传 `R/s/t`，在 map-back 内用相同公式计算参考原点像；不要改变已知载荷/旋量模型。|
|已完成|`test_invariance_geom.py::_base`、`test_invariance_interlock.py::_margin_ref`|已改 `_pair_for_name` / `_margin_pair_for_name` 固定分支，表内无 callable；另一个测试驱动的表内直接调用同步改为相同 helper，样本不变。|
|2|`test_geom3_face_polygon.py::Frame.poly`|`self(p)` 调用数值 `__call__` 协议。可用显式命名的坐标变换方法，并同步 fixture 调用方；不能因类名已知就笼统信任对象 callable。|
|2|`test_limit_exact_selfcheck.py::q`|`getattr(v,'exact',F(v))` 是证书标量读取，不是任意函数调用，但仍依赖反射。可改明确支持类型/字段分支，注意原默认表达式 `F(v)` 是立即求值，不可无意改变异常语义。|
|已完成|`test_margin.py::_true_normal`、`_lipschitz_worst`、`_lipschitz_verdict`|正常法向以直接导入绑定调用；数值判据 helper 只吃原样本与法向数据、不接受 callback。测试驱动保留错误函数注入与原调用顺序；近似 Lipschitz 判据本身仍不是精确构造 oracle。|
|已完成|`test_perf_covers.py`、`test_perf_edge_frame.py`、`test_perf_integer_geometry.py`、`test_perf_2d_directions.py`|`audit_design` 已完成数值 map/lambda、稳定排序键及 `_outcome(func)` 的直接化；报告 140 条定向通过，原 8 个 mutation/teeth AST 不变。|

## 与上述不同：不生产数值期望的测试架构

- 文档路径解析、文本拆行、CSV/TSV 字段读取、SHA256/JSON 摘要、记录身份键核对：输出路径、字节、字符串或身份元数据。
- `inspect/compile/exec/monkeypatch` 内部源码故障安装：必须保留对应目标断言真正报红，不可说注入代码“无先舍入”。
- `pytest.fixture` 与 `cache_clear` 生命周期、门的 `scan(source,path)` 调用：处理测试执行/源码诊断。
- 通用线程超时执行器仍是运行协议边界，不证明传入任意 `fn` 的数值安全；局部例外只能描述该边界。

## 近似诊断边界

浮点旋转采样、OBB SAT 容差诊断、有限差分梯度、显示见证点的并列标签筛选等确有中间舍入。它们可被如实记录为给定输入或旧近似诊断，但不能写成“没有先舍入再构造”，更不能作为精确构造 oracle 的豁免理由。
