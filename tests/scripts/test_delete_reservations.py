"""..."""
from unittest.mock import MagicMock, patch

from pymongo.errors import ConnectionFailure
from scripts.delete_reservations import delete_all_reservations, main


def test_delete_all_reservations_clears_collection_and_returns_count():
    """ 
    Unit test for delete_all_reservations: ensure it returns deleted_count
    when the collection.delete_many() result has deleted_count.
    """
    # Arrange: make a fake result object with deleted_count attribute
    fake_result = MagicMock()
    fake_result.deleted_count = 3

    # Fake collection with delete_many returning fake_result
    fake_collection = MagicMock()
    fake_collection.delete_many.return_value = fake_result

    # Act
    deleted_count = delete_all_reservations(fake_collection)

    # Assert
    assert deleted_count == 3
    fake_collection.delete_many.assert_called_once_with({})
