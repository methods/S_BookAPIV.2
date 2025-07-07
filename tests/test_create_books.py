# pylint: disable=missing-docstring,line-too-long, too-many-arguments, too-many-positional-arguments
from unittest.mock import patch, MagicMock
import sys
import runpy
from app.datastore.mongo_helper import insert_book_to_mongo
from scripts.create_books import main, populate_books, run_population

# --------------------- Helper functions ------------------------------
def run_create_books_script_cleanup():
    """
    Safely re-runs the 'scripts.create_books' module as a script.

    Removes 'scripts.create_books' from sys.modules to avoid re-import conflicts,
    then executes it using runpy as if run from the command line (__main__ context).
    """
    sys.modules.pop("scripts.create_books", None)
    runpy.run_module("scripts.create_books", run_name="__main__")

# ------------------------- Test Suite -------------------------------


def test_populate_books_inserts_data_to_db(mock_books_collection, sample_book_data):

    # Arrange
    test_books = sample_book_data
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
def test_run_population_orchestrates_logic(
    mock_get_collection,
    mock_load_books,
    mock_populate_books,
    sample_book_data):
    """
    Tests that run_population correctly calls its dependencies
    and returns the right status message.
    """
    # Arrange
    test_books = sample_book_data
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection
    mock_load_books.return_value = test_books
    mock_populate_books.return_value = test_books # Simulate 2 books inserted

    expected_message = f"Inserted {len(test_books)} books"

    # Act
    result_message = run_population()

    # Assert
    assert result_message == expected_message
    mock_get_collection.assert_called_once()
    mock_load_books.assert_called_once()
    mock_populate_books.assert_called_once_with(mock_collection, test_books)


@patch("scripts.create_books.get_book_collection")
def test_run_population_handles_no_collection(mock_get_collection):
    """
    Tests the failure path where the database collection is not available.
    """
    # Arrange
    mock_get_collection.return_value = None
    expected_message = "Error: no books_collection object found"

    # Act
    result_message = run_population()

    # Assert
    assert result_message == expected_message


@patch("scripts.create_books.get_book_collection")
@patch("scripts.create_books.load_books_json")
def test_run_population_handles_no_books_json(
    mock_load_books_json,
    mock_get_book_collection
    ):
    # Arrange
    mock_get_book_collection.return_value = MagicMock()
    mock_load_books_json.return_value = None
    expected_message = "Error: no books_data JSON found"

    # Act
    result_message = run_population()

    # Assert
    assert result_message == expected_message
    mock_get_book_collection.assert_called_once()
    mock_load_books_json.assert_called_once()


@patch("scripts.create_books.get_book_collection")
@patch("scripts.create_books.load_books_json")
@patch("scripts.create_books.populate_books")
def test_run_population_handles_no_inserted_list_books(
    mock_populate_books,
    mock_load_books_json,
    mock_get_book_collection,
    sample_book_data
    ):
    # Arrange
    mock_get_book_collection.return_value = MagicMock()
    mock_load_books_json.return_value = sample_book_data
    mock_populate_books.return_value = None
    expected_message = "Error: Population step failed and returned no data."

    # Act
    result_message = run_population()

    # Assert
    assert result_message == expected_message
    mock_get_book_collection.assert_called_once()
    mock_load_books_json.assert_called_once()
    mock_populate_books.assert_called_once_with(mock_get_book_collection.return_value, sample_book_data)


@patch("scripts.create_books.create_app")
@patch("scripts.create_books.run_population")
def test_main_creates_app_context_and_calls_run_population(
    mock_run_population,
    mock_create_app,
    capsys):

    # Arrange
    # Mock Flask app object that has a working app_context manager
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    mock_run_population.return_value = "Success from mock"
    expected_output = "Success from mock\n"

    # Act
    main()
    captured = capsys.readouterr()

    # Assert
    # 1. Did we set up the environment correctly?
    mock_create_app.assert_called_once()
    mock_app.app_context.return_value.__enter__.assert_called_once()

    # 2. Did we call the core logic?
    mock_run_population.assert_called_once()

    # 3. Did we print the result?
    assert captured.out == expected_output


@patch("app.datastore.mongo_helper.insert_book_to_mongo")
@patch("utils.db_helpers.load_books_json")     # PATCHING AT THE SOURCE
@patch("app.datastore.mongo_db.get_book_collection") # PATCHING AT THE SOURCE
def test_script_entry_point_calls_main(
    mock_get_collection,
    mock_load_json,
    mock_insert_book,
    sample_book_data
    ):
    # Arrange test_book sample and return values of MOCKS
    test_books = sample_book_data

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


def test_run_population_should_insert_new_book_when_id_does_not_exist(
    monkeypatch,
    mock_books_collection,
    sample_book_data
    ):
    # Arrange
    mock_db_collection_func = MagicMock(return_value=mock_books_collection)
    monkeypatch.setattr('scripts.create_books.get_book_collection', mock_db_collection_func)

    mock_load_data = MagicMock(return_value=sample_book_data)
    monkeypatch.setattr('scripts.create_books.load_books_json', mock_load_data)

    assert mock_books_collection.count_documents({}) == 0

    # Act
    # Call the function with the new list_of_books and the MONGODB COLLECTION instance
    result_message = run_population()

    # Assert
    mock_db_collection_func.assert_called_once()
    mock_load_data.assert_called_once()

    # Check for specific book to be sure the data is right
    book_a_from_db = mock_books_collection.find_one({"id": "550e8400-e29b-41d4-a716-446655440000"})
    assert book_a_from_db is not None
    assert book_a_from_db['title'] == "To Kill a Mockingbird"

    # Verify that the function returned the correct status message
    assert result_message == "Inserted 2 books"

def test_run_population_correctly_upserts_a_batch_of_books(
    mock_books_collection,
    monkeypatch
):
    """
    BEHAVIORAL TEST: Verifies that run_population correctly handles a mix
    of new and existing books, resulting in a fully updated collection.
    """
    # ARRANGE
    common_id = "550e8400-e29b-41d4-a716-446655440000"

    # Pre-seed the database with an "old" version of a book
    old_book_version = {
        "id": common_id,
        "title": "The Age of Surveillance talism",
        "synopsis": "An exploration of how major tech companies use personal data to predict and influence behavior in the modern economy.",
        "author": "S Zuboff",
        "version": "old",
        "links": {
            "self": "/books/550e8400-e29b-41d4-a716-446655440003",
            "reservations": "/books/550e8400-e29b-41d4-a716-446655440003/reservations",
            "reviews": "/books/550e8400-e29b-41d4-a716-446655440003/reviews"
        },
        "state": "active"
    }
    mock_books_collection.insert_one(old_book_version)

    # Define the "new book" data that the script will load
    # This list contains the updated book and a brand new one
    new_book_data_from_json = [
        {
            "id": common_id,
            "title": "The Age of Surveillance Capitalism",
            "synopsis": "An exploration of how major tech companies use personal data to predict and influence behavior in the modern economy.",
            "author": "Shoshana Zuboff",
            "links": {
                "self": "/books/550e8400-e29b-41d4-a716-446655440003",
                "reservations": "/books/550e8400-e29b-41d4-a716-446655440003/reservations",
                "reviews": "/books/550e8400-e29b-41d4-a716-446655440003/reviews"
            },
            "state": "active"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "title": "Brave New World",
            "synopsis": "A futuristic novel exploring a society shaped by genetic engineering and psychological manipulation.",
            "author": "Aldous Huxley",
            "links": {
                "self": "/books/550e8400-e29b-41d4-a716-446655440002",
                "reservations": "/books/550e8400-e29b-41d4-a716-446655440002/reservations",
                "reviews": "/books/550e8400-e29b-41d4-a716-446655440002/reviews"
            },
            "state": "active"
        }
    ]

    # Monkeypatch the helper functions to isolate test
    # - make get_book_collection return our mockDB
    # - make load_books_json return our hard-coded new data
    monkeypatch.setattr("scripts.create_books.get_book_collection", lambda: mock_books_collection)
    monkeypatch.setattr("scripts.create_books.load_books_json", lambda: new_book_data_from_json)

    # Sanity check: confim the database starts with exactly one document
    assert mock_books_collection.count_documents({}) == 1

    # Act
    run_population()

    # Assert
    # Check final state of database, total count == 2
    assert mock_books_collection.count_documents({}) == 2, "The total document count should be 2"

    # Retrieve the book we expected to be replaced and verify its contents
    updated_book = mock_books_collection.find_one({"id": common_id})

    assert updated_book is not None, "The updated book was not found in the database"
    assert updated_book["title"] == "The Age of Surveillance Capitalism"
    assert updated_book["author"] == "Shoshana Zuboff"
    assert "version" not in updated_book


def test_insert_book_to_mongo_replaces_document_when_id_exists(mock_books_collection):
    """
    UNIT TEST: Verifies that insert_book_to_mongo performs a replacement
    on a single document if the ID already exists.
    """
    # --- ARRANGE ---
    common_id = "550e8400-e29b-41d4-a716-446655440000"

    # Pre-seed the database with an "old" version of a book
    old_book_version = {
        "id": common_id,
        "title": "The Age of Surveillance talism",
        "synopsis": "An exploration of how major tech companies use personal data to predict and influence behavior in the modern economy.",
        "author": "S Zuboff",
        "version": "old",
        "links": {
            "self": "/books/550e8400-e29b-41d4-a716-446655440003",
            "reservations": "/books/550e8400-e29b-41d4-a716-446655440003/reservations",
            "reviews": "/books/550e8400-e29b-41d4-a716-446655440003/reviews"
        },
        "state": "active"
    }
    mock_books_collection.insert_one(old_book_version)
    assert mock_books_collection.count_documents({}) == 1

    # Define new version of book
    new_book = {
            "id": common_id,
            "title": "The Age of Surveillance Capitalism",
            "synopsis": "An exploration of how major tech companies use personal data to predict and influence behavior in the modern economy.",
            "author": "Shoshana Zuboff",
            "links": {
                "self": "/books/550e8400-e29b-41d4-a716-446655440003",
                "reservations": "/books/550e8400-e29b-41d4-a716-446655440003/reservations",
                "reviews": "/books/550e8400-e29b-41d4-a716-446655440003/reviews"
            },
            "state": "active"
        }

    # ACT: Call the function under test directly
    insert_book_to_mongo(new_book, mock_books_collection)

    # ASSERT
    assert mock_books_collection.count_documents({}) == 1

    # Fetch the document and verify its contents are new
    updated_book = mock_books_collection.find_one({"id": common_id})

    assert updated_book is not None, "The updated book was not found in the database"
    assert updated_book["title"] == "The Age of Surveillance Capitalism"
    assert updated_book["author"] == "Shoshana Zuboff"
