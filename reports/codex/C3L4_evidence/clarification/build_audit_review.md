# WO-C3L4：fresh 子目录构建审计修复只读复核

## 结论

**未发现本次筛选修复放宽既定 authored 源码范围或编译合同。** 修复仅在 `authored` 编码/换行扫描中显式排除既有 ignored `ROOT/eab2/build`，同时保留调用方 `args.build` 与已独立核验的 vendor 排除。原来默认 `--build=eab2/build` 已经排除整个该树；改用 `--build=eab2/build/clarified` 时，旧逻辑只排除了该子目录，误将同一 ignored 树下的旧 DLL/obj/变异构建当成手写 UTF-8 源文件。本次恢复的是原默认构建的扫描集合，不是新增数值或源码准入。

本轮只有读取源文件/历史 ZIP/失败 JSON、内存 AST 比较与路径集合核验；未运行构建、实际 DLL 审计或任何长测试。只新增本记录，不编辑源码或报告。

## 直接核验

1. 从 [prior_delivery.zip](file:///D:/eab-evidence/reports/codex/C3L4_evidence/clarification_20261023/prior_handoff/prior_delivery.zip) 读取原 `tools/eab2_audit.py`，与当前源码构造 AST；仅将当前 `authored = [...]` 赋值替换成旧赋值后，**整个文件 AST 完全相等**。这证明本次修改没有改变编译标志、工具链版本、依赖、DLL身份或导出检查的执行逻辑；注释不进入 AST。
2. 对当前文件树计算三个集合：旧默认 build 的 authored 集合、旧 nested build 的集合、新 nested build 的集合。**新 nested 集合等于旧默认集合**；两者保留 `eab2/` 43 个文件（vendor 与整个 ignored build 除外），所核40个 CMake/ABI合同/生产源码/公共头/测试源码全部仍在集合内。`tools/eab2_*.py` 追加范围未改。
3. 旧 [build_audit.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/tmp/clarified_final/build_audit.json) 实有570项 findings，逐项路径均位于 `eab2/build/`。未发现被此次过滤遮掉的源码树路径或编译合同失败。该失败记录应保留，不把新复跑结果拼接覆盖。
4. `.gitignore` 既有 `build/`、`eab2/**/build*/` 及编译产物规则，未修改。新筛选没有扩成“忽略全部二进制后缀”或“忽略任意名为 build 的 authored 目录”；只恢复固定已知 `ROOT/eab2/build` 边界。

原样只读核验输出：

```text
BUILD_AUDIT_REVIEW rest_of_AST_unchanged=true established_authored_scope_equal=true retained_eab2_files=43 required_source_header_test_files=40
OLD_FAILURE_REVIEW findings=570 all_under_ignored_eab2_build=true
audit_source_sha256=0f0a566fc0404dfc580f5bd071ef5b21a149bf5873e649048002a6b9eb3561b9
```

## 未改变的验证与边界

- `compile_commands.json` 仍来自实际选定的新 build；仍逐条检查 `/O2 /MD /utf-8 /fp:precise`、C++20、`/permissive-`，拒 `/arch:*`、`/GL`、fast/contract，并核指定14.44.35207工具路径。
- Ninja header 依赖、真实编译器 `/Bv`、DLL嵌入身份、AVX源码保护、vendor逐文件哈希/大小/库存、生产/测试入口隔离与尺寸卫生调用均 AST 未变。
- 发布/测试 DLL 仍从实际 `args.build` 加载；此次 authored 过滤只用于编码/BOM/混合换行检查，不排除新 DLL 的编译身份/能力/导出验证。
- fresh CMake `clarified_r2` 的完整重跑由主代理执行。本审查不宣称它已通过；也不把构建目录当作新鲜 Git 工作树或独立对抗验收。
