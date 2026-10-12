"""G6I-06 text-only contract guards; no claim of general semantic proof."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    (
        "docs/canon_map.md",
        "依赖命题 7、8；命题 7 首入已有二维/三维 API 与门，命题 8 及完整首入控制仍未实现",
        "依赖命题 7、8，均未实现",
        (
            "命题 7 首入已有二维/三维 API 与门",
            "命题 8 及完整首入控制仍未实现",
        ),
        "proposition 7 is implemented but proposition 8 and entrance control are not",
    ),
    (
        "README.md",
        "随后已经过 G6 第二至第五轮独立重审",
        "canon_map（未经 G6）",
        (
            "历史 HEAD `094861c` 尚不存在",
            "随后已经过 G6 第二至第五轮独立重审",
            "历史文档核验不等于当前全部实现通过 G6，更不等于 M0 已退出",
        ),
        "canon map has historical independent review, not current M0 exit",
    ),
    (
        "tests/test_invariance_2d.py",
        "默认分类对每格实际给定坐标精确；舍入后的刚体变换\n"
        "可能改变边界输入，但每格必须通过独立精确 oracle，不能凭旧格子清单豁免。\n"
        "仅对有分辨余量的格子另外要求标签不变；显式调用方窗口不含隐式 tol_eff 地板。",
        "那 19 个格子只断言夹逼",
        (
            "默认分类对每格实际给定坐标精确",
            "每格必须通过独立精确 oracle，不能凭旧格子清单豁免",
            "显式调用方窗口不含隐式 tol_eff 地板",
            "历史 b6468f3 的 M0.2 red_before 曾记录 19 格角度分辨率现象，该历史记录不再是现门的例外",
        ),
        "every supplied cell has an exact oracle, without an implicit tolerance floor",
    ),
)


def _assert_current_contract(text, stale, required, meaning):
    assert stale not in text, "G6I-06 superseded contract: " + meaning
    for phrase in required:
        assert phrase in text, "G6I-06 missing current contract: " + phrase


@pytest.mark.parametrize("path,current,stale,required,meaning", CASES)
def test_current_contracts_do_not_repeat_superseded_status(path, current, stale, required, meaning):
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    _assert_current_contract(text, stale, required, meaning)
    assert text.count(current) == 1, "document rollback anchor must be unique"


@pytest.mark.parametrize("path,current,stale,required,meaning", CASES)
def test_current_contract_gate_rejects_reintroduced_old_text(path, current, stale, required, meaning):
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    assert text.count(current) == 1, "document rollback anchor must be unique"
    # Revert the corresponding actual clause, rather than append unrelated text.
    mutated = text.replace(current, stale, 1)
    assert mutated != text
    with pytest.raises(AssertionError, match="G6I-06 superseded contract") as caught:
        _assert_current_contract(mutated, stale, required, meaning)
    assert meaning in str(caught.value)


@pytest.mark.parametrize("path,current,stale,required,meaning", CASES)
def test_current_contract_gate_rejects_deleted_current_boundary(path, current, stale, required, meaning):
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    for phrase in required:
        assert phrase in text
        mutated = text.replace(phrase, "")
        with pytest.raises(AssertionError, match="G6I-06 missing current contract") as caught:
            _assert_current_contract(mutated, stale, required, meaning)
        assert phrase in str(caught.value)


def _assert_route_is_explicit_history(text):
    section = text.split("## 路线", 1)[1].split("2026-09-21 前的旧路线", 1)[0]
    assert "历史路线快照（094861c 时期）" in section, "G6I-06 route history"
    assert "不是当前实现状态" in section, "G6I-06 route history"


def test_readme_route_old_status_is_not_advertised_as_current():
    _assert_route_is_explicit_history((ROOT / "README.md").read_text(encoding="utf-8-sig"))


def test_route_history_marker_internal_text_mutation_is_caught():
    text = (ROOT / "README.md").read_text(encoding="utf-8-sig")
    with pytest.raises(AssertionError, match="G6I-06 route history"):
        _assert_route_is_explicit_history(text.replace("历史路线快照（094861c 时期）", "当前路线"))


def test_entrance_docstrings_describe_finite_domain_and_overlapping_witness():
    from eab.kernel2d import entrance
    assert "有限源特征域精确复核" in entrance.__doc__, "finite-domain current docstring"
    assert "FF 取两闭段真实重叠上的同点" in entrance._facet_points.__doc__, "FF current witness docstring"
