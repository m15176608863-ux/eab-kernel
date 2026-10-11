# E5a G2 下游最小适配

## 红线事件：本轮不能作为有效工单验收

我首次执行 G2 回归时漏传 `--basetemp`，pytest 在授权工作树外
`C:\Users\m1517\AppData\Local\Temp\pytest-of-m1517\pytest-1058` 创建了 54 个测试输出文件、55 个目录（含根）。
文件创建/修改时间与本次日志区间吻合，全部 54 个文件与随后树内指定 basetemp 复跑逐字节相等；
其中包含本轮新增牙独有的 `moved_real_cover_tooth.json`。只读核查明细见 `scope_violation.json`。
没有擅自删除/移动外部文件。pytest 是否清理过更早的临时目录缺乏运行前快照，不能断言没有。
树内复跑 **125 passed in 9.83s**（`g2_adapter_verified.log`）只证明留树可用，不能抹除已发生的红线违规。
本审计不证明本轮其它直调 pytest 无树外写入。主线程另报告一次没有持久日志、未设 basetemp 的
G2 `--maxfail=2` 调用；相邻 `pytest-1057` 确有更早的 G2 临时产物，与该叙述一致，但缺少日志/进程审计，
不能精确建立命令—目录因果链。逐路径事实和非穷尽限制已追加到 `scope_violation.json`，不得把事件说成仅代理一次。

## 改动与局部验证（不代表有效验收）

- 修前日志 `g2_final.log`：34 failed, 90 passed in 8.46s。
- 失败分类：1 格历史机器报告仅 top face 编号 5→4；27 格舍入运动后的精确拓扑/局部盖不再等于理想旋转；6 格小倒角面数不再恒为 7。
- `tools/g2_bdda3d.py` 不再先浮点减原点、取 hull 后浮点加回；直接对保留的原始坐标建立精确凸包并精确回映。按原顶点集合稳定排序面，基础 fixture 的历史 top face 编号恢复，历史报告无需改写。
- 原 legacy 三角在精确 hull 上没有对应面时，保留全部引用及唯一负标签，并明确记入 `violations`；不近似配面、不忽略入口、不提前终止其它盖的对账。它是真差异，不声称 legacy 与精确浮点模型仍同构。
- 27 个原运动格对同输入独立支持三元组/局部盖/参数/构造/对账 oracle 逐字段相等。9 个倒角格对精确支持面全量检查，10 个原顶点、alias、manifold 均有门。详见 `g2_test_rewrites.json`。
- 新牙从 `compare` 内部窗口裁决删去真实首盖，独立逐字段门报红；正确函数先在同输入通过。未删除/弱化原 alias、hash、机器报告、基础同构和带窗口缺陷门。
- 验证：`python -X utf8 -m pytest -q tests/test_g2_bdda3d.py --tb=short` → **125 passed in 9.88s**，日志 `g2_adapter1.log`。
- 边界：历史 alias 导入函数的近重复长度窗口及舍入地板本单未改语义；它不是精确成员谓词。原始核中的 `window` 仍读取浮点 gap，本次 oracle 逐字段核验的是该现有窗口构造口径，不声称已完成窗口边界精确化。
