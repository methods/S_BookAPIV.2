# pylint: disable=missing-docstring,line-too-long
from unittest.mock import patch, MagicMock
import mongomock
import pytest
from scripts.create_books import main, populate_books

@pytest.fixture(name="mock_books_collection")
def mock_books_collection_fixture():
    """Provides an in-memory, empty 'books' collection for each test."""
    # mongomock.MongoClient() creates a fake client.
    client = mongomock.MongoClient()
    db = client['test_database']
    return db["test_books_collection"]

def test_populate_books_inserts_data_to_db(mock_books_collection):

    # Arrange
    test_books = [
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
    expected_book_count = len(test_books)

    # Act
    # Inject our mockbooks collection and test_data into the function
    result = populate_books(mock_books_collection, test_books)

    # 1. Assert - function's return value for immediate feedback
    assert isinstance(result, list)
    assert len(result) == expected_book_count

    # Assert - final state of the db
    assert mock_books_collection.count_documents({}) == expected_book_count

    # 3. Assert - spot-check acutal content
    retrieved_book = mock_books_collection.find_one({"title": "1984"})
    assert retrieved_book is not None
    assert retrieved_book["author"] == "George Orwell"

# Use patch to replace real functions with mock objects
# Note: They are applied bottom-up - the last decorater is the first argument
@patch("scripts.create_books.populate_books")
@patch("scripts.create_books.load_books_json")
@patch("scripts.create_books.get_book_collection")
def test_main_orchestrates_book_creation_and_prints_summary(
    mock_get_collection,
    mock_load_books,
    mock_populate_books,
    capsys):
    # Arrange
    test_books = [
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

    # Arrange: configure the return values of the MOCKS
    mock_collection = MagicMock()

    # When get_book_collection is called, it will return our fake collection
    mock_get_collection.return_value = mock_collection

    # When load_books_json is called, it will return our fake book data
    mock_load_books.return_value = test_books

    # When populate_books is called, we'll pretend it inserted 2 books
    mock_populate_books.return_value = test_books

    expected_output = f"Inserted {len(test_books)} books\n"


    # Act: Call the main function. It will use our mocks instead of the real functions.
    main()
    # Capture everything printed to the console
    captured = capsys.readouterr()
    assert captured.out == expected_output
    # Good practice to ensure no errors were printed
    assert captured.err == ""

    # Did it call our dependencies as epxected?
    mock_get_collection.assert_called_once()
    mock_load_books.assert_called_once()
    mock_populate_books.assert_called_once()
