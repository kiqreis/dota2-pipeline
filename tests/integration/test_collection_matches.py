import pytest
import requests

from unittest.mock import Mock

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
