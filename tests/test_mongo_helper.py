# pylint: disable=missing-docstring

from unittest.mock import MagicMock

from bson import ObjectId

from app.datastore.mongo_helper import (delete_book_by_id, find_books,
                                        insert_book_to_mongo,
                                        replace_book_by_id,
                                        validate_book_put_payload)


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


def test_delete_book_by_id_happy_path():
    """Given a valid book_id, soft deletes the book"""
    # Arrange
    valid_id = ObjectId()
    fake_book_id_str = str(valid_id)
    fake_book_from_db = {
        "_id": valid_id,
        "title": "A Mocked Book",
        "author": "The Mockist",
        "synopsis": "A tale of fakes and stubs.",
        "state": "active",
    }

    mock_collection = MagicMock()
    mock_collection.find_one_and_update.return_value = fake_book_from_db

    # Act
    result = delete_book_by_id(mock_collection, fake_book_id_str)

    # Assert
    mock_collection.find_one_and_update.assert_called_once()
    assert result == fake_book_from_db
    # Was the method called with the EXACT right arguments?
    expected_filter = {"_id": valid_id, "state": {"$ne": "deleted"}}
    expected_update = {"$set": {"state": "deleted"}}
    mock_collection.find_one_and_update.assert_called_once_with(
        expected_filter, expected_update
    )


def test_soft_delete_already_deleted_book_returns_none():
    # Arrange
    valid_id = ObjectId()
    fake_book_id_str = str(valid_id)

    mock_collection = MagicMock()
    mock_collection.find_one_and_update.return_value = None

    # Act
    result = delete_book_by_id(mock_collection, fake_book_id_str)

    # Assert
    assert result is None
    mock_collection.find_one_and_update.assert_called_once()
    expected_filter = {"_id": valid_id, "state": {"$ne": "deleted"}}
    expected_update = {"$set": {"state": "deleted"}}
    mock_collection.find_one_and_update.assert_called_with(
        expected_filter, expected_update
    )


def test_replace_book_by_id_happy_path():
    """Given a valid book_id, replace_book_by_id returns a matched_count of 1."""
    # Arrange
    valid_id_str = str(ObjectId())
    new_book_data = {
        "title": "A Mocked Book: After",
        "author": "The Mockist: After",
        "synopsis": "A tale of fakes and stubs.",
    }

    # Create mock to represent Pymongo result inc. the matched_count attribute
    mock_pymongo_result = MagicMock()
    mock_pymongo_result.matched_count = 1

    # Create mock collection
    mock_collection = MagicMock()
    mock_collection.replace_one.return_value = mock_pymongo_result

    # Act
    result = replace_book_by_id(mock_collection, valid_id_str, new_book_data)

    # Assert
    assert result is True
    mock_collection.replace_one.assert_called_once()
    mock_collection.replace_one.assert_called_once_with(
        {"_id": ObjectId(valid_id_str)}, new_book_data
    )


def test_replace_book_by_id_invalid_id_returns_false():
    """
    Given an invalidly formatted book_id string,
    update_book_by_id should return False.
    """
    # Arrange
    invalid_id = "1234-this-is-not-a-valid-id"
    new_book_data = {
        "title": "A Mocked Book: After",
        "author": "The Mockist: After",
        "synopsis": "A tale of fakes and stubs.",
    }
    mock_collection = MagicMock()

    # Act
    result = replace_book_by_id(mock_collection, invalid_id, new_book_data)

    # Assert
    assert result is False
    mock_collection.replace_one.assert_not_called()


def test_validate_payload_fails_with_extra_fields():
    payload_with_extra_field = {
        "title": "Valid Title",
        "author": "Valid Author",
        "synopsis": "A valid synopsis.",
        "rating": 5  # This is the unexpected, extra field
    }

    is_valid, error_dict = validate_book_put_payload(payload_with_extra_field)

    assert is_valid is False
    assert isinstance(error_dict, dict)
    assert "error" in error_dict

    expected_error_message = "Unexpected fields provided: rating"
    assert error_dict["error"] == expected_error_message

def test_validate_payload_fails_with_multiple_extra_fields():
    """
    GIVEN a payload with multiple extra fields
    WHEN validate_book_put_payload is called
    THEN the error message should list all extra fields in alphabetical order.
    """
    payload_with_extra_fields = {
        "title": "Valid Title",
        "author": "Valid Author",
        "synopsis": "A valid synopsis.",
        "year": 2024,          # Extra field
        "isbn": "123-456"      # Extra field
    }

    is_valid, error_dict = validate_book_put_payload(payload_with_extra_fields)

    assert is_valid is False
    expected_error_message = "Unexpected fields provided: isbn, year"
    assert error_dict["error"] == expected_error_message
