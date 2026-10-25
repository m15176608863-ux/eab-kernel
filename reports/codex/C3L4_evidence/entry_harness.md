# WO-C3L4 harness 入口与实施接口计划

## 状态与边界

- 2026-10-23 只读审计完成；开工四分片基线进行中，尚未修改源码或执行差分。本文件为计划，不是完成声明。
- 写域：`tools/eab2_c3l4_diff.py`、必要的 `tools/eab2_c3l4_abi.py`、`tests/test_eab2_c3l4_harness.py`；最小扩展 L3 冻结能力下限；输入复制到 `tests/data/`。不改 `src/eab`。
- 回滚锚点：入口 b34c966；不执行 Git 写操作。全档仅 root 统一运行，本代理不启动。

## 入口订正（不是设计冲突）

1. 当前 L3 `compare` 已对 Python-only / C++-only exact_threshold 做对称独立证书核验与四字段规范化，已有参数化具名门。工单 4(a) 的非对称现状不适用于入口字节，不重复改写正确逻辑。
2. T1b 当前验收已经升级三个括号点 13/16/30；36 点中 A 方向 smooth 26、t 方向 smooth 28；8 无理点仍未证，2 个 A=0 的 A 方向无有效骨架。“23 点”是旧范围，下限以当前冻结证据为准。
3. tia2d-2：114 cases、280 sensitivity，limit 160 / critical 120；73 smooth、2 one_sided、36 singular、169 unresolved；全部 quality=exact_jet。quality 不能单独解读成存在认证斜率。

## 待对接 C ABI

实际名称/布局由 ABI 代理依据头文件冻结，所需语义：

- 目标绑定 limit / critical 已求解对象或可重求解请求，不接受伪造结果 JSON。
- 显式参数数、输出数、通道数、数组元素数和 stride，固定行主序。
- geometry_seed：参数名、稳定 vertex/body IDs、vertices[param][vertex][2]、dead/live[param][body][3]、dof_anchor[param][body][2]、mu[param]，均为 canonical 有理字符串。
- 正反方向有效性及 validity_conditions 保真；顶点按原 ID，不以 CCW 容器位置替代身份。
- 返回 Python SensitivityResult2 的语义字段，并公开实际传播 dA/db/dc 与行列标签（或单独传播函数）。
- wrapper 可复用 C3L3Dll；consumer 不得导入任何 harness/生产 Python 模块。

## 差分流水线

1. formal loader：独立 JSON/IEEE bits/有理解析、gzip 分片 SHA/长度核验、query indices 无漏重；保留全部 sensitivity，显式绑定 limit_query_ref/threshold_query_ref。
2. 以 C3L3 rebuilt_problem 从原始边/顶点 ID、荷载、anchor 重建 A/b/c；接触选择由 Python 裁判提供，不信任 C++ 导出 tangent/normal/matrix。
3. 独立传播：核稳定 ID 排序、形状、共享点种子一致性；原始边求 T/dT、N/dN、g/dg；力矩 (p-anchor)×g 的导数含 dp-danchor；荷载含 reference 到 anchor 力矩转换与移动 anchor 项；live 导数进入 A，dead 导数进入 b。与 frozen seed 和 C++ 派生 seed 精确比对。
4. limit：核原始最优证书；stable 基独立验秩、正基值、非基约化成本与包络；singular 验两侧回收射线、null 斜率；Mills/Freund 重建 ±d LP，核 primal/dual 可行、目标等值、D+/D- 符号。
5. critical：先核临界证书及多项式/延续；开闭选仍有效 branch；Fraction 消元解状态与 p/mu 变分，逐真正越零分量核 phi_p、phi_mu、-phi_p/phi_mu 及标签；证据不足不得认证斜率。
6. 严格比较 differentiability、quality、parameter、model、method、reason、validity_conditions、directional/left/right、D+/D-、tied/near labels。非唯一 basis/witness/selected piece 先数学核验再规范化，不放松状态或精确标量。
7. 仅保存逐查询摘要/计数/核验结论/差异，不复制整套冻结证据；记录源码前后 hash、DLL hash、计时边界、原始末行。逐 case 落盘进度，中断不标完成、不拼日志。

## 冻结证明能力下限

新增 require_python_proof_floor，不替代通用双向比较；独立核验后，仅 frozen formal/T1b 要求 Python 已认证非空 exact_threshold 或斜率在 C++ 不退 null。默认空例外表；例外必须 stable case/query ID + 非空理由，禁 wildcard。报告 checked/passed/exception 数量。

门区分：通用 Python-only 可过，frozen Python-only 拒绝，C++-only 可过，双方非空数值/开闭不符拒绝，Python null 不强迫 C++。

## T1b 输入与期望

- 将 acceptance_fix/p1_classification.json 的最终 36 rows 必要期望与来源 hash 复制为小 tests/data 输入，避免依赖报告或外部历史归档；保留来源，不修改旧证据。
- adapter 仅生成原始几何/共享顶点 jets；期望斜率来自冻结 rows，不由 C++ 或本次 Python 求解生成。实时 Python 作完整合同裁判并独立核证。
- 厚度复用 binary64 分区：7 样点 + 18 controls，19 唯一模型；32 非 binary64 完整模型明确排除，不舍入冒充。新增合理排除逐例记录。

## 定向 checker 门

- formal inventory、绑定/重复 JSON/坏 SHA/维度拒收。
- frozen dA/db/dc 核验覆盖 live、dead、anchor、共享点、CW 原 ID。
- 错 seed/符号/y/Mills witness/回收射线/阈值 phi/漏 tied labels 均拒绝。
- proof_floor 与通用对称语义分离。
- 修改 JSON 的 checker 门不冒称生产内部变异；P1 另作内部源码变异。

## 计划验证命令（尚未执行）

```powershell
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp reports/codex/C3L4_evidence/tmp/harness tests/test_eab2_c3l4_harness.py tests/test_eab2_c3l3_harness.py
python -X utf8 tools/eab2_c3l4_diff.py --dll D:/eab-wt/cx-c0/eab2/build/eab2.dll --family all --output reports/codex/C3L4_evidence/l4_differential.json
```

C0/C1/LP/L1/L3 分别使用 eab2_diff.py / eab2_diff_c1.py / eab2_opt_diff.py / eab2_c3l1_diff.py / eab2_c3l3_diff.py。
