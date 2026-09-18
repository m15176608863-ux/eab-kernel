"""G1 一级门（bb52 步 1，legacy 兼容模式）+ G0 真几何自证。数字于 2026-09-18 钉死。

牙：cone_tol 退回严格 0 时 legacy-only 必须 > 0（证明这道门真的在测法锥容差这件事）。
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
    return bb52_g0.analyze(samples_per_pair=25, seed=0)


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


def test_g0_real_concave_geometry(result):
    assert result["g0_samples"] > 300
    assert result["g0_agree"] == result["g0_samples"], result["g0_disagree"]


def test_gate_has_teeth_strict_cone_loses_legacy_contacts():
    strict = bb52_g0.analyze(samples_per_pair=0, cone_tol=0.0)
    assert len(strict["ve_legacy_only"]) > 0
