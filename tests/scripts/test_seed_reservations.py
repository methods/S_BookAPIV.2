# pylint: disable=line-too-long
"""..."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest
from bson import ObjectId
from pymongo.errors import PyMongoError

from scripts import seed_reservations as load_reservations_module
from scripts.seed_reservations import (load_reservations_json,
                                       run_reservation_population)


def test_load_reservations_json_success():
    """
    GIVEN a valid JSON string representing reservation data
    WHEN load_reservations_json is called with a mock of the file system
    THEN it should return the parsed data as a list of dictionaries.
    """
    # Arrange
    test_reservations_data = """[
        {
        "book_title": "To Kill a Mockingbird",
        "user_identifier": "user_harper_l",
        "state": "reserved"
    },
    {
        "book_title": "Pride and Prejudice",
        "user_identifier": "user_jane_a",
        "state": "cancelled"
    }
    ]"""

    # use mock_open to simulate reading this valid content
    mocked_file = mock_open(read_data=test_reservations_data)

    with patch("builtins.open", mocked_file):

        # Act
        reservations = load_reservations_json()
        # Assert
        assert isinstance(reservations, list)
        assert len(reservations) == 2

        assert reservations[0]["book_title"] == "To Kill a Mockingbird"
        assert reservations[0]["user_identifier"] == "user_harper_l"
        assert reservations[0]["state"] == "reserved"
        assert reservations[-1]["book_title"] == "Pride and Prejudice"
        assert reservations[-1]["user_identifier"] == "user_jane_a"
        assert reservations[-1]["state"] == "cancelled"


def test_load_reservation_file_not_found(capsys):
    """
    GIVEN that the reservation data file is not found on the file system
    WHEN load_reservations_json is called
    THEN the function should return None and print a 'file not found' error message to stderr.
    """
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = load_reservations_json()

        assert result is None
        captured = capsys.readouterr()
        assert "ERROR: Data file not found" in captured.err


def test_load_reservations_json_decode_error(capsys):
    """
    GIVEN that the reservation data file contains invalid (malformed) JSON
    WHEN load_reservations_json is called
    THEN the function should handle the JSONDecodeError,
    return None, and print a helpful error message to stderr.
    """
    bad_json = '{"broken": }'  # invalid JSON
    m = mock_open(read_data=bad_json)
    # patch builtins.open so json.load() raises JSONDecodeError inside function
    with patch("builtins.open", m):
        result = load_reservations_json()

    assert result is None
    captured = capsys.readouterr()
    assert "Could not decode JSON" in captured.err


def test_load_reservations_integration_reads_file(tmp_path, monkeypatch):
    """
    Integration: create a temporary scripts/test_data/sample_reservations.json
    and monkeypatch module __file__ so load_reservations_json resolves to that path.
    """
    # Prepare temporary dir structure
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    test_data_dir = scripts_dir / "test_data"
    test_data_dir.mkdir()
    # IMPORTANT: create the exact filename the function expects
    file_path = test_data_dir / "sample_reservations.json"

    sample_data = [{"reservation_id": "r1", "status": "active"}]
    file_path.write_text(json.dumps(sample_data), encoding="utf-8")

    # Monkeypatch the module's __file__ so os.path.dirname(__file__) -> scripts_dir
    fake_module_file = scripts_dir / "seed_reservations.py"
    monkeypatch.setattr(load_reservations_module, "__file__", str(fake_module_file))

    # Call the function — it should read the created file
    result = load_reservations_json()
    assert result == sample_data


# -------------- TESTS for run_reservation_population -----------------

# A list of test cases for the failure scenarios
error_scenarios = [
    # id is a descriptive name that will appear in the test results
    pytest.param(None, [{"user_id": 1}], id="book_collection_is_empty"),
    pytest.param([{"id": 1}], None, id="reservation_collection_is_none"),
    pytest.param(None, None, id="both_collections_are_none"),
]


@pytest.mark.parametrize(
    "mock_books_return_val, mock_reservations_return_val", error_scenarios
)
@patch("scripts.seed_reservations.get_book_collection")
@patch("scripts.seed_reservations.get_reservation_collection")
def test_returns_404_if_any_collection_is_missing(
    mock_get_books,
    mock_get_reservations,  # Mocks come first
    test_app,  # fixture from conftest.py
    mock_books_return_val,
    mock_reservations_return_val,  # Params come after
):
    """
    GIVEN that either the book or reservation collection is missing (falsy)
    WHEN run_reservations_population is called
    THEN it should return a 404 error with a specific message
    """
    # ARRANGE: Use the parameters to set the return values of our mocks
    mock_get_books.return_value = mock_books_return_val
    mock_get_reservations.return_value = mock_reservations_return_val

    # ACT
    with test_app.app_context():
        response, status_code = run_reservation_population()

    # ASSERT: The expected outcome is the same for all parametrized cases
    assert status_code == 404
    assert response.get_json() == {"error": "Required collections could not be loaded."}

    # You can also assert that the first function was always called
    mock_get_books.assert_called_once()


def test_returns_200_when_collections_are_present(
    test_app, mongo_setup, sample_book_data
):
    """
    GIVEN a database with books and reservations
    WHEN run_reservations_population is called
    THEN it should return a 200 success response
    """
    _ = mongo_setup

    with test_app.app_context():
        # Get the collections from the GLOBAL `mongo` object
        from app.extensions import \
            mongo  # pylint: disable=import-outside-toplevel

        mock_books_collection_with_data = mongo.db.books
        mock_reservations_collection_with_data = mongo.db.reservations

        # SEED the collection directly with your sample data.
        mock_books_collection_with_data.insert_many(sample_book_data)
        mock_reservations_collection_with_data.insert_many([
            {"user_id": "user_george_o", "book_title": "A Book", "state": "reserved"}
        ])

        # 4. NOW, patch the helper functions to return THESE specific, seeded collection objects.
        with patch(
            "scripts.seed_reservations.get_book_collection",
            return_value=mock_books_collection_with_data,
        ), patch(
            "scripts.seed_reservations.get_reservation_collection",
            return_value=mock_reservations_collection_with_data,
        ):

            # ACT: Call the function. It will now use the seeded mongomock collection.
            with test_app.app_context():
                response, status_code = run_reservation_population()

    # ASSERT
    assert status_code == 200
    assert response.get_json()["status"] == "success"


def test_returns_warning_when_no_books_are_found(test_app):
    """
    GIVEN get_book_collection returns a collection that finds no books
    WHEN run_reservation_population is called
    THEN it should return a tuple with a warning message
    """
    # ARRANGE
    # 1. Create a mock collection object. This simulates the real collection.
    mock_books_collection = MagicMock()

    # 2. Control what `.find()` returns:
    # make it return an empty list to simulate no books being found.
    mock_books_collection.find.return_value = []

    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()
    ):
        # ACT
        with test_app.app_context():
            # In Flask, non-jsonify responses don't get split into (response, status)
            # So we just capture the single return value.
            result = run_reservation_population()

    # ASSERT
    expected_warning = (
        True,
        "Warning: No books found in the database. Cannot create reservations.",
    )
    assert result == expected_warning

    mock_books_collection.find.assert_called_once_with({}, {"_id": 1, "title": 1})


def test_returns_error_on_pymongo_error(test_app):
    """
    GIVEN the database call to find books raises a PyMongoError
    WHEN run_reservation_population is called
    THEN it should catch the exception and return a tuple with an error message
    """
    # ARRANGE
    mock_books_collection = MagicMock()

    # 2. Control the BEHAVIOR of .find() with .side_effect
    error_message = "Database connection failed"
    mock_books_collection.find.side_effect = PyMongoError(error_message)

    # 3. Patch the helpers
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()
    ):

        # ACT
        with test_app.app_context():
            result = run_reservation_population()

    # ASSERT
    expected_error = (
        False,
        f"ERROR: Failed to fetch books from database: {error_message}",
    )
    assert result == expected_error


def test_creates_book_id_map_and_proceeds_on_happy_path(test_app):
    """
    GIVEN the database contains books
    WHEN run_reservation_population is called
    THEN it should create the book_id_map and proceed successfully
    """
    # ARRANGE
    mock_books_collection = MagicMock()

    # 2. Simulate a successful find() call that returns documents
    sample_books_cursor = [
        {"_id": ObjectId(), "title": "To Kill a Mockingbird"},
        {"_id": ObjectId(), "title": "1984"},
    ]
    mock_books_collection.find.return_value = sample_books_cursor

    # 3. Patch the helpers
    with patch(
        "scripts.seed_reservations.get_book_collection",
        return_value=mock_books_collection,
    ), patch(
        "scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()
    ):

        # ACT
        with test_app.app_context():
            response, status_code = run_reservation_population()

    # ASSERT
    # Check that we made it to the end of the function successfully
    assert status_code == 200
    assert response.get_json()["status"] == "success"

    # Crucially, verify that the database was queried correctly
    mock_books_collection.find.assert_called_once_with({}, {"_id": 1, "title": 1})


def test_returns_error_if_reservation_json_fails_to_load(test_app):
    """
    GIVEN the load_reservations_json helper returns None
    WHEN run_reservation_population is called
    THEN it should return a tuple with a failure message
    """
    # ARRANGE: Mock all previous steps to succeed so we can test the target logic.

    # 1. Mock get_book_collection to return a collection...
    mock_books_collection = MagicMock()
    # ...that returns at least one book, so the book_id_map is created.
    sample_book_cursor = [{"_id": ObjectId(), "title": "A Book"}]
    mock_books_collection.find.return_value = sample_book_cursor

    # 2. Need to patch all the external dependencies for this unit.
    #    The key is patching `load_reservations_json` to return None.
    with patch("scripts.seed_reservations.get_book_collection", return_value=mock_books_collection), \
         patch("scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()), \
         patch("scripts.seed_reservations.load_reservations_json", return_value=None) as mock_load_json:

        # ACT
        with test_app.app_context():
            result = run_reservation_population()

    # ASSERT
    expected_error = (False, "Failed to load reservation data.")
    assert result == expected_error

    # Verify that we did attempt to load the JSON file.
    mock_load_json.assert_called_once()


def test_proceeds_when_reservation_json_loads_successfully(test_app):
    """
    GIVEN the load_reservations_json helper returns a list of data
    WHEN run_reservation_population is called
    THEN it should proceed successfully to the end of the function
    """
    # ARRANGE: Same setup as the failure test, but with a different return value for the key mock.

    mock_books_collection = MagicMock()
    sample_book_cursor = [{"_id": ObjectId(), "title": "A Book"}]
    mock_books_collection.find.return_value = sample_book_cursor

    # This is our simulated successful data load.
    sample_reservation_data = [{
        "user_id": "test_user_123",
        "book_title": "A Book",
        "state": "reserved"
        }]

    with patch("scripts.seed_reservations.get_book_collection", return_value=mock_books_collection), \
         patch("scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()), \
         patch("scripts.seed_reservations.load_reservations_json", return_value=sample_reservation_data) as mock_load_json:

        # ACT
        with test_app.app_context():
            # Expecting the final success response
            response, status_code = run_reservation_population()

    # ASSERT
    assert status_code == 200
    assert response.get_json()["status"] == "success"

    # Verify we attempted to load the JSON file.
    mock_load_json.assert_called_once()


def test_skips_reservation_if_book_title_not_found(test_app, capsys):
    """
    GIVEN a reservation's book_title is not in the book_id_map
    WHEN run_reservation_population is called
    THEN it should print a warning and continue, eventually succeeding
    """
    # ARRANGE: Set up the entire function to run, controlling the inputs.

    # 1. Create a book map with known books.
    mock_books_collection = MagicMock()
    sample_book_for_map = [{"_id": ObjectId(), "title": "The Hobbit"}]
    mock_books_collection.find.return_value = sample_book_for_map

    # 2. Create a reservation data from JSON that contains an UNKNOWN book title.
    reservation_with_bad_title = [{"book_title": "A Book That Does Not Exist"}]

    # 3. Patch all dependencies.
    with patch("scripts.seed_reservations.get_book_collection", return_value=mock_books_collection), \
         patch("scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()), \
         patch("scripts.seed_reservations.load_reservations_json", return_value=reservation_with_bad_title):

        # ACT
        with test_app.app_context():
            _response, status_code = run_reservation_population()

    # ASSERT
    # The function should still complete successfully overall.
    assert status_code == 200

    # Capture the printed output.
    captured = capsys.readouterr()
    expected_warning = "WARNING: Skipping reservation because book 'A Book That Does Not Exist' was not found.\n"
    assert expected_warning in captured.out

def test_proceeds_if_book_title_is_found(test_app, capsys):
    """
    GIVEN a reservation's book_title IS in the book_id_map
    WHEN run_reservation_population is called
    THEN it should not print a warning and should proceed
    """
    # ARRANGE
    # 1. The book map has a specific, known book.
    mock_books_collection = MagicMock()
    book_title_to_find = "The Lord of the Rings"
    sample_book_for_map = [{"_id": ObjectId(), "title": book_title_to_find}]
    mock_books_collection.find.return_value = sample_book_for_map

    # 2. The reservation data refers to that EXACT book title.
    reservation_with_good_title = [{
        "book_title": book_title_to_find,
        "user_id": "another_user_456",
        "state": "pending"
        }]

    # 3. Patch dependencies.
    with patch("scripts.seed_reservations.get_book_collection", return_value=mock_books_collection), \
         patch("scripts.seed_reservations.get_reservation_collection", return_value=MagicMock()), \
         patch("scripts.seed_reservations.load_reservations_json", return_value=reservation_with_good_title):

        # ACT
        with test_app.app_context():
            _response, status_code = run_reservation_population()

    # ASSERT
    assert status_code == 200

    # Crucially, assert that NO warning was printed.
    captured = capsys.readouterr()
    warning_message_to_avoid = "WARNING: Skipping reservation"
    assert warning_message_to_avoid not in captured.out


def test_creates_new_reservation_if_not_exists(test_app):
    """
    GIVEN a reservation does not exist in the database
    WHEN run_reservation_population processes it
    THEN it should call update_one with upsert=True and increment created_count
    """
    # ARRANGE
    # 1. Setup mocks for all preceding steps to succeed.
    mock_book_id = ObjectId()
    mock_user_id = "user123"
    book_title = "The Hobbit"

    mock_books_collection = MagicMock()
    mock_books_collection.find.return_value = [{"_id": mock_book_id, "title": book_title}]

    reservations_from_json = [
        {"user_id": mock_user_id, "book_title": book_title, "state": "reserved"}
    ]

    # 2. This is the crucial part: Mock the reservations collection and its method results.
    mock_reservations_collection = MagicMock()

    # 3. Create a MOCK result object for a successful UPSERT.
    mock_upsert_result = MagicMock()
    mock_upsert_result.upserted_id = ObjectId() # A non-None value signals creation
    mock_upsert_result.matched_count = 0
    mock_reservations_collection.update_one.return_value = mock_upsert_result

    # 4. Patch all dependencies.
    with patch("scripts.seed_reservations.get_book_collection", return_value=mock_books_collection), \
         patch("scripts.seed_reservations.get_reservation_collection", return_value=mock_reservations_collection), \
         patch("scripts.seed_reservations.load_reservations_json", return_value=reservations_from_json):

        # ACT
        with test_app.app_context():
            response, status_code = run_reservation_population()

    # ASSERT
    assert status_code == 200

    # Assert that the database method was called with the correct data
    expected_filter = {"user_id": mock_user_id, "book_id": mock_book_id}
    expected_update = {"$set": {"user_id": mock_user_id, "book_id": mock_book_id, "state": "reserved"}}
    mock_reservations_collection.update_one.assert_called_once_with(expected_filter, expected_update, upsert=True)

    # Assert the final counts in the success message (this will fail until you update the return statement)
    expected_message = "Collections loaded."
    assert response.get_json()["message"] == expected_message


def test_returns_error_on_reservation_upsert_failure(test_app):
    """
    GIVEN the call to update_one raises a PyMongoError
    WHEN run_reservation_population processes a reservation
    THEN it should catch the error and return a failure tuple
    """
    # ARRANGE
    mock_book_id = ObjectId()
    mock_user_id = "user789"
    book_title = "Dune"

    mock_books_collection = MagicMock()
    mock_books_collection.find.return_value = [{"_id": mock_book_id, "title": book_title}]

    reservations_from_json = [
        {"user_id": mock_user_id, "book_title": book_title, "state": "reserved"}
    ]

    mock_reservations_collection = MagicMock()

    # Configure the mock to RAISE an error instead of returning a value.
    error_message = "Connection refused"
    mock_reservations_collection.update_one.side_effect = PyMongoError(error_message)

    with patch("scripts.seed_reservations.get_book_collection", return_value=mock_books_collection), \
         patch("scripts.seed_reservations.get_reservation_collection", return_value=mock_reservations_collection), \
         patch("scripts.seed_reservations.load_reservations_json", return_value=reservations_from_json):

        # ACT
        with test_app.app_context():
            result = run_reservation_population()

    # ASSERT
    expected_error = (False, f"ERROR: Failed to upsert reservation for user '{mock_user_id}': {error_message}")
    assert result == expected_error
