import pytest

from sqlalchemy import create_engine
from collect.models import Base

from src.shared.settings import Settings


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixute(scope="session")
def engine(settings):
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()
