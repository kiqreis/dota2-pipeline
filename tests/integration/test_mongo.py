import pytest

from pymongo.errors import DuplicateKeyError

pytestmark = pytest.mark.integration


def test_when_collection_created_then_name_test_prefix(mongo_collection):
    assert mongo_collection.name.startswith("match_details_test")


def test_when_collection_created_then_match_id_index_is_unique(mongo_collection):
    index = next(
        (i for i in mongo_collection.list_indexes() if i["name"] == "match_id_1"),
        None,
    )

    assert index is not None
    assert index["unique"] is True


def test_when_insert_then_can_find_by_match_id(mongo_collection, sample_match_details):
    result = mongo_collection.insert_one(sample_match_details)
    found = mongo_collection.find_one({"match_id": sample_match_details["match_id"]})

    assert result.inserted_id is not None
    assert found is not None
    assert found["radiant_win"] is True
    assert found["radiant_name"] == "Team Radiant"


def test_when_duplicate_match_id_then_raises_duplicate_key_error(
    mongo_collection, sample_match_details
):
    mongo_collection.insert_one(sample_match_details)

    with pytest.raises(DuplicateKeyError):
        mongo_collection.insert_one(sample_match_details)
