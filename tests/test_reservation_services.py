"""..."""

from unittest.mock import patch

from bson import ObjectId

from app.services.reservation_services import count_reservations_for_book


@patch("app.services.reservation_services.mongo")
def test_count_reservations_for_book(mock_mongo, test_app):
    """
    WHEN count_reservations_for_book is called with a book_id
    THEN it should call count_documents on the reservations collection
    WITH the correct filter
    """
    # Arrange
    book_id_obj = ObjectId()
    mock_mongo.db.reservations.count_documents.return_value = 5

    with test_app.app_context():
        # ACT
        result = count_reservations_for_book(book_id_obj)

    # Assert
    assert result == 5
    mock_mongo.db.reservations.count_documents.assert_called_once_with(
        {"book_id": book_id_obj}
    )
