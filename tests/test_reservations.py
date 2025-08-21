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

@pytest.mark.parametrize("test_case, expected_status, expected_message",
    [
        ("no_payload", 415, "Unsupported Media Type"),
        ("empty_json_object", 400, "Request body must be a non-empty JSON object"),
        ("null_payload", 400, "Request body must be a non-empty JSON object"),
        ("invalid_json", 400, "Invalid JSON format"),
        ("invalid_json", 400, "Invalid JSON format"),
    ]
)
def test_create_reservation_with_bad_payload(
    test_case,
    expected_status,
    expected_message,
    client_with_book
):
    """
    GIVEN a Flask app with a pre-existing book
    WHEN a POST request is made with no payload, an empty payload, a null payload, or invalid JSON
    THEN the correct error status code and message are returned.
    """
    _ = client_with_book
    book_id = "5f8f8b8b8b8b8b8b8b8b8b8b"
    url = f'/books/{book_id}/reservations'

    # Act
    if test_case == "no_payload":
        response = client_with_book.post(url)
    elif test_case == "empty_json_object":
        response = client_with_book.post(url, json={})
    elif test_case == "null_payload":
        response = client_with_book.post(url, data='null', content_type='application/json')
    elif test_case == "invalid_json":
        response = client_with_book.post(
            url,
            data='{ "bad" json }',
            content_type='application/json'
        )

    # Assert
    assert response.status_code == expected_status # pylint: disable=possibly-used-before-assignment

    data = response.get_json()
    if response.status_code == 415:
        # Flask's default 415 error message uses a 'name' field
        assert data["error"]["name"] == expected_message
    else:
        error_message = data.get("message") or data.get("error")
        assert error_message == expected_message


def test_reservation_for_nonexistant_book(client_with_book):
    """
    GIVEN a FLASK APP WITH A PRE-EXISTING BOOK
    WHEN a POST request is made with a valid but non-existent book ID
    THEN a 404 Not Found statu sis returned
    """
    _ = client_with_book
    non_existent_id = ObjectId()

    response = client_with_book.post(
        f'/books/{non_existent_id}/reservations',
        json={"forenames": "Firstname", "surname": "Tester"}
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data is not None

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
    assert data['user']['forenames'] == 'Firstname'
    assert data['user']['surname'] == 'Tester'
