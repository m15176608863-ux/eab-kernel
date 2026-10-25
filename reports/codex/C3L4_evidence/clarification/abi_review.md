# WO-C3L4 Claude 澄清：ABI / consumer 复核

## 结论与本次范围

2026-10-23 按主代理转达的 Claude ruling，现有独立标准库 ctypes consumer 已满足设计 §8.5，Claude 在验收环节亲自运行；本单不再等待另行安排“真实人工使用者”。本条覆盖旧 [abi_scope_review.md](../abi_scope_review.md) 中将人工复跑列为额外未完成项的推断，不回写历史执行日志，也不宣称本子任务执行了新的验收复跑。

旧报告的 32 项 `tied_labels` RED 是旧严格集合比较口径下的原始结果。后续应按本次裁定，对双方各自的临界基证书与全部越零标签/斜率独立核验并登记差异；是否通过本轮最终门以主代理的新执行证据为准。本次文案修订不声称数学门已绿，不修改任何数值或输出标签。

本次只修改 [ABI_CONTRACT 正文](file:///D:/eab-wt/cx-c0/eab2/ABI_CONTRACT.md) 的顶部和冻结节两段，新增本记录。冻结 marker 内字节、31 个函数、28 个结构、字段类型/偏移/尺寸、能力位及所有生产/测试代码均不改。机器表的 `release_acceptance=pending_full_work_order_and_real_human_TIA_consumer` 是历史元数据，按要求保留；合同正文明确其不代表当前仍缺使用者验收条件。

## 极短审核（不加载 DLL）

仅调用公开头解析器和冻结比较函数，核 `abi_version/platform/exports/signatures/capabilities/supported_capabilities/structures`。这不是完整发布门，不验证 PE 导出或新构建运行时；结果及冻结表字节 SHA 见本记录末尾。未运行构建、六层差分、pytest 全档或 consumer；最终执行由主代理统一完成。

## 完整构建之后的主代理命令

工作目录：`D:/eab-wt/cx-c0`。以下是待执行命令，不是本轮成功记录；Python 可沿用已核存在的 `C:/Program Files/Python312/python.exe`。

### 发布 ABI 门

```powershell
& 'C:/Program Files/Python312/python.exe' -B -X utf8 tools/eab2_release_abi.py `
  --dll 'D:/eab-wt/cx-c0/eab2/build/eab2.dll' `
  --header 'D:/eab-wt/cx-c0/eab2/include/eab2/c_api.h' `
  --contract 'D:/eab-wt/cx-c0/eab2/ABI_CONTRACT.md' `
  --output 'D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/release_abi.json'
```

成功必须同时满足进程退出 0、JSON `status=PASS` / `findings=[]` / `export_count=31` / `structure_count=28` / `header_and_frozen_equal=true` / `supported_capabilities=581501`，且 DLL/header SHA 与本轮受测产物相等。stdout 原始最后一行必须为：

```text
EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0
```

该工具直接读取完整 PE32+ 导出表，核所有公开声明/冻结表/结构字段规范 C 类型及运行时能力，不是仅探测已知符号是否存在。

### 独立 consumer 的最小隔离复跑

**先刷新复制品，不能沿用上轮 DLL 当成本轮构建。** 在工作树内新的中性构建临时目录（建议 `eab2/build/tmp/c3l4_consumer_clarification`）只放以下 10 个文件，并记录逐项来源、字节数、SHA-256：

1. `tools/eab2_tia_consumer.py` → `eab2_tia_consumer.py`。
2. 本轮完整构建的 `eab2/build/eab2.dll` → `eab2.dll`；禁止测试 DLL。
3. `eab2/include/eab2/c_api.h` → `c_api.h`。
4. 正式 `fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64/manifest.json` → `fixtures/manifest.json`。
5. 同目录 `g1_unreversed_t1.part001.json.gz`、`g1_slender.part001.json.gz`、`g5_n3_mu0.part001.json.gz`、`g5_n3_mu1.part001.json.gz`、`g5_n3_mu2.part001.json.gz`、`g5_n3_mu3.part001.json.gz` → `fixtures/`。

该目录不得有 `src/eab`、差分 harness、pybind、姊妹仓库或测试 DLL；它是最小字节副本，不称 Git 新鲜树。

```powershell
Push-Location 'D:/eab-wt/cx-c0/eab2/build/tmp/c3l4_consumer_clarification'
try {
  & 'C:/Program Files/Python312/python.exe' -B -I -S -X utf8 .\eab2_tia_consumer.py `
    --dll 'D:/eab-wt/cx-c0/eab2/build/tmp/c3l4_consumer_clarification/eab2.dll' `
    --header .\c_api.h --fixtures .\fixtures `
    --output 'D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer.json'
} finally {
  Pop-Location
}
```

主代理须读取 Python 退出码（不能只取 PowerShell finally 的成功），保存全部 stdout 的唯一压缩日志、完整命令、cwd、耗时、复制清单与 SHA；可沿用 `consumer_isolation.json` / `consumer_isolation.log.gz` 的既有格式。上一轮证据已由主代理在 clarification intake 归档，当前 consumer.json 保留一份权威输出。

成功必须同时满足退出 0、JSON `status=PASS`、`consumer=independent_stdlib_ctypes`、`python_isolated=true`、`mismatch=0`、6 个 case 全 PASS、`sensitivity_queries=18`、能力 581501，且输出 DLL/header SHA 等于本轮复制来源。程序逐例打印承载力/阈值和每条导数 D+/D−；完整链包含 body/entrance → contact → lock/first_order → limit → critical → retained-result sensitivity。原始最后一行必须为：

```text
EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0
```

代表例调用链消费与全语料独立数学裁判的职责仍不同：consumer 的 6/18 绿不能替代全部 L4 及 T1b 证书验证。此范围说明不再被用作额外人工使用者阻塞项。

## 本次纯头审核实测输出

执行：Python 3.12 -B -X utf8；读取 PublicHeader、frozen_contract、header_contract 后调用 differences，并逐字节比较修订前后的冻结 marker 内内容。未加载 DLL。

```text
ABI_HEADER_REVIEW exports=31 structures=28 findings=0 frozen_bytes_unchanged=true
frozen_block_sha256=71ef011f4aca716a8baeccb39de372f2ee7414c9b77ba2cb2fe00eea96b73f41
header_sha256=6d70c524f1914302e06363806032c4139e884967f7377c5369c9ce0b4c1b1993
contract_sha256=899b6a777df108aae931572edab6fb2011ee01324eb6568cbc16133756f975cb
UTF8_NO_BOM cjk_preserved=true
```
