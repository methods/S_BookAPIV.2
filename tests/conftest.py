# pylint: disable=line-too-long
"""
A configuration file for pytest.

This file contains shared fixtures and helpers that are automatically discovered by pytest and made available to all tests.
"""
from unittest.mock import patch

import mongomock
import pytest

from app import create_app, mongo
from app.datastore.mongo_db import get_book_collection


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
            "MONGO_URI": "mongodb://localhost:27017/",
            "DB_NAME": "test_database",
            "COLLECTION_NAME": "test_books",
        }
    )
    # PATCH mongodb context to be mock db object
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
def users_db_setup(test_app):  # pylint: disable=redefined-outer-name
    """
    Sets up and tears down the 'users' collection for a test.
    """
    with test_app.app_context():
        # Now, the 'mongo' variable is defined and linked to the test_app
        users_collection = mongo.db.users
        users_collection.delete_many({})

    yield

    with test_app.app_context():
        users_collection = mongo.db.users
        users_collection.delete_many({})
