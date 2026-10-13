# R15FIX O04 与读取器同类扫描

## 范围与合同

仅修改 src/eab/readers/numeric_decode.py、src/eab/readers/bdda3d.py；新增 tests/test_r15fix_numeric_decode.py，未改任何原测试、fixtures、M4a 生产代码。整数身份/状态只需分母为 1，无 binary64 幅度上限；已知连续字段在字段 schema 中检查 RN-even 非零/有限域。未知 metadata 保持已有 numeric-tree 模型，不虚构新物理单位。

## 修前红 → 修后绿

- 原始代码新增测试：o04_red.log 最后行 `57 failed, 3 passed, 1 deselected in 0.76s`。
- 37 格巨大十进制身份：ContactRecord 11 个字段乘 2 拼写、3 个嵌套 Feature 字段、bdda3d reader/document 乘 6 个身份字段。全被 `JSON numeric literal: exact scalar is outside finite binary64 range` 过度拒收。看护断言为 `unbounded integer schema rejected an exact integer`。
- 12 格连续量拒绝虽然仍拒收，但错误在字段 schema 之前；`continuous domain check must name its schema field` 报红。修后同样拒绝，错误 quantity 指向 gap/area，不再无差别拒绝 token。
- 另外 8 格同类扫描发现见下。
- 修后含原 R14 读取器、原契约往返、M4 adapter/VV 门：o04_green_final.log，最后行 `446 passed in 5.62s`。
- 追加原 tools 读取器和 M4 shadow 门：o04_m4_tools.log，最后行 `77 passed in 9.92s`。
- 新文件共 71 个测试格，其中 9 个生产函数内部变异看护；原门零改写、零删减、零 skip/xfail。

最初运行因 pytest --basetemp 父目录尚未创建有 24 个 setup error；保留 o04_initial_tmp_setup_error.log，分类为环境路径错误。创建本树证据 tmp 目录后重跑正式红，没有 setup error。

## O04 根因与修法

JSON parse_float 回调 _decimal 把与字段类型无关的 token 提前放入连续输出域。删除其中 scalar_rational，仅 Fraction(token) 精确保留，并继续保留实数字面量负零。整数由 integer() 检查可整除，连续由 scalar() 检查可表达域；NaN/Infinity 仍拒绝。输入 1e400 与 10.00e399 均按 10**400 的整数身份保留。

### 同类 S-O04-1：bdda3d 离散证据字段分派遗漏

nsign、owner 进入 generic decode_tree，直接 int 被保留，等值 Fraction/decimal 被当作连续量；超大整数错拒，小分数又会作为 float 通过。修前 2 格报 `unbounded integer schema rejected`；入口现复制源 dict，按明确 integer schema 规范 nsign/owner。添加分数不许截断门；不添加未约定的状态值范围限制。

### 同类 S-O04-2：bdda3d 已知连续字段依赖 token 类型或配对存在

d1、fa/coh/tens 作为 extra 时，巨大 int 绕过 decode_tree 的 float/Fraction 分支；单独 t1 或 t2 被 _KNOWN 吃掉，只有成对时才构造 params，因此完全绕过检查。修前 6 格均 `Failed: DID NOT RAISE <class 'eab.numeric_domain.ConstructionDomainError'>`。入口现在逐个按连续 schema 检查 6 个字段：整数字面量不能绕过连续域，缺配对也不能绕过。源 dict 用复制保留，不原地改用户输入。

## 真实内部变异

o04_mutation_probe.py 在内存重编译生产函数并替换模块入口，然后运行未包装的普通看护测试。没有改输出、没有写回生产文件。9 项日志与退出码汇总在 o04_mutations.json，全部 exit_code=1，每项 `1 failed`，且红的是预期断言：

| 变异 | 普通门红因 |
|---|---|
| parser：把 _decimal 中早期 scalar_rational 加回 | unbounded integer schema rejected an exact integer |
| nsign/owner：各去掉 integer 规范一步 | unbounded integer schema rejected an exact integer |
| d1/fa/coh/tens/t1/t2：各移出已知连续 schema 元组 | DID NOT RAISE ConstructionDomainError |

最小重跑：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 reports/codex/R15FIX_evidence/o04_mutation_probe.py parser`（预期退出码 1）。完整集内对应 9 条 mutation-tooth 测试捕获预期红，因此总体仍绿。

## 扫描覆盖与边界

- o04_schema_scan.txt：全部 src/eab/readers/*.py，ContactRecord，bdda2d adapter，以及 tools/bdda3d_document 的 float/int、scalar、tree、loads 分派检索。
- o04_json_scan.txt：src/tools 下全部 JSON parser 检索。运行时数字入口只有 numeric_decode 的 parse_float；其它 json.load 是 fixture/provenance/静态策略 manifest，不混入几何输入 schema。
- 已检查 ContactRecord 已知连续标量/向量、Feature 整数、extra 树，bdda3d reader/document，b-DDA CSV/TF 探针连续读取和 M4 detparams。CSV 整数字段仍遵守其整数文字格式，无 JSON 指数拼写承诺。
- tools/bdda3d_document 已对 owner/nsign/refs 采用 integer schema，不需生产改动。known _REAL 最后逐一 scalar 检查，巨大 int 不会漏收。未知 metadata 保留规则不扩大。
- 未扩大为任意未声明字段/类型的完整 schema 校验；不声称 G6 独立退出。
