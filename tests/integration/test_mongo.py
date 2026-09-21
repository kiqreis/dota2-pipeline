import pytest

pytestmark = pytest.mark.integration


def test_when_collection_created_then_name_test_prefix(mongo_collection):
    assert mongo_collection.name.startswith("match_details_test")
