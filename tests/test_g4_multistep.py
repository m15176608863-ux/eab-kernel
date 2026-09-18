"""G4 砖一第一批数据钉死（bb52_N10 / bbW025_N10，2026-09-18）。

这不是"通过=好"的门，是"数字变了就要有人解释"的门：静态几何先验对翻转零预测力这个负结果
和运动学外推抓一半这个有限结果，都要被钉住。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import g4_multistep  # noqa: E402

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "bdda_df"


@pytest.mark.skipif(not (FIX / "bb52_N10").exists(), reason="fixture missing")
def test_bb52_n10_pinned():
    t = g4_multistep.analyze(FIX / "bb52_N10")["total"]
    assert t["n"] == 477 and t["closed_true"] == 378
    assert (t["p1"], t["p2"], t["p3"], t["post"]) == (456, 439, 445, 453)
    assert (t["flips"], t["flip_p2"], t["flip_p3"], t["flip_post"]) == (21, 0, 12, 17)


@pytest.mark.skipif(not (FIX / "bbW025_N10").exists(), reason="fixture missing")
def test_w025_n10_pinned():
    t = g4_multistep.analyze(FIX / "bbW025_N10")["total"]
    assert t["n"] == 886 and t["closed_true"] == 702
    assert (t["p1"], t["p2"], t["p3"], t["post"]) == (825, 815, 809, 844)
    assert (t["flips"], t["flip_p2"], t["flip_p3"], t["flip_post"]) == (61, 5, 27, 43)


@pytest.mark.skipif(not (FIX / "bbF038_N20").exists(), reason="fixture missing")
def test_f038_sliding_block_no_open_close_events():
    t = g4_multistep.analyze(FIX / "bbF038_N20")["total"]
    assert t["n"] == 38 and t["flips"] == 0 and t["p1"] == t["p2"] == 38
