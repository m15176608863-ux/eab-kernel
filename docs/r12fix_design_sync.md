# R12FIX / R12FIXb 设计同步（2026-10-12）

## 1. 工单状态与范围

R12FIXb 接替 R12FIX 的静态构造门设计。原方案的 16936 条 waiver 和全部 Python 文件依赖快照被撤下；
不能把旧报告中的全库冻结方式当作现行合同。HEAD 为 `0ce65a4`，改动未提交。最终计数、全套运行结果、
未完成项及逐站点审核见 [R12FIXb 报告](../reports/codex/R12FIXb_report.md)。

本轮不是独立六路 G6；工单禁止新建 worktree，所以未执行新鲜 worktree 门。
M0 所有者退出决定及 M4a 离线影子合同不变。姊妹仓库、其他工作树与外部设计正本只读。

## 2. 数据流准入，不再一律拒绝 float

入口 `tools/check_exact_construction.py` 扫描 `src/` 与 `tests/` 全部 Python。
`exact_construction_flow.py` 从源码求有限的一阶类型、调用、参数到构造入口的流向；
`exact_construction_subset.py` 默认拒绝未知语法和动态执行。
旧控制流/别名 may-analysis 仍同时运行，循环回边、分支合流及容器写入不会被新摘要替代。

- 已知 int / Fraction 的算术、比较和已证明元素类型的累加可自动准入。int/int、负整数幂、
  Fraction 与 float 混算不冒充精确有理运算。
- 统一构造模块的已知直接调用有明确摘要。输入 float 与由算术产生的 float 分开；
  `Fraction(已舍入值)` 不会洗去舍入来源。
- 普通 float 加减乘除如果不流入开方、范数、单位化或几何差分构造，不因其类型就被拒绝。
  已知类型的 abs/min/max、math.isfinite 等纯函数可分析。
  非整数指数的 `**` / `math.pow` 也按潜在根构造追踪，不能只识别字面 `** 0.5`。
  sink 类型事实与成熟 CFG 的当前舍入状态结合，不能由较弱的一阶摘要覆盖循环/异常分支事实。
- 源码可解析的直接函数、记录字段与局部容器按有限摘要分析；新本地模块的静态 import 不需要
  更新全库清单。import 可解析不等于它的任意函数都安全；修改 callee 后重新读取源码。
- 高阶 callable、反射、动态模块/函数替换、未知对象协议等仍无通用证明；未识别的新形态必须报违例。
  数值算法优先改成直接调用和显式循环，而不是登记一个“可信 callable 名字”。

相应正向门：`test_r12fixb_safe_subset.py::test_normal_safe_numeric_programs_are_proved_without_waivers`、
`test_new_local_source_import_needs_no_repository_registry_refresh`。
反向门保留 R12FIX 全部原节点，另有 `test_r12fixb_flow_adversarial.py` 的实际错误结果与拒绝断言。

**保证边界**：这是有限标量/记录/容器数据模型上的源码准入和舍入来源检查，不是任意 Python 的数值证明，
也不证明每个算法数学正确。未知对象的运算/属性协议、运行时 monkeypatch 和外部动态代码不在自动证明内。
一阶摘要仍有保守误报；不能把局部人工例外写成机器已证明。实际近似诊断/旧 oracle 必须明示排除范围，
不得声称它们没有中间舍入。

## 3. 局部例外机制

`tools/exact_construction_policy.json` 每条规则站点记录：

1. 相对路径和限定函数（或模块/类的最小封闭作用域）；
2. 不含行号的完整 AST 节点指纹；
3. 该作用域的源码 SHA-256；
4. 具体原因、类别与审核证据。

删除整库 `dependency_snapshot` / dependencies；也不再保留不带哈希的函数级 EXCEPTIONS 旁路。
源码 hash 按扫描时 UTF-8 文本、通用换行解码后的内容计算，包含函数签名、装饰器、注释和函数体。
模块/类的独立函数或方法分别锁定；外层函数包含其嵌套定义，嵌套函数也有自己的作用域。
同一限定名在不同分支重复定义时，锁住该绑定的全部候选函数源码组，而不是后一个覆盖前一个；
该候选组不包含其他无关函数。修改组内任一候选会使该同名绑定的例外失效。

修改无关文件或同文件其他独立函数不使例外失效。被审函数变化、站点删除或 AST 不匹配时，
报告 `closed-stale-waiver`，即使改写已经安全也要求显式删除旧记录。例外不随行号迁移误失效，
也不因“路径存在”或旧函数名而扩展到新增站点。

扫描器只读 policy，不更新 hash，不生成例外；不提供“扫描后全部重新豁免”的命令。
复核应只处理被修改作用域的相关记录。证据目录中的审核候选是分析记录，不等于自动批准。
最终 policy 的人工排除与证明缺口计数必须连同报告阅读；未达到 200 条目标不能以“零违例”冒充完成。

本次过渡清单为 **2365 条局部规则站点排除**（1755 个不同 AST 站点、557 个作用域），超过 200 条目标。
其中 642 条是未完成的证明缺口，467 条涉及近似/名义诊断范围，16 条涉及待改写的数值动态路径；
其他类别见逐站点清单及报告。它们是 root 显式记录的遗留排除决定，**不是机器证明或独立 G6 批准**。
零诊断只表示在这些排除生效后的门通过，不表示所有站点不存在先舍入再构造；本轮按 PARTIAL 交付。

局部锁定并不为被调用函数的将来语义背书：被调用源码仍重扫，新不支持形态报红。
被人工排除的旧近似路径不因此获得任意新调用场景下的精确构造保证。

## 4. 测试范围

- `src/eab` 中 oracle/helper 和 `tests` 独立 oracle/helper 同样受检。
- `tests/test_*.py` 的顶层独立 helper 不因为文件名而放行。
- 沿用 R12FIX 的明确边界：该类测试文件的模块级 pytest/import scaffold，以及顶层
  `test_*` 驱动整个子树不受新增闭集前检保证；它们仍接受旧直接转换/舍入检查。
  动态变异器必须能够植入坏代码，不能把其“有意错误”说成安全数值构造。
- 数值 oracle 的独立性仍按 AGENTS A 单独核查；源码准入不替代独立几何/中点/证书 oracle。

## 5. 可维护性与牙

`tests/test_r12fixb_maintenance.py`：
- 实际仓库副本的无关 `src/eab/__init__.py` 加注释，扫描仍零违例；
- 只改带例外函数体，仅该作用域的例外失效，同文件其他函数保持有效；
- 新增禁止构造或动态函数报红；
- AST 指纹、注释 hash、删除/安全改写后的陈旧记录都有额外检查。

`tests/test_r12fix_static_closed.py` 保留四种真实 cone 内部植入、未知高阶形态、舍入实参跨调用、
运行时注解/反射、格式化、隐式混合算术等全部牙。
`test_l01_disabling_closed_pass_trips_real_cone_rejection_assertion` 在被测 scanner 内撤掉拒绝层，
确认失败的是目标拒绝断言，不靠伪造输出。
历史 nodeid 中的 changed_dependency 保留以保证节点集合不缩水；其断言已改为无关依赖编辑不失效。

新增对抗测试实际执行中点下溢错误，再要求扫描拒绝；包括默认值/闭包、局部重绑定、循环/异常别名写入、
dataclass 字段与自定义记录初始化。独立 Fraction 平方中点证书不调用被测构造求正确答案。
最终独立任务复核还找到幂根的循环/异常状态漏传、同名分支函数 pin 覆盖两个缺陷，已增加
`test_r12fixb_final_mechanism.py` 的永久红绿门（含增强赋值、callee 返回、嵌套 break/continue）；
最终节点数见报告。这次任务复核不是六路 G6。

最终集成还修复了清单提取器将 Call/Yield 错绑到外层 Expr 的 165 条记录（168 个实际诊断位置），
并按当前源码更正 39 条理由/分类。更正没有增加排除条数、没有刷新任何作用域哈希。
原 R10 自展开属性别名门发现裸构造 intrinsic 在新摘要中未被识别为 sink，现与旧扫描 API 对齐；
保留原断言不变，仍要求未知属性进入构造时拒绝，不以“普通数据读取”洗白。

## 6. 重跑与治理

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/check_exact_construction.py
python -X utf8 tools/fix_canon_ptrs.py --apply
# pytest 的 basetemp 父目录须先存在，且位于本工作树内
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=reports/codex/R12FIXb_evidence/tmp/manual_full
```

本轮完整验证同时保存收集/执行节点并检查原 11368 节点均存在，不删格、不跳过、不 xfail。
全套绿只对报告冻结的工作树版本成立，不能代替独立 G6。

M4a 原三组门 `test_m4_bdda_adapter.py`、`test_m4_bdda_shadow.py`、`test_m4_bdda_vv_reader.py` 保留；
只消费冻结导出，不重新捕获、不修改 fixtures、不写姊妹。静态局部盖不冒充真实运动首入或力学轨迹等价。
