# pylint: disable=redefined-outer-name
"""..."""
from datetime import datetime, timedelta, timezone
from bson.objectid import ObjectId
import pytest
import jwt
from app.extensions import mongo

# ------------------- FILE SPECIFIC FIXTURES -----------------
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


@pytest.fixture(scope="function")
def auth_token(client_with_book, seeded_user_in_db):
    """
    GIVEN a test client
    WHEN this fixture is used
    THEN a valid JWT and Authorization header are generated for a user that exists in the database.
    """
    _ = client_with_book

    # Section 1: Get the app context and secret key
    app = client_with_book.application
    secret_key = app.config.get('JWT_SECRET_KEY')

    # Section 2: Define the token's payload
    # Use the ID from the user seeded into the databse by the fixture
    fake_user_id = seeded_user_in_db['_id']
    payload = {
        'sub': fake_user_id,
        'iat': datetime.now(timezone.utc),  # Issued at
        'exp': datetime.now(timezone.utc) + timedelta(minutes=15) # Expires at
    }

    # Section 3: Encode the token and create the header
    # PyJWT's encode function creates the token string.
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    # The HTTP header must be in the format 'Bearer <token>'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    return headers

#            ------------------ TESTS -----------------------

@pytest.mark.parametrize("payload, expected_message",
    [
        ("invalid!!", "Invalid Book ID"),
    ]
)
def test_reservation_with_invalid_book_id(
    payload,
    expected_message,
    client_with_book,
    auth_token,
    seeded_user_in_db
    ):
    """
    GIVEN a Flask app with a pre-existing book in the mock DB
    WHEN a POST request is made to /books/<book_id>/reservations without a book_id_str argument
    THEN a 400 status code is returned.
    """
    _ = client_with_book
    _ = seeded_user_in_db

    # Act
    response = client_with_book.post(
        f'/books/{payload}/reservations',
        json={"forenames": "Firstname", "surname": "Tester"},
        headers=auth_token

    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == expected_message


def test_reservation_for_nonexistant_book(
    client_with_book,
    auth_token,
    seeded_user_in_db
    ):
    """
    GIVEN a FLASK APP WITH A PRE-EXISTING BOOK
    WHEN a POST request is made with a valid but non-existent book ID
    THEN a 404 Not Found statu sis returned
    """
    _ = client_with_book
    _ = seeded_user_in_db
    non_existent_id = ObjectId()

    response = client_with_book.post(
        f'/books/{non_existent_id}/reservations',
        headers=auth_token
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Book not found"


def test_create_reservation_success(client_with_book, auth_token, seeded_user_in_db):
    """
    GIVEN a Flask app with a pre-existing book in the mock DB
    WHEN a POST request is made to /books/<book_id>/reservations with valid data
    THEN a 201 status code is returned with the new reservation data
    """
    _ = client_with_book
    # Arrange
    book_id = "5f8f8b8b8b8b8b8b8b8b8b8b"
    _expected_user_id = seeded_user_in_db["_id"]

    # Act- make an authenticated request
    response = client_with_book.post(
        f'/books/{book_id}/reservations',
        headers=auth_token,
        json={}
    )

    # Assert
    data = response.get_json()
    assert response.status_code == 201, f"Expected 201, got {response.status_code} with data: {data}" # pylint disable=line-too-long
    assert data['state'] == 'reserved'
