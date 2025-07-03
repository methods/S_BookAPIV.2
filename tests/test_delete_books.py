# pylint: disable=missing-docstring,line-too-long
import mongomock
import pytest
from scripts.delete_books import delete_all_books

# ----------------- PyFixtures ---------------------------------
@pytest.fixture(name="mock_books_collection")
def mock_books_collection_fixture():
    """Provides an in-memory, empty 'books' collection for each test."""
    # mongomock.MongoClient() creates a fake client.
    client = mongomock.MongoClient()
    db = client['test_database']
    return db["test_books_collection"]

@pytest.fixture(name="initial_book_data")
def initial_book_data_fixture():
    """Provides the initial list of book documents."""
    return [
            {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "To Kill a Mockingbird",
            "synopsis": "The story of racial injustice and the loss of innocence in the American South.",
            "author": "Harper Lee",
            "links": {
                "self": "/books/550e8400-e29b-41d4-a716-446655440000",
                "reservations": "/books/550e8400-e29b-41d4-a716-446655440000/reservations",
                "reviews": "/books/550e8400-e29b-41d4-a716-446655440000/reviews"
                },
            "state": "active"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "title": "1984",
            "synopsis": "A dystopian novel about totalitarianism and surveillance.",
            "author": "George Orwell",
            "links": {
                "self": "/books/550e8400-e29b-41d4-a716-446655440001",
                "reservations": "/books/550e8400-e29b-41d4-a716-446655440001/reservations",
                "reviews": "/books/550e8400-e29b-41d4-a716-446655440001/reviews"
                },
            "state": "active"
        }
    ]

# ----------------- TEST SUITE ---------------------------------

def test_delete_database_empties_database(mock_books_collection, initial_book_data):
    # Arrange - integration test = MongoMock
    # Insert the data from mock_DB_state into the empty mock_books_collection
    mock_books_collection.insert_many(initial_book_data)
    # Sanity check: make sure the data is there before we act.
    assert mock_books_collection.count_documents({}) == 2

    # Act
    # Use function to delete
    delete_all_books(mock_books_collection)

    # Assert
    # returns message everything is deleted
    # checks length is 0
    assert mock_books_collection.count_documents({}) == 0
