import pytest

from src.collect.matches_details import sanitize_for_mongo


def test_when_sanitize_is_normal_then_returns_unchanged():
    data = {"match_id": 12345, "name": "test_12345"}

    assert sanitize_for_mongo(data) == data
