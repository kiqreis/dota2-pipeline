import pytest

import pandas as pd

from src.collect.matches_details import sanitize_for_mongo
from src.process.transform import MatchDetailsProcessor
from pandas.api.types import is_string_dtype


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


def test_when_match_fields_are_missing_then_fills_values_with_none(processor):
    df = processor.extract_match_details({})

    assert len(df) == 1
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert pd.isna(df["match_id"].iloc[0])
    assert df.isnull().all().all()


def test_when_match_has_players_then_returns_player_dataframe(
    processor, sample_match_details
):
    df = processor.extract_players_details(sample_match_details)

    assert len(df) == 1
    assert df["match_id"].iloc[0] == sample_match_details["match_id"]
    assert df["kills"].iloc[0] == 10
    assert df["account_id"].iloc[0] == 111


def test_when_match_has_no_players_then_returns_empty_dataframe(processor):
    data = {"match_id": 1, "players": []}
    df = processor.extract_players_details(data)

    assert len(df) == 0
    assert df.columns[0] == "match_id"
    assert "kills" in df.columns
    assert "account_id" in df.columns
    assert "hero_id" in df.columns
    assert "match_id" in df.columns
    assert df.index.empty


def test_when_match_details_are_sanitized_then_large_ints_converted_to_strings(
    processor, full_match_payload
):
    payload = {
        **full_match_payload,
        "radiant_logo": 12345,
        "dire_logo": None,
    }

    df = processor.extract_match_details(payload)

    assert is_string_dtype(df["radiant_logo"])
    assert is_string_dtype(df["dire_logo"])
    assert df["radiant_logo"].iloc[0] == "12345"
    assert pd.isna(df["dire_logo"].iloc[0])


@pytest.mark.parametrize(
    "column",
    [
        "match_id",
        "duration",
        "start_time",
        "radiant_score",
        "dire_score",
        "radiant_name",
    ],
)
def test_when_match_details_are_extracted_then_values_map_correctly(
    processor, full_match_payload, column
):
    df = processor.extract_match_details(full_match_payload)

    assert df[column].iloc[0] == full_match_payload[column]


def test_when_match_details_extracted_then_radiant_win_is_boolean_true(
    processor, full_match_payload
):
    df = processor.extract_match_details(full_match_payload)

    assert df["radiant_win"].iloc[0].item() is True


@pytest.mark.parametrize(
    "column",
    ["match_id", "radiant_win", "duration", "radiant_name"],
)
def test_when_match_details_missing_columns_become_none(processor, column):
    df = processor.extract_match_details({})

    assert df[column].iloc[0] is None
