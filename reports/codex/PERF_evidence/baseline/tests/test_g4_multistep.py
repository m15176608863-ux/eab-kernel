"""G4 砖一数据钉死（bb52_N10 / bbW025_N10 / bbF038_N20）。

这不是"通过=好"的门，是"数字变了就要有人解释"的门。
2026-09-24（G6 gap 1）真值口径改为 df22 本步末轮开闭判定 m0_new（与 readers.bdda_df 同一规则）；
旧口径（下一步携带进来的 m0_2，键缺失即判张开）保留为 *_old_truth 对照列，它的数字与 09-18 首批钉数逐位相同
（456/439/445/453、21 翻转；825/815/809/844、61 翻转）——对照列本身就是"只换了真值、别的没动"的证据。
新口径下：真翻转 19 + 42 = 61（旧口径 82 里 2 + 19 = 21 个是 k+1 键消失的转移/移除假象，新口径没有旧口径之外的翻转）；
静态几何先验 P2 抓 0 + 5 = 5/61，间隙外推 P3 抓 12 + 27 = 39/61，结果几何回看抓 17 + 41 = 58/61。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import g4_multistep  # noqa: E402

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "bdda_df"


def _pins(t):
    return {
        "n": t["n"], "closed": t["closed_true"],
        "hits": (t["p1"], t["p2"], t["p3"], t["post"]),
        "flips": (t["flips"], t["flip_p2"], t["flip_p3"], t["flip_post"]),
        "old_hits": (t["p1_old_truth"], t["p2_old_truth"], t["p3_old_truth"], t["post_old_truth"]),
        "old_flips": (t["flips_old_truth"], t["flip_p2_old_truth"], t["flip_p3_old_truth"], t["flip_post_old_truth"]),
        "split": (t["flips_both"], t["flips_only_old_truth"], t["flips_only_old_truth_removed"], t["flips_only_new_truth"]),
    }


@pytest.mark.skipif(not (FIX / "bb52_N10").exists(), reason="fixture missing")
def test_bb52_n10_pinned():
    p = _pins(g4_multistep.analyze(FIX / "bb52_N10")["total"])
    assert p["n"] == 477 and p["closed"] == 380
    assert p["hits"] == (458, 441, 447, 455)
    assert p["flips"] == (19, 0, 12, 17)
    assert p["old_hits"] == (456, 439, 445, 453)                 # 09-18 首批钉数（旧口径）
    assert p["old_flips"] == (21, 0, 12, 17)
    assert p["split"] == (19, 2, 2, 0)                            # 旧口径多出的 2 个全是 k+1 键消失


@pytest.mark.skipif(not (FIX / "bbW025_N10").exists(), reason="fixture missing")
def test_w025_n10_pinned():
    p = _pins(g4_multistep.analyze(FIX / "bbW025_N10")["total"])
    assert p["n"] == 886 and p["closed"] == 721
    assert p["hits"] == (844, 834, 828, 859)
    assert p["flips"] == (42, 5, 27, 41)
    assert p["old_hits"] == (825, 815, 809, 844)
    assert p["old_flips"] == (61, 5, 27, 43)
    assert p["split"] == (42, 19, 19, 0)                          # 旧口径多出的 19 个全是 k+1 键消失


@pytest.mark.skipif(not (FIX / "bbF038_N20").exists(), reason="fixture missing")
def test_f038_sliding_block_no_open_close_events():
    t = g4_multistep.analyze(FIX / "bbF038_N20")["total"]
    assert t["n"] == 38 and t["flips"] == 0 and t["flips_old_truth"] == 0 and t["p1"] == t["p2"] == 38


def test_static_prior_verdict_under_the_df22_truth():
    """"砖一静态版关闭"在正确真值上重算（G6 gap 1）：两份有翻转的夹具合计 61 个真翻转，静态几何先验 P2 抓 5 个（8%）；
    间隙外推 P3 抓 39 个（64%，不是旧报告的"约一半 39/82"）；结果几何回看抓 58 个（95%，不是旧报告的"~70% 天花板 60/82"）。
    静态版的否定结论在新口径下仍成立；旧报告读法 2、3 的比例数字不成立（由合并者订正报告）。"""
    tot = {k: 0 for k in ("flips", "flip_p2", "flip_p3", "flip_post")}
    for fx in ("bb52_N10", "bbW025_N10"):
        if not (FIX / fx).exists():
            pytest.skip("fixture missing")
        t = g4_multistep.analyze(FIX / fx)["total"]
        for k in tot:
            tot[k] += t[k]
    assert (tot["flips"], tot["flip_p2"], tot["flip_p3"], tot["flip_post"]) == (61, 5, 39, 58)
    assert tot["flip_p2"] / tot["flips"] < 0.1


# ---------------------------------------------------------------- G6 gap 1：真值口径 = df22 末轮开闭判定

def _df22_last(d):
    """独立解析 df22（不用 csv 模块、不用 bdda_df/g4_multistep）：(step, contact) -> 该步 oc_iter 最大那一轮的 m0_new。"""
    text = (d / "bdda_debug_df22.csv").read_bytes().decode("utf-8")
    lines = [ln for ln in text.replace(chr(13) + chr(10), chr(10)).split(chr(10)) if ln]
    head = lines[0].split(",")
    last = {}
    for ln in lines[1:]:
        r = dict(zip(head, ln.split(",")))
        k, it = (int(r["step"]), int(r["contact"])), int(r["oc_iter"])
        if k not in last or it > last[k][0]:
            last[k] = (it, int(r["m0_new"]))
    return {k: v[1] for k, v in last.items()}


@pytest.mark.parametrize("fx", ["bb52_N10", "bbW025_N10", "bbF038_N20"])
def test_g4_truth_is_the_df22_final_open_close_judgment(fx):
    """G6 gap 1：旧真值 = 下一步携带进来的 m0_2（键缺失即判张开），混进了转移/移除假象（bbW025 的 61 个"翻转"里
    26 个来自 k+1 消失的键）。本仓库读取器（bdda_df.load_records）以 df22 该步最后一轮开闭迭代的 m0_new 为终判；
    G4 改用同一口径，旧口径留作对照列。逐样本对独立解析的 df22 核对。"""
    if not (FIX / fx).exists():
        pytest.skip("fixture missing")
    res = g4_multistep.analyze(FIX / fx)
    assert res["truth"] == "df22_last_oc_iter_m0_new"
    oracle = _df22_last(FIX / fx)
    assert res["samples"]
    for s in res["samples"]:
        assert s["truth_closed"] == (oracle[(s["step"], s["contact"])] > 0), s
    t = res["total"]
    assert t["flips"] == sum(s["p1_closed"] != s["truth_closed"] for s in res["samples"])
    assert t["flips_old_truth"] == sum(s["p1_closed"] != s["old_truth_closed"] for s in res["samples"])
