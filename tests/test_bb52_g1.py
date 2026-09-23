"""G1 一级门（bb52 步 1，legacy 兼容模式）+ G0 真几何自证。G1 数字于 2026-09-18 钉死。

牙：cone_tol 退回严格 0 时 legacy-only 必须 > 0（证明这道门真的在测法锥容差这件事）。

G0 于 2026-09-24 重做（审查盲区 1）：旧版用 sign(min gap) 当凹块成员谓词，这条规则是假的
（细臂 L 块反例钉在本文件末尾）；现在真值一律暴力 `polygons_overlap`，盖侧检验距离完备性。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import bb52_g0  # noqa: E402

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "bdda_df" / "studio_20260712"
pytestmark = pytest.mark.skipif(not (FIX / "bdda_debug_verts.csv").exists(), reason="bb52 fixture missing")


@pytest.fixture(scope="module")
def result():
    # samples_per_pair=60, seed=0：与 2026-09-18 报 "1186/1186" 的那次逐位相同的平移序列
    return bb52_g0.analyze(samples_per_pair=60, seed=0)


def test_geometry_reconstruction(result):
    assert result["blocks"] == 11
    assert result["stripped_duplicates"] == 22          # 每块两个回绕重复点
    assert result["convex_blocks"] == 3


def test_g1_tier1_all_legacy_ve_reproduced(result):
    assert result["ve_legacy"] == 53
    assert result["ve_common"] == 53
    assert result["ve_legacy_only"] == []
    assert result["matched_gap_max_abs"] < 1e-6          # 初始位形全贴合


def test_g1_tier1_extras_are_vertex_on_vertex_representation(result):
    # eab 多出的顶点-边盖：除 1 条锥边界情形（legacy 记为 v-v [126,171]）外全部在边端点
    assert result["ve_eab_only_endpoint"] >= 26
    assert len(result["ve_eab_only_mid"]) <= 1
    if result["ve_eab_only_mid"]:
        v, e, gap, s = result["ve_eab_only_mid"][0]
        assert v == 171 and sorted(e) == [124, 125]


def test_g1_tier2_vertex_block(result):
    assert result["vb_legacy"] == 45 and result["vb_common"] == 45
    assert result["vb_legacy_only"] == []
    assert result["vb_eab_only_mirror"] >= result["vb_eab_only"] - 1     # 至多 1 个非镜像（即上面那条）


def test_g0_distance_completeness_real_concave_geometry(result):
    """bb52 真几何（8/11 凹块）上的 G0，2026-09-24 重跑，如实钉数。

    同一批 21 块对 × 60 = 1260 次平移（旧投票当初计入其中 1186 次）。暴力谓词：相交 657、
    仅接触 0、分离 603。分离样本上距离完备性 603/603，最大绝对误差 0（见证距离与暴力距离逐位相等）。
    **相交的 657 次不受任何门检验**——凹块成员谓词要等入口块全局构造（M3）；旧 "1186/1186"
    里有 621 次正是这类相交样本，它们当时靠一条假规则"通过"。
    """
    assert result["g0_proposition"] == "distance_completeness"
    assert result["g0_draws"] == 1260
    assert (result["g0_brute_overlap"], result["g0_brute_touch"], result["g0_samples"]) == (657, 0, 603)
    assert result["g0_agree"] == result["g0_samples"], result["g0_disagree"]
    assert result["g0_worst_abs_error"] <= 1e-12


def _drop_vv(monkeypatch):
    import eab.kernel2d.covers as cv
    monkeypatch.setattr(cv, "vv_cover", lambda *a, **k: None)


def _drop_cone_boundary(monkeypatch):
    import eab.kernel2d.covers as cv
    orig = cv.in_cone
    monkeypatch.setattr(cv, "in_cone", lambda cone, v, tol=0.0: 1 if orig(cone, v, tol) == 1 else -1)


@pytest.mark.parametrize("mutate", [_drop_vv, _drop_cone_boundary], ids=["no_VV_covers", "strict_cone_only"])
def test_g0_distance_completeness_has_teeth(monkeypatch, mutate):
    """门要有牙：两种现实的盖枚举退化（丢零维 VV 盖；只收法锥严格内部、丢边界盖）都必须让 G0 红。

    对照（2026-09-24 scratch 实测，同一批平移）：丢 VV 盖时旧投票门仍报 1186/1186，完全无感；
    只收严格内部时旧门 106/110。旧门检验的命题与盖枚举是否完备基本无关。
    """
    mutate(monkeypatch)
    r = bb52_g0.analyze(samples_per_pair=60, seed=0)
    assert r["g0_samples"] > 0
    assert r["g0_agree"] < r["g0_samples"]
    assert all(d[-1].startswith("盖漏枚举") for d in r["g0_disagree"]), r["g0_disagree"][:2]


def test_gate_has_teeth_strict_cone_loses_legacy_contacts():
    strict = bb52_g0.analyze(samples_per_pair=0, cone_tol=0.0)
    assert len(strict["ve_legacy_only"]) > 0


# ---------------------------------------------------------------- 审查盲区 1 的反例（2026-09-21）

THIN_L = [(0.0, 0.0), (3.0, 0.0), (3.0, 0.1), (0.1, 0.1), (0.1, 3.0), (0.0, 3.0)]   # 臂厚 0.1 < D0，CCW
NOTCH_BOX = [(0.3, 0.11), (0.8, 0.11), (0.8, 0.16), (0.3, 0.16)]                   # 0.5×0.05，悬浮于臂上 0.01


def _l_notch_blocks(*_a, **_k):
    return ({1: {"poly": list(THIN_L), "vidx": list(range(6)), "flipped": False},
             2: {"poly": list(NOTCH_BOX), "vidx": [10, 11, 12, 13], "flipped": False}}, {})


def test_g0_gate_no_false_alarm_on_thin_arm_L_notch(monkeypatch):
    """审查盲区 1 的反例钉成门：细臂 L 块 + 凹槽内悬浮方块，走 `analyze` 的同一条 G0 路径。

    盖系统在这组几何上没有错（见 test_kernel2d_review 的距离完备性门），所以一道正确的 G0
    在这里必须零失配；旧 G0 用 sign(min gap) 当成员谓词，方块顶角对 L 块**外**底边的非严格 VE 盖
    （gap≈−0.16，落在窗口 D0 内）让它把分离判成相交——旧门在这里红，说明旧门检验的是一条假命题。
    """
    monkeypatch.setattr(bb52_g0, "load_blocks", _l_notch_blocks)
    monkeypatch.setattr(bb52_g0, "legacy_contacts", lambda *a, **k: [])
    r = bb52_g0.analyze(samples_per_pair=60, seed=0)
    assert r["g0_samples"] > 0
    assert r["g0_agree"] == r["g0_samples"], r["g0_disagree"][:3]
