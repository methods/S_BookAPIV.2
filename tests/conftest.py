# pylint: disable=line-too-long
"""
A configuration file for pytest.

This file contains shared fixtures and helpers that are automatically discovered by pytest and made available to all tests.
"""

import mongomock
import pytest
from app import create_app


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
    """Creates an app with a specific 'TESTING' config"""
    app = create_app({
        "TESTING": True, 
        "API_KEY": "test-key-123"
        })
    yield app

@pytest.fixture(name="test_client")
def client(app):
    """A test client for the app."""
    return app.test_client()
