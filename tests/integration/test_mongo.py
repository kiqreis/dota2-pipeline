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


def test_when_find_unknown_match_id_then_returns_none(mongo_collection):
    assert mongo_collection.find_one({"match_id": 1}) is None


def test_when_update_one_with_set_then_only_listed_field_changes(
    mongo_collection, sample_match_details
):
    mongo_collection.insert_one(sample_match_details)

    result = mongo_collection.update_one(
        {"match_id": sample_match_details["match_id"]},
        {"$set": {"radiant_win": False}},
    )

    found = mongo_collection.find_one({"match_id": sample_match_details["match_id"]})

    assert result.matched_count == 1
    assert result.modified_count == 1
    assert found["radiant_win"] is False
    assert found["duration"] == sample_match_details["duration"]
    assert found["version"] == sample_match_details["version"]
    assert found["players"] == sample_match_details["players"]
