import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collect.models import Base

from src.shared.settings import Settings


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixute(scope="session")
def db_engine(settings):
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(db_engine):
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture(scope="session")
def db_session(db_engine, session_factory):
    conn = db_engine.connect()
    transaction = conn.begin()
    session = session_factory(bind=conn)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        conn.close()
