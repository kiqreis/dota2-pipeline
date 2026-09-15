import pytest

from src.collect.matches_details import sanitize_for_mongo
from src.process.transform import MatchDetailsProcessor


@pytest.fixture
def processor():
    return MatchDetailsProcessor(collection=None)


@pytest.fixture
def payload():
    return {
        "match_id": 1,
        "version": 1,
        "radiant_win": True,
        "duration": 1234,
        "start_time": 1700000000,
        "radiant_name": "Team Radiant",
        "dire_name": "Team Dire",
        "leagueid": 123,
        "series_id": 1,
        "series_type": 1,
        "radiant_score": 30,
        "dire_score": 20,
        "cluster": 1,
        "replay_salt": 1,
        "pre_game_duration": 0,
        "match_seq_num": 1,
        "tower_status_radiant": 0,
        "tower_status_dire": 0,
        "barracks_status_radiant": 0,
        "barracks_status_dire": 0,
        "first_blood_time": 0,
        "lobby_type": 0,
        "human_players": 10,
        "game_mode": 1,
        "flags": 0,
        "engine": 1,
        "radiant_team_id": 1,
        "radiant_logo": None,
        "radiant_team_complete": 0,
        "dire_team_id": 2,
        "dire_logo": None,
        "dire_team_complete": 0,
        "radiant_captain": 0,
        "dire_captain": 0,
        "replay_url": "",
        "patch": 1,
        "region": 0,
    }


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


def test_when_match_payload_is_complete_then_returns_expected_columns(
    processor, payload
):
    df = processor.extract_match_details(payload)

    assert "match_id" in df.columns
    assert "radiant_win" in df.columns
    assert "leagueid" in df.columns
    assert len(df) == 1
