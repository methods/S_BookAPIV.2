# pylint: disable=missing-docstring

from unittest.mock import MagicMock

from app.datastore.mongo_helper import insert_book_to_mongo


def test_insert_book_to_mongo_calls_replace_one_with_upsert():
    # ARRANGE:
    mock_books_collection = MagicMock()

    # Test data
    new_book = {
        "id": "some-unique-id-123",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "synopsis": "A story about the American Dream",
    }

    # ACT:
    # Call the function
    insert_book_to_mongo(new_book, mock_books_collection)

    # ASSERT:
    mock_books_collection.replace_one.assert_called_once()
    expected_filter = {"id": "some-unique-id-123"}
    mock_books_collection.replace_one.assert_called_once_with(
        expected_filter,  # Argument 1: The query filter
        new_book,  # Argument 2: The replacement document
        upsert=True,  # Argument 3: The upsert keyword argument
    )
