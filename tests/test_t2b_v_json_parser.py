"""Exact JSON hygiene regression after removing callback-based parsing.

The oracle for ordinary JSON syntax/string decoding is Python's standard JSON
parser; raw integer-token restrictions and duplicate-key rejection are the
additional lemma section 7 requirements, tested independently below.
"""
import json
from decimal import Decimal
from pathlib import Path
import subprocess
import sys

import pytest

import t2b_independent_cage_verifier as verifier


VALID_TREES = (
    None, True, False, 0, 37, "", "x", "a\nb\tc", '\"\\/',
    "??", "\u0000", [], {}, [[], {}], {"x": [0, None, True, False, {"y": "?"}]},
    ["0.5", "1e-3", "-0", "NaN", "Infinity", "\\u0061"],
)
INVALID_SYNTAX = (
    "", " ", "[", "{", "]", "}", ",", ":", "[1,]", '{"a":1,}',
    "[,1]", "[1 2]", "[[] []]", '{"a" 1}', '{"a":}', '{"a"::1}',
    "{a:1}", "{1:2}", "[true false]", "true false", "nullx", "True", "NULL",
    "'x'", '"x', '"\\q"', '"\\u12"', '"x\ny"', "[0]#comment", "\ufeff{}",
    '{"a":[],"b":{]}}', "[[1],]", "[1,,2]", "[1:2]", '{"a":1 "b":2}',
)
INVALID_NUMBERS = (
    "-0", "-1", "+3", "00", "03", "1.0", "0.5", "1e0", "1e-3", "1E+2",
    "NaN", "Infinity", "-Infinity", "?", "?", "1_000", "0x10", ".5", "1.",
)


@pytest.mark.parametrize("value", VALID_TREES)
@pytest.mark.parametrize("ascii_only", (False, True))
def test_json_parser_matches_standard_json_for_valid_trees(value, ascii_only):
    text = json.dumps(value, ensure_ascii=ascii_only)
    expected = json.loads(text)
    actual = verifier._json_parse(" \t\r\n" + text + " \n")
    assert actual == expected
    assert type(actual) is type(expected)


@pytest.mark.parametrize("text", INVALID_SYNTAX)
def test_json_parser_rejects_malformed_json_syntax(text):
    with pytest.raises(ValueError):
        json.loads(text)
    with pytest.raises((verifier.CageReject, ValueError)):
        verifier._json_parse(text)


@pytest.mark.parametrize("token", INVALID_NUMBERS)
def test_json_parser_rejects_noncanonical_raw_number_tokens(token):
    for text in (token, "[" + token + "]", '{"index":' + token + "}"):
        with pytest.raises(verifier.CageReject) as caught:
            verifier._json_parse(text)
        assert caught.value.condition == "V0"
        assert caught.value.check_id == "integer_token"


@pytest.mark.parametrize("text", (
    '{"x":1,"x":2}', '{"x":1,"\\u0078":2}',
    '{"a":{"z":0,"z":1}}', '[{"same":null,"same":false}]',
))
def test_json_parser_rejects_duplicate_decoded_keys_at_every_depth(text):
    with pytest.raises(verifier.CageReject) as caught:
        verifier._json_parse(text)
    assert caught.value.condition == "V0"
    assert caught.value.check_id == "duplicate_key"


def test_json_parser_preserves_unbounded_integer_tokens_without_binary64():
    token = "9" * 5000
    actual = verifier._json_parse('{"index":' + token + "}")["index"]
    assert actual == int(Decimal(token))
    assert not isinstance(actual, bool)


def test_json_parser_uses_explicit_stack_for_deep_arrays():
    depth = 1500
    value = verifier._json_parse("[" * depth + "0" + "]" * depth)
    for unused in range(depth):
        assert isinstance(value, list) and len(value) == 1
        value = value[0]
    assert value == 0


def test_cli_runs_and_rejects_under_python_optimization(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = root / "tests/t2b_independent_cage_verifier.py"
    directory = root / "tests/data/t2b_hand_cages"
    instance = directory / "doorway.instance.json"
    certificate = directory / "doorway.cert.json"
    command = [sys.executable, "-O", "-X", "utf8", str(script), str(instance), str(certificate)]
    accepted = subprocess.run(command, capture_output=True, text=True, check=False)
    assert accepted.returncode == 0
    assert len(accepted.stdout.splitlines()) == 1
    assert json.loads(accepted.stdout)["valid"] is True
    forged = json.loads(certificate.read_text(encoding="utf-8"))
    forged["radius"] = "-1"
    rejected_path = tmp_path / "rejected.cert.json"
    rejected_path.write_text(json.dumps(forged), encoding="utf-8", newline="\n")
    command[-1] = str(rejected_path)
    rejected = subprocess.run(command, capture_output=True, text=True, check=False)
    assert rejected.returncode != 0
    assert len(rejected.stdout.splitlines()) == 1
    outcome = json.loads(rejected.stdout)
    assert outcome["valid"] is False and outcome["condition"] == "V0"
