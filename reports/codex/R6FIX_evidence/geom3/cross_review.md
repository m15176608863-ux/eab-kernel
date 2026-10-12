# 只读交叉复核：root 构造量、2D 接触与 margin 缓存

范围：`src/eab/construction.py`、`kernel2d/covers.py`、`kernel2d/entrance.py`、`margin.py` 及 `tests/test_r6fix_construction.py`。本复核没有修改源码或测试，只增加本目录的可重跑检查和证据。

## 结果

本轮未确认新缺陷；不等于全输入空间证明，也不替代六路独立 G6。

1. **有理平方根**：审查指数拆分、相邻浮点 bracketing、精确平方中点、ties-to-even、显式显示下溢。另以 1600 位 Decimal 平方根作不同实现参考：固定种子随机尺度加最小 subnormal、普通数和大尺度的中点两侧，共 **1036** 个结果与最终 binary64 完全相等。不可表达非零数默认 ArithmeticError，超范围默认 OverflowError；`allow_underflow=True` 是显式显示模式。
2. **2D 原始差分与接触见证**：VE/EV/FF 的新 gap 符号与旧法向约定逐式核对；FF 选择两条反向边中的较长边时方向一致。用 3–4–5 有理旋转、2^-600/1/2^600 尺度、左右两种进入方向，**6** 个接触同时满足精确进入时刻 1、gap=0、A/B 接触见证相同。
3. **margin 缓存产物**：`_surface_payload` 保存不可变输入 tuple 和 labels；`_resolved_cached` 保存 Cover3 字段 tuple，读取时新建 Cover3 和 rows list。实际替换所有返回记录的身份/normal/point/params，并清空 rows，再读值与原始完整签名一致；清空 surface view 的 vertices/faces 后再读也完整恢复。
4. **08 投影/法向**：审查确认 exact=True 返回有理全局点，距离先 exact 相减后平方，法向先 exact 相减再按最大分量缩放；不会再从默认 float display 点反减。
5. **单个边界语义**：`sqrt_rational` 将数学根大于 max-finite 视为超输出范围并响亮失败；不承诺 IEEE 溢出区间内仍舍入到 max-finite。与其文档中的范围失败策略一致，不列缺陷。

## 证据与重跑

- [cross_review.py](cross_review.py)：独立 Decimal 根号、旋转接触、缓存多字段污染检查。
- [cross_review.log](cross_review.log)：实际输出。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/R6FIX_evidence/geom3/cross_review.py
```

最后一行：`CROSS_REVIEW_PASS`。
