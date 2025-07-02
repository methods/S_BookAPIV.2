# pylint: disable=missing-docstring,line-too-long
from unittest.mock import patch, MagicMock
import sys
import runpy
import mongomock
import pytest
from scripts.create_books import main, populate_books

# -------------------- PyFixtures ---------------------------------
@pytest.fixture(name="mock_books_collection")
def mock_books_collection_fixture():
    """Provides an in-memory, empty 'books' collection for each test."""
    # mongomock.MongoClient() creates a fake client.
    client = mongomock.MongoClient()
    db = client['test_database']
    return db["test_books_collection"]

# --------------------- Helper functions ------------------------------
def sample_book_data():
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

def run_create_books_script_cleanup():
    """
    Safely re-runs the 'scripts.create_books' module as a script.

    Removes 'scripts.create_books' from sys.modules to avoid re-import conflicts,
    then executes it using runpy as if run from the command line (__main__ context).
    """
    sys.modules.pop("scripts.create_books", None)
    runpy.run_module("scripts.create_books", run_name="__main__")

# ------------------------- Test Suite -------------------------------


def test_populate_books_inserts_data_to_db(mock_books_collection):

    # Arrange
    test_books = sample_book_data()
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
@patch("scripts.create_books.create_app")
@patch("scripts.create_books.populate_books")
@patch("scripts.create_books.load_books_json")
@patch("scripts.create_books.get_book_collection")
def test_main_creates_app_context_and_orchestrates_book_creation(
    mock_get_collection,
    mock_load_books,
    mock_populate_books,
    mock_create_app,
    capsys):

    # Arrange
    # Mock Flask app object that has a working app_context manager
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    test_books = sample_book_data()

    # Arrange: configure the return values of the MOCKS
    # Create mock mongodb collection
    mock_collection = MagicMock()

    # When get_book_collection is called, it will return our mocked collection
    mock_get_collection.return_value = mock_collection

    # When load_books_json is called, it will return our test_books data
    mock_load_books.return_value = test_books

    # When populate_books is called, we'll pretend it inserted 2 books
    mock_populate_books.return_value = test_books

    expected_output = f"Inserted {len(test_books)} books\n"


    # Act: Call the main function. It will use our mocks instead of the real functions.
    main()
    # Capture everything printed to the console
    captured = capsys.readouterr()

    # Assert
    assert captured.out == expected_output
    # Good practice to ensure no errors were printed
    assert captured.err == ""

    # Did it call our dependencies as expected?
    mock_create_app.assert_called_once()
    # Asserts the 'with' statement's '__enter__' method is called once
    mock_app.app_context.return_value.__enter__.assert_called_once()
    mock_get_collection.assert_called_once()
    mock_load_books.assert_called_once()
    mock_populate_books.assert_called_once()


@patch("app.datastore.mongo_helper.insert_book_to_mongo")
@patch("utils.db_helpers.load_books_json")     # PATCHING AT THE SOURCE
@patch("app.datastore.mongo_db.get_book_collection") # PATCHING AT THE SOURCE
def test_script_entry_point_calls_main(
    mock_get_collection,
    mock_load_json,
    mock_insert_book
    ):
    # Arrange test_book sample and return values of MOCKS
    test_books = sample_book_data()

    mock_load_json.return_value = test_books
    # Mock mongodb collection object
    mock_collection_obj = MagicMock()
    mock_get_collection.return_value = mock_collection_obj

    # Act: Run the script's main entry point.
    run_create_books_script_cleanup()

    # Assert: Verify mocked dependencies were called correctly.
    mock_get_collection.assert_called_once()
    mock_load_json.assert_called_once()

    assert mock_insert_book.call_count == len(test_books)
    mock_insert_book.assert_any_call(test_books[0], mock_collection_obj)
    mock_insert_book.assert_any_call(test_books[1], mock_collection_obj)
