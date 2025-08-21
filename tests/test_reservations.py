# pylint: disable=redefined-outer-name
"""..."""

import pytest
from bson.objectid import ObjectId
from app.extensions import mongo

@pytest.fixture
def client_with_book(test_app):
    """
    Provides a test client,
    sets up the DB and
    ensures the database is clean and
    seeded with a single book for reservation tests.
    """
    with test_app.app_context():
        mongo.db.books.delete_many({})
        mongo.db.reservations.delete_many({})
        mongo.db.books.insert_one({
            "_id": ObjectId("5f8f8b8b8b8b8b8b8b8b8b8b"),
            "title": "Test Book"
        })

    yield test_app.test_client()

    # Teardown: Clean up the database
    with test_app.app_context():
        mongo.db.books.delete_many({})
        mongo.db.reservations.delete_many({})


@pytest.mark.parametrize("payload, expected_message",
    [
        ("invalid!!", "Invalid Book ID"),
    ]
)
def test_reservation_with_invalid_book_id(payload, expected_message, client_with_book):
    """
    GIVEN a Flask app with a pre-existing book in the mock DB
    WHEN a POST request is made to /books/<book_id>/reservations without a book_id_str argument
    THEN a 400 status code is returned.
    """
    _ = client_with_book

    # Act
    response = client_with_book.post(
        f'/books/{payload}/reservations',
        json={"forenames": "Firstname", "surname": "Tester"}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == expected_message
