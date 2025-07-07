# pylint: disable=missing-docstring,line-too-long
from unittest.mock import patch, MagicMock
from scripts.delete_books import delete_all_books, main


# ----------------- TEST SUITE ---------------------------------

@patch("scripts.delete_books.create_app")
@patch("scripts.delete_books.get_book_collection")
@patch("scripts.delete_books.delete_all_books")
def test_main_orchestrates_book_deletion_and_reports_success(
    mock_delete_all_books,
    mock_get_book_collection,
    mock_create_app,
    capsys
):
    # Arrange:
    # 1. Mock the Flask app object and its config
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    # 2. Mock the collection object that our helper will "return"
    mock_collection = MagicMock(name="mock_collection")
    mock_get_book_collection.return_value = mock_collection

    # 3. Configure the mock for delete_all_books
    mock_delete_all_books.return_value = 2

    # Act: run the function we are testing
    # It will use our MOCKS instead of real functions
    main()

    # Assert:
    # 1. Check that our helper was called correctly
    mock_get_book_collection.assert_called_once()

    # 2. Check that delete_all_books was called with the collection from the helper
    mock_delete_all_books.assert_called_once_with(mock_collection)

    # 3. Check that the correct output was printed
    captured = capsys.readouterr()
    assert "✅ Success: Removed 2 existing document(s)." in captured.out


@patch("scripts.delete_books.create_app")
@patch("scripts.delete_books.get_book_collection")
@patch("scripts.delete_books.delete_all_books")
def test_main_reports_info_when_collection_is_empty(
    mock_delete_all_books,
    mock_get_book_collection,
    mock_create_app,
    capsys
):
    """
    Unit Test: Verifies `main`'s logic for the "already empty" path.
    GIVEN the delete_all_books function reports it deleted 0 documents,
    WHEN main() is called,
    THEN it should print the informational message.
    """
    # ARRANGE
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

     # 2. Mock the collection object that our helper will "return"
    mock_collection = MagicMock(name="mock_collection")
    mock_get_book_collection.return_value = mock_collection

    # Simulate that the delete function found nothing to remove
    mock_delete_all_books.return_value = 0

    # ACT
    main()

    # ASSERT
    # Check that our mocks were called as expected
    mock_get_book_collection.assert_called_once()
    mock_delete_all_books.assert_called_once_with(mock_collection)

    # Check that the correct output was printed
    captured = capsys.readouterr()
    assert "ℹ️ Info: The collection was already empty." in captured.out



# INTEGRATION TEST for the `delete_all_books` function
def test_delete_all_books_clears_collection_and_returns_count(
    mock_books_collection,
    sample_book_data
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
