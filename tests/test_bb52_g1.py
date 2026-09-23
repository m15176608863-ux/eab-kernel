"""G1 一级门（bb52 步 1，legacy 兼容模式）+ G0 真几何自证。G1 数字于 2026-09-18 钉死。

牙：cone_tol 退回严格 0 时 legacy-only 必须 > 0（证明这道门真的在测法锥容差这件事）。

G0 于 2026-09-24 重做（审查盲区 1）：旧版用 sign(min gap) 当凹块成员谓词，这条规则**两个方向都是假的**
（分离判相交：细臂 L 块；相交判分离：槽角楔块——两条反例都钉在本文件末尾）。现在真值一律暴力
`polygons_overlap`；盖侧检验定理"∂E ⊆ ∪ 有效盖线段"的两面：分离样本上的距离完备性、相交样本上的出口完备性。
凹块的成员谓词本身仍无门（要等入口块全局构造，M3）。
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
    相交的 657 次由出口完备性检验（下一条）；它们的**成员判定**不受任何门检验——凹块成员谓词要等入口块
    全局构造（M3）。旧 "1186/1186" 里有 621 次正是这类相交样本，它们当时靠一条假规则"通过"。
    """
    assert result["g0_proposition"] == "distance_completeness"
    assert result["g0_draws"] == 1260
    assert (result["g0_brute_overlap"], result["g0_brute_touch"], result["g0_samples"]) == (657, 0, 603)
    assert result["g0_agree"] == result["g0_samples"], result["g0_disagree"]
    assert result["g0_worst_abs_error"] <= 1e-12


def test_g0_exit_completeness_real_concave_geometry(result):
    """相交的 657 次平移上的 G0：出口完备性（2026-09-24 新增，补上旧门被删后这 657 次无门可检的缺口）。

    每次相交平移配一个随机方向（独立 rng，不动平移序列），暴力求沿该方向首次离开 E 的 ∂E 点 z，
    要求 z 处有效盖的最小见证距离为 0：657/657，最坏 1.8e-15（门限 1e-12）。检验的是"∂E ⊆ ∪ 有效盖线段"在 E 内侧的
    那一面；**不是**成员谓词（凹块成员判定仍待 M3）。
    """
    assert result["g0_exit_proposition"] == "exit_completeness"
    assert result["g0_exit_samples"] == result["g0_brute_overlap"] == 657
    assert result["g0_exit_agree"] == result["g0_exit_samples"], result["g0_exit_disagree"]
    assert result["g0_exit_worst_witness"] <= 1e-12


def _retired_vote(r):
    """重放 2026-09-18 版的旧投票（**已退役的规则**，只为对照）：sign(min gap over 非 VV 盖) 当成员谓词，
    计入条件 = 有非 VV 盖、|min gap| > 1e-9、暴力谓词非 0。返回 dict：计入 total、与暴力一致 agree、
    计入者中暴力相交 overlap、误报相交 false_alarm（暴力分离、投票相交）、漏报相交 false_negative（反之）。"""
    import eab.kernel2d.covers as cv
    from eab.kernel2d.geom import polygons_overlap, translate
    blocks, _ = bb52_g0.load_blocks(1)
    out = dict(total=0, agree=0, overlap=0, false_alarm=0, false_negative=0)
    for bi, bj, xs in bb52_g0.g0_draws(r["g0_pairs"], 60, 0):
        A, B = blocks[bi]["poly"], blocks[bj]["poly"]
        for x in xs:
            At = translate(A, x)
            brute = polygons_overlap(At, B, 1e-12)
            pen = min((c.gap for c in cv.enumerate_covers(At, B, window=bb52_g0.D0, tol=bb52_g0.TOL)
                       if c.kind != "VV"), default=None)
            if pen is None or abs(pen) <= 1e-9 or brute == 0:
                continue
            vote = 1 if pen < 0 else -1
            out["total"] += 1
            out["agree"] += vote == brute
            out["overlap"] += brute == 1
            out["false_alarm"] += (vote, brute) == (1, -1)
            out["false_negative"] += (vote, brute) == (-1, 1)
    return out


def test_g0_rerun_replays_the_original_1186_translations(result):
    """看着"同一批平移"与"旧 1186 里 621 次是相交样本"这两句话：在 analyze 用的同一平移序列上重放旧投票，
    必须恰好复现当初的 1186/1186，其中暴力相交 621。"""
    v = _retired_vote(result)
    assert (v["total"], v["agree"], v["overlap"]) == (1186, 1186, 621)


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

    对照（同一批平移、同一退化下重放旧投票）：丢 VV 盖时旧门仍报 1186/1186，完全无感；
    只收严格内部时旧门 106/110。旧门检验的命题与盖枚举是否完备基本无关。
    """
    mutate(monkeypatch)
    r = bb52_g0.analyze(samples_per_pair=60, seed=0, exit_probes=False)
    assert r["g0_samples"] > 0
    assert r["g0_agree"] < r["g0_samples"]
    assert all(d[-1].startswith("盖漏枚举") for d in r["g0_disagree"]), r["g0_disagree"][:2]
    v = _retired_vote(r)
    assert (v["total"], v["agree"]) == {_drop_vv: (1186, 1186), _drop_cone_boundary: (110, 106)}[mutate]


def _drop_ev(monkeypatch):
    import eab.kernel2d.covers as cv
    monkeypatch.setattr(cv, "ev_cover", lambda *a, **k: None)


def _drop_ve_subset(monkeypatch):
    """只丢一部分 VE 盖（动块局部顶点号 ≡ 3 mod 7）：局部、稀疏的枚举缺口。"""
    import eab.kernel2d.covers as cv
    orig = cv.ve_cover
    monkeypatch.setattr(cv, "ve_cover", lambda A, ia, B, jb, tol=0.0, cone_tol=None:
                        None if ia % 7 == 3 else orig(A, ia, B, jb, tol, cone_tol))


@pytest.mark.parametrize("mutate,distance_gate_red,old_vote", [
    (_drop_cone_boundary, True, (110, 106)),
    (_drop_ev, True, (897, 892)),
    (_drop_ve_subset, False, (1186, 1186)),
], ids=["strict_cone_only", "no_EV_covers", "drop_VE_subset"])
def test_g0_exit_completeness_has_teeth(monkeypatch, mutate, distance_gate_red, old_vote):
    """出口完备性要有牙：三种盖枚举缺口都必须让相交样本上的门红，且归因为"盖漏枚举"。

    drop_VE_subset 是这道门存在的理由之一：分离侧的距离完备性对它无感（603/603），旧投票也无感
    （1186/1186），只有相交侧的出口检验抓得到——相交的 657 次平移不是"多余的样本"。
    """
    mutate(monkeypatch)
    r = bb52_g0.analyze(samples_per_pair=60, seed=0)
    assert r["g0_exit_samples"] > 0
    assert r["g0_exit_agree"] < r["g0_exit_samples"]
    assert all(d[-1].startswith("盖漏枚举") for d in r["g0_exit_disagree"]), r["g0_exit_disagree"][:2]
    assert (r["g0_agree"] < r["g0_samples"]) == distance_gate_red
    v = _retired_vote(r)
    assert (v["total"], v["agree"]) == old_vote


def test_g0_exit_completeness_is_blind_to_vv_by_construction(monkeypatch):
    """看着 g0_exit_completeness 文档里的那句"丢 VV 盖这里不会红"：出口几乎必在某段 ∂E 的相对内部，
    零维盖不参与见证。这颗牙由分离侧的距离完备性负责（no_VV_covers 下它必红，这里一并断言）。"""
    _drop_vv(monkeypatch)
    r = bb52_g0.analyze(samples_per_pair=60, seed=0)
    assert r["g0_exit_agree"] == r["g0_exit_samples"] == 657
    assert r["g0_agree"] < r["g0_samples"]


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
    assert r["g0_exit_samples"] > 0
    assert r["g0_exit_agree"] == r["g0_exit_samples"], r["g0_exit_disagree"][:3]
    v = _retired_vote(r)
    # 旧规则：分离判成相交 11 次（2026-09-24 实测；投票计入 60，一致 49）
    assert (v["total"], v["agree"], v["false_alarm"], v["false_negative"]) == (60, 49, 11, 0)


# ---------------------------------------------------------------- 旧规则另一半也是假的（2026-09-24）

CHANNEL = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.0, 1.0), (1.0, 1.8), (3.0, 1.8), (3.0, 2.8), (0.0, 2.8)]  # C 形槽，CCW
WEDGE = [(1.0, 1.0), (1.6, 1.2), (1.2, 1.75)]      # 楔尖 56.7° 恰坐在槽的反射角 (1,1)，顶角距槽顶 0.05


def _wedge_channel_blocks(*_a, **_k):
    return ({1: {"poly": list(CHANNEL), "vidx": list(range(8)), "flipped": False},
             2: {"poly": list(WEDGE), "vidx": [10, 11, 12], "flipped": False}}, {})


def test_g0_gate_no_false_negative_on_wedge_in_channel(monkeypatch):
    """被删的旧断言（sign(min gap) 投票 == 暴力）**另一半也是假的**：相交判成分离。

    analyze 里槽块是动块 A、楔块是 B；槽块平移落在 (+,+) 象限时楔尖相对压进槽角。楔尖对槽底上沿、槽左壁的
    顶点-边盖（这里是 EV）法锥有效、间隙为负，但投影参数出界（如 1.068 / −0.127），被边内筛选剔除；窗口里
    只剩楔顶对槽顶的正间隙 EV 盖，于是 min gap > 0、投票判分离，暴力判相交（楔块作动块的同一机制见
    test_kernel2d_review，逐位钉着）。所以旧断言的两半（分离侧、相交侧）都不能恢复成门；新门在同一批平移上零失配。
    """
    monkeypatch.setattr(bb52_g0, "load_blocks", _wedge_channel_blocks)
    monkeypatch.setattr(bb52_g0, "legacy_contacts", lambda *a, **k: [])
    r = bb52_g0.analyze(samples_per_pair=60, seed=0)
    assert r["g0_pairs"] == [(1, 2)]
    assert r["g0_samples"] > 0 and r["g0_agree"] == r["g0_samples"], r["g0_disagree"][:3]
    assert r["g0_exit_samples"] > 0 and r["g0_exit_agree"] == r["g0_exit_samples"], r["g0_exit_disagree"][:3]
    v = _retired_vote(r)
    # 旧规则：相交判成分离 15 次（2026-09-24 实测；投票计入 53，一致 38）
    assert (v["total"], v["agree"], v["false_alarm"], v["false_negative"]) == (53, 38, 0, 15)
