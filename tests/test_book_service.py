"""Unit tests for the book service layer."""

from unittest.mock import patch

from app.services.book_service import count_active_books


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
