# Kernel 四项交叉发现最终复核

**四项全部关闭，当前四项复核残留 = 0。** 这里只关闭本交叉审查发现的覆盖缺口，不代表全部 77 项已通过独立 G6。

| API | 最终状态 |
|---|---|
| `kernel2d.g0.g0_distance_completeness` | closed；前次复核已确认非零误差及完整失败 payload |
| `kernel2d.g0.g0_exit_completeness` | closed；前次复核已确认非零见证及完整失败 payload |
| `kernel3d.exact_sweep.surface_events` | closed；前次复核已确认独立每 `(label,time)` 绑定 |
| `kernel3d.g03.g0_distance_completeness3` | **closed**；本次补齐非空 `completeness_failures` |

最后新门 `test_3d_g0_nonempty_completeness_payload_matches_omitted_nearest_face` 在**真实 `enumerate_covers3` 的 `vf_cover` 调用位置**遗漏 face 3，未在枚举后追加假盖，未在报告后拼接 payload。其余盖仍来自真实生产构造。

解析参考：真实最近面距离 `3s`；遗漏该 VF 族后保留的最近候选距离 `5s`，来自坐标分量 `(3s,4s)` 的边距离等。因此独立核对 `minimum2=25s²`、`truth2=9s²`，并完整比较 `worst_abs_error=2s`、`got=5s`、`truth=3s`、非空失败列表与构造失败列表。

三档为 `2^-400, 1, 2^395`，扩大后的几何最大坐标 `24s < 2^400`。这次调整让高档仍在声明工程输入范围内，并非规避某输出失败。

只读复跑结果保存在 `kernel_cross_review_final.log`；同名 JSON 保留命令、时间、测试文件执行前后相同 SHA256 和四项最终状态。

覆盖清单已引用最后新门。另发现其最新 proof / limits 中存在连续字面 `?`（文本编码损坏），且顶层 scales 仍列主格 `2^397`；建议主代理修复可读说明，并标明 3D 失败子族高档为 `2^395`。这是证据元数据整理事项，不是仍未关闭的数值门缺口。
