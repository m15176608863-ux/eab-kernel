# src/eab 数值候选逐站点源码审核（raw round 2）

- 对 raw round 2 的 **594 站点 / 18 源文件**逐项记录 path、function、rule、原始 AST node、源码、理由和 disposition；没有读取或依赖旧 16936 waiver。
- 仅审核数值 constructor / arithmetic / reduction / rounded-call 与 legacy rule；其他反射、文件I/O、decorator未知不在此子任务范围。
- 这是人工源码证据，不是最终 policy 批准，不是一次新的独立六路 G6。审核者此前只执行了本单的动态语法机械改写。

## 分类

- `SOURCE_PROOF_GAP`：344
- `REVIEWED_FINAL_OUTPUT_OR_DATA`：8
- `SCOPED_MODEL_OR_DIAGNOSTIC_NOT_EXACT_APPROVAL`：156
- `SOURCE_PROOF_GAP_CALLER_SENSITIVE`：25
- `LEGACY_APPROX_NOT_EXACT`：61

`SOURCE_PROOF_GAP`：源码链说明原始坐标已先 Fraction 化/事件根有理/证书完整，但分析器尚未证明；应补类型与参数敏感数据流，**不得把这些站点当作人工豁免去凑数**。

`SOURCE_PROOF_GAP_CALLER_SENSITIVE`：geom3 的 sub/add/dot/mul/norm/unit 等泛型原语可能收到 float 派生量。不能全函数豁免，应保留调用方 taint，拒绝具体不安全 sink。

`LEGACY_APPROX_NOT_EXACT`：例如未使用的 covers3._orth、kernel2d.geom._tri_axes 真有 float 差分/投影后构造。geom3 的旧候选方向链也存在近似；最终候选内点虽可精确核验，不等于候选法向本身是 exact。按父任务指示只记录技术债，不改旧数学算法，不伪称不存在舍入。

`SCOPED_MODEL_OR_DIAGNOSTIC_NOT_EXACT_APPROVAL`：显式随机/采样模型、有限差分诊断、名义 cover 标签候选、力显示及误差预算。必须明确使用边界；exact 几何/LP 证书另外存在。此分类同样不是自动 waiver 批准。

完整站点清单：[src_numerical_review.json](src_numerical_review.json)。
