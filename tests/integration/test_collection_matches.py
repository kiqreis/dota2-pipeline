import pytest
import requests

from unittest.mock import Mock
from src.collect.models import Match
from collect.matches import CollectorMatch

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


def test_when_http_200_then_persists_matches_and_returns_true(
    patch_get_session, db_session, match_factory, mock_get
):
    payload = [match_factory()]
    mock_get(payload)

    result = CollectorMatch().collect_matches()
    rows = db_session.query(Match).all()

    assert result is True
    assert [r.match_id for r in rows] == [m["match_id"] for m in payload]


def test_when_collecting_then_calls_api_with_timeout(
    patch_get_session, match_factory, mock_get
):
    mock_get([match_factory()])

    CollectorMatch().collect_matches()

    assert requests.get.call_count == 1
    assert requests.get.call_args.kwargs["timeout"] == 30
