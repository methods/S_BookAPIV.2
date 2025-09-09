"""Unit tests for the book service layer."""

from unittest.mock import patch

from app.services.book_service import count_active_books, fetch_active_books


def test_count_active_books_returns_correct_count(test_app):
    """
    GIVEN a mocked database layer
    WHEN count_active_books()
    THEN it should call the underlying database method wiht the correct query
    AND return the mocked value
    """
    # Arrange: set patch target
    with patch("app.services.book_service.mongo") as mock_mongo:
        mock_mongo.db.books.count_documents.return_value = 5

        with test_app.app_context():
            # Act
            result = count_active_books()

        assert result == 5
        expected_query = {"state": {"$ne": "deleted"}}
        mock_mongo.db.books.count_documents.assert_called_once_with(expected_query)


@patch("app.services.book_service.mongo")
def test_fetch_active_books_uses_default_pagination(mock_mongo, test_app):
    """
    GIVEN no arguments are provided
    WHEN fetch_active_books is called
    THEN it should query the database using the default offset (0) and limit (20).
    """
    mock_mongo.db.books.find.return_value.skip.return_value.limit.return_value = [
        {"_id": "1", "title": "A Book"}
    ]
    with test_app.app_context():
        # ACT: Call the function with no arguments
        result = fetch_active_books()

    # Assert
    # 1. Check that the result is what we expect
    assert isinstance(result, list)
    assert len(result) == 1

    # 2. Check that the database methods were called with the correct default values
    expected_filter = {"state": {"$ne": "deleted"}}
    mock_mongo.db.books.find.assert_called_once_with(expected_filter)
    mock_mongo.db.books.find.return_value.skip.assert_called_once_with(0)
    mock_mongo.db.books.find.return_value.skip.return_value.limit.assert_called_once_with(
        20
    )


@patch("app.services.book_service.mongo")
def test_fetch_active_books_uses_custom_pagination(mock_mongo, test_app):
    """
    GIVEN custom offset and limit arguments
    WHEN fetch_active_books is called
    THEN it should query the database using those specific values.
    """
    # ARRANGE
    mock_mongo.db.books.find.return_value.skip.return_value.limit.return_value = []

    with test_app.app_context():
        # ACT: Call the function with custom arguments
        fetch_active_books(offset=10, limit=5)

    # ASSERT
    # Check that the database methods were called with the custom values
    expected_filter = {"state": {"$ne": "deleted"}}
    mock_mongo.db.books.find.assert_called_once_with(expected_filter)
    mock_mongo.db.books.find.return_value.skip.assert_called_once_with(10)
    mock_mongo.db.books.find.return_value.skip.return_value.limit.assert_called_once_with(
        5
    )
