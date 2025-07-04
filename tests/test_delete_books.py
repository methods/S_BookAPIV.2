# pylint: disable=missing-docstring,line-too-long
from unittest.mock import patch, MagicMock
from scripts.delete_books import delete_all_books, main


# ----------------- TEST SUITE ---------------------------------

def test_delete_database_empties_database(mock_books_collection, sample_book_data):
    # Arrange - integration test = MongoMock
    # Insert the data from mock_DB_state into the empty mock_books_collection
    mock_books_collection.insert_many(sample_book_data)
    # Sanity check: 
    assert mock_books_collection.count_documents({}) == len(sample_book_data)

    # Act
    # Use function to delete
    deleted_count = delete_all_books(mock_books_collection)
    # Assert
    assert deleted_count == len(sample_book_data)
    assert mock_books_collection.count_documents({}) == 0


@patch("scripts.delete_books.create_app")
@patch("scripts.delete_books.MongoClient")
@patch("scripts.delete_books.delete_all_books")
def test_main_orchestrates_book_creation_and_reports_success_when_books_are_deleted(
    mock_delete_all_books,
    mock_mongo_client,
    mock_create_app,
    capsys):

    # Arrange: create Flask app object with working app_context manager
    mock_app = MagicMock()
    fake_db_name = 'fake_db'
    mock_app.config = {
        'MONGO_URI': 'mongodb://fake_uri:27017',
        'DB_NAME': 'fake_db',
        'COLLECTION_NAME': 'fake_collection'
    }
    mock_create_app.return_value = mock_app

    # Configure the mock for MongoClient()
    mock_client_instance = mock_mongo_client.return_value
    mock_db = mock_client_instance['fake_db']
    mock_collection = mock_db['fake_collection']
    mock_delete_all_books.return_value = 2

    # Act: run the function we are testing
    # It will use our MOCKS instead of real functions
    main()
    
    # Assert
    captured = capsys.readouterr()
    assert "Connecting to database 'fake_db'..." in captured.out
    assert f"✅ Success: Dropped {mock_delete_all_books.return_value} existing document(s)." in captured.out
    # Good practice to ensure no errors were printed
    assert captured.err == ""

    # Assert
    mock_create_app.assert_called_once()
    mock_mongo_client.assert_called_once_with('mongodb://fake_uri:27017')
    mock_delete_all_books.assert_called_once_with(mock_collection)

@patch("scripts.delete_books.create_app")
@patch("scripts.delete_books.delete_all_books")
def test_main_reports_info_when_collection_is_empty(
    mock_delete_all_books, mock_create_app, capsys
):
    """
    Unit Test: Verifies `main`'s logic for the "already empty" path.
    GIVEN the delete_all_books function reports it deleted 0 documents,
    WHEN main() is called,
    THEN it should print the informational message.
    """
    # ARRANGE
    mock_app = MagicMock()
    mock_app.config = {
        'MONGO_URI': 'x', 
        'DB_NAME': 'db', 
        'COLLECTION_NAME': 'col'}
    mock_create_app.return_value = mock_app

    # Simulate that the delete function found nothing to remove
    mock_delete_all_books.return_value = 0

    # ACT
    main()

    # ASSERT
    captured = capsys.readouterr()
    assert "ℹ️ Info: The collection was already empty." in captured.out
    mock_delete_all_books.assert_called_once()


# CATEGORY 2: INTEGRATION TEST for the `delete_all_books` function
def test_delete_all_books_clears_collection_and_returns_count(
    mock_books_collection, sample_book_data
):
    """
    Integration Test: Verifies the `delete_all_books` function itself.
    GIVEN a mock database collection with documents in it,
    WHEN delete_all_books is called on that collection,
    THEN the collection should be empty and the correct count returned.
    """
    # ARRANGE: Populate the mock database
    mock_books_collection.insert_many(sample_book_data)
    initial_count = len(sample_book_data)
    assert mock_books_collection.count_documents({}) == initial_count

    # ACT: Call the *real* function with the mock collection
    deleted_count = delete_all_books(mock_books_collection)

    # ASSERT: Check the return value and the final state of the DB
    assert deleted_count == initial_count
    assert mock_books_collection.count_documents({}) == 0