import pytest

from src.shared.settings import Settings


@pytest.fixture(scope="session")
def settings():
    return Settings()
