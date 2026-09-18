from contextlib import contextmanager
import uuid

import pytest
from pymongo import MongoClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from collect.models import Base
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.mongodb import MongoContainer

from src.shared.settings import Settings
import src.db.session as session_module


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture(scope="session")
def db_engine():
    with PostgresContainer("postgres:16", driver="psycopg") as postgres:
        _engine = create_engine(postgres.get_connection_url(), pool_pre_ping=True)
        Base.metadata.create_all(_engine)

        yield _engine

        Base.metadata.drop_all(_engine)
        _engine.dispose()


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


@pytest.fixture
def patch_get_session(monkeypatch, db_session):
    @contextmanager
    def fake_session_local():
        yield db_session

    monkeypatch.setattr(session_module, "SessionLocal", fake_session_local)

    return fake_session_local


@pytest.fixture(scope="session")
def mongo_client():
    with MongoContainer("mongo:7") as mongo:
        yield MongoClient(mongo.get_connection_url())


@pytest.fixture
def mongo_collection(mongo_client, settings):
    db = mongo_client[settings.MONGO_DB_NAME]

    collection_name = f"match_details_test_{uuid.uuid4().hex}"
    collection = db[collection_name]
    collection.create_index("match_id", unique=True)

    try:
        yield collection
    finally:
        db.drop_collection(collection_name)


@pytest.fixture
def match_factory():
    def _make(**overrides):
        data = {
            "match_id": 9999999999,
            "duration": 2400,
            "start_time": 1700000000,
            "radiant_team_id": 12345,
            "radiant_name": "Team Radiant",
            "dire_team_id": 67890,
            "dire_name": "Team Dire",
            "leagueid": 1234,
            "league_name": "Test League",
            "series_id": 1,
            "series_type": 1,
            "radiant_score": 30,
            "dire_score": 20,
            "radiant_win": True,
            "version": 1,
        }

        data.update(overrides)

        return data

    return _make


@pytest.fixture
def match_details_factory():
    def _make(**overrides):
        data = {
            "match_id": 9999999999,
            "version": 1,
            "radiant_win": True,
            "duration": 2400,
            "start_time": 1700000000,
            "radiant_name": "Team Radiant",
            "dire_name": "Team Dire",
            "players": [
                {
                    "player_slot": 0,
                    "account_id": 111,
                    "hero_id": 1,
                    "kills": 10,
                    "deaths": 2,
                    "assists": 15,
                    "gold_per_min": 500,
                    "xp_per_min": 600,
                    "isRadiant": True,
                    "win": True,
                    "lose": False,
                }
            ],
        }

        data.update(overrides)

        return data

    return _make


@pytest.fixture
def sample_match(match_factory):
    return match_factory()


@pytest.fixture
def sample_match_details(match_details_factory):
    return match_details_factory()
