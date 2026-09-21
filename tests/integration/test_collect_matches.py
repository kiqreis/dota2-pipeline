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


def test_when_http_error_then_returns_false_and_saves_nothing(
    patch_get_session, db_session, mock_get
):
    mock_get([], status=500)
    result = CollectorMatch().collect_matches()

    assert result is False
    assert db_session.query(Match).count() == 0


def test_when_match_already_exists_then_skips_insert(
    patch_get_session, db_session, match_factory, mock_get
):
    existing_matches = match_factory(radiant_win=False)

    db_session.add(Match(**existing_matches))
    db_session.commit()

    incoming = match_factory(radiant_win=True)
    mock_get([incoming])

    CollectorMatch().collect_matches()
    rows = db_session.query(Match).all()

    assert len(rows) == 1
    assert rows[0].radiant_win is False


def test_when_empty_batch_then_saves_nothing(patch_get_session, db_session, mock_get):
    mock_get([])

    CollectorMatch().collect_matches()

    assert db_session.query(Match).count() == 0


def test_when_three_matches_returned_then_all_are_saved(
    patch_get_session, db_session, match_factory, mock_get
):
    payload = [
        match_factory(match_id=10_000_000_001, radiant_win=False, duration=1000),
        match_factory(match_id=10_000_000_002, radiant_win=True, duration=2000),
        match_factory(match_id=10_000_000_003, radiant_win=False, duration=3000),
    ]

    mock_get(payload)

    CollectorMatch().collect_matches()

    rows = db_session.query(Match).order_by(Match.match_id).all()
    by_id = {r.match_id: r for r in rows}

    assert set(by_id.keys()) == {m["match_id"] for m in payload}

    for match in payload:
        row = by_id[match["match_id"]]

        assert row.radiant_win == match["radiant_win"]
        assert row.duration == match["duration"]


def test_when_match_already_exists_then_skips_insert_and_preserves_data(
    patch_get_session, db_session, match_factory, mock_get
):
    existing = match_factory(match_id=10_000_000_001, radiant_win=False)
    new = match_factory(match_id=10_000_000_002)

    db_session.add(Match(**existing))
    db_session.commit()

    incoming_existing = {**existing, "radiant_win": True}
    mock_get([incoming_existing, new])

    CollectorMatch().collect_matches()

    rows = db_session.query(Match).order_by(Match.match_id).all()
    match_by_id = {r.match_id: r for r in rows}

    assert set(match_by_id.keys()) == {existing["match_id"], new["match_id"]}
    assert match_by_id[existing["match_id"]].radiant_win is False
