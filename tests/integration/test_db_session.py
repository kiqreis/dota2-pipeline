import pytest

from src.collect.models import Match

pytestmark = pytest.mark.integration


def test_given_valid_match_when_inserted_then_can_be_queried(db_session, sample_match):
    db_session.add(Match(**sample_match))
    db_session.commit()

    result = db_session.get(Match, sample_match["match_id"])

    assert result.match_id is not None
    assert result.radiant_name == "Team Radiant"
    assert result.league_name == "Test League"
