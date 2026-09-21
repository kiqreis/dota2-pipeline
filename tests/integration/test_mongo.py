import pytest

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
