from unittest.mock import MagicMock

import pytest

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
