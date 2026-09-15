import pytest

from src.collect.matches_details import sanitize_for_mongo
from src.process.transform import MatchDetailsProcessor


@pytest.fixture
def processor():
    return MatchDetailsProcessor(collection=None)


def test_when_sanitize_is_normal_then_returns_unchanged():
    data = {"match_id": 12345, "name": "test_12345"}

    assert sanitize_for_mongo(data) == data


def test_when_integer_exceeds_mongo_limit_then_converts_to_string():
    data = {"value": 9223372036854775808}
    result = sanitize_for_mongo(data)

    assert result["value"] == "9223372036854775808"


def test_when_nested_integer_exceeds_mongo_limit_then_converts_to_string():
    data = {"outer": {"inner": 9223372036854775808}}
    result = sanitize_for_mongo(data)

    assert result["outer"]["inner"] == "9223372036854775808"


def test_when_list_contains_large_integers_then_converts_nested_values():
    data = {"values": [1, 9223372036854775808, {"x": 9223372036854775808}]}
    result = sanitize_for_mongo(data)

    assert result["values"][1] == "9223372036854775808"
    assert result["values"][2]["x"] == "9223372036854775808"


def test_when_integers_are_within_mongo_limit_then_preserves_values():
    data = {"count": 13, "max_int_valid": 9223372036854775807}
    result = sanitize_for_mongo(data)

    assert result["count"] == 13
    assert result["max_int_valid"] == 9223372036854775807
