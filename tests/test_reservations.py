# pylint: disable=redefined-outer-name
"""
This module contains tests for the reservation functionality of the application,
including setup fixtures and test cases for creating, validating, and handling reservations.
Fixtures provide a clean database state and authentication for each test.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from bson.objectid import ObjectId

from app.extensions import mongo


# ------------------- FILE SPECIFIC FIXTURES -----------------
@pytest.fixture
def client_with_book(client, mongo_setup, test_app):
    """
    Provides a test client,
    ensures the database is clean (via mongo_setup) and
    seeds a single book for reservation tests.
    """
    _ = mongo_setup
    with test_app.app_context():
        mongo.db.books.insert_one(
            {"_id": ObjectId("5f8f8b8b8b8b8b8b8b8b8b8b"), "title": "Test Book"}
        )

    yield client


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
    secret_key = app.config.get("JWT_SECRET_KEY")

    # Section 2: Define the token's payload
    # Use the ID from the user seeded into the database by the fixture
    fake_user_id = seeded_user_in_db["_id"]
    payload = {
        "sub": fake_user_id,
        "iat": datetime.now(timezone.utc),  # Issued at
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),  # Expires at
    }

    # Section 3: Encode the token and create the header
    # PyJWT's encode function creates the token string.
    token = jwt.encode(payload, secret_key, algorithm="HS256")

    # The HTTP header must be in the format 'Bearer <token>'
    headers = {"Authorization": f"Bearer {token}"}

    return headers


#            ------------------ TESTS -----------------------


@pytest.mark.parametrize(
    "payload, expected_message",
    [
        ("invalid!!", "Invalid Book ID"),
    ],
)
def test_reservation_with_invalid_book_id(
    payload, expected_message, client_with_book, auth_token, seeded_user_in_db
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
        f"/books/{payload}/reservations",
        json={"forenames": "Firstname", "surname": "Tester"},
        headers=auth_token,
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == expected_message


def test_reservation_for_nonexistant_book(
    client_with_book, auth_token, seeded_user_in_db
):
    """
    GIVEN a FLASK APP WITH A PRE-EXISTING BOOK
    WHEN a POST request is made with a valid but non-existent book ID
    THEN a 404 Not Found status is returned
    """
    _ = client_with_book
    _ = seeded_user_in_db
    non_existent_id = ObjectId()

    response = client_with_book.post(
        f"/books/{non_existent_id}/reservations", headers=auth_token
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
        f"/books/{book_id}/reservations", headers=auth_token, json={}
    )

    # Assert
    data = response.get_json()
    assert (
        response.status_code == 201
    ), f"Expected 201, got {response.status_code} with data: {data}"  # pylint: disable=line-too-long
    assert data["state"] == "reserved"


def test_create_reservation_for_already_reserved_book_fails(
    client_with_book, auth_token, seeded_user_in_db
):
    """
    GIVEN a user who already reserved a specific book
    WHEN they attempt to reserve that same book again
    THEN a 409 Conflict status is returned.
    """
    _ = client_with_book
    _ = seeded_user_in_db
    book_id = "5f8f8b8b8b8b8b8b8b8b8b8b"
    url = f"/books/{book_id}/reservations"

    # Arrange: Create the first reservation
    response1 = client_with_book.post(url, headers=auth_token, json={})
    assert response1.status_code == 201, "The initial reservation failed"

    # ACT
    response2 = client_with_book.post(url, headers=auth_token, json={})

    # Assert
    assert response2.status_code == 409
    data = response2.get_json()
    assert data["error"] == "You have already reserved this book"


# ============= GET /books/{id}/reservations TESTS & Fixtures ======================

# New fixture, SCOPED TO THIS FILE, that sets up the specific data we need.abs
def seeded_book_with_reservation(mongo_setup, seeded_user_in_db, test_app):
    """
    Uses the app context and mock mongo to seed a book and a reservation.
    Yields the IDSs of the created documents.
    Depends on mongo_setup to ensure clean state.
    """
    _ = mongo_setup
    _ = seeded_user_in_db

    with test_app.app_context():
        # Get the user ID from the user that's already in the mock DB
        user_id = ObjectId(seeded_user_in_db("_id"))

        book_id = test_app.app.mongo.books.insert_one(
            {
                "title": "The Admin's Guide",
                "author": "Dr. Secure",
            }
        ).inserted_id

        test_app.mongo.db.reservations.insert_one(
            {
                "book_id": book_id,
                "user_id": user_id,
                "status": "active",
            }
        )
    yield {"book_id": str(book_id), "user_id": str(user_id)}

def test_get_reservations_as_admin(client, admin_token, seeded_book_with_reservation):
    """
    GIVEN a valid book ID and an admin user's JWT
    WHEN the GET /books/{id}/reservations endpoint is hit
    THEN it should return 200 OK and list of reservations
    """
    # Arrange
    book_id = seeded_book_with_reservation["book_id"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Act
    response = client.get(f"/books/{book_id}/reservations", headers=headers)
    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert "reservations" in data
    assert len(data["reservations"]) == 1
    assert data["reservations"][0]["status"] == "active"
    assert data["reservations"][0]["user_id"] == seeded_book_with_reservation["user_id"]


def test_get_reservations_as_user(client, user_token, seeded_book_with_reservation):
    """
    GIVEN a valid book ID and a regular user's JWT
    WHEN the GET /books/{id}/ reservations endpoint is hit
    THEN it should return a 403 Forbidden error
    """
    # Arrange
    book_id = seeded_book_with_reservation["book_id"]
    headers = {"Authorization": f"Bearer {user_token}"}
    # Act
    response = client.get(f"/books/{book_id}/reservations", headers=headers)
    # Assert
    assert response.status_code == 403
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Admin privileges required."


def test_get_reservations_unauthenticated(client, seeded_book_with_reservation):
    """
    GIVEN a valid book ID but no JWT
    WHEN the GET /books/{id}/reservations endpoint is hit
    THEN it should return a 401 Unauthorized error
    """
    book_id = seeded_book_with_reservation["book_id"]
    response = client.get(f"/books/{book_id}/reservations") # no header

    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Authorization header missing"


def test_get_reservations_for_nonexistent_book(client, admin_token):
    """
    GIVEN a non-existent book ID and an admin user's JWT
    WHEN the GET /books/{id}/reservations endpoint is hit
    THEN it should return a 404 Not Found error
    """
    non_existent_id = ObjectId()
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(f"/books/{non_existent_id}/reservations", headers=headers)

    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Book not found"