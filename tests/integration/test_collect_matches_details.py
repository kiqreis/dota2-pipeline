from unittest.mock import MagicMock, Mock

import pytest
import requests

from src.collect.matches_details import CollectorMatchDetails
from src.collect.models import Match, patch

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _fake_proxies(monkeypatch):
    monkeypatch.setattr(
        "src.collect.matches.PROXIES",
        [
            {
                "http": "http://localhost:8080",
                "https": "http://localhost:8080",
            }
        ],
    )


@pytest.fixture
def mock_get(monkeypatch):
    def _mock(payload, status=200):
        response = Mock(status_code=status)
        response.json.return_value = payload

        mock = Mock(return_value=response)
        monkeypatch.setattr(requests, "get", mock)

        return mock

    return _mock


@pytest.fixture
def collector(mongo_collection):
    return CollectorMatchDetails(mongo_collection, max_workers=1)


@pytest.fixture
def persisted_match(db_session, sample_match):
    db_session.add(Match(**sample_match))
    db_session.commit()

    return Match(**sample_match)


@pytest.fixture
def http_OK(sample_match_details):
    response = MagicMock(status_code=200)
    response.json.return_value = sample_match_details

    with patch("requests.get", return_value=response) as mock_get:
        yield mock_get


def test_when_exec_one_succeeds_then_calls_api_with_match_url(
    patch_get_session, http_OK, persisted_match, collector, sample_match
):
    collector.exec_one(persisted_match)

    http_OK.assert_called_once()

    assert http_OK.call_args.args[0].endswith(f"/{sample_match['match_id']}")
    assert http_OK.call_args.kwargs["timeout"] == 30


def test_when_exec_one_succeeds_then_inserts_into_mongo(
    patch_get_session,
    http_OK,
    persisted_match,
    mongo_collection,
    collector,
    sample_match,
):
    collector.exec_one(persisted_match)

    assert mongo_collection.count_documents({"match_id": sample_match["match_id"]}) == 1


def test_when_exec_one_succeeds_then_flags_match_as_collected(
    patch_get_session,
    http_OK,
    db_session,
    persisted_match,
    collector,
    sample_match,
):
    collector.exec_one(persisted_match)

    db_session.expire_all()
    updated = db_session.get(Match, sample_match["match_id"])

    assert updated.flag_details_collected is True


def test_when_exec_one_succeeds_then_returns_true(
    patch_get_session, http_OK, persisted_match, collector
):
    assert collector.exec_one(persisted_match) is True


def test_when_exec_one_gets_non_200_then_returns_false(
    patch_get_session,
    collector,
    persisted_match,
    sample_match_details,
    mock_get,
):
    mock_get(sample_match_details, status=404)

    assert collector.exec_one(persisted_match) is False


def test_when_exec_one_gets_non_200_then_does_not_insert_into_mongo(
    patch_get_session,
    collector,
    mongo_collection,
    persisted_match,
    sample_match_details,
    mock_get,
):
    mock_get(sample_match_details, status=404)

    collector.exec_one(persisted_match)

    assert mongo_collection.count_documents({}) == 0


def test_when_exec_one_gets_non_200_then_does_not_flag_match(
    patch_get_session,
    db_session,
    collector,
    persisted_match,
    sample_match,
    sample_match_details,
    mock_get,
):
    mock_get(sample_match_details, status=404)

    collector.exec_one(persisted_match)

    db_session.expire_all()
    not_manipulated = db_session.get(Match, sample_match["match_id"])

    assert not_manipulated.flag_details_collected is False
