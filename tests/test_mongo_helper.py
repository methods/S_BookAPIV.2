# pylint: disable=missing-docstring

from unittest.mock import MagicMock

from app.datastore.mongo_helper import find_books, insert_book_to_mongo


def test_insert_book_to_mongo_calls_insert_one():
    # ARRANGE:
    mock_books_collection = MagicMock()

    # Test data
    new_book = {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "synopsis": "A story about the American Dream",
    }

    # ACT:
    # Call the function
    insert_book_to_mongo(new_book, mock_books_collection)

    # ASSERT:
    mock_books_collection.insert_one.assert_called_once()
    mock_books_collection.insert_one.assert_called_once_with(new_book)


def test_find_books_calls_find_with_filter_and_projection():
    # Arrange
    mock_collection = MagicMock()
    mock_cursor = MagicMock()

    mock_collection.find.return_value = mock_cursor

    # Define the inputs for our function.
    test_filter = {"author": "Jane Doe"}
    test_projection = {"_id": 0, "title": 1}

    # Act
    result_cursor = find_books(
        collection=mock_collection, query_filter=test_filter, projection=test_projection
    )

    # Assert
    mock_collection.find.assert_called_once_with(test_filter, test_projection)
    mock_cursor.limit.assert_not_called()
    assert result_cursor == mock_cursor


def test_find_books_applies_limit_when_provided():
    """
    GIVEN a mock collection and a limit
    WHEN find_books is called with a positive limit
    THEN it should call the limit method on the cursor with the correct value.
    """
    # Arrange
    mock_collection = MagicMock()
    mock_cursor = MagicMock()
    # Create a NEW mock for the final cursor after .limit() is called.
    mock_limited_cursor = MagicMock()

    mock_collection.find.return_value = mock_cursor
    # Teach the first cursor what to do when .limit() is called.
    mock_cursor.limit.return_value = mock_limited_cursor

    test_limit = 10

    # Act
    result_cursor = find_books(collection=mock_collection, limit=test_limit)

    # Assert
    # 1. Check that find() was called (this time with a default filter).
    mock_collection.find.assert_called_once()

    # 2. CRUCIAL: Check that the .limit() method was called exactly once
    mock_cursor.limit.assert_called_once_with(test_limit)

    # 3. Check that the function returned the FINAL cursor from the chain.
    assert result_cursor == mock_limited_cursor
