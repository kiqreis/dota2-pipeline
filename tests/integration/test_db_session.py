import pytest

from src.collect.matches import CollectorMatch
from src.collect.models import Match, get_oldest_match_id

pytestmark = pytest.mark.integration


def test_given_valid_match_when_inserted_then_can_be_queried(db_session, sample_match):
    db_session.add(Match(**sample_match))
    db_session.commit()

    result = db_session.get(Match, sample_match["match_id"])

    assert result.match_id is not None
    assert result.radiant_name == "Team Radiant"
    assert result.league_name == "Test League"


def test_when_multiple_matches_exist_then_get_oldest_match_id_returns_earliest(
    patch_get_session, sample_match, match_factory, db_session
):
    oldest_id = 9999999999 - 1

    db_session.add_all(
        [Match(**match_factory()), Match(**match_factory(match_id=oldest_id))]
    )

    db_session.commit()

    assert get_oldest_match_id() == oldest_id


def test_given_existing_match_when_save_matches_then_skips_duplicate(
    patch_get_session, db_session, sample_match
):
    collector = CollectorMatch()

    collector.save_matches([sample_match])
    collector.save_matches([sample_match])

    assert db_session.query(Match).count() == 1
