# pylint: disable=line-too-long
"""
A configuration file for pytest.

This file contains shared fixtures and helpers that are automatically discovered by pytest and made available to all tests.
"""
from unittest.mock import patch

import bcrypt
import mongomock
import pytest
from bson.objectid import ObjectId

from app import create_app
from app.datastore.mongo_db import get_book_collection
from app.extensions import bcrypt, mongo


@pytest.fixture(name="_insert_book_to_db")
def stub_insert_book():
    """Fixture that mocks insert_book_to_mongo() to prevent real DB writes during tests. Returns a mock with a fixed inserted_id."""

    with patch("app.routes.legacy_routes.insert_book_to_mongo") as mock_insert_book:
        mock_insert_book.return_value.inserted_id = "12345"
        yield mock_insert_book


@pytest.fixture(name="mock_books_collection")
def mock_books_collection_fixture():
    """Provides an in-memory, empty 'books' collection for each test."""
    # mongomock.MongoClient() creates a fake client.
    mongo_client = mongomock.MongoClient()
    db = mongo_client["test_database"]
    return db["test_books_collection"]


@pytest.fixture(name="sample_book_data")
def sample_book_data():
    """Provides an sample 'books' collection for each test."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "To Kill a Mockingbird",
            "synopsis": "The story of racial injustice and the loss of innocence in the American South.",
            "author": "Harper Lee",
            "links": {
                "self": "/books/550e8400-e29b-41d4-a716-446655440000",
                "reservations": "/books/550e8400-e29b-41d4-a716-446655440000/reservations",
                "reviews": "/books/550e8400-e29b-41d4-a716-446655440000/reviews",
            },
            "state": "active",
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "title": "1984",
            "synopsis": "A dystopian novel about totalitarianism and surveillance.",
            "author": "George Orwell",
            "links": {
                "self": "/books/550e8400-e29b-41d4-a716-446655440001",
                "reservations": "/books/550e8400-e29b-41d4-a716-446655440001/reservations",
                "reviews": "/books/550e8400-e29b-41d4-a716-446655440001/reviews",
            },
            "state": "active",
        },
    ]


@pytest.fixture()
def test_app():
    """
    Creates the Flask app instance configured for testing.
    This is the single source of truth for the test app.
    """
    app = create_app(
        {
            "TESTING": True,
            "TRAP_HTTP_EXCEPTIONS": True,
            "API_KEY": "test-key-123",
            "SECRET_KEY": "a-secure-key-for-testing-only",
            "JWT_SECRET_KEY": "a-secure-jwt-key-for-testing-only",
            "MONGO_URI": "mongodb://localhost:27017/",
            "DB_NAME": "test_database",
            "COLLECTION_NAME": "test_books",
        }
    )
    # The application now uses the Flask-PyMongo extension,
    # which requires initialization via `init_app`.
    # In the test environment, the connection to a real database fails,
    # leaving `mongo.db` as None.
    # Fix: Manually patch the global `mongo` object's connection with a `mongomock` client.
    # This ensures all tests run against a fast, in-memory mock database AND
    # are isolated from external services."
    with app.app_context():
        mongo.cx = mongomock.MongoClient()
        mongo.db = mongo.cx[app.config["DB_NAME"]]

    yield app


@pytest.fixture(name="client")
def client(test_app):  # pylint: disable=redefined-outer-name
    """A test client for the app."""
    return test_app.test_client()


@pytest.fixture(scope="function")
def db_setup(test_app):  # pylint: disable=redefined-outer-name
    """
    Sets up and tears down the database for a test.
    Scope is "function" to ensure a clean DB for each test.
    """
    # Use app_context to access the database
    with test_app.app_context():
        collection = get_book_collection()

        collection.delete_many({})
    # Pass control to the test function
    yield

    # Teardown: code runs after the test is finished
    with test_app.app_context():
        collection = get_book_collection()
        collection.delete_many({})


# Fixture for tests/test_auth.py
@pytest.fixture(scope="function")
def mongo_setup(test_app):  # pylint: disable=redefined-outer-name
    """
    Updated to a more robust setup fixture.
    Ensures all relevant collections ('users', 'books', 'reservations')
    are clean before each test fucntion runs.
    """
    with test_app.app_context():
        # Clear all collections before using in tests
        mongo.db.users.delete_many({})
        mongo.db.books.delete_many({})
        mongo.db.reservations.delete_many({})

    yield

    with test_app.app_context():
        # Clear after tests have run
        mongo.db.users.delete_many({})
        mongo.db.books.delete_many({})
        mongo.db.reservations.delete_many({})


TEST_USER_ID = "6154b3a3e4a5b6c7d8e9f0a1"
PLAIN_PASSWORD = "a-secure-password"


@pytest.fixture(scope="session")  # because this data never changes
def mock_user_data():
    """Provides a dictionary of a test user's data, with a hashed password."""
    # Use Flask-Bcrypt's function to CREATE the hash.
    hashed_password = bcrypt.generate_password_hash(PLAIN_PASSWORD).decode("utf-8")

    return {
        "_id": ObjectId(TEST_USER_ID),
        "email": "testuser@example.com",
        "password": hashed_password,
        "role": "user",
    }

@pytest.fixture(scope="session")
def mock_admin_data():
    """
    PROVIDES a dictionary of a test admin's data,
    WITH a hashed password
    """
    hashed_password = bcrypt.generate_password_hash("admin-password").decode("utf-8")

    return {
        "email": "admin@example.com",
        "password": hashed_password,
        "role": "admin", # Role explicityly set to 'admin'
    }

@pytest.fixture
def seeded_user_in_db(
    test_app, mock_user_data, mongo_setup
):  # pylint: disable=redefined-outer-name
    """
    Ensures the test database is clean and contains exactly one predefined user.
    Depends on:
    - test_app: To get the application context and correct mongo.db object
    - mock_user_data: To get the user data to insert.
    - mongo_setup: To ensure the users collection is empty before seeding.
    """
    _ = mongo_setup

    with test_app.app_context():
        mongo.db.users.insert_one(mock_user_data)

    yield_data = mock_user_data.copy()
    yield_data["_id"] = str(yield_data["_id"])

    yield yield_data


@pytest.fixture
def seeded_admin_in_db(test_app, mock_admin_data, mongo_setup): # pylint: disable=redefined-outer-name
    """
    Ensures the test database is clean and 
    Contains exaclty one predefined admin
    """
    _ = mongo_setup

    with test_app.app_context():
        result = mongo.db.users.insert_one(mock_admin_data)

    yield_data = mock_admin_data.copy()
    yield_data["_id"] = str(result.inserted_id)
    yield yield_data


@pytest.fixture
def user_token(client, seeded_user_in_db): # pylint: disable=redefined-outer-name
    """Logs in the seeded user and returns a valid JWT"""
    _ = seeded_user_in_db
    login_payload = {
        "email": "testuser@example.com",
        "password": PLAIN_PASSWORD
    }

    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200, "Failed to log in test user"
    token = response.get_json()["token"]
    return token

@pytest.fixture
def admin_token(client, seeded_admin_in_db): # pylint: disable=redefined-outer-name
    """Logs in the seeded admin and returns a valid JWT."""
    _ = seeded_admin_in_db
    login_payload = {
        "email": "admin@example.com",
        "password": "admin-password"
    }

    resposne = client.post("/auth/login", json=login_payload)
    assert resposne.status_code == 200, "Failed to log in test admin"
    token = resposne.get_json(["token"])
    return token
