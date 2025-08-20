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
        ("", "Book ID is required")
    ]
)
def test_reservation_with_missing_or_invalid_book_id(payload, expected_message, client_with_book):
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

def test_create_reservation_success(client_with_book):
    """
    GIVEN a Flask app with a pre-existing book in the mock DB
    WHEN a POST request is made to /books/<book_id>/reservations with valid data
    THEN a 201 status code is returned with the new reservation data
    """
    _ = client_with_book
    # Arrange
    book_id = "5f8f8b8b8b8b8b8b8b8b8b8b"

    # Act
    response = client_with_book.post(
        f'/books/{book_id}/reservations',
        json={"forenames": "Firstname", "surname": "Tester"}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['state'] == 'reserved'
    assert data['user']['forenames'] == ['Firstname']
    assert data['user']['surname'] == ['Tester']
